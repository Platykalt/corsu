"""A window that fails never takes Corsu with it: the window runs in a process of its own, and when that process
crashes (a .NET exception in pywebview's WinForms thread ends the whole process, Corsu 0.27.0) or never shows the page,
Corsu, still serving its page, opens it in the browser with a ticket of its own.

The window engines are replaced by a fake `webview` module put first on PYTHONPATH, which the window process imports.
"""
import http.client
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import window

SRC = Path(__file__).resolve().parent.parent / 'src'

FAKE_WEBVIEW = '''
import os, sys, time
BEHAVIOUR = os.environ['FAKE_WEBVIEW']

class Event:
    def __iadd__(self, handler):
        return self

class Window:
    def __init__(self):
        self.events = type('Events', (), {'shown': Event(), 'before_show': Event()})()

def create_window(*arguments, **options):
    return Window()

def start(**options):
    if BEHAVIOUR == 'crash':
        sys.stdout.flush()
        os._exit(3)  # as a .NET exception in pywebview's GUI thread ends the process: no Python traceback
    if BEHAVIOUR == 'hang':
        time.sleep(600)
'''


class FakeEngine:
    def __init__(self, test, behaviour):
        folder = tempfile.TemporaryDirectory()
        test.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        (self.folder / 'webview.py').write_text(FAKE_WEBVIEW, encoding='utf-8')
        home = self.folder / 'home'
        home.mkdir()
        self.environment = {'PYTHONPATH': str(self.folder), 'FAKE_WEBVIEW': behaviour, 'HOME': str(home),
                            'USERPROFILE': str(home), 'LOCALAPPDATA': str(home / 'AppData/Local'),
                            'APPDATA': str(home / 'AppData/Roaming'),
                            # Nothing reaches the network (the window's update check).
                            'https_proxy': 'http://127.0.0.1:9', 'HTTPS_PROXY': 'http://127.0.0.1:9'}


class WindowProcessTests(unittest.TestCase):
    def show(self, behaviour, loaded=None):
        engine = FakeEngine(self, behaviour)
        opened = []
        with patch.dict(os.environ, engine.environment), patch.object(window.webbrowser, 'open', opened.append), \
                patch.object(window, 'LOAD_SECONDS', 3):
            started = time.monotonic()
            result = window.show('http://127.0.0.1:1/#t=first', 'window', loaded=loaded,
                                 again=lambda: 'http://127.0.0.1:1/#t=second')
        return result, opened, time.monotonic() - started

    def test_a_crashing_window_sends_the_page_to_the_browser_with_a_new_ticket(self):
        result, opened, _ = self.show('crash')
        self.assertFalse(result)
        self.assertEqual(opened, ['http://127.0.0.1:1/#t=second'])

    def test_a_window_whose_page_never_loads_is_ended_and_the_browser_used(self):
        result, opened, seconds = self.show('hang', loaded=lambda: False)
        self.assertFalse(result)
        self.assertEqual(opened, ['http://127.0.0.1:1/#t=second'])
        self.assertLess(seconds, 60)

    def test_a_window_that_loaded_its_page_and_was_closed(self):
        result, opened, _ = self.show('close', loaded=lambda: True)
        self.assertTrue(result)
        self.assertEqual(opened, [])

    def test_the_ticket_is_not_on_the_window_process_command_line(self):
        calls = []

        class Process:
            returncode = 0

            def __init__(self, command, **options):
                calls.append((command, options))

            def wait(self, timeout=None):
                return 0
        with patch.object(window.subprocess, 'Popen', Process):
            self.assertIsNone(window.run_window('http://127.0.0.1:1/#t=secret'))
        command, options = calls[0]
        self.assertNotIn('secret', ' '.join(command))
        self.assertEqual(options['env']['CORSU_WINDOW_URL'], 'http://127.0.0.1:1/#t=secret')


class StartFailureTests(unittest.TestCase):
    def test_corsu_that_cannot_start_says_where_its_log_is_and_how_to_repair(self):
        import app
        import logbook
        shown = []
        with tempfile.TemporaryDirectory() as folder, patch.object(app.corsu, 'DATA', Path(folder)), \
                patch.object(sys, 'argv', ['app.py']), patch.object(sys, 'stdout', sys.stdout), \
                patch.object(sys, 'stderr', sys.stderr), patch.object(app, 'alert', shown.append), \
                patch.object(app, 'serve', side_effect=RuntimeError('Ports 7744 to 7753 are all in use')):
            with self.assertRaises(SystemExit) as stop:
                app.main()
            where = str(logbook.path())
            log = logbook.path().read_text(encoding='utf-8')
        self.assertEqual(stop.exception.code, 1)
        self.assertEqual(len(shown), 1)
        for part in ('Ports 7744 to 7753 are all in use', where, 'corsu-windows.zip',
                     'Install for Windows.cmd'):
            self.assertIn(part, shown[0])
        self.assertIn('RuntimeError: Ports 7744 to 7753', log)


@unittest.skipUnless(os.name == 'posix', 'BROWSER is given as a POSIX command line')
class CorsuSurvivesItsWindowTests(unittest.TestCase):
    """Corsu itself (src/app.py, as its shortcut starts it, without --browser) with a window engine that crashes. Before
    0.28.4 the window ran in Corsu's own process: the crash ended Corsu with its server, nothing on screen."""

    def test_the_page_opens_in_the_browser_and_works(self):
        engine = FakeEngine(self, 'crash')
        record = engine.folder / 'browser.txt'
        browser = engine.folder / 'browser.py'
        browser.write_text('import sys; open(sys.argv[1], "w").write(sys.argv[2])', encoding='utf-8')
        environment = {**os.environ, **engine.environment, 'PYTHONUTF8': '1',
                       'BROWSER': f'{shlex.quote(sys.executable)} {shlex.quote(str(browser))} {shlex.quote(str(record))} %s'}
        environment.pop('DISPLAY', None)
        environment.pop('WAYLAND_DISPLAY', None)
        process = subprocess.Popen([sys.executable, str(SRC / 'app.py')], env=environment, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline and process.poll() is None and not record.exists():
                time.sleep(0.2)
            data = 'Library/Application Support/corsu' if sys.platform == 'darwin' else '.local/share/corsu'
            log = Path(engine.environment['HOME']) / data / 'logs/corsu.log'
            details = log.read_text(encoding='utf-8') if log.exists() else '(no log)'
            self.assertIsNone(process.poll(), f'Corsu ended with its window (code {process.returncode}):\n{details}')
            self.assertTrue(record.exists(), f'the browser was not opened:\n{details}')
            address = record.read_text(encoding='utf-8')
            self.assertIn('#t=', address)
            self.assertIn("Corsu's window stopped (code 3)", details)
            # The page in the browser gets the key with its ticket: Corsu works there.
            port = int(address.split('#')[0].rstrip('/').rsplit(':', 1)[1])
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/api/key', body=json.dumps({'ticket': address.split('#t=')[1]}),
                               headers={'Host': f'127.0.0.1:{port}', 'X-Corsu': '1', 'Origin': f'http://127.0.0.1:{port}',
                                        'Content-Type': 'application/json'})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertTrue(json.loads(response.read())['key'])
            connection.close()
        finally:
            process.kill()
            process.wait()
            process.stdout.close()


if __name__ == '__main__':
    unittest.main()
