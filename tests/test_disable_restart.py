"""Switching a part off and the restart it needs.

The bug: after « Désactiver », the programs already open keep showing Corsican (Firefox and Discord keep their
interface until they close; the Vencord plugin is still loaded). Corsu used to flip the switch to off and say nothing
more, so the window showed the change as done while the open program was still in Corsican. The window must name the
program and tell the person to restart it, whatever switched it off — a single switch, « switch everything off », or
reopening the window — so the displayed state matches the real effect.

Everything runs in a temporary data folder; no real installation is touched and the installer is never started.
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


class SnapshotRestart(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix='corsu-disable-'))
        self.data = self.folder / 'data'
        self.data.mkdir()
        patches = [patch.object(app.corsu, 'DATA', self.data), patch.object(app.corsu, 'STATE', self.data / 'installation.json'),
                   patch.object(app.corsu, 'HOME', self.folder / 'home'), patch.object(app, 'SESSION', self.data / 'setup-session.json'),
                   patch.dict(app.UPDATE, {'info': None, 'checking': False, 'auto_started': None, 'restart_error': None}),
                   patch.object(app, 'detected', return_value=set())]
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
        return next(item for item in app.snapshot()['items'] if item['name'] == name)

    def test_a_part_switched_off_asks_for_a_restart(self):
        # Reproduces the panne: Firefox is switched off but the window must not present it as simply done.
        self.write_state(['firefox'], disabled=['firefox'])
        firefox = self.item('firefox')
        self.assertFalse(firefox['on'])
        self.assertTrue(firefox.get('restart'), 'a switched-off part must ask for a restart')

    def test_a_part_left_on_asks_for_nothing(self):
        self.write_state(['firefox'])
        self.assertFalse(self.item('firefox').get('restart'))

    def test_switch_everything_off_asks_each_program_to_restart(self):
        # The big « Désactiver » sets the marker; every switchable part reads as off and asks for a restart.
        self.write_state(['firefox', 'discord'], everything_off=True)
        for name in ('firefox', 'discord'):
            self.assertFalse(self.item(name)['on'], name)
            self.assertTrue(self.item(name).get('restart'), name)


class KeepDisabledOnRepair(unittest.TestCase):
    """A repair, an update or a restart of Corsu re-runs the installer for the installed parts; the ones switched off
    must stay off. installer.keep_choices is what every such run passes through."""

    def test_repair_never_switches_a_disabled_part_back_on(self):
        state = {'components': ['firefox', 'discord'], 'disabled': ['discord']}
        with patch.object(corsu, 'disabled_marker') as marker:
            marker.return_value.exists.return_value = False  # no full-disable marker: only Discord is off
            kept, notes = installer.keep_choices(['firefox', 'discord'], ['firefox', 'discord'], None, state)
        self.assertEqual(kept, ['firefox'])
        self.assertTrue(any('discord' in note.lower() for note in notes))

    def test_everything_off_repairs_nothing(self):
        state = {'components': ['firefox', 'discord'], 'disabled': ['firefox', 'discord']}
        with patch.object(corsu, 'disabled_marker') as marker:
            marker.return_value.exists.return_value = True  # switched everything off
            kept, _ = installer.keep_choices(['firefox', 'discord'], ['firefox', 'discord'], None, state)
        self.assertEqual(kept, [])


if __name__ == '__main__':
    unittest.main()
