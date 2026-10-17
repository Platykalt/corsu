"""Audacity, Tenacity and fre:ac on simulated folders (no real program runs here): one setting switched, everything
else in the file kept, given back only while it still holds Corsu's value."""
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
from apps import audacity, freac, settings

MO = {b'': b'Content-Type: text/plain; charset=UTF-8\n', b'Open': b'Apre', b'Play': b'Sun\xc3\xa0'}


def write_mo(path, extra=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = dict(MO)
    if extra:
        entries[b'Stop'] = b'Arr\xc3\xaat'
    path.write_bytes(engine.make_mo(entries))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode('utf-8')
    path.write_bytes(data)
    return data


AUDACITY_CFG = ('PrefsVersion=1.1.1r1\n[GUI]\nTheme=dark\n[Version]\nMajor=3\nMinor=7\n'
                '[Locale]\nLanguage=fr\n[AudioIO]\nRecordingDevice=Mic\n')
AUDACITY4_INI = ('[General]\nExporters="PCM,MP3"\nSendAnonymousUsageInfo=false\n\n'
                 '[application]\nlastUpdateCheckRequestDay=2026-10-16\n')
# What smooth's libxml2 writer produces (indent of one space per level).
FREAC_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n<ConfigFile>\n <configuration name="default">\n'
             '  <section name="Settings">\n   <value name="WindowPosX">10</value>\n'
             '   <value name="Language">freac_fr.xml</value>\n   <value name="StartCount">3</value>\n  </section>\n'
             '  <section name="Ripper">\n   <value name="Language">ignored</value>\n  </section>\n'
             ' </configuration>\n</ConfigFile>\n')


class AudioAppsTests(unittest.TestCase):
    platform = 'linux'

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / 'casa è spaziu'
        self.files = self.root / 'Program Files'
        self.locale = self.root / 'usr/share/locale'
        self.share = self.root / 'usr/share'
        self.running = set()
        self.defaults = {}
        self.which = {}
        known = {app.id: app for app in (audacity.Audacity(), audacity.Tenacity(), freac.Freac())}
        self.stack = ExitStack()
        for target, name, value in (
                (corsu, 'HOME', self.root), (corsu, 'DATA', self.root / 'data'),
                (corsu, 'STATE', self.root / 'data/state.json'), (corsu, 'PLATFORM', self.platform),
                (corsu, 'running_executables', lambda: self.running),
                (apps, 'registry', lambda: known), (apps, 'FLATPAK_SYSTEM', self.root / 'flatpak'),
                (apps.shutil, 'which', lambda name: self.which.get(name)),
                (audacity, 'LOCALE', self.locale), (audacity, 'SHARE', self.share),
                (audacity, 'APPLICATIONS', (self.root / 'Applications',)),
                (freac, 'SHARE', self.share), (freac, 'APPLICATIONS', (self.root / 'Applications',)),
                (settings, 'defaults_get', lambda domain, key: self.defaults.get((domain, key))),
                (settings, 'defaults_put', self.defaults_put)):
            self.stack.enter_context(patch.object(target, name, value))
        self.stack.enter_context(patch.dict(os.environ, {
            'XDG_CONFIG_HOME': '', 'ProgramFiles': str(self.files), 'ProgramFiles(x86)': '', 'ProgramW6432': '',
            'APPDATA': str(self.root / 'Roaming'), 'LOCALAPPDATA': str(self.root / 'Local')}))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def defaults_put(self, domain, key, value):
        if value is None:
            self.defaults.pop((domain, key), None)
        else:
            self.defaults[(domain, key)] = value

    def tearDown(self):
        self.stack.close()
        self.directory.cleanup()

    def run_install(self, app_id):
        installer = corsu.Installer()
        report = apps.install(installer, app_id)
        installer.state['components'] = [app_id]
        corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
        return report

    def system_audacity(self):
        self.which['audacity'] = '/usr/bin/audacity'
        write_mo(self.locale / 'co/LC_MESSAGES/audacity.mo')
        write_mo(self.locale / 'fr/LC_MESSAGES/audacity.mo', extra=True)


