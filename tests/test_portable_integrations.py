from datetime import datetime, timedelta
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from jidou_runtime.schedule import Rule, UTC, instant, localize, zone
from jidou_runtime.store import Store, default_home
from jidou_runtime import outbox


class ScheduleTests(unittest.TestCase):
    def rule(self, text, due='2026-11-06T09:00:00+08:00'):
        return Rule.fields({'重复': text, '到期': due, '提醒': '准时'}, 'Asia/Shanghai')

    def test_month_day_skips_invalid_month(self):
        result = self.rule('每月31号 09:00').next(instant('2026-01-31T09:00:00+08:00'))
        self.assertEqual(result.date().isoformat(), '2026-03-31')

    def test_month_end_uses_leap_february(self):
        result = self.rule('每月最后一天 09:00').next(instant('2028-01-31T09:00:00+08:00'))
        self.assertEqual(result.date().isoformat(), '2028-02-29')

    def test_annual_feb29(self):
        self.assertEqual(self.rule('每年2月29日 09:00').next(instant('2026-11-06T09:00:00+08:00')).year, 2028)

    def test_weekdays_and_multiple_weekdays(self):
        after = instant('2026-11-06T10:00:00+08:00')
        self.assertEqual(self.rule('每个工作日 09:00').next(after).weekday(), 0)
        self.assertEqual(self.rule('每周一、周四 20:00').next(after).weekday(), 0)

    def test_interval_and_biweekly_use_anchor(self):
        anchor = '2026-11-02T09:00:00+08:00'
        rule = self.rule(json.dumps({'rule': '每3天 09:00', 'anchor': anchor}))
        self.assertEqual(rule.next(instant('2026-11-06T10:00:00+08:00')).day, 8)
        rule = self.rule(json.dumps({'rule': '每两周的周一 09:00', 'anchor': anchor}))
        self.assertEqual(rule.next(instant('2026-11-06T10:00:00+08:00')).day, 16)

    def test_lead_is_elapsed_time_across_dst(self):
        rule = self.rule(json.dumps({'rule': None, 'lead_minutes': 1440, 'timezone': 'America/New_York'}))
        event = localize(datetime(2026, 3, 8).date(), datetime.min.time().replace(hour=9), zone('America/New_York'))
        self.assertEqual(event.astimezone(UTC) - rule.reminder_at(event).astimezone(UTC), timedelta(hours=24))

    def test_dst_gaps_and_overlaps_require_disambiguation(self):
        for day, hour in [('2026-03-08', 2), ('2026-11-01', 1)]:
            with self.subTest(day=day), self.assertRaises(ValueError):
                localize(datetime.fromisoformat(day).date(), datetime.min.time().replace(hour=hour, minute=30), zone('America/New_York'))

    def test_invalid_rule_json_and_boolean_lead_fail(self):
        for rule in ['{"rule":', json.dumps({'rule': None, 'lead_minutes': True})]:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                self.rule(rule)


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='jidou-outbox-')
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name), instant('2026-11-06T08:00:00+08:00'))
        self.store.initialize()
        self.store.add({'内容': '合同', '原文': '提醒我发合同', '类型': '待办', '领域': '工作', '到期': '2026-11-06T10:00:00+08:00', '提醒': '准时'})
        self.store.now = instant('2026-11-06T10:00:00+08:00')
        outbox.scan(self.store)

    def test_failed_transport_does_not_consume_notification(self):
        def fail(message):
            raise RuntimeError('synthetic private response must not be persisted')
        self.assertEqual(outbox.deliver(self.store, sender=fail)['failed'], 1)
        self.assertEqual(outbox.pending(self.store)['total'], 1)
        self.store.now += timedelta(minutes=6)
        sent = []
        self.assertEqual(outbox.deliver(self.store, sender=sent.append)['accepted'], 1)
        self.assertEqual(len(sent), 1)
        self.assertEqual(outbox.deliver(self.store, sender=sent.append)['accepted'], 0)

    def test_original_text_is_not_in_notification(self):
        message = outbox.pending(self.store)['notifications'][0]
        self.assertNotIn('提醒我发合同', message['body'])

    def test_acceptance_is_reflected_in_the_matching_record_receipt(self):
        record = self.store.list()['records'][0]
        outbox.deliver(self.store, sender=lambda message: None)
        marker = json.loads(self.store.get(record['id'])['fields']['上次结果'])
        self.assertEqual(marker['delivery'], 'accepted')
        outbox.scan(self.store)
        marker = json.loads(self.store.get(record['id'])['fields']['上次结果'])
        self.assertEqual(marker['delivery'], 'accepted')

    def test_corrected_content_is_used_when_delivered(self):
        record = self.store.list()['records'][0]
        self.store.update(record['id'], {'内容': '已纠正的合同事项'})
        sent = []
        outbox.deliver(self.store, sender=sent.append)
        self.assertIn('已纠正的合同事项', sent[0]['body'])

    def test_changed_event_with_same_reminder_time_has_new_identity(self):
        record = self.store.list()['records'][0]
        self.store.update(record['id'], {'重复': '每天 11:00', '到期': '2026-11-06T11:00:00+08:00', '下次触发': '2026-11-06T11:00:00+08:00', '提醒': '提前1小时'})
        outbox.scan(self.store)
        self.store.occurrence(record['id'], '2026-11-06T11:00:00+08:00')
        self.assertEqual(outbox.pending(self.store)['total'], 0)

    def test_real_clock_is_read_again_for_long_running_workers(self):
        first = instant('2026-11-06T10:00:00+08:00')
        later = first + timedelta(minutes=5)
        with patch('jidou_runtime.store.datetime') as clock:
            clock.now.side_effect = [first, later]
            store = Store(Path(self.temp.name))
            self.assertLess(store.now, store.now)

    def test_backup_rejects_sqlite_reserved_sidecars(self):
        for suffix in ['-wal', '-shm', '-journal']:
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                self.store.backup(str(self.store.path) + suffix)

    def test_delivery_rechecks_quiet_hours_during_a_batch(self):
        self.store.add({'内容': '另一项', '原文': '另一项', '类型': '待办', '到期': '2026-11-06T21:59:00+08:00', '提醒': '准时'})
        self.store.now = instant('2026-11-06T21:59:00+08:00')
        outbox.scan(self.store)
        sent = []
        def sender(message):
            sent.append(message)
            self.store.now = instant('2026-11-06T22:01:00+08:00')
        result = outbox.deliver(self.store, sender=sender)
        self.assertEqual(result['accepted'], 1)
        self.assertEqual(len(sent), 1)
        self.assertEqual(outbox.pending(self.store)['total'], 1)

    def test_stale_recurrence_can_fire_exactly_at_activation(self):
        record = self.store.add({'内容': 'stale cursor', '原文': 'stale cursor', '类型': '待办', '到期': '2026-11-05T08:00:00+08:00', '下次触发': '2026-11-05T08:00:00+08:00', '重复': '每天 08:00', '提醒': '准时'})['records'][0]
        self.store.now = instant('2026-11-06T08:00:00+08:00')
        report = outbox.scan(self.store)
        self.assertTrue(any(item['key'].split('/')[1] == record['id'] for item in report['notifications']))

    def test_windows_notification_uses_static_code_and_stdin_payload(self):
        with patch('jidou_runtime.outbox.sys.platform', 'win32'), patch('jidou_runtime.outbox.subprocess.run') as run:
            run.return_value.returncode = 0
            outbox.send_system('记兜', 'literal "; $(not-code)')
            args, kwargs = run.call_args
            self.assertNotIn('not-code', ' '.join(args[0]))
            self.assertEqual(json.loads(kwargs['input'])['body'], 'literal "; $(not-code)')


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='jidou-install-')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'Project With Spaces'
        self.home = Path(self.temp.name) / 'data'

    def command(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/jidou.py'), '--home', str(self.home), *args], capture_output=True, text=True, encoding='utf-8')
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def test_agent_install_plan_is_readonly(self):
        for agent, parent in [('codex', '.agents'), ('claude', '.claude'), ('trae', '.trae')]:
            report = self.command('install', '--agent', agent, '--scope', 'project', '--project', str(self.project))
            self.assertEqual(Path(report['destination']).resolve(), (self.project / parent / 'skills/jidou').resolve())
            self.assertFalse(self.project.exists())
        self.assertFalse(self.home.exists())

    def test_install_copies_whole_package_without_data(self):
        report = self.command('install', '--agent', 'codex', '--scope', 'project', '--project', str(self.project), '--apply')
        destination = Path(report['destination'])
        for name in ['SKILL.md', 'references/schema.json', 'scripts/jidou.py', 'requirements.txt']:
            self.assertTrue((destination / name).is_file())
        self.assertFalse((destination / 'archive').exists())
        self.assertFalse((destination / 'jidou.sqlite3').exists())
        self.assertFalse(self.home.exists())

    def test_unmanaged_install_directory_is_not_overwritten(self):
        destination = self.project / '.claude/skills/jidou'
        destination.mkdir(parents=True)
        (destination / 'user.txt').write_text('keep me', encoding='utf-8')
        self.command('install', '--agent', 'claude', '--scope', 'project', '--project', str(self.project), '--apply', ok=False)
        self.assertEqual((destination / 'user.txt').read_text(encoding='utf-8'), 'keep me')

    def test_installed_english_package_has_no_broken_document_routes(self):
        for agent in ['codex', 'claude', 'trae']:
            with self.subTest(agent=agent):
                report = self.command('install', '--agent', agent, '--scope', 'project', '--project', str(self.project), '--apply')
                destination = Path(report['destination'])
                checked = subprocess.run([sys.executable, str(destination / 'scripts/validate.py')], capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_os_user_data_paths(self):
        root = Path(self.temp.name)
        self.assertEqual(default_home('darwin', {}, root), root / 'Library/Application Support/jidou')
        self.assertEqual(default_home('linux', {'XDG_DATA_HOME': str(root / 'xdg')}, root), root / 'xdg/jidou')
        self.assertEqual(default_home('win32', {'LOCALAPPDATA': str(root / 'local')}, root), root / 'local/jidou')

    def test_scheduler_plans_do_not_register_tasks(self):
        self.command('init')
        windows = self.command('scheduler', 'plan', '--platform', 'windows')
        argv = windows['commands'][0]
        self.assertIn('/IT', argv)
        self.assertNotIn('/F', argv)
        self.assertIn('schtasks.exe', argv[0])
        mac = self.command('scheduler', 'plan', '--platform', 'darwin')
        plist = plistlib.loads(mac['files'][0]['content'].encode('utf-8'))
        self.assertEqual(plist['StartInterval'], 60)
        self.assertIsInstance(plist['ProgramArguments'], list)
        self.assertIn('jidou.py', plist['ProgramArguments'][1])
        self.assertFalse((self.home / 'scheduler').exists())


if __name__ == '__main__':
    unittest.main()
