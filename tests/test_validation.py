from contextlib import contextmanager
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render import RenderError, render, version
from validate import validate


@contextmanager
def package_copy():
    with tempfile.TemporaryDirectory(prefix='jidou-validation-') as directory:
        root = Path(directory) / 'jidou'
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'archive', '__pycache__', '*.pyc'))
        yield root


class ValidationRegressionTests(unittest.TestCase):
    def test_english_readme_version_drift_is_detected(self):
        with package_copy() as root:
            path = root / 'README.en.md'
            path.write_text(path.read_text(encoding='utf-8').replace('**' + version(root) + '**', '**99.0.0**'), encoding='utf-8')
            self.assertTrue(any('README.en.md' in error for error in validate(root)))

    def test_english_readme_broken_link_is_detected(self):
        with package_copy() as root:
            path = root / 'README.en.md'
            path.write_text(path.read_text(encoding='utf-8') + '\n[missing](missing-english-guide.md)\n', encoding='utf-8')
            self.assertTrue(any('missing-english-guide.md' in error for error in validate(root)))

    def config(self, **changes):
        context = {'SPACE_ID': 'space', 'FOLDER_ID': 'folder', 'DATABASE_ID': 'db', 'TODAY': '2026-11-06', 'INIT_MODE': '测试'}
        context.update(changes)
        return context

    def test_invalid_yaml_is_reported(self):
        with package_copy() as root:
            path = root / 'SKILL.md'
            path.write_text(path.read_text(encoding='utf-8').replace('license: MIT', 'license: [MIT'), encoding='utf-8')
            self.assertTrue(any('YAML' in error for error in validate(root)))

    def test_duplicate_nested_yaml_keys_are_reported(self):
        with package_copy() as root:
            path = root / 'SKILL.md'
            text = path.read_text(encoding='utf-8')
            text = re.sub(r'(  version: "[^"]+"\n)', r'\1  version: "99.0.0"\n', text, count=1)
            path.write_text(text, encoding='utf-8')
            self.assertTrue(any('YAML' in error for error in validate(root)))

    def test_valid_yaml_scalar_styles_are_accepted(self):
        for style in ['single', 'plain']:
            with self.subTest(style=style), package_copy() as root:
                path = root / 'SKILL.md'
                text = path.read_text(encoding='utf-8')
                text = re.sub(r'description: >-\n(?:  .*\n)+', 'description: "Capture and recall personal notes."\n', text, count=1)
                text = re.sub(r'  version: "([^"]+)"', r"  version: '\1'" if style == 'single' else r'  version: \1', text, count=1)
                path.write_text(text, encoding='utf-8')
                self.assertEqual(validate(root), [])

    def test_field_type_change_is_detected(self):
        with package_copy() as root:
            path = root / 'references/schema.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            next(p for p in data['schema']['properties'] if p['name'] == '到期')['config'] = {'text': ''}
            path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            self.assertTrue(validate(root))

    def test_same_count_enum_rename_is_detected(self):
        with package_copy() as root:
            path = root / 'references/schema.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            next(p for p in data['schema']['properties'] if p['name'] == '提醒')['config']['select']['options'][0]['text'] = '错误枚举'
            path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            self.assertTrue(validate(root))

    def test_field_semantic_table_type_drift_is_detected(self):
        with package_copy() as root:
            path = root / 'references/data-model.md'
            path.write_text(path.read_text(encoding='utf-8').replace('| 到期 | date |', '| 到期 | text |'), encoding='utf-8')
            self.assertTrue(validate(root))

    def test_same_document_missing_anchor_is_detected(self):
        with package_copy() as root:
            path = root / 'SKILL.md'
            path.write_text(path.read_text(encoding='utf-8') + '\n[broken](#does-not-exist)\n', encoding='utf-8')
            self.assertTrue(validate(root))

    def test_supplied_optional_id_placeholders_are_rejected(self):
        for field in ['TASK_ID', 'FOLDER_BACKUP_ID', 'FOLDER_ARCHIVE_ID']:
            with self.subTest(field=field), self.assertRaises(RenderError):
                render('config', self.config(**{field: '<实际ID>'}))

    def test_enabled_config_rejects_placeholder_task(self):
        with self.assertRaises(RenderError):
            render('config', self.config(REMINDER_STATUS='enabled', TASK_ID='<实际任务ID>', REMINDER_START_AT='2026-11-06T08:00:00+08:00'))

    def test_nonexistent_timezone_rejected(self):
        with self.assertRaises(RenderError):
            render('config', self.config(TIMEZONE='Mars/Olympus_Mons'))

    def test_context_controls_are_rejected(self):
        for value in ['db\x00id', 'db\x1bid', 'db\u2028id']:
            with self.subTest(value=repr(value)), self.assertRaises(RenderError):
                render('config', self.config(DATABASE_ID=value))

    def test_whitespace_optional_task_is_rejected(self):
        with self.assertRaises(RenderError):
            render('config', self.config(REMINDER_STATUS='enabled', TASK_ID='   ', REMINDER_START_AT='2026-11-06T08:00:00+08:00'))

    def test_yaml_constructor_is_not_executed(self):
        with package_copy() as root, patch('os.system') as system:
            path = root / 'SKILL.md'
            text = path.read_text(encoding='utf-8').replace('license: MIT', 'license: !!python/object/apply:os.system ["echo synthetic"]')
            path.write_text(text, encoding='utf-8')
            self.assertTrue(any('YAML' in error for error in validate(root)))
            system.assert_not_called()

    def test_yaml_dependency_failure_is_actionable(self):
        with patch('frontmatter.yaml', None), self.assertRaisesRegex(RenderError, 'requirements.txt'):
            render('config', self.config())

    def test_missing_timezone_database_is_actionable(self):
        from zoneinfo import ZoneInfoNotFoundError
        with patch('render.ZoneInfo', side_effect=ZoneInfoNotFoundError), self.assertRaisesRegex(RenderError, 'tzdata'):
            render('config', self.config())


if __name__ == '__main__':
    unittest.main()
