import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render import RenderError, render
from validate import EXPECTED_FIELDS, validate


class TemplateTests(unittest.TestCase):
    def config(self, **changes):
        context = {'SPACE_ID': 'test-space', 'FOLDER_ID': 'test-folder', 'DATABASE_ID': 'test-db', 'TODAY': '2026-11-06', 'INIT_MODE': '接回存量'}
        context.update(changes)
        return context

    def reminder(self, **changes):
        context = {'DATABASE_ID': 'test-db', 'SKILLS_DIR': "/opt/jidou skills/O'Brien", 'REMINDER_START_AT': '2026-11-06T08:00:00+08:00'}
        context.update(changes)
        return context

    def test_package_invariants(self):
        self.assertEqual(validate(), [])

    def test_schema_replacement_does_not_change_fields(self):
        result = json.loads(render('schema', {'SPACE_ID': 'space-一', 'FOLDER_ID': 'folder-一'}))['schema']
        self.assertEqual([p['name'] for p in result['properties']], EXPECTED_FIELDS)
        self.assertEqual(result['space_id'], 'space-一')
        self.assertEqual(result['parent_id'], 'folder-一')

    def test_schema_json_escapes_quotes(self):
        result = json.loads(render('schema', {'SPACE_ID': 'space"quote', 'FOLDER_ID': 'folder\\path'}))
        self.assertEqual(result['schema']['space_id'], 'space"quote')
        self.assertEqual(result['schema']['parent_id'], 'folder\\path')

    def test_config_without_scheduler_or_optional_folders(self):
        output = render('config', self.config())
        self.assertIn('| task_id_reminder |  |', output)
        self.assertIn('| reminder_status | disabled |', output)
        self.assertIn('| active_database_ids | ["test-db"] |', output)

    def test_enabled_config_requires_real_task_and_start(self):
        with self.assertRaises(RenderError):
            render('config', self.config(REMINDER_STATUS='enabled'))

    def test_full_enabled_config(self):
        output = render('config', self.config(REMINDER_STATUS='enabled', TASK_ID='test-task', REMINDER_START_AT='2026-11-06T08:00:00+08:00'))
        self.assertIn('| reminder_status | enabled |', output)

    def test_background_prompt_includes_entire_protocol(self):
        output = render('reminder', self.reminder())
        rules = (ROOT / 'references/reminder-rules.md').read_text(encoding='utf-8').strip()
        self.assertIn(rules, output)
        self.assertIn('原文', output)
        self.assertNotIn('__REMINDER_RULES__', output)

    def test_shell_path_quotes_round_trip(self):
        context = self.reminder()
        output = render('reminder', context)
        command = next(line for line in output.splitlines() if line.startswith('cd '))
        self.assertEqual(shlex.split(command.split(' || ', 1)[0]), ['cd', context['SKILLS_DIR'] + '/library/database'])
        self.assertTrue(command.endswith(' || exit 1'))

    def test_database_ids_are_quoted_for_shell(self):
        output = render('reminder', self.reminder(DATABASE_ID="db'; echo unsafe", DATABASE_IDS=["db'; echo unsafe", 'old-db']))
        line = next(line for line in output.splitlines() if line.startswith('for database_id'))
        tokens = shlex.split(line)
        self.assertIn("db'; echo unsafe", tokens)
        self.assertIn('old-db;', tokens)

    def test_multiple_active_tables_in_embedded_prompt(self):
        output = render('reminder', self.reminder(DATABASE_IDS=['test-db', 'previous-year-db']))
        self.assertIn('["test-db", "previous-year-db"]', output)

    def test_duplicate_or_missing_primary_database_rejected(self):
        for ids in [[], ['test-db', 'test-db'], ['old-db'], 'test-db']:
            with self.subTest(ids=ids), self.assertRaises(RenderError):
                render('reminder', self.reminder(DATABASE_IDS=ids))

    def test_missing_values_and_unresolved_placeholders_rejected(self):
        for value in ['', '<实际ID>', '__DATABASE_ID__']:
            with self.subTest(value=value), self.assertRaises(RenderError):
                render('reminder', self.reminder(DATABASE_ID=value))

    def test_multiline_or_markdown_table_context_rejected(self):
        for value in ['multi\nline', 'bad|table', 'tab\tvalue']:
            with self.subTest(value=value), self.assertRaises(RenderError):
                render('config', self.config(INIT_MODE=value))

    def test_naive_or_invalid_start_rejected(self):
        for value in ['2026-11-06T08:00:00', 'not-a-date']:
            with self.subTest(value=value), self.assertRaises(RenderError):
                render('reminder', self.reminder(REMINDER_START_AT=value))

    def test_relative_background_path_rejected(self):
        with self.assertRaises(RenderError):
            render('reminder', self.reminder(SKILLS_DIR='./skills'))

    def test_windows_background_requires_native_adapter(self):
        with self.assertRaises(RenderError):
            render('reminder', self.reminder(SKILLS_DIR='D:\\skills'))

    def test_custom_policy_settings(self):
        output = render('reminder', self.reminder(QUIET_START_HOUR=23, QUIET_END_HOUR=7, CATCHUP_HOURS=12))
        self.assertIn('23:00–7:00', output)
        self.assertIn('补发窗口小时数：12', output)
        config = render('config', self.config(QUIET_START_HOUR=23, QUIET_END_HOUR=7, CATCHUP_HOURS=12))
        self.assertIn('| quiet_start_hour | 23 |', config)
        self.assertIn('| quiet_end_hour | 7 |', config)
        self.assertIn('| catchup_hours | 12 |', config)
        for changes in [{'QUIET_START_HOUR': True}, {'QUIET_END_HOUR': 24}, {'CATCHUP_HOURS': 0}]:
            with self.subTest(changes=changes), self.assertRaises(RenderError):
                render('reminder', self.reminder(**changes))

    def test_invalid_json_does_not_leak_values(self):
        with tempfile.TemporaryDirectory(prefix='jidou-test-') as directory:
            path = Path(directory) / 'context.json'
            path.write_text('{"private":"do-not-print-this-secret"', encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/render.py'), 'config', '--context', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertNotIn('do-not-print-this-secret', result.stderr)

    def test_unknown_keys_are_not_accepted(self):
        with self.assertRaises(RenderError):
            render('config', self.config(SECRET='never rendered'))

    def test_empty_timezone_rejected(self):
        with self.assertRaises(RenderError):
            render('reminder', self.reminder(TIMEZONE=''))


if __name__ == '__main__':
    unittest.main()
