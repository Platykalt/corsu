#!/usr/bin/env python3
"""The Corsu app: install Corsu, switch each part on or off, pause the terminal, remove everything.

The window is a local page served on 127.0.0.1 at a fixed address (http://localhost:7744 while Corsu is open), shown
in a window of its own (see window.py) or in any browser. `--browser` opens it in the browser instead of a window,
`--text` gives a menu in the terminal.
"""
import json
import os
import re
import shlex
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import corsu
import installer
import review
import update
from installer import t

PAGE = Path(__file__).resolve().parent / 'app/index.html'
# The page asks for news every few seconds; without any for this long, the window was closed.
IDLE_SECONDS = 600
# Once Corsu's own window is closed, a browser tab on the address keeps it running; without one it stops sooner.
CLOSED_IDLE_SECONDS = 30
# The fixed address; when another program holds the port, the next free one is used.
PORT = 7744
PORTS = range(PORT, PORT + 10)

# Names stay general (what the part is); the detail line says what changes.
COMPONENTS = {
    'firefox': {'co': ('Firefox', "Listini, parametri è pagine d'errore. Nant'à Google, ancu i buttoni chì Google ùn traduce micca."),
               'en': ('Firefox', 'Menus, settings and error pages. On Google, also the buttons Google leaves untranslated.'),
                'fr': ('Firefox', 'Menus, réglages et pages d\'erreur. Sur Google, aussi les boutons que Google ne traduit pas.')},
    'chromium': {'co': ('Navigatori Chromium', 'Listini è parametri.'),
                'en': ('Chromium browsers', 'Menus and settings.'),
                 'fr': ('Navigateurs Chromium', 'Menus et réglages.')},
    'discord': {'co': ('Discord', "L'interfaccia di l'appiecazione, cù Vencord. I messaghji ùn cambianu micca."),
               'en': ('Discord', 'The app\'s interface, through Vencord. Messages are not changed.'),
                'fr': ('Discord', 'L\'interface de l\'application, avec Vencord. Les messages ne changent pas.')},
    'vesktop': {'co': ('Vesktop', "L'interfaccia di l'appiecazione. I messaghji ùn cambianu micca."),
               'en': ('Vesktop', 'The app\'s interface. Messages are not changed.'),
                'fr': ('Vesktop', 'L\'interface de l\'application. Les messages ne changent pas.')},
    'desktop': {'co': ('Scagnu', "KDE Plasma : u scagnu, u listinu di l'appiecazioni è i prugrammi KDE."),
               'en': ('Desktop', 'KDE Plasma: the desktop, the application menu and KDE programs.'),
                'fr': ('Bureau', 'KDE Plasma : le bureau, le menu des applications et les programmes KDE.')},
    'qt': {'co': ('Traduzzioni di u sistema', "Prugrammi GTK, messaghji di e cummande è finestre Qt. Dumanda a parolla d'intesa d'amministratore."),
          'en': ('System translations', 'GTK programs, command output and Qt dialogs. Needs the administrator password.'),
           'fr': ('Traductions du système', 'Programmes GTK, messages des commandes et fenêtres Qt. Demande le mot de '
                  'passe administrateur.')},
    'minecraft': {'co': ('Minecraft', "Minecraft Java Edition in corsu, secondu a versione di ogni cartulare di ghjocu : u pacchettu di risorse è a lingua. Chjudite Minecraft prima."),
                  'en': ('Minecraft', 'Minecraft Java Edition in Corsican, for the version each game folder plays: the resource pack and the language. Close Minecraft first.'),
                  'fr': ('Minecraft', 'Minecraft Java Edition en corse, selon la version de chaque dossier de jeu : le pack de ressources et la langue. Fermez Minecraft d\'abord.')},
    'terminal': {'co': ('Terminale', 'I messaghji di e cummande, in i novi terminali.'),
                'en': ('Terminal', 'Command messages, in new terminal windows.'),
                 'fr': ('Terminal', 'Les messages des commandes, dans les nouveaux terminaux.')},
}
ORDER = ['firefox', 'chromium', 'discord', 'vesktop', 'desktop', 'qt', 'terminal', 'minecraft']


# The installer lock's message when another Corsu window or installer is at work (docs/update-architecture.md).
BUSY = re.compile(r'already busy|déjà occupé', re.I)


