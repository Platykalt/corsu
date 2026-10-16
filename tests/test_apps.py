import io
import json
import os
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import corsu
import engine
import apps
from apps import settings, vlc


class IniTests(unittest.TestCase):
    def test_one_key_changes_and_the_rest_stays(self):
        text = '[Context]\nfoo=1\n\n[Environment]\nPATH=/x\n'
        changed = settings.ini_set(text, 'Environment', 'LANGUAGE', 'co:fr')
        self.assertEqual(changed, '[Context]\nfoo=1\n\n[Environment]\nPATH=/x\nLANGUAGE=co:fr\n')
        self.assertEqual(settings.ini_set(changed, 'Environment', 'LANGUAGE', None), text)
        self.assertEqual(settings.ini_set('', 'Environment', 'LANGUAGE', 'co'), '[Environment]\nLANGUAGE=co\n')
        self.assertEqual(settings.ini_set('[A]\r\nk=1\r\n', 'A', 'k', '2', '\r\n'), '[A]\r\nk=2\r\n')


class VLCTests(unittest.TestCase):
    """VLC on Linux: the menu entry starts it with Corsican first, only where its Corsican catalogue exists."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / 'casa è spaziu'
        self.system = self.root / 'usr'
        (self.system / 'applications').mkdir(parents=True)
        (self.system / 'applications/vlc.desktop').write_text(
            '[Desktop Entry]\nName=VLC media player\nExec=/usr/bin/vlc --started-from-file %U\nTryExec=/usr/bin/vlc\n'
            '\n[Desktop Action play]\nExec=/usr/bin/vlc --play %U\n')
        self.locale = self.root / 'locale'
        for language in ('co', 'fr'):
            folder = self.locale / language / 'LC_MESSAGES'
            folder.mkdir(parents=True)
            entries = {b'': b'Content-Type: text/plain; charset=UTF-8\n', b'Open': b'Apre', b'Play': b'Sun\xc3\xa0'}
            if language == 'fr':
                entries[b'Stop'] = b'Arr\xc3\xaat'
            (folder / 'vlc.mo').write_bytes(engine.make_mo(entries))
        self.stack = ExitStack()
        for target, name, value in ((corsu, 'HOME', self.root), (corsu, 'DATA', self.root / 'data'),
                                    (corsu, 'STATE', self.root / 'data/state.json'), (corsu, 'PLATFORM', 'linux'),
                                    (apps, 'APPLICATION_DIRS', (self.system / 'applications',)),
                                    (apps, 'FLATPAK_SYSTEM', self.root / 'flatpak'), (vlc, 'LOCALE', self.locale),
                                    (vlc, 'SNAP', self.root / 'snap/vlc'), (apps.shutil, 'which', lambda name: '/usr/bin/vlc'),
                                    (vlc, 'version', lambda executable: '3.0.21')):
            self.stack.enter_context(patch.object(target, name, value))
        self.stack.enter_context(patch.dict(os.environ, {'LANGUAGE': '', 'LC_ALL': '', 'LC_MESSAGES': '', 'LANG': 'fr_FR.UTF-8'}))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def tearDown(self):
        self.stack.close()
        self.directory.cleanup()

    def install(self):
        installer = corsu.Installer()
        report = apps.install(installer, 'vlc')
        installer.state['components'] = ['vlc']
        corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
        return report

    def test_menu_entry_starts_vlc_in_corsican_and_switches_back(self):
        [installation] = vlc.VLC().find()
        self.assertEqual(installation.coverage, '2/3')
        report = self.install()
        self.install()
        entry = self.root / '.local/share/applications/vlc.desktop'
        text = entry.read_text()
        self.assertIn('Exec=env LANGUAGE=co:fr_FR /usr/bin/vlc --started-from-file %U', text)
        self.assertIn('Exec=env LANGUAGE=co:fr_FR /usr/bin/vlc --play %U', text)
        self.assertEqual(text.count('LANGUAGE='), 2)
        self.assertEqual(len(report['installed']), 1)
        corsu.disable(['vlc'])
        self.assertFalse(entry.exists())
        corsu.install(['vlc'])
        self.assertTrue(entry.exists())
        corsu.uninstall()
        self.assertFalse(entry.exists())

    def test_without_the_corsican_catalogue_nothing_changes(self):
        (self.locale / 'co/LC_MESSAGES/vlc.mo').unlink()
        report = self.install()
        self.assertFalse((self.root / '.local/share/applications/vlc.desktop').exists())
        self.assertEqual(len(report['skipped']), 1)

    def test_a_menu_entry_of_your_own_is_left_alone(self):
        own = self.root / '.local/share/applications/vlc.desktop'
        own.parent.mkdir(parents=True)
        own.write_text('[Desktop Entry]\nExec=vlc --my-options\n')
        self.install()
        self.assertEqual(own.read_text(), '[Desktop Entry]\nExec=vlc --my-options\n')

    def test_flatpak_override_keeps_your_other_settings(self):
        with patch.object(apps.shutil, 'which', lambda name: None):
            base = self.root / '.local/share/flatpak'
            catalog = base / 'runtime/org.videolan.VLC.Locale/x86_64/stable/abc/files/co/share/co/LC_MESSAGES/vlc.mo'
            catalog.parent.mkdir(parents=True)
            catalog.write_bytes((self.locale / 'co/LC_MESSAGES/vlc.mo').read_bytes())
            (base / 'app/org.videolan.VLC').mkdir(parents=True)
            override = base / 'overrides/org.videolan.VLC'
            override.parent.mkdir(parents=True)
            override.write_text('[Context]\nfilesystems=home;\n')
            self.install()
            self.assertIn('[Environment]\nLANGUAGE=co:fr_FR\n', override.read_text())
            # Something else written to the file since stays.
            override.write_text(override.read_text().replace('home;', 'home;xdg-music;'))
            corsu.disable(['vlc'])
            self.assertEqual(override.read_text(), '[Context]\nfilesystems=home;xdg-music;\n')


if __name__ == '__main__':
    unittest.main()
