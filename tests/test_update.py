"""One managed installation per user (docs/update-architecture.md): version policy, choices kept across updates and
repairs, the lock, safe downloads and extraction, recovery and the release folders' clean-up."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import time
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import corsu
import installer
import update
from tests.test_installer import Isolated

SRC = Path(__file__).resolve().parent.parent / 'src'


def quiet():
    return redirect_stdout(io.StringIO())


class VersionPolicyTests(Isolated):
    def test_policy(self):
        self.assertEqual(installer.version_policy('0.23.0', None), 'install')
        self.assertEqual(installer.version_policy('0.23.0', '0.22.0'), 'update')
        self.assertEqual(installer.version_policy('0.23.0', '0.23.0'), 'repair')
        self.assertEqual(installer.version_policy('0.22.0', '0.23.0'), 'downgrade')
        self.assertEqual(installer.version_policy('0.10.0', '0.9.2'), 'update')

    def test_installed_release_is_recorded_or_found_from_the_launchers(self):
        self.assertIsNone(installer.installed_release())
        old, new = self.release('0.21.0'), self.release('0.22.0')
        # 0.21 and 0.22 recorded no release: the Corsu menu entry tells, even when another launcher was left on an
        # older copy.
        entry = self.home / 'corsu-setup.desktop'
        entry.write_text(f'Exec=python3 {new / "src/app.py"}\n', encoding='utf-8')
        launcher = self.home / 'firefox-corsu'
        launcher.write_text(f'exec python3 {old / "src/corsu.py"} launch-firefox\n', encoding='utf-8')
        state = {'files': {str(entry): {}, str(launcher): {}}, 'components': ['firefox']}
        corsu.save_state(state)
        found = installer.installed_release()
        self.assertEqual((found['version'], Path(found['folder']).name), ('0.22.0', new.name))
        # Without the menu entry, the newest copy any launcher uses.
        entry.unlink()
        newer_launcher = self.home / 'vesktop.desktop'
        newer_launcher.write_text(f'Exec=python3 {new / "src/corsu.py"}\n', encoding='utf-8')
        state['files'][str(newer_launcher)] = {}
        corsu.save_state(state)
        self.assertEqual(installer.installed_release()['version'], '0.22.0')
        # From now on it is recorded; a folder written on Windows is found by its name.
        state['release'] = {'version': '0.21.0', 'folder': 'C:\\Users\\x\\corsu\\releases\\' + old.name, 'installed_at': 1}
        corsu.save_state(state)
        self.assertEqual(installer.installed_release()['folder'], str(old))
        # A recorded folder that is gone falls back to the launchers.
        installer.shutil.rmtree(old)
        self.assertEqual(installer.installed_release()['version'], '0.22.0')

    def run_main(self, arguments, root=None, deploy=None):
        """installer.main with every step that touches programs replaced; returns the corsu.install mock."""
        root = root or installer.ROOT
        with patch.object(installer, 'ROOT', root), \
                patch.object(installer, 'available_components', return_value=['firefox', 'minecraft', 'chromium']), \
                patch.object(installer, 'discord_location', return_value=None), \
                patch.object(installer, 'deploy_release', return_value=deploy or root), \
                patch.object(installer, 'deploy_runtime', return_value=Path(sys.executable)), \
                patch.object(installer, 'clients_running', return_value=False), \
                patch.object(corsu, 'firefox_install', return_value=True), \
                patch.object(corsu, 'setup_shortcut'), patch.object(installer.shutil, 'which', return_value=None), \
                patch.object(corsu, 'install') as install, quiet() as output:
            code = installer.main(arguments)
        self.output = output.getvalue()
        return code, install

    def installed(self, components, disabled=(), release=None, **extra):
        state = {'files': {}, 'components': components, 'disabled': list(disabled), 'enabled': True, **extra}
        if release:
            state['release'] = {'version': installer.release_version(release), 'folder': str(release), 'installed_at': 1}
        corsu.save_state(state)

    def test_update_and_repair_keep_switched_off_parts_off_and_add_nothing(self):
        current = self.release('0.22.0')
        self.installed(['firefox', 'minecraft'], disabled=['minecraft'], release=current)
        newer = self.release('0.23.0')
        # The installer of the new release, as update.py (and 0.21/0.22's update.py) runs it: every recorded part.
        code, install = self.run_main(['--yes', '--components', 'firefox', 'minecraft'], root=newer)
        self.assertEqual(code, 0)
        install.assert_called_once_with({'firefox'}, qt_system=False)
        self.assertIn('stays off', self.output)
        state = corsu.load_state()
        self.assertEqual(state['disabled'], ['minecraft'])
        self.assertEqual(state['release']['version'], '0.23.0')
        self.assertEqual(state['release']['python'], sys.executable)
        self.assertEqual(Path(state['previous_release']['folder']).name, current.name)
        # Running it again without a list repairs what is installed: chromium, found but never chosen, is not added.
        code, install = self.run_main(['--yes'], root=newer)
        install.assert_called_once_with({'firefox'}, qt_system=False)
        self.assertIn('repairing', self.output)

    def test_everything_switched_off_stays_off_and_launchers_are_still_refreshed(self):
        current = self.release('0.22.0')
        self.installed(['firefox'], disabled=['firefox'], release=current, enabled=False)
        corsu.disabled_marker().write_text('off', encoding='utf-8')
        newer = self.release('0.23.0')
        code, install = self.run_main(['--yes', '--components', 'firefox'], root=newer)
        self.assertEqual(code, 0)
        install.assert_not_called()
        self.assertTrue(corsu.disabled_marker().exists())
        self.assertEqual(corsu.load_state()['release']['version'], '0.23.0')

    def test_parts_whose_program_is_gone_are_left_alone(self):
        self.installed(['firefox', 'vlc'], release=self.release('0.22.0'))
        code, install = self.run_main(['--yes', '--components', 'firefox', 'vlc'], root=self.release('0.23.0'))
        install.assert_called_once_with({'firefox'}, qt_system=False)
        self.assertIn('no longer found', self.output)

    def test_older_copy_is_refused_unless_asked(self):
        self.installed(['firefox'], release=self.release('9.0.0'))
        older = self.release('0.22.0')
        with self.assertRaises(installer.Refused):
            self.run_main(['--yes', '--components', 'firefox'], root=older)
        self.assertEqual(corsu.load_state()['release']['version'], '9.0.0')
        code, install = self.run_main(['--yes', '--components', 'firefox', '--allow-downgrade'], root=older)
        install.assert_called_once()
        self.assertEqual(corsu.load_state()['release']['version'], '0.22.0')

    def test_a_source_folder_is_never_registered(self):
        source = self.home / 'git clone' / 'corsu'
        (source / 'src').mkdir(parents=True)
        (source / 'src/release.json').write_text(json.dumps({'version': '0.23.0'}), encoding='utf-8')
        self.installed(['firefox'])
        self.run_main(['--yes', '--components', 'firefox'], root=source)
        self.assertNotIn('release', corsu.load_state())

    def test_migration_from_0_21_records_the_release_and_keeps_the_old_copy_once(self):
        # 0.21: no 'results', no 'release'; launchers point at its copy.
        old = self.release('0.21.0')
        entry = self.home / 'corsu-setup.desktop'
        writer = corsu.Installer()
        writer.write(entry, f'Exec=python3 {old / "src/app.py"}\n')
        state = corsu.load_state()
        state.update(components=['firefox'], disabled=[], enabled=True, qt_system=False)
        corsu.save_state(state)
        newer = self.release('0.23.0')
        with patch.object(corsu, 'ROOT', newer):
            code, _ = self.run_main(['--yes'], root=newer)
        self.assertEqual(code, 0)
        state = corsu.load_state()
        self.assertEqual(Path(state['release']['folder']).name, newer.name)
        self.assertEqual(state['previous_release']['version'], '0.21.0')
        self.assertIn(str(newer), entry.read_text(encoding='utf-8'))
        self.assertTrue(old.is_dir(), 'the previous copy stays until the next successful update')
        newest = self.release('0.24.0')
        with patch.object(corsu, 'ROOT', newest):
            self.run_main(['--yes'], root=newest)
        self.assertFalse(old.exists())
        self.assertTrue(newer.is_dir())

    def test_failed_new_copy_leaves_launchers_on_the_previous_one(self):
        current = self.release('0.22.0')
        launcher = self.home / 'firefox-corsu'
        corsu.Installer().write(launcher, f'#!/bin/sh\nexec python3 {current / "src/corsu.py"} launch-firefox\n')
        state = corsu.load_state()
        state.update(components=['firefox'], release={'version': '0.22.0', 'folder': str(current), 'installed_at': 1})
        corsu.save_state(state)
        newer = self.release('0.23.0')
        archive = self.home / 'archive'
        (archive / 'src').mkdir(parents=True)
        (archive / 'src/release.json').write_text(json.dumps({'version': '0.23.0'}), encoding='utf-8')

        def child_fails(command, **kwargs):
            # The new copy switched the launcher, then stopped.
            with patch.object(corsu, 'ROOT', newer):
                corsu.refresh_launchers(corsu.Installer())
            self.assertIn(newer.name, launcher.read_text(encoding='utf-8'))
            raise subprocess.CalledProcessError(1, command)

        with patch.object(installer, 'run', side_effect=child_fails), redirect_stderr(io.StringIO()):
            with self.assertRaises(subprocess.CalledProcessError):
                self.run_main(['--yes', '--components', 'firefox'], root=archive, deploy=newer)
        self.assertIn(current.name, launcher.read_text(encoding='utf-8'))
        self.assertEqual(Path(corsu.load_state()['release']['folder']).name, current.name)
        self.assertTrue(newer.is_dir(), 'kept for the next try')


class PruneTests(Isolated):
    def test_only_genuine_unused_release_folders_are_deleted(self):
        current, previous, old = self.release('0.23.0'), self.release('0.22.0'), self.release('0.21.0')
        corsu.save_state({'files': {}, 'release': {'version': '0.23.0', 'folder': str(current)},
                          'previous_release': {'version': '0.22.0', 'folder': str(previous)}})
        releases = self.data / 'releases'
        lookalike = releases / 'abcdef0123456789'  # a fingerprint name without Corsu inside
        (lookalike / 'mine').mkdir(parents=True)
        other = releases / 'notes'
        other.mkdir()
        stage_new, stage_old = releases / 'stage-new', releases / 'stage-old'
        stage_new.mkdir()
        stage_old.mkdir()
        os.utime(stage_old, (time.time() - 3 * installer.DAY,) * 2)
        backup = self.data / 'backups' / 'x'
        backup.parent.mkdir(parents=True)
        backup.write_text('original', encoding='utf-8')
        with patch.object(installer, 'clients_running', return_value=False):
            installer.prune_releases(current)
        self.assertEqual(sorted(path.name for path in releases.iterdir()),
                         sorted([current.name, previous.name, lookalike.name, 'notes', 'stage-new']))
        self.assertFalse(old.exists())
        self.assertEqual(backup.read_text(encoding='utf-8'), 'original')

    def test_a_folder_in_use_is_skipped_and_tried_again_later(self):
        current, old = self.release('0.23.0'), self.release('0.21.0')
        corsu.save_state({'files': {}})
        real_rename = Path.rename

        def locked(path, target):
            if path.name == old.name:
                raise PermissionError(32, 'The process cannot access the file because it is being used')
            return real_rename(path, target)

        with patch.object(installer, 'clients_running', return_value=False), patch.object(Path, 'rename', locked):
            installer.prune_releases(current)
        self.assertTrue((old / 'src/release.json').is_file(), 'nothing deleted from a folder in use')
        with patch.object(installer, 'clients_running', return_value=False):
            installer.prune_releases(current)
        self.assertFalse(old.exists())

    def test_incomplete_copy_is_made_again(self):
        archive = self.home / 'archive'
        for name in ('src/installer.py', 'src/release.json'):
            (archive / name).parent.mkdir(parents=True, exist_ok=True)
            (archive / name).write_text(name, encoding='utf-8')
        with patch.object(installer, 'ROOT', archive), patch.dict(os.environ, {'CORSU_DEPLOYED': ''}):
            copy = installer.deploy_release()
            (copy / 'src/installer.py').unlink()  # what a half-finished deletion by an earlier version leaves
            self.assertEqual(installer.deploy_release(), copy)
            self.assertTrue((copy / 'src/installer.py').is_file())


LOCK_SCRIPT = textwrap.dedent('''
    import json, sys, time
    sys.path.insert(0, sys.argv[1])
    import corsu
    try:
        with corsu.lock('install'):
            state = corsu.load_state()
            state['runs'] = state.get('runs', 0) + 1
            if len(sys.argv) > 3:
                # Hold the lock until the test says so: a slow computer cannot let the other run slip past it.
                from pathlib import Path
                deadline = time.monotonic() + 60
                while not Path(sys.argv[3]).exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
            else:
                time.sleep(float(sys.argv[2]))
            corsu.save_state(state)
        print('done')
    except corsu.Busy as error:
        print('busy:', error)
''')


def environment_for(home):
    inherited = {name: value for name, value in os.environ.items() if name != 'CORSU_LOCK_TOKEN'}
    return {**inherited, 'HOME': str(home), 'USERPROFILE': str(home), 'LOCALAPPDATA': str(home / 'AppData/Local'),
            'APPDATA': str(home / 'AppData/Roaming'), 'XDG_CONFIG_HOME': str(home / '.config'), 'CORSU_LANG': 'en',
            'CORSU_LOCK_WAIT': '0.5'}


def data_for(home):
    return {'windows': home / 'AppData/Local/corsu', 'macos': home / 'Library/Application Support/corsu'}.get(
        corsu.PLATFORM, home / '.local/share/corsu')


class LockTests(Isolated):
    def test_second_run_waits_then_says_who_is_busy(self):
        sleeper = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        self.addCleanup(sleeper.wait)
        self.addCleanup(sleeper.kill)
        self.data.mkdir(parents=True)
        (self.data / 'lock').write_text(json.dumps({'pid': sleeper.pid, 'started': time.time(), 'action': 'update',
                                                    'token': 'other'}), encoding='utf-8')
        started = time.monotonic()
        with self.assertRaises(corsu.Busy) as caught:
            with corsu.lock('install', wait=0.4):
                pass
        self.assertGreaterEqual(time.monotonic() - started, 0.35)
        self.assertIn('Corsu is already busy: updating since', str(caught.exception))
        with patch.dict(os.environ, {'CORSU_LANG': 'fr'}):
            self.assertIn('Corsu est déjà occupé : mise à jour depuis', corsu.busy_message(corsu.lock_holder()))
        # The installer stops before changing anything.
        with self.assertRaises(corsu.Busy), patch.object(installer, 'available_components', return_value=['firefox']), \
                patch.object(installer, 'discord_location', return_value=None), \
                patch.object(installer, 'deploy_release') as deploy, quiet():
            installer.main(['--yes', '--components', 'firefox'])
        deploy.assert_not_called()
        # Nor the VLC complement's choice.
        with self.assertRaises(corsu.Busy), patch.object(installer, 'available_components', return_value=['firefox']), \
                patch.object(installer, 'discord_location', return_value=None), \
                patch.object(installer, 'deploy_release'), quiet():
            installer.main(['--yes', '--components', 'firefox', '--vlc-complement', 'on'])
        self.assertIs(update.preferences()['vlc_complement'], False)

    def test_stale_lock_of_a_finished_process_is_taken_over(self):
        finished = subprocess.run([sys.executable, '-c', 'import os; print(os.getpid())'], capture_output=True, text=True)
        self.data.mkdir(parents=True)
        (self.data / 'lock').write_text(json.dumps({'pid': int(finished.stdout), 'started': time.time(),
                                                    'action': 'install', 'token': 'gone'}), encoding='utf-8')
        with corsu.lock('repair', wait=0):
            self.assertEqual(corsu.lock_holder()['action'], 'repair')
        self.assertFalse((self.data / 'lock').exists())
        # Half written by a process that stopped right after creating it.
        (self.data / 'lock').write_text('', encoding='utf-8')
        os.utime(self.data / 'lock', (time.time() - 60,) * 2)
        with corsu.lock('install', wait=0):
            pass

    def test_processes_started_by_the_holder_go_through(self):
        with corsu.lock('update'):
            token = os.environ['CORSU_LOCK_TOKEN']
            with corsu.lock('install', wait=0):  # the installer update.py runs
                with corsu.lock('install', wait=0):  # that installer re-running from the installed copy
                    self.assertEqual(corsu.lock_holder()['token'], token)
            self.assertTrue((self.data / 'lock').exists(), 'only the holder releases it')
        self.assertNotIn('CORSU_LOCK_TOKEN', os.environ)
        self.assertFalse((self.data / 'lock').exists())

    def test_a_child_process_inherits_the_lock(self):
        home = self.home / 'child home'
        with patch.object(corsu, 'DATA', data_for(home)), corsu.lock('update'):
            token = os.environ['CORSU_LOCK_TOKEN']
            child = subprocess.run([sys.executable, '-c', LOCK_SCRIPT, str(SRC), '0'], capture_output=True, text=True,
                                   env={**environment_for(home), 'CORSU_LOCK_TOKEN': token}, timeout=60)
            self.assertEqual(child.stdout.strip(), 'done', child.stderr)
            self.assertEqual(corsu.lock_holder()['token'], token, 'the child left the lock to its parent')
            stranger = subprocess.run([sys.executable, '-c', LOCK_SCRIPT, str(SRC), '0'], capture_output=True,
                                      text=True, env=environment_for(home), timeout=60)
            self.assertIn('busy', stranger.stdout)
        self.assertFalse((data_for(home) / 'lock').exists())

    def test_two_installers_at_once(self):
        home = self.home / 'other home'
        release = self.home / 'release'
        script = [sys.executable, '-c', LOCK_SCRIPT, str(SRC), '0']
        first = subprocess.Popen([*script, str(release)], stdout=subprocess.PIPE, text=True, env=environment_for(home))
        lock = data_for(home) / 'lock'
        deadline = time.monotonic() + 20
        while not lock.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        second = subprocess.run(script, capture_output=True, text=True, env=environment_for(home), timeout=60)
        release.write_text('', encoding='utf-8')
        self.assertIn('busy: Corsu is already busy: installing since', second.stdout)
        self.assertEqual(first.communicate(timeout=60)[0].strip(), 'done')
        state = json.loads((data_for(home) / 'installation.json').read_text(encoding='utf-8'))
        self.assertEqual(state['runs'], 1)
        self.assertFalse(lock.exists())
        # Once free, the next one runs.
        third = subprocess.run([sys.executable, '-c', LOCK_SCRIPT, str(SRC), '0'], capture_output=True, text=True,
                               env=environment_for(home), timeout=60)
        self.assertEqual(third.stdout.strip(), 'done')


def tar_archive(path, members):
    """members: [(name, bytes) | (name, ('symlink'|'hardlink', target)) | (name, None) for a folder]"""
    with tarfile.open(path, 'w:gz') as bundle:
        for name, content in members:
            info = tarfile.TarInfo(name)
            if content is None:
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                bundle.addfile(info)
            elif isinstance(content, tuple):
                info.type = tarfile.SYMTYPE if content[0] == 'symlink' else tarfile.LNKTYPE
                info.linkname = content[1]
                bundle.addfile(info)
            else:
                info.size, info.mode = len(content), 0o755
                bundle.addfile(info, io.BytesIO(content))


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def extract(self, archive):
        target = self.root / ('out-' + archive.name)
        update.safe_extract(archive, target)
        return target

    def test_a_release_archive_with_its_python_links(self):
        archive = self.root / 'good.tar.gz'
        tar_archive(archive, [('corsu/', None), ('corsu/src/release.json', b'{}'),
                              ('corsu/runtime/python/bin/python3.13', b'#!python'),
                              ('corsu/runtime/python/bin/python3', ('symlink', 'python3.13')),
                              ('corsu/runtime/python/lib/copy', ('hardlink', 'corsu/src/release.json'))])
        try:
            target = self.extract(archive)
        except OSError:
            self.skipTest('Symbolic links need extra rights on this system')
        self.assertEqual((target / 'corsu/runtime/python/bin/python3').read_bytes(), b'#!python')
        self.assertTrue((target / 'corsu/runtime/python/bin/python3').is_symlink())
        self.assertEqual((target / 'corsu/runtime/python/lib/copy').read_bytes(), b'{}')
        if os.name != 'nt':
            self.assertTrue(os.access(target / 'corsu/runtime/python/bin/python3.13', os.X_OK))

    def test_malicious_tar_archives_are_refused(self):
        outside = self.root / 'outside.txt'
        cases = {
            'parent': [('corsu/../../outside.txt', b'x')],
            'absolute': [(str(outside), b'x')],
            'link out': [('corsu/link', ('symlink', '../../')), ('corsu/link/outside.txt', b'x')],
            'absolute link': [('corsu/etc', ('symlink', '/etc'))],
            'link chain': [('corsu/a', None), ('corsu/a/b', ('symlink', '../..')), ('corsu/c', ('symlink', 'a/b/..'))],
            'hard link out': [('corsu/h', ('hardlink', '../outside.txt'))],
            'device': None,
        }
        for label, members in cases.items():
            archive = self.root / f'{label}.tar.gz'
            if members is None:
                with tarfile.open(archive, 'w:gz') as bundle:
                    info = tarfile.TarInfo('corsu/dev')
                    info.type = tarfile.CHRTYPE
                    bundle.addfile(info)
            else:
                tar_archive(archive, members)
            with self.subTest(label), self.assertRaises(update.UnsafeArchive):
                self.extract(archive)
            self.assertFalse(outside.exists())
            self.assertFalse((self.root / 'outside.txt').exists())

    def test_malicious_zip_archives_are_refused(self):
        for label, name in (('parent', 'corsu/../../evil.txt'), ('absolute', '/evil.txt'), ('drive', 'C:/evil.txt'),
                            ('backslash', 'corsu\\..\\..\\evil.txt')):
            archive = self.root / f'{label}.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.writestr(zipfile.ZipInfo(name), b'x')
            with self.subTest(label), self.assertRaises(update.UnsafeArchive):
                self.extract(archive)
        archive = self.root / 'link.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            info = zipfile.ZipInfo('corsu/link')
            info.external_attr = (0o120777 << 16)
            bundle.writestr(info, '/etc/passwd')
        with self.assertRaises(update.UnsafeArchive):
            self.extract(archive)
        good = self.root / 'good.zip'
        with zipfile.ZipFile(good, 'w') as bundle:
            bundle.writestr('corsu/src/release.json', '{}')
        self.assertEqual((self.extract(good) / 'corsu/src/release.json').read_text(), '{}')


FAKE_INSTALLER = textwrap.dedent('''
    # Records how it was run and, like the real one, which release is now installed.
    import json, os, sys
    from pathlib import Path
    with open(os.environ['CORSU_TEST_MARK'], 'w') as output:
        json.dump(sys.argv[1:], output)
    print('@progress 50 Halfway')
    code = int(os.environ.get('CORSU_TEST_EXIT', '0'))
    if not code:
        state_path = Path(os.environ['CORSU_TEST_STATE'])
        version = json.loads((Path(__file__).parent / 'release.json').read_text())['version']
        folder = state_path.parent / 'releases' / ('f' * 12 + version.replace('.', '').rjust(4, '0'))
        (folder / 'src').mkdir(parents=True, exist_ok=True)
        (folder / 'src/release.json').write_text(json.dumps({'version': version}))
        state = json.loads(state_path.read_text())
        state['release'] = {'version': version, 'folder': str(folder), 'installed_at': 2}
        state_path.write_text(json.dumps(state))
    sys.exit(code)
''')


class UpdateTests(Isolated):
    def setUp(self):
        super().setUp()
        self.mark = self.home / 'ran.json'
        self.served = self.home / 'served'
        self.served.mkdir()
        os.environ['CORSU_TEST_MARK'] = str(self.mark)
        os.environ['CORSU_TEST_STATE'] = str(corsu.STATE)
        self.addCleanup(os.environ.pop, 'CORSU_TEST_MARK', None)
        self.addCleanup(os.environ.pop, 'CORSU_TEST_STATE', None)
        self.current = self.release('0.22.0')
        corsu.save_state({'files': {}, 'components': ['firefox', 'minecraft'], 'disabled': ['minecraft'],
                          'release': {'version': '0.22.0', 'folder': str(self.current), 'installed_at': 1}})

    def publish(self, version, cut=None, checksum=None):
        name = update.ARCHIVES[corsu.PLATFORM]
        archive = self.served / name
        files = {'corsu/src/release.json': json.dumps({'version': version}).encode(),
                 'corsu/src/installer.py': FAKE_INSTALLER.encode()}
        if name.endswith('.zip'):
            with zipfile.ZipFile(archive, 'w') as bundle:
                for path, data in files.items():
                    bundle.writestr(path, data)
        else:
            tar_archive(archive, list(files.items()))
        data = archive.read_bytes()
        (self.served / (name + '.sha256')).write_text(f'{checksum or hashlib.sha256(data).hexdigest()}  {name}\n')
        if cut:
            archive.write_bytes(data[:cut])
        return archive

    def install(self, *arguments, base=True):
        environment = {'CORSU_DOWNLOAD_BASE': self.served.as_uri()} if base else {}
        with patch.dict(os.environ, environment), quiet() as output, redirect_stderr(io.StringIO()):
            code = update.main(['--install', *arguments])
        lines = output.getvalue().splitlines()
        result = json.loads(next(line for line in lines if line.startswith('@result '))[len('@result '):])
        self.progress = [line for line in lines if line.startswith('@progress ')]
        return code, result

    def test_update_runs_the_new_installer_with_the_recorded_parts(self):
        self.publish('0.23.0')
        code, result = self.install('--version', '0.23.0')
        self.assertEqual(code, 0, result)
        # The installer keeps minecraft (switched off) off; update.py passes what is recorded.
        self.assertEqual(json.loads(self.mark.read_text()), ['--yes', '--components', 'firefox', 'minecraft'])
        self.assertEqual((result['corsu'], result['from'], result['to'], result['restart_app']),
                         ('updated', '0.22.0', '0.23.0', True))
        self.assertTrue(any(line.startswith('@progress 74 Halfway') for line in self.progress), self.progress)
        self.assertFalse(list((self.data / 'tmp').iterdir()), 'download folder removed')
        self.assertFalse((self.data / 'lock').exists())

    def test_pinned_version_must_match_the_archive(self):
        self.publish('0.23.0')
        code, result = self.install('--version', '0.24.0')
        self.assertEqual((code, result['corsu']), (1, 'failed'))
        self.assertIn('not 0.24.0', result['error'])
        self.assertFalse(self.mark.exists())

    def test_truncated_or_tampered_archive_installs_nothing(self):
        self.publish('0.23.0', cut=100)
        code, result = self.install()
        self.assertEqual(result['corsu'], 'failed')
        self.assertIn('checksum', result['error'])
        self.publish('0.23.0', checksum='0' * 64)
        code, result = self.install()
        self.assertIn('checksum', result['error'])
        self.assertFalse(self.mark.exists())
        self.assertEqual(corsu.load_state()['release']['folder'], str(self.current))

    def test_download_cut_short_is_an_error(self):
        class Response(io.BytesIO):
            headers = {'Content-Length': '1000'}

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        with patch.object(update.urllib.request, 'urlopen', return_value=Response(b'x' * 10)), quiet():
            with self.assertRaisesRegex(OSError, 'cut short'):
                update.download('https://example.invalid/a', self.home / 'a')

    def test_older_archive_is_refused(self):
        self.publish('0.21.0')
        code, result = self.install()
        self.assertEqual(result['corsu'], 'failed')
        self.assertIn('older', result['error'])
        self.assertFalse(self.mark.exists())
        code, result = self.install('--version', '0.21.0', '--allow-downgrade')
        self.assertEqual(result['corsu'], 'updated', result)
        # An older installer may not keep switched-off parts off: it gets only the parts switched on.
        self.assertEqual(json.loads(self.mark.read_text()), ['--yes', '--components', 'firefox', '--allow-downgrade'])

    def test_failed_installer_is_reported(self):
        self.publish('0.23.0')
        with patch.dict(os.environ, {'CORSU_TEST_EXIT': '1'}):
            code, result = self.install()
        self.assertEqual((code, result['corsu']), (1, 'failed'))
        self.assertIn('0.22.0 is still in place', result['error'])

    def test_busy(self):
        sleeper = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        self.addCleanup(sleeper.wait)
        self.addCleanup(sleeper.kill)
        (self.data / 'lock').write_text(json.dumps({'pid': sleeper.pid, 'started': time.time(), 'action': 'install',
                                                    'token': 'x'}), encoding='utf-8')
        self.publish('0.23.0')
        code, result = self.install()
        self.assertEqual((result['corsu'], result['busy']), ('failed', True))
        self.assertIn('busy', result['error'])

    def test_latest_stable_release_by_exact_tag(self):
        releases = [{'tag_name': 'v0.24.0', 'draft': False, 'prerelease': True, 'html_url': 'u24'},
                    {'tag_name': 'v0.25.0', 'draft': True, 'prerelease': False, 'html_url': 'u25'},
                    {'tag_name': 'v0.23.0', 'draft': False, 'prerelease': False, 'html_url': 'u23'},
                    {'tag_name': 'v0.9.0', 'draft': False, 'prerelease': False, 'html_url': 'u9'}]
        with patch.object(update, 'fetch_latest', wraps=update.fetch_latest) as fetch, \
                patch.object(update.urllib.request, 'urlopen', side_effect=lambda *a, **k: io.BytesIO(json.dumps(releases).encode())):
            with patch.object(update, 'current', return_value='0.22.0'):
                info = update.check()
                self.assertEqual((info['latest'], info['tag'], info['status'], info['error']),
                                 ('0.23.0', 'v0.23.0', 'available', None))
                update.check()
                self.assertEqual(fetch.call_count, 1, 'saved for an hour (CHECK_EVERY)')
            with patch.object(update, 'current', return_value='0.23.0'):
                self.assertEqual(update.check()['status'], 'up_to_date')
            with patch.object(update, 'current', return_value='0.30.0'):
                # A development copy: the saved answer is older than this copy, so GitHub is asked again.
                self.assertEqual(update.check()['status'], 'ahead')
                self.assertEqual(fetch.call_count, 2)
        self.assertEqual(update.download_url('corsu-linux.tar.gz', '0.23.0'),
                         'https://github.com/Platykalt/corsu/releases/download/v0.23.0/corsu-linux.tar.gz')
        # Without --version, the latest stable tag is downloaded, by its exact address.
        with patch.object(update, 'check', return_value={'latest': '0.23.0', 'status': 'available', 'error': None}), \
                patch.object(update, 'download', side_effect=OSError('offline')) as download:
            code, result = self.install(base=False)
        self.assertIn('/releases/download/v0.23.0/', download.call_args_list[0].args[0])
        with patch.object(update, 'check', return_value={'latest': '0.22.0', 'status': 'up_to_date', 'error': None}):
            code, result = self.install(base=False)
        self.assertEqual((code, result['corsu']), (0, 'unchanged'))

    def test_offline_or_rate_limited(self):
        error = update.urllib.error.HTTPError('u', 403, 'rate limited', {}, None)
        with patch.object(update.urllib.request, 'urlopen', side_effect=error):
            info = update.check(force=True)
        self.assertEqual(info['status'], 'unknown')
        self.assertIn('GitHub limits', info['error'])
        with patch.object(update.urllib.request, 'urlopen', side_effect=AssertionError('asked again')):
            self.assertEqual(update.check()['status'], 'unknown')  # not asked again right away

    def test_preferences(self):
        self.assertEqual(update.preferences(), {'auto_update': False, 'vlc_complement': False})
        self.assertEqual(update.set_preference('auto_update', True), {'auto_update': True, 'vlc_complement': False})
        self.assertTrue(json.loads((self.data / 'preferences.json').read_text())['auto_update'])
        with self.assertRaises(ValueError):
            update.set_preference('auto_update', 'yes')
        with self.assertRaises(ValueError):
            update.set_preference('unknown', True)


if __name__ == '__main__':
    unittest.main()
