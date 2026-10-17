"""Poedit on simulated folders, menu entries, Flatpak overrides, registry and preferences (no real program runs here;
the Linux package and the Flatpak were also run for real, see src/apps/poedit.py). SIMULATED: macOS's `defaults` is a
fake here (FakeDefaults, plist files written with plistlib), and `locale` is never run."""
import io
import json
import os
import plistlib
import subprocess
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import corsu
import engine
import apps
from apps import poedit, settings

MO = {b'': b'Content-Type: text/plain; charset=UTF-8\n', b'Open': b'Apre', b'Save': b'Arregistr\xc3\xa0'}
SYSTEM_ENTRY = ('[Desktop Entry]\nName=Poedit\nExec=poeditor %F\nIcon=net.poedit.Poedit\nType=Application\n')
URI_ENTRY = ('[Desktop Entry]\nName=Poedit\nNoDisplay=true\nMimeType=x-scheme-handler/poedit;\n'
             'Exec=poeditor --handle-poedit-uri %u\n')
FORMATS = ('LC_CTYPE=fr_FR.UTF-8 LC_NUMERIC=fr_FR.UTF-8 LC_TIME=fr_FR.UTF-8 LC_COLLATE=fr_FR.UTF-8 '
           'LC_MONETARY=fr_FR.UTF-8 LC_PAPER=fr_FR.UTF-8 LC_MEASUREMENT=fr_FR.UTF-8')
REAL_CHECK = poedit.messages_name_works  # patched in every test but test_messages_name_check
PREFIX = 'env LANGUAGE=co:fr_FR LC_MESSAGES=/C.UTF-8 '
FALLBACK_PREFIX = f'env LANGUAGE=co:fr_FR LANG=C.UTF-8 LC_MESSAGES=C.UTF-8 {FORMATS} '


def write_mo(path, extra=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = dict(MO)
    if extra:
        entries[b'Quit'] = b'Quitter'
    path.write_bytes(engine.make_mo(entries))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding='utf-8')
    return data


