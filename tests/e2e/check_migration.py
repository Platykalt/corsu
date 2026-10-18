#!/usr/bin/env python3
"""Migrating a real installation of a published Corsu to the archives being checked, what check_update.py does not
look at (Linux). Everything happens in a throwaway home folder; nothing reaches the real user's Corsu or programs.

Usage: check_migration.py --archives DIR [--from 0.24.0]

Needs Firefox (CORSU_FIREFOX names its folder) and VLC from the system's packages with its Corsican catalogue.
 0. the archive of DIR: its .sha256, the Discord plugin built into it (Vencord/dist), and with Node.js the dictionary
    fingerprint its renderer reports equal to the one computed from its dictionary.json;
 1. the published version (checked against its .sha256) installed with Firefox and VLC, the VLC complement on, then
    Firefox switched off; its extracted archive deleted. Personal files are put next to Corsu's: in its data folder,
    the home folder, the applications menu and the Firefox profile;
 2. the installed copy's own update.py installs DIR's archive: Firefox stays off, VLC and its complement stay on, one
    copy in use, the new window's files (src/app, appearance.py) and the Discord plugin are the archive's, the bundled
    Python is kept and the launchers fall back to it, no download left in the data folder;
 3. the extracted archive deleted: the Corsu menu entry opens the window, Firefox Corsu starts Firefox;
 4. appearance settings saved, then a repair and a later update (the same files saying 99.0.0): they stay, and the
    published version's copy is removed by that later update;
 5. uninstalling: the launchers go, every personal file stays as it was.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_update  # noqa: E402
from check_update import check, check_launchers_complete, extract, fetch_published, releases, run, step  # noqa: E402
from check_update_apps import entry  # noqa: E402
from e2e import data_directory, isolated_environment, launchers, state  # noqa: E402
import update  # noqa: E402

DIST = ('patcher.js', 'preload.js', 'renderer.js', 'renderer.css', 'vencordDesktopRenderer.js',
        'vencordDesktopRenderer.css', 'vencordDesktopPreload.js', 'vencordDesktopMain.js')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def same_files(source, copy, names):
    """Names of `names` (relative to both folders) that are missing from `copy` or differ from `source`."""
    return [name for name in names if not (copy / name).is_file() or digest(copy / name) != digest(source / name)]


def check_plugin(root):
    """The Discord plugin built into the archive, and the dictionary it carries."""
    dist = root / 'Vencord/dist'
    present = [name for name in DIST if (dist / name).is_file()]
    check({'patcher.js', 'renderer.js', 'vencordDesktopRenderer.js'} <= set(present), f'the archive carries the built plugin: {present}')
    dictionary = json.loads((root / 'Vencord/src/userplugins/corsu/dictionary.json').read_text(encoding='utf-8'))
    for name in ('renderer.js', 'vencordDesktopRenderer.js'):
        bundle = (dist / name).read_text(encoding='utf-8')
        check('[CorsuMissing]' in bundle and re.search(r'dictionary:\w+\(\)', bundle),
              f'{name} has the Corsu plugin and its dictionary fingerprint')
    if not shutil.which('node'):
        print('NOT CHECKED: the fingerprint value (Node.js is missing here)', flush=True)
        return
    from check_discord_activity import fingerprint
    from check_discord_built import EXTRACT
    expected = fingerprint(dictionary)
    with tempfile.TemporaryDirectory() as folder:
        for name in ('renderer.js', 'vencordDesktopRenderer.js'):
            module = Path(folder) / f'{name}.translator.js'
            subprocess.run(['node', '-e', EXTRACT, str(dist / name), str(module)], check=True)
            found = subprocess.run(['node', '-e', 'global.window = {}; global.document = {}; require(process.argv[1]); '
                                    'console.log(window.CorsuBuilt.dictionaryFingerprint())', str(module)],
                                   capture_output=True, text=True, check=True).stdout.strip()
            check(found == expected, f'{name} reports the dictionary fingerprint of dictionary.json: {found}')


def personal_files(home):
    """Files of the person's own, next to what Corsu writes, with their content."""
    data = data_directory(home)
    profile = home / '.mozilla/firefox/abcd1234.default-release'
    profile.mkdir(parents=True)
    (home / '.mozilla/firefox/profiles.ini').write_text(
        '[Profile0]\nName=default-release\nIsRelative=1\nPath=abcd1234.default-release\nDefault=1\n\n'
        '[General]\nStartWithLastProfile=1\nVersion=2\n', encoding='utf-8')
    files = {
        data / 'my-notes.txt': 'notes kept in the Corsu folder by hand\n',
        data / 'mine/keep.txt': 'a folder of my own in the Corsu folder\n',
        home / 'Documents/letter.txt': 'a letter\n',
        home / '.local/bin/my-script': '#!/bin/sh\necho mine\n',
        home / '.local/share/applications/my-own.desktop': '[Desktop Entry]\nType=Application\nName=Mine\nExec=true\n',
        profile / 'bookmarks-decoy.json': '{"mine": true}\n',
        profile / 'user.js': 'user_pref("browser.startup.homepage", "https://example.org/");\n',
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    return files


def check_personal_files(files, moment):
    changed = [str(path) for path, text in files.items() if not path.is_file() or path.read_text(encoding='utf-8') != text]
    check(not changed, f'{moment}: personal files untouched {changed or ""}')


def check_launchers_work(home, environment):
    """Firefox Corsu starts Firefox; the Corsu menu entry opens the window's server."""
    firefox = subprocess.run([str(home / '.local/bin/firefox-corsu'), '--version'], env=environment, capture_output=True,
                             text=True, timeout=300)
    check(firefox.returncode == 0 and 'Firefox' in firefox.stdout, f'Firefox Corsu starts Firefox: {firefox.stdout.strip()}')
    line = next(line for line in launchers(home)[1].read_text(encoding='utf-8').splitlines() if line.startswith('Exec='))
    command = shlex.split(line[5:])
    with tempfile.TemporaryFile() as output:
        app = subprocess.Popen(command, env=environment, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            address = None
            for _ in range(60):
                output.seek(0)
                found = re.search(rb'http://localhost:(\d+)/', output.read())
                if found:
                    address = f'http://127.0.0.1:{found[1].decode()}/'
                    break
                if app.poll() is not None:
                    break
                time.sleep(1)
            check(address is not None, f'the Corsu menu entry starts the window ({" ".join(command)})')
            with urllib.request.urlopen(address, timeout=30) as response:
                check(response.status == 200, f'the window answers at {address}')
        finally:
            os.killpg(app.pid, signal.SIGTERM)
            app.wait(timeout=30)


def check_runtime(home):
    """The archive's Python is kept, and the launchers fall back to it when they run on the system's."""
    copies = sorted((data_directory(home) / 'runtime').glob('*/python/bin/python3'))
    check(len(copies) == 1, f'one copy of the bundled Python is kept: {[str(path) for path in copies]}')
    wrapper = data_directory(home) / 'bin/corsu-python'
    for launcher in launchers(home):
        text = launcher.read_text(encoding='utf-8')
        check(str(wrapper) in text or str(copies[0]) in text, f'{launcher.name} starts Corsu through its own Python or the fallback')
    if wrapper.exists():
        check(str(copies[0]) in wrapper.read_text(encoding='utf-8'), 'the fallback script names the kept copy')


def later_archive(new_root, work, version):
    """The same files saying `version`, packed as the release archives are."""
    later = work / f'later-{version}'
    bumped = check_update.bumped(new_root, version, later / 'corsu')
    (later / 'dist').mkdir()
    with tarfile.open(later / 'dist' / check_update.ARCHIVE, 'w:gz') as archive:
        archive.add(bumped, arcname='corsu')
    (later / 'dist' / (check_update.ARCHIVE + '.sha256')).write_text(
        f'{check_update.sha256(later / "dist" / check_update.ARCHIVE)}  {check_update.ARCHIVE}\n', encoding='utf-8')
    shutil.rmtree(later / 'corsu')
    return later / 'dist'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--archives', type=Path, required=True)
    parser.add_argument('--from', dest='version', default='0.24.0')
    arguments = parser.parse_args()
    archives = arguments.archives.resolve()
    work = Path(tempfile.mkdtemp(prefix='corsu-migration-'))
    home = work / 'home'
    (home / 'tmp').mkdir(parents=True)
    environment = {**isolated_environment(home), 'CORSU_LANG': 'en', 'TMPDIR': str(home / 'tmp')}
    for name in ('CORSU_LOCK_TOKEN', 'CORSU_DEPLOYED', 'CORSU_APP_ROOT', 'CORSU_DOWNLOAD_BASE', 'CORSU_SETUP_WINDOW',
                 'DBUS_SESSION_BUS_ADDRESS', 'DISPLAY', 'WAYLAND_DISPLAY', 'XDG_DATA_HOME', 'XDG_DATA_DIRS',
                 'XDG_CONFIG_DIRS', 'XDG_RUNTIME_DIR'):
        environment.pop(name, None)

    step('0. The archive being checked')
    check(check_update.sha256(archives / check_update.ARCHIVE)
          == (archives / (check_update.ARCHIVE + '.sha256')).read_text(encoding='utf-8').split()[0], 'it matches its .sha256')
    new_root = extract(archives / check_update.ARCHIVE, work / 'new')
    new_version = update.installer.release_version(new_root)
    check_plugin(new_root)
    interface = sorted(path.relative_to(new_root).as_posix() for path in (new_root / 'src/app').rglob('*') if path.is_file())
    check(any(name.endswith('.js') for name in interface) and any(name.endswith('.css') for name in interface)
          and (new_root / 'src/appearance.py').is_file(), f'the archive has the window\'s files ({len(interface)} in src/app)')

    step(f'1. Corsu {arguments.version} installed, the VLC complement on, Firefox switched off')
    old_root = extract(fetch_published(arguments.version, work / 'published'), work / 'old')
    files = personal_files(home)
    run(old_root, environment, 'src/installer.py', '--yes', '--components', 'firefox', 'vlc', '--vlc-complement', 'on')
    shutil.rmtree(work / 'old')
    shutil.rmtree(work / 'published')
    old_copy = releases(home) / state(home)['release']['folder'].rsplit('/', 1)[-1]
    run(old_copy, environment, 'src/installer.py', '--disable', 'firefox')
    check('firefox' in state(home).get('disabled', []) and 'VLC_DATA_PATH=' in entry(home),
          'Firefox switched off, VLC in Corsican with the complement')
    check_personal_files(files, f'{arguments.version} installed')

    step(f'2. Update {arguments.version} → {new_version} by the installed copy\'s update.py')
    run(old_copy, {**environment, 'CORSU_DOWNLOAD_BASE': archives.as_uri()}, 'src/update.py', '--install')
    after = state(home)
    check(after.get('release', {}).get('version') == new_version, f'installation.json records {new_version}')
    copy = Path(after['release']['folder'])
    check(sorted(after.get('components', [])) == ['firefox', 'vlc'], f'the same parts: {after.get("components")}')
    check('firefox' in after.get('disabled', []) and 'vlc' not in after.get('disabled', []), 'Firefox still off, VLC on')
    check('VLC_DATA_PATH=' in entry(home), 'the VLC complement is still on')
    check_launchers_complete(home, copy.name)
    check(set(path.name for path in releases(home).iterdir()) == {old_copy.name, copy.name},
          'two copies: the new one and the previous one, kept until the next update')
    check(not same_files(new_root, copy, interface + ['src/appearance.py']), 'the window\'s files are the archive\'s')
    check(not same_files(new_root, copy, [f'Vencord/dist/{name}' for name in DIST if (new_root / 'Vencord/dist' / name).is_file()]),
          'the Discord plugin is the one built into the archive')
    check(not list((data_directory(home) / 'tmp').glob('update-*')), 'no download left in the data folder')
    check_runtime(home)
    check_personal_files(files, 'after the update')

    step('3. The extracted archive deleted: the launchers still work')
    shutil.rmtree(work / 'new')
    check_launchers_work(home, environment)

    step('4. Appearance settings kept by a repair and a later update')
    settings = {'format': 1, 'theme': 'dark', 'palette': 'mare', 'accent': '#336699', 'density': 'compact',
                'background': 'none', 'image': None, 'dim': 0.4, 'blur': 6}
    saved = data_directory(home) / 'appearance/settings.json'
    subprocess.run([sys.executable, '-c', 'import sys, json; sys.path.insert(0, sys.argv[1]); import appearance; '
                    'appearance.save(json.loads(sys.argv[2]))', str(copy / 'src'), json.dumps(settings)],
                   env=environment, check=True)
    kept = saved.read_bytes()
    check(json.loads(kept)['palette'] == 'mare', 'appearance settings saved')
    count = len(state(home)['files'])
    run(copy, environment, 'src/installer.py', '--yes')
    check(saved.read_bytes() == kept and len(state(home)['files']) == count, 'a repair keeps them, nothing recorded twice')
    check(state(home)['release']['folder'] == str(copy), 'the repair kept the same copy')
    later = later_archive(extract(archives / check_update.ARCHIVE, work / 'again'), work, '99.0.0')
    shutil.rmtree(work / 'again')
    run(copy, {**environment, 'CORSU_DOWNLOAD_BASE': later.as_uri()}, 'src/update.py', '--install', '--version', '99.0.0')
    check(state(home)['release']['version'] == '99.0.0', 'updated again, to 99.0.0')
    check(saved.read_bytes() == kept, 'the later update keeps them')
    check('firefox' in state(home).get('disabled', []) and 'VLC_DATA_PATH=' in entry(home), 'Firefox still off, complement on')
    if update.installer.clients_running():
        print('Note: Discord or Vesktop is open on this computer, so copies loaded before are kept on purpose.')
    else:
        check(not old_copy.exists(), f'the {arguments.version} copy is removed by the later update')
    check_launchers_complete(home, Path(state(home)['release']['folder']).name)
    check_runtime(home)
    check_launchers_work(home, environment)

    step('5. Uninstall')
    current = Path(state(home)['release']['folder'])
    run(current, environment, 'src/installer.py', '--uninstall', '--yes')
    check(state(home)['files'] == {}, 'nothing left recorded')
    for launcher in launchers(home):
        check(not launcher.exists(), f'launcher removed: {launcher.name}')
    check_personal_files(files, 'after uninstalling')
    print(f'\nPASS: migration from {arguments.version} to {new_version}', flush=True)
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    sys.exit(main())
