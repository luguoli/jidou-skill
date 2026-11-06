#!/usr/bin/env python3
"""Render jidou templates, using the POSIX reminder adapter. No network or mutations."""
from __future__ import annotations

import argparse
from datetime import date, datetime
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'__([A-Z_]+)__')
TEMPLATES = {'schema': 'schema.json', 'config': 'config-doc.md', 'reminder': 'reminder-prompt.md'}
INPUTS = {
    'SPACE_ID', 'DATABASE_ID', 'DATABASE_IDS', 'FOLDER_ID', 'FOLDER_BACKUP_ID',
    'FOLDER_ARCHIVE_ID', 'TASK_ID', 'TODAY', 'INIT_MODE', 'TIMEZONE', 'SKILLS_DIR',
    'REMINDER_START_AT', 'REMINDER_STATUS', 'QUIET_START_HOUR', 'QUIET_END_HOUR', 'CATCHUP_HOURS',
}


class RenderError(ValueError):
    """Safe diagnostic that never includes context values."""


def version(root: Path = ROOT) -> str:
    text = (root / 'SKILL.md').read_text(encoding='utf-8')
    match = re.search(r'^  version: "(\d+\.\d+\.\d+)"$', text, re.M)
    if not match:
        raise RenderError('Skill metadata version is missing or invalid.')
    return match.group(1)


def render(kind: str, context: dict, root: Path = ROOT) -> str:
    if kind not in TEMPLATES or not isinstance(context, dict):
        raise RenderError('Unsupported template or context structure.')
    if set(context) - INPUTS:
        raise RenderError('Context contains unsupported keys.')
    defaults = json.loads((root / 'references/defaults.json').read_text(encoding='utf-8'))['reminder']
    schema = json.loads((root / 'references/schema.json').read_text(encoding='utf-8'))
    required = {
        'schema': ['SPACE_ID', 'FOLDER_ID'],
        'config': ['SPACE_ID', 'DATABASE_ID', 'FOLDER_ID', 'TODAY', 'INIT_MODE'],
        'reminder': ['DATABASE_ID', 'SKILLS_DIR', 'REMINDER_START_AT'],
    }[kind]
    values = dict(context)
    values.setdefault('TIMEZONE', defaults['timezone'])
    values.setdefault('REMINDER_STATUS', 'disabled')
    for key in ['FOLDER_BACKUP_ID', 'FOLDER_ARCHIVE_ID', 'TASK_ID', 'REMINDER_START_AT']:
        values.setdefault(key, '')
    for key, source in [('QUIET_START_HOUR', 'quiet_start_hour'), ('QUIET_END_HOUR', 'quiet_end_hour'), ('CATCHUP_HOURS', 'catchup_hours')]:
        values.setdefault(key, defaults[source])
    for key in required:
        value = values.get(key)
        if not isinstance(value, str) or not value.strip() or TOKEN.search(value) or re.search(r'<[^>]+>', value):
            raise RenderError(f'Missing or unresolved required context key: {key}.')
    for key, value in values.items():
        if key == 'DATABASE_IDS':
            continue
        if key in ['QUIET_START_HOUR', 'QUIET_END_HOUR', 'CATCHUP_HOURS']:
            if type(value) is not int or (key != 'CATCHUP_HOURS' and not 0 <= value <= 23) or (key == 'CATCHUP_HOURS' and value <= 0):
                raise RenderError('Invalid reminder timing settings.')
        elif not isinstance(value, str) or any(c in value for c in '\r\n\t|'):
            raise RenderError('Context scalar must be a single safe text value.')
    if values['QUIET_START_HOUR'] == values['QUIET_END_HOUR']:
        raise RenderError('Quiet start and end must differ.')
    if not values['TIMEZONE'].strip():
        raise RenderError('Task timezone must not be empty.')
    if kind != 'schema':
        ids = values.get('DATABASE_IDS', [values['DATABASE_ID']])
        if not isinstance(ids, list) or not ids or any(not isinstance(x, str) or not x.strip() or any(c in x for c in '\r\n\t|') or TOKEN.search(x) or re.search(r'<[^>]+>', x) for x in ids):
            raise RenderError('Active database IDs must be a nonempty list of resolved strings.')
        if len(set(ids)) != len(ids) or values['DATABASE_ID'] not in ids:
            raise RenderError('Active database IDs must be unique and include the primary database.')
        values['DATABASE_IDS_JSON'] = json.dumps(ids, ensure_ascii=False)
        values['DATABASE_IDS_SHELL'] = ' '.join(shlex.quote(x) for x in ids)
    if kind == 'config':
        try:
            date.fromisoformat(values['TODAY'])
        except ValueError:
            raise RenderError('TODAY must be an ISO date.') from None
        if values['REMINDER_STATUS'] not in ['unavailable', 'disabled', 'enabled']:
            raise RenderError('Invalid reminder capability status.')
        if values['REMINDER_STATUS'] == 'enabled' and not (values['TASK_ID'] and values['REMINDER_START_AT']):
            raise RenderError('Enabled reminders require a task ID and start time.')
    if kind == 'reminder' or values['REMINDER_START_AT']:
        try:
            start = datetime.fromisoformat(values['REMINDER_START_AT'].replace('Z', '+00:00'))
            if start.tzinfo is None or start.utcoffset() is None:
                raise ValueError
        except (ValueError, TypeError):
            raise RenderError('Reminder start must be an ISO timestamp with an offset.') from None
    if kind == 'reminder':
        skills = values['SKILLS_DIR']
        if not PurePosixPath(skills).is_absolute():
            raise RenderError('The reminder adapter requires an absolute POSIX path; other backends need a native adapter.')
        values['LIBRARY_DATABASE_DIR_SHELL'] = shlex.quote(skills.rstrip('/\\') + '/library/database')
        values['REMINDER_RULES'] = (root / 'references/reminder-rules.md').read_text(encoding='utf-8').strip()
    values['SCHEMA_VERSION'] = version(root)
    values['FIELD_COUNT'] = str(len(schema['schema']['properties']))
    values['FIELDS'] = '、'.join(p['name'] for p in schema['schema']['properties'])

    def replace(text: str) -> str:
        def token(match: re.Match) -> str:
            key = match.group(1)
            if key not in values:
                raise RenderError(f'Missing template context key: {key}.')
            return str(values[key])
        result = TOKEN.sub(token, text)
        if TOKEN.search(result):
            raise RenderError('Rendered output still contains unresolved placeholders.')
        return result

    if kind == 'schema':
        def walk(value):
            if isinstance(value, dict):
                return {key: walk(item) for key, item in value.items()}
            if isinstance(value, list):
                return [walk(item) for item in value]
            return replace(value) if isinstance(value, str) else value
        return json.dumps(walk(schema), ensure_ascii=False, indent=2) + '\n'
    template = (root / 'references' / TEMPLATES[kind]).read_text(encoding='utf-8')
    return replace(template).rstrip() + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=TEMPLATES)
    parser.add_argument('--context', type=Path, required=True, help='JSON file with instance values; never commit it.')
    args = parser.parse_args()
    try:
        context = json.loads(args.context.read_text(encoding='utf-8'))
        result = render(args.kind, context)
    except RenderError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError):
        print('Unable to read or render template/context. No values were printed.', file=sys.stderr)
        return 1
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.stdout.write(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