class Job:
    """One installer run at a time; its output is shown live in the page."""

    def __init__(self):
        self.lock = threading.Lock()
        self.title = ''
        self.lines = []
        self.running = False
        self.ok = None
        self.progress = None
        # The update script's last word (`@result {json}`), and whether the installer lock stopped the run.
        self.result = None
        self.busy = False

    def start(self, title, arguments, language, script='installer.py'):
        with self.lock:
            if self.running:
                return False
            self.title, self.lines, self.running, self.ok, self.progress = title, [], True, None, None
            self.result, self.busy = None, False
        environment = {**os.environ, 'CORSU_LANG': language, 'PYTHONUNBUFFERED': '1', 'PYTHONIOENCODING': 'utf-8',
                       'CORSU_SETUP_WINDOW': '1', 'CORSU_APP_ROOT': str(corsu.ROOT)}
        command = [sys.executable, str(corsu.SRC / script), *arguments]
        threading.Thread(target=self.run, args=(command, environment), daemon=True).start()
        return True

    def run(self, command, environment):
        try:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                                       env=environment)
            for line in process.stdout:
                # Commands the installer runs are echoed with "+ "; they are noise for most people.
                if line.startswith('@progress '):
                    percent, _, label = line[10:].strip().partition(' ')
                    if percent.isdigit():
                        self.progress = {'percent': int(percent), 'label': label}
                    continue
                if line.startswith('@result '):
                    try:
                        self.result = json.loads(line[8:])
                    except ValueError:
                        pass
                    continue
                if BUSY.search(line):
                    self.busy = True
                if not line.startswith('+ '):
                    self.lines.append(line.rstrip('\n'))
            ok = process.wait() == 0
        except OSError as error:
            self.lines.append(str(error))
            ok = False
        if not ok:
            import logbook
            self.lines.append(corsu.t(f'Details: {logbook.path()}', f'Détails : {logbook.path()}'))
        with self.lock:
            self.running, self.ok = False, ok

    def snapshot(self):
        return {'title': self.title, 'lines': self.lines[-400:], 'running': self.running, 'ok': self.ok,
                'progress': self.progress, 'result': self.result, 'busy': self.busy}


DETECTED = {'time': 0.0, 'names': set()}


def detected():
    """The programs found on this computer, looked up again at most every 20 seconds."""
    if time.monotonic() - DETECTED['time'] > 20:
        DETECTED['names'], DETECTED['time'] = set(installer.available_components()), time.monotonic()
    return DETECTED['names']


def components():
    """The fixed parts, then each program with its own Corsican translation (src/apps)."""
    import apps
    return {**COMPONENTS, **{app_id: app.description for app_id, app in apps.registry().items()}}


def order():
    import apps
    return ORDER + list(apps.registry())


def status(name, item, state):
    """Activation, installations, coverage and validation of one part, from the record the installer keeps
    (state['results'], also behind its summary). Records from before that field get an activation derived from the
    switches and no details."""
    import apps
    result = state.get('results', {}).get(name)
    app = apps.registry().get(name)
    validation = dict(app.validation) if app else None
    if result is None:
        activation = 'active' if item['on'] else 'inactive' if item['installed'] else None
        return {'activation': activation, 'instances': [], 'coverage': None, 'validation': validation, 'updated': None}
    activation = result['activation']
    return {'activation': activation, 'on': activation in apps.ACTIVE, 'instances': result['instances'],
            'coverage': result.get('coverage'), 'validation': validation, 'updated': result.get('time')}


