#!/usr/bin/env python3
"""The Appearance page in headless Chrome, against the window's own server (src/app.py) with a sample state.

Usage: check_appearance.py CHROME [OUTPUT_DIR]
Opens the page as Corsu does (a ticket after '#', exchanged for the window's key) and checks that a reload keeps the
key, that a page without it is told so, and that the state, settings and picture are refused without it. Changes
theme, palette, accent and density; imports synthetic pictures (drawn in the browser, saved to a temporary folder)
through the page's file input, animated GIF, PNG and WebP among them (kept as still pictures); frames one with the
keyboard, cancels, applies; checks that the periodic refresh leaves the focus and a slider alone and that reduced
motion turns transitions off; reloads and checks that the settings came back from the server; feeds an undecodable
file and a text file and checks the messages; resets and checks that only DATA/appearance changed. Screenshots go to
OUTPUT_DIR. HOME is a temporary folder: nothing of the person's own Corsu or files is read or written.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zlib

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


def serve():
    """The window's own server (src/app.py: the page, its files, the appearance routes, the Host/X-Corsu/Origin
    checks, the window's key and, on Linux, the owner check), answering /api/state with a complete sample state."""
    import app
    # A complete sample state (window_screens.py): with fields missing, the window's own render fails and the page
    # reads as closed, taking the Appearance section with it.
    app.snapshot = lambda job=None: dict(sample_state())
    job = app.Job()
    server = app.Server(('127.0.0.1', 0), app.make_handler(job, [0.0], 0))
    port = server.server_address[1]
    server.RequestHandlerClass = app.make_handler(job, [0.0], port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, app


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


def gif_animated(width=48, height=32):
    """A two-frame animated GIF (red, then blue), LZW-coded with a clear code every two pixels so the codes stay 3 bits."""
    def frame(index):
        codes, bits, count = [], 0, 0
        stream = [4]
        for pixel in range(width * height):
            stream.append(index)
            if pixel % 2:
                stream.append(4)
        stream.append(5)
        value = 0
        for code in stream:
            value |= code << bits
            bits += 3
        data = value.to_bytes((bits + 7) // 8, 'little')
        blocks = b''.join(bytes([len(data[i:i + 255])]) + data[i:i + 255] for i in range(0, len(data), 255))
        control = b'\x21\xf9\x04\x00\x0a\x00\x00\x00'  # 100 ms
        return control + b'\x2c' + struct.pack('<HHHHB', 0, 0, width, height, 0) + b'\x02' + blocks + b'\x00'
    palette = bytes([220, 40, 40, 40, 60, 220, 0, 0, 0, 255, 255, 255])
    loop = b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00'
    return (b'GIF89a' + struct.pack('<HHBBB', width, height, 0xf1, 0, 0) + palette + loop + frame(0) + frame(1) + b'\x3b')


def png_animated(width=48, height=32):
    """A two-frame animated PNG (APNG): green, then purple."""
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    def pixels(colour):
        return zlib.compress(b''.join(b'\0' + bytes(colour) * width for _ in range(height)))
    def control(sequence):
        return chunk(b'fcTL', struct.pack('>IIIIIHHBB', sequence, width, height, 0, 0, 1, 10, 0, 0))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'acTL', struct.pack('>II', 2, 0)) + control(0) + chunk(b'IDAT', pixels((40, 160, 60)))
            + control(1) + chunk(b'fdAT', struct.pack('>I', 2) + pixels((120, 40, 160))) + chunk(b'IEND', b''))


def webp_animated(frames, width, height):
    """An animated WebP made of still WebP frames (each a RIFF with a 'VP8 ' chunk, as the browser encodes them)."""
    def chunk(kind, body):
        return kind + struct.pack('<I', len(body)) + body + (b'\0' if len(body) % 2 else b'')
    def bitstream(data):
        position, found = 12, b''
        while position < len(data):
            kind, length = data[position:position + 4], struct.unpack('<I', data[position + 4:position + 8])[0]
            if kind in (b'VP8 ', b'VP8L', b'ALPH'):
                found += chunk(kind, data[position + 8:position + 8 + length])
            position += 8 + length + (length & 1)
        return found
    three = lambda value: value.to_bytes(3, 'little')
    body = b'WEBP' + chunk(b'VP8X', bytes([0x02, 0, 0, 0]) + three(width - 1) + three(height - 1))
    body += chunk(b'ANIM', bytes(4) + struct.pack('<H', 0))
    for frame in frames:
        body += chunk(b'ANMF', three(0) + three(0) + three(width - 1) + three(height - 1) + three(100) + b'\x00' + bitstream(frame))
    return b'RIFF' + struct.pack('<I', len(body)) + body