class LinuxTests(AudioAppsTests):
    def test_audacity_3_switches_one_setting_and_gives_it_back(self):
        self.system_audacity()
        config = self.root / '.config/audacity/audacity.cfg'
        original = write(config, AUDACITY_CFG)
        [installation] = audacity.Audacity().find()
        self.assertEqual((installation.coverage, installation.version, installation.reason), ('2/3', '3.x', None))
        report = self.run_install('audacity')
        self.run_install('audacity')  # a second run changes nothing more and keeps the first original
        self.assertEqual(len(report['installed']), 1)
        self.assertEqual(config.read_bytes(), original.replace(b'Language=fr', b'Language=co'))
        corsu.disable(['audacity'])
        self.assertEqual(config.read_bytes(), original)

    def test_audacity_without_language_gets_a_locale_section_then_loses_it(self):
        self.system_audacity()
        config = self.root / '.config/audacity/audacity.cfg'
        original = write(config, 'PrefsVersion=1.1.1r1\n[GUI]\nTheme=dark\n')
        self.run_install('audacity')
        self.assertEqual(config.read_text(), 'PrefsVersion=1.1.1r1\n[GUI]\nTheme=dark\n\n[Locale]\nLanguage=co\n')
        corsu.uninstall()
        self.assertEqual(config.read_bytes(), original)

    def test_audacity_uses_its_legacy_folder_when_it_exists_and_xdg_otherwise(self):
        self.system_audacity()
        legacy = self.root / '.audacity-data/audacity.cfg'
        write(legacy, AUDACITY_CFG)
        modern = self.root / '.config/audacity/audacity.cfg'
        write(modern, AUDACITY_CFG)
        self.run_install('audacity')
        self.assertIn('Language=co', legacy.read_text())
        self.assertEqual(modern.read_text(), AUDACITY_CFG)
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.root / 'xdg')}):
            self.assertEqual(audacity.Audacity().linux_settings(), legacy)
            legacy.unlink()
            legacy.parent.rmdir()
            self.assertEqual(audacity.Audacity().linux_settings(), self.root / 'xdg/audacity/audacity.cfg')

    def test_left_alone_without_catalogue_settings_file_or_while_open(self):
        self.which['audacity'] = '/usr/bin/audacity'
        report = self.run_install('audacity')
        self.assertEqual(len(report['skipped']), 1)  # no Corsican catalogue
        self.assertIn('Reinstall Audacity', report['skipped'][0]['action'])  # what the window says to do next
        self.system_audacity()
        report = self.run_install('audacity')
        self.assertIn('once', report['skipped'][0]['reason'])
        self.assertIn('Start Audacity once', report['skipped'][0]['action'])
        self.assertFalse((self.root / '.config/audacity/audacity.cfg').exists())  # never invented
        config = self.root / '.config/audacity/audacity.cfg'
        write(config, AUDACITY_CFG)
        self.running = {'/usr/bin/audacity'}
        report = self.run_install('audacity')
        self.assertEqual(config.read_text(), AUDACITY_CFG)
        self.assertIn('Audacity', report['skipped'][0]['reason'])
        self.assertIn('Close Audacity', report['skipped'][0]['action'])

    def test_value_changed_since_and_malformed_file_are_kept(self):
        self.system_audacity()
        config = self.root / '.config/audacity/audacity.cfg'
        write(config, AUDACITY_CFG)
        self.run_install('audacity')
        config.write_text(config.read_text().replace('Language=co', 'Language=en'))
        corsu.disable(['audacity'])
        self.assertIn('Language=en', config.read_text())
        broken = b'[Locale]\nLanguage=fr\n\xff\xfe\n'
        config.write_bytes(broken)
        report = self.run_install('audacity')
        self.assertEqual(config.read_bytes(), broken)
        self.assertEqual(len(report['skipped']), 1)

    def test_audacity_flatpak_with_and_without_corsican_in_its_languages(self):
        base = self.root / '.local/share/flatpak'
        (base / 'app/org.audacityteam.Audacity/x86_64/stable/abc/files').mkdir(parents=True)
        report = self.run_install('audacity')
        self.assertIn('extra-languages', report['skipped'][0]['reason'])
        write_mo(base / 'runtime/org.audacityteam.Audacity.Locale/x86_64/stable/abc/files/co/share/co/LC_MESSAGES/audacity.mo')
        config = self.root / '.var/app/org.audacityteam.Audacity/config/audacity/audacity.cfg'
        original = write(config, AUDACITY_CFG)
        report = self.run_install('audacity')
        self.assertEqual(report['skipped'], [])
        self.assertIn('Language=co', config.read_text())
        corsu.disable(['audacity'])
        self.assertEqual(config.read_bytes(), original)

    def test_audacity_4_system_install_uses_its_qt_settings(self):
        self.which['audacity'] = '/usr/bin/audacity'
        write(self.share / 'audacity-4.0/locale/audacity_co.qm', b'qm')
        ini = self.root / '.config/Audacity/Audacity4.ini'
        original = write(ini, AUDACITY4_INI)
        [installation] = audacity.Audacity().find()
        self.assertEqual((installation.version, installation.reason), ('4.x', None))
        self.run_install('audacity')
        self.assertEqual(ini.read_text(), AUDACITY4_INI.replace('false\n\n', 'false\nlanguage=co\n\n'))
        corsu.disable(['audacity'])
        self.assertEqual(ini.read_bytes(), original)

    def test_tenacity_system_and_flatpak(self):
        self.which['tenacity'] = '/usr/bin/tenacity'
        write_mo(self.locale / 'co/LC_MESSAGES/tenacity.mo')
        config = self.root / '.config/tenacity/tenacity.cfg'
        original = write(config, AUDACITY_CFG)
        base = self.root / '.local/share/flatpak'
        (base / 'app/org.tenacityaudio.Tenacity').mkdir(parents=True)
        write_mo(base / 'runtime/org.tenacityaudio.Tenacity.Locale/x86_64/stable/abc/files/co/share/co/LC_MESSAGES/tenacity.mo')
        flatpak_config = self.root / '.var/app/org.tenacityaudio.Tenacity/config/tenacity/tenacity.cfg'
        report = self.run_install('tenacity')
        self.assertEqual(len(report['installed']), 1)
        self.assertIn('once', report['skipped'][0]['reason'])  # the Flatpak was never started
        self.assertIn('Language=co', config.read_text())
        write(flatpak_config, AUDACITY_CFG)
        self.run_install('tenacity')
        self.assertIn('Language=co', flatpak_config.read_text())
        corsu.disable(['tenacity'])
        self.assertEqual(config.read_bytes(), original)
        self.assertEqual(flatpak_config.read_text(), AUDACITY_CFG)

    def test_freac_linux_settings_location(self):
        self.assertEqual(freac.linux_settings(), self.root / '.config/freac/freac.xml')
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.root / '.config')}):
            self.assertEqual(freac.linux_settings(), self.root / '.config/freac/freac.xml')
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.root / '.var/app/org.freac.freac/config')}):
            self.assertEqual(freac.linux_settings(), self.root / '.var/app/org.freac.freac/config/.freac/freac.xml')

    def test_freac_system_package_and_unverified_flatpak(self):
        self.which['freac'] = str(self.root / 'usr/bin/freac')
        write(self.root / 'usr/bin/freac', b'')
        lang = self.share / 'freac/lang'
        write(lang / 'freac_co.xml', '<LangFile><data><entry id="1" string="OK">Vai</entry></data></LangFile>')
        write(lang / 'freac.xml', '<LangFile><data><entry id="1" string="OK">OK</entry>'
                                  '<entry id="2" string="Cancel">Cancel</entry></data></LangFile>')
        config = self.root / '.config/freac/freac.xml'
        original = write(config, FREAC_XML)
        (self.root / '.local/share/flatpak/app/org.freac.freac').mkdir(parents=True)
        installations = freac.Freac().find()
        self.assertEqual([item.coverage for item in installations], ['1/2', None])
        report = self.run_install('freac')
        self.assertEqual(len(report['installed']), 1)
        self.assertIn('Flatpak', report['skipped'][0]['kind'])
        self.assertIn('<value name="Language">freac_co.xml</value>', config.read_text())
        self.assertIn('<value name="Language">ignored</value>', config.read_text())
        corsu.disable(['freac'])
        self.assertEqual(config.read_bytes(), original)


