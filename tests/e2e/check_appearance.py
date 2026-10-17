#!/usr/bin/env python3
"""The Appearance page in headless Chrome, against a local server using src/appearance.py's handle().

Usage: check_appearance.py CHROME [OUTPUT_DIR]
Changes theme, palette, accent and density; imports synthetic pictures (drawn in the browser, saved to a temporary
folder) through the page's file input; frames one with the keyboard, cancels, applies; reloads and checks that the
settings came back from the server; feeds an undecodable file and a text file and checks the messages; resets and
checks that only DATA/appearance changed. Screenshots go to OUTPUT_DIR. HOME is a temporary folder: nothing of the
person's own Corsu or files is read or written.

When src/app/index.html does not have the Appearance section yet, a small stand-in page is served instead: the
contract's tokens and background layers (docs/window-design.md), the shared classes, window.corsu and the events.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
APP = ROOT / 'src' / 'app'
sys.path.insert(0, str(HERE))
from check_chromium import DevTools  # noqa: E402


def sample_state():
    """The window's state with nothing installed, as window_screens.py builds it (every field the page reads)."""
    from window_screens import states
    if not hasattr(sample_state, 'value'):
        sample_state.value = states()['empty']
    return sample_state.value

# The window's own policy (src/app.py, send()), with the img-src the wiring adds.
CSP = ("default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
       "img-src 'self' blob: data:; frame-ancestors 'none'")