class PoeditTests(unittest.TestCase):
    platform = 'linux'

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / 'casa è spaziu'
        self.applications = self.root / 'usr/share/applications'
        self.running = set()
        self.registry = {}
        self.defaults = {}
        self.which = {}
        self.separate = True
        self.c_utf8 = True
        known = {'poedit': poedit.Poedit()}
        self.stack = ExitStack()
        for target, name, value in (
                (corsu, 'HOME', self.root), (corsu, 'DATA', self.root / 'data'),
                (corsu, 'STATE', self.root / 'data/state.json'), (corsu, 'PLATFORM', self.platform),
                (corsu, 'running_executables', lambda: self.running),
                (apps, 'registry', lambda: known), (apps, 'FLATPAK_SYSTEM', self.root / 'flatpak'),
                (apps, 'APPLICATION_DIRS', (self.applications,)),
                (apps.shutil, 'which', lambda name: self.which.get(name)),
                (poedit, 'LOCALE', self.root / 'nowhere/locale'), (poedit, 'SNAP', self.root / 'snap/poedit'),
                (poedit, 'APPLICATIONS', (self.root / 'Applications',)),
                (poedit, 'messages_name_works', lambda: self.separate),
                (poedit, 'c_utf8_works', lambda: self.c_utf8),
                (settings, 'registry_get', lambda key, name: self.registry.get((key, name))),
                (settings, 'registry_set', self.registry_set),
                (settings, 'defaults_get', lambda domain, key: self.defaults.get((domain, key))),
                (settings, 'defaults_put', self.defaults_put)):
            self.stack.enter_context(patch.object(target, name, value))
        environment = {name: '' for name in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', *poedit.CATEGORIES)}
        environment.update({'LANG': 'fr_FR.UTF-8', 'ProgramFiles': str(self.root / 'Program Files'),
                            'ProgramFiles(x86)': '', 'ProgramW6432': '', 'APPDATA': str(self.root / 'Roaming'),
                            'LOCALAPPDATA': str(self.root / 'Local')})
        self.stack.enter_context(patch.dict(os.environ, environment))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def registry_set(self, key, name, value):
        if value is None:
            self.registry.pop((key, name), None)
        else:
            self.registry[(key, name)] = tuple(value)

    def defaults_put(self, domain, key, value):
        if value is None:
            self.defaults.pop((domain, key), None)
        else:
            self.defaults[(domain, key)] = value

    def tearDown(self):
        self.stack.close()
        self.directory.cleanup()

    def run_install(self):
        installer = corsu.Installer()
        report = apps.install(installer, 'poedit')
        installer.state['components'] = ['poedit']
        corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
        return report

    def entry(self, name='net.poedit.Poedit.desktop'):
        return self.root / '.local/share/applications' / name


class LinuxTests(PoeditTests):
    def system_poedit(self, catalogue=True):
        executable = self.root / 'usr/bin/poeditor'
        write(executable, '')
        self.which['poeditor'] = str(executable)
        if catalogue:
            write_mo(self.root / 'usr/share/locale/co/LC_MESSAGES/poedit.mo')
        write_mo(self.root / 'usr/share/locale/fr/LC_MESSAGES/poedit.mo', extra=True)
        write(self.applications / 'net.poedit.Poedit.desktop', SYSTEM_ENTRY)
        write(self.applications / 'net.poedit.PoeditURI.desktop', URI_ENTRY)

    def test_menu_entries_start_poedit_in_corsican_then_go_back(self):
        self.system_poedit()
        [installation] = poedit.Poedit().find()
        self.assertEqual((installation.coverage, installation.reason), ('2/3', None))
        report = self.run_install()
        self.run_install()  # a second run (update) rebuilds the same entries
        self.assertEqual(report['activation'], 'active')
        self.assertEqual(self.entry().read_text(), SYSTEM_ENTRY.replace('Exec=', 'Exec=' + PREFIX))
        self.assertIn('Exec=' + PREFIX + 'poeditor --handle-poedit-uri %u', self.entry('net.poedit.PoeditURI.desktop').read_text())
        corsu.disable(['poedit'])
        self.assertFalse(self.entry().exists())
        self.assertFalse(self.entry('net.poedit.PoeditURI.desktop').exists())
        self.run_install()  # an update while switched off: the program's own setting is the person's choice
        corsu.enable(['poedit'])
        self.assertTrue(self.entry().exists())
        corsu.uninstall()
        self.assertFalse(self.entry().exists())
        self.assertFalse(self.entry('net.poedit.PoeditURI.desktop').exists())

    def test_session_locale_variables(self):
        # GTK keeps the session's language: only LC_MESSAGES changes, LANG and the formats stay the session's.
        self.assertEqual(poedit.environment(), {'LC_MESSAGES': '/C.UTF-8'})
        with patch.dict(os.environ, {'LC_ALL': 'de_DE.UTF-8', 'LC_TIME': 'en_GB.UTF-8'}):
            # LC_ALL beats LC_MESSAGES: emptied, its value goes to LANG and to the categories the session sets.
            self.assertEqual(poedit.environment(), {'LC_MESSAGES': '/C.UTF-8', 'LC_ALL': '', 'LANG': 'de_DE.UTF-8',
                                                    'LC_TIME': 'de_DE.UTF-8'})
        with patch.dict(os.environ, {'LC_TIME': 'en_GB.UTF-8', 'LANG': 'C'}):
            self.assertEqual(poedit.environment(), {'LC_MESSAGES': '/C.UTF-8'})
        self.system_poedit()
        with patch.dict(os.environ, {'LC_ALL': 'fr_FR.UTF-8'}):
            self.run_install()
        self.assertIn('Exec=env LANGUAGE=co:fr_FR LC_MESSAGES=/C.UTF-8 "LC_ALL=" LANG=fr_FR.UTF-8 poeditor %F',
                      self.entry().read_text())

    def test_fallback_locale_variables(self):
        self.assertEqual(poedit.environment(separate=False), {'LANG': 'C.UTF-8', 'LC_MESSAGES': 'C.UTF-8',
                                                              **{name: 'fr_FR.UTF-8' for name in poedit.FORMATS}})
        with patch.dict(os.environ, {'LC_ALL': 'de_DE.UTF-8', 'LC_TIME': 'en_GB.UTF-8'}):
            values = poedit.environment(separate=False)
            self.assertEqual((values['LC_ALL'], values['LC_TIME'], values['LC_NUMERIC']), ('', 'de_DE.UTF-8', 'de_DE.UTF-8'))
        with patch.dict(os.environ, {'LC_TIME': 'en_GB.UTF-8'}):
            self.assertNotIn('LC_TIME', poedit.environment(separate=False))  # the session's own value is inherited
        with patch.dict(os.environ, {'LANG': 'C'}):
            self.assertEqual(poedit.environment(separate=False), {'LANG': 'C.UTF-8', 'LC_MESSAGES': 'C.UTF-8'})
        self.c_utf8 = False  # no C.UTF-8 at all: plain C, which always loads, so the formats still apply
        self.assertEqual(poedit.environment(separate=False), {'LANG': 'C', 'LC_MESSAGES': 'C',
                                                              **{name: 'fr_FR.UTF-8' for name in poedit.FORMATS}})

    def test_without_the_c_utf8_folder_the_fallback_says_what_it_costs(self):
        self.system_poedit()
        self.separate = False
        [installation] = poedit.Poedit().find()
        self.assertIn('file dialogs will be in English', installation.kind)
        self.assertIsNone(installation.reason)
        self.run_install()
        self.assertEqual(self.entry().read_text(), SYSTEM_ENTRY.replace('Exec=', 'Exec=' + FALLBACK_PREFIX))
        self.separate = True  # e.g. glibc updated: the next run writes the separate way
        self.run_install()
        self.assertEqual(self.entry().read_text(), SYSTEM_ENTRY.replace('Exec=', 'Exec=' + PREFIX))
        corsu.uninstall()
        self.assertFalse(self.entry().exists())

    def test_messages_name_check(self):
        calls, outcome = [], {}

        def run(command, **options):
            calls.append((command, options['env']))
            return subprocess.CompletedProcess(command, 0, outcome['out'], outcome['err'])
        with patch.object(poedit.subprocess, 'run', run):
            outcome.update(out='LANG=\nLC_MESSAGES="/C.UTF-8"\nLC_ALL=/C.UTF-8\n', err='')
            self.assertTrue(REAL_CHECK())
            self.assertEqual((calls[0][0], calls[0][1]['LC_ALL']), (['locale'], '/C.UTF-8'))
            outcome.update(out='LC_ALL=/C.UTF-8\n', err='locale: Cannot set LC_ALL to default locale: No such file\n')
            self.assertFalse(REAL_CHECK())
            outcome.update(out='LC_ALL=C.UTF-8\n', err='')
            self.assertTrue(poedit.locale_loads('C.UTF-8'))
            self.assertEqual(calls[-1][1]['LC_ALL'], 'C.UTF-8')

        def missing(command, **options):
            raise FileNotFoundError(command[0])
        with patch.object(poedit.subprocess, 'run', missing):
            self.assertFalse(REAL_CHECK())

    def test_without_catalogue_or_in_a_corsican_session_nothing_is_written(self):
        self.system_poedit(catalogue=False)
        report = self.run_install()
        self.assertEqual(report['activation'], 'blocked')
        self.assertIn('poedit-common', report['skipped'][0]['action'])
        self.assertFalse(self.entry().exists())
        write_mo(self.root / 'usr/share/locale/co/LC_MESSAGES/poedit.mo')
        with patch.dict(os.environ, {'LANG': 'co_FR.UTF-8'}):
            report = self.run_install()
        self.assertIn('already in Corsican', report['skipped'][0]['reason'])

    def test_catalogue_gone_later_takes_back_the_menu_entries(self):
        self.system_poedit()
        self.run_install()
        (self.root / 'usr/share/locale/co/LC_MESSAGES/poedit.mo').unlink()
        report = self.run_install()
        self.assertEqual(report['activation'], 'blocked')
        self.assertFalse(self.entry().exists())
        self.assertFalse(self.entry('net.poedit.PoeditURI.desktop').exists())

    def test_menu_entries_of_your_own_or_changed_since_are_left_alone(self):
        self.system_poedit()
        own = write(self.entry(), '[Desktop Entry]\nExec=poeditor --my-options\n')
        report = self.run_install()
        self.assertEqual(report['activation'], 'blocked')
        self.assertEqual(self.entry().read_text(), own)
        self.entry().unlink()
        self.run_install()
        changed = self.entry().read_text().replace('LANGUAGE=co:fr_FR', 'LANGUAGE=it')
        self.entry().write_text(changed)
        report = self.run_install()
        self.assertIn('changed', report['skipped'][0]['reason'])
        corsu.disable(['poedit'])
        self.assertEqual(self.entry().read_text(), changed)  # the person's edit stays

    def test_open_poedit_needs_a_restart(self):
        self.system_poedit()
        self.running = {'/usr/bin/poeditor'}
        report = self.run_install()
        self.assertEqual(report['activation'], 'restart_required')
        self.assertIn('Restart Poedit', report['instances'][0]['action'])
        self.assertTrue(self.entry().exists())
        corsu.disable(['poedit'])  # nothing to wait for: Poedit never writes the menu entry
        self.assertFalse(self.entry().exists())

    def flatpak(self, corsican=True):
        base = self.root / '.local/share/flatpak'
        (base / 'app/net.poedit.Poedit/x86_64/stable/abc/files').mkdir(parents=True)
        if corsican:
            write_mo(base / 'runtime/net.poedit.Poedit.Locale/x86_64/stable/abc/files/co/share/co/LC_MESSAGES/poedit.mo')
        return base / 'overrides/net.poedit.Poedit'

    def test_flatpak_override_keeps_your_other_settings_and_your_later_choice(self):
        override = self.flatpak(corsican=False)
        report = self.run_install()
        self.assertIn('extra-languages', report['skipped'][0]['reason'])
        self.assertIn('flatpak config', report['skipped'][0]['action'])
        write_mo(self.root / '.local/share/flatpak/runtime/net.poedit.Poedit.Locale/x86_64/stable/abc/files/co/share/co/'
                 'LC_MESSAGES/poedit.mo')
        original = write(override, '[Context]\nfilesystems=home;\n\n[Environment]\nLANG=fr_FR.UTF-8\n')
        report = self.run_install()
        self.run_install()
        self.assertEqual(report['activation'], 'active')
        text = override.read_text()
        self.assertIn('LANGUAGE=co:fr_FR\n', text)
        self.assertIn('LC_MESSAGES=/C.UTF-8\n', text)
        self.assertIn('LANG=fr_FR.UTF-8\n', text)  # the person's own variable, untouched
        self.assertNotIn('LC_TIME', text)
        self.assertIn('[Context]\nfilesystems=home;\n', text)
        corsu.disable(['poedit'])
        self.assertEqual(override.read_text(), original)
        corsu.enable(['poedit'])
        override.write_text(override.read_text().replace('LANGUAGE=co:fr_FR', 'LANGUAGE=de'))
        report = self.run_install()
        self.assertIn('your choice is kept', report['skipped'][0]['reason'])
        self.assertIn('LANGUAGE=de\n', override.read_text())
        corsu.disable(['poedit'])
        self.assertIn('LANGUAGE=de\n', override.read_text())
        self.assertIn('LANG=fr_FR.UTF-8\n', override.read_text())

    def test_flatpak_variable_no_longer_needed_goes_back(self):
        override = self.flatpak()
        write(override, '[Context]\nshared=network;\n')
        with patch.dict(os.environ, {'LC_ALL': 'fr_FR.UTF-8'}):
            self.run_install()
        self.assertIn('LC_ALL=\n', override.read_text())
        self.run_install()
        self.assertNotIn('LC_ALL', override.read_text())
        corsu.uninstall()
        self.assertEqual(override.read_text(), '[Context]\nshared=network;\n')

    def test_flatpak_override_from_the_earlier_way_is_brought_up_to_date(self):
        override = self.flatpak()
        original = write(override, '[Context]\nshared=network;\n\n[Environment]\nLC_TIME=en_GB.UTF-8\n')
        # What Corsu 0.25's first way wrote (LANG and LC_MESSAGES C.UTF-8, formats given back):
        earlier = {'LANG': 'C.UTF-8', 'LC_MESSAGES': 'C.UTF-8', 'LC_TIME': 'fr_FR.UTF-8'}
        with patch.object(poedit, 'environment', lambda separate=True: dict(earlier)):
            self.run_install()
        self.assertIn('LANG=C.UTF-8\n', override.read_text())
        self.assertIn('LC_TIME=fr_FR.UTF-8\n', override.read_text())
        self.run_install()
        text = override.read_text()
        self.assertNotIn('LANG=', text)
        self.assertIn('LC_TIME=en_GB.UTF-8\n', text)  # the person's own value is back
        self.assertIn('LC_MESSAGES=/C.UTF-8\n', text)
        corsu.uninstall()
        self.assertEqual(override.read_text(), original)

    def test_snap_is_left_alone(self):
        (self.root / 'snap/poedit').mkdir(parents=True)
        report = self.run_install()
        self.assertIn('Snap', report['skipped'][0]['reason'])


class WindowsTests(PoeditTests):
    platform = 'windows'
    KEY = (r'Software\Vaclav Slavik\Poedit', 'ui_language')

    def install_poedit(self, catalogue=True):
        folder = self.root / 'Program Files/Poedit'
        write(folder / 'Poedit.exe', 'x')
        if catalogue:
            write_mo(folder / 'Translations/co/poedit.mo')
        write_mo(folder / 'Translations/fr/poedit.mo', extra=True)

    def test_registry_value_set_before_the_first_start_and_removed_again(self):
        self.install_poedit()
        [installation] = poedit.Poedit().find()
        self.assertEqual((installation.coverage, installation.reason), ('2/3', None))
        report = self.run_install()  # Poedit never started: no key yet, nothing to wait for
        self.run_install()
        self.assertEqual(report['activation'], 'active')
        self.assertEqual(self.registry[self.KEY], ('co', 1))
        corsu.disable(['poedit'])
        self.assertNotIn(self.KEY, self.registry)
        corsu.enable(['poedit'])
        self.assertEqual(self.registry[self.KEY], ('co', 1))
        corsu.uninstall()
        self.assertNotIn(self.KEY, self.registry)

    def test_earlier_language_comes_back_and_a_later_choice_is_kept(self):
        self.install_poedit()
        self.registry[self.KEY] = ('de', 1)
        self.registry[(r'Software\Vaclav Slavik\Poedit', 'last_file_path')] = (r'C:\po', 1)
        self.run_install()
        corsu.disable(['poedit'])
        self.assertEqual(self.registry[self.KEY], ('de', 1))
        self.assertEqual(self.registry[(r'Software\Vaclav Slavik\Poedit', 'last_file_path')], (r'C:\po', 1))
        corsu.enable(['poedit'])
        self.assertEqual(self.registry[self.KEY], ('co', 1))
        self.registry[self.KEY] = ('default', 1)  # "(Use default language)" chosen in Poedit afterwards
        report = self.run_install()
        self.assertEqual(report['activation'], 'blocked')
        self.assertIn('your choice is kept', report['skipped'][0]['reason'])
        self.assertEqual(self.registry[self.KEY], ('default', 1))
        corsu.disable(['poedit'])
        self.assertEqual(self.registry[self.KEY], ('default', 1))

    def test_missing_catalogue_and_open_poedit(self):
        self.install_poedit(catalogue=False)
        report = self.run_install()
        self.assertIn('Reinstall Poedit', report['skipped'][0]['action'])
        self.assertNotIn(self.KEY, self.registry)
        write_mo(self.root / 'Program Files/Poedit/Translations/co/poedit.mo')
        self.running = {r'C:\Program Files\Poedit\Poedit.exe'}
        report = self.run_install()
        self.assertEqual(report['activation'], 'restart_required')
        self.assertEqual(self.registry[self.KEY], ('co', 1))
        corsu.disable(['poedit'])  # Poedit never writes this value back: no need to wait for it to close
        self.assertNotIn(self.KEY, self.registry)


class FakeDefaults:
    """SIMULATED macOS `defaults` (export, write, delete) over plist files written with plistlib, one per domain:
    what the real command does through cfprefsd, without a Mac. The global domain's file is .GlobalPreferences.plist."""

    GLOBAL = ('NSGlobalDomain', '-g', '-globalDomain')

    def __init__(self, folder):
        self.folder, self.writes = Path(folder), []
        self.folder.mkdir(parents=True, exist_ok=True)

    def path(self, domain):
        return self.folder / ('.GlobalPreferences.plist' if domain in self.GLOBAL else f'{domain}.plist')

    def load(self, domain):
        path = self.path(domain)
        return plistlib.loads(path.read_bytes()) if path.exists() else None

    def save(self, domain, values):
        self.path(domain).write_bytes(plistlib.dumps(values, fmt=plistlib.FMT_BINARY))

    def __call__(self, command, **options):
        if command[0] != 'defaults':
            raise FileNotFoundError(command[0])
        verb, domain = command[1], command[2]
        values = self.load(domain)
        if verb == 'export':
            if values is None:
                return subprocess.CompletedProcess(command, 1, b'', f'Domain {domain} does not exist\n'.encode())
            return subprocess.CompletedProcess(command, 0, plistlib.dumps(values, fmt=plistlib.FMT_XML), b'')
        self.writes.append(list(command))
        if verb == 'write':
            text = command[4]
            value = settings.plist_value(text) if text.startswith('<') else text
            self.save(domain, {**(values or {}), command[3]: value})
            return subprocess.CompletedProcess(command, 0, b'', b'')
        if verb == 'delete':
            if values is None or command[3] not in values:
                if options.get('check'):
                    raise subprocess.CalledProcessError(1, command)
                return subprocess.CompletedProcess(command, 1, b'', b'not found')
            del values[command[3]]
            self.save(domain, values)
            return subprocess.CompletedProcess(command, 0, b'', b'')
        raise AssertionError(command)


class MacTests(PoeditTests):
    platform = 'macos'
    DOMAIN = 'net.poedit.Poedit'

    def setUp(self):
        super().setUp()
        self.fake = FakeDefaults(self.root / 'Library/Preferences')
        self.fake.save('NSGlobalDomain', {'AppleLanguages': ['fr-FR', 'en-FR', 'co-FR'], 'AppleLocale': 'fr_FR'})
        self.stack.enter_context(patch.object(subprocess, 'run', self.fake))

    def install_poedit(self, catalogue=True):
        bundle = self.root / 'Applications/Poedit.app'
        write_mo(bundle / 'Contents/Resources/fr.lproj/poedit.mo', extra=True)
        if catalogue:
            write_mo(bundle / 'Contents/Resources/co.lproj/poedit.mo')
        return bundle

    def languages(self):
        return (self.fake.load(self.DOMAIN) or {}).get('AppleLanguages')

    def test_per_application_language_list_set_and_removed_again(self):
        self.install_poedit()
        self.fake.save(self.DOMAIN, {'NSNavLastRootDirectory': '~/po', 'SUEnableAutomaticChecks': True})
        [installation] = poedit.Poedit().find()
        self.assertEqual((installation.coverage, installation.reason), ('2/3', None))
        self.assertIn('experimental', installation.kind)
        report = self.run_install()
        self.run_install()
        self.assertEqual(report['activation'], 'active')
        # Corsican, then the person's own list (Corsican taken out of it): AppKit's panels take French.
        self.assertEqual(self.languages(), ['co', 'fr-FR', 'en-FR'])
        corsu.disable(['poedit'])
        self.assertEqual(self.fake.load(self.DOMAIN), {'NSNavLastRootDirectory': '~/po', 'SUEnableAutomaticChecks': True})
        corsu.enable(['poedit'])
        self.assertEqual(self.languages(), ['co', 'fr-FR', 'en-FR'])
        corsu.uninstall()
        self.assertIsNone(self.languages())
        self.assertEqual(self.fake.load(self.DOMAIN)['SUEnableAutomaticChecks'], True)
        # The system's own list is read, never written.
        self.assertFalse([command for command in self.fake.writes if command[2] in FakeDefaults.GLOBAL])
        self.assertEqual(self.fake.load('NSGlobalDomain')['AppleLanguages'], ['fr-FR', 'en-FR', 'co-FR'])

    def test_before_the_first_start_there_is_no_domain_yet(self):
        self.install_poedit()
        self.run_install()
        self.assertEqual(self.languages(), ['co', 'fr-FR', 'en-FR'])
        corsu.uninstall()
        self.assertEqual(self.fake.load(self.DOMAIN), {})

    def test_earlier_value_comes_back_with_its_type(self):
        self.install_poedit()
        for earlier in (['de-DE', 'en'], 'de'):  # an array, and a stray string some tool wrote
            self.fake.save(self.DOMAIN, {'AppleLanguages': earlier})
            report = self.run_install()
            self.assertEqual(self.languages(), ['co', 'fr-FR', 'en-FR'], report)
            corsu.disable(['poedit'])
            self.assertEqual(self.languages(), earlier)
            self.assertIs(type(self.languages()), type(earlier))
            corsu.enable(['poedit'])
            corsu.uninstall()
            self.assertEqual(self.languages(), earlier)

    def test_a_list_changed_since_is_kept(self):
        self.install_poedit()
        self.fake.save(self.DOMAIN, {'AppleLanguages': ['de']})
        self.run_install()
        # The person chooses Italian for Poedit in System Settings → Language & Region → Applications.
        self.fake.save(self.DOMAIN, {'AppleLanguages': ['it']})
        report = self.run_install()
        self.assertEqual(report['activation'], 'blocked')
        self.assertIn('your choice is kept', report['skipped'][0]['reason'])
        self.assertEqual(self.languages(), ['it'])
        corsu.disable(['poedit'])
        self.assertEqual(self.languages(), ['it'])
        corsu.uninstall()
        self.assertEqual(self.languages(), ['it'])

    def test_system_default_chosen_since_is_kept(self):
        self.install_poedit()
        self.fake.save(self.DOMAIN, {'AppleLanguages': ['de']})
        self.run_install()
        # The person picks "System default" for Poedit in System Settings, which deletes the key.
        self.fake.save(self.DOMAIN, {})
        report = self.run_install()
        self.assertEqual(report['activation'], 'blocked')
        self.assertIn('your choice is kept', report['skipped'][0]['reason'])
        self.assertIsNone(self.languages())
        corsu.uninstall()
        self.assertIsNone(self.languages())  # not the list from before that choice

    def test_system_list_changed_later_is_followed(self):
        self.install_poedit()
        self.run_install()
        self.fake.save('NSGlobalDomain', {'AppleLanguages': ['it-IT']})
        self.run_install()
        self.assertEqual(self.languages(), ['co', 'it-IT'])
        corsu.disable(['poedit'])
        self.assertIsNone(self.languages())  # absent at first: removed, not set to the list of the first run

    def test_without_a_readable_system_list_the_session_language_follows(self):
        self.install_poedit()
        self.fake.path('NSGlobalDomain').unlink()
        self.run_install()
        self.assertEqual(self.languages(), ['co', 'fr-FR'])

    def test_missing_catalogue_and_open_poedit(self):
        self.install_poedit(catalogue=False)
        report = self.run_install()
        self.assertIn('Reinstall Poedit', report['skipped'][0]['action'])
        self.assertIsNone(self.languages())
        write_mo(self.root / 'Applications/Poedit.app/Contents/Resources/co.lproj/poedit.mo')
        self.running = {'/Applications/Poedit.app/Contents/MacOS/Poedit'}
        report = self.run_install()
        self.assertEqual(report['activation'], 'restart_required')
        self.assertEqual(self.languages(), ['co', 'fr-FR', 'en-FR'])
        (self.root / 'Applications/Poedit.app/Contents/Resources/co.lproj/poedit.mo').unlink()
        self.run_install()  # catalogue gone: the list goes back
        self.assertIsNone(self.languages())

    def test_not_installed(self):
        self.assertEqual(poedit.Poedit().find(), [])


class ValidationTests(unittest.TestCase):
    def test_states_how_it_was_checked(self):
        validation = poedit.Poedit.validation
        self.assertEqual(set(validation), {'simulated', 'real_app', 'visual', 'linguistic_review'})
        self.assertEqual(validation['real_app'], ['linux'])


if __name__ == '__main__':
    unittest.main()
