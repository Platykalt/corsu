"""Discord start watch (src/discord_watch.py): classification from real Discord logs, one supervisor, notifications,
rescue mode and the Linux desktop-entry wrappers. Everything runs in a temporary home: no real Discord is touched."""
import io
import json
import os
from pathlib import Path
import sys
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import corsu
import discord_watch as watch
import installer
from tests.test_installer import Isolated
sys.path.insert(0, str(Path(__file__).resolve().parent / 'e2e'))
from check_discord_real_start import launcher_asar  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / 'fixtures/discord-watch'
SPLASH = ('[2026-11-08 10:00:00.000] [info]  splashScreenPreload: signalReady\n'
          '[2026-11-08 10:00:00.003] [info]  splashScreenPreload: onStateUpdate: {"status":"checking-for-updates"}\n')


def fixture(name):
    return (FIXTURES / name).read_text(encoding='utf-8')


def start_of(text):
    return watch.parse(text)[0]['t']


class Feed:
    """A log follower giving the whole excerpt at once, then nothing."""

    def __init__(self, text):
        self.text = text

    def read(self):
        text, self.text = self.text, ''
        return text


class Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class Watching(Isolated):
    def setUp(self):
        super().setUp()
        self.notified = []
        module = types.ModuleType('notify')
        module.notify = lambda title, body, action, incident: self.notified.append((action, incident)) or True
        patcher = patch.dict(sys.modules, {'notify': module})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_watch(self, text, alive=lambda: True, offscreen=lambda: None):
        started = start_of(text)
        clock = Clock(started + 1)
        record = watch.watch(Feed(text), alive, started, 'shortcut', None, clock=clock, sleep=clock.sleep,
                             check_offscreen=offscreen)
        return watch.alert(record), clock.now - started