class WindowsTests(AudioAppsTests):
    platform = 'windows'

    def make(self, *paths):
        for path in paths:
            write(self.files / path, b'x')

    def test_audacity_3_keeps_line_endings_and_byte_order_mark(self):
        self.make('Audacity/Audacity.exe')
        write_mo(self.files / 'Audacity/Languages/co/audacity.mo')
        write_mo(self.files / 'Audacity/Languages/fr/audacity.mo', extra=True)
        config = self.root / 'Roaming/audacity/audacity.cfg'
        original = write(config, '\ufeff' + AUDACITY_CFG.replace('\n', '\r\n'))
        [installation] = audacity.Audacity().find()
        self.assertEqual(installation.coverage, '2/3')
        self.run_install('audacity')
        self.assertEqual(config.read_bytes(), original.replace(b'Language=fr', b'Language=co'))
        corsu.disable(['audacity'])
        self.assertEqual(config.read_bytes(), original)

    def test_audacity_portable_or_just_installed_is_left_alone(self):
        self.make('Audacity/Audacity.exe', 'Audacity/FirstTime.ini')
        write_mo(self.files / 'Audacity/Languages/co/audacity.mo')
        config = self.root / 'Roaming/audacity/audacity.cfg'
        write(config, AUDACITY_CFG)
        report = self.run_install('audacity')
        self.assertIn('installed or updated', report['skipped'][0]['reason'])
        self.assertEqual(config.read_text(), AUDACITY_CFG)
        (self.files / 'Audacity/FirstTime.ini').unlink()
        (self.files / 'Audacity/Portable Settings').mkdir()
        report = self.run_install('audacity')
        self.assertIn('Portable Settings', report['skipped'][0]['reason'])
        self.assertEqual(config.read_text(), AUDACITY_CFG)

    def test_audacity_3_and_4_side_by_side(self):
        self.make('Audacity/Audacity.exe', 'Audacity 4/bin/Audacity4.exe', 'Audacity 4/locale/audacity_co.qm')
        write_mo(self.files / 'Audacity/Languages/co/audacity.mo')
        config = self.root / 'Roaming/audacity/audacity.cfg'
        write(config, AUDACITY_CFG)
        ini = self.root / 'Roaming/Audacity/Audacity4.ini'
        original = write(ini, AUDACITY4_INI.replace('\n', '\r\n'))
        installations = audacity.Audacity().find()
        self.assertEqual([item.version for item in installations], ['3.x', '4.x'])
        self.running = {r'C:\Program Files\Audacity 4\bin\Audacity4.exe'}
        report = self.run_install('audacity')
        self.assertEqual(len(report['skipped']), 2)  # Audacity 4 open: both wait, one process list for the program
        self.running = set()
        report = self.run_install('audacity')
        self.assertEqual(len(report['installed']), 2)
        self.assertIn(b'SendAnonymousUsageInfo=false\r\nlanguage=co\r\n', ini.read_bytes())
        corsu.disable(['audacity'])
        self.assertEqual(ini.read_bytes(), original)
        self.assertEqual(config.read_text(), AUDACITY_CFG)

    def test_tenacity(self):
        self.make('Tenacity/tenacity.exe')
        write_mo(self.files / 'Tenacity/Languages/co/tenacity.mo')
        config = self.root / 'Roaming/tenacity/tenacity.cfg'
        write(config, AUDACITY_CFG)
        self.run_install('tenacity')
        self.assertIn('Language=co', config.read_text())

    def freac_install(self, folder):
        write(folder / 'freac.exe', b'x')
        write(folder / 'lang/freac_co.xml', '<LangFile><entry id="1" string="OK">Vai</entry></LangFile>')
        write(folder / 'lang/freac.xml', '<LangFile><entry id="1" string="OK">OK</entry></LangFile>')

    def test_freac_installed_in_program_files_uses_appdata(self):
        self.freac_install(self.files / 'freac')
        config = self.root / 'Roaming/freac/freac.xml'
        report = self.run_install('freac')
        self.assertIn('once', report['skipped'][0]['reason'])
        original = write(config, FREAC_XML.replace('\n', '\r\n'))
        [installation] = freac.Freac().find()
        self.assertEqual(installation.coverage, '1/1')
        self.run_install('freac')
        self.run_install('freac')
        self.assertEqual(config.read_bytes(), original.replace(b'freac_fr.xml', b'freac_co.xml'))
        corsu.disable(['freac'])
        self.assertEqual(config.read_bytes(), original)

    def test_freac_outside_program_files_keeps_its_settings_beside_it(self):
        folder = self.root / 'Local/Programs/freac'
        self.freac_install(folder)
        without = FREAC_XML.replace('   <value name="Language">freac_fr.xml</value>\n', '')
        original = write(folder / 'freac.xml', without)
        self.run_install('freac')
        self.assertIn('   <value name="StartCount">3</value>\n   <value name="Language">freac_co.xml</value>\n  </section>',
                      (folder / 'freac.xml').read_text())
        self.assertFalse((self.root / 'Roaming/freac/freac.xml').exists())
        corsu.disable(['freac'])
        self.assertEqual((folder / 'freac.xml').read_bytes(), original)

    def test_freac_malformed_other_configuration_and_open(self):
        self.freac_install(self.files / 'freac')
        config = self.root / 'Roaming/freac/freac.xml'
        write(config, '<ConfigFile><configuration name="default"><section name="Settings">')
        report = self.run_install('freac')
        self.assertEqual(config.read_text(), '<ConfigFile><configuration name="default"><section name="Settings">')
        self.assertEqual(len(report['skipped']), 1)
        other = FREAC_XML.replace(' </configuration>\n', ' </configuration>\n <configuration name="Fast">\n'
                                  '  <section name="Settings">\n   <value name="Language">freac_de.xml</value>\n'
                                  '  </section>\n </configuration>\n')
        write(config, other)
        report = self.run_install('freac')
        self.assertIn('Fast', report['skipped'][0]['reason'])
        self.assertEqual(config.read_text(), other)
        write(config, FREAC_XML)
        self.running = {r'C:\Program Files\freac\freac.exe'}
        report = self.run_install('freac')
        self.assertIn('fre:ac', report['skipped'][0]['reason'])
        self.assertEqual(config.read_text(), FREAC_XML)


