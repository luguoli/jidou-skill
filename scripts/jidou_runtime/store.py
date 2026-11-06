"""Explicit, transactional local storage; all 21 business fields are preserved."""
from contextlib import contextmanager
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import uuid

from . import JidouError
from .schedule import Rule, instant, stamp, zone

ROOT = Path(__file__).resolve().parents[2]
PROPERTIES = json.loads((ROOT / 'references/schema.json').read_text(encoding='utf-8'))['schema']['properties']
FIELDS = [prop['name'] for prop in PROPERTIES]
ENUMS = {prop['name']: {x['text'] for x in prop['config']['select']['options']} for prop in PROPERTIES if 'select' in prop['config']}
DATES = {prop['name'] for prop in PROPERTIES if 'date' in prop['config']}


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def default_home(platform=None, env=None, user_home=None):
    platform, env, user_home = platform or sys.platform, os.environ if env is None else env, Path(user_home or Path.home())
    if env.get('JIDOU_HOME'):
        return Path(env['JIDOU_HOME']).expanduser()
    if platform == 'win32':
        return Path(env.get('LOCALAPPDATA') or user_home / 'AppData/Local') / 'jidou'
    if platform == 'darwin':
        return user_home / 'Library/Application Support/jidou'
    return Path(env.get('XDG_DATA_HOME') or user_home / '.local/share') / 'jidou'


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