class ClassifyTests(Watching):
    def test_normal_start_with_corsu_gives_no_alert(self):
        record, _ = self.run_watch(fixture('real-ok-corsu.log'))
        self.assertEqual(record['state'], 'ok-corsu')
        self.assertIsNone(record['incident'])
        self.assertEqual(record['app_version'], '1.0.168')
        self.assertEqual(self.notified, [])
        self.assertEqual(watch.read_state()['state'], 'ok-corsu')

    def test_login_page_counts_as_started(self):
        # A real isolated start without an account (Corsu starts only after login): the login page is the UI.
        record, _ = self.run_watch(fixture('isolated-new-vencord-login.log'))
        self.assertEqual(record['state'], 'ok')
        self.assertEqual(self.notified, [])

    def test_failure_before_corsu_loads_is_a_probable_vencord_error(self):
        for name in ('real-vencord-error.log', 'isolated-old-vencord.log'):
            self.notified.clear()
            record, waited = self.run_watch(fixture(name))
            self.assertEqual(record['state'], 'vencord-error', name)
            self.assertLess(waited, watch.WINDOW)  # decided at the error's grace period, not after the whole window
            self.assertEqual(self.notified, [('discord-recovery', record['incident'])])
            self.assertTrue(watch.read_state()['notified'])
            self.assertIn('uncaught', [item['kind'] for item in record['evidence']])

    def test_error_without_vencord_is_a_start_error(self):
        text = SPLASH + ('[2026-11-08 10:00:01.000] [info]  [default] [BUILD INFO] Release Channel: stable\n'
                         '[2026-11-08 10:00:02.000] [error] Uncaught TypeError: x is undefined\n')
        record, _ = self.run_watch(text)
        self.assertEqual(record['state'], 'start-error')

    def test_harmless_uncaught_errors_are_ignored(self):
        # NoTrack's "Sentry successfully disabled" and a taken RPC port appear in good real starts.
        entries = watch.parse(fixture('isolated-new-vencord-login.log'))
        self.assertNotIn('uncaught', [entry['kind'] for entry in entries])

    def test_stuck_but_alive_is_slow(self):
        record, waited = self.run_watch(SPLASH)
        self.assertEqual(record['state'], 'slow')
        self.assertGreaterEqual(waited, watch.WINDOW)
        self.assertEqual(len(self.notified), 1)

    def test_network_failure_is_network_never_vencord_error(self):
        record, _ = self.run_watch(fixture('real-update-failure.log'))
        self.assertEqual(record['state'], 'network')

    def test_page_that_cannot_load_is_network_not_an_error(self):
        # A real isolated start behind an unreachable proxy: Discord's preload fails on the error page and retries.
        record, waited = self.run_watch(fixture('isolated-offline.log'))
        self.assertEqual(record['state'], 'network')
        self.assertGreaterEqual(waited, watch.WINDOW)

    def test_voluntary_close_is_closed_without_alert(self):
        record, _ = self.run_watch(SPLASH, alive=lambda: False)
        self.assertEqual(record['state'], 'closed')
        self.assertEqual(self.notified, [])

    def test_updater_extends_the_window_once_and_a_restart_is_updating(self):
        text = SPLASH + '[2026-11-08 10:00:01.000] [info]  splashScreenPreload: onStateUpdate: {"status":"downloading-updates"}\n'
        record, waited = self.run_watch(text)
        self.assertEqual(record['state'], 'updating')
        self.assertGreaterEqual(waited, 2 * watch.WINDOW)
        record, waited = self.run_watch(text, alive=lambda: False)
        self.assertEqual(record['state'], 'updating')
        self.assertLess(waited, watch.WINDOW)
        self.assertEqual(self.notified, [])

    def test_window_outside_the_monitors_is_offscreen(self):
        record, _ = self.run_watch(fixture('real-ok-corsu.log'), offscreen=lambda: 'Discord window outside all monitors')
        self.assertEqual(record['state'], 'offscreen')
        self.assertEqual(len(self.notified), 1)
        monitors = [{'x': 0, 'y': 0, 'width': 1920, 'height': 1080, 'scale': 1}]
        self.assertIsNotNone(watch.outside([{'class': 'discord', 'at': [5000, 0], 'size': [800, 600]}], monitors))
        self.assertIsNone(watch.outside([{'class': 'discord', 'at': [100, 100], 'size': [800, 600]}], monitors))
        self.assertIsNone(watch.outside([], monitors))

    def test_evidence_is_short_redacted_and_bounded(self):
        lines = ''.join(f'[2026-11-08 10:00:{index:02d}.000] [info]  [GatewaySocket] [WS CLOSED] user me@example.com '
                        f'id 608936007278002177 token mfa.{"a" * 40} {"x" * 400}\n' for index in range(40))
        items = watch.evidence(watch.parse(SPLASH + lines))
        self.assertLessEqual(len(items), watch.EVIDENCE)
        text = json.dumps(items)
        for secret in ('me@example.com', '608936007278002177', 'a' * 40):
            self.assertNotIn(secret, text)
        self.assertTrue(all(len(item['line']) <= 300 for item in items))
        # Lines matching no known pattern (message content, names) are never kept.
        self.assertEqual(watch.parse('[2026-11-08 10:00:00.000] [info]  [MessageActionCreators] Fetched 11 messages\n'), [])

    def test_notifier_with_its_own_wording_gets_the_whole_record(self):
        records = []
        sys.modules['notify'].notify_incident = lambda record: records.append(record) or True
        record, _ = self.run_watch(SPLASH)
        self.assertEqual([item['incident'] for item in records], [record['incident']])
        self.assertEqual(self.notified, [])
        self.assertTrue(watch.read_state()['notified'])

    def test_dismiss_only_the_current_incident(self):
        record, _ = self.run_watch(SPLASH)
        self.assertFalse(watch.dismiss('another')['ok'])
        self.assertFalse(watch.read_state()['dismissed'])
        self.assertEqual(watch.dismiss(record['incident']), {'ok': True, 'reason': None})
        self.assertTrue(watch.read_state()['dismissed'])

    def test_post_hoc_scan_classifies_the_last_start_once(self):
        user_data = self.home / 'discord'
        (user_data / 'logs').mkdir(parents=True)
        (user_data / 'logs/renderer_js.log').write_text(fixture('real-ok-corsu.log') + fixture('real-vencord-error.log'))
        with patch.object(watch, 'client_folder', return_value=None):
            first = watch.scan_last_start(user_data, alive=False)
            self.assertEqual(first['state'], 'vencord-error')
            self.assertEqual(watch.scan_last_start(user_data, alive=False)['incident'], first['incident'])
        self.assertEqual(self.notified, [])  # the window shows it; the scan itself does not notify


