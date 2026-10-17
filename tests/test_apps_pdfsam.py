"""PDFsam Basic on simulated folders, Java preferences and registry (no real PDFsam runs here; the real run on Linux
is described in docs/apps-research.md §3.13): one preference switched, everything else kept, given back only while it
still holds Corsu's value."""
import io
import json
import os
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import corsu
import apps
from apps import pdfsam, settings

# What PDFsam 6.0.6 wrote at its first start (seen in a real run), shortened.
PREFS = ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
         '<!DOCTYPE map SYSTEM "http://java.sun.com/dtd/preferences.dtd">\n'
         '<map MAP_XML_VERSION="1.0">\n'
         '  <entry key="compression_policy" value="COMPRESS"/>\n'
         '  <entry key="locale" value="en"/>\n'
         '  <entry key="theme" value="UD34F1S9XX45FMQ"/>\n'
         '  <entry key="workspace_path" value=""/>\n'
         '</map>\n')
EMPTY = ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
         '<!DOCTYPE map SYSTEM "http://java.sun.com/dtd/preferences.dtd">\n'
         '<map MAP_XML_VERSION="1.0"/>\n')
CORSICAN = '# Corsican\n!=Project-Id-Version\\: PDFsam\nExtract=Estrae\nSplit\\ by\\ size=Sparte \\\n  da dimensione\n'
FRENCH = 'Extract=Extraire\nSplit\\ by\\ size=Découpage par taille\nMerge=Fusion\n'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode('utf-8')
    path.write_bytes(data)
    return data