class MacTests(AudioAppsTests):
    platform = 'macos'

    def test_audacity_3_file_and_audacity_4_preference(self):
        bundle = self.root / 'Applications/Audacity.app'
        write_mo(bundle / 'Contents/Resources/co.lproj/audacity.mo')
        config = self.root / 'Library/Application Support/audacity/audacity.cfg'
        write(config, AUDACITY_CFG)
        four = self.root / 'Applications/Audacity 4.app'
        write(four / 'Contents/Resources/locale/audacity_co.qm', b'qm')
        report = self.run_install('audacity')
        self.assertIn('once', report['skipped'][0]['reason'])  # Audacity 4 never started: no preferences yet
        write(self.root / 'Library/Preferences/org.audacityteam.Audacity4.plist', b'plist')
        self.defaults[('org.audacityteam.Audacity4', 'language')] = 'system'
        report = self.run_install('audacity')
        self.assertEqual(len(report['installed']), 2)
        self.assertIn('Language=co', config.read_text())
        self.assertEqual(self.defaults[('org.audacityteam.Audacity4', 'language')], 'co')
        corsu.disable(['audacity'])
        self.assertEqual(self.defaults[('org.audacityteam.Audacity4', 'language')], 'system')
        self.assertEqual(config.read_text(), AUDACITY_CFG)

    def test_tenacity_and_unverified_freac(self):
        write_mo(self.root / 'Applications/Tenacity.app/Contents/Resources/co.lproj/tenacity.mo')
        config = self.root / 'Library/Application Support/tenacity/tenacity.cfg'
        write(config, AUDACITY_CFG)
        self.run_install('tenacity')
        self.assertIn('Language=co', config.read_text())
        (self.root / 'Applications/freac.app').mkdir(parents=True)
        report = self.run_install('freac')
        self.assertIn('macOS', report['skipped'][0]['reason'])