class LaunchTests(Watching):
    def launch(self, running=False, command=('/usr/bin/discord', '--url', '--', 'discord://-/channels/1/2')):
        started = []

        class Process:
            def poll(self):
                return None
        with patch.object(watch, 'start', side_effect=lambda command: started.append(command) or Process()), \
             patch.object(watch, 'discord_running', return_value=running), \
             patch.object(watch, 'client_folder', return_value=None), \
             patch.object(watch, 'watch', return_value={'state': 'slow', 'incident': 'i1', 'notified': False}) as watcher:
            result = watch.launch(list(command), 'shortcut')
        return started, watcher, result

    def test_repeated_launch_has_one_supervisor_and_no_second_notification(self):
        lock = corsu.DATA / 'discord-watch/lock'
        lock.parent.mkdir(parents=True)
        lock.write_text(str(os.getppid()))  # another live watcher
        started, watcher, result = self.launch()
        self.assertEqual(len(started), 1)  # Discord still started, arguments untouched
        self.assertEqual(started[0][-1], 'discord://-/channels/1/2')
        watcher.assert_not_called()
        self.assertIsNone(result)
        self.assertEqual(self.notified, [])

    def test_a_failing_check_before_the_start_still_starts_discord(self):
        started = []
        with patch.object(watch, 'start', side_effect=lambda command: started.append(command)), \
             patch.object(watch, 'discord_running', side_effect=OSError('no process list')), \
             patch.object(watch, 'watch') as watcher:
            self.assertIsNone(watch.launch(['/usr/bin/discord', 'discord://-/channels/1/2'], 'shortcut'))
        self.assertEqual(started, [['/usr/bin/discord', 'discord://-/channels/1/2']])
        watcher.assert_not_called()

    def test_already_running_discord_is_not_watched(self):
        started, watcher, result = self.launch(running=True)
        self.assertEqual(len(started), 1)
        watcher.assert_not_called()
        self.assertEqual(watch.read_state()['state'], 'already-running')

    def test_stale_lock_is_taken_over_and_released(self):
        lock = corsu.DATA / 'discord-watch/lock'
        lock.parent.mkdir(parents=True)
        lock.write_text('999999999')
        started, watcher, result = self.launch()
        watcher.assert_called_once()
        self.assertEqual(watcher.call_args.args[3], 'url')
        self.assertFalse(lock.exists())

    def test_watcher_error_after_start_is_swallowed(self):
        with patch.object(watch, 'start') as start, patch.object(watch, 'discord_running', return_value=False), \
             patch.object(watch, 'client_folder', side_effect=RuntimeError('boom')):
            self.assertIsNone(watch.launch(['/usr/bin/discord']))
        start.assert_called_once_with(['/usr/bin/discord'])

    def test_command_line_keeps_discord_arguments(self):
        with patch.object(watch, 'launch') as launch:
            watch.main(['launch', '--from', 'autostart', '--', '/usr/bin/discord', '--url', '--', 'discord://x'])
        launch.assert_called_once_with(['/usr/bin/discord', '--url', '--', 'discord://x'], 'autostart')

    def test_windows_start_opens_no_console(self):
        with patch.object(watch.sys, 'platform', 'win32'), patch.object(watch.subprocess, 'Popen') as popen:
            watch.start(['Update.exe', '--processStart', 'Discord.exe'])
        self.assertTrue(popen.call_args.kwargs['creationflags'] & 0x08000000)

    def test_launch_without_arguments_starts_discord_the_platform_way(self):
        link = self.config / 'discord/Discord'
        link.parent.mkdir(parents=True)
        link.write_text('')
        with patch.object(watch.sys, 'platform', 'linux'), patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.config)}):
            self.assertEqual(watch.default_command(), [str(link)])
        with patch.object(watch.sys, 'platform', 'win32'), patch.dict(os.environ, {'LOCALAPPDATA': str(self.home)}):
            self.assertEqual(watch.default_command(), [str(self.home / 'Discord/Update.exe'), '--processStart', 'Discord.exe'])
        with patch.object(watch.sys, 'platform', 'darwin'):
            self.assertEqual(watch.default_command(), ['open', '-a', 'Discord'])
        with patch.object(watch, 'launch') as launch:
            watch.main(['launch', '--'])
        launch.assert_called_once_with(None, None)

    def test_user_data_folder_follows_the_channel(self):
        self.assertEqual(watch.user_data_dir(['/usr/bin/discord-ptb']).name, 'discordptb')
        self.assertEqual(watch.user_data_dir(['x', '--user-data-dir=/tmp/u']), Path('/tmp/u'))


