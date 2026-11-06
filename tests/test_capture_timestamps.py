import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from jidou_runtime.schedule import instant
from jidou_runtime.store import Store


class CaptureTimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='jidou-capture-time-')
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'data', instant('2026-11-07T00:15:16.987654+00:00'))
        self.store.initialize('Asia/Shanghai')

    def note(self, text='note', **fields):
        return self.store.add({'内容': text, '原文': text, **fields})['records'][0]

    def legacy(self, day, text='legacy'):
        # A real exported record from an older version, with date-only precision.
        payload = {'jidou_export': 1, 'database_id': 'older-database', 'records': [{'id': text, 'fields': {'内容': text, '原文': text, '记录时间': day}}]}
        self.store.import_records(payload)
        return self.store.get(text)

    def test_new_capture_has_offset_and_second_precision_in_user_timezone(self):
        record = self.note()
        self.assertEqual(record['fields']['记录时间'], '2026-11-07T08:15:16+08:00')

    def test_explicit_timestamp_is_normalized_to_seconds(self):
        record = self.note(记录时间='2026-11-06T23:59:58.123456-05:00')
        self.assertEqual(record['fields']['记录时间'], '2026-11-06T23:59:58-05:00')

    def test_new_date_only_and_naive_capture_times_are_rejected(self):
        for value in ['2026-11-07', '2026-11-07T08:00:00']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.note(记录时间=value)
        self.assertEqual(self.store.list()['total'], 0)

    def test_updates_keep_capture_time_including_legacy_precision(self):
        record = self.note()
        legacy = self.legacy('2026-11-06')
        self.store.now = instant('2026-11-09T10:20:30+08:00')
        for original in [record, legacy]:
            changed = self.store.update(original['id'], {'内容': 'corrected'})
            self.assertEqual(changed['fields']['记录时间'], original['fields']['记录时间'])
        with self.assertRaises(ValueError):
            self.store.update(record['id'], {'记录时间': ''})

    def test_import_and_export_preserve_old_date_and_unknown_time(self):
        for day, name in [('2026-11-06', 'date-only'), ('', 'unknown')]:
            self.legacy(day, name)
        exported = self.store.export()
        self.assertEqual({r['id']: r['fields']['记录时间'] for r in exported['records']}, {'date-only': '2026-11-06', 'unknown': ''})

    def test_day_filter_uses_local_calendar_day_not_timestamp_prefix(self):
        included = [self.note('start', 记录时间='2026-11-06T16:00:00+00:00')['id'], self.note('end', 记录时间='2026-11-07T15:59:59+00:00')['id'], self.legacy('2026-11-07')['id']]
        self.note('before', 记录时间='2026-11-06T15:59:59+00:00')
        self.note('after', 记录时间='2026-11-07T16:00:00+00:00')
        self.legacy('', 'unknown')
        result = self.store.list(recorded_on='2026-11-07')
        self.assertEqual({r['id'] for r in result['records']}, set(included))
        # Preserve the old API's exact-date filter as a day query.
        self.assertEqual(self.store.list(filters={'记录时间': '2026-11-07'})['total'], 3)

    def test_range_filter_is_inclusive_and_combines_with_search_and_pagination(self):
        for day in ['2026-11-06', '2026-11-07', '2026-11-08']:
            self.note('meeting', 领域='工作', 记录时间=day + 'T09:00:00+08:00')
        self.note('other', 领域='生活', 记录时间='2026-11-07T09:00:00+08:00')
        result = self.store.list(filters={'领域': '工作'}, query='meeting', date_from='2026-11-06', date_to='2026-11-07', limit=1, offset=1)
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['records']), 1)

    def test_dst_short_and_long_days_include_all_occurrences(self):
        cases = [
            ('2026-03-08', ['2026-03-08T05:00:00Z', '2026-03-09T03:59:59Z'], ['2026-03-08T04:59:59Z', '2026-03-09T04:00:00Z']),
            ('2026-11-01', ['2026-11-01T04:00:00Z', '2026-11-01T05:30:00Z', '2026-11-01T06:30:00Z', '2026-11-02T04:59:59Z'], ['2026-11-01T03:59:59Z', '2026-11-02T05:00:00Z']),
        ]
        for day, included, excluded in cases:
            with self.subTest(day=day):
                ids = {self.note(value, 记录时间=value)['id'] for value in included}
                for value in excluded:
                    self.note(value, 记录时间=value)
                before = self.store.settings()['timezone']
                found = self.store.list(recorded_on=day, timezone_name='America/New_York')
                self.assertEqual({r['id'] for r in found['records']}, ids)
                self.assertEqual(self.store.settings()['timezone'], before)

    def test_invalid_or_conflicting_ranges_fail_clearly(self):
        for kwargs in [dict(recorded_on='2026-02-30'), dict(date_from='2026-11-08', date_to='2026-11-07'), dict(recorded_on='2026-11-07', date_to='2026-11-08'), dict(recorded_on='2026-11-07', timezone_name='Invalid/Zone')]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.store.list(**kwargs)

    def test_cli_supports_day_range_and_timezone_queries(self):
        self.note('boundary', 记录时间='2026-11-06T16:00:00Z')
        for args, expected in [(['--date', '2026-11-07'], 1), (['--date', '2026-11-06', '--timezone', 'UTC'], 1), (['--from-date', '2026-11-07', '--to-date', '2026-11-07'], 1), (['--date', '2026-11-08'], 0)]:
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/jidou.py'), '--home', str(self.store.home), 'list', *args], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['total'], expected)


if __name__ == '__main__':
    unittest.main()
