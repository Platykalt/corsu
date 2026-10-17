import gettext
import io
import json
import os
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

    def test_firefox_copy_follows_the_system_formats_by_default_only(self):
        # Measured in Firefox 157: in defaults/pref the browser's own default (false) is read later and wins, and the
        # copy then shows "11:32 AM" on a French or German system. browser/defaults/preferences is read after it.
        with tempfile.TemporaryDirectory() as directory:
            resources = Path(directory)
            corsu.regional_formats(resources)
            text = (resources / 'browser/defaults/preferences/corsu.js').read_text(encoding='utf-8')
            self.assertEqual(text, 'pref("intl.regional_prefs.use_os_locales", true);\n')
            # A default, never a user value or a locked one: the user's own choice in the profile keeps priority.
            self.assertNotIn('user_pref', text)
            self.assertNotIn('lockPref', text)
            self.assertFalse((resources / 'defaults').exists())

    def test_install_sections_match_firefox(self):
        # Sections Firefox wrote itself, for its usual folders on Linux and Windows and for a long path.
        self.assertEqual(corsu.install_section('/usr/lib/firefox'), 'Install4F96D1932A9F858E')
        self.assertEqual(corsu.install_section('C:\\Program Files\\Mozilla Firefox'), 'Install308046B0AF4A39CB')
        self.assertEqual(corsu.install_section('/home/kalt/.local/share/corsu/firefox/d28cdbade330decb'),
                         'Install964A175157EB0296')

    def test_system_firefox_profile_wins_and_copies_open_it(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            base = home / '.config/mozilla/firefox'
            for name in ('mine', 'empty'):
                (base / name).mkdir(parents=True)
            system = corsu.FirefoxInstall(home / 'firefox')
            (base / 'profiles.ini').write_text(
                f'[Profile0]\nPath=mine\n\n[{corsu.install_section(system.root)}]\nDefault=mine\nLocked=1\n\n'
                '[InstallDD1636AE193E3CB3]\nDefault=empty\nLocked=1\n')
            with patch.object(corsu, 'HOME', home), patch.object(corsu, 'PLATFORM', 'linux'), \
                    patch.object(corsu, 'firefox_install', return_value=system):
                self.assertEqual(corsu.firefox_profile(), base / 'mine')
                copy = home / 'data/firefox/abc'
                corsu.link_profile(copy, base / 'mine')
                for name in ('profiles.ini', 'installs.ini'):
                    text = (base / name).read_text()
                    self.assertIn(f'[{corsu.install_section(copy)}]\nDefault=mine\nLocked=1\n', text)
                self.assertIn('[Profile0]\nPath=mine\n', (base / 'profiles.ini').read_text())
                corsu.unlink_profile(copy)
                self.assertNotIn(corsu.install_section(copy), (base / 'profiles.ini').read_text())

    def test_default_browser_entry_of_a_copy_is_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            applications = home / '.local/share/applications'
            applications.mkdir(parents=True)
            (applications / 'firefox.desktop').write_text('[Desktop Entry]\nIcon=firefox\n')
            data = home / '.local/share/corsu'
            (applications / 'userapp-Firefox-AB12.desktop').write_text(
                f'[Desktop Entry]\nExec={data}/firefox/0123/firefox %u\nNoDisplay=true\n')
            (applications / 'userapp-Other-CD34.desktop').write_text('[Desktop Entry]\nExec=/usr/bin/other %u\n')
            mimeapps = home / '.config/mimeapps.list'
            mimeapps.parent.mkdir()
            mimeapps.write_text('[Default Applications]\nx-scheme-handler/https=userapp-Firefox-AB12.desktop\n'
                                '[Added Associations]\ntext/html=userapp-Firefox-AB12.desktop;firefox.desktop;\n')
            with patch.object(corsu, 'HOME', home), patch.object(corsu, 'PLATFORM', 'linux'), \
                    patch.object(corsu, 'DATA', data), patch.object(corsu, 'CONFIG', home / '.config'):
                corsu.repair_default_browser()
            self.assertEqual(mimeapps.read_text(), '[Default Applications]\nx-scheme-handler/https=firefox.desktop\n'
                                                   '[Added Associations]\ntext/html=firefox.desktop;\n')
            self.assertFalse((applications / 'userapp-Firefox-AB12.desktop').exists())
            self.assertTrue((applications / 'userapp-Other-CD34.desktop').exists())

    def test_default_browser_is_repaired_by_corsu_itself_not_only_by_the_launcher(self):
        # The entry Firefox wrote on a real computer: it starts the copy directly, so the launcher's repair never ran,
        # and the taskbar's browser button showed a blank page. Switching off or removing Corsu must still fix it,
        # even when only the system has a firefox.desktop left.
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            data = home / '.local/share/corsu'
            applications = home / '.local/share/applications'
            applications.mkdir(parents=True)
            userapp = applications / 'userapp-Firefox-DQPWW3.desktop'
            userapp.write_text('[Desktop Entry]\nEncoding=UTF-8\nVersion=1.0\nType=Application\nNoDisplay=true\n'
                               f'Exec={data}/firefox/fbf656f92f218836/firefox %u\nName=Firefox\n'
                               'Comment=Définition personnalisée pour Firefox\n', encoding='utf-8')
            mimeapps = home / '.config/mimeapps.list'
            mimeapps.parent.mkdir()
            mimeapps.write_text('[Added Associations]\nx-scheme-handler/https=userapp-Firefox-DQPWW3.desktop;firefox.desktop;\n'
                                '[Default Applications]\nx-scheme-handler/https=userapp-Firefox-DQPWW3.desktop\n'
                                'x-scheme-handler/discord=vesktop.desktop\n', encoding='utf-8')
            data.mkdir(parents=True)
            (data / 'state.json').write_text('{"files": {}}', encoding='utf-8')
            system = Path('/usr/share/applications/firefox.desktop')
            exists = Path.exists
            with patch.object(corsu, 'HOME', home), patch.object(corsu, 'DATA', data), \
                    patch.object(corsu, 'STATE', data / 'state.json'), patch.object(corsu, 'CONFIG', home / '.config'), \
                    patch.object(corsu, 'PLATFORM', 'linux'), redirect_stdout(io.StringIO()), \
                    patch.object(Path, 'exists', lambda path: path == system or exists(path)):
                corsu.uninstall()
            self.assertFalse(userapp.exists())
            self.assertEqual(mimeapps.read_text(encoding='utf-8'),
                             '[Added Associations]\nx-scheme-handler/https=firefox.desktop;\n'
                             '[Default Applications]\nx-scheme-handler/https=firefox.desktop\n'
                             'x-scheme-handler/discord=vesktop.desktop\n')

    def test_interrupted_state_write_keeps_the_way_back(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            state = data / 'installation.json'
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', state):
                corsu.save_state({'files': {'/a': {'backup': '/b'}}})
                corsu.save_state({'files': {'/a': {'backup': '/b'}, '/c': {'backup': None}}})
                # A power cut while an older version wrote the file in place left half of it.
                state.write_text('{"files": {"/a": {"back', encoding='utf-8')
                with redirect_stdout(io.StringIO()), patch('sys.stderr', io.StringIO()) as errors:
                    self.assertEqual(corsu.load_state(), {'files': {'/a': {'backup': '/b'}}})
                self.assertIn('installation.json', errors.getvalue())
                (data / 'installation.json.previous').write_text('{', encoding='utf-8')
                with patch('sys.stderr', io.StringIO()), self.assertRaises(RuntimeError):
                    corsu.load_state()
                self.assertEqual(state.read_text(encoding='utf-8'), '{"files": {"/a": {"back')

    def test_interrupted_downloads_and_copies_are_never_taken_as_complete(self):
        import zipfile
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            # A language pack cut short by a lost connection used to be reused at every start.
            cache = data / 'langpacks/fr-150.0.xpi'
            cache.parent.mkdir(parents=True)
            cache.write_bytes(b'PK\x03\x04 cut short')
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'ROOT', data / 'release'), \
                    patch.object(corsu.urllib.request, 'urlopen', side_effect=OSError('network is unreachable')):
                self.assertIsNone(corsu.french_pack('150.0'))
            # Replacing an installed application: a failed copy leaves the working one in place.
            application = data / 'Applications/Firefox.app'
            (application / 'Contents').mkdir(parents=True)
            (application / 'Contents/firefox').write_text('working')
            source = data / 'new.app'
            (source / 'Contents').mkdir(parents=True)
            (source / 'Contents/firefox').write_text('new')
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', data / 'installation.json'):
                installer = corsu.Installer()
                installer.state['files'][str(application)] = {'tree': True}
                with patch.object(corsu.shutil, 'copytree', side_effect=OSError('disk full')), self.assertRaises(OSError):
                    installer.tree(application, source)
                self.assertEqual((application / 'Contents/firefox').read_text(), 'working')
                installer.tree(application, source)
                self.assertEqual((application / 'Contents/firefox').read_text(), 'new')
                self.assertEqual(sorted(path.name for path in application.parent.iterdir()), ['Firefox.app'])
            self.assertFalse(zipfile.is_zipfile(cache))

    def test_old_firefox_copies_are_removed_unless_running(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            for name in ('current', 'old', 'running'):
                (data / 'firefox' / name).mkdir(parents=True)
            running = {str(data / 'firefox/running/firefox')}
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'running_executables', return_value=running), \
                    patch.object(corsu, 'firefox_install', return_value=corsu.FirefoxInstall(data)), \
                    patch.object(corsu, 'PLATFORM', 'linux'), patch.object(corsu, 'HOME', data):
                corsu.prune_runtimes(data / 'firefox/current')
            self.assertEqual(sorted(path.name for path in (data / 'firefox').iterdir()), ['current', 'running'])

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
        self.assertEqual(corsu.translate('  &Save…  '), '  &Arregistrà…  ')
        self.assertEqual(corsu.translate('_Save'), 'Arregi_strà')
        self.assertEqual(corsu.translate('Save my private message'), 'Save my private message')
        self.assertEqual(corsu.translate('Nonexistent %1'), 'Nonexistent %1')

    def test_fluent_expressions_and_keys_preserved(self):
        source = 'save =\n    .label = Save\n    .accesskey = S\ncount = { $count } zzz-untranslated\n'
        translated, count = corsu.patch_ftl(source)
        self.assertEqual(count, 1)
        self.assertIn('.label = Arregistrà', translated)
        self.assertIn('.accesskey = S', translated)
        self.assertIn('count = { $count } zzz-untranslated', translated)

    def test_french_pack_from_other_version_merges_by_message(self):
        english = '# note\n\nkept = New only\n\nshared = Hello\n    .title = Hi\n\nfooter = Bye\n'
        french = 'shared = Bonjour\n    .title = Salut\nremoved = Ancien\nfooter = Au revoir\n'
        merged, count = corsu.merge_ftl(english, french)
        self.assertEqual(count, 2)
        self.assertEqual(merged, '# note\n\nkept = New only\n\nshared = Bonjour\n    .title = Salut\n\nfooter = Au revoir\n')

    def test_french_properties_merge_by_key(self):
        merged, count = corsu.merge_properties('# c\nkept=Keep\nshared=Hello %S\n', 'shared=Bonjour %S\ngone=x\n')
        self.assertEqual((merged, count), ('# c\nkept=Keep\nshared=Bonjour %S\n', 1))

    def test_firefox_copy_is_rebuilt_when_the_translation_engine_changes(self):
        # A fix in engine.py (such as Mozilla's %S arguments) must reach copies built before it.
        self.assertIn(Path(corsu.engine.__file__).resolve(), corsu.FIREFOX_BUILD_CODE)
        self.assertIn(Path(corsu.__file__).resolve(), corsu.FIREFOX_BUILD_CODE)

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

    def test_system_catalogs_never_overwrite_package_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            user = root / 'home/.local/share/locale/co/LC_MESSAGES'
            user.mkdir(parents=True)
            (user / 'gtk30.mo').write_bytes(b'ours')
            (user / 'packaged.mo').write_bytes(b'ours')
            system = root / 'usr/share/locale/co/LC_MESSAGES'
            system.mkdir(parents=True)
            (system / 'packaged.mo').write_bytes(b'from a package')
            qt = root / 'qt'
            qt.mkdir()
            with patch.object(corsu, 'HOME', root / 'home'), patch.object(corsu, 'DATA', root / 'data'), \
                    patch.object(corsu, 'STATE', root / 'data/state.json'), patch.object(corsu, 'SYSTEM_LOCALE', system), \
                    patch.object(corsu, 'QT_TRANSLATIONS', qt), redirect_stdout(io.StringIO()):
                installer = corsu.Installer()
                self.assertEqual(corsu.system_catalogs(installer), ['gtk30.mo'])
                self.assertEqual((system / 'gtk30.mo').read_bytes(), b'ours')
                self.assertEqual((system / 'packaged.mo').read_bytes(), b'from a package')
                corsu.uninstall()
                self.assertFalse((system / 'gtk30.mo').exists())
                self.assertTrue((system / 'packaged.mo').exists())

    def test_parts_switch_off_and_on_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / 'config/Vencord/settings/settings.json'
            with patch.object(corsu, 'HOME', root), patch.object(corsu, 'DATA', root / 'data'), \
                    patch.object(corsu, 'STATE', root / 'data/state.json'), patch.object(corsu, 'CONFIG', root / 'config'), \
                    patch.object(corsu, 'PLATFORM', 'linux'), redirect_stdout(io.StringIO()):
                installer = corsu.Installer()
                installer.json_settings(settings, {'plugins/Corsu/enabled': True}, toggle=True)
                installer.state['components'] = ['discord', 'desktop']
                corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
                corsu.disable(['terminal'], hours=1)
                self.assertTrue(corsu.is_disabled('terminal'))
                self.assertFalse(corsu.is_disabled('discord'))
                self.assertTrue(json.loads(settings.read_text())['plugins']['Corsu']['enabled'])
                corsu.disable(['discord'])
                self.assertFalse(json.loads(settings.read_text())['plugins']['Corsu']['enabled'])
                self.assertTrue(corsu.is_disabled('discord'))
                with patch.object(corsu, 'install') as install:
                    corsu.enable(['terminal'])
                    install.assert_not_called()
                self.assertFalse(corsu.is_disabled('terminal'))
                self.assertTrue(corsu.is_disabled('discord'))

    def test_google_module_is_built_into_the_firefox_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            resources = Path(directory)
            corsu.google_labels(resources)
            config = (resources / 'corsu.cfg').read_text(encoding='utf-8')
            self.assertIn('"google.fr"', config)
            self.assertNotIn('HOSTS', config)
        modules = corsu.google_modules()
        self.assertIn(b'export function translatePage', modules['CorsuChild.sys.mjs'])
        self.assertIn('Riassuntu IA', modules['dictionary.mjs'].decode())
        self.assertTrue(modules['dictionary.mjs'].startswith(b'export const words = {'))

    def test_gettext_context_and_fallback(self):
        data = corsu.make_mo({'': 'Content-Type: text/plain; charset=UTF-8\nLanguage: co\n',
                              'Save': 'Arregistrà', 'button\x04Close': 'Chjode'})
        loaded = gettext.GNUTranslations(io.BytesIO(data))
        self.assertEqual(loaded.gettext('Save'), 'Arregistrà')
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

    def test_launchers_follow_the_current_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            # Reached through a link, like /var -> /private/var on macOS or a short name on Windows: launchers hold
            # the path as written, which differs from the real one.
            (Path(directory) / 'real').mkdir()
            try:
                (Path(directory) / 'link').symlink_to(Path(directory) / 'real', target_is_directory=True)
                data = Path(directory) / 'link/data'
            except OSError:
                data = Path(directory) / 'real/data'
            current = data / 'releases/0123456789abcdef'
            (current / 'src').mkdir(parents=True)
            launcher = Path(directory) / 'firefox-corsu'
            old = data / 'releases/fedcba9876543210/src/corsu.py'
            state = data / 'installation.json'
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', state), \
                    patch.object(corsu, 'ROOT', current.resolve()):
                installer = corsu.Installer()
                installer.write(launcher, f'#!/bin/sh\nexec python3 {old} launch-firefox "$@"\n', 0o755)
                edited = Path(directory) / 'edited.desktop'
                installer.write(edited, f'Exec=python3 {old}\n')
                edited.write_text(f'Exec=python3 {old} --mine\n')
                corsu.refresh_launchers(installer)
                self.assertIn(str(current / 'src/corsu.py'), launcher.read_text())
                if os.name != 'nt':
                    self.assertEqual(launcher.stat().st_mode & 0o777, 0o755)
                # A file the user changed is left as it is.
                self.assertIn(str(old), edited.read_text())


class OriginalsKeptTests(unittest.TestCase):
    """A repair or an update runs every step again over what Corsu already changed: the value recorded as original
    stays the one found before the first change, never one Corsu wrote."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        for name, value in (('HOME', self.root), ('DATA', self.root / 'data'), ('CONFIG', self.root / 'config'),
                            ('STATE', self.root / 'data/installation.json'), ('repair_default_browser', lambda: None)):
            patcher = patch.object(corsu, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_backup_of_a_file(self):
        path = self.root / 'file.txt'
        path.write_text('original', encoding='utf-8')
        for run in range(3):
            corsu.Installer().write(path, f'corsu {run}')
        record = corsu.load_state()['files'][str(path)]
        self.assertEqual(Path(record['backup']).read_text(encoding='utf-8'), 'original')
        with redirect_stdout(io.StringIO()):
            corsu.uninstall()
        self.assertEqual(path.read_text(encoding='utf-8'), 'original')

    def test_json_settings(self):
        path = self.root / 'settings.json'
        path.write_text(json.dumps({'autoUpdate': True}), encoding='utf-8')
        for run in range(3):
            corsu.Installer().json_settings(path, {'autoUpdate': False, 'plugins/Corsu/enabled': True})
        saved = corsu.load_state()['files'][str(path)]['json_changes']
        self.assertEqual(saved['autoUpdate'], {'existed': True, 'original': True, 'installed': False})
        self.assertFalse(saved['plugins/Corsu/enabled']['existed'])
        with redirect_stdout(io.StringIO()):
            corsu.uninstall()
        self.assertEqual(json.loads(path.read_text(encoding='utf-8')), {'autoUpdate': True, 'plugins': {'Corsu': {}}})

    def test_program_settings(self):
        from apps import settings
        path = self.root / 'program.ini'
        path.write_text('[General]\nLanguage=fr\n', encoding='utf-8')
        for run in range(3):
            settings.set_ini(corsu.Installer(), 'vlc', path, 'General', 'Language', 'co')
        record = next(record for name, record in corsu.load_state()['files'].items() if name.startswith(str(path)))
        self.assertEqual((record['setting']['original'], record['setting']['installed']), ('fr', 'co'))
        settings.revert(record)
        self.assertIn('Language=fr', path.read_text(encoding='utf-8'))

    def test_minecraft_options(self):
        import minecraft
        folder = self.root / 'game'
        (folder / 'resourcepacks').mkdir(parents=True)
        (folder / 'options.txt').write_text('lang:en_us\nresourcePacks:["vanilla"]\n', encoding='utf-8')
        for run in range(3):
            self.assertIsNone(minecraft.install_folder(corsu.Installer(), folder, b'pack'))
        record = corsu.load_state()['files'][str(folder / 'options.txt')]
        self.assertEqual(record['options_original']['lang'], 'en_us')
        self.assertTrue(minecraft.revert(folder / 'options.txt', record))
        self.assertIn('lang:en_us', (folder / 'options.txt').read_text(encoding='utf-8'))

    def test_menu_entry_override(self):
        applications = self.root / '.local/share/applications'
        applications.mkdir(parents=True)
        mine = '[Desktop Entry]\nName=Firefox\nExec=firefox %u\n'
        (applications / 'firefox.desktop').write_text(mine, encoding='utf-8')
        with patch.object(corsu, 'PLATFORM', 'linux'):
            for run in range(3):
                corsu.desktop(corsu.Installer(), firefox=True, vesktop=False)
        entry = (applications / 'firefox.desktop').read_text(encoding='utf-8')
        self.assertIn('Name=Firefox Corsu', entry)
        self.assertEqual(entry.count('Name[co]='), 1)
        with redirect_stdout(io.StringIO()):
            corsu.uninstall()
        self.assertEqual((applications / 'firefox.desktop').read_text(encoding='utf-8'), mine)


if __name__ == '__main__':
    unittest.main()
