#!/usr/bin/env python3
"""Start a Chromium browser headless in a throwaway profile and read interface text it renders.

Usage: check_chromium.py BROWSER_EXECUTABLE
Reads the network error page and chrome://version through the DevTools protocol (standard library
WebSocket client) and fails when their labels are still French or English.
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


def page_text(devtools, url):
    target = devtools.call('Target.createTarget', {'url': 'about:blank'})['targetId']
    session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
    devtools.call('Page.enable', session=session)
    devtools.call('Page.navigate', {'url': url}, session=session)
    text = ''
    for _ in range(40):
        time.sleep(0.5)
        result = devtools.call('Runtime.evaluate', {'expression': 'document.body ? document.body.innerText : ""',
                                                    'returnByValue': True}, session=session)
        text = result['result'].get('value') or ''
        if len(text) > 40:
            break
    devtools.call('Target.closeTarget', {'targetId': target})
    return text


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
            failures = []
            for url, forbidden in UNTRANSLATED.items():
                text = page_text(devtools, url)
                first = ' | '.join(line for line in text.splitlines() if line.strip())[:160]
                leftover = [phrase for phrase in forbidden if phrase in text]
                status = 'FAIL' if leftover or len(text) < 20 else 'PASS'
                print(f'{status}: {url} → {first}')
                if status == 'FAIL':
                    failures.append(f'{url}: {leftover or "no text"}')
            if failures:
                raise SystemExit('Untranslated in the running browser: ' + '; '.join(failures))
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    main(sys.argv[1])
