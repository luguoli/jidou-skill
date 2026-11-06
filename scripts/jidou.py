#!/usr/bin/env python3
"""Portable jidou CLI. No data files are created until explicit init."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

from jidou_runtime import JidouError
from jidou_runtime.schedule import instant
from jidou_runtime.store import Store, default_home, encode
from jidou_runtime import outbox
from jidou_runtime import integrations
from jidou_runtime import jobs


def read_json(path):
    try:
        return json.loads(sys.stdin.read() if path == '-' else Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise JidouError('Unable to read valid JSON input; no input values were printed.') from None


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--home', type=Path, default=None, help='Shared user data directory; defaults to the OS user-data location.')
    result.add_argument('--now', help='Explicit offset timestamp for diagnostics; omitted in real scheduled commands.')
    commands = result.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor')
    init = commands.add_parser('init')
    init.add_argument('--timezone', default='Asia/Shanghai')
    settings = commands.add_parser('settings')
    setting_commands = settings.add_subparsers(dest='settings_command', required=True)
    setting_commands.add_parser('show')
    setting_update = setting_commands.add_parser('update')
    setting_update.add_argument('--input', required=True)
    add = commands.add_parser('add')
    add.add_argument('--input', required=True, help='JSON file, or - for stdin; 原文 must be supplied explicitly.')
    add.add_argument('--operation-id')
    get = commands.add_parser('get')
    get.add_argument('id')
    listing = commands.add_parser('list')
    for flag in ['type', 'domain', 'status', 'lineage', 'person', 'query']:
        listing.add_argument('--' + flag)
    listing.add_argument('--limit', type=int, default=100)
    listing.add_argument('--offset', type=int, default=0)
    listing.add_argument('--date', help='Capture day (YYYY-MM-DD) in the configured user timezone.')
    listing.add_argument('--from-date', help='First capture day, inclusive (YYYY-MM-DD).')
    listing.add_argument('--to-date', help='Last capture day, inclusive (YYYY-MM-DD).')
    listing.add_argument('--timezone', help='Read-only timezone override for capture-date filtering.')
    update = commands.add_parser('update')
    update.add_argument('id')
    update.add_argument('--input', required=True)
    for name in ['complete', 'skip']:
        action = commands.add_parser(name)
        action.add_argument('id')
        action.add_argument('--event-at')
        action.add_argument('--original', default='')
    undo = commands.add_parser('undo')
    undo.add_argument('receipt_id')
    undo.add_argument('--restore-reminder', action='store_true')
    commands.add_parser('export')
    importing = commands.add_parser('import')
    importing.add_argument('--input', required=True)
    backup = commands.add_parser('backup')
    backup.add_argument('--output', required=True)
    installing = commands.add_parser('install')
    installing.add_argument('--agent', choices=['codex', 'claude', 'trae'], required=True)
    installing.add_argument('--scope', choices=['project', 'user'], default='project')
    installing.add_argument('--project', type=Path)
    installing.add_argument('--user-home', type=Path)
    installing.add_argument('--edition', choices=['cn', 'intl'], default='cn')
    installing.add_argument('--apply', action='store_true')
    scheduler = commands.add_parser('scheduler')
    schedules = scheduler.add_subparsers(dest='scheduler_command', required=True)
    schedules.add_parser('status')
    for name in ['plan', 'install']:
        action = schedules.add_parser(name)
        action.add_argument('--platform', choices=['windows', 'darwin', 'linux'])
        action.add_argument('--channel', choices=['stdout', 'system', 'webhook'], default='system')
        action.add_argument('--webhook-env')
        action.add_argument('--user-home', type=Path)
        action.add_argument('--apply', action='store_true')
    work = commands.add_parser('work')
    work.add_argument('--channel', choices=['stdout', 'system', 'webhook'], default='stdout')
    work.add_argument('--webhook-env')
    work.add_argument('--quiet', action='store_true')
    job = commands.add_parser('job')
    job_commands = job.add_subparsers(dest='job_command', required=True)
    adding = job_commands.add_parser('add')
    adding.add_argument('--input', required=True)
    adding.add_argument('--disabled', action='store_true')
    job_commands.add_parser('list')
    job_commands.add_parser('tick')
    history = job_commands.add_parser('runs')
    history.add_argument('--job')
    for name in ['enable', 'disable']:
        action = job_commands.add_parser(name)
        action.add_argument('id')
        action.add_argument('--next-run')
    resolving = job_commands.add_parser('resolve')
    resolving.add_argument('run_id')
    resolving.add_argument('--status', choices=['success', 'failed'], required=True)
    reminders = commands.add_parser('reminders')
    reminder_commands = reminders.add_subparsers(dest='reminder_command', required=True)
    reminder_commands.add_parser('scan')
    reminder_commands.add_parser('pending')
    for name in ['deliver', 'run']:
        action = reminder_commands.add_parser(name)
        action.add_argument('--channel', choices=['stdout', 'system', 'webhook'], default='stdout')
        action.add_argument('--webhook-env')
        action.add_argument('--quiet', action='store_true', help='Emit no successful worker summary; errors still have nonzero exit status.')
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        now = instant(args.now) if args.now else None
        store = Store(args.home or default_home(), now)
        if args.command == 'doctor':
            response = store.doctor()
        elif args.command == 'init':
            response = store.initialize(args.timezone)
        elif args.command == 'settings':
            response = store.settings() if args.settings_command == 'show' else store.update_settings(read_json(args.input))
        elif args.command == 'add':
            response = store.add(read_json(args.input), args.operation_id)
        elif args.command == 'get':
            response = store.get(args.id)
        elif args.command == 'list':
            names = {'type': '类型', 'domain': '领域', 'status': '状态', 'lineage': '线索', 'person': '相关人'}
            response = store.list({target: getattr(args, source) for source, target in names.items() if getattr(args, source)}, args.query, args.limit, args.offset, recorded_on=args.date, date_from=args.from_date, date_to=args.to_date, timezone_name=args.timezone)
        elif args.command == 'update':
            response = store.update(args.id, read_json(args.input))
        elif args.command in {'complete', 'skip'}:
            response = store.occurrence(args.id, args.event_at, 'completed' if args.command == 'complete' else 'skipped', args.original)
        elif args.command == 'undo':
            response = store.undo(args.receipt_id, args.restore_reminder)
        elif args.command == 'export':
            response = store.export()
        elif args.command == 'import':
            response = store.import_records(read_json(args.input))
        elif args.command == 'backup':
            response = store.backup(args.output)
        elif args.command == 'install':
            response = integrations.install_agent(args.agent, args.scope, args.project, args.user_home, args.apply, args.edition)
        elif args.command == 'scheduler':
            if args.scheduler_command == 'status':
                response = integrations.scheduler_status(store)
            else:
                response = integrations.scheduler_plan(store, args.platform, args.channel, args.webhook_env, args.user_home)
                if args.scheduler_command == 'install' and args.apply:
                    response = integrations.apply_scheduler(store, response)
        elif args.command == 'work':
            scanned = outbox.scan(store)
            response = outbox.deliver(store, args.channel, args.webhook_env)
            response['jobs'] = jobs.tick(store)
            if any(run['status'] != 'success' for run in response['jobs']['runs']):
                raise JidouError('One or more jobs failed or are uncertain; inspect job runs before any retry.')
            if response['failed'] or scanned['errors']:
                raise JidouError('Worker completed with reminder errors; inspect pending and doctor.')
            if args.quiet:
                return 0
        elif args.command == 'job':
            if args.job_command == 'add':
                response = jobs.add(store, read_json(args.input), args.disabled)
            elif args.job_command == 'list':
                response = jobs.list_jobs(store)
            elif args.job_command == 'tick':
                response = jobs.tick(store)
            elif args.job_command == 'runs':
                response = jobs.list_runs(store, args.job)
            elif args.job_command in {'enable', 'disable'}:
                response = jobs.set_enabled(store, args.id, args.job_command == 'enable', args.next_run)
            else:
                response = jobs.resolve(store, args.run_id, args.status)
        elif args.command == 'reminders':
            if args.reminder_command == 'scan':
                response = outbox.scan(store)
            elif args.reminder_command == 'pending':
                response = outbox.pending(store)
            else:
                scanned = outbox.scan(store) if args.reminder_command == 'run' else {'errors': []}
                response = outbox.deliver(store, args.channel, args.webhook_env)
                response['scan_errors'] = scanned['errors']
                if response['failed'] or response['scan_errors']:
                    print('Some reminders could not be processed; inspect doctor and pending. No payloads were printed.', file=sys.stderr)
                    return 1
                if args.quiet:
                    return 0
        else:
            raise JidouError('Unsupported command.')
        print(encode(response))
        if isinstance(response, dict) and response.get('errors'):
            return 1
        return 0
    except JidouError as error:
        print('jidou: ' + str(error), file=sys.stderr)
        return 1
    except (sqlite3.Error, OSError, ValueError, KeyError, TypeError):
        # Do not echo SQL, user original text, paths containing secrets or HTTP responses.
        print('jidou: operation failed. Check initialization, input fields, timezone and available dependencies; existing data was not replaced.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    raise SystemExit(main())