STAND_IN = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corsu</title>
<link rel="stylesheet" href="stand-in.css"><link rel="stylesheet" href="appearance.css">
<script src="texts-appearance.js"></script><script src="stand-in.js"></script><script src="appearance.js"></script>
</head><body><div class="app"><aside><div class="brand"><b>Corsu</b></div>
<nav><button type="button">Logiciels</button><button type="button">Ajouter</button>
<button type="button" aria-current="page">Apparence</button><button type="button">Aide</button></nav></aside>
<main><section id="appearance" data-page-panel></section></main></div></body></html>"""

STAND_IN_JS = """"use strict";
window.corsu = { language: "fr", t: (name, values = {}) => (textsAppearance.fr[name] ?? name) };
document.addEventListener("DOMContentLoaded", () => document.dispatchEvent(new CustomEvent("corsu:page", { detail: "appearance" })));
"""

# Only what the contract says style.css provides, kept small: tokens per palette and theme, background layers.
STAND_IN_CSS = """
:root { --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-6: 24px;
  --bg: #f6f3ec; --surface: #fffdf8; --surface-2: #efebe2; --line: #ddd6c8; --text: #1e2421; --muted: #5d6662;
  --accent: #1f6b5c; --on-accent: #ffffff; --focus: #1f6b5c; --danger: #a1302b; }
[data-palette=mare] { --bg: #f2f5f8; --surface: #ffffff; --surface-2: #e8eef4; --accent: #22609a; --focus: #22609a; }
[data-palette=granitu] { --bg: #efedea; --surface: #fbfaf8; --surface-2: #e5e2dd; --accent: #8a5a14; --focus: #8a5a14; }
[data-palette=tramontu] { --bg: #f7efe9; --surface: #fffaf6; --surface-2: #f0e3da; --accent: #a64b2f; --focus: #a64b2f; }
[data-palette=notte] { --bg: #eef1f7; --surface: #ffffff; --surface-2: #e3e8f2; --accent: #2b4a8c; --focus: #2b4a8c; }
[data-theme=dark] { --bg: #151a18; --surface: #1d2321; --surface-2: #181d1b; --line: #323b38; --text: #e6ebe8;
  --muted: #9ba7a2; --accent: #6cc3ad; --on-accent: #0d1a16; --focus: #6cc3ad; --danger: #f08a80; }
[data-theme=dark][data-palette=mare] { --accent: #7fb6ea; --focus: #7fb6ea; --bg: #12171d; --surface: #1a2129; }
[data-theme=dark][data-palette=granitu] { --accent: #e0b062; --focus: #e0b062; --bg: #191817; --surface: #22201e; }
[data-theme=dark][data-palette=tramontu] { --accent: #f0a080; --focus: #f0a080; --bg: #1c1513; --surface: #261d1a; }
[data-theme=dark][data-palette=notte] { --accent: #9bb8ff; --focus: #9bb8ff; --bg: #0f1422; --surface: #172036; --surface-2: #121a2c; }
:root { color-scheme: light; } [data-theme=dark] { color-scheme: dark; }
:root[style*="--accent-user"] { --accent: var(--accent-user); --focus: var(--accent-user); }
* { box-sizing: border-box; } html, body { margin: 0; min-height: 100%; }
body { background: var(--bg); color: var(--text); font: 1rem/1.45 system-ui, sans-serif; }
[data-background=image] body::before { content: ""; position: fixed; inset: 0; z-index: -2; background: var(--bg-image) var(--bg-position, 50% 50%) / cover no-repeat; }
[data-background=image] body::after { content: ""; position: fixed; inset: 0; z-index: -1; background: var(--bg); opacity: var(--bg-dim, 0.35); }
[data-background=image] body { background: transparent; }
.app { display: grid; grid-template-columns: 200px minmax(0, 1fr); min-height: 100vh; }
aside { background: color-mix(in srgb, var(--surface-2) 88%, transparent); border-right: 1px solid var(--line); padding: 16px 10px; }
.brand { padding: 4px 10px 14px; font-size: 1.05rem; }
nav { display: flex; flex-direction: column; gap: 2px; }
nav button { text-align: left; border: 0; background: none; color: inherit; font: inherit; padding: 7px 10px; border-radius: 6px; }
nav button[aria-current=page] { background: var(--surface); font-weight: 600; box-shadow: inset 3px 0 var(--accent); }
main { padding: 28px 36px 80px; max-width: 820px; }
h1 { font-size: 1.5rem; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 0.8125rem; font-weight: 600; color: var(--muted); margin: 24px 0 8px 2px; }
.lead { color: var(--muted); margin: 0 0 18px; }
.detail, .muted { color: var(--muted); font-size: 0.875rem; }
.group { list-style: none; margin: 0; padding: 0; border: 1px solid var(--line); border-radius: 10px; background: color-mix(in srgb, var(--surface) 92%, transparent); }
[data-background=image]:not([data-reduced-transparency]) .group, [data-background=image]:not([data-reduced-transparency]) aside { backdrop-filter: blur(var(--bg-blur)); }
.group > li { display: flex; align-items: center; gap: 14px; padding: 10px 16px; min-height: 52px; }
.group > li[hidden] { display: none; }
.group > li + li { border-top: 1px solid var(--line); }
.group .label { flex: 1; min-width: 0; } .group .label > :first-child { display: block; font-weight: 550; }
.group .detail { display: block; }
.buttons { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.button { font: inherit; font-size: 0.875rem; color: var(--text); background: var(--surface); border: 1px solid var(--line); border-radius: 7px; padding: 6px 12px; cursor: pointer; }
.button.default { background: var(--accent); color: var(--on-accent); border-color: transparent; }
.button.danger { color: var(--danger); border-color: currentColor; }
.button[hidden] { display: none; }
.switch { position: relative; display: inline-block; width: 40px; height: 22px; flex: none; }
.switch input { position: absolute; inset: 0; opacity: 0; margin: 0; cursor: pointer; }
.switch i { position: absolute; inset: 0; border-radius: 11px; background: var(--line); pointer-events: none; }
.switch i::after { content: ""; position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; border-radius: 50%; background: #fff; transition: left .15s; }
.switch input:checked + i { background: var(--accent); } .switch input:checked + i::after { left: 21px; }
.switch input:focus-visible + i { outline: 2px solid var(--focus); outline-offset: 2px; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
a { color: var(--accent); }
"""


def chrome(executable, profile):
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
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


def serve(appearance, port_holder):
    """The page (or the stand-in), its files, and appearance.handle() behind a Host/X-Corsu/Origin check."""
    real = 'id="appearance"' in (APP / 'index.html').read_text(encoding='utf-8')
    extra = {} if real else {'/': (STAND_IN.encode(), 'text/html; charset=utf-8'),
                             '/stand-in.css': (STAND_IN_CSS.encode(), 'text/css; charset=utf-8'),
                             '/stand-in.js': (STAND_IN_JS.encode(), 'text/javascript; charset=utf-8')}
    kinds = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
             '.js': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml'}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *arguments):
            pass

        def reply(self, status, body, kind='application/json; charset=utf-8'):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', CSP)
            self.end_headers()
            self.wfile.write(data)

        def allowed(self):
            host = f'127.0.0.1:{port_holder[0]}'
            return (self.headers.get('Host') == host and self.headers.get('X-Corsu') == '1'
                    and self.headers.get('Origin') in (None, f'http://{host}'))

        def answer(self, method):
            path = self.path.split('?')[0]
            body = b''
            if method == 'POST':
                length = int(self.headers.get('Content-Length') or 0)
                if length > appearance.body_limit(self.path):
                    self.close_connection = True
                    return self.reply(413, {'error': 'too_large'})
                body = self.rfile.read(length)
            found = appearance.handle(method, self.path, body, self.headers, self.allowed)
            if found is not None:
                return self.reply(*found)
            if method == 'GET' and path in extra:
                return self.reply(200, *extra[path])
            if method == 'GET' and path == '/api/state':
                # A complete sample state (window_screens.py): with fields missing, the window's own render fails and
                # the page reads as closed, taking the Appearance section with it.
                return self.reply(200, sample_state())
            name = 'index.html' if path == '/' else path.lstrip('/')
            file = (APP / name).resolve()
            if method == 'GET' and file.is_file() and APP in file.parents:
                return self.reply(200, file.read_bytes(), kinds.get(file.suffix, 'application/octet-stream'))
            if method == 'POST':
                return self.reply(200, {'started': False})
            self.reply(404, {'error': 'not found'})

        def do_GET(self):
            self.answer('GET')

        def do_POST(self):
            self.answer('POST')

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    port_holder[0] = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, real


# Synthetic pictures, drawn by the browser itself.
DRAW = """(() => {
  const [width, height, kind] = %s;
  const canvas = document.createElement("canvas"); canvas.width = width; canvas.height = height;
  const c = canvas.getContext("2d");
  if (kind === "sky") {
    const g = c.createLinearGradient(0, 0, 0, height); g.addColorStop(0, "#8fc1e3"); g.addColorStop(0.62, "#f3d9b1"); g.addColorStop(1, "#5f7f5a");
    c.fillStyle = g; c.fillRect(0, 0, width, height);
    c.fillStyle = "#3d5a3f"; c.beginPath(); c.moveTo(0, height * 0.75);
    for (let x = 0; x <= width; x += width / 12) c.lineTo(x, height * (0.62 + 0.08 * Math.sin(x / width * 9)));
    c.lineTo(width, height); c.lineTo(0, height); c.fill();
    c.fillStyle = "#fff6d8"; c.beginPath(); c.arc(width * 0.72, height * 0.3, height * 0.08, 0, 7); c.fill();
  } else {
    let seed = 7; const random = () => (seed = (seed * 16807) %% 2147483647) / 2147483647;
    for (let y = 0; y < height; y += 40) for (let x = 0; x < width; x += 40) {
      c.fillStyle = `hsl(${Math.floor(random() * 360)} 80%% ${30 + random() * 50}%%)`; c.fillRect(x, y, 40, 40);
    }
    for (let i = 0; i < 400; i++) { c.strokeStyle = `hsl(${Math.floor(random() * 360)} 90%% 50%%)`; c.lineWidth = 2 + random() * 10;
      c.beginPath(); c.arc(random() * width, random() * height, 10 + random() * 200, 0, 7); c.stroke(); }
    c.font = "bold 120px sans-serif"; c.fillStyle = "#000"; c.fillText("Lorem ipsum CORSU 123", 60, height / 2);
  }
  return canvas.toDataURL("image/png").split(",")[1];
})()"""


class Page:
    def __init__(self, devtools, url, scheme):
        self.devtools = devtools
        self.target = devtools.call('Target.createTarget', {'url': 'about:blank'})['targetId']
        self.session = devtools.call('Target.attachToTarget', {'targetId': self.target, 'flatten': True})['sessionId']
        self.call('Page.enable')
        self.call('Runtime.enable')
        self.call('Emulation.setDeviceMetricsOverride', {'width': 1100, 'height': 1250, 'deviceScaleFactor': 1, 'mobile': False})
        self.scheme(scheme)
        # The messages checked below are the French ones; the window itself starts in Corsican.
        self.call('Page.addScriptToEvaluateOnNewDocument', {'source': 'try { localStorage.setItem("corsu-language", "fr"); } catch (e) {}'})
        self.url = url

    def call(self, method, params=None):
        return self.devtools.call(method, params, session=self.session)

    def scheme(self, value):
        self.call('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-color-scheme', 'value': value}]})

    def run(self, expression):
        result = self.call('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
        if 'exceptionDetails' in result:
            raise RuntimeError(f'{expression[:80]}: {result["exceptionDetails"]}')
        return result['result'].get('value')

    def wait(self, expression, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if self.run(expression):
                    return True
            except RuntimeError:
                pass
            time.sleep(0.1)
        raise AssertionError(f'timed out waiting for {expression}')

    def open(self):
        self.call('Page.navigate', {'url': self.url})
        self.wait('document.readyState === "complete" && !!document.getElementById("ap-theme-dark")')
        self.wait('window.corsuAppearance && document.documentElement.dataset.palette')
        # The Appearance page shown, as a person opening it (a hidden page cannot take the focus).
        self.run('(document.querySelector(\'[data-page="appearance"]\') || { click() {} }).click()')
        time.sleep(0.4)

    def files(self, selector, paths):
        document = self.call('DOM.getDocument', {'depth': -1})
        node = self.call('DOM.querySelector', {'nodeId': document['root']['nodeId'], 'selector': selector})['nodeId']
        self.call('DOM.setFileInputFiles', {'nodeId': node, 'files': [str(path) for path in paths]})

    def key(self, key, code=None, count=1, shift=False):
        codes = {'ArrowRight': 39, 'ArrowLeft': 37, 'ArrowUp': 38, 'ArrowDown': 40, 'Escape': 27, 'Enter': 13}
        for _ in range(count):
            for kind in ('keyDown', 'keyUp'):
                self.call('Input.dispatchKeyEvent', {'type': kind, 'key': key, 'code': code or key,
                                                     'windowsVirtualKeyCode': codes.get(key, 0), 'modifiers': 8 if shift else 0})

    def shot(self, path):
        self.run('document.activeElement && document.activeElement.blur && document.activeElement.blur()')
        time.sleep(0.4)
        path.write_bytes(base64.b64decode(self.call('Page.captureScreenshot', {'format': 'png'})['data']))
        print('  screenshot', path)

    def close(self):
        self.devtools.call('Target.closeTarget', {'targetId': self.target})


def main(arguments):
    executable = arguments[0]
    output = Path(arguments[1]) if len(arguments) > 1 else Path(tempfile.gettempdir()) / 'corsu-appearance'
    output.mkdir(parents=True, exist_ok=True)
    failures = []

    def check(condition, what):
        print(('PASS ' if condition else 'FAIL ') + what)
        if not condition:
            failures.append(what)

    with tempfile.TemporaryDirectory(prefix='corsu-appearance-') as temporary:
        temporary = Path(temporary)
        os.environ['HOME'] = str(temporary)
        sys.path.insert(0, str(ROOT / 'src'))
        import corsu
        import appearance
        corsu.DATA = temporary / 'data'
        corsu.DATA.mkdir()
        record = corsu.DATA / 'installation.json'
        record.write_text('{"files": {}, "components": ["vlc"]}', encoding='utf-8')
        record_hash = hashlib.sha256(record.read_bytes()).hexdigest()
        port = [0]
        server, real = serve(appearance, port)
        url = f'http://127.0.0.1:{port[0]}/'
        print('page:', 'src/app/index.html' if real else 'stand-in page (index.html has no Appearance section yet)')
        pictures = temporary / 'pictures'
        pictures.mkdir()
        process, devtools = chrome(executable, temporary / 'profile')
        try:
            page = Page(devtools, url, 'light')
            page.call('Page.navigate', {'url': 'about:blank'})
            time.sleep(0.3)
            for name, size in (('sky.png', (1800, 1100, 'sky')), ('busy.png', (3200, 2000, 'busy'))):
                (pictures / name).write_bytes(base64.b64decode(page.run(DRAW % json.dumps(list(size)))))
            (pictures / 'fake.png').write_bytes(b'<!doctype html><script>alert(1)</script>')
            (pictures / 'notes.txt').write_text('not a picture', encoding='utf-8')

            # Defaults, then plain light and dark.
            page.open()
            html = 'document.documentElement'
            check(page.run(f'{html}.dataset.theme') == 'light' and page.run(f'{html}.dataset.palette') == 'maquis'
                  and page.run(f'{html}.dataset.density') == 'comfortable' and page.run(f'{html}.dataset.background') == 'none',
                  'defaults: system theme (light here), maquis, comfortable, plain background')
            page.shot(output / 'light.png')
            page.run('document.getElementById("ap-theme-dark").click()')
            page.run('document.getElementById("ap-palette-notte").click()')
            page.run('document.getElementById("ap-density-compact").click()')
            check(page.run(f'{html}.dataset.theme') == 'dark' and page.run(f'{html}.dataset.palette') == 'notte'
                  and page.run(f'{html}.dataset.density') == 'compact', 'theme, palette and density preview at once')
            page.shot(output / 'dark.png')
            time.sleep(0.8)
            saved = appearance.load()
            check((saved['theme'], saved['palette'], saved['density']) == ('dark', 'notte', 'compact'),
                  'changes saved to the server (debounced)')

            # Accent: a preset, then a custom colour that needs adjusting (yellow on dark text, on light panels).
            page.run('document.getElementById("ap-accent-terracotta").click()')
            check(bool(page.run(f'{html}.style.getPropertyValue("--accent-user")')), 'preset accent applied')
            page.run('document.getElementById("ap-theme-light").click()')
            page.run('(() => { const input = document.getElementById("ap-accent-custom"); input.value = "#ffe600";'
                     ' input.dispatchEvent(new Event("input", {bubbles: true})); })()')
            used = page.run(f'{html}.style.getPropertyValue("--accent-user").trim()')
            ratios = page.run('(() => { const a = corsuAppearance, s = getComputedStyle(document.documentElement);'
                              ' const accent = a.rgb(s.getPropertyValue("--accent-user"));'
                              ' return [a.contrast(accent, a.rgb(s.getPropertyValue("--surface"))),'
                              ' a.contrast(accent, a.rgb(s.getPropertyValue("--on-accent")))]; })()')
            note = page.run('document.getElementById("ap-accent-note").textContent')
            check(used and used != '#ffe600' and min(ratios) >= 4.5,
                  f'custom yellow adjusted to {used}, contrast surface/on-accent {ratios[0]:.2f}/{ratios[1]:.2f} ≥ 4.5')
            check('#ffe600' in note and used in note, f'adjustment said in words: {note!r}')
            time.sleep(0.8)
            check(appearance.load()['accent'] == '#ffe600', 'the chosen colour is saved; the adjustment is recomputed per theme')

            # Picture: refused files first.
            page.files('#ap-file', [pictures / 'fake.png'])
            page.wait('document.getElementById("ap-alert").textContent.length > 0')
            message = page.run('document.getElementById("ap-alert").textContent')
            check(message == "Cette image ne peut pas être lue : elle est peut-être abîmée, ou dans un format que ce navigateur ne connaît pas.",
                  f'undecodable file refused with a message: {message!r}')
            page.files('#ap-file', [pictures / 'notes.txt'])
            page.wait('document.getElementById("ap-alert").textContent.startsWith("Ce fichier")')
            check(True, 'text file refused: ' + page.run('document.getElementById("ap-alert").textContent'))
            check(not list((corsu.DATA / 'appearance').glob('background-*')), 'nothing stored for refused files')

            # Import, frame with the keyboard, cancel.
            page.files('#ap-file', [pictures / 'busy.png'])
            page.wait('!document.getElementById("ap-framing").hidden', 30)
            check(page.run(f'{html}.dataset.background') == 'image'
                  and page.run(f'{html}.style.getPropertyValue("--bg-image")').startswith('url("blob:'),
                  'preview shows the picture before it is applied')
            check(page.run('document.activeElement && document.activeElement.id') == 'ap-frame', 'focus moves to the framing area')
            page.key('ArrowRight', count=3, shift=True)
            page.key('ArrowUp', count=5)
            check(page.run('document.getElementById("ap-frame-x").value + "," + document.getElementById("ap-frame-y").value') == '80,45'
                  and page.run(f'{html}.style.getPropertyValue("--bg-position")') == '80% 45%',
                  'arrow keys move the focal point (80 %, 45 %)')
            page.run('document.getElementById("ap-framing").scrollIntoView({block: "center"})')
            page.shot(output / 'framing.png')
            page.run('window.scrollTo(0, 0)')
            page.run('document.getElementById("ap-cancel").click()')
            check(page.run('document.getElementById("ap-framing").hidden') and page.run(f'{html}.dataset.background') == 'none'
                  and not list((corsu.DATA / 'appearance').glob('background-*')), 'cancel: back to plain, nothing stored')

            # Import again and apply.
            page.files('#ap-file', [pictures / 'busy.png'])
            page.wait('!document.getElementById("ap-framing").hidden', 30)
            page.run('(() => { const x = document.getElementById("ap-frame-x"); x.value = 30;'
                     ' x.dispatchEvent(new Event("input", {bubbles: true})); })()')
            page.run('document.getElementById("ap-apply").click()')
            page.wait('document.getElementById("ap-framing").hidden && document.getElementById("ap-status").textContent.length > 0', 30)
            saved = appearance.load()
            stored = list((corsu.DATA / 'appearance').glob('background-*'))
            check(saved['background'] == 'image' and saved['image'] and (saved['image']['width'], saved['image']['height']) == (2560, 1600)
                  and (saved['image']['x'], saved['image']['y']) == (30, 50) and len(stored) == 1,
                  f'applied: stored {stored[0].name if stored else None}, {saved["image"]}')
            check(saved['image']['type'] in ('image/webp', 'image/jpeg'), 'stored re-encoded (WebP or JPEG), never the original')
            check((pictures / 'busy.png').stat().st_size != stored[0].stat().st_size, 'original file untouched and not copied as is')
            page.shot(output / 'light-busy-image.png')

            # Replace with the calmer picture; the earlier one is removed.
            page.files('#ap-file', [pictures / 'sky.png'])
            page.wait('!document.getElementById("ap-framing").hidden', 30)
            page.run('document.getElementById("ap-apply").click()')
            page.wait('document.getElementById("ap-framing").hidden && document.getElementById("ap-status").textContent.length > 0', 30)
            stored = list((corsu.DATA / 'appearance').glob('background-*'))
            check(len(stored) == 1 and appearance.load()['image']['width'] == 1800, 'replaced: only the new picture is kept, not upscaled')
            page.shot(output / 'light-image.png')

            # Reload: everything comes back from the server (the local cache is cleared to prove it).
            page.run('localStorage.clear()')
            page.open()
            page.wait(f'{html}.style.getPropertyValue("--bg-image").startsWith(\'url("blob:\')')
            check(page.run(f'{html}.dataset.theme') == 'light' and page.run(f'{html}.dataset.palette') == 'notte'
                  and page.run(f'{html}.dataset.background') == 'image' and page.run(f'{html}.dataset.density') == 'compact',
                  'after reload: settings and picture come back from the server')
            check(page.run('document.getElementById("ap-accent-custom").value') == '#ffe600', 'custom accent kept')

            page.run('document.getElementById("ap-theme-dark").click()')
            page.run('document.getElementById("ap-blur").click()')
            page.shot(output / 'dark-image.png')
            check(page.run(f'{html}.style.getPropertyValue("--bg-blur")') in ('12px', '0px'), 'blur switch sets --bg-blur')

            page.call('Emulation.setDeviceMetricsOverride', {'width': 420, 'height': 1400, 'deviceScaleFactor': 1, 'mobile': False})
            page.shot(output / 'narrow-dark-image.png')
            page.call('Emulation.setDeviceMetricsOverride', {'width': 1100, 'height': 1250, 'deviceScaleFactor': 1, 'mobile': False})

            # The picture needs the X-Corsu header like every other route.
            try:
                urllib.request.urlopen(url + 'appearance/background', timeout=5)
                check(False, 'picture refused without X-Corsu')
            except urllib.error.HTTPError as error:
                check(error.code == 403, f'picture refused without X-Corsu ({error.code})')

            # Reset: back to defaults, only DATA/appearance changed.
            page.run('document.getElementById("ap-reset").click()')
            page.wait('!document.getElementById("ap-reset-confirm").hidden')
            page.run('document.getElementById("ap-reset-yes").click()')
            page.wait(f'{html}.dataset.palette === "maquis" && {html}.dataset.background === "none"')
            check(page.run(f'{html}.dataset.theme') == 'light' and page.run(f'{html}.dataset.density') == 'comfortable'
                  and not page.run(f'{html}.style.getPropertyValue("--accent-user")'), 'reset: defaults in the page')
            check(list((corsu.DATA / 'appearance').iterdir()) == [], 'reset: appearance files removed')
            check(hashlib.sha256(record.read_bytes()).hexdigest() == record_hash, 'reset: installation.json identical')
            page.close()
        finally:
            process.terminate()
            process.wait(timeout=20)
            server.shutdown()
    print(f'{len(failures)} failure(s)' if failures else 'all checks passed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