class Store:
    def __init__(self, home, now=None):
        self.home = Path(home).expanduser().resolve()
        self.path = self.home / 'jidou.sqlite3'
        self._now = now

    @property
    def now(self):
        return self._now if self._now is not None else datetime.now(timezone.utc)

    @now.setter
    def now(self, value):
        self._now = value

    @contextmanager
    def connection(self, write=False):
        if not self.path.is_file():
            raise JidouError('Local storage is not initialized. Choose this backend and run init first.')
        mode = 'rw' if write else 'ro'
        con = sqlite3.connect(self.path.as_uri() + '?mode=' + mode, uri=True, timeout=15)
        con.row_factory = sqlite3.Row
        try:
            con.execute('PRAGMA foreign_keys=ON')
            if con.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise JidouError('Unsupported local database version; do not overwrite it.')
            owner = con.execute("SELECT value FROM meta WHERE key='owner'").fetchone()
            if owner is None or owner[0] != 'jidou-local-v1':
                raise JidouError('This is not a jidou-owned database.')
            if write:
                con.execute('BEGIN IMMEDIATE')
            yield con
            if write:
                con.commit()
        except Exception:
            if write:
                con.rollback()
            raise
        finally:
            con.close()

    def initialize(self, timezone_name='Asia/Shanghai'):
        zone(timezone_name)
        if self.path.exists():
            with self.connection() as con:
                return {'initialized': True, 'backend': 'local', 'database_id': self.config(con)['database_id'], 'database': str(self.path)}
        new_directory = not self.home.exists()
        self.home.mkdir(parents=True, exist_ok=True)
        if os.name != 'nt' and new_directory:
            self.home.chmod(0o700)
        con = sqlite3.connect(self.path, timeout=15)
        try:
            if os.name != 'nt':
                self.path.chmod(0o600)
            con.execute('PRAGMA journal_mode=WAL')
            con.execute('BEGIN IMMEDIATE')
            existing = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if existing:
                raise JidouError('Database appeared during initialization; retry without overwriting it.')
            con.execute('CREATE TABLE meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            columns = ','.join(quoted(name) + " TEXT NOT NULL DEFAULT ''" for name in FIELDS)
            con.execute('CREATE TABLE records (id TEXT PRIMARY KEY,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,' + columns + ')')
            con.execute('CREATE INDEX lineage_idx ON records ("线索")')
            con.execute('CREATE TABLE sequence (day TEXT PRIMARY KEY,number INTEGER NOT NULL)')
            con.execute('CREATE TABLE operations (id TEXT PRIMARY KEY,digest TEXT NOT NULL,response TEXT NOT NULL)')
            con.execute('CREATE TABLE occurrences (receipt_id TEXT PRIMARY KEY REFERENCES records(id),template_id TEXT NOT NULL REFERENCES records(id),event_at TEXT NOT NULL,status TEXT NOT NULL)')
            con.execute('CREATE INDEX occurrence_lookup ON occurrences(template_id,event_at,status)')
            con.execute('CREATE TABLE notifications (id TEXT PRIMARY KEY,event_key TEXT UNIQUE NOT NULL,record_id TEXT NOT NULL REFERENCES records(id),event_at TEXT NOT NULL,reminder_at TEXT NOT NULL,body TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,lease_token TEXT,lease_until TEXT,next_attempt TEXT,last_error TEXT,accepted_at TEXT)')
            con.execute('CREATE TABLE jobs (id TEXT PRIMARY KEY,record_id TEXT NOT NULL REFERENCES records(id),recipe TEXT NOT NULL,next_run TEXT NOT NULL,enabled INTEGER NOT NULL)')
            con.execute('CREATE TABLE job_runs (id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id),event_key TEXT UNIQUE NOT NULL,status TEXT NOT NULL,started_at TEXT NOT NULL,finished_at TEXT,result TEXT)')
            defaults = json.loads((ROOT / 'references/defaults.json').read_text(encoding='utf-8'))
            settings = {**defaults['reminder'], **defaults['local'], 'timezone': timezone_name, 'database_id': uuid.uuid4().hex, 'reminder_start_at': stamp(self.now)}
            con.execute('INSERT INTO meta VALUES (?,?)', ('owner', 'jidou-local-v1'))
            con.execute('INSERT INTO meta VALUES (?,?)', ('settings', encode(settings)))
            con.execute('PRAGMA user_version=1')
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
        return {'initialized': True, 'backend': 'local', 'database_id': settings['database_id'], 'database': str(self.path)}

    @staticmethod
    def config(con):
        return json.loads(con.execute("SELECT value FROM meta WHERE key='settings'").fetchone()[0])

    def settings(self):
        with self.connection() as con:
            return self.config(con)

    def update_settings(self, changes):
        allowed = {'timezone', 'quiet_start_hour', 'quiet_end_hour', 'catchup_hours', 'reminders_enabled'}
        if not isinstance(changes, dict) or set(changes) - allowed:
            raise JidouError('Only timezone, quiet hours, catchup hours and reminders_enabled are configurable here.')
        with self.connection(write=True) as con:
            previous = self.config(con)
            settings = {**previous, **changes}
            zone(settings['timezone'])
            for name in ('quiet_start_hour', 'quiet_end_hour'):
                if type(settings[name]) is not int or not 0 <= settings[name] <= 23:
                    raise JidouError('Quiet hours must be integers from 0 to 23.')
            if settings['quiet_start_hour'] == settings['quiet_end_hour']:
                raise JidouError('Quiet start and end must differ; pause reminders explicitly for all-day silence.')
            if type(settings['catchup_hours']) is not int or settings['catchup_hours'] <= 0:
                raise JidouError('Catchup hours must be a positive integer.')
            if type(settings.get('reminders_enabled', True)) is not bool:
                raise JidouError('reminders_enabled must be a JSON boolean.')
            if not settings.get('reminders_enabled', True):
                con.execute("UPDATE notifications SET status='cancelled' WHERE status IN ('pending','claimed')")
            elif not previous.get('reminders_enabled', True):
                settings['reminder_start_at'] = stamp(self.now)
            con.execute("UPDATE meta SET value=? WHERE key='settings'", (encode(settings),))
            return settings

    def doctor(self):
        result = {'backend': 'local', 'initialized': self.path.is_file(), 'home': str(self.home), 'database': str(self.path), 'platform': sys.platform, 'python': sys.version.split()[0]}
        if result['initialized']:
            with self.connection() as con:
                result['settings'] = self.config(con)
                result['records'] = con.execute('SELECT count(*) FROM records').fetchone()[0]
                result['pending_notifications'] = con.execute("SELECT count(*) FROM notifications WHERE status IN ('pending','claimed')").fetchone()[0]
                result['uncertain_job_runs'] = con.execute("SELECT count(*) FROM job_runs WHERE status IN ('running','unknown')").fetchone()[0]
                scan = con.execute("SELECT value FROM meta WHERE key='last_scan'").fetchone()
                scheduler = con.execute("SELECT value FROM meta WHERE key='scheduler'").fetchone()
                result['last_scan'] = json.loads(scan[0]) if scan else None
                result['scheduler_registration_saved'] = bool(scheduler)
                result['notification_status_counts'] = {row[0]: row[1] for row in con.execute('SELECT status,count(*) FROM notifications GROUP BY status')}
        return result

    @staticmethod
    def unpack(payload):
        if not isinstance(payload, dict) or set(payload) - set(FIELDS):
            raise JidouError('Record fields must be a JSON object containing only the 21 documented names.')
        result = {}
        for key, value in payload.items():
            if isinstance(value, dict):
                if len(value) != 1 or next(iter(value)) not in {'text', 'date', 'select'}:
                    raise JidouError('Invalid field wrapper.')
                value = next(iter(value.values()))
            if value is None:
                value = ''
            if not isinstance(value, str) or '\x00' in value:
                raise JidouError('Record values must be text or null, without NUL characters.')
            if key in ENUMS and value and value not in ENUMS[key]:
                raise JidouError('Invalid select value for field: ' + key)
            if key in DATES and value:
                if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                    date.fromisoformat(value)
                else:
                    instant(value)
            result[key] = value
        return result

    def normalize(self, con, payload, old=None):
        values = self.unpack(payload)
        if old is None and '原文' not in values:
            raise JidouError('Provide 原文 explicitly; use an empty value only for system-generated records.')
        result = {name: '' for name in FIELDS}
        if old:
            result.update(old)
        else:
            result.update({'类型': '想法', '领域': '其他', '状态': '待看', '提醒': '不提醒'})
        result.update(values)
        if not result['内容'].strip():
            raise JidouError('内容 must not be empty.')
        settings = self.config(con)
        tz = zone(settings['timezone'])
        if not result['记录时间']:
            result['记录时间'] = self.now.astimezone(tz).date().isoformat()
        for key in ('到期', '下次触发', '静音至'):
            if result[key] and len(result[key]) == 10:
                from .schedule import localize
                result[key] = localize(date.fromisoformat(result[key]), datetime.min.time().replace(hour=9), tz).isoformat()
        rule = Rule.fields(result, settings['timezone'])
        if rule.text and not result['到期']:
            result['到期'] = rule.next(self.now).isoformat()
        if not result['下次触发'] and result['到期']:
            result['下次触发'] = result['到期']
        if not result['线索']:
            day = self.now.astimezone(tz).strftime('%Y%m%d')
            row = con.execute('SELECT number FROM sequence WHERE day=?', (day,)).fetchone()
            existing_max = con.execute('SELECT max(CAST(substr("线索",11) AS INTEGER)) FROM records WHERE "线索" LIKE ?', (f'Q{day}-%',)).fetchone()[0] or 0
            number = max(row[0] if row else 0, existing_max) + 1
            while con.execute('SELECT 1 FROM records WHERE "线索"=?', (f'Q{day}-{number:02d}',)).fetchone():
                number += 1
            con.execute('INSERT INTO sequence VALUES (?,?) ON CONFLICT(day) DO UPDATE SET number=excluded.number', (day, number))
            result['线索'] = f'Q{day}-{number:02d}'
        return result

    def insert(self, con, fields, record_id=None, created_at=None, updated_at=None):
        record_id = record_id or uuid.uuid4().hex
        created = stamp(instant(created_at)) if created_at else stamp(self.now)
        updated = stamp(instant(updated_at)) if updated_at else created
        values = (record_id, created, updated, *(fields[name] for name in FIELDS))
        names = ['id', 'created_at', 'updated_at', *FIELDS]
        con.execute('INSERT INTO records (' + ','.join(quoted(x) for x in names) + ') VALUES (' + ','.join('?' for _ in names) + ')', values)
        return self.get_in(con, record_id)

    @staticmethod
    def record(row):
        return {'id': row['id'], 'created_at': row['created_at'], 'updated_at': row['updated_at'], 'fields': {name: row[name] for name in FIELDS}}

    def get_in(self, con, record_id):
        row = con.execute('SELECT * FROM records WHERE id=?', (record_id,)).fetchone()
        if row is None:
            raise JidouError('Record not found.')
        return self.record(row)

    def get(self, record_id):
        with self.connection() as con:
            return self.get_in(con, record_id)

    def save(self, con, record_id, fields):
        con.execute('UPDATE records SET ' + ','.join(quoted(name) + '=?' for name in FIELDS) + ',updated_at=? WHERE id=?', (*(fields[name] for name in FIELDS), stamp(self.now), record_id))
        return self.get_in(con, record_id)

    def add(self, payload, operation_id=None):
        rows = payload.get('records') if isinstance(payload, dict) and set(payload) == {'records'} else [payload]
        if not isinstance(rows, list) or not rows or len(rows) > 1000:
            raise JidouError('Provide one record or a nonempty batch of at most 1000 records.')
        digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        with self.connection(write=True) as con:
            if operation_id:
                previous = con.execute('SELECT * FROM operations WHERE id=?', (operation_id,)).fetchone()
                if previous:
                    if previous['digest'] != digest:
                        raise JidouError('Operation ID already belongs to a different payload.')
                    return {**json.loads(previous['response']), 'replayed': True}
            records = [self.insert(con, self.normalize(con, row)) for row in rows]
            response = {'records': records, 'replayed': False}
            if operation_id:
                con.execute('INSERT INTO operations VALUES (?,?,?)', (operation_id, digest, encode(response)))
            return response

    def update(self, record_id, payload):
        with self.connection(write=True) as con:
            old = self.get_in(con, record_id)['fields']
            fields = self.normalize(con, payload, old)
            job = con.execute('SELECT id,enabled FROM jobs WHERE record_id=?', (record_id,)).fetchone()
            if job:
                managed = {'执行', '执行内容', '任务ID', '类型', '重复', '到期', '下次触发'}
                if any(fields[name] != old[name] for name in managed):
                    raise JidouError('Use job controls for native execution fields; a record update cannot silently change the job recipe.')
                if fields['状态'] in {'归档', '已完成'}:
                    con.execute('UPDATE jobs SET enabled=0 WHERE id=?', (job['id'],))
                elif fields['状态'] != old['状态'] and not job['enabled']:
                    raise JidouError('Use job enable to explicitly resume this paused native task.')
            timing = {'到期', '下次触发', '重复', '提醒', '静音至', '状态', '执行', '类型'}
            if any(old[name] != fields[name] for name in timing):
                con.execute("UPDATE notifications SET status='cancelled' WHERE record_id=? AND status IN ('pending','claimed')", (record_id,))
            return self.save(con, record_id, fields)

    def list(self, filters=None, query=None, limit=100, offset=0):
        if not 1 <= limit <= 1000 or offset < 0:
            raise JidouError('Invalid pagination range.')
        clauses, params = [], []
        for name, value in (filters or {}).items():
            if name not in FIELDS:
                raise JidouError('Unknown filter field.')
            clauses.append(quoted(name) + '=?')
            params.append(value)
        if query:
            pattern = '%' + query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
            clauses.append('(' + ' OR '.join(quoted(name) + " LIKE ? ESCAPE '\\'" for name in ['内容', '标签', '相关人', '来源']) + ')')
            params.extend([pattern] * 4)
        where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
        with self.connection() as con:
            total = con.execute('SELECT count(*) FROM records' + where, params).fetchone()[0]
            rows = con.execute('SELECT * FROM records' + where + ' ORDER BY created_at DESC,rowid DESC LIMIT ? OFFSET ?', [*params, limit, offset]).fetchall()
            return {'records': [self.record(row) for row in rows], 'total': total, 'limit': limit, 'offset': offset}

    def export(self):
        with self.connection() as con:
            return {'jidou_export': 1, 'database_id': self.config(con)['database_id'], 'timezone': self.config(con)['timezone'], 'records': [self.record(row) for row in con.execute('SELECT * FROM records ORDER BY rowid')]}

    def import_records(self, payload):
        if not isinstance(payload, dict) or payload.get('jidou_export') != 1 or not isinstance(payload.get('records'), list):
            raise JidouError('Expected a jidou record export, not a database backup.')
        with self.connection(write=True) as con:
            target_id = self.config(con)['database_id']
            records, receipts = [], []
            for row in payload['records']:
                fields = dict(row['fields'])
                try:
                    marker = json.loads(fields.get('上次结果') or '{}')
                except ValueError:
                    marker = {}
                if isinstance(marker, dict) and marker.get('kind') in {'completion', 'occurrence'} and marker.get('template_record_id'):
                    if marker.get('template_database_id') != payload.get('database_id'):
                        raise JidouError('Occurrence receipt does not belong to the exported database.')
                    marker['template_database_id'] = target_id
                    status = marker.get('status') or ('completed' if fields.get('状态') == '已完成' else 'voided')
                    if status not in {'completed', 'skipped', 'voided'}:
                        raise JidouError('Invalid imported occurrence status.')
                    fields['上次结果'] = encode(marker)
                    receipts.append((row['id'], marker['template_record_id'], stamp(instant(marker['event_at'])), status))
                records.append(self.insert(con, self.normalize(con, fields), row['id'], row.get('created_at'), row.get('updated_at')))
            for receipt in receipts:
                self.get_in(con, receipt[1])
                con.execute('INSERT INTO occurrences VALUES (?,?,?,?)', receipt)
            return {'imported': len(records), 'occurrence_links_restored': len(receipts), 'queue_restored': False}

    def occurrence(self, record_id, event_at=None, status='completed', original=''):
        with self.connection(write=True) as con:
            record = self.get_in(con, record_id)
            if con.execute('SELECT 1 FROM jobs WHERE record_id=?', (record_id,)).fetchone():
                raise JidouError('Use native job controls; record completion is not evidence that a command executed.')
            fields = record['fields']
            settings = self.config(con)
            rule = Rule.fields(fields, settings['timezone'])
            if not rule.text:
                if status != 'completed':
                    raise JidouError('Skip applies only to a recurring record.')
                fields['状态'], fields['完成于'] = '已完成', self.now.astimezone(rule.tz).date().isoformat()
                con.execute("UPDATE notifications SET status='cancelled' WHERE record_id=? AND status IN ('pending','claimed')", (record_id,))
                return {'record': self.save(con, record_id, fields)}
            if not event_at:
                raise JidouError('Specify --event-at for the exact recurring occurrence; do not infer it from an advanced pointer.')
            event = instant(event_at)
            active = con.execute("SELECT receipt_id FROM occurrences WHERE template_id=? AND event_at=? AND status IN ('completed','skipped')", (record_id, stamp(event))).fetchone()
            if active:
                return {'record': record, 'receipt': self.get_in(con, active[0]), 'replayed': True}
            marker = {'kind': 'completion' if status == 'completed' else 'occurrence', 'status': status, 'template_database_id': settings['database_id'], 'template_record_id': record_id, 'event_at': stamp(event)}
            child = self.normalize(con, {'内容': ('完成：' if status == 'completed' else '跳过：') + fields['内容'], '原文': original, '类型': fields['类型'], '领域': fields['领域'], '线索': fields['线索'], '状态': '已完成' if status == 'completed' else '归档', '完成于': self.now.astimezone(rule.tz).date().isoformat() if status == 'completed' else '', '上次结果': encode(marker)})
            receipt = self.insert(con, child)
            con.execute('INSERT INTO occurrences VALUES (?,?,?,?)', (receipt['id'], record_id, stamp(event), status))
            current = instant(fields['下次触发'] or fields['到期'])
            if current == event:
                fields['下次触发'] = rule.next(event).isoformat()
            fields['上次结果'] = encode({'kind': 'occurrence', 'event_at': stamp(event), 'status': status})
            con.execute("UPDATE notifications SET status='cancelled' WHERE record_id=? AND event_at=? AND status IN ('pending','claimed')", (record_id, stamp(event)))
            return {'record': self.save(con, record_id, fields), 'receipt': receipt}

    def undo(self, receipt_id, restore=False):
        with self.connection(write=True) as con:
            row = con.execute('SELECT * FROM occurrences WHERE receipt_id=?', (receipt_id,)).fetchone()
            if row is None:
                raise JidouError('This record is not a local occurrence receipt.')
            if row['status'] == 'voided':
                return {'receipt': self.get_in(con, receipt_id), 'replayed': True}
            template = self.get_in(con, row['template_id'])
            fields = template['fields']
            event = instant(row['event_at'])
            rule = Rule.fields(fields, self.config(con)['timezone'])
            if restore:
                if rule.reminder_at(event) <= self.now:
                    raise JidouError('This reminder is in the past; explicitly choose a new reminder time instead of replaying it.')
                if con.execute("SELECT 1 FROM notifications WHERE record_id=? AND event_at>? AND status NOT IN ('cancelled','expired')", (template['id'], stamp(event))).fetchone():
                    raise JidouError('A later occurrence was already processed; restore the old occurrence separately.')
                if con.execute("SELECT 1 FROM occurrences WHERE template_id=? AND event_at>? AND status IN ('completed','skipped')", (template['id'], stamp(event))).fetchone():
                    raise JidouError('A later occurrence was already completed or skipped; restore the old occurrence separately.')
                fields['下次触发'] = event.isoformat()
            con.execute("UPDATE occurrences SET status='voided' WHERE receipt_id=?", (receipt_id,))
            child = self.get_in(con, receipt_id)['fields']
            marker = json.loads(child['上次结果'])
            marker['status'] = 'voided'
            child['状态'], child['上次结果'] = '归档', encode(marker)
            try:
                previous = json.loads(fields['上次结果'])
            except ValueError:
                previous = {}
            if previous.get('event_at') and instant(previous['event_at']) == event:
                previous['status'] = 'voided'
                fields['上次结果'] = encode(previous)
            self.save(con, template['id'], fields)
            return {'receipt': self.save(con, receipt_id, child), 'reminder_restored': restore}

    def backup(self, destination):
        target = Path(destination).expanduser().resolve()
        reserved = {self.path, *(Path(str(self.path) + suffix) for suffix in ['-wal', '-shm', '-journal'])}
        if target.exists() or target in reserved:
            raise JidouError('Backup destination must be a new file.')
        target.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with self.connection() as source:
            dest = sqlite3.connect(target)
            try:
                source.backup(dest)
            finally:
                dest.close()
        return {'backup': str(target)}
