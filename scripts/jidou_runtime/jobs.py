"""Explicit argv-only jobs, with durable execution claims and no automatic replay."""
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid

from . import JidouError
from .schedule import Rule, instant, stamp
from .store import encode


def add(store, recipe, disabled=False):
    allowed = {'name', 'argv', 'run_at', 'repeat', 'timeout_seconds', 'cwd', 'env_refs'}
    if not isinstance(recipe, dict) or set(recipe) - allowed:
        raise JidouError('Unsupported job recipe; use argv, not a shell string.')
    argv = recipe.get('argv')
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or '\x00' in x for x in argv) or not argv[0]:
        raise JidouError('A job needs a nonempty argv array of strings.')
    executable = shutil.which(argv[0])
    if not executable:
        raise JidouError('The explicitly selected job executable is unavailable.')
    timeout = recipe.get('timeout_seconds', 300)
    if type(timeout) is not int or not 1 <= timeout <= 3600:
        raise JidouError('Job timeout must be 1..3600 seconds.')
    env_refs = recipe.get('env_refs', {})
    if not isinstance(env_refs, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', v) for k, v in env_refs.items()):
        raise JidouError('env_refs maps environment names to other environment names, never secret values.')
    cwd = Path(recipe.get('cwd') or store.home).expanduser().resolve()
    if not cwd.is_dir():
        raise JidouError('Job working directory must already exist.')
    name = recipe.get('name')
    if not isinstance(name, str) or not name.strip():
        raise JidouError('Job name is required.')
    selected = {**recipe, 'argv': [executable, *argv[1:]], 'cwd': str(cwd), 'timeout_seconds': timeout, 'env_refs': env_refs}
    with store.connection(write=True) as con:
        timezone_name = store.config(con)['timezone']
        rule = Rule.fields({'重复': recipe.get('repeat', ''), '到期': recipe.get('run_at', ''), '提醒': '准时'}, timezone_name)
        first = instant(recipe['run_at']) if recipe.get('run_at') else rule.next(store.now) if rule.text else None
        if first is None or first <= store.now:
            raise JidouError('Provide a future run_at or a recurring schedule; expired once jobs are not automatically replayed.')
        job_id = uuid.uuid4().hex
        fields = store.normalize(con, {'内容': name, '原文': '', '类型': '定时', '领域': '其他', '状态': '归档' if disabled else '进行中', '执行': '脚本', '执行内容': encode(selected), '任务ID': job_id, '到期': first.isoformat(), '下次触发': first.isoformat(), '重复': recipe.get('repeat', '')})
        record = store.insert(con, fields)
        selected['run_at'] = first.isoformat()
        con.execute('INSERT INTO jobs VALUES (?,?,?,?,?)', (job_id, record['id'], encode(selected), stamp(first), 0 if disabled else 1))
        return {'job_id': job_id, 'record': record, 'enabled': not disabled}


def list_jobs(store):
    with store.connection() as con:
        rows = con.execute('SELECT id,record_id,next_run,enabled FROM jobs ORDER BY rowid').fetchall()
        return {'jobs': [dict(row) for row in rows]}


def list_runs(store, job_id=None):
    with store.connection() as con:
        where, params = (' WHERE job_id=?', (job_id,)) if job_id else ('', ())
        rows = con.execute('SELECT * FROM job_runs' + where + ' ORDER BY started_at DESC LIMIT 100', params).fetchall()
        return {'runs': [dict(row) for row in rows]}


def set_enabled(store, job_id, enabled, next_run=None):
    with store.connection(write=True) as con:
        row = con.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
        if row is None:
            raise JidouError('Job not found.')
        run = instant(next_run) if next_run else instant(row['next_run'])
        if enabled and next_run and run <= store.now:
            raise JidouError('--next-run must be in the future.')
        if enabled and run <= store.now:
            recipe = json.loads(row['recipe'])
            rule = Rule.fields({'重复': recipe.get('repeat', ''), '到期': recipe['run_at'], '提醒': '准时'}, store.config(con)['timezone'])
            if not rule.text:
                raise JidouError('Re-enabling an expired once job requires --next-run with a future timestamp.')
            run = rule.next(store.now)
        con.execute('UPDATE jobs SET enabled=?,next_run=? WHERE id=?', (int(enabled), stamp(run), job_id))
        fields = store.get_in(con, row['record_id'])['fields']
        fields['状态'], fields['下次触发'] = ('进行中' if enabled else '归档'), run.isoformat()
        store.save(con, row['record_id'], fields)
        return {'job_id': job_id, 'enabled': enabled, 'already_running': bool(con.execute("SELECT 1 FROM job_runs WHERE job_id=? AND status IN ('running','unknown')", (job_id,)).fetchone())}


def tick(store):
    runs = []
    with store.connection() as con:
        ids = [row[0] for row in con.execute('SELECT id FROM jobs WHERE enabled=1 AND next_run<=?', (stamp(store.now),))]
    for job_id in ids:
        with store.connection(write=True) as con:
            row = con.execute('SELECT * FROM jobs WHERE id=? AND enabled=1 AND next_run<=?', (job_id, stamp(store.now))).fetchone()
            if row is None or con.execute("SELECT 1 FROM job_runs WHERE job_id=? AND status IN ('running','unknown')", (job_id,)).fetchone():
                continue
            record_fields = store.get_in(con, row['record_id'])['fields']
            if record_fields['状态'] in {'归档', '已完成'} or record_fields['执行'] != '脚本' or record_fields['任务ID'] != job_id or record_fields['类型'] != '定时':
                con.execute('UPDATE jobs SET enabled=0 WHERE id=?', (job_id,))
                continue
            recipe = json.loads(row['recipe'])
            event = instant(row['next_run'])
            run_id = uuid.uuid4().hex
            key = job_id + '/' + stamp(event)
            if con.execute('SELECT 1 FROM job_runs WHERE event_key=?', (key,)).fetchone():
                continue
            rule = Rule.fields({'重复': recipe.get('repeat', ''), '到期': recipe['run_at'], '提醒': '准时'}, store.config(con)['timezone'])
            next_run = stamp(rule.next(max(store.now, event))) if rule.text else row['next_run']
            con.execute('INSERT INTO job_runs (id,job_id,event_key,status,started_at) VALUES (?,?,?,?,?)', (run_id, job_id, key, 'running', stamp(store.now)))
            con.execute('UPDATE jobs SET enabled=?,next_run=? WHERE id=?', (1 if rule.text else 0, next_run, job_id))
        result = {'run_id': run_id, 'job_id': job_id, 'status': 'failed', 'exit_code': None}
        try:
            env = dict(os.environ)
            for target, source in recipe['env_refs'].items():
                if source not in os.environ:
                    raise JidouError('A required job environment reference is unavailable.')
                env[target] = os.environ[source]
            # No shell and no automatic retries; stdout/stderr may contain secrets.
            completed = subprocess.run(recipe['argv'], cwd=recipe['cwd'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=recipe['timeout_seconds'])
            result.update(status='success' if completed.returncode == 0 else 'failed', exit_code=completed.returncode)
        except subprocess.TimeoutExpired:
            result.update(status='unknown', error='timeout; verify external effects before resolving this run')
        except (OSError, JidouError):
            result['error'] = 'command/environment unavailable; no secrets or program output stored'
        with store.connection(write=True) as con:
            con.execute('UPDATE job_runs SET status=?,finished_at=?,result=? WHERE id=?', (result['status'], stamp(store.now), encode(result), run_id))
            fields = store.get_in(con, row['record_id'])['fields']
            fields['上次结果'] = encode(result)
            current_job = con.execute('SELECT next_run FROM jobs WHERE id=?', (job_id,)).fetchone()
            fields['下次触发'] = current_job['next_run'] if rule.text else ''
            if not rule.text and fields['状态'] != '归档':
                fields['状态'] = '已完成' if result['status'] == 'success' else '待看'
                fields['完成于'] = store.now.astimezone(rule.tz).date().isoformat() if result['status'] == 'success' else ''
            store.save(con, row['record_id'], fields)
        runs.append(result)
    return {'runs': runs}


def resolve(store, run_id, status):
    with store.connection(write=True) as con:
        row = con.execute('SELECT * FROM job_runs WHERE id=?', (run_id,)).fetchone()
        if row is None or row['status'] not in {'running', 'unknown'}:
            raise JidouError('Only an uncertain run can be explicitly resolved after checking its real effects.')
        result = {'run_id': run_id, 'job_id': row['job_id'], 'status': status, 'resolution': 'explicitly verified by user; not executed again'}
        con.execute('UPDATE job_runs SET status=?,finished_at=?,result=? WHERE id=?', (status, stamp(store.now), encode(result), run_id))
        job = con.execute('SELECT record_id FROM jobs WHERE id=?', (row['job_id'],)).fetchone()
        fields = store.get_in(con, job['record_id'])['fields']
        try:
            current = json.loads(fields['上次结果'] or '{}')
        except ValueError:
            current = {}
        if current.get('run_id') == run_id:
            fields['上次结果'] = encode(result)
            recipe = json.loads(con.execute('SELECT recipe FROM jobs WHERE id=?', (row['job_id'],)).fetchone()[0])
            if not recipe.get('repeat') and fields['状态'] != '归档':
                fields['状态'] = '已完成' if status == 'success' else '待看'
                fields['完成于'] = store.now.astimezone(Rule.fields({}, store.config(con)['timezone']).tz).date().isoformat() if status == 'success' else ''
                fields['下次触发'] = ''
            store.save(con, job['record_id'], fields)
        return {'run_id': run_id, 'status': status, 'executed_again': False}
