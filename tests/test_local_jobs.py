import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='jidou-jobs-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'data'
        self.command('init')

    def command(self, *args, payload=None, now='2026-11-06T08:00:00+08:00', ok=True):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/jidou.py'), '--home', str(self.home), '--now', now, *args], input=json.dumps(payload) if payload is not None else None, capture_output=True, text=True, encoding='utf-8')
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def recipe(self, **changes):
        return {'name': 'synthetic command', 'argv': [sys.executable, '-c', 'print("synthetic")'], 'run_at': '2026-11-06T10:00:00+08:00', **changes}

    def test_explicit_argv_job_runs_once(self):
        job = self.command('job', 'add', '--input', '-', payload=self.recipe())
        self.assertEqual(job['record']['fields']['类型'], '定时')
        self.assertEqual(self.command('job', 'tick', now='2026-11-06T09:00:00+08:00')['runs'], [])
        result = self.command('job', 'tick', now='2026-11-06T10:00:00+08:00')
        self.assertEqual(result['runs'][0]['status'], 'success')
        self.assertEqual(self.command('job', 'tick', now='2026-11-06T10:01:00+08:00')['runs'], [])
        record = self.command('get', job['record']['id'])
        self.assertEqual(record['fields']['状态'], '已完成')

    def test_archiving_a_job_record_stops_future_execution(self):
        job = self.command('job', 'add', '--input', '-', payload=self.recipe())
        self.command('update', job['record']['id'], '--input', '-', payload={'状态': '归档'})
        self.assertEqual(self.command('job', 'tick', now='2026-11-06T10:00:00+08:00')['runs'], [])

    def test_job_recipe_cannot_be_silently_changed_via_record_update(self):
        job = self.command('job', 'add', '--input', '-', payload=self.recipe())
        self.command('update', job['record']['id'], '--input', '-', payload={'执行': '', '执行内容': ''}, ok=False)

    def test_disabled_job_is_not_executed(self):
        job = self.command('job', 'add', '--input', '-', payload=self.recipe())
        self.command('job', 'disable', job['job_id'])
        self.assertEqual(self.command('job', 'tick', now='2026-11-06T10:00:00+08:00')['runs'], [])

    def test_shell_string_is_not_accepted_as_argv(self):
        self.command('job', 'add', '--input', '-', payload=self.recipe(argv='echo bad && echo worse'), ok=False)

    def test_failed_command_has_no_automatic_retry(self):
        self.command('job', 'add', '--input', '-', payload=self.recipe(argv=[sys.executable, '-c', 'raise SystemExit(4)']))
        result = self.command('job', 'tick', now='2026-11-06T10:00:00+08:00')
        self.assertEqual(result['runs'][0]['status'], 'failed')
        self.assertEqual(self.command('job', 'tick', now='2026-11-06T10:01:00+08:00')['runs'], [])

    def test_program_output_is_not_persisted_as_a_receipt(self):
        job = self.command('job', 'add', '--input', '-', payload=self.recipe(argv=[sys.executable, '-c', 'print("synthetic-secret-output")']))
        self.command('job', 'tick', now='2026-11-06T10:00:00+08:00')
        record = self.command('get', job['record']['id'])
        self.assertNotIn('synthetic-secret-output', record['fields']['上次结果'])

    def test_job_run_history_contains_the_actual_result(self):
        job = self.command('job', 'add', '--input', '-', payload=self.recipe())
        self.command('job', 'tick', now='2026-11-06T10:00:00+08:00')
        result = self.command('job', 'runs', '--job', job['job_id'])
        self.assertEqual(result['runs'][0]['status'], 'success')

    def test_timed_out_job_requires_resolution_and_is_not_replayed(self):
        job = self.command('job', 'add', '--input', '-', payload=self.recipe(argv=[sys.executable, '-c', 'import time; time.sleep(3)'], timeout_seconds=1))
        result = self.command('job', 'tick', now='2026-11-06T10:00:00+08:00')
        run = result['runs'][0]
        self.assertEqual(run['status'], 'unknown')
        self.assertEqual(self.command('doctor')['uncertain_job_runs'], 1)
        self.assertEqual(self.command('job', 'tick', now='2026-11-06T10:01:00+08:00')['runs'], [])
        resolved = self.command('job', 'resolve', run['run_id'], '--status', 'success', now='2026-11-06T10:02:00+08:00')
        self.assertFalse(resolved['executed_again'])
        self.assertEqual(self.command('get', job['record']['id'])['fields']['状态'], '已完成')


if __name__ == '__main__':
    unittest.main()