def snapshot(job=None):
    """Everything the page shows, read fresh each time."""
    try:
        state, problem = corsu.load_state(), None
    except RuntimeError as error:
        # A damaged record: say so instead of the page reading as if Corsu had closed.
        state, problem = {'files': {}}, str(error)
    installed = set(state.get('components', [])) if corsu.STATE.exists() else set()
    if state.get('qt_system'):
        installed.add('qt')
    available = detected()
    switchable = set(corsu.switchable(state)) if corsu.STATE.exists() else set()
    paused = corsu.terminal_paused_until() if 'terminal' in switchable else None
    items = []
    texts = components()
    for name in order():
        if name == 'terminal' and name not in switchable:
            continue
        if name not in available | installed | switchable:
            continue
        text = texts[name]
        if name == 'chromium':
            import chromium
            found = ', '.join(browser.label for browser in chromium.browsers())
            if found:
                text = {language: (label, f'{found}. {detail}') for language, (label, detail) in text.items()}
        if name == 'firefox' and not corsu.firefox_install():
            text = {'co': ('Firefox', "Ùn hè micca stallatu : Corsu scarica u Firefox francese di Mozilla (circa 90 Mo), u verifica è u traduce."),
                    'fr': ('Firefox', "Pas encore installé : Corsu télécharge le Firefox français de Mozilla (environ 90 Mo), le vérifie et le traduit."),
                    'en': ('Firefox', "Not installed yet: Corsu downloads Mozilla's French Firefox (about 90 MB), checks it and translates it.")}
        if name == 'vesktop' and not installer.vesktop_installed():
            text = {'co': ('Vesktop', "Una appiecazione Discord cù Vencord. Corsu a scarica (circa 130 Mo), a verifica è a regula."),
                    'fr': ('Vesktop', 'Une application Discord avec Vencord. Corsu la télécharge (environ 130 Mo), la vérifie et la règle.'),
                    'en': ('Vesktop', 'A Discord app with Vencord. Corsu downloads it (about 130 MB), checks it and sets it up.')}
        item = {'name': name, 'text': text, 'installed': name in installed or name in switchable,
                'switchable': name in switchable, 'on': name in switchable and not corsu.is_disabled(name, state)}
        item.update(status(name, item, state))
        if name == 'minecraft' and item['installed']:
            waiting = minecraft_waiting(state, state.get('results', {}).get(name))
            item['instances'] = [*item['instances'], *waiting]
            item['waiting'] = len(waiting)
        items.append(item)
    profile = corsu.firefox_profile() if 'firefox' in installed else None
    return {
        'version': running_version(),
        'pid': os.getpid(),
        'platform': corsu.PLATFORM,
        'language': 'fr' if corsu.french() else 'en',
        'installed': bool(installed),
        'everything_off': corsu.disabled_marker().exists(),
        'items': items,
        'terminal_paused_until': paused,
        'firefox_profile': str(profile) if profile else None,
        'lexicon_entries': len(corsu.WORDS),
        'review': review.progress_all(),
        'options': review.options(),
        'update': {**(UPDATE['info'] or {'current': running_version(), 'latest': None, 'status': None,
                                         'checked': None, 'error': None}),
                   'checking': UPDATE['checking'], 'auto_started': UPDATE['auto_started'],
                   'restart': restart_info(state, job or Job())},
        'preferences': preferences(),
        'problem': problem,
    }


def peer_uid(port):
    """The user owning the local TCP connection from `port` (Linux only; None elsewhere or when unknown)."""
    for table in ('/proc/net/tcp', '/proc/net/tcp6'):
        try:
            lines = Path(table).read_text().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) > 7 and int(fields[1].rsplit(':', 1)[1], 16) == port:
                return int(fields[7])
    return None


