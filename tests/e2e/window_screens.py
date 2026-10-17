#!/usr/bin/env python3
"""Screenshots of Corsu's window page in typical situations, from fixed sample states (no installation needed).

Usage: window_screens.py CHROME OUTPUT_DIR [--only NAME ...]
Serves src/app/ with a small local server whose /api/state answers a sample state (empty, active, partial, blocked,
failed, update available, operation running, damaged record), loads the page in headless Chrome and saves one PNG
per situation, in light and dark, wide and narrow, with larger text and zoom. The appearance endpoints of
src/appearance.py are used when that module exists, with its data in a temporary folder, so the same script shows
the page before and after the redesign. Nothing of the person's own Corsu is read or written: HOME points to a
temporary folder while it runs. This is the page with sample data, not an observation of a real installation.
"""
import base64
import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
APP = ROOT / 'src' / 'app'
sys.path.insert(0, str(HERE))
from check_chromium import DevTools  # noqa: E402


def texts():
    """Each part's real name and description, as the window shows them."""
    sys.path.insert(0, str(ROOT / 'src'))
    import app
    return app.components()


def item(texts, name, on=True, activation=None, **extra):
    record = {'name': name, 'text': texts[name], 'installed': True, 'switchable': True, 'on': on,
              'activation': activation or ('active' if on else 'inactive'), 'instances': [], 'coverage': None,
              'validation': None, 'updated': None}
    record.update(extra)
    return record


def states():
    names = texts()
    validation = {'simulated': True, 'real_app': ['linux'], 'visual': True, 'linguistic_review': False}
    base = {'version': '0.25.0', 'pid': 4242, 'platform': 'linux', 'language': 'fr', 'installed': True,
            'everything_off': False, 'terminal_paused_until': None, 'firefox_profile': '/home/ana/.local/share/corsu/firefox/profile',
            'lexicon_entries': 119398, 'review': {}, 'options': {'showOriginal': False},
            'update': {'current': '0.25.0', 'latest': '0.25.0', 'status': 'up_to_date', 'checked': 1792230000,
                       'error': None, 'checking': False, 'auto_started': None, 'restart': {}},
            'preferences': {'auto_update': False}, 'problem': None,
            'job': {'title': None, 'lines': [], 'running': False, 'ok': None, 'progress': None, 'result': None, 'busy': False}}
    minecraft = item(names, 'minecraft', instances=[
        {'kind': 'Prism Launcher', 'location': '/home/ana/.local/share/PrismLauncher/instances/26.3/minecraft',
         'version': '26.3', 'loader': None, 'activation': 'active', 'reason': None, 'action': None,
         'coverage': {'state': 'complete', 'translated': 8559, 'total': 8559, 'note': None}, 'note': None},
        {'kind': 'Minecraft Launcher', 'location': '/home/ana/.minecraft', 'version': '1.21.4', 'loader': 'Fabric',
         'activation': 'active', 'reason': None, 'action': None,
         'coverage': {'state': 'partial', 'translated': 7012, 'total': 7440, 'note': None}, 'note': None}],
        coverage={'state': 'complete', 'translated': 8559, 'total': 8559, 'note': None}, updated=1792230000)
    vlc = item(names, 'vlc', coverage={'state': 'partial', 'translated': 4120, 'total': 5877, 'note': None},
               validation=validation,
               complement={'available': True, 'enabled': True, 'translations': 1757, 'reason': None})
    active = [item(names, 'firefox'), item(names, 'discord'), item(names, 'desktop'), minecraft, vlc,
              item(names, 'poedit', coverage={'state': 'complete', 'translated': 1, 'total': 1, 'note': None}, validation=validation),
              item(names, 'audacity', on=False)]
    result = {}
    result['active'] = {**base, 'items': active}
    empty = copy.deepcopy(base)
    empty.update(installed=False, firefox_profile=None, items=[
        {**item(names, name, on=False), 'installed': False, 'switchable': False, 'activation': None}
        for name in ('firefox', 'discord', 'desktop', 'vlc', 'poedit')])
    result['empty'] = empty
    trouble = copy.deepcopy(active)
    trouble[3]['activation'] = 'partial'
    trouble[3]['instances'][1].update(activation='blocked', reason='Minecraft est ouvert sur ce dossier.',
                                      action='Fermez Minecraft, puis réactivez.')
    trouble[3]['waiting'] = 1
    trouble[5].update(activation='failed', on=False, instances=[{'kind': 'Poedit', 'location': '/usr/bin/poedit',
                      'version': '3.6.3', 'loader': None, 'activation': 'failed',
                      'reason': "L'entrée de menu n'a pas pu être écrite.", 'action': None, 'coverage': None, 'note': None}])
    trouble.append(item(names, 'pdfsam', activation='restart_required'))
    result['attention'] = {**base, 'items': trouble}
    update = copy.deepcopy(result['active'])
    update['update'].update(latest='0.26.0', status='available')
    result['update'] = update
    running = copy.deepcopy(result['active'])
    running['job'] = {'title': 'install', 'running': True, 'ok': None, 'busy': False, 'result': None,
                      'progress': {'percent': 42, 'label': 'Firefox : vérification de la langue française'},
                      'lines': ['Firefox: téléchargement (91 Mo)…', 'Firefox: vérification de la signature…']}
    result['running'] = running
    failed = copy.deepcopy(result['active'])
    failed['job'] = {'title': 'switch', 'running': False, 'ok': False, 'busy': False, 'result': None, 'progress': None,
                     'lines': ['VLC : passage en corse…', 'Erreur : le catalogue de VLC est en lecture seule.']}
    failed['problem'] = "Le fichier installation.json est endommagé ; une copie a été gardée sous installation.json.damaged."
    result['error'] = failed
    many = copy.deepcopy(result['active'])
    for name in ('pdfsam', 'freac', 'tenacity', 'chromium', 'vesktop', 'qt', 'kde', 'terminal'):
        if name in names and not any(entry['name'] == name for entry in many['items']):
            many['items'].append(item(names, name, on=name != 'chromium'))
    result['many'] = many
    return result


