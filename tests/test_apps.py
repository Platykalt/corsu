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


class WindowsProgramsTests(unittest.TestCase):
    """Programs with a language setting of their own, on simulated Windows folders and registry."""

    def setUp(self):
        from apps import programs
        self.programs = programs
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / 'Utilizatore è spaziu'
        self.files = self.root / 'Program Files'
        self.registry = {}
        self.stack = ExitStack()
        for target, name, value in ((corsu, 'HOME', self.root), (corsu, 'DATA', self.root / 'data'),
                                    (corsu, 'STATE', self.root / 'data/state.json'), (corsu, 'PLATFORM', 'windows'),
                                    (corsu, 'running_executables', lambda: self.running),
                                    (settings, 'registry_get', lambda key, name: self.registry.get((key, name))),
                                    (settings, 'registry_set', self.registry_set)):
            self.stack.enter_context(patch.object(target, name, value))
        self.stack.enter_context(patch.dict(os.environ, {'ProgramFiles': str(self.files), 'ProgramFiles(x86)': '',
                                                         'ProgramW6432': '', 'APPDATA': str(self.root / 'Roaming'),
                                                         'LOCALAPPDATA': str(self.root / 'Local')}))
        self.stack.enter_context(redirect_stdout(io.StringIO()))
        self.running = set()

    def registry_set(self, key, name, value):
        if value is None:
            self.registry.pop((key, name), None)
        else:
            self.registry[(key, name)] = tuple(value)

    def tearDown(self):
        self.stack.close()
        self.directory.cleanup()

    def make(self, *paths):
        for path in paths:
            target = self.files / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('x')

    def run_install(self, app_id):
        installer = corsu.Installer()
        report = apps.install(installer, app_id)
        installer.state['components'] = [app_id]
        corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
        return report

    def test_registry_programs_switch_and_give_back_a_value_changed_since(self):
        self.make('7-Zip/7zFM.exe', '7-Zip/Lang/co.txt', 'VideoLAN/VLC/vlc.exe', 'VideoLAN/VLC/locale/co/LC_MESSAGES/vlc.mo')
        self.registry[(r'Software\7-Zip', 'Lang')] = ('fr', 1)
        self.run_install('7zip')
        self.run_install('7zip')
        self.assertEqual(self.registry[(r'Software\7-Zip', 'Lang')], ('co', 1))
        corsu.disable(['7zip'])
        self.assertEqual(self.registry[(r'Software\7-Zip', 'Lang')], ('fr', 1))
        self.run_install('vlc')
        self.assertEqual(self.registry[(r'Software\VideoLAN\VLC', 'Lang')], ('co', 1))
        # The person picks English in VLC afterwards: uninstalling must not undo that.
        self.registry[(r'Software\VideoLAN\VLC', 'Lang')] = ('en', 1)
        corsu.uninstall()
        self.assertEqual(self.registry[(r'Software\VideoLAN\VLC', 'Lang')], ('en', 1))

    def test_program_without_its_corsican_file_is_left_alone(self):
        self.make('7-Zip/7zFM.exe')
        report = self.run_install('7zip')
        self.assertEqual(self.registry, {})
        self.assertEqual(len(report['skipped']), 1)

    def test_notepad_plus_plus_keeps_the_previous_language_file(self):
        self.make('Notepad++/notepad++.exe')
        corsican = self.files / 'Notepad++/localization/corsican.xml'
        corsican.parent.mkdir(parents=True)
        corsican.write_text('<NotepadPlus><Native-Langue name="Corsu"/></NotepadPlus>')
        previous = self.root / 'Roaming/Notepad++/nativeLang.xml'
        previous.parent.mkdir(parents=True)
        previous.write_text('<NotepadPlus><Native-Langue name="Français"/></NotepadPlus>')
        self.run_install('notepadpp')
        self.assertIn('Corsu', previous.read_text())
        corsu.disable(['notepadpp'])
        self.assertIn('Français', previous.read_text())

    def test_settings_files_open_program_and_missing_file(self):
        self.make('FileZilla FTP Client/filezilla.exe', 'FileZilla FTP Client/locales/co/filezilla.mo',
                  'SumatraPDF/SumatraPDF.exe', 'VeraCrypt/VeraCrypt.exe', 'VeraCrypt/Languages/Language.co.xml')
        report = self.run_install('filezilla')
        self.assertEqual(len(report['skipped']), 1)  # never started: no filezilla.xml to change
        config = self.root / 'Roaming/FileZilla/filezilla.xml'
        config.parent.mkdir(parents=True)
        original = '<FileZilla3>\n\t<Settings>\n\t\t<Setting name="Ascii Binary mode">0</Setting>\n\t</Settings>\n</FileZilla3>\n'
        config.write_text(original)
        self.running = {r'C:\Program Files\FileZilla FTP Client\filezilla.exe'}
        self.run_install('filezilla')
        self.assertEqual(config.read_text(), original)  # open: it would write its settings back when quitting
        self.running = set()
        self.run_install('filezilla')
        self.assertIn('<Setting name="Language Code">co</Setting>', config.read_text())
        corsu.disable(['filezilla'])
        self.assertEqual(config.read_text(), original)
        sumatra = self.root / 'Local/SumatraPDF/SumatraPDF-settings.txt'
        sumatra.parent.mkdir(parents=True)
        sumatra.write_text('UiLanguage = fr\nShowToolbar = true\n')
        self.run_install('sumatrapdf')
        self.assertEqual(sumatra.read_text(), 'UiLanguage = co\nShowToolbar = true\n')
        corsu.disable(['sumatrapdf'])
        self.assertEqual(sumatra.read_text(), 'UiLanguage = fr\nShowToolbar = true\n')
        broken = self.root / 'Roaming/VeraCrypt/Configuration.xml'
        broken.parent.mkdir(parents=True)
        broken.write_text('<VeraCrypt><configuration>')
        report = self.run_install('veracrypt')
        self.assertEqual(broken.read_text(), '<VeraCrypt><configuration>')  # malformed: never rewritten
        self.assertEqual(len(report['skipped']), 1)

    def test_notepad_plus_plus_without_its_language_folder_gets_the_official_file(self):
        self.make('Notepad++/notepad++.exe')
        official = b'<NotepadPlus><Native-Langue name="Corsu"/></NotepadPlus>'
        with patch.object(self.programs.NotepadPlusPlus, 'official_file', lambda app, executable: (official, 'v8.9.8')):
            self.run_install('notepadpp')
        native = self.root / 'Roaming/Notepad++/nativeLang.xml'
        self.assertEqual(native.read_bytes(), official)
        corsu.disable(['notepadpp'])
        self.assertFalse(native.exists())


