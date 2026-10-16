import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import corsu
import installer


def R(name):
    """A release folder name as Corsu makes them (16 hexadecimal digits), for a readable label."""
    import hashlib
    return hashlib.sha256(name.encode()).hexdigest()[:16]


def names(*labels):
    return sorted(R(label) for label in labels)


def genuine(folder, version='0.22.0'):
    (folder / 'src').mkdir(parents=True, exist_ok=True)
    (folder / 'src/release.json').write_text(json.dumps({'version': version}), encoding='utf-8')
    return folder


class Isolated(unittest.TestCase):
    """Every path Corsu writes (home, data, settings, Start menu) in a temporary folder: tests that run the installer
    never touch the real installation, its launchers or its record."""

    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name).resolve()
        self.data = self.home / 'data'
        self.config = self.home / 'config'
        for name, value in (('HOME', self.home), ('DATA', self.data), ('CONFIG', self.config),
                            ('STATE', self.data / 'installation.json'), ('START_MENU', self.home / 'start')):
            patcher = patch.object(corsu, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        environment = patch.dict(os.environ, {'CORSU_LOCK_WAIT': '0.5'})
        environment.start()
        self.addCleanup(environment.stop)
        for name in ('CORSU_LOCK_TOKEN', 'CORSU_DEPLOYED', 'CORSU_APP_ROOT', 'CORSU_DOWNLOAD_BASE'):
            os.environ.pop(name, None)

    def release(self, version, name=None, files=None):
        """A Corsu release folder as deploy_release makes them: fingerprint name, src/release.json inside."""
        import hashlib
        name = name or hashlib.sha256(version.encode()).hexdigest()[:16]
        folder = self.data / 'releases' / name
        (folder / 'src').mkdir(parents=True, exist_ok=True)
        (folder / 'src/release.json').write_text(json.dumps({'version': version}), encoding='utf-8')
        for relative, text in (files or {}).items():
            (folder / relative).parent.mkdir(parents=True, exist_ok=True)
            (folder / relative).write_text(text, encoding='utf-8')
        return folder


class InstallerTests(Isolated):
    def test_declining_or_previewing_makes_no_changes(self):
        for arguments, consent in (([], 'no'), (['--dry-run'], None)):
            with patch.object(installer, 'available_components', return_value=['firefox']), \
                 patch.object(installer, 'discord_location', return_value=None), \
                 patch.object(installer, 'deploy_release') as deploy, \
                 patch.object(corsu, 'install') as install, \
                 patch('builtins.input', return_value=consent) as question, redirect_stdout(io.StringIO()):
                self.assertEqual(installer.main(arguments), 0)
                deploy.assert_not_called()
                install.assert_not_called()
                if consent is None:
                    question.assert_not_called()

    def test_only_selected_components_are_installed(self):
        with patch.object(installer, 'available_components', return_value=['firefox', 'desktop', 'discord']), \
             patch.object(installer, 'discord_location', return_value=Path('/fake/discord')), \
             patch.object(installer, 'deploy_release', return_value=installer.ROOT), \
             patch.object(installer, 'prepare_build') as build, \
             patch.object(installer, 'install_discord') as discord, \
             patch.object(corsu, 'install') as install, patch.object(corsu, 'firefox_install', return_value=True), \
             patch.object(installer.shutil, 'which', return_value=None), redirect_stdout(io.StringIO()):
            installer.main(['--yes', '--components', 'firefox'])
            install.assert_called_once_with({'firefox'}, qt_system=False)
            discord.assert_not_called()
            build.assert_not_called()

    def test_external_archive_is_restored_and_later_edits_preserved(self):
        for user_edit in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with patch.object(corsu, 'DATA', root / 'data'), patch.object(corsu, 'STATE', root / 'data/state.json'), redirect_stdout(io.StringIO()):
                    archive = root / 'app.asar'
                    archive.write_bytes(b'patched archive')
                    corsu.Installer().external_file(archive, b'original archive')
                    if user_edit:
                        archive.write_bytes(b'user archive')
                    corsu.uninstall()
                    self.assertEqual(archive.read_bytes(), b'user archive' if user_edit else b'original archive')

    def test_discord_checksum_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'vendor').mkdir()
            (root / 'vendor/VencordInstallerCli').write_bytes(b'bad binary')
            entry = {'file': 'VencordInstallerCli', 'sha256': 'invalid'}
            (root / 'src').mkdir()
            (root / 'src/release.json').write_text(json.dumps({
                'installer_base_url': 'https://invalid/', 'installers': {name: entry for name in ('linux', 'windows', 'macos')}}))
            with patch.object(installer, 'ROOT', root), patch.object(installer, 'run') as run, \
                 patch.object(installer.platform, 'machine', return_value='x86_64'):
                with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                    installer.install_discord(root / 'discord')
                run.assert_not_called()

    def test_menu_toggles_detected_components(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(corsu, 'STATE', Path(directory) / 'state.json'), \
             patch('builtins.input', side_effect=['2', '']), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(installer.choose(['firefox', 'discord', 'vesktop']), ['firefox', 'vesktop'])
            self.assertIn('Select what you want to translate:', output.getvalue())
        with patch('builtins.input', return_value='q'), redirect_stdout(io.StringIO()):
            self.assertEqual(installer.choose(['firefox']), [])

    def test_interactive_run_installs_only_the_chosen_components(self):
        with patch.object(installer, 'available_components', return_value=['firefox', 'vesktop']), \
             patch.object(installer, 'discord_location', return_value=None), \
             patch.object(installer, 'deploy_release', return_value=installer.ROOT), \
             patch.object(installer, 'prepare_build'), patch.object(installer.sys.stdin, 'isatty', return_value=True), \
             patch.object(corsu, 'install') as install, patch.object(corsu, 'firefox_install', return_value=True), \
             patch('builtins.input', side_effect=['2', '', 'y']), redirect_stdout(io.StringIO()):
            installer.main([])
            install.assert_called_once_with({'firefox'}, qt_system=False)

    def test_discord_archive_per_platform(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for version in ('1.0.9', '1.0.10'):
                (root / f'app-{version}/resources').mkdir(parents=True)
                (root / f'app-{version}/resources/app.asar').write_bytes(b'')
            with patch.object(corsu, 'PLATFORM', 'windows'):
                self.assertEqual(installer.discord_archive(root), root / 'app-1.0.10/resources/app.asar')
            with patch.object(corsu, 'PLATFORM', 'macos'):
                self.assertEqual(installer.discord_archive(root), root / 'Contents/Resources/app.asar')
            with patch.object(corsu, 'PLATFORM', 'linux'):
                self.assertEqual(installer.discord_archive(root), root / 'resources/app.asar')

    def test_release_pins_an_installer_for_every_platform(self):
        manifest = json.loads((installer.ROOT / 'src/release.json').read_text(encoding='utf-8'))
        for name in ('linux', 'windows', 'macos'):
            self.assertRegex(manifest['installers'][name]['sha256'], r'^[0-9a-f]{64}$')

    def test_deployed_copy_is_recognised_through_symlinked_or_short_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            real = Path(directory).resolve() / 'data'
            (real / 'releases/abc').mkdir(parents=True)
            alias = Path(directory) / 'alias'
            try:
                alias.symlink_to(real)
            except OSError:
                self.skipTest('Symbolic links need extra rights on this system')
            with patch.object(corsu, 'DATA', alias), patch.object(installer, 'ROOT', real / 'releases/abc'):
                self.assertEqual(installer.deploy_release(), real / 'releases/abc')

    def test_every_linux_discord_version_is_found(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for version in ('1.0.159', '1.0.160'):
                (root / f'app-{version}/resources').mkdir(parents=True)
                (root / f'app-{version}/resources/app.asar').write_bytes(b'')
            with patch.object(corsu, 'PLATFORM', 'linux'):
                self.assertEqual(installer.sibling_versions(root / 'app-1.0.160'), [root / 'app-1.0.159'])


    def test_old_releases_are_deleted_unless_something_loads_them(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data'
            for name in ('current', 'old', 'discord', 'vesktop'):
                genuine(data / 'releases' / R(name))
            asar = Path(directory) / 'app.asar'
            asar.write_text(f'require("{data / "releases" / R("discord") / "Vencord/dist/patcher.js"}")')
            config = Path(directory) / 'config'
            (config / 'vesktop').mkdir(parents=True)
            (config / 'vesktop/state.json').write_text(json.dumps({'vencordDir': str(data / 'releases' / R('vesktop') / 'Vencord/dist')}))
            state = data / 'installation.json'
            state.write_text(json.dumps({'files': {str(asar): {}}}))
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', state), patch.object(corsu, 'CONFIG', config):
                installer.prune_releases(data / 'releases' / R('current'))
            self.assertEqual(sorted(path.name for path in (data / 'releases').iterdir()), names('current', 'discord', 'vesktop'))

    def test_releases_used_by_launchers_are_kept(self):
        # Installing only Discord leaves the Firefox launcher and the Corsu shortcut on an earlier copy; deleting that
        # copy broke every link Discord opened in Firefox.
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data'
            for name in ('current', 'old', 'firefox', 'shortcut', 'applet'):
                genuine(data / 'releases' / R(name))
            launcher = Path(directory) / 'firefox-corsu'
            launcher.write_text(f'#!/bin/sh\nexec python3 {data / "releases" / R("firefox") / "src/corsu.py"} launch-firefox "$@"\n')
            shortcut = Path(directory) / 'corsu-setup.desktop'
            shortcut.write_text(f'[Desktop Entry]\nExec=python3 {data / "releases" / R("shortcut") / "src/app.py"}\n')
            applet = Path(directory) / 'Corsu.app'
            (applet / 'Contents/Resources/Scripts').mkdir(parents=True)
            (applet / 'Contents/Resources/Scripts/main.scpt').write_bytes(
                b'\x00' + str(data / 'releases' / R('applet') / 'src/app.py').encode('utf-16-be') + b'\x00')
            state = data / 'installation.json'
            state.write_text(json.dumps({'files': {str(launcher): {}, str(shortcut): {}, str(applet): {'tree': True}}}))
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', state), \
                    patch.object(corsu, 'CONFIG', Path(directory) / 'config'):
                installer.prune_releases(data / 'releases' / R('current'))
            self.assertEqual(sorted(path.name for path in (data / 'releases').iterdir()),
                             names('applet', 'current', 'firefox', 'shortcut'))


    def test_records_of_removed_discord_versions_are_forgotten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            kept = root / 'app-2'
            (kept / 'resources').mkdir(parents=True)
            state = {'files': {str(root / 'app-1/resources/app.asar'): {'discord_location': str(root / 'app-1')},
                               str(kept / 'resources/app.asar'): {'discord_location': str(kept)}}}
            with patch.object(corsu, 'STATE', root / 'state.json'), redirect_stdout(io.StringIO()):
                corsu.STATE.write_text(json.dumps(state))
                installer.forget_removed_discord()
                self.assertEqual(list(corsu.load_state()['files']), [str(kept / 'resources/app.asar')])

    def test_copies_loaded_by_an_open_client_stay_until_it_closes(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data'
            for name in ('current', 'loaded', 'old'):
                genuine(data / 'releases' / R(name))
            state = data / 'installation.json'
            state.write_text(json.dumps({'files': {}}))
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', state), \
                    patch.object(corsu, 'CONFIG', Path(directory) / 'config'):
                with patch.object(installer, 'clients_running', return_value=True):
                    installer.prune_releases(data / 'releases' / R('current'), {R('loaded')})
                    self.assertEqual(sorted(path.name for path in (data / 'releases').iterdir()), names('current', 'loaded'))
                    # A later run still knows the open client uses it, even though nothing points there any more.
                    installer.prune_releases(data / 'releases' / R('current'))
                    self.assertTrue((data / 'releases' / R('loaded')).is_dir())
                with patch.object(installer, 'clients_running', return_value=False):
                    installer.prune_releases(data / 'releases' / R('current'))
                self.assertEqual(sorted(path.name for path in (data / 'releases').iterdir()), names('current'))
                self.assertEqual(json.loads(state.read_text())['running_releases'], [])

    def test_the_copy_of_the_open_corsu_app_is_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data'
            for name in ('current', 'app', 'old'):
                genuine(data / 'releases' / R(name))
            state = data / 'installation.json'
            state.write_text(json.dumps({'files': {}}))
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', state), \
                    patch.object(corsu, 'CONFIG', Path(directory) / 'config'), \
                    patch.object(installer, 'clients_running', return_value=False), \
                    patch.dict(os.environ, {'CORSU_APP_ROOT': str(data / 'releases' / R('app'))}):
                installer.prune_releases(data / 'releases' / R('current'))
            self.assertEqual(sorted(path.name for path in (data / 'releases').iterdir()), names('app', 'current'))

    def test_the_bundled_python_is_copied_once_and_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root, data = Path(directory) / 'archive', Path(directory) / 'data'
            python = root / 'runtime' / installer.machine() / 'python'
            interpreter = python / ('python.exe' if corsu.PLATFORM == 'windows' else 'bin/python3')
            interpreter.parent.mkdir(parents=True)
            interpreter.write_text('')
            (root / 'src').mkdir()
            (root / 'src/release.json').write_text(json.dumps({'python_runtime': {'version': '3.13.16+20261001'}}))
            with patch.object(installer, 'ROOT', root), patch.object(corsu, 'DATA', data), \
                    patch.object(installer.sys, 'executable', str(interpreter)):
                deployed = installer.deploy_runtime()
                self.assertEqual(deployed, installer.runtime_python(data / 'runtime/3.13.16-20261001'))
                self.assertTrue(deployed.exists())
                self.assertEqual(installer.deploy_runtime(), deployed)
            # A system Python stays the one used.
            with patch.object(installer, 'ROOT', root), patch.object(corsu, 'DATA', data):
                self.assertEqual(installer.deploy_runtime(), Path(installer.sys.executable))

    def test_unused_python_copies_are_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data'
            for name in ('old', 'launcher'):
                (data / 'runtime' / name / 'python').mkdir(parents=True)
            launcher = Path(directory) / 'firefox-corsu'
            launcher.write_text(f'exec {data / "runtime/launcher/python/bin/python3"} corsu.py\n')
            state = data / 'installation.json'
            state.write_text(json.dumps({'files': {str(launcher): {}}}))
            with patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', state), \
                    patch.object(corsu, 'CONFIG', Path(directory) / 'config'):
                installer.prune_runtimes()
            self.assertEqual([path.name for path in (data / 'runtime').iterdir()], ['launcher'])


if __name__ == '__main__':
    unittest.main()


class DeployedCopyTests(unittest.TestCase):
    def test_installed_copy_carries_what_minecraft_reads(self):
        # The extracted archive had minecraft/java; the copy launchers use did not, and installing Minecraft stopped.
        with tempfile.TemporaryDirectory() as directory:
            root, data = Path(directory) / 'extracted', Path(directory) / 'data'
            for name in ('src/installer.py', *installer.DEPLOYED_MINECRAFT):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(name, encoding='utf-8')
            with patch.object(installer, 'ROOT', root), patch.object(corsu, 'DATA', data), \
                    patch.dict(os.environ, {'CORSU_DEPLOYED': ''}):
                copy = installer.deploy_release()
                for name in installer.DEPLOYED_MINECRAFT:
                    self.assertEqual((copy / name).read_text(encoding='utf-8'), name)
                (root / 'minecraft/java/VERSION').write_text('26.4', encoding='utf-8')
                self.assertNotEqual(installer.deploy_release(), copy)  # a new pack version is a new copy
