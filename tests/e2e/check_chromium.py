#!/usr/bin/env python3
"""Start a Chromium browser headless in a throwaway profile and read interface text it renders.

Usage: check_chromium.py BROWSER_EXECUTABLE
Reads the network error page and chrome://version through the DevTools protocol (standard library
WebSocket client) and fails when their labels are still French or English.

A new tab first loads about:blank. On Windows, that load sometimes replaced the navigation sent right after
(Page.navigate: net::ERR_ABORTED, the tab stayed blank and the check read no text: 1 to 3 cold starts in 40 on
GitHub's runners; waiting for a replayed "load" event first made it worse, 9 in 60, because that event belongs to the
tab's initial empty document). The abort is reported by Chrome itself, so on exactly that result the check waits for
the replacing navigation's own event and navigates once more, saying so; anything else fails with what was seen.
On failure, a screenshot is saved in CORSU_E2E_ARTIFACTS (or the temporary folder).
"""
import base64
import json
import os
import re
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

# Interface text that must not appear once the French pack is translated.
UNTRANSLATED = {
    'http://127.0.0.1:9/': ['Ce site est inaccessible', "This site can’t be reached", 'Essayez de :', 'Recharger'],
    'chrome://version/': ['Ligne de commande', 'Command Line', 'Chemin d’accès au profil', 'Profile Path'],
}


