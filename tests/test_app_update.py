"""The Corsu window's update section on the server side: checks (with update.check() or the older update.latest()),
preferences, the automatic update, the update job's result, restarting from the newly installed copy, and Minecraft
game folders waiting for activation. Everything runs in a temporary data folder."""
import http.client
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

import app


class Isolated(unittest.TestCase):
    """corsu.DATA, the state file, the session file and the window's update memory in a temporary folder."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix='corsu-app-update-'))
        self.data = self.folder / 'data'
        self.data.mkdir()
        patches = [patch.object(app.corsu, 'DATA', self.data), patch.object(app.corsu, 'STATE', self.data / 'installation.json'),
                   patch.object(app.corsu, 'HOME', self.folder / 'home'), patch.object(app, 'SESSION', self.data / 'setup-session.json'),
                   patch.dict(app.UPDATE, {'info': None, 'checking': False, 'auto_started': None, 'restart_error': None}),
                   patch.dict(app.MINECRAFT, {'time': 0.0, 'waiting': []})]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.folder, ignore_errors=True)

    def release(self, name, version, program=None):
        """A release folder (releases/<name>/src/app.py and release.json), as the installer deploys it."""
        src = self.data / 'releases' / name / 'src'
        src.mkdir(parents=True)
        (src / 'release.json').write_text(json.dumps({'version': version}), encoding='utf-8')
        (src / 'app.py').write_text(program or 'print("new copy")\n', encoding='utf-8')
        return src.parent

    def write_state(self, state):
        app.corsu.STATE.write_text(json.dumps(state), encoding='utf-8')


class CheckTests(Isolated):
    def test_the_older_update_module_is_read_through_latest(self):
        current = app.running_version()
        with patch.object(app, 'update', MagicMock(spec=['latest', 'current'])) as update:
            update.latest.return_value = {'version': '999.0.0', 'newer': True, 'url': 'https://example.org/r'}
            info = app.update_check(force=True)
            update.latest.assert_called_once_with(force=True)
            self.assertEqual((info['status'], info['latest'], info['current'], info['error']), ('available', '999.0.0', current, None))
            update.latest.return_value = {'version': '0.0.1', 'newer': False, 'url': None}
            self.assertEqual(app.update_check()['status'], 'ahead')
            update.latest.return_value = {'version': current, 'newer': False, 'url': None}
            self.assertEqual(app.update_check()['status'], 'up_to_date')
            update.latest.return_value = None
            info = app.update_check()
            self.assertEqual(info['status'], 'unknown')
            self.assertTrue(info['error'])

    def test_check_is_used_when_update_has_it_and_failures_never_raise(self):
        answer = {'current': '1.0.0', 'latest': '1.1.0', 'tag': 'v1.1.0', 'url': None, 'status': 'available', 'checked': 1.0, 'error': None}
        with patch.object(app, 'update', MagicMock(spec=['check'])) as update:
            update.check.return_value = answer
            self.assertEqual(app.update_check(force=True), answer)
            update.check.assert_called_once_with(force=True)
            update.check.side_effect = OSError('network is unreachable')
            info = app.update_check()
        self.assertEqual(info['status'], 'unknown')
        self.assertIn('network is unreachable', info['error'])

    def test_preferences_default_off_and_persist(self):
        with patch.object(app, 'update', MagicMock(spec=['latest'])):
            self.assertIs(app.preferences()['auto_update'], False)
            app.set_preference('auto_update', True)
            self.assertIs(app.preferences()['auto_update'], True)
            self.assertEqual(json.loads((self.data / 'preferences.json').read_text(encoding='utf-8')), {'auto_update': True})
            (self.data / 'preferences.json').write_text('not json', encoding='utf-8')
            self.assertIs(app.preferences()['auto_update'], False)
        with patch.object(app, 'update', MagicMock(spec=['preferences', 'set_preference'])) as update:
            update.preferences.return_value = {'auto_update': True}
            self.assertIs(app.preferences()['auto_update'], True)
            app.set_preference('auto_update', False)
            update.set_preference.assert_called_once_with('auto_update', False)


class AutomaticUpdateTests(Isolated):
    def check(self, job, status='available', auto=True, latest='9.0.0'):
        info = {'current': '1.0.0', 'latest': latest, 'status': status, 'checked': 1.0, 'error': None}
        with patch.object(app, 'update_check', return_value=info), \
                patch.object(app, 'preferences', return_value={'auto_update': auto}):
            self.assertTrue(app.claim_check())
            app.check_update(job)

    def test_installs_a_stable_release_once_per_window(self):
        job = MagicMock(running=False)
        job.start.return_value = True
        self.check(job)
        job.start.assert_called_once()
        self.assertEqual(job.start.call_args[0][:2], ('update', ['--install', '--version', '9.0.0']))
        self.assertEqual(job.start.call_args[1], {'script': 'update.py'})
        self.assertEqual(app.UPDATE['auto_started'], '9.0.0')
        self.assertFalse(app.UPDATE['checking'])
        self.check(job)
        job.start.assert_called_once()

    def test_not_when_off_not_available_or_busy(self):
        job = MagicMock(running=False)
        self.check(job, auto=False)
        self.check(job, status='ahead')
        self.check(job, status='unknown')
        self.check(MagicMock(running=True))
        job.start.assert_not_called()
        self.assertIsNone(app.UPDATE['auto_started'])

    def test_a_check_already_running_is_not_doubled(self):
        self.assertTrue(app.claim_check())
        self.assertFalse(app.start_check(MagicMock()))
        app.UPDATE['checking'] = False


class JobTests(unittest.TestCase):
    def run_program(self, program):
        job = app.Job()
        job.running = True
        # The environment Job.start gives the scripts it runs.
        environment = {**os.environ, 'PYTHONUNBUFFERED': '1', 'PYTHONIOENCODING': 'utf-8'}
        with patch('logbook.path', return_value='log', create=True):
            job.run([sys.executable, '-c', program], environment)
        return job.snapshot()

    def run_lines(self, *lines, code=0):
        return self.run_program(''.join(f'print({line!r})\n' for line in lines) + f'raise SystemExit({code})\n')

    def test_result_and_progress_lines_stay_out_of_the_log(self):
        result = {'corsu': 'updated', 'from': '1.0.0', 'to': '1.1.0', 'restart_app': True, 'error': None}
        snapshot = self.run_lines('@progress 40 Downloading', 'Checksum verified.', '@result ' + json.dumps(result))
        self.assertEqual(snapshot['result'], result)
        self.assertEqual(snapshot['progress'], {'percent': 40, 'label': 'Downloading'})
        self.assertEqual(snapshot['lines'], ['Checksum verified.'])
        self.assertTrue(snapshot['ok'])
        self.assertFalse(snapshot['busy'])

    def test_the_installer_lock_reads_as_busy(self):
        self.assertTrue(self.run_lines('Corsu is already busy: update since 10:02', code=1)['busy'])
        self.assertTrue(self.run_lines('Corsu est déjà occupé : mise à jour depuis 10:02', code=1)['busy'])
        self.assertFalse(self.run_lines('Something else failed', code=1)['busy'])
        # A program writing in the Windows code page rather than UTF-8: each "é" arrives replaced.
        legacy = 'Corsu est déjà occupé : mise à jour'.encode('cp1252')
        self.assertTrue(self.run_program(f'import sys\nsys.stdout.buffer.write({legacy!r} + b"\\n")\nraise SystemExit(1)\n')['busy'])


class RestartInfoTests(Isolated):
    def test_offered_for_a_newer_installed_copy(self):
        folder = self.release('abc123', '99.0.0')
        state = {'files': {}, 'release': {'folder': str(folder), 'version': '99.0.0'}}
        info = app.restart_info(state, app.Job())
        self.assertEqual((info['available'], info['version']), (True, '99.0.0'))
        self.assertEqual(app.installed_app(state)[1], str(folder / 'src/app.py'))
        running = app.Job()
        running.running = True
        self.assertFalse(app.restart_info(state, running)['available'])

    def test_same_version_only_when_the_update_asks_for_it(self):
        folder = self.release('abc123', app.running_version())
        state = {'files': {}, 'release': {'folder': str(folder)}}
        job = app.Job()
        self.assertFalse(app.restart_info(state, job)['available'])
        job.title, job.result = 'update', {'corsu': 'repaired', 'restart_app': True}
        self.assertTrue(app.restart_info(state, job)['available'])

    def test_never_for_the_running_copy_nor_without_an_installation(self):
        self.assertFalse(app.restart_info({'files': {}}, app.Job())['available'])
        state = {'files': {}, 'release': {'folder': str(app.corsu.ROOT)}}
        job = app.Job()
        job.title, job.result = 'update', {'restart_app': True}
        self.assertFalse(app.restart_info(state, job)['available'])

    def test_the_menu_entry_is_the_fallback(self):
        folder = self.release('def456', '99.0.0')
        program = str(folder / 'src/app.py')
        entry = app.corsu.HOME / '.local/share/applications/corsu-setup.desktop'
        entry.parent.mkdir(parents=True)
        # Written as corsu.setup_shortcut writes it: each path quoted for the shell.
        entry.write_text(f'[Desktop Entry]\nName=Corsu\nExec={shlex.quote(sys.executable)} {shlex.quote(program)}\n', encoding='utf-8')
        with patch.object(app.corsu, 'PLATFORM', 'linux'):
            self.assertEqual(app.installed_app({'files': {}}), [sys.executable, program])
            self.assertTrue(app.restart_info({'files': {}}, app.Job())['available'])

    def test_the_windows_shortcut_is_read_through_the_shell(self):
        start_menu = self.folder / 'Start Menu'
        start_menu.mkdir()
        (start_menu / 'Corsu.lnk').write_bytes(b'L')
        answer = MagicMock(stdout='C:\\Corsu\\runtime\\pythonw.exe\n"C:\\Corsu\\releases\\abc\\src\\app.py"\n')
        with patch.object(app.corsu, 'PLATFORM', 'windows'), patch.object(app.corsu, 'START_MENU', start_menu, create=True), \
                patch.object(app.subprocess, 'run', return_value=answer) as run:
            self.assertEqual(app.shortcut_command(), ['C:\\Corsu\\runtime\\pythonw.exe', 'C:\\Corsu\\releases\\abc\\src\\app.py'])
        self.assertIn(str(start_menu / 'Corsu.lnk'), run.call_args[0][0][-1])
        with patch.object(app.corsu, 'PLATFORM', 'windows'), patch.object(app.corsu, 'START_MENU', self.folder / 'none', create=True):
            self.assertIsNone(app.shortcut_command())

    def test_the_macos_applet_is_read_through_its_script(self):
        script = app.corsu.HOME / 'Applications/Corsu.app/Contents/Resources/Scripts/main.scpt'
        script.parent.mkdir(parents=True)
        script.write_bytes(b'FasdUAS')
        answer = MagicMock(stdout='do shell script "exec \'/Users/a b/corsu/python3\' \'/Users/a b/corsu/releases/abc/src/app.py\' >/dev/null 2>&1 &"\n')
        with patch.object(app.corsu, 'PLATFORM', 'macos'), patch.object(app.subprocess, 'run', return_value=answer):
            self.assertEqual(app.shortcut_command(), ['/Users/a b/corsu/python3', '/Users/a b/corsu/releases/abc/src/app.py'])


class MinecraftWaitingTests(Isolated):
    def test_new_game_folders_wait_without_anything_written(self):
        import minecraft
        old, new, busy, unsupported = (self.folder / name for name in ('old', 'new', 'busy', 'unsupported'))
        for path in (old, new, busy, unsupported):
            path.mkdir()
        folders = [minecraft.Folder(old, 'Prism', '1.21.4'), minecraft.Folder(new, 'Prism', '1.21.4', loader='Fabric'),
                   minecraft.Folder(busy, 'official', '1.20.1'), minecraft.Folder(unsupported, 'official', '0.1')]
        state = {'files': {str(old / 'options.txt'): {'component': 'minecraft', 'options_original': {}}}}
        with patch.object(minecraft, 'find_folders', return_value=folders), \
                patch.object(minecraft, 'target', side_effect=lambda version: None if version == '0.1' else {'language_code': 'co_fr'}), \
                patch.object(minecraft, 'running_folders', return_value={busy.resolve()}):
            waiting = app.minecraft_waiting(state, None)
        self.assertEqual([item['location'] for item in waiting], [str(new), str(busy)])
        self.assertEqual({item['activation'] for item in waiting}, {'waiting'})
        self.assertEqual(waiting[0]['loader'], 'Fabric')
        self.assertIsNone(waiting[0]['action'])
        self.assertIn('Minecraft', waiting[1]['action'])
        self.assertEqual(sorted(path.name for path in self.folder.iterdir()), ['busy', 'data', 'new', 'old', 'unsupported'])
        self.assertEqual([path.name for path in new.iterdir()], [])
        # Folders the last installation already listed (blocked, unsupported) are not repeated.
        app.MINECRAFT['time'] = 0.0
        with patch.object(minecraft, 'find_folders', return_value=folders), \
                patch.object(minecraft, 'target', return_value={'language_code': 'co_fr'}), \
                patch.object(minecraft, 'running_folders', return_value=set()):
            waiting = app.minecraft_waiting(state, {'instances': [{'location': str(new)}, {'location': str(busy)}]})
        self.assertEqual([item['location'] for item in waiting], [str(unsupported)])


class ServerTests(Isolated):
    def setUp(self):
        super().setUp()
        self.job = app.Job()
        self.handover = MagicMock()
        self.server = app.Server(('127.0.0.1', 0), app.make_handler(self.job, [0.0], 0))
        self.port = self.server.server_address[1]
        self.server.RequestHandlerClass = app.make_handler(self.job, [0.0], self.port, self.handover)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        super().tearDown()

    def request(self, method, path, corsu=True, body=None, host=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        headers = {'Host': host or f'127.0.0.1:{self.port}', 'Content-Type': 'application/json'}
        if corsu:
            headers.update({'X-Corsu': '1', 'X-Corsu-Key': app.ACCESS.key})
        connection.request(method, path, body=json.dumps(body or {}) if method == 'POST' else None, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read() or b'null')

    def test_new_actions_need_corsus_page(self):
        with patch.object(app, 'update_check') as check, patch.object(app, 'set_preference') as save:
            for path in ('/api/update/check', '/api/preferences', '/api/restart'):
                self.assertEqual(self.request('POST', path, corsu=False, body={'auto_update': True})[0], 403, path)
                self.assertEqual(self.request('POST', path, host='attacker.example', body={'auto_update': True})[0], 403, path)
            with patch.object(app.corsu, 'PLATFORM', 'linux'), patch.object(app, 'peer_uid', return_value=-5), \
                    patch.object(app.os, 'getuid', create=True, return_value=1000):
                self.assertEqual(self.request('POST', '/api/restart')[0], 403)
            # A caller whose connection cannot be found, or found twice with different users, is refused too.
            with patch.object(app.corsu, 'PLATFORM', 'linux'), patch.object(app, 'peer_uid', return_value=None), \
                    patch.object(app.os, 'getuid', create=True, return_value=1000):
                for path in ('/api/update/check', '/api/preferences', '/api/restart'):
                    self.assertEqual(self.request('POST', path, body={'auto_update': True})[0], 403, path)
        check.assert_not_called()
        save.assert_not_called()
        self.handover.start.assert_not_called()

    def test_check_runs_in_the_background_and_once_at_a_time(self):
        release = threading.Event()
        calls = []

        def slow(force=False):
            calls.append(force)
            release.wait(5)
            return {'current': '1.0.0', 'latest': '1.0.0', 'status': 'up_to_date', 'checked': 2.0, 'error': None}

        with patch.object(app, 'update_check', side_effect=slow):
            self.assertEqual(self.request('POST', '/api/update/check'), (200, {'checking': True}))
            self.assertEqual(self.request('POST', '/api/update/check'), (200, {'checking': True}))
            with patch.object(app, 'snapshot', side_effect=lambda job=None: {'update': dict(app.UPDATE)}):
                self.assertTrue(self.request('GET', '/api/state')[1]['update']['checking'])
            release.set()
            for _ in range(50):
                if not app.UPDATE['checking']:
                    break
                time.sleep(0.05)
        self.assertEqual(calls, [True])
        self.assertEqual(app.UPDATE['info']['status'], 'up_to_date')

    def test_preferences_take_booleans_only(self):
        with patch.object(app, 'update', MagicMock(spec=['latest'])):
            self.assertEqual(self.request('POST', '/api/preferences', body={'auto_update': 'yes'})[0], 400)
            status, body = self.request('POST', '/api/preferences', body={'auto_update': True})
        self.assertEqual((status, body['preferences']['auto_update']), (200, True))
        self.assertTrue(json.loads((self.data / 'preferences.json').read_text(encoding='utf-8'))['auto_update'])

    def test_update_installs_the_version_shown(self):
        app.UPDATE['info'] = {'status': 'available', 'latest': '9.1.0'}
        with patch.object(self.job, 'start', return_value=True) as start:
            self.assertEqual(self.request('POST', '/api/update', body={'language': 'en'})[0], 200)
        start.assert_called_once_with('update', ['--install', '--version', '9.1.0'], 'en', script='update.py')
        app.UPDATE['info'] = {'status': 'available', 'latest': '9.1.0; rm -rf /'}
        with patch.object(self.job, 'start', return_value=False) as start:
            self.assertEqual(self.request('POST', '/api/update')[0], 409)
        start.assert_called_once_with('update', ['--install'], 'fr', script='update.py')

    def test_restart(self):
        self.assertEqual(self.request('POST', '/api/restart'), (200, {'restarting': True}))
        self.handover.start.assert_called_once()
        self.handover.start.side_effect = RuntimeError('nothing newer')
        self.assertEqual(self.request('POST', '/api/restart'), (400, {'error': 'nothing newer'}))
        self.job.running = True
        self.assertEqual(self.request('POST', '/api/restart')[0], 409)

    def test_state_carries_the_update_section(self):
        self.release('abc', '99.0.0')
        self.write_state({'files': {}, 'components': [], 'release': {'folder': str(self.data / 'releases/abc')}})
        app.UPDATE['info'] = {'current': '1.0.0', 'latest': '99.0.0', 'status': 'available', 'checked': 3.0, 'error': None}
        with patch.object(app, 'detected', return_value=set()), patch.object(app, 'update', MagicMock(spec=['latest'])):
            status, state = self.request('GET', '/api/state')
        self.assertEqual(status, 200)
        self.assertEqual(state['update']['status'], 'available')
        self.assertFalse(state['update']['checking'])
        self.assertEqual(state['update']['restart'], {'available': True, 'version': '99.0.0', 'error': None})
        self.assertEqual(state['preferences'], {'auto_update': False})
        self.assertEqual(state['pid'], os.getpid())
        self.assertIn('result', state['job'])


# A stand-in for the newly installed copy: takes the port it is given with --replace, answers /api/state with its
# own pid for a few seconds, then ends.
NEW_COPY = textwrap.dedent('''
    import json, os, socketserver, sys, time
    from http.server import BaseHTTPRequestHandler, HTTPServer
    if os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))) == 'fail':
        raise SystemExit(3)
    port = int(sys.argv[sys.argv.index('--replace') + 1])
    asked = []
    class Quick(HTTPServer):
        # As app.Server: no reverse name lookup, which can take seconds on macOS.
        def server_bind(self):
            socketserver.TCPServer.server_bind(self)
            self.server_name, self.server_port = 'localhost', port
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *arguments):
            pass
        def do_GET(self):
            data = json.dumps({'pid': os.getpid(), 'argv': sys.argv[1:]}).encode()
            self.send_response(200)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            asked.append(time.time())
    for _ in range(300):
        try:
            server = Quick(('127.0.0.1', port), Handler)
            break
        except OSError:
            time.sleep(0.1)
    server.timeout = 0.2
    # Serves until a little after the first answer (the old window and the test both ask), at most a minute.
    end = time.time() + 60
    while time.time() < end and not (asked and time.time() > asked[0] + 3):
        server.handle_request()
''')


class HandoverTests(Isolated):
    def start_window(self):
        self.job = app.Job()
        self.activity = [time.monotonic()]
        self.holder = {}
        # Any free port, not Corsu's own 7744 and following: a real Corsu window may be open.
        server = app.Server(('127.0.0.1', 0), app.make_handler(self.job, self.activity, 0))
        self.port = server.server_address[1]
        self.handover = app.Handover(self.job, self.activity, self.holder, self.port)
        server.RequestHandlerClass = app.make_handler(self.job, self.activity, self.port, self.handover)
        self.holder['server'] = server
        threading.Thread(target=server.serve_forever, daemon=True).start()

    def wait(self):
        deadline = time.monotonic() + app.Handover.WAIT + 10
        while time.monotonic() < deadline:
            if not self.handover.running:
                return
            time.sleep(0.05)
        self.fail('the restart did not finish')

    def state_of(self):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        connection.request('GET', '/api/state', headers={'Host': f'127.0.0.1:{self.port}', 'X-Corsu': '1',
                                                                 'X-Corsu-Key': app.ACCESS.key})
        return json.loads(connection.getresponse().read())

    def test_the_new_copy_takes_the_same_address(self):
        folder = self.release('new', '99.0.0', NEW_COPY)
        self.write_state({'files': {}, 'release': {'folder': str(folder), 'python': sys.executable}})
        self.start_window()
        with patch.object(app, 'ARGUMENTS', ['--browser']), patch.object(app.Handover, 'WAIT', 30):
            self.handover.start()
            self.wait()
        self.assertTrue(self.handover.done)
        self.assertIsNone(app.UPDATE['restart_error'])
        answer = self.state_of()
        self.assertNotEqual(answer['pid'], os.getpid())
        self.assertEqual(answer['argv'], ['--browser', '--replace', str(self.port)])
        self.handover.process.wait(10)

    def test_a_new_copy_that_fails_gives_the_address_back(self):
        folder = self.release('fail', '99.0.0', NEW_COPY)
        self.write_state({'files': {}, 'release': {'folder': str(folder)}})
        self.start_window()
        try:
            with patch.object(app.Handover, 'WAIT', 30), patch.object(app, 'snapshot', return_value={'pid': os.getpid()}):
                self.handover.start()
                self.wait()
                self.assertFalse(self.handover.done)
                self.assertIn('3', app.UPDATE['restart_error'])
                self.assertEqual(self.state_of()['pid'], os.getpid())
        finally:
            self.holder['server'].shutdown()
            self.holder['server'].server_close()

    def test_refused_without_a_newer_copy(self):
        self.start_window()
        try:
            with self.assertRaises(RuntimeError):
                self.handover.start()
            self.assertFalse(self.handover.running)
        finally:
            self.holder['server'].shutdown()
            self.holder['server'].server_close()


if __name__ == '__main__':
    unittest.main()
