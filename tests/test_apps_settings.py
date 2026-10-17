"""Typed macOS preferences (apps/settings.py: plist values through `defaults`).

SIMULATED: everywhere but a GitHub Actions macOS runner, `defaults` is a fake (FakeDefaults from test_apps_poedit,
plist files written with plistlib); nothing here touches real preferences. RealMacTests run only on a GitHub Actions
macOS runner (a throwaway machine), on throwaway domains they delete afterwards.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corsu  # noqa: E402
from apps import settings  # noqa: E402
from test_apps_poedit import FakeDefaults  # noqa: E402

VALUES = (['co', 'fr-FR'], 'de', 3, 2.5, True, False, {'a': [1, 'b']}, b'\x00\xff',
          datetime.datetime(2026, 10, 17, 12, 0, 0), [], {})


class Installer:
    def __init__(self):
        self.state = {'files': {}}


class FragmentTests(unittest.TestCase):
    def test_every_property_list_type_comes_back_the_same(self):
        for value in VALUES:
            fragment = settings.plist_fragment(value)
            self.assertTrue(fragment.startswith('<'), fragment)
            self.assertNotIn('<plist', fragment)
            back = settings.plist_value(fragment)
            self.assertEqual((back, type(back)), (value, type(value)))
        self.assertEqual(settings.plist_fragment(['co', 'fr']), '<array><string>co</string><string>fr</string></array>')
        # Different types, different fragments: a string "1" is not the number 1, nor True.
        self.assertEqual(len({settings.plist_fragment(value) for value in ('1', 1, True)}), 3)

    def test_the_global_domain_is_refused(self):
        for domain in ('NSGlobalDomain', '-g', '-globalDomain', ' nsglobaldomain ', '.GlobalPreferences',
                       '/Users/x/Library/Preferences/.GlobalPreferences.plist', ''):
            with self.assertRaises(ValueError, msg=domain):
                settings.check_app_domain(domain)
        self.assertEqual(settings.check_app_domain('net.poedit.Poedit'), 'net.poedit.Poedit')


class SimulatedDefaultsTests(unittest.TestCase):
    """SIMULATED `defaults`."""
    DOMAIN = 'org.example.App'

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.fake = FakeDefaults(root / 'Preferences')
        self.patches = [patch.object(subprocess, 'run', self.fake), patch.object(corsu, 'STATE', root / 'state.json')]
        for item in self.patches:
            item.start()
        self.installer = Installer()

    def tearDown(self):
        for item in self.patches:
            item.stop()
        self.directory.cleanup()

    def record(self):
        return self.installer.state['files'][f'defaults:{self.DOMAIN}:AppleLanguages']

    def test_absent_key_and_missing_domain(self):
        self.assertIsNone(settings.defaults_value(self.DOMAIN, 'AppleLanguages'))  # "does not exist"
        self.fake.save(self.DOMAIN, {})
        self.assertIsNone(settings.defaults_value(self.DOMAIN, 'AppleLanguages'))
        settings.set_defaults_value(self.installer, 'app', self.DOMAIN, 'AppleLanguages', ['co', 'fr'])
        self.assertIsNone(self.record()['setting']['original'])
        self.assertEqual(self.fake.load(self.DOMAIN), {'AppleLanguages': ['co', 'fr']})
        self.assertTrue(settings.revert(self.record()))
        self.assertEqual(self.fake.load(self.DOMAIN), {})
        json.dumps(self.installer.state)  # the record is plain JSON

    def test_every_original_type_is_given_back(self):
        for original in VALUES:
            self.installer = Installer()
            self.fake.save(self.DOMAIN, {'AppleLanguages': original, 'Other': 1})
            settings.set_defaults_value(self.installer, 'app', self.DOMAIN, 'AppleLanguages', ['co', 'fr'])
            settings.set_defaults_value(self.installer, 'app', self.DOMAIN, 'AppleLanguages', ['co', 'it'])  # rerun
            self.assertEqual(settings.defaults_value(self.DOMAIN, 'AppleLanguages'), ['co', 'it'])
            self.assertTrue(settings.revert(self.record()))
            back = self.fake.load(self.DOMAIN)
            self.assertEqual((back['AppleLanguages'], type(back['AppleLanguages'])), (original, type(original)))
            self.assertEqual(back['Other'], 1)

    def test_a_value_changed_since_stays(self):
        self.fake.save(self.DOMAIN, {'AppleLanguages': ['de']})
        settings.set_defaults_value(self.installer, 'app', self.DOMAIN, 'AppleLanguages', ['co', 'de'])
        self.fake.save(self.DOMAIN, {'AppleLanguages': ['co', 'de', 'en']})
        self.assertTrue(settings.revert(self.record()))
        self.assertEqual(self.fake.load(self.DOMAIN), {'AppleLanguages': ['co', 'de', 'en']})
        # Removed by the person since: stays removed.
        settings.set_defaults_value(self.installer, 'app', self.DOMAIN, 'AppleLanguages', ['co', 'de'])
        self.fake.save(self.DOMAIN, {})
        self.assertTrue(settings.revert(self.record()))
        self.assertEqual(self.fake.load(self.DOMAIN), {})

    def test_unreadable_preferences_are_left_alone(self):
        def broken(command, **options):
            if command[1] == 'export':
                return subprocess.CompletedProcess(command, 1, b'', b'cfprefsd not answering')
            raise AssertionError('nothing written when the value cannot be read')
        with patch.object(subprocess, 'run', broken):
            with self.assertRaises(ValueError):
                settings.defaults_value(self.DOMAIN, 'AppleLanguages')
            with self.assertRaises(ValueError):
                settings.set_defaults_value(self.installer, 'app', self.DOMAIN, 'AppleLanguages', ['co'])
            self.assertEqual(self.installer.state['files'], {})
            record = {'setting': {'type': 'defaults-plist', 'domain': self.DOMAIN, 'key': 'AppleLanguages',
                                  'original': None, 'installed': settings.plist_fragment(['co'])}}
            self.assertFalse(settings.revert(record))  # kept, tried again later

        def garbage(command, **options):
            return subprocess.CompletedProcess(command, 0, b'not a plist', b'')
        with patch.object(subprocess, 'run', garbage), self.assertRaises(ValueError):
            settings.defaults_value(self.DOMAIN, 'AppleLanguages')

    def test_global_domain_is_never_written(self):
        for domain in ('NSGlobalDomain', '-g'):
            with self.assertRaises(ValueError):
                settings.set_defaults_value(self.installer, 'app', domain, 'AppleLanguages', ['co'])
            with self.assertRaises(ValueError):
                settings.defaults_write_value(domain, 'AppleLanguages', None)
        self.assertEqual(self.fake.writes, [])
        self.assertEqual(self.installer.state['files'], {})


ON_MAC_RUNNER = sys.platform == 'darwin' and os.environ.get('GITHUB_ACTIONS') == 'true'


@unittest.skipUnless(ON_MAC_RUNNER, 'real `defaults` only on a GitHub Actions macOS runner (throwaway machine)')
class RealMacTests(unittest.TestCase):
    """REAL macOS: `defaults` and NSLocale on a CI runner, throwaway domains only."""

    def setUp(self):
        self.domain = f'org.corsu.test.{uuid.uuid4().hex}'
        self.addCleanup(subprocess.run, ['defaults', 'delete', self.domain], capture_output=True)
        self.installer = Installer()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        state = patch.object(corsu, 'STATE', self.folder / 'state.json')
        state.start()
        self.addCleanup(state.stop)

    def test_array_written_read_and_given_back(self):
        subprocess.run(['defaults', 'write', self.domain, 'AppleLanguages', '-string', 'de'], check=True)
        settings.set_defaults_value(self.installer, 'app', self.domain, 'AppleLanguages', ['co', 'fr-FR'])
        self.assertEqual(settings.defaults_value(self.domain, 'AppleLanguages'), ['co', 'fr-FR'])
        read = subprocess.run(['defaults', 'read-type', self.domain, 'AppleLanguages'], capture_output=True, text=True)
        self.assertIn('array', read.stdout)
        record = self.installer.state['files'][f'defaults:{self.domain}:AppleLanguages']
        self.assertTrue(settings.revert(record))
        self.assertEqual(settings.defaults_value(self.domain, 'AppleLanguages'), 'de')
        subprocess.run(['defaults', 'delete', self.domain, 'AppleLanguages'], check=True)
        self.assertIsNone(settings.defaults_value(self.domain, 'AppleLanguages'))

    @unittest.skipUnless(shutil.which('swiftc'), 'no swiftc')
    def test_nslocale_puts_corsican_first_for_that_application_only(self):
        """What wxWidgets asks on macOS ([NSLocale preferredLanguages]) for a tool with its own bundle identifier."""
        info = self.folder / 'Info.plist'
        info.write_text('<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict>'
                        f'<key>CFBundleIdentifier</key><string>{self.domain}</string></dict></plist>')
        source = self.folder / 'main.swift'
        source.write_text('import Foundation\nprint(NSLocale.preferredLanguages.joined(separator: ","))\n')
        tool = self.folder / 'languages'
        subprocess.run(['swiftc', str(source), '-o', str(tool), '-Xlinker', '-sectcreate', '-Xlinker', '__TEXT',
                        '-Xlinker', '__info_plist', '-Xlinker', str(info)], check=True, capture_output=True)
        before = subprocess.run([str(tool)], capture_output=True, text=True, check=True).stdout.strip()
        settings.set_defaults_value(self.installer, 'app', self.domain, 'AppleLanguages', ['co', 'fr-FR'])
        after = subprocess.run([str(tool)], capture_output=True, text=True, check=True).stdout.strip()
        print(f'\nNSLocale.preferredLanguages before: {before}; with the per-application list: {after}')
        self.assertTrue(after.split(',')[0].startswith('co'), after)
        self.assertNotEqual(before.split(',')[0][:2], 'co')


if __name__ == '__main__':
    unittest.main()
