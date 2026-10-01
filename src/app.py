#!/usr/bin/env python3
"""Corsu Setup: install Corsu, switch each part on or off, pause the terminal, remove everything.

The window is a local page opened in the browser, served on 127.0.0.1 only and protected by a random key, so it
works the same way on Windows, macOS and Linux without extra libraries. `--text` gives a menu in the terminal.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import webbrowser

import corsu
import installer
from installer import t

PAGE = Path(__file__).resolve().parent / 'app/index.html'
# The page asks for news every few seconds; without any for this long, the window was closed.
IDLE_SECONDS = 600

COMPONENTS = {
    'firefox': {'en': ('Firefox', 'Menus, settings, error pages, and the labels Google leaves untranslated.'),
                'fr': ('Firefox', 'Menus, réglages, pages d\'erreur, et les libellés que Google laisse non traduits.')},
    'chromium': {'en': ('Chrome, Opera GX and other browsers', 'Menus and settings of Chromium-based browsers.'),
                 'fr': ('Chrome, Opera GX et autres navigateurs', 'Menus et réglages des navigateurs basés sur Chromium.')},
    'discord': {'en': ('Discord', 'The interface, through Vencord. Messages are never changed.'),
                'fr': ('Discord', 'L\'interface, grâce à Vencord. Les messages ne sont jamais modifiés.')},
    'vesktop': {'en': ('Vesktop', 'The interface of this Discord app, through Vencord.'),
                'fr': ('Vesktop', 'L\'interface de cette application Discord, grâce à Vencord.')},
    'desktop': {'en': ('KDE Plasma desktop', 'The desktop, KDE programs and the application menu.'),
                'fr': ('Bureau KDE Plasma', 'Le bureau, les programmes KDE et le menu des applications.')},
    'qt': {'en': ('System translations', 'GTK programs, terminal commands and Qt dialogs. Asks for your password.'),
           'fr': ('Traductions système', 'Programmes GTK, commandes du terminal et boîtes de dialogue Qt. '
                  'Demande votre mot de passe.')},
    'terminal': {'en': ('Terminal commands', 'Can go back to French for an hour, in new terminal windows.'),
                 'fr': ('Commandes du terminal', 'Peut repasser en français pendant une heure, dans les nouveaux '
                        'terminaux.')},
}
ORDER = ['firefox', 'chromium', 'discord', 'vesktop', 'desktop', 'qt', 'terminal']


class Job:
    """One installer run at a time; its output is shown live in the page."""

    def __init__(self):
        self.lock = threading.Lock()
        self.title = ''
        self.lines = []
        self.running = False
        self.ok = None

    def start(self, title, arguments, language):
        with self.lock:
            if self.running:
                return False
            self.title, self.lines, self.running, self.ok = title, [], True, None
        environment = {**os.environ, 'CORSU_LANG': language, 'PYTHONUNBUFFERED': '1', 'PYTHONIOENCODING': 'utf-8',
                       'CORSU_SETUP_WINDOW': '1'}
        command = [sys.executable, str(corsu.SRC / 'installer.py'), *arguments]
        threading.Thread(target=self.run, args=(command, environment), daemon=True).start()
        return True

    def run(self, command, environment):
        try:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                                       env=environment)
            for line in process.stdout:
                # Commands the installer runs are echoed with "+ "; they are noise for most people.
                if not line.startswith('+ '):
                    self.lines.append(line.rstrip('\n'))
            ok = process.wait() == 0
        except OSError as error:
            self.lines.append(str(error))
            ok = False
        with self.lock:
            self.running, self.ok = False, ok

    def snapshot(self):
        return {'title': self.title, 'lines': self.lines[-400:], 'running': self.running, 'ok': self.ok}


DETECTED = {'time': 0.0, 'names': set()}


def detected():
    """The programs found on this computer, looked up again at most every 20 seconds."""
    if time.monotonic() - DETECTED['time'] > 20:
        DETECTED['names'], DETECTED['time'] = set(installer.available_components()), time.monotonic()
    return DETECTED['names']


def snapshot():
    """Everything the page shows, read fresh each time."""
    state = corsu.load_state()
    installed = set(state.get('components', [])) if corsu.STATE.exists() else set()
    if state.get('qt_system'):
        installed.add('qt')
    available = detected()
    switchable = set(corsu.switchable(state)) if corsu.STATE.exists() else set()
    paused = corsu.terminal_paused_until() if 'terminal' in switchable else None
    items = []
    for name in ORDER:
        if name == 'terminal' and name not in switchable:
            continue
        if name not in available | installed | switchable:
            continue
        items.append({'name': name, 'text': COMPONENTS[name], 'installed': name in installed or name in switchable,
                      'switchable': name in switchable,
                      'on': name in switchable and not corsu.is_disabled(name, state)})
    profile = corsu.firefox_profile() if 'firefox' in installed else None
    return {
        'version': json.loads((corsu.SRC / 'release.json').read_text(encoding='utf-8')).get('version'),
        'platform': corsu.PLATFORM,
        'language': 'fr' if corsu.french() else 'en',
        'installed': bool(installed),
        'everything_off': corsu.disabled_marker().exists(),
        'items': items,
        'terminal_paused_until': paused,
        'firefox_profile': str(profile) if profile else None,
        'lexicon_entries': len(corsu.WORDS),
    }


def make_handler(key, job, activity):
    page = PAGE.read_bytes()

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
            # Other pages open in the browser cannot read the key, so they cannot drive Corsu.
            host = self.headers.get('Host', '')
            return host.startswith(('127.0.0.1:', 'localhost:')) and secrets.compare_digest(
                self.headers.get('X-Corsu-Key', ''), key)

        def do_GET(self):
            activity[0] = time.monotonic()
            if self.path.split('?')[0] == '/':
                return self.send(200, page, 'text/html; charset=utf-8')
            if self.path == '/api/state' and self.allowed():
                return self.send(200, {**snapshot(), 'job': job.snapshot()})
            self.send(404, {'error': 'not found'})

        def do_POST(self):
            activity[0] = time.monotonic()
            if not self.allowed():
                return self.send(403, {'error': 'forbidden'})
            length = min(int(self.headers.get('Content-Length') or 0), 65536)
            try:
                request = json.loads(self.rfile.read(length) or b'{}')
            except ValueError:
                return self.send(400, {'error': 'bad request'})
            language = 'fr' if request.get('language') == 'fr' else 'en'
            names = [name for name in request.get('components', []) if name in COMPONENTS]
            if self.path == '/api/plan':
                if not names:
                    return self.send(400, {'error': 'nothing selected'})
                result = subprocess.run([sys.executable, str(corsu.SRC / 'installer.py'), '--dry-run', '--components', *names],
                                        capture_output=True, text=True, encoding='utf-8', errors='replace',
                                        env={**os.environ, 'CORSU_LANG': language})
                return self.send(200, {'plan': (result.stdout + result.stderr).strip(), 'ok': result.returncode == 0})
            if self.path in ('/api/install', '/api/uninstall'):
                DETECTED['time'] = 0.0
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


def running_session():
    """The address of a Corsu Setup already open, so a second click shows it instead of starting another."""
    try:
        url = json.loads(SESSION.read_text(encoding='utf-8'))['url']
        request = urllib.request.Request(url.split('#')[0] + 'api/state', headers={'X-Corsu-Key': url.split('#')[1]})
        with urllib.request.urlopen(request, timeout=2) as response:
            return url if response.status == 200 else None
    except (OSError, ValueError, KeyError, IndexError):
        return None


def serve(open_browser=True):
    existing = running_session()
    if existing:
        if open_browser:
            webbrowser.open(existing)
        return
    key = secrets.token_urlsafe(24)
    job = Job()
    activity = [time.monotonic()]
    server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(key, job, activity))
    url = f'http://127.0.0.1:{server.server_address[1]}/#{key}'
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        corsu.DATA.mkdir(parents=True, exist_ok=True)
        SESSION.write_text(json.dumps({'url': url}), encoding='utf-8')
        if corsu.PLATFORM != 'windows':
            SESSION.chmod(0o600)
    except OSError:
        pass
    print(t(f'Corsu Setup is open in your browser. If not, open this address:\n  {url}\nClose this window to stop.',
            f'Corsu Setup est ouvert dans votre navigateur. Sinon, ouvrez cette adresse :\n  {url}\n'
            'Fermez cette fenêtre pour arrêter.'), flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        while job.running or time.monotonic() - activity[0] < IDLE_SECONDS:
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    server.shutdown()
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
        items = [(name, COMPONENTS[name][language][0], not corsu.is_disabled(name, state)) for name in corsu.switchable(state)]
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
    if '--text' in sys.argv:
        return run_text()
    serve(open_browser='--no-browser' not in sys.argv)


if __name__ == '__main__':
    main()