def make_handler(job, activity, port, handover=None):
    page = PAGE.read_bytes()
    icon = (PAGE.parent / 'corsu.svg').read_bytes()
    hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
    origins = {f'http://{host}' for host in hosts}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *arguments):
            pass

        def send(self, status, body, content_type='application/json; charset=utf-8'):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                                                        "script-src 'self' 'unsafe-inline'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def allowed(self):
            """Only Corsu's own page may drive Corsu. The Host check stops other sites reaching it through a
            rebound domain name; the custom header can only be sent by a page of this address (a page elsewhere
            would need permission the server never gives); on Linux the connection must also come from this user,
            so another account on the same computer cannot use it."""
            if self.headers.get('Host', '') not in hosts or self.headers.get('X-Corsu') != '1':
                return False
            if self.headers.get('Origin') and self.headers['Origin'] not in origins:
                return False
            if corsu.PLATFORM == 'linux' and hasattr(os, 'getuid'):
                return peer_uid(self.client_address[1]) in (None, os.getuid())
            return True

        def do_GET(self):
            if self.path.split('?')[0] == '/':
                if self.headers.get('Host', '') not in hosts:
                    return self.send(403, {'error': 'forbidden'})
                return self.send(200, page, 'text/html; charset=utf-8')
            if self.path == '/corsu.svg':
                return self.send(200, icon, 'image/svg+xml')
            if self.path == '/api/state' and self.allowed():
                activity[0] = time.monotonic()
                return self.send(200, {**snapshot(job), 'job': job.snapshot()})
            if self.path.startswith('/api/review/next') and self.allowed():
                section = 'Google' if 'section=Google' in self.path else 'Discord'
                return self.send(200, {'item': review.next_item(section), 'progress': review.progress_all()})
            if self.path == '/api/review/issue' and self.allowed():
                return self.send(200, review.issue_link())
            self.send(404, {'error': 'not found'})

        def do_POST(self):
            if not self.allowed():
                return self.send(403, {'error': 'forbidden'})
            activity[0] = time.monotonic()
            length = min(int(self.headers.get('Content-Length') or 0), 65536)
            try:
                request = json.loads(self.rfile.read(length) or b'{}')
            except ValueError:
                return self.send(400, {'error': 'bad request'})
            # The installer speaks French or English; the Corsican window gets French messages.
            language = 'en' if request.get('language') == 'en' else 'fr'
            names = [name for name in request.get('components', []) if name in components()]
            if self.path == '/api/review':
                try:
                    progress = review.record(request.get('french', ''), request.get('english', ''),
                                             request.get('verdict'), request.get('corsican'))
                except ValueError as error:
                    return self.send(400, {'error': str(error)})
                return self.send(200, {'progress': progress})
            if self.path == '/api/options':
                try:
                    return self.send(200, {'options': review.set_option('showOriginal', request.get('showOriginal'))})
                except ValueError as error:
                    return self.send(400, {'error': str(error)})
            if self.path == '/api/logs':
                import logbook
                return self.send(200, {'folder': logbook.open_folder()})
            if self.path == '/api/update':
                info = UPDATE['info'] or {}
                started = start_update(job, language, info.get('latest') if info.get('status') == 'available' else None)
                return self.send(200 if started else 409, {'started': started})
            if self.path == '/api/update/check':
                started = start_check(job, force=True, automatic=False)
                return self.send(200, {'checking': started or UPDATE['checking']})
            if self.path == '/api/preferences':
                value = request.get('auto_update')
                if not isinstance(value, bool):
                    return self.send(400, {'error': 'auto_update must be true or false'})
                try:
                    set_preference('auto_update', value)
                except OSError as error:
                    return self.send(500, {'error': str(error)})
                return self.send(200, {'preferences': preferences()})
            if self.path == '/api/restart':
                if handover is None or job.running:
                    return self.send(409, {'started': False})
                try:
                    handover.start()
                except RuntimeError as error:
                    return self.send(400, {'error': str(error)})
                return self.send(200, {'restarting': True})
            if self.path == '/api/plan':
                if not names:
                    return self.send(400, {'error': 'nothing selected'})
                result = subprocess.run([sys.executable, str(corsu.SRC / 'installer.py'), '--dry-run', '--components', *names],
                                        capture_output=True, text=True, encoding='utf-8', errors='replace',
                                        env={**os.environ, 'CORSU_LANG': language})
                lines = (result.stdout + result.stderr).strip().splitlines()
                # The dialog has its own title; drop the installer's heading line.
                if lines and lines[0].rstrip().endswith(':'):
                    lines = lines[1:]
                plan = '\n'.join(line.strip() for line in lines).strip()
                return self.send(200, {'plan': plan, 'ok': result.returncode == 0})
            if self.path in ('/api/install', '/api/uninstall', '/api/rescan'):
                DETECTED['time'] = 0.0
            if self.path == '/api/rescan':
                return self.send(200, {'ok': True})
            if self.path == '/api/install' and names:
                arguments = ['--yes', '--components', *[name for name in names if name != 'terminal']]
                started = job.start('install', arguments, language)
            elif self.path == '/api/switch' and names:
                started = job.start('switch', ['--enable' if request.get('on') else '--disable', *names], language)
            elif self.path == '/api/all':
                started = job.start('switch', ['--enable' if request.get('on') else '--disable'], language)
            elif self.path == '/api/pause':
                hours = request.get('hours')
                arguments = ['--disable', 'terminal'] + (['--hours', str(float(hours))] if hours else [])
                started = job.start('switch', arguments, language)
            elif self.path == '/api/uninstall':
                started = job.start('uninstall', ['--uninstall', '--yes'], language)
            else:
                return self.send(404, {'error': 'not found'})
            self.send(200 if started else 409, {'started': started})

    return Handler


