#!/usr/bin/env python3
"""The Corsu app: install Corsu, switch each part on or off, pause the terminal, remove everything.

The window is a local page served on 127.0.0.1 at a fixed address (http://localhost:7744 while Corsu is open), shown
in a window of its own (see window.py) or in any browser. `--browser` opens it in the browser instead of a window,
`--text` gives a menu in the terminal.
"""
import json
import os
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
    'terminal': {'co': ('Terminale', 'I messaghji di e cummande, in i novi terminali.'),
                'en': ('Terminal', 'Command messages, in new terminal windows.'),
                 'fr': ('Terminal', 'Les messages des commandes, dans les nouveaux terminaux.')},
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
        self.progress = None

    def start(self, title, arguments, language, script='installer.py'):
        with self.lock:
            if self.running:
                return False
            self.title, self.lines, self.running, self.ok, self.progress = title, [], True, None, None
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
                'progress': self.progress}


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
        text = COMPONENTS[name]
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
        items.append({'name': name, 'text': text, 'installed': name in installed or name in switchable,
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
        'review': review.progress_all(),
        'options': review.options(),
        'update': UPDATE.get('info'),
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


def make_handler(job, activity, port):
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
                return self.send(200, {**snapshot(), 'job': job.snapshot()})
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
            names = [name for name in request.get('components', []) if name in COMPONENTS]
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
                started = job.start('update', ['--install'], language, script='update.py')
                return self.send(200 if started else 409, {'started': started})
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
UPDATE = {}


def check_update():
    """Look for a newer release in the background, once per window."""
    UPDATE['info'] = update.latest()


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


def listen(job, activity):
    """Serve on the fixed port, or the next free one when another program holds it."""
    for port in PORTS:
        try:
            return Server(('127.0.0.1', port), make_handler(job, activity, port))
        except OSError:
            continue
    raise RuntimeError(t(f'Ports {PORTS.start} to {PORTS.stop - 1} are all in use; close the program using them.',
                         f'Les ports {PORTS.start} à {PORTS.stop - 1} sont tous utilisés ; fermez le programme qui les occupe.'))


def serve(mode='window'):
    """Run Corsu at its address. `mode`: 'window' (its own window, the browser when none is possible), 'browser'
    or 'none' (only the address)."""
    existing = running_session()
    if existing:
        if mode != 'none':
            import window
            window.show(existing, mode)
        return
    job = Job()
    activity = [time.monotonic()]
    server = listen(job, activity)
    url = f'http://localhost:{server.server_address[1]}/'
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=check_update, daemon=True).start()
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
        while job.running or time.monotonic() - activity[0] < idle:
            time.sleep(1)
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
    import logbook
    logbook.start('app')
    try:
        if '--text' in sys.argv:
            return run_text()
        serve('none' if '--no-browser' in sys.argv else 'browser' if '--browser' in sys.argv else 'window')
    except Exception as error:
        print(logbook.failure(error), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
