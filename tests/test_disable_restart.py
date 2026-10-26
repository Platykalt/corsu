"""Switching a part off: the real round-trip, and the restart hint only while it is needed.

The bug: after « Désactiver », a program that is already open keeps showing Corsican (Firefox keeps its interface
until it closes; the Vencord plugin stays loaded in Discord). Corsu used to flip the switch to off and say nothing
more, so the window showed the change as done while the open program was still in Corsican.

What is checked here:
- the functional round-trip in a throwaway folder: a part switched on returns to its earlier settings once switched
  off, and comes back on when switched on again (not only the hint in the window);
- the restart hint is conditional: shown only while the program is actually running, gone once it is not, and never
  shown for a program that was already closed;
- the disable/enable flip touches only the one Vencord setting Corsu owns, never the client's own data.

No real installation is touched and the installer is never started.
"""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import app
import corsu
import installer


PLUGIN = {'plugins/Corsu/enabled': True, 'autoUpdate': False, 'autoUpdateNotification': False}


class SnapshotRestart(unittest.TestCase):
    """The window asks for a restart only while the switched-off program is still open."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix='corsu-disable-'))
        self.data = self.folder / 'data'
        self.data.mkdir()
        self.processes = []
        patches = [patch.object(app.corsu, 'DATA', self.data), patch.object(app.corsu, 'STATE', self.data / 'installation.json'),
                   patch.object(app.corsu, 'HOME', self.folder / 'home'), patch.object(app, 'SESSION', self.data / 'setup-session.json'),
                   patch.dict(app.UPDATE, {'info': None, 'checking': False, 'auto_started': None, 'restart_error': None}),
                   patch.dict(app.RUNNING, {'time': 0.0, 'paths': None}),
                   patch.object(app, 'detected', return_value=set()),
                   patch.object(app.corsu, 'running_executables', side_effect=lambda: list(self.processes))]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(shutil.rmtree, self.folder, True)

    def write_state(self, components, disabled=(), everything_off=False):
        app.corsu.STATE.write_text(json.dumps({'files': {}, 'components': list(components), 'disabled': list(disabled)}),
                                   encoding='utf-8')
        if everything_off:
            app.corsu.disabled_marker().write_text('off\n', encoding='utf-8')

    def item(self, name):
        app.RUNNING['time'] = 0.0  # read the (mocked) process list afresh for this snapshot
        return next(item for item in app.snapshot()['items'] if item['name'] == name)

    def test_switched_off_and_still_open_asks_for_a_restart(self):
        # Reproduces the panne: Discord is off but still running, so the window must not present it as simply done.
        self.write_state(['discord'], disabled=['discord'])
        self.processes = ['/usr/bin/Discord']
        discord = self.item('discord')
        self.assertFalse(discord['on'])
        self.assertTrue(discord.get('restart'), 'a switched-off program still open must ask for a restart')

    def test_switched_off_but_closed_asks_for_nothing(self):
        # The conditional the user asked for: a program that was already closed raises no hint.
        self.write_state(['discord'], disabled=['discord'])
        self.processes = []
        self.assertFalse(self.item('discord').get('restart'))

    def test_the_hint_goes_away_once_the_program_has_restarted(self):
        self.write_state(['discord'], disabled=['discord'])
        self.processes = ['/usr/bin/Discord']
        self.assertTrue(self.item('discord').get('restart'))
        self.processes = []  # the person closed and reopened Discord: it is no longer the Corsican build
        self.assertFalse(self.item('discord').get('restart'))

    def test_a_part_left_on_asks_for_nothing(self):
        self.write_state(['discord'])
        self.processes = ['/usr/bin/Discord']
        self.assertFalse(self.item('discord').get('restart'))

    def test_firefox_hint_only_for_the_running_translated_copy(self):
        self.write_state(['firefox'], disabled=['firefox'])
        # The ordinary Firefox a switched-off launcher opens is not the copy: no hint.
        self.processes = ['/usr/lib/firefox/firefox']
        self.assertFalse(self.item('firefox').get('restart'))
        # The translated copy under DATA/firefox is still open: hint.
        self.processes = [str(self.data / 'firefox/128.0/firefox')]
        self.assertTrue(self.item('firefox').get('restart'))

    def test_unknown_process_list_shows_no_permanent_hint(self):
        self.write_state(['discord'], disabled=['discord'])
        with patch.object(app.corsu, 'running_executables', return_value=None):
            app.RUNNING['time'] = 0.0
            self.assertFalse(self.item('discord').get('restart'))

    def test_switch_everything_off_asks_only_the_running_programs(self):
        self.write_state(['firefox', 'discord'], everything_off=True)
        self.processes = ['/usr/bin/Discord']  # Discord open, Firefox copy closed
        self.assertTrue(self.item('discord').get('restart'))
        self.assertFalse(self.item('firefox').get('restart'))


class FunctionalRoundTrip(unittest.TestCase):
    """On → off → on with real files: the earlier settings come back, and nothing outside Corsu's one setting moves."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix='corsu-roundtrip-'))
        self.config = self.folder / 'config'
        self.settings = self.config / 'Vencord/settings/settings.json'
        self.settings.parent.mkdir(parents=True)
        # The person's own Vencord settings before Corsu, and a file standing for the client's own data store.
        self.original = {'autoUpdate': True, 'plugins': {'OtherPlugin': {'enabled': True}}, 'windowBounds': {'width': 1200}}
        self.settings.write_text(json.dumps(self.original), encoding='utf-8')
        self.store = self.config / 'Vencord/data/messages.sqlite'
        self.store.parent.mkdir(parents=True)
        self.store.write_bytes(b'draft and message data')
        patches = [patch.object(corsu, 'DATA', self.folder / 'data'), patch.object(corsu, 'STATE', self.folder / 'data/installation.json'),
                   patch.object(corsu, 'HOME', self.folder / 'home'), patch.object(corsu, 'CONFIG', self.config),
                   patch.object(corsu, 'PLATFORM', 'linux'),
                   # Switching Discord on re-runs install(); the parts that touch the desktop are not what this checks.
                   patch.object(corsu, 'desktop'), patch.object(corsu, 'refresh_launchers'), patch.object(corsu, 'repair_default_browser'),
                   patch.object(corsu, 'progress')]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        (self.folder / 'data').mkdir()
        self.addCleanup(shutil.rmtree, self.folder, True)

    def plugin_on(self):
        document = json.loads(self.settings.read_text(encoding='utf-8'))
        return document.get('plugins', {}).get('Corsu', {}).get('enabled')

    def activate(self):
        installer_ = corsu.Installer()
        installer_.json_settings(self.settings, dict(PLUGIN), toggle=True)
        installer_.state['components'] = ['discord']
        corsu.save_state(installer_.state)

    def test_on_off_on_restores_the_earlier_settings(self):
        self.activate()
        self.assertTrue(self.plugin_on())  # activée : le plugin traduit

        corsu.disable(['discord'])
        self.assertFalse(self.plugin_on())                       # désactivation : le plugin ne traduit plus
        self.assertTrue(corsu.is_disabled('discord'))
        restored = json.loads(self.settings.read_text(encoding='utf-8'))
        self.assertTrue(restored['autoUpdate'])                  # réglage antérieur revenu (Corsu l'avait mis à False)
        self.assertEqual(restored['windowBounds'], {'width': 1200})   # réglage personnel intact
        self.assertTrue(restored['plugins']['OtherPlugin']['enabled'])

        with patch.object(corsu, 'WORDS', {}):
            corsu.enable(['discord'])                            # relancement : on réactive
        self.assertTrue(self.plugin_on())
        self.assertFalse(corsu.is_disabled('discord'))

    def test_the_flip_never_touches_the_clients_own_data(self):
        self.activate()
        before = self.store.read_bytes()
        corsu.disable(['discord'])
        with patch.object(corsu, 'WORDS', {}):
            corsu.enable(['discord'])
        corsu.disable(['discord'])
        self.assertEqual(self.store.read_bytes(), before)        # messages/brouillons du client jamais touchés
        # The only Discord file Corsu records is the Vencord setting; nothing was written near the data store.
        files = json.loads(corsu.STATE.read_text(encoding='utf-8'))['files']
        self.assertTrue(all('messages.sqlite' not in name for name in files))


class KeepDisabledOnRepair(unittest.TestCase):
    """A repair, an update or a restart of Corsu re-runs the installer for the installed parts; the ones switched off
    must stay off. installer.keep_choices is what every such run passes through."""

    def test_repair_never_switches_a_disabled_part_back_on(self):
        state = {'components': ['firefox', 'discord'], 'disabled': ['discord']}
        with patch.object(corsu, 'disabled_marker') as marker:
            marker.return_value.exists.return_value = False
            kept, notes = installer.keep_choices(['firefox', 'discord'], ['firefox', 'discord'], None, state)
        self.assertEqual(kept, ['firefox'])
        self.assertTrue(any('discord' in note.lower() for note in notes))

    def test_everything_off_repairs_nothing(self):
        state = {'components': ['firefox', 'discord'], 'disabled': ['firefox', 'discord']}
        with patch.object(corsu, 'disabled_marker') as marker:
            marker.return_value.exists.return_value = True
            kept, _ = installer.keep_choices(['firefox', 'discord'], ['firefox', 'discord'], None, state)
        self.assertEqual(kept, [])


if __name__ == '__main__':
    unittest.main()