class DevTools:
    def __init__(self, url):
        host, port, path = re.match(r'ws://([^:/]+):(\d+)(/.*)', url).groups()
        self.socket = socket.create_connection((host, int(port)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.socket.sendall((f'GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n'
                             f'Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        response = b''
        while b'\r\n\r\n' not in response:
            response += self.socket.recv(1)
        if b' 101 ' not in response.split(b'\r\n', 1)[0]:
            raise RuntimeError(response.decode(errors='replace'))
        self.counter = 0
        self.events = []

    def _receive_exact(self, count):
        data = b''
        while len(data) < count:
            chunk = self.socket.recv(count - len(data))
            if not chunk:
                raise EOFError('DevTools closed')
            data += chunk
        return data

    def _frame(self):
        message = b''
        while True:
            first, second = self._receive_exact(2)
            length = second & 0x7f
            if length == 126:
                length = struct.unpack('>H', self._receive_exact(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', self._receive_exact(8))[0]
            message += self._receive_exact(length)
            if first & 0x80:
                return message

    def call(self, method, params=None, session=None):
        self.counter += 1
        payload = {'id': self.counter, 'method': method, 'params': params or {}}
        if session:
            payload['sessionId'] = session
        data = json.dumps(payload).encode()
        mask = os.urandom(4)
        header = bytes([0x81])
        header += bytes([0x80 | len(data)]) if len(data) < 126 else bytes([0x80 | 126]) + struct.pack('>H', len(data))
        self.socket.sendall(header + mask + bytes(byte ^ mask[index % 4] for index, byte in enumerate(data)))
        while True:
            reply = json.loads(self._frame())
            if reply.get('id') == self.counter:
                if 'error' in reply:
                    raise RuntimeError(reply['error'])
                return reply['result']
            self.events.append(reply)

    def event(self, session, predicate, timeout):
        """The first event of this session matching predicate, kept or still to come; None after timeout."""
        deadline = time.monotonic() + timeout
        while True:
            for index, event in enumerate(self.events):
                if event.get('sessionId') == session and predicate(event):
                    return self.events.pop(index)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            self.socket.settimeout(remaining)
            try:
                self.events.append(json.loads(self._frame()))
            except socket.timeout:
                return None
            finally:
                self.socket.settimeout(30)


def page_state(devtools, session):
    """URL, readiness, text and HTML excerpt; empty while a navigation replaces the document under evaluation."""
    result = devtools.call('Runtime.evaluate', {'expression': STATE, 'returnByValue': True}, session=session)
    value = result['result'].get('value')
    return json.loads(value) if value else {'url': '', 'ready': 'replaced', 'text': '', 'html': ''}


STATE = 'JSON.stringify({url: location.href, ready: document.readyState, text: document.body ? document.body.innerText : "", html: document.documentElement.outerHTML.slice(0, 600)})'


def screenshot(devtools, session, name):
    folder = Path(os.environ.get('CORSU_E2E_ARTIFACTS') or tempfile.gettempdir())
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (re.sub(r'[^A-Za-z0-9]+', '-', name).strip('-') + '.png')
    try:
        path.write_bytes(base64.b64decode(devtools.call('Page.captureScreenshot', session=session)['data']))
        return path
    except (RuntimeError, OSError) as error:
        return f'no screenshot ({error})'


def open_page(devtools, url, timeout=30):
    """(page state, problem): the page's URL, readiness, text and HTML excerpt once it shows text; problem is None
    when it did, else what went wrong, with each navigation result and a screenshot."""
    target = devtools.call('Target.createTarget', {'url': 'about:blank'})['targetId']
    session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
    try:
        devtools.call('Page.enable', session=session)
        navigations = [devtools.call('Page.navigate', {'url': url}, session=session)]
        if navigations[0].get('errorText') == 'net::ERR_ABORTED':
            # Replaced by the tab's own about:blank load: its commit or end is reported after Page.enable.
            replaced = devtools.event(session, lambda event: event.get('method') in (
                'Page.frameNavigated', 'Page.frameStoppedLoading'), timeout)
            print(f'  {url}: first navigation replaced by the new tab\'s about:blank load '
                  f'({replaced and replaced["method"]}); navigating again')
            navigations.append(devtools.call('Page.navigate', {'url': url}, session=session))
        deadline = time.monotonic() + timeout
        while True:
            page = page_state(devtools, session)
            if page['url'] != 'about:blank' and page['ready'] == 'complete' and len(page['text'].strip()) >= 20:
                return page, None
            if time.monotonic() > deadline:
                problem = (f'no page text after {timeout} s; Page.navigate returned {navigations}; '
                           f'screenshot: {screenshot(devtools, session, url)}')
                return page, problem
            # Waiting for the page to render its text; the deadline above bounds it.
            devtools.event(session, lambda event: event.get('method') in ('Page.lifecycleEvent', 'Page.frameNavigated',
                                                                          'Page.loadEventFired'), 0.25)
    finally:
        devtools.call('Target.closeTarget', {'targetId': target})


def main(executable):
    with tempfile.TemporaryDirectory(prefix='corsu-chromium-', ignore_cleanup_errors=True) as profile:
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        environment = {**os.environ, 'LANGUAGE': 'co:fr'}
        command = [executable, '--headless=new', '--disable-gpu', f'--user-data-dir={profile}', '--lang=fr',
                   f'--remote-debugging-port={port}', '--no-first-run', '--no-default-browser-check', 'about:blank']
        if sys.platform.startswith('linux'):
            command.insert(1, '--no-sandbox')
        process = subprocess.Popen(command, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 60
            while True:
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=2) as response:
                        endpoint = json.load(response)['webSocketDebuggerUrl']
                    break
                except OSError:
                    if process.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError('The browser did not start')
                    time.sleep(0.5)
            devtools = DevTools(endpoint)
            version = devtools.call('Browser.getVersion')
            print(f'Browser: {version["product"]} ({version["userAgent"]})')
            failures = []
            for url, forbidden in UNTRANSLATED.items():
                page, problem = open_page(devtools, url)
                text = page['text']
                first = ' | '.join(line for line in text.splitlines() if line.strip())[:160]
                leftover = [phrase for phrase in forbidden if phrase in text]
                if problem or leftover:
                    print(f'FAIL: {url} → {first!r}')
                    print(f'  shown: {page["url"]} (document {page["ready"]})')
                    print(f'  expected: Corsican text, none of {forbidden}')
                    print(f'  untranslated found: {leftover}' if leftover else f'  problem: {problem}')
                    print(f'  HTML: {page["html"]!r}')
                    failures.append(f'{url}: {leftover or problem}')
                else:
                    print(f'PASS: {url} → {first}')
            if failures:
                raise SystemExit('Chromium check failed: ' + '; '.join(failures))
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        # UTF-8, so Windows logs show the page text instead of question marks.
        stream.reconfigure(encoding='utf-8', errors='replace')
    main(sys.argv[1])
