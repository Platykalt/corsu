#!/usr/bin/env python3
"""Start Firefox Corsu through its launcher and ask Firefox itself about the default browser (Linux).

Usage: check_firefox_default.py LAUNCHER
Uses the HOME, XDG_DATA_HOME and XDG_CONFIG_HOME of the environment, which must be a throwaway one.
Firefox compares the default browser's command with its own. Before Corsu told it the launcher's path, the copy never
saw itself as the default, and "Make default" wrote an icon-less userapp-Firefox-*.desktop for its versioned folder:
the taskbar's browser button then showed a blank page. Firefox is driven through Marionette (standard library only).
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time


class Marionette:
    def __init__(self, port, process):
        deadline = time.monotonic() + 90
        while True:
            try:
                self.socket = socket.create_connection(('127.0.0.1', port), timeout=30)
                break
            except OSError:
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('Firefox did not start Marionette')
                time.sleep(0.5)
        self.stream = self.socket.makefile('rb')
        self.counter = 0
        self._read()

    def _read(self):
        size = b''
        while not size.endswith(b':'):
            byte = self.stream.read(1)
            if not byte:
                raise EOFError('Marionette closed')
            size += byte
        return json.loads(self.stream.read(int(size[:-1])))

    def call(self, name, parameters=None):
        self.counter += 1
        body = json.dumps([0, self.counter, name, parameters or {}]).encode()
        self.socket.sendall(str(len(body)).encode() + b':' + body)
        _, _, error, result = self._read()
        if error:
            raise RuntimeError(f'{name}: {error}')
        return result

    def script(self, source):
        return self.call('WebDriver:ExecuteScript', {'script': source, 'args': []})['value']


SHELL = "Cc['@mozilla.org/browser/shell-service;1'].getService(Ci.nsIShellService)"


def main(launcher):
    applications = Path(os.environ['XDG_DATA_HOME']) / 'applications'
    entry = applications / 'firefox.desktop'
    if not entry.exists():
        # Runners have no system menu entry to adapt; write the one Corsu writes over it.
        applications.mkdir(parents=True, exist_ok=True)
        entry.write_text(f'[Desktop Entry]\nType=Application\nName=Firefox Corsu\nExec={launcher} %u\nIcon=firefox\n'
                         'MimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;\n', encoding='utf-8')
    mimeapps = Path(os.environ['XDG_CONFIG_HOME']) / 'mimeapps.list'
    mimeapps.parent.mkdir(parents=True, exist_ok=True)
    mimeapps.write_text('[Default Applications]\nx-scheme-handler/http=firefox.desktop\n'
                        'x-scheme-handler/https=firefox.desktop\ntext/html=firefox.desktop\n', encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='corsu-default-', ignore_cleanup_errors=True) as profile:
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        Path(profile, 'user.js').write_text(f'user_pref("marionette.port", {port});\n'
                                            'user_pref("browser.shell.checkDefaultBrowser", false);\n', encoding='utf-8')
        environment = {name: value for name, value in os.environ.items() if not name.startswith('MOZ_')}
        environment['XDG_CURRENT_DESKTOP'] = 'GNOME'
        environment['MOZ_REMOTE_ALLOW_SYSTEM_ACCESS'] = '1'  # Firefox 159 needs it for the chrome context
        process = subprocess.Popen([launcher, '--headless', '--marionette', '--remote-allow-system-access',
                                    '--profile', profile], env=environment,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            marionette = Marionette(port, process)
            marionette.call('WebDriver:NewSession')
            marionette.call('Marionette:SetContext', {'value': 'chrome'})
            launcher_seen = marionette.script("return Services.env.get('MOZ_APP_LAUNCHER')")
            before = marionette.script(f'return {SHELL}.isDefaultBrowser(false, false)')
            marionette.script(f'{SHELL}.setDefaultBrowser(false); return true')
            after = marionette.script(f'return {SHELL}.isDefaultBrowser(false, false)')
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
    written = sorted(path.name for path in applications.glob('userapp-*.desktop'))
    defaults = mimeapps.read_text(encoding='utf-8')
    print(f'MOZ_APP_LAUNCHER in Firefox: {launcher_seen!r}; default before: {before}; after "Make default": {after}; '
          f'new entries: {written or "none"}')
    problems = []
    if not before:
        problems.append('Firefox Corsu does not recognise firefox.desktop as itself, so it will offer "Make default"')
    if written:
        problems.append(f'"Make default" wrote {written}, an entry without the Firefox icon')
    if 'userapp-' in defaults or 'x-scheme-handler/https=firefox.desktop' not in defaults:
        problems.append('mimeapps.list no longer names firefox.desktop:\n' + defaults)
    if problems:
        raise SystemExit('FAIL: ' + '; '.join(problems))
    print('PASS: Firefox Corsu is the default browser through firefox.desktop, with its icon')


if __name__ == '__main__':
    main(sys.argv[1])