def make_jar(path, corsican=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('org/pdfsam/i18n/Messages.properties', '')
        archive.writestr('org/pdfsam/i18n/Messages_fr.properties', FRENCH.encode('latin-1'))
        if corsican:
            archive.writestr('org/pdfsam/i18n/Messages_co.properties', CORSICAN)


class PdfsamTests(unittest.TestCase):
    platform = 'linux'

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / 'casa è spaziu'
        self.files = self.root / 'Program Files'
        self.opt = self.root / 'opt/pdfsam-basic'
        self.which = {}
        self.open = False
        self.running = set()
        self.registry = {}
        self.node = False
        known = {'pdfsam': pdfsam.PDFsam()}
        self.stack = ExitStack()
        for target, name, value in (
                (corsu, 'HOME', self.root), (corsu, 'DATA', self.root / 'data'),
                (corsu, 'STATE', self.root / 'data/state.json'), (corsu, 'PLATFORM', self.platform),
                (corsu, 'running_executables', lambda: self.running),
                (apps, 'registry', lambda: known), (apps.shutil, 'which', lambda name: self.which.get(name)),
                (pdfsam, 'LINUX_FOLDERS', (self.opt, self.root / 'usr/share/java/pdfsam')),
                (pdfsam, 'APPLICATIONS', (self.root / 'Applications',)),
                (pdfsam, 'linux_running', lambda: self.open),
                (pdfsam, 'registry_node_exists', lambda: self.node),
                (settings, 'registry_get', lambda key, name: self.registry.get((key, name))),
                (settings, 'registry_set', self.registry_set)):
            self.stack.enter_context(patch.object(target, name, value))
        self.stack.enter_context(patch.dict(os.environ, {
            'ProgramFiles': str(self.files), 'ProgramFiles(x86)': '', 'ProgramW6432': '',
            'APPDATA': str(self.root / 'Roaming'), 'LOCALAPPDATA': str(self.root / 'Local')}))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def registry_set(self, key, name, value):
        if value is None:
            self.registry.pop((key, name), None)
        else:
            self.registry[(key, name)] = tuple(value)

    def tearDown(self):
        self.stack.close()
        self.directory.cleanup()

    def run_install(self):
        installer = corsu.Installer()
        report = apps.install(installer, 'pdfsam')
        installer.state['components'] = ['pdfsam']
        corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
        return report

    @property
    def prefs(self):
        return self.root / '.java/.userPrefs/org/pdfsam/user/conf/prefs.xml'


class LinuxTests(PdfsamTests):
    def deb(self, version='6.0.6', corsican=True):
        make_jar(self.opt / f'lib/pdfsam-i18n-{version}.jar', corsican)
        write(self.opt / 'bin/pdfsam-basic', '#!/bin/sh\n')

    def test_switched_twice_then_off_gives_back_the_exact_file(self):
        self.deb()
        original = write(self.prefs, PREFS)
        [installation] = pdfsam.PDFsam().find()
        self.assertEqual((installation.version, installation.coverage, installation.reason), ('6.0.6', '2/3', None))
        report = self.run_install()
        self.run_install()  # a second run (an update of Corsu) changes nothing more and keeps the first original
        self.assertEqual(report['activation'], 'active')
        self.assertEqual(self.prefs.read_bytes(), original.replace(b'value="en"', b'value="co"'))
        corsu.disable(['pdfsam'])
        self.assertEqual(self.prefs.read_bytes(), original)
        corsu.enable(['pdfsam'])
        self.assertIn(b'<entry key="locale" value="co"/>', self.prefs.read_bytes())
        corsu.uninstall()
        self.assertEqual(self.prefs.read_bytes(), original)

    def test_never_started_is_left_alone_with_what_to_do(self):
        self.deb()
        report = self.run_install()
        [skipped] = report['skipped']
        self.assertEqual(report['activation'], 'blocked')
        self.assertIn('not been started', skipped['reason'])
        self.assertIn('Start PDFsam Basic once', skipped['action'])
        self.assertFalse(self.prefs.exists())  # never invented

    def test_node_without_keys_gets_the_entry_then_loses_it(self):
        self.deb()
        write(self.prefs, EMPTY)
        self.run_install()
        self.assertEqual(self.prefs.read_text(), EMPTY.replace(
            '<map MAP_XML_VERSION="1.0"/>', '<map MAP_XML_VERSION="1.0">\n  <entry key="locale" value="co"/>\n</map>'))
        corsu.disable(['pdfsam'])
        # No value before Corsu: PDFsam again follows the system language (Java reads an empty map the same way).
        self.assertEqual(self.prefs.read_text(), EMPTY.replace('<map MAP_XML_VERSION="1.0"/>',
                                                               '<map MAP_XML_VERSION="1.0">\n</map>'))

    def test_language_chosen_in_pdfsam_afterwards_is_kept(self):
        self.deb()
        write(self.prefs, PREFS)
        self.run_install()
        # The person picks French in PDFsam's settings: PDFsam writes its own value.
        self.prefs.write_text(self.prefs.read_text().replace('value="co"', 'value="fr"'))
        report = self.run_install()
        self.assertIn('changed in PDFsam', report['instances'][0]['reason'])
        self.assertIn('value="fr"', self.prefs.read_text())
        corsu.disable(['pdfsam'])
        self.assertIn('value="fr"', self.prefs.read_text())
        corsu.uninstall()
        self.assertIn('value="fr"', self.prefs.read_text())

    def test_open_pdfsam_waits_to_switch_on_and_off(self):
        self.deb()
        write(self.prefs, PREFS)
        self.open = True
        report = self.run_install()
        self.assertIn('Close PDFsam Basic', report['skipped'][0]['action'])
        self.assertEqual(self.prefs.read_text(), PREFS)
        self.open = False
        self.run_install()
        self.open, self.running = True, {'/opt/pdfsam-basic/runtime/bin/java'}
        corsu.disable(['pdfsam'])  # it would write its old value back when it quits
        self.assertIn('value="co"', self.prefs.read_text())
        self.assertFalse(corsu.is_disabled('pdfsam'))
        self.open, self.running = False, set()
        corsu.disable(['pdfsam'])
        self.assertEqual(self.prefs.read_text(), PREFS)
        self.assertTrue(corsu.is_disabled('pdfsam'))

    def test_without_corsican_old_version_or_broken_preferences(self):
        self.deb(corsican=False)
        write(self.prefs, PREFS)
        report = self.run_install()
        self.assertIn('Update or reinstall', report['skipped'][0]['action'])
        for jar in (self.opt / 'lib').glob('*.jar'):
            jar.unlink()
        self.deb(version='4.3.4')
        report = self.run_install()
        self.assertIn('4.3.4', report['skipped'][0]['reason'])
        self.assertEqual(self.prefs.read_text(), PREFS)
        for jar in (self.opt / 'lib').glob('*.jar'):
            jar.unlink()
        self.deb()
        broken = PREFS.replace('</map>\n', '')
        self.prefs.write_text(broken)
        report = self.run_install()
        self.assertEqual(report['activation'], 'failed')
        self.assertEqual(self.prefs.read_text(), broken)

    def test_tar_gz_found_through_its_command_and_one_preference_for_all(self):
        folder = self.root / 'Prugrammi/pdfsam-basic-6.0.6-linux-x64'
        make_jar(folder / 'lib/pdfsam-i18n-6.0.6.jar')
        write(folder / 'bin/pdfsam.sh', '#!/bin/sh\n')
        self.which['pdfsam'] = str(folder / 'bin/pdfsam.sh')
        self.deb()
        write(self.prefs, PREFS)
        installations = pdfsam.PDFsam().find()
        # The command is followed to its real folder (/private/var on macOS, long names on Windows).
        self.assertEqual([item.location for item in installations], [self.opt, folder.resolve()])
        report = self.run_install()
        self.assertEqual(len(report['installed']), 2)
        corsu.disable(['pdfsam'])
        self.assertEqual(self.prefs.read_text(), PREFS)

    def test_a_launcher_script_elsewhere_is_not_an_installation(self):
        # The AUR package's /usr/bin/pdfsam is a script; its jars are in /usr/share/java/pdfsam.
        write(self.root / 'usr/bin/pdfsam', '#!/bin/sh\n')
        self.which['pdfsam'] = str(self.root / 'usr/bin/pdfsam')
        self.assertEqual(pdfsam.PDFsam().find(), [])
        make_jar(self.root / 'usr/share/java/pdfsam/pdfsam-i18n-6.0.5.jar')
        [installation] = pdfsam.PDFsam().find()
        self.assertEqual((installation.location, installation.version), (self.root / 'usr/share/java/pdfsam', '6.0.5'))


class WindowsTests(PdfsamTests):
    platform = 'windows'
    KEY = r'Software\JavaSoft\Prefs\org\pdfsam\user\conf'

    def msi(self):
        folder = self.files / 'PDFsam Basic'
        write(folder / 'pdfsam.exe', b'MZ')
        make_jar(folder / 'app/mods/pdfsam-i18n-6.0.6.jar')
        return folder

    def test_registry_value_switched_and_given_back(self):
        folder = self.msi()
        report = self.run_install()
        self.assertIn('Start PDFsam Basic once', report['skipped'][0]['action'])
        self.assertEqual(self.registry, {})
        self.node = True
        self.registry[(self.KEY, 'locale')] = ('en', 1)
        [installation] = pdfsam.PDFsam().find()
        self.assertEqual((installation.location, installation.coverage), (folder / 'pdfsam.exe', '2/3'))
        self.run_install()
        self.run_install()
        self.assertEqual(self.registry[(self.KEY, 'locale')], ('co', 1))
        corsu.disable(['pdfsam'])
        self.assertEqual(self.registry[(self.KEY, 'locale')], ('en', 1))

    def test_open_pdfsam_needs_a_restart_and_a_later_choice_is_kept(self):
        self.msi()
        self.node = True
        self.running = {r'C:\Program Files\PDFsam Basic\pdfsam.exe'}
        report = self.run_install()
        self.assertEqual(report['activation'], 'restart_required')
        self.assertEqual(self.registry[(self.KEY, 'locale')], ('co', 1))  # no value before: removed when switched off
        self.registry[(self.KEY, 'locale')] = ('pt-/B/R', 1)  # Brazilian Portuguese chosen in PDFsam
        report = self.run_install()
        self.assertIn('pt-/B/R', report['instances'][0]['reason'])
        corsu.uninstall()
        self.assertEqual(self.registry[(self.KEY, 'locale')], ('pt-/B/R', 1))
        self.registry.clear()
        self.run_install()
        corsu.uninstall()
        self.assertEqual(self.registry, {})


class MacTests(PdfsamTests):
    platform = 'macos'

    def test_found_but_left_to_pdfsam_settings(self):
        bundle = self.root / 'Applications/PDFsam Basic.app'
        make_jar(bundle / 'Contents/app/mods/pdfsam-i18n-6.0.6.jar')
        report = self.run_install()
        [skipped] = report['skipped']
        self.assertIn('macOS', skipped['reason'])
        self.assertIn('Settings', skipped['action'])
        self.assertEqual(skipped['version'], '6.0.6')


class JavaPrefsKindTests(unittest.TestCase):
    get, put = (staticmethod(function) for function in settings.FILE_KINDS['java-prefs'])

    def test_one_entry_changed_others_untouched(self):
        changed = self.put(PREFS, 'locale', 'co')
        self.assertEqual(changed, PREFS.replace('value="en"', 'value="co"'))
        self.assertEqual(self.get(changed, 'locale'), 'co')
        self.assertEqual(self.put(changed, 'locale', 'en'), PREFS)

    def test_added_at_the_end_and_removed_with_its_line(self):
        without = PREFS.replace('  <entry key="locale" value="en"/>\n', '')
        added = self.put(without, 'locale', 'co')
        self.assertTrue(added.endswith('  <entry key="workspace_path" value=""/>\n  <entry key="locale" value="co"/>\n</map>\n'))
        self.assertEqual(self.put(added, 'locale', None), without)

    def test_escaping_and_malformed_files(self):
        value = 'a "b" & <c>\nd'
        text = self.put(PREFS, 'stage.status', value)
        self.assertEqual(self.get(text, 'stage.status'), value)
        self.assertIsNone(self.get(PREFS, 'local'))
        with self.assertRaises(Exception):
            self.get(PREFS.replace('</map>', ''), 'locale')
        with self.assertRaises(ValueError):
            self.get('<properties/>', 'locale')


class CatalogueTests(unittest.TestCase):
    def test_properties_entries_count_continued_lines_once(self):
        self.assertEqual(pdfsam.properties_count(CORSICAN.encode('latin-1')), 2)
        self.assertEqual(pdfsam.properties_count(b'# a comment \\\nkey=value\n\n'), 1)

    def test_version_from_the_jar_name(self):
        self.assertEqual(pdfsam.version_of(Path('pdfsam-i18n-6.0.6.jar')), '6.0.6')
        self.assertEqual(pdfsam.version_of(Path('pdfsam-i18n-5.0.0.M1.jar')), '5.0.0')
        self.assertIsNone(pdfsam.version_of(Path('pdfsam-core-6.0.6.jar')))


if __name__ == '__main__':
    unittest.main()
