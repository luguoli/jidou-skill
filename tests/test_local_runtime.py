import concurrent.futures
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/jidou.py'
NOW = '2026-11-06T08:00:00+08:00'


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='jidou-runtime-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'data'

    def command(self, *args, payload=None, now=NOW, ok=True):
        result = subprocess.run([sys.executable, str(CLI), '--home', str(self.home), '--now', now, *args],
                                input=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
                                capture_output=True, text=True, encoding='utf-8')
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result

    def init(self):
        return self.command('init', '--timezone', 'Asia/Shanghai')

    def note(self, content='想法', **fields):
        payload = {'内容': content, '原文': content, '类型': '想法', '领域': '工作', **fields}
        return self.command('add', '--input', '-', payload=payload)['records'][0]

    def test_doctor_is_readonly_before_init(self):
        report = self.command('doctor')
        self.assertFalse(report['initialized'])
        self.assertFalse(self.home.exists())

    def test_init_is_explicit_and_repeatable(self):
        first = self.init()
        second = self.init()
        self.assertEqual(first['database_id'], second['database_id'])
        self.assertTrue((self.home / 'jidou.sqlite3').is_file())

    def test_add_requires_initialization(self):
        self.command('add', '--input', '-', payload={'内容': 'x', '原文': 'x'}, ok=False)
        self.assertFalse(self.home.exists())

    def test_original_text_survives_roundtrip(self):
        self.init()
        text = '那个"周报"啊\n`$(not-a-command)`，能不能自己生成？'
        record = self.note('自动周报', 原文=text)
        saved = self.command('get', record['id'])
        self.assertEqual(saved['fields']['原文'], text)
        self.assertEqual(len(saved['fields']), 21)

    def test_operation_key_prevents_duplicate_batch(self):
        self.init()
        payload = {'records': [{'内容': 'one', '原文': 'one'}, {'内容': 'two', '原文': 'two'}]}
        first = self.command('add', '--input', '-', '--operation-id', 'same-request', payload=payload)
        second = self.command('add', '--input', '-', '--operation-id', 'same-request', payload=payload)
        self.assertEqual([x['id'] for x in first['records']], [x['id'] for x in second['records']])
        self.assertTrue(second['replayed'])
        self.assertEqual(self.command('list')['total'], 2)
        self.command('add', '--input', '-', '--operation-id', 'same-request', payload={'内容': 'different', '原文': 'different'}, ok=False)

    def test_invalid_batch_is_atomic(self):
        self.init()
        self.command('add', '--input', '-', payload={'records': [{'内容': 'good', '原文': 'good'}, {'内容': 'bad', '原文': 'bad', '类型': '不存在'}]}, ok=False)
        self.assertEqual(self.command('list')['total'], 0)

    def test_filtering_and_pagination(self):
        self.init()
        for n in range(3):
            self.note(f'条目{n}', 领域='生活' if n == 0 else '工作')
        result = self.command('list', '--domain', '工作', '--limit', '1', '--offset', '1')
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['records']), 1)

    def test_completion_only_changes_the_target(self):
        self.init()
        first = self.note('first', 类型='待办')
        second = self.note('second', 类型='待办', 线索=first['fields']['线索'])
        self.command('complete', first['id'])
        self.assertEqual(self.command('get', first['id'])['fields']['状态'], '已完成')
        self.assertEqual(self.command('get', second['id'])['fields']['状态'], '待看')

    def test_concurrent_lineage_allocation_is_unique(self):
        self.init()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            records = list(pool.map(lambda n: self.note(f'并发{n}'), range(8)))
        self.assertEqual(len({x['fields']['线索'] for x in records}), 8)

    def test_export_import_keeps_records_and_raw_text(self):
        self.init()
        self.note('quoted', 原文='引号"和\n换行')
        export = self.command('export')
        self.home = Path(self.temp.name) / 'other-data'
        self.init()
        self.command('import', '--input', '-', payload=export)
        self.assertEqual(self.command('list')['records'][0]['fields']['原文'], '引号"和\n换行')

    def test_reminder_does_not_fire_early_and_is_queued_once(self):
        self.init()
        self.note('合同', 类型='待办', 到期='2026-11-06T19:30:00+08:00', 提醒='准时')
        self.assertEqual(self.command('reminders', 'scan', now='2026-11-06T19:00:00+08:00')['queued'], 0)
        self.assertEqual(self.command('reminders', 'scan', now='2026-11-06T20:00:00+08:00')['queued'], 1)
        self.assertEqual(self.command('reminders', 'scan', now='2026-11-06T20:01:00+08:00')['queued'], 0)
        self.assertEqual(self.command('reminders', 'pending')['total'], 1)

    def test_quiet_hours_do_not_consume_the_reminder(self):
        self.init()
        record = self.note('夜间事件', 类型='事件', 到期='2026-11-06T23:00:00+08:00', 提醒='准时')
        report = self.command('reminders', 'scan', now='2026-11-06T23:05:00+08:00')
        self.assertTrue(report['quiet'])
        self.assertEqual(self.command('get', record['id'])['fields']['上次结果'], '')
        self.assertEqual(self.command('reminders', 'scan', now='2026-11-07T08:00:00+08:00')['queued'], 1)

    def test_custom_recurring_lead_keeps_event_time(self):
        self.init()
        record = self.note('交租', 类型='待办', 到期='2026-11-08T10:00:00+08:00', 提醒='准时', 重复=json.dumps({'rule': '每月8号 10:00', 'lead_minutes': 2880}))
        self.assertEqual(self.command('reminders', 'scan', now='2026-11-06T10:00:00+08:00')['queued'], 1)
        after = self.command('get', record['id'])['fields']
        self.assertEqual(after['到期'], '2026-11-08T10:00:00+08:00')
        self.assertEqual(datetime.fromisoformat(after['下次触发']).month, 12)

    def test_complete_occurrence_then_undo_does_not_end_series(self):
        self.init()
        event = '2026-11-08T10:00:00+08:00'
        record = self.note('交租', 类型='待办', 到期=event, 提醒='准时', 重复='每月8号 10:00')
        receipt = self.command('complete', record['id'], '--event-at', event)['receipt']
        self.assertEqual(self.command('get', record['id'])['fields']['状态'], '待看')
        self.assertEqual(self.command('reminders', 'scan', now=event)['queued'], 0)
        self.command('undo', receipt['id'], '--restore-reminder')
        self.assertEqual(self.command('reminders', 'scan', now=event)['queued'], 1)

    def test_correction_cancels_stale_pending_notification(self):
        self.init()
        record = self.note('合同', 类型='待办', 到期='2026-11-06T10:00:00+08:00', 提醒='准时')
        self.command('reminders', 'scan', now='2026-11-06T10:00:00+08:00')
        self.command('update', record['id'], '--input', '-', payload={'到期': '2026-11-07T10:00:00+08:00', '下次触发': '2026-11-07T10:00:00+08:00'})
        self.assertEqual(self.command('reminders', 'pending')['total'], 0)

    def test_imported_occurrence_receipt_can_be_undone(self):
        self.init()
        event = '2026-11-08T10:00:00+08:00'
        record = self.note('系列', 类型='待办', 到期=event, 提醒='准时', 重复='每月8号 10:00')
        receipt = self.command('complete', record['id'], '--event-at', event)['receipt']
        exported = self.command('export')
        self.home = Path(self.temp.name) / 'import-target'
        target = self.init()
        self.command('import', '--input', '-', payload=exported)
        imported = self.command('get', receipt['id'])
        self.assertEqual(json.loads(imported['fields']['上次结果'])['template_database_id'], target['database_id'])
        self.command('undo', receipt['id'], '--restore-reminder')
        self.assertEqual(self.command('reminders', 'scan', now=event)['queued'], 1)

    def test_paused_notifications_stay_paused_until_explicit_resume(self):
        self.init()
        self.note('事项', 类型='待办', 到期='2026-11-06T10:00:00+08:00', 提醒='准时')
        self.command('settings', 'update', '--input', '-', payload={'reminders_enabled': False})
        report = self.command('reminders', 'scan', now='2026-11-06T10:00:00+08:00')
        self.assertTrue(report['paused'])
        self.command('settings', 'update', '--input', '-', now='2026-11-06T12:00:00+08:00', payload={'reminders_enabled': True})
        self.assertEqual(self.command('reminders', 'scan', now='2026-11-06T12:00:00+08:00')['queued'], 0)

    def test_undo_cannot_restore_over_a_later_completed_occurrence(self):
        self.init()
        record = self.note('系列', 类型='待办', 到期='2026-11-08T10:00:00+08:00', 提醒='准时', 重复='每月8号 10:00')
        early = self.command('complete', record['id'], '--event-at', '2026-11-08T10:00:00+08:00')['receipt']
        self.command('complete', record['id'], '--event-at', '2026-12-08T10:00:00+08:00')
        self.command('undo', early['id'], '--restore-reminder', ok=False)
        self.assertEqual(self.command('get', record['id'])['fields']['下次触发'], '2027-01-08T10:00:00+08:00')


if __name__ == '__main__':
    unittest.main()