SCENES = [
    # name, state, page, width, height, scheme, zoom, font size
    ('programs-light', 'active', 'programs', 1040, 780, 'light', 1, 16),
    ('programs-dark', 'active', 'programs', 1040, 780, 'dark', 1, 16),
    ('programs-many', 'many', 'programs', 1040, 1100, 'light', 1, 16),
    ('programs-narrow', 'active', 'programs', 420, 900, 'light', 1, 16),
    ('programs-zoom200', 'active', 'programs', 1040, 780, 'light', 2, 16),
    ('programs-large-text', 'active', 'programs', 1040, 900, 'light', 1, 24),
    ('attention', 'attention', 'programs', 1040, 1000, 'light', 1, 16),
    ('attention-dark', 'attention', 'programs', 1040, 1000, 'dark', 1, 16),
    ('empty-add', 'empty', 'add', 1040, 780, 'light', 1, 16),
    ('update-available', 'update', 'programs', 1040, 780, 'light', 1, 16),
    ('running', 'running', 'programs', 1040, 780, 'light', 1, 16),
    ('error', 'error', 'programs', 1040, 900, 'dark', 1, 16),
    ('about', 'update', 'about', 1040, 900, 'light', 1, 16),
    ('appearance', 'active', 'appearance', 1040, 900, 'light', 1, 16),
    ('appearance-dark', 'active', 'appearance', 1040, 900, 'dark', 1, 16),
]


