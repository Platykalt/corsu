"""Discord start watch, Corsu's side (docs/dev/discord-watch.md): native notifications (src/notify.py), the window's
Discord status and actions (src/app.py) against a stub of src/discord_watch.py, and the discord-recovery page and
home row drawn in node (src/app/discord.js). Simulated: no notification server, no Discord, no real watcher."""
import http.client
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch

import app
import corsu
import notify
from tests.test_app_ui import HARNESS, PAGE, FIXTURE, all_texts

INCIDENT = '0b8c2f9e-1d2a-4c3b-9f00-123456789abc'


class Data(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.data = Path(folder.name)
        for name, value in (('DATA', self.data), ('STATE', self.data / 'installation.json')):
            patcher = patch.object(corsu, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def watch_state(self, state, **fields):
        folder = self.data / 'discord-watch'
        folder.mkdir(exist_ok=True)
        record = {'version': 1, 'incident': INCIDENT, 'state': state, 'started_at': 1.79e9, 'decided_at': 1.79e9 + 20,
                  'launch': 'shortcut', 'client': '/home/x/.config/discord/app-1.0.168', 'app_version': '1.0.168',
                  'vencord': {'injected': True, 'revision': '383409e6a6ec9008', 'corsu_version': '0.28.4',
                              'dist': '/data/releases/new/Vencord/dist'},
                  'evidence': [{'t': 1.0, 'kind': 'uncaught', 'line': 'Uncaught TypeError: i.A is not a constructor'}],
                  'notified': False, 'dismissed': False, **fields}
        (folder / 'state.json').write_text(json.dumps(record), encoding='utf-8')
        return record


class NotifyTests(Data):
    def run_result(self, code=0, stdout=''):
        return subprocess.CompletedProcess([], code, stdout=stdout, stderr='')

    def test_linux_uses_the_notification_service_with_a_button_and_waits_for_the_click(self):
        with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(shutil, 'which', lambda name: '/usr/bin/' + name), \
                patch.object(subprocess, 'run', return_value=self.run_result(stdout='(uint32 42,)\n')) as run, \
                patch.object(subprocess, 'Popen') as popen:
            self.assertTrue(notify.notify("Discord n'a pas démarré", 'Corps « 1 »', 'discord-recovery', INCIDENT))
        command = run.call_args[0][0]
        self.assertEqual(command[:3], ['/usr/bin/gdbus', 'call', '--session'])
        self.assertIn('org.freedesktop.Notifications.Notify', command)
        self.assertIn("'Discord n\\'a pas démarré'", command)  # GVariant quoting
        self.assertTrue(any("'default'" in part and "'open'" in part for part in command))
        self.assertTrue(any("'urgency': <byte 1>" in part for part in command))
        helper = popen.call_args[0][0]
        self.assertEqual(helper[2:4], ['wait', '42'])
        self.assertEqual(helper[-4:], ['--page', 'discord-recovery', '--incident', INCIDENT])
        self.assertTrue(popen.call_args[1]['start_new_session'])

    def test_one_notification_per_incident(self):
        with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(shutil, 'which', lambda name: '/usr/bin/' + name), \
                patch.object(subprocess, 'run', return_value=self.run_result(stdout='(uint32 7,)')) as run, \
                patch.object(subprocess, 'Popen'):
            self.assertTrue(notify.notify('T', 'B', 'discord-recovery', INCIDENT))
            self.assertTrue(notify.notify('T', 'B', 'discord-recovery', INCIDENT))
            self.assertTrue(notify.notify('T', 'B', 'discord-recovery', 'another'))
        self.assertEqual(run.call_count, 2)

    def test_notify_send_without_button_then_nothing(self):
        found = {'notify-send': '/usr/bin/notify-send'}
        with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(shutil, 'which', found.get), \
                patch.object(subprocess, 'run', return_value=self.run_result()) as run:
            self.assertTrue(notify.notify('T', 'B', 'discord-recovery', INCIDENT))
        self.assertEqual(run.call_args[0][0], ['/usr/bin/notify-send', '--app-name=Corsu', '--urgency=normal', 'T', 'B'])
        with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(shutil, 'which', lambda name: None):
            self.assertFalse(notify.notify('T', 'B', 'discord-recovery', 'other-incident'))
        # Not shown, so not remembered: a later try may show it.
        self.assertNotIn('other-incident', notify.sent())

    def test_a_refused_notification_falls_back_and_reports_false(self):
        with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(shutil, 'which', lambda name: '/usr/bin/' + name), \
                patch.object(subprocess, 'run', return_value=self.run_result(1)):
            self.assertFalse(notify.notify('T', 'B', 'discord-recovery', INCIDENT))

    def test_windows_toast_without_console_and_escaped(self):
        with patch.object(corsu, 'PLATFORM', 'windows'), patch.object(corsu, 'console_window', return_value=0), \
                patch.object(subprocess, 'run', return_value=self.run_result()) as run:
            self.assertTrue(notify.notify('A <b> & "c"', 'B', 'discord-recovery', INCIDENT))
        command, options = run.call_args[0][0], run.call_args[1]
        self.assertEqual(command[0], 'powershell')
        self.assertEqual(options['creationflags'] & corsu.CREATE_NO_WINDOW, corsu.CREATE_NO_WINDOW)
        self.assertIn('<text>A &lt;b&gt; &amp; "c"</text>', options['env']['CORSU_TOAST'])
        self.assertNotIn('A <b>', ' '.join(command))  # the text travels in the environment, never in the command

    def test_macos_passes_texts_as_arguments(self):
        with patch.object(corsu, 'PLATFORM', 'macos'), patch.object(subprocess, 'run', return_value=self.run_result()) as run:
            self.assertTrue(notify.notify('Titre "x"', 'Corps', None, None))
        self.assertEqual(run.call_args[0][0][-2:], ['Titre "x"', 'Corps'])

    def test_unknown_pages_and_odd_incidents_are_not_passed_on(self):
        self.assertEqual(notify.window_command('../../evil', 'x')[2:], [])
        self.assertEqual(notify.window_command('discord-recovery', '; rm -rf')[2:], ['--page', 'discord-recovery'])

    def test_click_helper_opens_the_window_only_for_its_notification(self):
        lines = ["/org/freedesktop/Notifications: org.freedesktop.Notifications.ActionInvoked (uint32 41, 'open')\n",
                 "/org/freedesktop/Notifications: org.freedesktop.Notifications.ActionInvoked (uint32 42, 'open')\n"]
        monitor = types.SimpleNamespace(stdout=iter(lines), kill=lambda: None)
        with patch.object(subprocess, 'Popen', side_effect=[monitor, None]) as popen:
            notify.wait_for_click('42', ['python', 'app.py', '--page', 'discord-recovery'])
        self.assertEqual(popen.call_args_list[1][0][0], ['python', 'app.py', '--page', 'discord-recovery'])
        closed = ["/org/freedesktop/Notifications: org.freedesktop.Notifications.NotificationClosed (uint32 42, uint32 2)\n"]
        monitor = types.SimpleNamespace(stdout=iter(closed), kill=lambda: None)
        with patch.object(subprocess, 'Popen', side_effect=[monitor]) as popen:
            notify.wait_for_click('42', ['python'])
        self.assertEqual(popen.call_count, 1)


def stub_watch(**overrides):
    """A stand-in for src/discord_watch.py with the contract's rescue API, recording its calls."""
    module = types.ModuleType('discord_watch')
    module.__file__ = str(Path(app.__file__).with_name('discord_watch.py'))
    module.calls = []
    module.rescue_check = lambda: {'ok': True, 'reason': None}
    module.rescue = lambda incident: module.calls.append(('rescue', incident)) or {'ok': True}
    module.reactivate = lambda: module.calls.append(('reactivate',)) or {'ok': True}
    for name, value in overrides.items():
        setattr(module, name, value)
    return module


class StatusTests(Data):
    def setUp(self):
        super().setUp()
        patcher = patch.object(app, 'still_open', return_value=False)
        self.still_open = patcher.start()
        self.addCleanup(patcher.stop)
        app.DISCORD['action'] = None

    def status(self, items=None, state=None, watch=None):
        items = items if items is not None else [{'name': 'discord', 'installed': True, 'on': True, 'activation': 'active'}]
        # None in sys.modules makes `import discord_watch` fail: the window without the watch module.
        with patch.dict(sys.modules, {'discord_watch': watch}):
            return app.discord_status(state or {'release': {'folder': '/data/releases/new'}}, items)

    def test_rows(self):
        self.assertIsNone(self.status(items=[]))
        self.assertEqual(self.status()['row'], 'active')
        self.watch_state('ok-corsu')
        self.assertEqual(self.status()['row'], 'active')
        self.assertEqual(self.status(items=[{'name': 'discord', 'installed': True, 'on': True,
                                              'activation': 'restart_required'}])['row'], 'restart')
        for state in app.WATCH_PROBLEMS:
            self.watch_state(state)
            found = self.status()
            self.assertEqual((found['row'], found['problem'], found['incident']), ('problem', True, INCIDENT), state)
        self.watch_state('vencord-error', dismissed=True)
        self.assertEqual(self.status()['row'], 'active')
        (self.data / 'discord-watch/rescue.json').write_text(json.dumps({'location': '/x', 'since': 1.79e9,
                                                                         'from_revision': 'abc'}))
        self.assertEqual(self.status()['row'], 'rescue')
        self.assertEqual(self.status()['rescue']['since'], 1.79e9)

    def test_discord_still_on_the_old_copy_needs_a_restart(self):
        self.watch_state('ok-corsu', vencord={'injected': True, 'revision': 'r', 'corsu_version': '0.28.3',
                                              'dist': '/data/releases/old/Vencord/dist'})
        self.assertEqual(self.status()['row'], 'active')  # closed since: nothing to do
        self.still_open.return_value = True
        found = self.status()
        self.assertEqual((found['row'], found['old_corsu']), ('restart', True))

    def test_unknown_or_damaged_records_are_ignored(self):
        self.watch_state('something-new')
        self.assertIsNone(self.status()['state'])
        (self.data / 'discord-watch/state.json').write_text('{broken')
        self.assertEqual(self.status()['row'], 'active')

    def test_evidence_is_bounded_and_the_watch_module_optional(self):
        self.watch_state('start-error', evidence=[{'t': n, 'kind': 'x' * 80, 'line': 'y' * 900} for n in range(30)])
        found = self.status()
        self.assertEqual((len(found['evidence']), len(found['evidence'][0]['line']), len(found['evidence'][0]['kind'])),
                         (20, 300, 40))
        self.assertFalse(found['watch_available'])
        self.assertTrue(self.status(watch=stub_watch())['watch_available'])

    def act(self, name, watch, incident=INCIDENT):
        with patch.dict(sys.modules, {'discord_watch': watch}):
            app.run_discord_action(name, incident)
        return app.DISCORD['action']['result']

    def test_rescue_checks_first_and_passes_the_incident(self):
        watch = stub_watch()
        self.assertEqual(self.act('rescue', watch), {'ok': True})
        self.assertEqual(watch.calls, [('rescue', INCIDENT)])
        refused = stub_watch(rescue_check=lambda: {'ok': False, 'reason': 'backup-mismatch'})
        self.assertEqual(self.act('rescue', refused), {'ok': False, 'reason': 'backup-mismatch'})
        self.assertEqual(refused.calls, [])
        # rescue() without a parameter, as the contract's API list writes it.
        plain = stub_watch(rescue=lambda: True)
        self.assertEqual(self.act('rescue', plain), {'ok': True})

    def test_failures_are_reported_not_raised(self):
        def broken():
            raise OSError('disk full')
        self.assertEqual(self.act('reactivate', stub_watch(reactivate=broken)),
                         {'ok': False, 'reason': 'error', 'error': 'disk full'})
        sys.modules.pop('discord_watch', None)
        with patch.object(app, 'discord_watch', return_value=None):
            app.run_discord_action('rescue', INCIDENT)
        self.assertEqual(app.DISCORD['action']['result'], {'ok': False, 'reason': 'unavailable'})

    def test_retry_never_over_an_open_discord(self):
        self.still_open.return_value = True
        with patch.object(subprocess, 'Popen') as popen:
            self.assertEqual(self.act('retry', stub_watch()), {'ok': False, 'reason': 'running'})
            popen.assert_not_called()
            self.still_open.return_value = False
            self.assertEqual(self.act('retry', stub_watch()), {'ok': True})
        command = popen.call_args[0][0]
        self.assertEqual(command[1:], [str(Path(app.__file__).with_name('discord_watch.py').resolve()), 'launch', '--'])

    def test_one_action_at_a_time(self):
        release = threading.Event()
        watch = stub_watch(reactivate=lambda: release.wait(5) and {'ok': True})
        with patch.dict(sys.modules, {'discord_watch': watch}):
            self.assertTrue(app.start_discord_action('reactivate', None))
            self.assertFalse(app.start_discord_action('rescue', INCIDENT))
            release.set()
            for _ in range(100):
                if not app.DISCORD['action']['running']:
                    break
                time.sleep(0.02)
        self.assertEqual(app.DISCORD['action']['result'], {'ok': True})

    def test_later_dismisses_only_the_current_incident(self):
        self.watch_state('slow')
        sys.modules.pop('discord_watch', None)
        with patch.object(app, 'discord_watch', return_value=None):
            self.assertFalse(app.dismiss_incident('another'))
            self.assertTrue(app.dismiss_incident(INCIDENT))
        self.assertTrue(json.loads((self.data / 'discord-watch/state.json').read_text())['dismissed'])

    def test_page_query_from_the_notification_arguments(self):
        self.assertEqual(app.page_query(['--page', 'discord-recovery', '--incident', INCIDENT]),
                         f'?page=discord-recovery&incident={INCIDENT}')
        self.assertEqual(app.page_query(['--page', 'discord-recovery', '--incident', '<script>']), '?page=discord-recovery')
        self.assertEqual(app.page_query(['--page', 'about']), '')
        self.assertEqual(app.page_query(['--incident']), '')


class RouteTests(Data):
    def setUp(self):
        super().setUp()
        self.job = app.Job()
        self.server = app.Server(('127.0.0.1', 0), app.make_handler(self.job, [0.0], 0))
        self.port = self.server.server_address[1]
        self.server.RequestHandlerClass = app.make_handler(self.job, [0.0], self.port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        app.DISCORD['action'] = None

    def post(self, path, body, key=True):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        headers = {'Host': f'127.0.0.1:{self.port}', 'Content-Type': 'application/json', 'X-Corsu': '1'}
        if key:
            headers['X-Corsu-Key'] = app.ACCESS.key
        connection.request('POST', path, body=json.dumps(body), headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read() or b'{}')

    def test_routes_need_the_key_and_run_the_rescue(self):
        watch = stub_watch()
        with patch.dict(sys.modules, {'discord_watch': watch}), \
                patch.object(app, 'peer_uid', return_value=os.getuid() if hasattr(os, 'getuid') else 0):
            self.assertEqual(self.post('/api/discord/rescue', {'incident': INCIDENT}, key=False)[0], 403)
            self.assertEqual(self.post('/api/discord/rescue', {'incident': INCIDENT}), (200, {'started': True}))
            for _ in range(100):
                if app.DISCORD['action'] and not app.DISCORD['action']['running']:
                    break
                time.sleep(0.02)
            self.assertEqual(watch.calls, [('rescue', INCIDENT)])
            self.watch_state('slow')
            self.assertEqual(self.post('/api/discord/dismiss', {'incident': INCIDENT})[1], {'dismissed': True})
            self.assertEqual(self.post('/api/discord/dismiss', {'incident': '../x'})[1], {'dismissed': False})


# The page in node (the same small DOM as tests/test_app_ui.py): the home row and the recovery page per state.
SCRIPT = HARNESS[:HARNESS.index('const out = vm.runInContext(`')] + r'''
const out = vm.runInContext(`
  const clean = value => value == null ? value : value.replace(/[\\u00a0\\u202f]/g, " ");
  const visible = () => ["check", "install", "rescue", "reactivate", "retry", "later"].filter(name => !$("dr-" + name).hidden);
  const results = {};
  language = "fr";
  for (const [name, discord, extra] of fixture.cases) {
    state = JSON.parse(JSON.stringify({ ...fixture.base, ...(extra || {}), discord }));
    render();
    results[name] = { row: $("discord-status").hidden ? null : clean($("discord-status-text").textContent),
      chip: clean($("discord-status-chip").textContent), message: clean($("dr-message").textContent), buttons: visible(),
      disabled: visible().filter(name => $("dr-" + name).disabled), update: $("dr-update").hidden ? null : clean($("dr-update").textContent),
      result: clean($("dr-result").textContent), running: !$("dr-running").hidden,
      evidence: $("dr-evidence").children.map(node => clean(node.textContent)), facts: $("dr-facts").children.map(node => clean(node.textContent)),
      help: $("dr-help").getAttribute("href") };
  }
  language = "co"; state = JSON.parse(JSON.stringify({ ...fixture.base, discord: fixture.cases[0][1] })); render();
  results.corsican = clean($("dr-message").textContent);
  JSON.stringify(results);
`, context);
const opened = vm.runInContext(`(async () => {
  call = async () => JSON.parse(JSON.stringify({ ...fixture.base, discord: fixture.cases[0][1] }));
  state = null; page = null;
  await refresh();
  return page;
})()`, context);
opened.then(page => process.stdout.write(JSON.stringify({ ...JSON.parse(out), openedPage: page })));
'''

WATCH = {'row': 'problem', 'state': 'vencord-error', 'problem': True, 'incident': INCIDENT, 'started_at': 1.79e9,
         'decided_at': 1.79e9, 'launch': 'shortcut', 'app_version': '1.0.168', 'client': '/x',
         'vencord': {'injected': True, 'revision': '7f0c10cc1234567890', 'corsu_version': '0.28.3'},
         'evidence': [{'t': 1, 'kind': 'uncaught', 'line': 'Uncaught TypeError: i.A is not a constructor'}],
         'dismissed': False, 'rescue': None, 'old_corsu': False, 'running': False, 'watch_available': True, 'action': None}
UP = {'current': '0.28.4', 'latest': '0.28.4', 'status': 'up_to_date', 'checked': 1.79e9, 'error': None, 'checking': False,
      'auto_started': None, 'restart': {'available': False, 'version': None, 'error': None}}


def case(name, extra=None, **fields):
    return [name, {**WATCH, **fields}, extra]


CASES = [
    case('vencord-error'),
    case('start-error', state='start-error'),
    case('slow', state='slow'),
    case('network', state='network'),
    case('offscreen', state='offscreen'),
    case('ok', row='active', state='ok-corsu', problem=False),
    case('rescue', row='rescue', state='vencord-error', rescue={'location': '/x', 'since': 1.79e9, 'from_revision': 'r'}),
    case('restart', row='restart', state='ok-corsu', problem=False, old_corsu=True, running=True),
    case('running', running=True),
    case('no-watch-module', watch_available=False),
    case('dismissed', dismissed=True, row='active'),
    case('busy', action={'name': 'rescue', 'running': True, 'result': None}),
    case('refused', action={'name': 'rescue', 'running': False, 'result': {'ok': False, 'reason': 'running'}}),
    case('failed', action={'name': 'reactivate', 'running': False, 'result': {'ok': False, 'reason': 'backup-mismatch'}}),
    case('done', action={'name': 'retry', 'running': False, 'result': {'ok': True}}),
    case('available', {'update': {**UP, 'latest': '0.29.0', 'status': 'available'}}),
    case('unknown', {'update': {**UP, 'status': 'unknown', 'error': 'GitHub est injoignable'}}),
    case('ahead', {'update': {**UP, 'latest': '0.28.3', 'status': 'ahead'}}),
    case('installed-restart-corsu', {'update': {**UP, 'restart': {'available': True, 'version': '0.29.0', 'error': None}}}),
    ['nothing', None, None],
]


@unittest.skipUnless(shutil.which('node'), 'node is not installed')
class PageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = {**FIXTURE, 'version': '0.28.4', 'update': UP, 'preferences': {'auto_update': False}}
        with tempfile.TemporaryDirectory() as folder:
            harness, fixture = Path(folder) / 'harness.js', Path(folder) / 'fixture.json'
            harness.write_text(SCRIPT, encoding='utf-8')
            fixture.write_text(json.dumps({'base': base, 'cases': CASES}), encoding='utf-8')
            # A notification's button opens the window with ?page=discord-recovery.
            code = harness.read_text(encoding='utf-8').replace('location: { hash: "", pathname: "/", search: "" }',
                                                               'location: { hash: "", pathname: "/", search: "?page=discord-recovery&incident=x" }')
            harness.write_text(code, encoding='utf-8')
            done = subprocess.run(['node', str(harness), str(PAGE), str(fixture)], capture_output=True, text=True,
                                  encoding='utf-8', timeout=60)
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.result = json.loads(done.stdout)

    def test_messages_never_state_a_certain_cause(self):
        self.assertIn('probablement une incompatibilité', self.result['vencord-error']['message'])
        self.assertEqual(self.result['start-error']['message'],
                         'Discord rencontre un problème au démarrage. Vous pouvez rechercher une mise à jour de Corsu '
                         'ou essayer de démarrer sans la traduction.')
        self.assertIn('cause est inconnue', self.result['slow']['message'])
        self.assertIn('probablement pas en cause', self.result['network']['message'])
        self.assertTrue(self.result['corsican'].startswith('Discord s\'hè piantatu'))
        for name, found in self.result.items():
            if isinstance(found, dict) and found.get('update'):
                self.assertNotRegex(found['update'], r'(corrige|résout|répare) (le|ce) problème', name)

    def test_actions_per_state_in_focus_order(self):
        problem = ['check', 'rescue', 'retry', 'later']
        for name in ('vencord-error', 'start-error', 'slow'):
            self.assertEqual(self.result[name]['buttons'], problem, name)
        self.assertEqual(self.result['network']['buttons'], ['retry', 'later'])
        self.assertEqual(self.result['offscreen']['buttons'], ['later'])
        self.assertEqual(self.result['ok']['buttons'], [])
        self.assertEqual(self.result['rescue']['buttons'], ['check', 'reactivate'])
        self.assertEqual(self.result['no-watch-module']['buttons'], ['check', 'later'])
        self.assertEqual(self.result['dismissed']['buttons'], ['check', 'rescue', 'retry'])
        self.assertEqual(self.result['available']['buttons'], ['check', 'install', 'rescue', 'retry', 'later'])
        self.assertEqual(self.result['nothing']['buttons'], [])
        self.assertEqual(self.result['nothing']['message'], "Aucun démarrage de Discord n'a encore été observé.")

    def test_open_discord_blocks_rescue_and_retry(self):
        self.assertEqual(self.result['running']['disabled'], ['rescue', 'retry'])
        self.assertTrue(self.result['running']['running'])
        self.assertFalse(self.result['vencord-error']['running'])
        self.assertEqual(self.result['busy']['disabled'], ['check', 'rescue', 'retry', 'later'])

    def test_action_results_are_spoken(self):
        self.assertEqual(self.result['busy']['result'], 'Passage en mode de secours…')
        self.assertIn('Quittez-le complètement', self.result['refused']['result'])
        self.assertIn('backup-mismatch', self.result['failed']['result'])
        self.assertEqual(self.result['done']['result'], 'Discord démarre ; Corsu surveille ce démarrage.')

    def test_update_states(self):
        self.assertIn('Corsu est à jour', self.result['vencord-error']['update'])
        self.assertIn('0.29.0', self.result['available']['update'])
        self.assertIn('Les notes de version disent ce que chaque version corrige.', self.result['available']['update'])
        self.assertIn('GitHub est injoignable', self.result['unknown']['update'])
        self.assertIn('version de développement', self.result['ahead']['update'])
        self.assertEqual(self.result['installed-restart-corsu']['update'], "Corsu 0.29.0 est installé. Redémarrez Corsu pour l'utiliser.")
        self.assertIsNone(self.result['ok']['update'])

    def test_home_row(self):
        self.assertEqual(self.result['vencord-error']['row'], 'Problème détecté au dernier démarrage de Discord.')
        self.assertEqual(self.result['ok']['row'], 'Traduction active.')
        self.assertEqual(self.result['rescue']['row'], 'Mode de secours : Discord démarre sans la traduction.')
        self.assertEqual(self.result['restart']['row'], 'Redémarrage nécessaire : quittez complètement Discord, puis rouvrez-le.')
        self.assertIsNone(self.result['nothing']['row'])
        for name in ('vencord-error', 'ok', 'rescue', 'restart'):
            self.assertTrue(self.result[name]['chip'], name)  # a word, not only a colour

    def test_rescue_mode_and_diagnostic(self):
        self.assertTrue(self.result['rescue']['message'].startswith('Mode de secours : Discord démarre sans la traduction (depuis le '))
        self.assertEqual(self.result['vencord-error']['evidence'], ['Uncaught TypeError: i.A is not a constructor (uncaught)'])
        self.assertIn('Version de Discord1.0.168', self.result['vencord-error']['facts'][4] + self.result['vencord-error']['facts'][5])
        self.assertTrue(self.result['vencord-error']['help'].endswith('docs/fr/discord-demarrage.md'))

    def test_notification_button_opens_the_recovery_page(self):
        self.assertEqual(self.result['openedPage'], 'discord-recovery')


class TextTests(unittest.TestCase):
    def test_every_state_has_a_message_in_every_language(self):
        texts = all_texts()
        for language in ('co', 'fr', 'en'):
            for state in (*app.WATCH_STATES, 'none'):
                self.assertTrue(texts[language].get('dc_state_' + state.replace('-', '_')), (language, state))

    def test_corsican_texts_are_marked_as_ai_proposals(self):
        self.assertIn('The Corsican texts are AI proposals, not reviewed by a speaker yet',
                      (PAGE.parent / 'texts-discord.js').read_text(encoding='utf-8'))

    def test_page_files_are_served(self):
        for name in ('texts-discord.js', 'discord.js'):
            self.assertIn(name, app.STATIC)
            self.assertIn(f'<script src="{name}"></script>', PAGE.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