def still(data):
    """Whether the stored bytes are a still picture: a JPEG, a WebP without animation, a PNG without acTL."""
    if data.startswith(b'\xff\xd8'):
        return True
    if data.startswith(b'RIFF'):
        return b'ANIM' not in data and b'ANMF' not in data and not (data[12:16] == b'VP8X' and data[20] & 0x02)
    if data.startswith(b'\x89PNG'):
        return b'acTL' not in data
    return False


def raw(url, path, headers):
    """Status of a GET to the window as another program would send it (urllib adds the Host header)."""
    request = urllib.request.Request(url + path.lstrip('/'), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


class Page:
    """A tab of headless Chrome. `url` is a function giving the address to open each time: Corsu's address with a fresh
    ticket, as Corsu itself opens its window (a ticket works once)."""

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

    def scheme(self, value, motion=''):
        self.call('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-color-scheme', 'value': value},
                                                              {'name': 'prefers-reduced-motion', 'value': motion}]})

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
        self.call('Page.navigate', {'url': self.url()})
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
        server, app = serve()
        url = f'http://127.0.0.1:{server.server_address[1]}/'
        opening = lambda: url + '#t=' + app.ACCESS.ticket()
        pictures = temporary / 'pictures'
        pictures.mkdir()
        process, devtools = chrome(executable, temporary / 'profile')
        try:
            page = Page(devtools, opening, 'light')
            page.call('Page.navigate', {'url': 'about:blank'})
            time.sleep(0.3)
            for name, size in (('sky.png', (1800, 1100, 'sky')), ('busy.png', (3200, 2000, 'busy'))):
                (pictures / name).write_bytes(base64.b64decode(page.run(DRAW % json.dumps(list(size)))))
            (pictures / 'fake.png').write_bytes(b'<!doctype html><script>alert(1)</script>')
            (pictures / 'notes.txt').write_text('not a picture', encoding='utf-8')

            # Opened as Corsu opens it: the ticket is exchanged for the key and leaves the address.
            page.open()
            html = 'document.documentElement'
            check(page.run('corsuAccess.has()') and page.run('location.hash') == '' and
                  page.run('sessionStorage.getItem("corsu-key")') == app.ACCESS.key,
                  'the ticket gave the page its key, and is no longer in the address')
            # Another program on the computer (another account on Windows or macOS) sends every header but the key.
            for path in ('/api/state', '/appearance/settings', '/appearance/background'):
                for key in (None, 'wrong-' + 'x' * 40):
                    headers = {'X-Corsu': '1', 'Origin': url.rstrip('/'), **({'X-Corsu-Key': key} if key else {})}
                    status = raw(url, path, headers)
                    check(status == 403, f'{path} refused without the key ({"wrong key" if key else "no key"}): {status}')
            check(raw(url, '/appearance/settings', {'X-Corsu': '1', 'X-Corsu-Key': app.ACCESS.key}) == 200,
                  'and answered with it')

            # Defaults, then plain light and dark.
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

            # A real reload (as F5 or the restart after an update): the key stays, nothing needs a new ticket.
            page.run('location.reload()')
            page.wait('document.readyState === "complete" && window.corsuAppearance && !!document.getElementById("ap-theme-dark")')
            page.wait(f'{html}.style.getPropertyValue("--bg-image").startsWith(\'url("blob:\')')
            check(page.run('corsuAccess.has()') and not page.run('!!document.querySelector("main .closed")'),
                  'after location.reload(): the key is kept and the picture fetched with it')
            page.run('(document.querySelector(\'[data-page="appearance"]\') || { click() {} }).click()')

            # A page without key (an old tab, a bookmark): told to reopen Corsu, nothing personal shown.
            stranger = Page(devtools, lambda: url, 'light')
            stranger.call('Page.navigate', {'url': url})
            stranger.wait('!!document.querySelector("main .closed")')
            check(stranger.run('document.querySelector("main .closed").textContent').startswith('Cette page n\'a pas la clé de Corsu')
                  and stranger.run(f'{html}.dataset.background') == 'none',
                  'a page without key says so and shows no picture: '
                  + repr(stranger.run('document.querySelector("main .closed").textContent')))
            stranger.close()

            # Reopened: everything comes back from the server (the local cache is cleared to prove it).
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

            # The window redraws every 1.5 s: a focused slider being moved keeps its focus, its node and its value.
            page.run('(() => { const dim = document.getElementById("ap-dim"); dim.focus(); dim.dataset.probe = "kept";'
                     ' dim.value = 40; dim.dispatchEvent(new Event("input", {bubbles: true})); })()')
            time.sleep(3.5)
            check(page.run('document.activeElement && document.activeElement.id') == 'ap-dim'
                  and page.run('document.getElementById("ap-dim").dataset.probe') == 'kept'
                  and page.run('document.getElementById("ap-dim").value') == '40',
                  'two refreshes later: focus, slider node and its value unchanged')
            check(page.run('!document.getElementById("appearance").hidden && document.getElementById("programs").hidden'
                           ' && document.querySelector(\'[data-page="appearance"]\').getAttribute("aria-current") === "page"'),
                  'two refreshes later: still on Appearance, not sent back to Home')
            page.run('document.getElementById("ap-dim").blur()')

            # Reduced motion: no transition or animation anywhere, the framing marker included.
            page.scheme('light', 'reduce')
            durations = page.run('(() => { const probe = document.createElement("span"); probe.className = "busy";'
                                 ' document.body.append(probe); const all = [...document.querySelectorAll("body *")];'
                                 ' const moving = all.filter(node => { const s = getComputedStyle(node);'
                                 ' return s.transitionDuration.split(",").some(d => parseFloat(d) > 0)'
                                 ' || (s.animationName !== "none" && parseFloat(s.animationDuration) > 0); })'
                                 '.map(node => node.className || node.tagName); probe.remove(); return moving; })()')
            check(durations == [], f'prefers-reduced-motion: nothing moves ({durations[:5]})')
            page.scheme('light')

            # Animated pictures (GIF, PNG, WebP) are kept as one still frame, re-encoded by the page.
            frames = [base64.b64decode(page.run('(() => { const c = document.createElement("canvas"); c.width = 48; c.height = 32;'
                                                f' const x = c.getContext("2d"); x.fillStyle = "{colour}"; x.fillRect(0, 0, 48, 32);'
                                                ' return c.toDataURL("image/webp", 0.9).split(",")[1]; })()'))
                      for colour in ('#c03030', '#3040c0')]
            for name, data in (('animated.gif', gif_animated()), ('animated.png', png_animated()),
                               ('animated.webp', webp_animated(frames, 48, 32))):
                (pictures / name).write_bytes(data)
                kept = sorted(path.name for path in (corsu.DATA / 'appearance').glob('background-*'))
                page.run('document.getElementById("ap-status").textContent = ""')
                page.files('#ap-file', [pictures / name])
                page.wait('!document.getElementById("ap-framing").hidden || document.getElementById("ap-alert").textContent.length > 0', 30)
                if not page.run('document.getElementById("ap-framing").hidden'):
                    page.run('document.getElementById("ap-apply").click()')
                    page.wait('document.getElementById("ap-framing").hidden && document.getElementById("ap-status").textContent.length > 0', 30)
                    stored = list((corsu.DATA / 'appearance').glob('background-*'))
                    data = stored[0].read_bytes() if len(stored) == 1 else b''
                    check(len(stored) == 1 and still(data) and appearance.inspect(data),
                          f'{name}: stored as one still picture ({stored[0].name if stored else None})')
                else:
                    message = page.run('document.getElementById("ap-alert").textContent')
                    check(sorted(path.name for path in (corsu.DATA / 'appearance').glob('background-*')) == kept,
                          f'{name}: refused by this browser, the stored picture unchanged ({message!r})')
            check(page.run('getComputedStyle(document.body, "::before").animationName') in ('none', ''),
                  'the background layer has no animation')

            # Reset: back to defaults, only DATA/appearance changed.
            page.run('document.getElementById("ap-reset").click()')
            page.wait('!document.getElementById("ap-reset-confirm").hidden')
            page.run('document.getElementById("ap-reset-yes").click()')
            page.wait(f'{html}.dataset.palette === "maquis" && {html}.dataset.background === "none"')
            check(page.run(f'{html}.dataset.theme') == 'light' and page.run(f'{html}.dataset.density') == 'comfortable'
                  and not page.run(f'{html}.style.getPropertyValue("--accent-user")'), 'reset: defaults in the page')
            check(list((corsu.DATA / 'appearance').iterdir()) == [], 'reset: appearance files removed')
            check(hashlib.sha256(record.read_bytes()).hexdigest() == record_hash, 'reset: installation.json identical')

            # A ticket read by someone else and used again: the key is replaced, so both pages are shut out.
            ticket = app.ACCESS.ticket()
            first = Page(devtools, lambda: url + '#t=' + ticket, 'light')
            first.open()
            before = app.ACCESS.key
            second = Page(devtools, lambda: url + '#t=' + ticket, 'light')
            second.call('Page.navigate', {'url': url + '#t=' + ticket})
            second.wait('!!document.querySelector("main .closed")')
            first.wait('!!document.querySelector("main .closed")')
            check(app.ACCESS.key != before and raw(url, '/api/state', {'X-Corsu': '1', 'X-Corsu-Key': before}) == 403,
                  'a ticket used twice replaces the key; both pages say to reopen Corsu')
            first.close()
            second.close()
            page.close()
        finally:
            process.terminate()
            process.wait(timeout=20)
            server.shutdown()
    print(f'{len(failures)} failure(s)' if failures else 'all checks passed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