def serve(folder, state_holder, data):
    """The page and its files from src/app, sample states, and src/appearance.py when present."""
    appearance = None
    if (ROOT / 'src' / 'appearance.py').exists():
        sys.path.insert(0, str(ROOT / 'src'))
        import appearance as module
        appearance = module

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *arguments):
            pass

        def reply(self, status, body, kind='application/json; charset=utf-8'):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def answer(self, method):
            path = self.path.split('?')[0]
            if appearance and hasattr(appearance, 'handle'):
                length = int(self.headers.get('Content-Length') or 0)
                body = self.rfile.read(length) if length else b''
                found = appearance.handle(method, path, body, self.headers)
                if found is not None:
                    return self.reply(*found)
            if method == 'GET' and path == '/api/state':
                return self.reply(200, state_holder[0])
            if method == 'POST' and path.startswith('/api/'):
                return self.reply(200, {'started': False})
            if method == 'GET' and path.startswith('/api/review'):
                return self.reply(200, {'item': None, 'progress': {'Discord': {'done': 0, 'total': 0, 'fixed': 0}}})
            name = 'index.html' if path == '/' else path.lstrip('/')
            file = (APP / name).resolve()
            if method == 'GET' and file.is_file() and APP in file.parents:
                kinds = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
                         '.js': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml'}
                return self.reply(200, file.read_bytes(), kinds.get(file.suffix, 'application/octet-stream'))
            self.reply(404, {'error': 'not found'})

        def do_GET(self):
            self.answer('GET')

        def do_POST(self):
            self.answer('POST')

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def chrome(executable, profile, font):
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    (Path(profile) / 'Default').mkdir(parents=True, exist_ok=True)
    (Path(profile) / 'Default' / 'Preferences').write_text(json.dumps(
        {'webkit': {'webprefs': {'default_font_size': font}}}))
    command = [executable, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
               f'--user-data-dir={profile}', '--lang=fr', f'--remote-debugging-port={port}', '--no-first-run',
               '--no-default-browser-check', 'about:blank']
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 60
    while True:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=2) as response:
                return process, DevTools(json.load(response)['webSocketDebuggerUrl'])
        except OSError:
            if process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('The browser did not start')
            time.sleep(0.3)


def shoot(devtools, url, scene, output, language='fr'):
    name, _, page, width, height, scheme, zoom, _ = scene
    target = devtools.call('Target.createTarget', {'url': 'about:blank'})['targetId']
    session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
    try:
        devtools.call('Page.enable', session=session)
        devtools.call('Emulation.setDeviceMetricsOverride', {'width': int(width / zoom), 'height': int(height / zoom),
                                                             'deviceScaleFactor': zoom, 'mobile': False}, session=session)
        devtools.call('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-color-scheme', 'value': scheme}]},
                      session=session)
        devtools.call('Page.addScriptToEvaluateOnNewDocument', {'source':
                      f'try {{ localStorage.setItem("corsu-language", "{language}"); }} catch (e) {{}}'}, session=session)
        devtools.call('Page.navigate', {'url': url}, session=session)
        time.sleep(1.5)
        devtools.call('Runtime.evaluate', {'expression':
                      f'(document.querySelector(\'[data-page="{page}"]\') || {{click() {{}}}}).click()'}, session=session)
        time.sleep(0.8)
        data = devtools.call('Page.captureScreenshot', {'format': 'png'}, session=session)['data']
        path = Path(output) / f'{name}.png'
        path.write_bytes(base64.b64decode(data))
        return path
    finally:
        devtools.call('Target.closeTarget', {'targetId': target})


def main(arguments):
    executable, output = arguments[0], Path(arguments[1])
    only = set(arguments[arguments.index('--only') + 1:]) if '--only' in arguments else None
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='corsu-screens-') as temporary:
        os.environ['HOME'] = temporary
        os.environ['XDG_DATA_HOME'] = str(Path(temporary) / 'data')
        os.environ['XDG_CONFIG_HOME'] = str(Path(temporary) / 'config')
        samples = states()
        holder = [None]
        server = serve(APP, holder, temporary)
        url = f'http://127.0.0.1:{server.server_address[1]}/'
        failures = 0
        for font in sorted({scene[7] for scene in SCENES}):
            process, devtools = chrome(executable, Path(temporary) / f'profile-{font}', font)
            try:
                for scene in SCENES:
                    if scene[7] != font or (only and scene[0] not in only):
                        continue
                    holder[0] = samples[scene[1]]
                    try:
                        print('saved', shoot(devtools, url, scene, output))
                    except (RuntimeError, OSError) as error:
                        failures += 1
                        print(f'FAIL {scene[0]}: {error}')
            finally:
                process.terminate()
                process.wait(timeout=20)
        server.shutdown()
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
