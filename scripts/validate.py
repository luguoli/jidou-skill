#!/usr/bin/env python3
"""Check jidou metadata syntax, immutable schema contract and package invariants."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re
import sys
from urllib.parse import unquote

from render import ROOT, RenderError, render, version
from frontmatter import SkillFormatError, load_skill

EXPECTED_FIELDS = '内容 类型 标签 线索 记录时间 状态 到期 提醒 重复 下次触发 静音至 完成于 执行 执行内容 任务ID 上次结果 领域 优先级 相关人 来源 原文'.split()
# Fingerprint of the v2.11.1 properties contract, not a second runtime schema.
# Change only alongside an explicitly reviewed schema migration.
SCHEMA_CONTRACT_SHA256 = '199fa106ad70d8428f23cf9feb57d40fbbdfd841904689b343c2abfa924a477a'


def validate(root: Path = ROOT) -> list[str]:
    errors = []
    skill = (root / 'SKILL.md').read_text(encoding='utf-8')
    try:
        front, body = load_skill(root / 'SKILL.md')
        current = version(root)
    except (SkillFormatError, RenderError) as error:
        return [str(error)]
    keys = set(front)
    if not {'name', 'description'} <= keys or keys - {'name', 'description', 'license', 'metadata', 'allowed-tools'}:
        errors.append('Frontmatter top-level keys are nonstandard or missing.')
    description = front.get('description')
    if front.get('name') != 'jidou' or not isinstance(description, str) or not description.strip() or len(description) > 1024 or '<' in description or '>' in description:
        errors.append('Name or description is invalid.')
    if 'license' in front and not isinstance(front['license'], str):
        errors.append('license must be a string.')
    metadata = front.get('metadata')
    if not isinstance(metadata, dict) or any(not isinstance(value, str) for value in metadata.values()):
        errors.append('metadata must map string keys to string values.')
    if not body.strip():
        errors.append('SKILL.md needs a Markdown instruction body after frontmatter.')
    changelog = (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    if re.search(r'^## (\d+\.\d+\.\d+)', changelog, re.M).group(1) != current:
        errors.append('Changelog latest version differs from metadata.')
    readme = (root / 'README.md').read_text(encoding='utf-8')
    if f'**{current}**' not in readme or 'https://github.com/luguoli/jidou-skill.git' not in readme or 'install --agent codex' not in readme:
        errors.append('README version or installation name differs.')
    if len(skill.splitlines()) > 200:
        errors.append('SKILL.md exceeds the maintained 200-line entrypoint budget.')
    data = json.loads((root / 'references/schema.json').read_text(encoding='utf-8'))['schema']
    props = data['properties']
    if [p['name'] for p in props] != EXPECTED_FIELDS:
        errors.append('The existing 21 field names/order changed.')
    digest = hashlib.sha256(json.dumps(props, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    if digest != SCHEMA_CONTRACT_SHA256:
        errors.append('Schema compatibility contract changed: field types, order, enum text/options or date formats differ.')
    counts = {'类型': 10, '状态': 4, '提醒': 7, '执行': 5, '领域': 6, '优先级': 3}
    for prop in props:
        if len(prop['config']) != 1:
            errors.append('A field has ambiguous type configuration.')
        if prop['name'] in counts:
            options = prop['config'].get('select', {}).get('options', [])
            if len(options) != counts[prop['name']] or len({x['text'] for x in options}) != len(options):
                errors.append(f'Invalid select options: {prop["name"]}.')
    model = (root / 'references/data-model.md').read_text(encoding='utf-8')
    rows = re.findall(r'^\| ([^|\n]+?) \| (text|select|date) \|', model, re.M)
    expected_rows = [(prop['name'], next(iter(prop['config']))) for prop in props]
    if rows != expected_rows:
        errors.append('Field semantics table names/types differ from schema order/types.')
    for path in [root / 'SKILL.md', root / 'README.md', *(root / 'references').glob('*.md')]:
        text = path.read_text(encoding='utf-8')
        for raw in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in raw:
                continue
            target, _, fragment = unquote(raw).partition('#')
            dest = (path.parent / target).resolve() if target else path.resolve()
            if not dest.is_relative_to(root.resolve()) or not dest.is_file():
                errors.append(f'Broken/outside relative link in {path.relative_to(root)}: {raw}.')
            elif fragment:
                headings = re.findall(r'^#{1,6} (.+)$', dest.read_text(encoding='utf-8'), re.M)
                anchors = [re.sub(r'[^\w\-\s]', '', heading.lower()).replace(' ', '-') for heading in headings]
                if fragment not in anchors:
                    errors.append(f'Missing heading anchor in {path.relative_to(root)}: {raw}.')
    defaults = json.loads((root / 'references/defaults.json').read_text(encoding='utf-8'))['reminder']
    if len(defaults['cron'].split()) != 6 or defaults['retry_count'] != 0:
        errors.append('Reminder cron/retry defaults need explicit compatibility review.')
    fixture = {'SPACE_ID': 'synthetic-space', 'FOLDER_ID': 'synthetic-folder', 'DATABASE_ID': 'synthetic-db', 'TODAY': '2026-11-06', 'INIT_MODE': 'synthetic test', 'SKILLS_DIR': '/opt/synthetic skills', 'REMINDER_START_AT': '2026-11-06T08:00:00+08:00'}
    for kind in ['schema', 'config', 'reminder']:
        try:
            render(kind, fixture, root)
        except RenderError as error:
            errors.append(f'Template {kind} does not render: {error}')
    return errors


if __name__ == '__main__':
    try:
        problems = validate()
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f'FAIL: Invalid package structure ({type(error).__name__}).')
        raise SystemExit(1)
    if problems:
        print('\n'.join('FAIL: ' + problem for problem in problems))
        raise SystemExit(1)
    print('PASS: metadata, version, 21-field compatibility, relative links, defaults and all template renders.')
