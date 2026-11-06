"""Explicit whole-package agent installation and native user scheduler plans."""
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import uuid

from . import JidouError
from .store import ROOT, encode

AGENTS = {'codex': '.agents', 'claude': '.claude', 'trae': '.trae'}
MARKER = '.jidou-install.json'


def install_agent(agent, scope='project', project=None, user_home=None, apply=False, edition='cn'):
    if agent not in AGENTS or scope not in {'project', 'user'}:
        raise JidouError('Choose codex, claude or trae, and project/user scope.')
    if scope == 'project' and project is None:
        raise JidouError('Project installation needs an explicit project directory.')
    if agent == 'trae' and scope == 'user' and edition != 'cn':
        raise JidouError('Use project scope for this TRAE edition; its global directory must be verified for the installed version.')
    base = Path(project if scope == 'project' else user_home or Path.home()).expanduser().resolve()
    folder = AGENTS[agent]
    if agent == 'trae' and scope == 'user' and edition == 'cn':
        folder = '.trae-cn'
    destination = base / folder / 'skills/jidou'
    if not destination.resolve().is_relative_to(base):
        raise JidouError('A parent symlink redirects the installation outside the selected project/profile.')
    report = {'agent': agent, 'scope': scope, 'destination': str(destination), 'applied': False, 'data_initialized': False}
    if not apply:
        return report
    if destination.resolve() == ROOT.resolve():
        return {**report, 'applied': True, 'unchanged': True}
    if destination.is_symlink():
        raise JidouError('Refusing to replace a symlink installation.')
    if destination.exists():
        marker = destination / MARKER
        try:
            previous = json.loads(marker.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            raise JidouError('Existing directory is unmanaged; back it up and select a clean installation location.') from None
        if previous.get('owner') != 'jidou-skill':
            raise JidouError('Existing installation is not jidou-managed.')
        expected = set(previous.get('files', [])) | {MARKER}
        actual = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        if actual - expected:
            raise JidouError('Installation contains unmanaged files; preserve them before updating.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.jidou-stage-', dir=destination.parent))
    backup = None
    try:
        files = []
        for top in ['SKILL.md', 'README.md', 'README.en.md', 'CHANGELOG.md', 'LICENSE', 'requirements.txt', 'references', 'scripts']:
            source = ROOT / top
            paths = source.rglob('*') if source.is_dir() else [source]
            for path in paths:
                if not path.is_file() or '__pycache__' in path.parts or path.suffix in {'.pyc', '.sqlite3', '.db'}:
                    continue
                if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
                    raise JidouError('Package source contains a symlink or outside resource.')
                relative = path.relative_to(ROOT)
                output = stage / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, output)
                files.append(relative.as_posix())
        (stage / MARKER).write_text(encode({'owner': 'jidou-skill', 'files': files}), encoding='utf-8')
        if destination.exists():
            backup = destination.with_name(destination.name + '.backup-' + uuid.uuid4().hex[:8])
            destination.rename(backup)
        try:
            stage.rename(destination)
        except OSError:
            if backup and not destination.exists():
                backup.rename(destination)
            raise
    finally:
        if stage.exists() and stage.resolve().parent == destination.parent.resolve() and stage.name.startswith('.jidou-stage-'):
            shutil.rmtree(stage)
    return {**report, 'applied': True, 'backup': str(backup) if backup else None}


def native_platform():
    return 'windows' if sys.platform == 'win32' else 'darwin' if sys.platform == 'darwin' else 'linux'


def scheduler_plan(store, platform=None, channel='system', webhook_env=None, user_home=None):
    settings = store.settings()
    platform = platform or native_platform()
    name = 'jidou-' + settings['database_id'][:16]
    user = Path(user_home or Path.home())
    worker = [sys.executable, str(ROOT / 'scripts/jidou.py'), '--home', str(store.home), 'work', '--channel', channel, '--quiet']
    if webhook_env:
        worker += ['--webhook-env', webhook_env]
    files, commands = [], []
    if platform == 'windows':
        run = subprocess.list2cmdline(worker)
        if len(run) > 260:
            raise JidouError('Task Scheduler command is too long; install the package and data directory at shorter paths.')
        commands = [['schtasks.exe', '/Create', '/TN', name, '/SC', 'MINUTE', '/MO', '1', '/TR', run, '/IT']]
    elif platform == 'darwin':
        name = 'io.jidou.' + settings['database_id'][:16]
        path = user / 'Library/LaunchAgents' / (name + '.plist')
        plist = {'Label': name, 'ProgramArguments': worker, 'StartInterval': settings['poll_seconds'], 'RunAtLoad': True,
                 'StandardOutPath': str(store.home / 'worker.stdout.log'), 'StandardErrorPath': str(store.home / 'worker.stderr.log')}
        files = [{'path': str(path), 'content': plistlib.dumps(plist).decode('utf-8')}]
        # load/unload are supported launchctl compatibility commands; no shell interpolation.
        commands = [['launchctl', 'load', str(path)]]
    elif platform != 'linux':
        raise JidouError('Unsupported scheduler platform.')
    return {'platform': platform, 'name': name, 'files': files, 'commands': commands, 'worker_command': worker,
            'requires_logged_in_desktop': channel == 'system', 'cross_platform_preview': platform != native_platform(),
            'applied': False, 'linux_manual': platform == 'linux'}


def apply_scheduler(store, plan):
    if plan['cross_platform_preview'] or plan['linux_manual']:
        raise JidouError('This plan is not applicable to the current host; use a native plan or your own Linux scheduler.')
    with store.connection() as con:
        existing = con.execute("SELECT value FROM meta WHERE key='scheduler'").fetchone()
    if existing:
        raise JidouError('This database already has a scheduler registration; inspect/remove the owned registration before replacing it.')
    if plan['platform'] == 'windows':
        probe = subprocess.run(['schtasks.exe', '/Query', '/TN', plan['name']], capture_output=True, timeout=15)
        if probe.returncode == 0:
            raise JidouError('A same-named system task already exists; it will not be overwritten.')
    created = []
    for file in plan['files']:
        path = Path(file['path']).expanduser()
        if path.exists() or path.is_symlink():
            raise JidouError('A same-named scheduler file already exists; it will not be overwritten.')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as output:
            output.write(file['content'])
        created.append(path)
    try:
        for argv in plan['commands']:
            result = subprocess.run(argv, capture_output=True, timeout=30)
            if result.returncode:
                raise JidouError('Native scheduler registration failed; no new registration was recorded.')
    except Exception:
        for path in created:
            if path.is_file() and path.read_text(encoding='utf-8') == next(x['content'] for x in plan['files'] if x['path'] == str(path)):
                path.unlink()
        raise
    with store.connection(write=True) as con:
        con.execute("INSERT INTO meta VALUES ('scheduler',?)", (encode(plan),))
    return {**plan, 'applied': True, 'delivery_verified': False}


def scheduler_status(store):
    with store.connection() as con:
        row = con.execute("SELECT value FROM meta WHERE key='scheduler'").fetchone()
    return {'configured': bool(row), 'registration': json.loads(row[0]) if row else None, 'delivery_verified': False}
