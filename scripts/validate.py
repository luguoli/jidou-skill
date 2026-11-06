#!/usr/bin/env python3
"""Check jidou package invariants using only the Python standard library."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

from render import ROOT, RenderError, render, version

EXPECTED_FIELDS = '内容 类型 标签 线索 记录时间 状态 到期 提醒 重复 下次触发 静音至 完成于 执行 执行内容 任务ID 上次结果 领域 优先级 相关人 来源 原文'.split()


def validate(root: Path = ROOT) -> list[str]:
    errors = []
    skill = (root / 'SKILL.md').read_text(encoding='utf-8')
    front = re.match(r'\A---\n(.*?)\n---\n', skill, re.S)
    if not front:
        return ['SKILL.md has no delimited frontmatter.']
    keys = re.findall(r'^([A-Za-z][\w-]*):', front.group(1), re.M)
    if len(keys) != len(set(keys)) or not {'name', 'description'} <= set(keys) or set(keys) - {'name', 'description', 'license', 'metadata', 'allowed-tools'}:
        errors.append('Frontmatter top-level keys are nonstandard, missing or duplicated.')
    if not re.search(r'^name: jidou$', front.group(1), re.M) or not re.search(r'^description: >-\n  \S', front.group(1), re.M):
        errors.append('Name or folded description is invalid.')
    current = version(root)
    changelog = (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    if re.search(r'^## (\d+\.\d+\.\d+)', changelog, re.M).group(1) != current:
        errors.append('Changelog latest version differs from metadata.')
    readme = (root / 'README.md').read_text(encoding='utf-8')
    if f'**{current}**' not in readme or 'https://github.com/luguoli/jidou-skill.git ~/.codebuddy/skills/jidou' not in readme:
        errors.append('README version or installation name differs.')
    if len(skill.splitlines()) > 200:
        errors.append('SKILL.md exceeds the maintained 200-line entrypoint budget.')
    data = json.loads((root / 'references/schema.json').read_text(encoding='utf-8'))['schema']
    props = data['properties']
    if [p['name'] for p in props] != EXPECTED_FIELDS:
        errors.append('The existing 21 field names/order changed.')
    counts = {'类型': 10, '状态': 4, '提醒': 7, '执行': 5, '领域': 6, '优先级': 3}
    for prop in props:
        if len(prop['config']) != 1:
            errors.append('A field has ambiguous type configuration.')
        if prop['name'] in counts:
            options = prop['config'].get('select', {}).get('options', [])
            if len(options) != counts[prop['name']] or len({x['text'] for x in options}) != len(options):
                errors.append(f'Invalid select options: {prop["name"]}.')
    model = (root / 'references/data-model.md').read_text(encoding='utf-8')
    rows = re.findall(r'^\| ([^|\n]+?) \| (?:text|select|date) \|', model, re.M)
    if rows != EXPECTED_FIELDS:
        errors.append('Field semantics table differs from schema order.')
    for path in [root / 'SKILL.md', root / 'README.md', *(root / 'references').glob('*.md')]:
        text = path.read_text(encoding='utf-8')
        for raw in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in raw or raw.startswith('#'):
                continue
            target, _, fragment = unquote(raw).partition('#')
            dest = (path.parent / target).resolve()
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
