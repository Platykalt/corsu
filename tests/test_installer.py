import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
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
            # A system Python stays the one used, and the copy is made all the same: launchers fall back to it.
            shutil.rmtree(data)
            with patch.object(installer, 'ROOT', root), patch.object(corsu, 'DATA', data):
                self.assertEqual(installer.deploy_runtime(), Path(installer.sys.executable))
                self.assertTrue(installer.runtime_python(data / 'runtime/3.13.16-20261001').exists())

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


class LauncherPythonTests(Isolated):
    """Launchers of an archive installed with the system's Python fall back to the bundled copy (corsu.launcher_python)."""

    VERSION = '3.13.16+20261001'

    def setUp(self):
        super().setUp()
        self.root = self.release('0.25.0', R('current'))
        (self.root / 'src/release.json').write_text(json.dumps({'version': '0.25.0', 'python_runtime': {'version': self.VERSION}}))
        patcher = patch.object(corsu, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def bundled(self, platform='linux'):
        python = self.data / 'runtime/3.13.16-20261001/python'
        interpreter = python / ('python.exe' if platform == 'windows' else 'bin/python3')
        interpreter.parent.mkdir(parents=True, exist_ok=True)
        interpreter.write_text('')
        return interpreter

    def test_without_a_bundled_copy_launchers_use_this_python(self):
        with patch.object(corsu, 'PLATFORM', 'linux'):
            self.assertEqual(corsu.launcher_python(corsu.Installer()), Path(sys.executable))
        self.assertFalse((self.data / 'bin/corsu-python').exists())

    @unittest.skipIf(os.name == 'nt', 'Linux and macOS launchers hold POSIX paths, which a Windows test run cannot make')
    def test_the_system_python_falls_back_to_the_bundled_copy(self):
        fallback = self.bundled()
        with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(corsu.sys, 'executable', '/usr/bin/python3'):
            wrapper = corsu.launcher_python(corsu.Installer())
        self.assertEqual(wrapper, self.data / 'bin/corsu-python')
        text = wrapper.read_text()
        self.assertIn(f'for python in /usr/bin/python3 {shlex.quote(str(fallback))}; do', text)
        self.assertTrue(os.access(wrapper, os.X_OK))
        self.assertIn(str(wrapper), corsu.load_state()['files'])
        # The wrapper names the copy: it is never deleted as unused.
        (self.data / 'runtime/old/python').mkdir(parents=True)
        installer.prune_runtimes()
        self.assertEqual(sorted(path.name for path in (self.data / 'runtime').iterdir()), ['3.13.16-20261001'])

    def test_corsu_running_on_the_bundled_copy_and_windows_use_it_directly(self):
        fallback = self.bundled()
        with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(corsu.sys, 'executable', str(fallback)):
            self.assertEqual(corsu.launcher_python(corsu.Installer()), fallback)
        windows = self.bundled('windows')
        with patch.object(corsu, 'PLATFORM', 'windows'), patch.object(corsu.sys, 'executable', 'C:/Python313/python.exe'):
            self.assertEqual(corsu.launcher_python(corsu.Installer()), Path('C:/Python313/python.exe'))
        self.assertTrue(windows.exists())
        self.assertFalse((self.data / 'bin/corsu-python').exists())

    @unittest.skipIf(os.name == 'nt', 'Linux and macOS launchers hold POSIX paths, which a Windows test run cannot make')
    def test_launchers_on_linux_and_macos_go_through_the_wrapper(self):
        self.bundled()
        commands = []

        def osacompile(command, **_):
            commands.append(command)
            Path(command[2]).mkdir(parents=True)
        for platform in ('linux', 'macos'):
            with patch.object(corsu, 'PLATFORM', platform), patch.object(corsu.sys, 'executable', '/usr/bin/python3'), \
                    patch.object(corsu.subprocess, 'run', side_effect=osacompile):
                corsu.setup_shortcut(corsu.Installer())
        wrapper = shlex.quote(str(self.data / 'bin/corsu-python'))
        entry = (self.home / '.local/share/applications/corsu-setup.desktop').read_text()
        self.assertIn(f'Exec={wrapper} ', entry)
        self.assertIn(f'exec {wrapper} ', commands[0][-1])

    @unittest.skipIf(os.name == 'nt', 'Linux and macOS launchers hold POSIX paths, which a Windows test run cannot make')
    def test_launchers_written_before_get_the_chosen_python(self):
        # 0.24.0 wrote the system Python into each launcher; Firefox switched off keeps its launcher unrewritten.
        old = self.data / 'releases' / R('old')
        launcher = self.home / '.local/bin/firefox-corsu'
        entry = self.home / '.local/share/applications/corsu-setup.desktop'
        shortcuts = corsu.Installer()
        shortcuts.write(launcher, f'#!/bin/sh\nexec /usr/bin/python3 {shlex.quote(str(old / "src/corsu.py"))} launch-firefox "$@"\n', 0o755)
        shortcuts.write(entry, f'[Desktop Entry]\nExec=/usr/bin/python3 {shlex.quote(str(old / "src/app.py"))}\nName=Corsu\n')
        wrapper = self.data / 'bin/corsu-python'
        with patch.object(corsu, 'PLATFORM', 'linux'):
            corsu.refresh_launchers(shortcuts, python=wrapper)
        self.assertEqual(launcher.read_text(), f'#!/bin/sh\nexec {shlex.quote(str(wrapper))} '
                                               f'{shlex.quote(str(self.root / "src/corsu.py"))} launch-firefox "$@"\n')
        self.assertIn(f'Exec={shlex.quote(str(wrapper))} {shlex.quote(str(self.root / "src/app.py"))}\n', entry.read_text())
        # Back on the bundled copy: the wrapper goes once nothing names it any more.
        shortcuts.write(wrapper, '#!/bin/sh\n', 0o755)
        fallback = self.bundled()
        installer.forget_python_wrapper(shortcuts, wrapper)
        self.assertTrue(wrapper.exists())
        installer.forget_python_wrapper(shortcuts, fallback)
        self.assertTrue(wrapper.exists(), 'launchers still name it')
        with patch.object(corsu, 'PLATFORM', 'linux'):
            corsu.refresh_launchers(shortcuts, python=fallback)
        installer.forget_python_wrapper(shortcuts, fallback)
        self.assertFalse(wrapper.exists())
        self.assertNotIn(str(wrapper), corsu.load_state()['files'])
        self.assertIn(f'exec {shlex.quote(str(fallback))} ', launcher.read_text())

    def test_windows_launchers_are_left_to_their_own_steps(self):
        launcher = self.data / 'bin/firefox-corsu.cmd'
        shortcuts = corsu.Installer()
        text = f'@"C:/Python/pythonw.exe" "{self.data / "releases" / R("old") / "src/corsu.py"}" launch-firefox %*\r\n'
        shortcuts.write(launcher, text)
        with patch.object(corsu, 'PLATFORM', 'windows'):
            corsu.refresh_launchers(shortcuts, python=Path('C:/other/pythonw.exe'))
        self.assertIn('C:/Python/pythonw.exe', launcher.read_text())
        self.assertIn(R('current'), launcher.read_text())

    @unittest.skipIf(os.name == 'nt', 'a shell script')
    def test_the_wrapper_starts_the_first_python_that_works(self):
        fallback = self.bundled()
        fallback.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n')
        fallback.chmod(0o755)
        broken = self.home / 'python3-minimal'
        broken.write_text('#!/bin/sh\nexit 1\n')
        broken.chmod(0o755)
        script = self.home / 'say.py'
        script.write_text('import sys; print(sys.argv[1])\n')
        for system in (self.home / 'removed/python3', broken, Path(sys.executable)):
            with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(corsu.sys, 'executable', str(system)):
                wrapper = corsu.launcher_python(corsu.Installer())
            result = subprocess.run([str(wrapper), str(script), 'corsu'], capture_output=True, text=True)
            self.assertEqual((result.returncode, result.stdout), (0, 'corsu\n'), system)
        with patch.object(corsu, 'PLATFORM', 'linux'), patch.object(corsu.sys, 'executable', str(broken)):
            corsu.launcher_python(corsu.Installer())
        fallback.unlink()  # the copy deleted by hand as well: nothing can start, and the script says so
        result = subprocess.run([str(wrapper), str(script), 'corsu'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('no usable Python', result.stderr)


if __name__ == '__main__':
    unittest.main()


class DeployedCopyTests(unittest.TestCase):
    def test_installed_copy_carries_what_minecraft_reads(self):
        # The extracted archive had minecraft/java; the copy launchers use did not, and installing Minecraft stopped.
        with tempfile.TemporaryDirectory() as directory:
            root, data = Path(directory) / 'extracted', Path(directory) / 'data'
            for name in ('src/installer.py', *installer.DEPLOYED_MINECRAFT, *installer.DEPLOYED_VLC):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(name, encoding='utf-8')
            with patch.object(installer, 'ROOT', root), patch.object(corsu, 'DATA', data), \
                    patch.dict(os.environ, {'CORSU_DEPLOYED': ''}):
                copy = installer.deploy_release()
                for name in (*installer.DEPLOYED_MINECRAFT, *installer.DEPLOYED_VLC):
                    self.assertEqual((copy / name).read_text(encoding='utf-8'), name)
                (root / 'minecraft/java/VERSION').write_text('26.4', encoding='utf-8')
                self.assertNotEqual(installer.deploy_release(), copy)  # a new pack version is a new copy