SESSION = corsu.DATA / 'setup-session.json'
# The arguments this window was started with, given again to the copy that replaces it.
ARGUMENTS = []
# What the window knows about updates: the last check ('info'), whether one runs, the automatic update started in
# this window session, and how a restart went.
UPDATE = {'info': None, 'checking': False, 'auto_started': None, 'restart_error': None}
UPDATE_LOCK = threading.Lock()
PREFERENCES = 'preferences.json'
VERSION = re.compile(r'^\d+(\.\d+){1,3}$')


def version_tuple(text):
    return tuple(int(part) for part in str(text).lstrip('v').split('.') if part.isdigit())


def running_version():
    return json.loads((corsu.SRC / 'release.json').read_text(encoding='utf-8')).get('version')


def update_check(force=False):
    """update.check() (docs/update-architecture.md), or the same answer built from the older update.latest().
    Never raises: a failure is status 'unknown' with its reason."""
    current = running_version()
    try:
        check = getattr(update, 'check', None)
        if check:
            return check(force=force)
        found = update.latest(force=force)
    except Exception as error:  # A network or parsing failure must never keep the window from opening.
        return {'current': current, 'latest': None, 'tag': None, 'url': None, 'status': 'unknown', 'checked': None,
                'error': str(error) or error.__class__.__name__}
    if not found:
        return {'current': current, 'latest': None, 'tag': None, 'url': None, 'status': 'unknown', 'checked': None,
                'error': t('GitHub could not be reached', 'GitHub est injoignable')}
    latest = found['version']
    status = ('available' if version_tuple(latest) > version_tuple(current) else
              'ahead' if version_tuple(latest) < version_tuple(current) else 'up_to_date')
    return {'current': current, 'latest': latest, 'tag': 'v' + latest, 'url': found.get('url'), 'status': status,
            'checked': time.time(), 'error': None}