class XmlPathTests(unittest.TestCase):
    STEPS = [['configuration', 'name', 'default'], ['section', 'name', 'Settings'], ['value', 'name', 'Language']]
    get, put = (staticmethod(function) for function in settings.FILE_KINDS['xml-path'])

    def test_compact_file_self_closing_value_and_escaping(self):
        text = '<ConfigFile><configuration name="default"><section name="Settings"></section></configuration></ConfigFile>'
        changed = self.put(text, self.STEPS, 'a&b')
        self.assertIn('<section name="Settings"><value name="Language">a&amp;b</value></section>', changed)
        self.assertEqual(self.get(changed, self.STEPS), 'a&b')
        self.assertEqual(self.put(changed, self.STEPS, None), text)
        closed = text.replace('</section>', '<value name="Language"/></section>')
        self.assertEqual(self.get(closed, self.STEPS), '')
        self.assertIn('<value name="Language">x</value>', self.put(closed, self.STEPS, 'x'))

    def test_missing_section_and_malformed_text_raise(self):
        with self.assertRaises(ValueError):
            self.put('<ConfigFile><configuration name="default"/></ConfigFile>', self.STEPS, 'x')
        with self.assertRaises(Exception):
            self.get('<ConfigFile><configuration name="default">', self.STEPS)
        self.assertIsNone(self.get('<ConfigFile><configuration name="other"/></ConfigFile>', self.STEPS))


class ValidationTests(unittest.TestCase):
    def test_every_new_program_states_how_it_was_checked(self):
        for program in (*audacity.PROGRAMS, *freac.PROGRAMS):
            self.assertEqual(set(program.validation), {'simulated', 'real_app', 'visual', 'linguistic_review'})
            self.assertTrue(program.validation['simulated'])


if __name__ == '__main__':
    unittest.main()
