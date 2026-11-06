"""Transactional reminder generation and leased, explicitly selected delivery."""
from datetime import timedelta
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid

from . import JidouError
from .schedule import Rule, UTC, instant, quiet, stamp, zone
from .store import encode


def scan(store):
    settings = store.settings()
    if not settings.get('reminders_enabled', True):
        return {'queued': 0, 'notifications': [], 'quiet': False, 'paused': True, 'errors': []}
    if quiet(store.now, settings):
        return {'queued': 0, 'notifications': [], 'quiet': True, 'errors': []}
    errors, notifications = [], []
    with store.connection(write=True) as con:
        rows = con.execute('SELECT * FROM records').fetchall()
        lower = store.now - timedelta(hours=settings['catchup_hours'])
        cutoff = instant(settings['reminder_start_at'])
        for row in rows:
            fields = store.record(row)['fields']
            if fields['状态'] in {'已完成', '归档'} or fields['执行'] not in {'', '仅提醒'} or fields['类型'] == '定时' or fields['提醒'] in {'', '不提醒'}:
                continue
            if not (fields['下次触发'] or fields['到期']):
                continue
            try:
                rule = Rule.fields(fields, settings['timezone'])
                event = instant(fields['下次触发'] or fields['到期'])
                mute = instant(fields['静音至']) if fields['静音至'] else None
                if mute and mute > store.now:
                    continue
                remind = rule.reminder_at(event)
                if rule.text and (remind <= lower or remind < cutoff or (mute and remind < mute)):
                    boundary = max(lower, cutoff, mute or lower)
                    inclusive = boundary > lower
                    event = rule.next(boundary + timedelta(minutes=rule.lead) - (timedelta(microseconds=1) if inclusive else timedelta(0)))
                    rule.override = None
                    remind = rule.reminder_at(event)
                for _ in range(1000):
                    completed = con.execute("SELECT 1 FROM occurrences WHERE template_id=? AND event_at=? AND status IN ('completed','skipped')", (row['id'], stamp(event))).fetchone()
                    if completed and rule.text:
                        event = rule.next(event)
                        rule.override = None
                        remind = rule.reminder_at(event)
                        continue
                    if rule.text:
                        following = rule.next(event)
                        if rule.reminder_at(following, False) <= store.now:
                            event, remind = following, rule.reminder_at(following, False)
                            rule.override = None
                            continue
                    break
                else:
                    raise JidouError('Too many missed occurrences; review the recurrence anchor.')
                if rule.text and fields['下次触发'] != event.isoformat():
                    fields['下次触发'] = event.isoformat()
                if not (lower < remind <= store.now and remind >= cutoff) or (mute and remind < mute):
                    if rule.text:
                        store.save(con, row['id'], fields)
                    continue
                key = settings['database_id'] + '/' + row['id'] + '/' + stamp(event) + '/' + stamp(remind)
                old = con.execute('SELECT status FROM notifications WHERE event_key=?', (key,)).fetchone()
                queued = old is None or old[0] == 'cancelled'
                local = event.astimezone(zone(settings['timezone']))
                body = local.strftime('%m-%d %H:%M') + ' ' + fields['内容'] + (' [' + fields['领域'] + ']' if fields['领域'] else '')
                notification_id = uuid.uuid4().hex
                if old is None:
                    con.execute('INSERT INTO notifications (id,event_key,record_id,event_at,reminder_at,body,status) VALUES (?,?,?,?,?,?,?)', (notification_id, key, row['id'], stamp(event), stamp(remind), body, 'pending'))
                elif old[0] == 'cancelled':
                    con.execute("UPDATE notifications SET status='pending',body=?,next_attempt=NULL,last_error=NULL WHERE event_key=?", (body, key))
                    notification_id = con.execute('SELECT id FROM notifications WHERE event_key=?', (key,)).fetchone()[0]
                if queued:
                    notifications.append({'id': notification_id, 'key': key, 'event_at': stamp(event), 'body': body})
                if queued:
                    fields['上次结果'] = encode({'kind': 'reminder', 'key': key, 'event_at': stamp(event), 'prepared_at': stamp(store.now), 'delivery': 'queued'})
                if rule.text:
                    fields['下次触发'] = rule.next(event).isoformat()
                    if fields['重复'].lstrip().startswith('{'):
                        options = json.loads(fields['重复'])
                        options.pop('override_reminder_at', None)
                        fields['重复'] = encode(options)
                store.save(con, row['id'], fields)
            except (JidouError, ValueError, OverflowError):
                errors.append({'record_id': row['id'], 'error': 'Invalid or unsupported time/recurrence; record was not queued.'})
        con.execute("INSERT INTO meta VALUES ('last_scan',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (encode({'at': stamp(store.now), 'queued': len(notifications), 'errors': errors}),))
    return {'queued': len(notifications), 'notifications': notifications, 'quiet': False, 'errors': errors}


def pending(store):
    with store.connection() as con:
        rows = con.execute("SELECT id,event_key,record_id,event_at,reminder_at,body,status,attempts,last_error FROM notifications WHERE status IN ('pending','claimed') ORDER BY reminder_at").fetchall()
        return {'notifications': [dict(row) for row in rows], 'total': len(rows)}


def send_system(title, body):
    if sys.platform == 'darwin':
        script = 'on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run'
        argv = ['osascript', '-e', script, '--', title, body]
        options = {}
    elif sys.platform == 'win32':
        # Static PowerShell; payload is JSON on stdin, never executable code.
        script = '''[Console]::InputEncoding = New-Object System.Text.UTF8Encoding
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$p = [Console]::In.ReadToEnd() | ConvertFrom-Json
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.Visible = $true
$n.ShowBalloonTip(8000, [string]$p.title, [string]$p.body, [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -Milliseconds 1500
$n.Dispose()
'''
        encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
        argv = ['powershell.exe', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-EncodedCommand', encoded]
        options = {'input': encode({'title': title, 'body': body}), 'encoding': 'utf-8', 'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0)}
    else:
        binary = shutil.which('notify-send')
        if not binary:
            raise JidouError('No desktop notifier is installed; choose stdout or a configured webhook.')
        argv, options = [binary, title, body], {}
    result = subprocess.run(argv, capture_output=True, timeout=15, **options)
    if result.returncode:
        raise JidouError('The operating-system notification command failed.')


def transport(channel, message, webhook_env=None):
    if channel == 'stdout':
        print(encode({'notification': message}), flush=True)
        return
    if channel == 'system':
        send_system('记兜 jidou', message['body'])
        return
    if channel == 'webhook':
        url = os.environ.get(webhook_env or '')
        if not url:
            raise JidouError('Webhook environment variable is unavailable in this execution environment.')
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != 'https' and not (parts.scheme == 'http' and parts.hostname in {'localhost', '127.0.0.1', '::1'}):
            raise JidouError('Use HTTPS for remote notification endpoints.')
        request = urllib.request.Request(url, data=encode(message).encode('utf-8'), headers={'Content-Type': 'application/json', 'X-Jidou-Delivery-Key': message['key']}, method='POST')
        with urllib.request.urlopen(request, timeout=15) as response:
            if not 200 <= response.status < 300:
                raise JidouError('Webhook did not accept the notification.')
        return
    raise JidouError('Unknown notification channel.')


def deliver(store, channel='stdout', webhook_env=None, maximum=100, sender=None):
    if not store.settings().get('reminders_enabled', True):
        return {'accepted': 0, 'failed': 0, 'quiet': False, 'paused': True}
    if quiet(store.now, store.settings()):
        return {'accepted': 0, 'failed': 0, 'quiet': True}
    accepted = failed = 0
    for _ in range(maximum):
        current_settings = store.settings()
        if not current_settings.get('reminders_enabled', True):
            return {'accepted': accepted, 'failed': failed, 'quiet': False, 'paused': True}
        if quiet(store.now, current_settings):
            return {'accepted': accepted, 'failed': failed, 'quiet': True}
        with store.connection(write=True) as con:
            row = con.execute("SELECT * FROM notifications WHERE (status='pending' AND (next_attempt IS NULL OR next_attempt<=?)) OR (status='claimed' AND lease_until<=?) ORDER BY reminder_at LIMIT 1", (stamp(store.now), stamp(store.now))).fetchone()
            if row is None:
                break
            fields = store.get_in(con, row['record_id'])['fields']
            if fields['状态'] in {'已完成', '归档'} or fields['提醒'] in {'', '不提醒'} or (fields['静音至'] and instant(row['reminder_at']) < instant(fields['静音至'])):
                con.execute("UPDATE notifications SET status='cancelled' WHERE id=?", (row['id'],))
                continue
            token = uuid.uuid4().hex
            con.execute("UPDATE notifications SET status='claimed',lease_token=?,lease_until=?,attempts=attempts+1 WHERE id=?", (token, stamp(store.now + timedelta(minutes=2)), row['id']))
            event = instant(row['event_at']).astimezone(zone(store.config(con)['timezone']))
            body = event.strftime('%m-%d %H:%M') + ' ' + fields['内容'] + (' [' + fields['领域'] + ']' if fields['领域'] else '')
            con.execute('UPDATE notifications SET body=? WHERE id=?', (body, row['id']))
            message = {'id': row['id'], 'key': row['event_key'], 'record_id': row['record_id'], 'event_at': row['event_at'], 'body': body}
        try:
            if sender:
                sender(message)
            else:
                transport(channel, message, webhook_env)
        except Exception:
            with store.connection(write=True) as con:
                con.execute("UPDATE notifications SET status='pending',lease_token=NULL,lease_until=NULL,next_attempt=?,last_error='Notification transport failed; no response body or credentials stored.' WHERE id=? AND lease_token=? AND status='claimed'", (stamp(store.now + timedelta(minutes=5)), message['id'], token))
            failed += 1
            continue
        with store.connection(write=True) as con:
            changed = con.execute("UPDATE notifications SET status='accepted',accepted_at=?,lease_token=NULL,lease_until=NULL,last_error=NULL WHERE id=? AND lease_token=? AND status='claimed'", (stamp(store.now), message['id'], token)).rowcount
            if changed:
                fields = store.get_in(con, message['record_id'])['fields']
                try:
                    marker = json.loads(fields['上次结果'])
                except ValueError:
                    marker = {}
                if isinstance(marker, dict) and marker.get('key') == message['key']:
                    marker.update(delivery='accepted', accepted_at=stamp(store.now))
                    fields['上次结果'] = encode(marker)
                    store.save(con, message['record_id'], fields)
            accepted += changed
    return {'accepted': accepted, 'failed': failed, 'quiet': False}
