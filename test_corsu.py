import gettext
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import corsu


class TranslationTests(unittest.TestCase):
    def test_firefox_install_default_and_explicit_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            base = home / '.config/mozilla/firefox'
            (base / 'release').mkdir(parents=True)
            (base / 'other').mkdir()
            (base / 'profiles.ini').write_text(
                '[InstallABC]\nDefault=release\n[Profile0]\nPath=other\nDefault=1\n')
            with patch.object(corsu, 'HOME', home), patch.object(corsu, 'PLATFORM', 'linux'):
                self.assertEqual(corsu.firefox_profile(), base / 'release')
                self.assertEqual(corsu.firefox_arguments(['https://example.com']),
                                 ['-profile', str(base / 'release'), '-UILocale', 'en-US', 'https://example.com'])
                for selection in (['-P', 'work'], ['--profile=/tmp/custom'], ['-ProfileManager']):
                    self.assertEqual(corsu.firefox_arguments(selection), ['-UILocale', 'en-US', *selection])

    def test_firefox_legacy_absolute_and_missing_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            base = home / '.mozilla/firefox'
            base.mkdir(parents=True)
            profile = home / 'custom'
            profile.mkdir()
            with patch.object(corsu, 'HOME', home), patch.object(corsu, 'PLATFORM', 'linux'):
                for content in (f'[Profile0]\nDefault=1\nIsRelative=0\nPath={profile}\n',
                                f'[InstallABC]\nDefault={profile}\n'):
                    (base / 'profiles.ini').write_text(content)
                    self.assertEqual(corsu.firefox_profile(), profile)
                (base / 'profiles.ini').write_text('[InstallABC]\nDefault=missing\n')
                self.assertEqual(corsu.firefox_arguments([]), ['-ProfileManager', '-UILocale', 'en-US'])
                (base / 'profiles.ini').write_text('[InstallABC]\nDefault=one\n[InstallDEF]\nDefault=two\n')
                self.assertIsNone(corsu.firefox_profile())

    def test_firefox_profiles_on_windows_and_macos(self):
        for platform, relative in (('windows', 'Mozilla/Firefox'), ('macos', 'Firefox')):
            with tempfile.TemporaryDirectory() as directory, patch.object(corsu, 'PLATFORM', platform), \
                    patch.object(corsu, 'CONFIG', Path(directory)):
                base = Path(directory) / relative
                (base / 'Profiles/abc.default-release').mkdir(parents=True)
                (base / 'profiles.ini').write_text('[InstallXYZ]\nDefault=Profiles/abc.default-release\n')
                self.assertEqual(corsu.firefox_profile(), base / 'Profiles/abc.default-release')

    def test_status_checks_owned_settings_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(corsu, 'DATA', root / 'data'), patch.object(corsu, 'STATE', root / 'data/state.json'), patch.object(corsu, 'HOME', root):
                settings = root / 'settings.json'
                corsu.Installer().json_settings(settings, {'plugins/Corsu/enabled': True})
                document = json.loads(settings.read_text(encoding='utf-8'))
                document['windowWidth'] = 1200
                settings.write_text(json.dumps(document))
                before = corsu.STATE.read_bytes()
                output = io.StringIO()
                with redirect_stdout(output):
                    corsu.status()
                self.assertEqual(json.loads(output.getvalue())['installation']['changed'], [])
                self.assertEqual(corsu.STATE.read_bytes(), before)
                document['plugins']['Corsu']['enabled'] = False
                settings.write_text(json.dumps(document))
                output = io.StringIO()
                with redirect_stdout(output):
                    corsu.status()
                self.assertEqual(json.loads(output.getvalue())['installation']['changed'],
                                 [f'{settings}: plugins/Corsu/enabled'])

    def test_disable_reverts_switches_and_enable_restores_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(corsu, 'DATA', root / 'data'), patch.object(corsu, 'STATE', root / 'data/state.json'):
                language = root / 'plasma-localerc'
                language.write_text('[Translations]\nLANGUAGE=fr\n')
                catalog = root / 'catalog.mo'
                settings = root / 'settings.json'
                installer = corsu.Installer()
                installer.write(language, '[Translations]\nLANGUAGE=co:fr\n', toggle=True)
                installer.write(catalog, b'catalog data')
                installer.json_settings(settings, {'plugins/Corsu/enabled': True, 'autoUpdate': False}, toggle=True)
                corsu.STATE.write_text(json.dumps({**installer.state, 'components': ['desktop']}, indent=2))

                output = io.StringIO()
                with redirect_stdout(output):
                    corsu.disable()
                self.assertEqual(language.read_text(encoding='utf-8'), '[Translations]\nLANGUAGE=fr\n')
                self.assertEqual(json.loads(settings.read_text(encoding='utf-8'))['plugins']['Corsu']['enabled'], False)
                self.assertEqual(json.loads(settings.read_text(encoding='utf-8'))['autoUpdate'], False)
                # Built catalogs stay in place, so switching back needs no rebuild.
                self.assertEqual(catalog.read_bytes(), b'catalog data')
                self.assertTrue(corsu.disabled_marker().exists())
                self.assertFalse(json.loads(corsu.STATE.read_text(encoding='utf-8'))['enabled'])

                with patch.object(corsu, 'kde') as kde, patch.object(corsu, 'desktop'), redirect_stdout(io.StringIO()):
                    kde.return_value = {'catalogs': 1}
                    corsu.enable()
                self.assertFalse(corsu.disabled_marker().exists())
                self.assertTrue(json.loads(corsu.STATE.read_text(encoding='utf-8'))['enabled'])

    def test_exact_labels_only(self):
        self.assertEqual(corsu.translate('  &Save…  '), '  &Salvà…  ')
        self.assertEqual(corsu.translate('_Save'), '_Salvà')
        self.assertEqual(corsu.translate('Save my private message'), 'Save my private message')
        self.assertEqual(corsu.translate('Nonexistent %1'), 'Nonexistent %1')

    def test_fluent_expressions_and_keys_preserved(self):
        source = 'save =\n    .label = Save\n    .accesskey = S\ncount = { $count } files\n'
        translated, count = corsu.patch_ftl(source)
        self.assertEqual(count, 1)
        self.assertIn('.label = Salvà', translated)
        self.assertIn('.accesskey = S', translated)
        self.assertIn('count = { $count } files', translated)

    def test_french_pack_from_other_version_merges_by_message(self):
        english = '# note\n\nkept = New only\n\nshared = Hello\n    .title = Hi\n\nfooter = Bye\n'
        french = 'shared = Bonjour\n    .title = Salut\nremoved = Ancien\nfooter = Au revoir\n'
        merged, count = corsu.merge_ftl(english, french)
        self.assertEqual(count, 2)
        self.assertEqual(merged, '# note\n\nkept = New only\n\nshared = Bonjour\n    .title = Salut\n\nfooter = Au revoir\n')

    def test_french_properties_merge_by_key(self):
        merged, count = corsu.merge_properties('# c\nkept=Keep\nshared=Hello %S\n', 'shared=Bonjour %S\ngone=x\n')
        self.assertEqual((merged, count), ('# c\nkept=Keep\nshared=Bonjour %S\n', 1))

    def test_french_pack_directories_follow_the_chrome_manifest(self):
        import zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as bundle:
            bundle.writestr('chrome/chrome.manifest', 'locale global en-US en-US/locale/en-US/global/\n'
                            'locale global-platform en-US en-US/locale/en-US/global-platform/win/ os=WINNT\n'
                            'locale global-platform en-US en-US/locale/en-US/global-platform/unix/ os=LikeUnix\n')
        manifest = {'languages': {'fr': {'chrome_resources': {
            'global': 'chrome/fr/locale/fr/global/',
            'global-platform': {'win': 'chrome/fr/win/', 'linux': 'chrome/fr/unix/'}}}}}
        with zipfile.ZipFile(buffer) as bundle, patch.object(corsu, 'PLATFORM', 'windows'):
            self.assertEqual(corsu.locale_directories(bundle, manifest), {
                'chrome/en-US/locale/en-US/global/': 'chrome/fr/locale/fr/global/',
                'chrome/en-US/locale/en-US/global-platform/win/': 'chrome/fr/win/'})

    def test_gettext_context_and_fallback(self):
        data = corsu.make_mo({'': 'Content-Type: text/plain; charset=UTF-8\nLanguage: co\n',
                              'Save': 'Salvà', 'button\x04Close': 'Chjode'})
        loaded = gettext.GNUTranslations(io.BytesIO(data))
        self.assertEqual(loaded.gettext('Save'), 'Salvà')
        self.assertEqual(loaded.pgettext('button', 'Close'), 'Chjode')
        self.assertEqual(loaded.gettext('Unknown'), 'Unknown')

    def test_backup_reinstall_restore_and_user_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'data/state.json'
            with patch.object(corsu, 'DATA', root / 'data'), patch.object(corsu, 'STATE', state):
                existing = root / 'settings.json'
                existing.write_text('original')
                created = root / 'new'
                installer = corsu.Installer()
                installer.write(existing, 'installed')
                installer.write(created, 'new file')
                corsu.Installer().write(existing, 'updated')
                self.assertEqual(Path(json.loads(state.read_text(encoding='utf-8'))['files'][str(existing)]['backup']).read_text(encoding='utf-8'), 'original')
                created.write_text('user edit')
                with self.assertRaises(RuntimeError):
                    corsu.Installer().write(created, 'overwrite')
                corsu.uninstall()
                self.assertEqual(existing.read_text(encoding='utf-8'), 'original')
                self.assertEqual(created.read_text(encoding='utf-8'), 'user edit')

    def test_restore_app_settings_preserves_later_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(corsu, 'DATA', root / 'data'), patch.object(corsu, 'STATE', root / 'data/state.json'):
                settings = root / 'settings.json'
                settings.write_text(json.dumps({'windowWidth': 800, 'autoUpdate': True}))
                corsu.Installer().json_settings(settings, {'autoUpdate': False, 'plugins/Corsu/enabled': True})
                changed = json.loads(settings.read_text(encoding='utf-8'))
                changed['windowWidth'] = 1200
                settings.write_text(json.dumps(changed))
                corsu.uninstall()
                restored = json.loads(settings.read_text(encoding='utf-8'))
                self.assertEqual(restored['windowWidth'], 1200)
                self.assertTrue(restored['autoUpdate'])
                self.assertNotIn('enabled', restored['plugins']['Corsu'])


if __name__ == '__main__':
    unittest.main()