def preferences():
    """update.preferences(), or corsu.DATA/preferences.json read directly. `auto_update` defaults to off."""
    try:
        if hasattr(update, 'preferences'):
            found = update.preferences()
        else:
            found = json.loads((corsu.DATA / PREFERENCES).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        found = {}
    found = found if isinstance(found, dict) else {}
    return {**found, 'auto_update': found.get('auto_update') is True}


def set_preference(name, value):
    if hasattr(update, 'set_preference'):
        update.set_preference(name, value)
        return
    path = corsu.DATA / PREFERENCES
    try:
        saved = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        saved = {}
    saved = {**(saved if isinstance(saved, dict) else {}), name: value}
    corsu.DATA.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.corsu-tmp')
    temporary.write_text(json.dumps(saved, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def start_update(job, language, version=None):
    """The update job: update.py --install, for the exact version the window showed when it knows it."""
    arguments = ['--install'] + (['--version', version] if version and VERSION.match(version) else [])
    return job.start('update', arguments, language, script='update.py')


def claim_check():
    """Mark a check as running; False when one already is."""
    with UPDATE_LOCK:
        if UPDATE['checking']:
            return False
        UPDATE['checking'] = True
        return True


def check_update(job=None, force=False, automatic=True):
    """Look for a newer release (once when the window opens, again on request); the caller claimed the check
    (claim_check). With automatic updates on and a stable release out, start installing it, once per window session
    and never over another job."""
    try:
        UPDATE['info'] = update_check(force)
    finally:
        UPDATE['checking'] = False
    info = UPDATE['info']
    if (automatic and job is not None and info.get('status') == 'available' and UPDATE['auto_started'] is None
            and not job.running and preferences()['auto_update']):
        if start_update(job, 'fr' if corsu.french() else 'en', info.get('latest')):
            UPDATE['auto_started'] = info.get('latest') or '?'


def start_check(job, force=False, automatic=True):
    """A check in the background; the page follows it through /api/state. False when one already runs."""
    if not claim_check():
        return False
    threading.Thread(target=check_update, args=(job, force, automatic), daemon=True).start()
    return True


def release_record(state):
    """installation.json → release ({'folder', 'version', …}), written by the installer since one managed
    installation per user (docs/update-architecture.md)."""
    record = state.get('release') if isinstance(state, dict) else None
    return record if isinstance(record, dict) else {}


def shortcut_command():
    """[python, app.py] from the Corsu menu entry (Linux), or None."""
    entry = corsu.HOME / '.local/share/applications/corsu-setup.desktop'
    try:
        for line in entry.read_text(encoding='utf-8').splitlines():
            if line.startswith('Exec='):
                command = shlex.split(line[5:])
                if len(command) >= 2 and command[1].endswith('app.py'):
                    return command[:2]
    except (OSError, ValueError):
        pass
    return None


def installed_app(state):
    """[python, app.py] of the installed Corsu copy (the one launchers point to), or None when it cannot be told.
    From installation.json → release.folder, else the Corsu menu entry."""
    record = release_record(state)
    folder = record.get('folder')
    if folder:
        folder = Path(folder)
        app = next((candidate for candidate in (folder / 'src/app.py', folder / 'app.py') if candidate.is_file()), None)
        if app:
            python = record.get('python')
            python = python if python and Path(python).is_file() else str(corsu.python_launcher())
            return [python, str(app)]
    command = shortcut_command()
    if command and Path(command[1]).is_file():
        if not Path(command[0]).is_file():
            command[0] = str(corsu.python_launcher())
        return command
    return None


def installed_version(app):
    try:
        return json.loads((Path(app).parent / 'release.json').read_text(encoding='utf-8')).get('version')
    except (OSError, ValueError):
        return None


def restart_info(state, job):
    """Whether "Restart Corsu" is offered: the installed copy is another one than this window's, after an update
    that asked for it (@result restart_app) or with another version than the one running."""
    command = installed_app(state)
    if not command:
        return {'available': False, 'version': None, 'error': UPDATE['restart_error']}
    app = Path(command[1]).resolve()
    other = app.parent != corsu.SRC.resolve()
    version = installed_version(app)
    asked = bool(job.title == 'update' and isinstance(job.result, dict) and job.result.get('restart_app'))
    return {'available': other and not job.running and (asked or (version is not None and version != running_version())),
            'version': version, 'error': UPDATE['restart_error']}


MINECRAFT = {'time': 0.0, 'waiting': []}


def minecraft_waiting(state, result):
    """Minecraft game folders found since Corsu switched the others (a new launcher instance, a new profile folder):
    shown as waiting for activation, with their version. Nothing is written; looked up at most every 20 seconds."""
    if time.monotonic() - MINECRAFT['time'] < 20:
        return MINECRAFT['waiting']
    import minecraft
    known = set()
    for path, record in state.get('files', {}).items():
        if isinstance(record, dict) and record.get('component') == 'minecraft' and Path(path).name == 'options.txt':
            known.add(Path(path).parent)
    for instance in (result or {}).get('instances', []):
        if instance.get('location'):
            known.add(Path(instance['location']))
    known = {path.resolve() for path in known}
    waiting = []
    try:
        folders = [folder for folder in minecraft.find_folders()
                   if folder.path.resolve() not in known and folder.version and minecraft.target(folder.version)]
        running = minecraft.running_folders() if folders else set()
    except Exception:
        folders, running = [], set()
    for folder in folders:
        busy = minecraft.in_use(folder.path, running)
        waiting.append({
            'kind': folder.launcher, 'location': str(folder.path), 'version': folder.version, 'loader': folder.loader,
            'activation': 'waiting', 'coverage': None, 'note': None,
            'reason': t('New game folder: Corsu has not switched it yet.',
                        'Nouveau dossier de jeu : Corsu ne l\'a pas encore activé.'),
            'action': (t('Minecraft is running there; close it first.', 'Minecraft y est lancé ; fermez-le d\'abord.')
                       if busy else None)})
    MINECRAFT['waiting'], MINECRAFT['time'] = waiting, time.monotonic()
    return waiting


def running_session():
    """The address of a Corsu already open, so a second click shows it instead of starting another."""
    try:
        url = json.loads(SESSION.read_text(encoding='utf-8'))['url']
        request = urllib.request.Request(url + 'api/state', headers={'X-Corsu': '1'})
        with urllib.request.urlopen(request, timeout=2) as response:
            return url if response.status == 200 else None
    except (OSError, ValueError, KeyError):
        return None


class Server(ThreadingHTTPServer):
    # On Windows, SO_REUSEADDR lets a second program take a port already in use; Corsu must move to the next one
    # instead, so it asks for the port alone.
    allow_reuse_address = os.name != 'nt'

    def server_bind(self):
        if os.name == 'nt' and hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Handover:
    """Restart the window from the newly installed copy, at the same address, so the page only has to reload (and
    keeps what it saved for that address, such as its language). This server lets go of its port, the new copy
    starts detached and takes it (`--replace <port>`), and once it answers this process ends as soon as its window
    allows. When the new copy does not answer, this server takes its port back and the page says why. Nothing
    else is stopped."""

    WAIT = 30

    def __init__(self, job, activity, holder, port):
        self.job, self.activity, self.holder, self.port = job, activity, holder, port
        self.lock = threading.Lock()
        self.running = False
        self.done = False
        self.process = None

    def start(self):
        with self.lock:
            if self.running or self.done:
                return
            state = corsu.load_state() if corsu.STATE.exists() else {}
            command = installed_app(state)
            if not command or not restart_info(state, self.job)['available']:
                raise RuntimeError(t('There is no newer installed copy of Corsu to restart from.',
                                     'Il n\'y a pas de copie installée plus récente de Corsu à redémarrer.'))
            self.running = True
        UPDATE['restart_error'] = None
        threading.Thread(target=self.run, args=(command,), daemon=True).start()

    def launch(self, command):
        options = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL,
                   'cwd': str(Path(command[1]).parent), 'close_fds': True}
        if os.name == 'nt':
            options['creationflags'] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        else:
            options['start_new_session'] = True
        return subprocess.Popen([*command, *ARGUMENTS, '--replace', str(self.port)], **options)

    def answered(self, url):
        try:
            request = urllib.request.Request(url + 'api/state', headers={'X-Corsu': '1'})
            with urllib.request.urlopen(request, timeout=3) as response:
                return json.load(response).get('pid') not in (None, os.getpid())
        except (OSError, ValueError, AttributeError):
            return False

    def run(self, command):
        time.sleep(0.3)  # The page gets its answer before the port closes.
        server = self.holder['server']
        server.shutdown()
        server.server_close()
        url = f'http://127.0.0.1:{self.port}/'
        error = None
        try:
            process = self.process = self.launch(command)
        except OSError as failure:
            process, error = None, str(failure)
        deadline = time.monotonic() + self.WAIT
        while process and time.monotonic() < deadline:
            if self.answered(url):
                self.done = True
                self.running = False
                return
            if process.poll() is not None:
                error = t(f'the new copy stopped (code {process.returncode})',
                          f'la nouvelle copie s\'est arrêtée (code {process.returncode})')
                break
            time.sleep(0.3)
        else:
            error = error or t('the new copy did not answer', 'la nouvelle copie n\'a pas répondu')
        UPDATE['restart_error'] = error
        self.activity[0] = time.monotonic()
        try:
            self.holder['server'] = bind(self.port, self.job, self.activity, self, wait=self.WAIT)
            threading.Thread(target=self.holder['server'].serve_forever, daemon=True).start()
        except OSError:
            # The port went to another program; this window can no longer be reached.
            self.done = True
        finally:
            self.running = False


def bind(port, job, activity, handover=None, wait=0):
    """A server on exactly `port`, retried for `wait` seconds while the copy being replaced lets go of it."""
    deadline = time.monotonic() + wait
    while True:
        try:
            return Server(('127.0.0.1', port), make_handler(job, activity, port, handover))
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.2)


def listen(job, activity, handover=None):
    """Serve on the fixed port, or the next free one when another program holds it."""
    for port in PORTS:
        try:
            return Server(('127.0.0.1', port), make_handler(job, activity, port, handover))
        except OSError:
            continue
    raise RuntimeError(t(f'Ports {PORTS.start} to {PORTS.stop - 1} are all in use; close the program using them.',
                         f'Les ports {PORTS.start} à {PORTS.stop - 1} sont tous utilisés ; fermez le programme qui les occupe.'))


def serve(mode='window', replace=None):
    """Run Corsu at its address. `mode`: 'window' (its own window, the browser when none is possible), 'browser'
    or 'none' (only the address). `replace`: the port of the Corsu window this copy takes over after an update;
    that window keeps showing the page, which reloads from here."""
    if replace is None:
        existing = running_session()
        if existing:
            if mode != 'none':
                import window
                window.show(existing, mode)
            return
    job = Job()
    activity = [time.monotonic()]
    holder = {}
    if replace is None:
        server = listen(job, activity)
    else:
        mode = 'none'
        try:
            server = bind(replace, job, activity, wait=Handover.WAIT)
        except OSError:
            return
    port = server.server_address[1]
    handover = Handover(job, activity, holder, port)
    server.RequestHandlerClass = make_handler(job, activity, port, handover)
    holder['server'] = server
    url = f'http://localhost:{port}/'
    threading.Thread(target=server.serve_forever, daemon=True).start()
    start_check(job)
    try:
        corsu.DATA.mkdir(parents=True, exist_ok=True)
        SESSION.write_text(json.dumps({'url': url}), encoding='utf-8')
        if corsu.PLATFORM != 'windows':
            SESSION.chmod(0o600)
    except OSError:
        pass
    print(t(f'Corsu is open at {url} until you close it.', f'Corsu est ouvert à l\'adresse {url} jusqu\'à sa fermeture.'),
          flush=True)
    idle = IDLE_SECONDS
    if mode != 'none':
        import window
        # The window blocks until it is closed; a browser tab returns at once and the idle timer decides.
        if window.show(url.replace('localhost', '127.0.0.1'), mode):
            idle = CLOSED_IDLE_SECONDS
            activity[0] = time.monotonic()
    try:
        while not handover.done and (handover.running or job.running or time.monotonic() - activity[0] < idle):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    if handover.done:
        # The new copy serves the address and owns the session file now.
        return
    holder['server'].shutdown()
    SESSION.unlink(missing_ok=True)


def apply(wanted):
    """Switch on what is in `wanted`, off what is not. Returns a short report."""
    state = corsu.load_state()
    current = {name: not corsu.is_disabled(name, state) for name in corsu.switchable(state)}
    turn_on = [name for name, on in current.items() if name in wanted and not on]
    turn_off = [name for name, on in current.items() if name not in wanted and on]
    if turn_off:
        corsu.disable(turn_off)
    if turn_on:
        corsu.enable(turn_on)
    if not (turn_on or turn_off):
        return t('Nothing to change.', 'Rien à changer.')
    return t('Done. Restart the programs concerned.', 'C\'est fait. Redémarrez les logiciels concernés.')


def run_text():
    if not corsu.STATE.exists():
        os.execv(sys.executable, [sys.executable, str(corsu.SRC / 'installer.py')])
    language = 'fr' if installer.french() else 'en'
    while True:
        state = corsu.load_state()
        items = [(name, components()[name][language][0], not corsu.is_disabled(name, state)) for name in corsu.switchable(state)]
        print('\nCorsu')
        for number, (name, label, on) in enumerate(items, 1):
            print(f'  [{"x" if on else " "}] {number}. {label}')
        print(t('  p. Terminal in French for 1 hour   s. Add programs   q. Quit',
                '  p. Terminal en français 1 heure   s. Ajouter des logiciels   q. Quitter'))
        answer = input(t('Type a number to switch it, or a letter: ',
                         'Tapez un numéro pour l\'inverser, ou une lettre : ')).strip().lower()
        if answer in ('q', ''):
            return
        if answer == 'p':
            corsu.disable(['terminal'], hours=1)
        elif answer == 's':
            os.execv(sys.executable, [sys.executable, str(corsu.SRC / 'installer.py')])
        elif answer.isdigit() and 1 <= int(answer) <= len(items):
            name = items[int(answer) - 1][0]
            wanted = {n for n, _, o in items if o} ^ {name}
            print(apply(wanted))


def main():
    for name in ('stdout', 'stderr'):
        # pythonw.exe, used by the Windows shortcut, has no console at all.
        stream = getattr(sys, name)
        if stream is None:
            setattr(sys, name, open(os.devnull, 'w', encoding='utf-8'))
        else:
            stream.reconfigure(errors='replace')
    import logbook
    logbook.start('app')
    try:
        if '--text' in sys.argv:
            return run_text()
        replace = None
        if '--replace' in sys.argv:
            position = sys.argv.index('--replace')
            value = sys.argv[position + 1] if position + 1 < len(sys.argv) else ''
            replace = int(value) if value.isdigit() and int(value) in PORTS else None
            del sys.argv[position:position + 2]
        ARGUMENTS[:] = [argument for argument in sys.argv[1:] if argument in ('--browser', '--no-browser')]
        serve('none' if '--no-browser' in sys.argv else 'browser' if '--browser' in sys.argv else 'window', replace)
    except Exception as error:
        print(logbook.failure(error), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