class SettingsIntegrityTests(WindowsProgramsTests):
    """What happens to the person's own files and choices around Corsu's single setting."""

    def test_windows_files_keep_their_line_endings_and_byte_order_mark(self):
        self.make('SumatraPDF/SumatraPDF.exe', 'HandBrake/HandBrake.exe')
        sumatra = self.root / 'Local/SumatraPDF/SumatraPDF-settings.txt'
        sumatra.parent.mkdir(parents=True)
        original = '\ufeffUiLanguage = fr\r\nShowToolbar = true\r\n'.encode('utf-8')
        sumatra.write_bytes(original)
        self.run_install('sumatrapdf')
        self.assertEqual(sumatra.read_bytes(), '\ufeffUiLanguage = co\r\nShowToolbar = true\r\n'.encode('utf-8'))
        corsu.disable(['sumatrapdf'])
        self.assertEqual(sumatra.read_bytes(), original)
        handbrake = self.root / 'Roaming/HandBrake/settings.json'
        handbrake.parent.mkdir(parents=True)
        original = '\ufeff{\r\n  "UpdateStatus": true\r\n}\r\n'.encode('utf-8')
        handbrake.write_bytes(original)
        report = self.run_install('handbrake')
        self.assertEqual(report['skipped'], [])
        self.assertTrue(handbrake.read_bytes().startswith('\ufeff{\r\n'.encode('utf-8')))
        self.assertNotIn(b'\n', handbrake.read_bytes().replace(b'\r\n', b''))
        self.assertEqual(json.loads(handbrake.read_bytes().decode('utf-8-sig'))['UiLanguage'], 'co')
        corsu.disable(['handbrake'])
        self.assertEqual(handbrake.read_bytes(), original)

    def test_program_open_when_switched_off_stays_on_until_it_is_closed(self):
        self.make('FileZilla FTP Client/filezilla.exe', 'FileZilla FTP Client/locales/co/filezilla.mo')
        config = self.root / 'Roaming/FileZilla/filezilla.xml'
        config.parent.mkdir(parents=True)
        original = '<FileZilla3>\n\t<Settings>\n\t</Settings>\n</FileZilla3>\n'
        config.write_text(original)
        self.run_install('filezilla')
        self.running = {r'C:\Program Files\FileZilla FTP Client\filezilla.exe'}
        output = io.StringIO()
        with redirect_stdout(output):
            corsu.disable(['filezilla'])
        # FileZilla writes its settings back when it quits: reverting now would be undone and then forgotten.
        self.assertIn('<Setting name="Language Code">co</Setting>', config.read_text())
        self.assertFalse(corsu.is_disabled('filezilla'))
        self.assertIn('FileZilla', output.getvalue())
        self.running = set()
        corsu.disable(['filezilla'])
        self.assertEqual(config.read_text(), original)
        self.assertTrue(corsu.is_disabled('filezilla'))

    def test_language_chosen_in_notepad_plus_plus_is_kept_when_corsu_runs_again(self):
        self.make('Notepad++/notepad++.exe')
        corsican = self.files / 'Notepad++/localization/corsican.xml'
        corsican.parent.mkdir(parents=True)
        corsican.write_text('<NotepadPlus><Native-Langue name="Corsu"/></NotepadPlus>')
        self.run_install('notepadpp')
        native = self.root / 'Roaming/Notepad++/nativeLang.xml'
        native.write_text('<NotepadPlus><Native-Langue name="English"/></NotepadPlus>')
        report = self.run_install('notepadpp')  # used to stop the whole installation with a RuntimeError
        self.assertIn('English', native.read_text())
        self.assertEqual(len(report['skipped']), 1)

    def test_summary_names_only_programs_actually_switched(self):
        self.make('7-Zip/7zFM.exe', 'WinMerge/WinMergeU.exe', 'WinMerge/Languages/Corsican.po')
        output = io.StringIO()
        with redirect_stdout(output), patch.object(corsu, 'ROOT', self.root / 'checkout'):
            corsu.install(['7zip', 'winmerge'])
        text = output.getvalue()
        self.assertIn('Installed: WinMerge', text)
        self.assertNotIn('7-Zip', text.split('Installed:')[1].splitlines()[0])
        self.assertIn('Not switched to Corsican (see the reasons above): 7-Zip', text)
        self.assertEqual(corsu.load_state()['components'], ['winmerge'])