class RescueTests(Isolated):
    def setUp(self):
        super().setUp()
        self.location = self.config / 'discord/app-1.0.168'
        resources = self.location / 'resources'
        resources.mkdir(parents=True)
        self.original = b'original discord archive' * 4000
        self.launcher = launcher_asar(self.home / 'Vencord/dist/patcher.js')
        (resources / '_app.asar').write_bytes(self.original)
        (resources / 'app.asar').write_bytes(self.launcher)
        self.app = resources / 'app.asar'
        record = corsu.Installer()
        record.external_file(self.app, self.original)
        record.state['files'][str(self.app)]['discord_location'] = str(self.location)
        corsu.save_state(record.state)
        watch.write_state({'version': 1, 'state': 'vencord-error', 'incident': 'i1', 'client': str(self.location),
                           'vencord': {'revision': '7f0c10cc'}})
        for name, value in (('discord_running', False),):
            patcher = patch.object(watch, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(installer, 'discord_archive', side_effect=lambda location: Path(location) / 'resources/app.asar')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_rescue_then_reactivate(self):
        result = watch.rescue('i1')
        self.assertTrue(result['ok'], result)
        self.assertEqual(self.app.read_bytes(), self.original)
        self.assertEqual(self.app.with_name('_app.asar').read_bytes(), self.original)  # Vencord's copy kept
        self.assertTrue(watch.in_rescue())
        self.assertEqual(json.loads((corsu.DATA / 'discord-watch/rescue.json').read_text())['from_revision'], '7f0c10cc')
        self.assertEqual(watch.read_state()['state'], 'rescue')
        # Repair and update go through install_discord: Discord is skipped, with the reason printed.
        output = io.StringIO()
        with patch.object(installer, 'vencord_installer') as official, redirect_stdout(output):
            installer.install_discord(self.location)
        official.assert_not_called()
        self.assertIn('rescue', output.getvalue())
        self.assertEqual(self.app.read_bytes(), self.original)

        def reinstall(location):
            self.assertFalse(watch.in_rescue())
            self.app.write_bytes(self.launcher)
        with patch.object(installer, 'install_discord', side_effect=reinstall), \
             patch.object(watch, 'launch', return_value={'state': 'ok-corsu', 'incident': None}):
            self.assertEqual(watch.reactivate(), {'ok': True, 'reason': None, 'state': 'ok-corsu'})
        self.assertFalse(watch.in_rescue())

    def test_failed_reactivation_goes_back_to_rescue(self):
        self.assertTrue(watch.rescue()['ok'])
        record = corsu.load_state()['files'][str(self.app)]

        def reinstall(location):
            self.app.write_bytes(self.launcher)
            state = corsu.load_state()
            state['files'][str(self.app)]['installed_sha256'] = corsu.digest(self.launcher)
            corsu.save_state(state)
        with patch.object(installer, 'install_discord', side_effect=reinstall), \
             patch.object(watch, 'launch', return_value={'state': 'vencord-error', 'incident': 'i2'}):
            result = watch.reactivate()
        self.assertFalse(result['ok'])
        self.assertTrue(result['rescue']['ok'], result)
        self.assertTrue(watch.in_rescue())
        self.assertEqual(self.app.read_bytes(), self.original)
        self.assertEqual(record['backup'], corsu.load_state()['files'][str(self.app)]['backup'])

    def test_rescue_never_closes_discord(self):
        with patch.object(watch, 'discord_running', return_value=True):
            self.assertEqual(watch.rescue()['reason'], 'running')
        self.assertEqual(self.app.read_bytes(), self.launcher)

    def test_invalid_backups_are_refused(self):
        state = corsu.load_state()
        backup = Path(state['files'][str(self.app)]['backup'])
        backup.write_bytes(self.launcher)
        self.assertEqual(watch.rescue()['reason'], 'launcher-backup')
        backup.unlink()
        self.assertEqual(watch.rescue()['reason'], 'backup-missing')
        backup.write_bytes(self.original)
        self.app.write_bytes(b'Discord updated itself' * 10)
        self.assertEqual(watch.rescue()['reason'], 'backup-mismatch')
        self.assertEqual(self.app.read_bytes(), b'Discord updated itself' * 10)
        self.assertFalse(watch.in_rescue())

    def test_other_discord_than_the_recorded_one_is_refused(self):
        watch.write_state({'state': 'vencord-error', 'client': str(self.config / 'discord/app-1.0.169')})
        self.assertEqual(watch.rescue()['reason'], 'unknown-app')

    def test_uninstall_in_rescue_restores_discord_and_forgets_the_watch(self):
        self.assertTrue(watch.rescue()['ok'])
        with redirect_stdout(io.StringIO()), patch.object(corsu, 'unlink_profiles'), \
             patch.object(corsu, 'repair_default_browser'):
            corsu.uninstall()
        self.assertEqual(self.app.read_bytes(), self.original)
        self.assertFalse(self.app.with_name('_app.asar').exists())
        self.assertFalse((corsu.DATA / 'discord-watch').exists())


@unittest.skipUnless(sys.platform.startswith("linux"), "the wrappers are desktop entries, Linux only")
class WrapperTests(Isolated):
    ENTRY = ('[Desktop Entry]\nName=Discord\nStartupWMClass=discord\nExec=/usr/bin/discord --url -- %u\nIcon=discord\n'
             'Type=Application\nMimeType=x-scheme-handler/discord;\n')

    def setUp(self):
        super().setUp()
        system = self.home / 'usr-share-applications'
        system.mkdir()
        (system / 'discord.desktop').write_text(self.ENTRY)
        patcher = patch.object(watch, 'SYSTEM_APPLICATIONS', system)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.menu = self.home / '.local/share/applications/discord.desktop'
        self.autostart = self.config / 'autostart/discord.desktop'
        self.autostart.parent.mkdir(parents=True)
        self.autostart.write_text(self.ENTRY.replace('--url -- %u', '--start-minimized'))
        self.python = self.home / 'python3'

    def test_wrappers_keep_the_entry_and_uninstall_removes_them(self):
        installer_state = corsu.Installer()
        watch.install_wrappers(installer_state, self.python)
        menu = self.menu.read_text()
        self.assertIn(f"Exec={self.python} {corsu.SRC / 'discord_watch.py'} launch --from shortcut -- /usr/bin/discord --url -- %u",
                      menu)
        self.assertIn('MimeType=x-scheme-handler/discord;', menu)
        self.assertIn('launch --from autostart -- /usr/bin/discord --start-minimized', self.autostart.read_text())
        # Installing again (a repair) never wraps the wrapper.
        watch.install_wrappers(corsu.Installer(), self.python)
        self.assertEqual(self.menu.read_text().count('discord_watch.py'), 1)
        with redirect_stdout(io.StringIO()), patch.object(corsu, 'unlink_profiles'), \
             patch.object(corsu, 'repair_default_browser'):
            corsu.uninstall()
        self.assertFalse(self.menu.exists())
        self.assertEqual(self.autostart.read_text(), self.ENTRY.replace('--url -- %u', '--start-minimized'))

    def test_switching_the_watch_off_removes_the_wrappers(self):
        state = corsu.Installer()
        watch.update_wrappers(state, self.python)
        self.assertTrue(self.menu.exists())
        import update
        update.set_preference('discord_watch', False)  # what `installer.py --discord-watch off` saves
        watch.update_wrappers(state, self.python)
        self.assertFalse(self.menu.exists())
        self.assertNotIn('discord_watch.py', self.autostart.read_text())
        self.assertFalse([name for name, record in corsu.load_state()['files'].items() if record.get('discord_watch')])

    def test_entry_rewritten_by_discord_is_wrapped_again_not_an_error(self):
        watch.install_wrappers(corsu.Installer(), self.python)
        self.autostart.write_text(self.ENTRY)  # Discord rewrote its autostart entry
        watch.install_wrappers(corsu.Installer(), self.python)
        self.assertIn('discord_watch.py', self.autostart.read_text())

    def test_launchers_follow_a_new_release(self):
        release = corsu.DATA / 'releases/0123456789abcdef'
        state = corsu.Installer()
        with patch.object(corsu, 'SRC', release / 'src'):
            watch.install_wrappers(state, self.python)
        corsu.refresh_launchers(state, root=corsu.DATA / 'releases/fedcba9876543210', python=self.home / 'python-new')
        text = self.menu.read_text()
        self.assertIn(f"Exec={self.home / 'python-new'} {corsu.DATA}/releases/fedcba9876543210/src/discord_watch.py launch", text)


if __name__ == '__main__':
    unittest.main()
