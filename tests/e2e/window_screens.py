#!/usr/bin/env python3
"""Screenshots of Corsu's window page in typical situations, from fixed sample states (no installation needed).

Usage: window_screens.py CHROME OUTPUT_DIR [--only NAME ...]
Serves src/app/ with the window's own server (src/app.py), whose /api/state answers a sample state (empty, active,
partial, blocked, failed, update available, operation running, damaged record), opens the page as Corsu does (with a
ticket for the window's key), loads it in headless Chrome and saves one PNG per situation, in light and dark, wide and
narrow, with larger text and zoom. Appearance settings are saved through src/appearance.py, its data in a temporary
folder. Nothing of the person's own Corsu is read or written: HOME points to a
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
    # The appearance contract on <html> (docs/window-design.md), set before the page draws.
    ('help', 'active', 'help', 1040, 780, 'light', 1, 16),
    ('review-dark', 'active', 'review', 1040, 780, 'dark', 1, 16),
    ('attention-narrow', 'attention', 'programs', 420, 1000, 'light', 1, 16),
    # Appearance settings saved through src/appearance.py (as the Appearance page saves them), with sample pictures.
    ('palette-mare', 'attention', 'programs', 1040, 780, 'light', 1, 16, {'palette': 'mare'}),
    ('palette-granitu-dark', 'attention', 'programs', 1040, 780, 'dark', 1, 16, {'palette': 'granitu', 'theme': 'dark'}),
    ('palette-tramontu', 'update', 'programs', 1040, 780, 'light', 1, 16, {'palette': 'tramontu'}),
    ('palette-notte-dark', 'running', 'programs', 1040, 780, 'light', 1, 16, {'palette': 'notte', 'theme': 'dark'}),
    ('compact', 'many', 'programs', 1040, 1100, 'light', 1, 16, {'density': 'compact'}),
    ('accent-yellow', 'attention', 'programs', 1040, 780, 'light', 1, 16, {'accent': '#ffe600'}),
    ('image-busy', 'attention', 'programs', 1040, 780, 'light', 1, 16, {'picture': 'busy', 'dim': 0.15, 'blur': 14}),
    ('image-busy-dark', 'attention', 'programs', 1040, 780, 'dark', 1, 16, {'picture': 'busy', 'dim': 0.55}),
    ('image-light', 'active', 'programs', 1040, 780, 'light', 1, 16, {'picture': 'light', 'dim': 0}),
    ('image-dark', 'active', 'programs', 1040, 780, 'light', 1, 16, {'picture': 'dark', 'dim': 0}),
    ('image-busy-narrow', 'attention', 'programs', 420, 900, 'dark', 1, 16, {'picture': 'busy', 'dim': 0.3, 'blur': 8}),
    ('image-appearance', 'active', 'appearance', 1040, 900, 'light', 1, 16, {'picture': 'busy', 'dim': 0.55, 'blur': 6}),
]

# A busy, high-contrast picture: text over it must stay readable.
def sample_png(kind, width=1200, height=800):
    """A synthetic picture: 'busy' (strong colours and fine detail), 'light' (almost white) or 'dark' (almost black)."""
    import struct
    import zlib
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            if kind == 'busy':
                pixel = ((x * 7 ^ y * 3) & 255, (x * y // 97) & 255, (255 - x // 5 + (y // 9 % 2) * 120) & 255)
            elif kind == 'light':
                pixel = (250 - y // 80, 248, 244 - x // 200)
            else:
                pixel = (8 + y // 100, 10 + x // 150, 14)
            rows += bytes(pixel)

    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes(rows), 6)) + chunk(b'IEND', b''))


def prepare_appearance(settings):
    """Save the scene's appearance in the temporary Corsu data, as the Appearance page would."""
    sys.path.insert(0, str(ROOT / 'src'))
    import appearance
    appearance.reset()
    settings = dict(settings)
    picture = settings.pop('picture', None)
    if picture:
        appearance.store_background(sample_png(picture))
        settings['background'] = 'image'
    if settings:
        appearance.update(settings)


def serve(folder, state_holder, data):
    """The window's own server (src/app.py: page, files, appearance routes and every check, the window's key
    included), its /api/state answering the sample state of the scene and the review page an empty review."""
    sys.path.insert(0, str(ROOT / 'src'))
    import corsu
    corsu.DATA = Path(data) / 'corsu-data'
    import app
    app.SESSION = corsu.DATA / 'setup-session.json'
    app.snapshot = lambda job=None: copy.deepcopy(state_holder[0])
    app.review.next_item = lambda section: None
    app.review.progress_all = lambda: {'Discord': {'done': 0, 'total': 0, 'fixed': 0}}
    job = app.Job()
    # The scene's operation (running, failed…), not this test server's idle one.
    job.snapshot = lambda: copy.deepcopy(state_holder[0]['job'])
    server = app.Server(('127.0.0.1', 0), app.make_handler(job, [0.0], 0))
    port = server.server_address[1]
    server.RequestHandlerClass = app.make_handler(job, [0.0], port)
    # Each scene opens the page as Corsu opens its window: the address with a fresh ticket after '#'.
    server.opening = lambda: f'http://127.0.0.1:{port}/#t=' + app.ACCESS.ticket()
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
    name, _, page, width, height, scheme, zoom, font = scene[:8]
    settings = scene[8] if len(scene) > 8 else {}
    target = devtools.call('Target.createTarget', {'url': 'about:blank'})['targetId']
    session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
    try:
        devtools.call('Page.enable', session=session)
        # The person's default text size (headless browsers ignore the profile's preference): rem and em follow it.
        devtools.call('Page.setFontSizes', {'fontSizes': {'standard': font, 'fixed': round(font * 13 / 16)}}, session=session)
        devtools.call('Emulation.setDeviceMetricsOverride', {'width': int(width / zoom), 'height': int(height / zoom),
                                                             'deviceScaleFactor': zoom, 'mobile': False}, session=session)
        devtools.call('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-color-scheme', 'value': scheme}]},
                      session=session)
        devtools.call('Page.addScriptToEvaluateOnNewDocument', {'source':
                      f'try {{ localStorage.setItem("corsu-language", "{language}"); }} catch (e) {{}}'}, session=session)
        if (ROOT / 'src' / 'appearance.py').exists():
            prepare_appearance(settings)
        devtools.call('Page.navigate', {'url': url() if callable(url) else url}, session=session)
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
        url = server.opening
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
