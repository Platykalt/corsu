#!/usr/bin/env python3
"""Updating a real installation, in an isolated home folder (docs/update-architecture.md). Never touches the real
user's Corsu, launchers or programs.

Usage: check_update.py --archives DIR [--from 0.21.0 0.22.0 ...]

DIR holds the archives being checked (corsu-linux.tar.gz, corsu-windows.zip or corsu-macos.tar.gz and their .sha256),
as CI builds them. For each published version given with --from (default 0.21.0 and 0.22.0), its archive is
downloaded from GitHub's release page and checked against its published .sha256, then, in a fresh home folder:

 1. that version is installed (Firefox, and Minecraft with a fake Prism Launcher instance when it supports it);
 2. one part is switched off and a Minecraft setting changed by hand;
 3. the archives of DIR are installed over it as an update: by the installed copy's own update.py when it accepts
    CORSU_DOWNLOAD_BASE (0.22), else by re-running the one-line install script (install/get.sh, get.ps1) — the two
    ways people update. Checked: the part switched off stays off, the hand-made change and the recorded originals
    are kept, the launchers point at the new copy, only one copy is in use and the previous one is kept once;
 4. the same version again is a repair: nothing recorded twice;
 5. an older copy is refused;
 6. an update from a truncated archive changes nothing, and an update killed mid-way leaves launchers on a complete
    copy and is completed by running it again (its stale lock is taken over);
 7. two installers at once: one runs, the other says Corsu is busy;
 8. uninstalling puts the original settings back.

Firefox must be installed (on Linux CI, CORSU_FIREFOX names the folder of a downloaded Firefox).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PROJECT / 'src'))
import e2e  # noqa: E402
from e2e import PLATFORM, data_directory, fake_prism_instance, isolated_environment, launchers, state  # noqa: E402
import update  # noqa: E402  (safe_extract only; nothing here uses the real data folder)

RELEASES = 'https://github.com/Platykalt/corsu/releases/download'
ARCHIVE = {'linux': 'corsu-linux.tar.gz', 'macos': 'corsu-macos.tar.gz', 'windows': 'corsu-windows.zip'}[PLATFORM]
RELEASE_NAME = re.compile(r'[0-9a-f]{16}')


def step(text):
    print(f'\n=== {text}', flush=True)


def check(condition, message):
    if not condition:
        raise SystemExit(f'FAIL: {message}')
    print(f'PASS: {message}', flush=True)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch_published(version, folder):
    """The published archive of `version` and its .sha256, checked."""
    folder.mkdir(parents=True, exist_ok=True)
    for name in (ARCHIVE, ARCHIVE + '.sha256'):
        request = urllib.request.Request(f'{RELEASES}/v{version}/{name}', headers={'User-Agent': 'corsu-e2e'})
        with urllib.request.urlopen(request, timeout=300) as response:
            (folder / name).write_bytes(response.read())
    expected = (folder / (ARCHIVE + '.sha256')).read_text(encoding='utf-8').split()[0].lower()
    check(sha256(folder / ARCHIVE) == expected, f'published {version} archive matches its .sha256')
    return folder / ARCHIVE


def extract(archive, folder):
    update.safe_extract(archive, folder)
    root = folder / 'corsu'
    check(update.installer.release_version(root) is not None, f'{archive.name} extracted with its release.json')
    return root


def python_of(root):
    """The archive's own Python when it has one (as Corsu's launch scripts choose it on macOS and Windows), else this
    one."""
    processor = 'aarch64' if PLATFORM == 'macos' and os.uname().machine == 'arm64' else 'x86_64'
    bundled = root / 'runtime' / processor / 'python' / ('python.exe' if PLATFORM == 'windows' else 'bin/python3')
    return str(bundled) if bundled.exists() and PLATFORM != 'linux' else sys.executable


def run(root, environment, *arguments, expect=0, python=None):
    command = [python or python_of(root), *map(str, arguments)]
    print('+ ' + ' '.join(command), flush=True)
    result = subprocess.run(command, cwd=root, env=environment, text=True, encoding='utf-8', errors='replace',
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout[-6000:], flush=True)
    if expect is not None and result.returncode != expect:
        raise SystemExit(f'FAIL: {arguments} exited {result.returncode}, expected {expect}')
    return result


def releases(home):
    return data_directory(home) / 'releases'


def recorded(home):
    """The installed release and the copy the Corsu menu entry opens."""
    current = state(home).get('release') or {}
    return re.split(r'[\\/]', current.get('folder', ''))[-1]


def copies_in_use(home):
    """Release folders any launcher or file Corsu wrote mentions."""
    used = set()
    folder = releases(home)
    for name in state(home)['files']:
        path = Path(name)
        files = [path] if path.is_file() else [file for file in path.rglob('*') if file.is_file()] if path.is_dir() else []
        for file in files:
            if file.name == 'app.asar' or file.stat().st_size > 4_000_000:
                continue
            for release in folder.iterdir():
                # Windows shortcuts keep the long form of the path (runneradmin, not RUNNER~1), in any case.
                forms = {str(release), str(release.resolve())}
                if os.name == 'nt':
                    forms |= {form.lower() for form in forms} | {form.upper() for form in forms}
                if any(e2e.mentions(file, form) for form in forms):
                    used.add(release.name)
    return used


def check_launchers_complete(home, expected=None):
    used = copies_in_use(home)
    check(used, f'launchers point into the data folder: {sorted(used)}')
    for name in used:
        copy = releases(home) / name
        check(RELEASE_NAME.fullmatch(name) and (copy / 'src/app.py').is_file() and (copy / 'src/release.json').is_file(),
              f'launchers point at a complete copy: {name}')
    if expected:
        check(used == {expected}, f'only the installed copy is in use ({expected}); in use: {sorted(used)}')


def originals(home):
    """What uninstalling would put back: backups' content and recorded original values."""
    result = {}
    for name, record in state(home)['files'].items():
        if record.get('backup'):
            result[name] = ('backup', sha256(record['backup']) if Path(record['backup']).exists() else None)
        for key in ('options_original', 'json_changes', 'setting'):
            if record.get(key) is not None:
                value = record[key]
                if key == 'json_changes':
                    value = {field: (saved['existed'], saved['original']) for field, saved in value.items()}
                if key == 'setting':
                    value = value.get('original')
                result[name + '#' + key] = value
    return result


def bumped(root, version, folder):
    """A copy of an extracted release that says it is `version`: a newer (or older) release made from the same files."""
    shutil.copytree(root, folder, symlinks=True)
    manifest = json.loads((folder / 'src/release.json').read_text(encoding='utf-8'))
    manifest['version'] = version
    (folder / 'src/release.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return folder


def get_script(new_root, environment, archives):
    """Re-run the one-line install, as a person updating by hand does, with the archives being checked."""
    environment = {**environment, 'CORSU_DOWNLOAD_BASE': archives.as_uri(), 'CI': '1'}
    if PLATFORM == 'windows':
        command = ['pwsh', '-NoProfile', '-File', str(new_root / 'install/get.ps1'), '--text', '--yes']
    else:
        command = ['sh', str(new_root / 'install/get.sh'), '--text', '--yes']
    print('+ ' + ' '.join(command), flush=True)
    result = subprocess.run(command, env=environment, text=True, encoding='utf-8', errors='replace',
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    print(result.stdout[-6000:], flush=True)
    check(result.returncode == 0, 'the one-line install script updated the installation')


def kill_tree(process):
    if PLATFORM == 'windows':
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(process.pid)], capture_output=True)
    else:
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def scenario(old_version, archives, work):
    home = work / f'home-{old_version}'
    home.mkdir(parents=True)
    (home / 'tmp').mkdir()
    environment = {**isolated_environment(home), 'CORSU_LANG': 'en', 'TMPDIR': str(home / 'tmp')}
    # Nothing reaches the desktop session of the computer running the check.
    for name in ('CORSU_LOCK_TOKEN', 'CORSU_DEPLOYED', 'CORSU_APP_ROOT', 'CORSU_DOWNLOAD_BASE', 'CORSU_SETUP_WINDOW',
                 'DBUS_SESSION_BUS_ADDRESS', 'DISPLAY', 'WAYLAND_DISPLAY', 'XDG_DATA_HOME', 'XDG_DATA_DIRS',
                 'XDG_CONFIG_DIRS', 'XDG_RUNTIME_DIR'):
        environment.pop(name, None)
    old_root = extract(fetch_published(old_version, work / f'published-{old_version}'), work / f'old-{old_version}')
    new_root = extract(archives / ARCHIVE, work / f'new-{old_version}')
    new_version = update.installer.release_version(new_root)
    old_source = (old_root / 'src/installer.py').read_text(encoding='utf-8')
    has_minecraft = "'minecraft'" in old_source

    step(f'1. Corsu {old_version} installed')
    components = ['firefox']
    instance = None
    if has_minecraft:
        instance = fake_prism_instance(home, (old_root / 'minecraft/java/VERSION').read_text(encoding='utf-8').strip())
        components.append('minecraft')
    run(old_root, environment, 'src/installer.py', '--yes', '--components', *components)
    shutil.rmtree(old_root.parent)  # the downloaded archive is gone, as after a real installation
    first = {path.name for path in releases(home).iterdir()}
    check(len(first) == 1, f'{old_version} deployed one copy: {first}')
    old_copy = releases(home) / first.pop()

    step('2. One part switched off, a setting changed by hand')
    off = 'minecraft' if has_minecraft else 'firefox'
    run(old_copy, environment, 'src/installer.py', '--disable', off)
    check(off in state(home).get('disabled', []), f'{off} switched off')
    if instance:
        options = instance / 'options.txt'
        check('lang:en_us' in options.read_text(encoding='utf-8'), 'switching Minecraft off gave its language back')
        options.write_text(options.read_text(encoding='utf-8') + 'guiScale:3\n', encoding='utf-8')
    before = originals(home)
    files_before = set(state(home)['files'])

    step(f'3. Update {old_version} → {new_version}')
    old_update = (old_copy / 'src/update.py').read_text(encoding='utf-8')
    if 'CORSU_DOWNLOAD_BASE' in old_update:
        # The installed version's own updater, as its window runs it.
        run(old_copy, {**environment, 'CORSU_DOWNLOAD_BASE': archives.as_uri()}, 'src/update.py', '--install')
    else:
        get_script(new_root, environment, archives)
    after = state(home)
    check(after.get('release', {}).get('version') == new_version, f'installation.json records {new_version}')
    current = releases(home) / recorded(home)
    check(current != old_copy and (current / 'src/app.py').is_file(), f'new copy {current.name} installed')
    check(Path(after['release'].get('python', '')).exists(), 'the recorded Python exists')
    check(off in after.get('disabled', []), f'{off} is still switched off after the update')
    check(set(after.get('components', [])) == set(components), f'the same parts are recorded: {after.get("components")}')
    if instance:
        text = options.read_text(encoding='utf-8')
        check('guiScale:3' in text, 'the hand-made Minecraft setting is kept')
        check('lang:en_us' in text, 'Minecraft, switched off, was not switched on by the update')
    kept = {name: value for name, value in originals(home).items() if name in before}
    check(kept == {name: value for name, value in before.items() if name in kept}, 'recorded originals unchanged')
    check(not [name for name in before if name.split('#')[0] in files_before and name not in originals(home)
               and Path(name.split('#')[0]).exists()], 'no original forgotten')
    check_launchers_complete(home, current.name)
    check(old_copy.is_dir(), 'the previous copy is kept until the next successful update')
    check(after.get('previous_release', {}).get('version') == old_version, 'the previous release is recorded')

    step('4. Same version again: repair')
    count = len(state(home)['files'])
    run(current, environment, 'src/installer.py', '--yes')
    check(len(state(home)['files']) == count, 'a repair records nothing twice')
    check(recorded(home) == current.name and off in state(home).get('disabled', []), 'repair kept the release and choices')
    check(all(originals(home).get(name) == value for name, value in kept.items()), 'repair kept the originals')

    step('5. An older copy is refused')
    older = bumped(new_root, '0.0.1', work / f'older-{old_version}')
    run(older, environment, 'src/installer.py', '--yes', expect=3)
    check(recorded(home) == current.name, 'nothing changed after the refusal')

    step('6a. Update from a truncated archive')
    broken = work / f'broken-{old_version}'
    broken.mkdir()
    data = (archives / ARCHIVE).read_bytes()
    (broken / ARCHIVE).write_bytes(data[:len(data) // 3])
    shutil.copy(archives / (ARCHIVE + '.sha256'), broken / (ARCHIVE + '.sha256'))
    result = run(current, {**environment, 'CORSU_DOWNLOAD_BASE': broken.as_uri()}, 'src/update.py', '--install', expect=1)
    line = next(line for line in result.stdout.splitlines() if line.startswith('@result '))
    check(json.loads(line[len('@result '):])['corsu'] == 'failed', 'the truncated archive is reported as failed')
    check(recorded(home) == current.name, 'nothing installed from the truncated archive')
    check_launchers_complete(home, current.name)

    step('6b. Update killed mid-way, then run again')
    newer_version = '.'.join([str(int(new_version.split('.')[0]) + 1), '0', '0'])
    newer = bumped(new_root, newer_version, work / f'newer-{old_version}')
    command = [python_of(newer), str(newer / 'src/installer.py'), '--yes']
    print('+ ' + ' '.join(command), flush=True)
    options_kw = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if PLATFORM == 'windows' else {'start_new_session': True}
    process = subprocess.Popen(command, cwd=newer, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace', **options_kw)
    killed = False
    for line in process.stdout:
        print(line, end='', flush=True)
        # The installed copy's installer has started: the new copy is deployed, the launchers not all switched yet.
        if line.startswith('+ ') and 'installer.py' in line:
            time.sleep(0.3)
            killed = process.poll() is None
            if killed:
                kill_tree(process)
            break
    if not killed:
        print(process.stdout.read(), flush=True)
    process.wait()
    print(f'killed mid-way: {killed}', flush=True)
    check_launchers_complete(home)
    check(bool(recorded(home)), 'installation.json still readable after the kill')
    run(newer, environment, 'src/installer.py', '--yes')
    check(state(home)['release']['version'] == newer_version, f'running it again completed the update to {newer_version}')
    check(off in state(home).get('disabled', []), f'{off} still off')
    check_launchers_complete(home, recorded(home))
    check(not (data_directory(home) / 'lock').exists(), 'no lock left')
    current = releases(home) / recorded(home)
    if update.installer.clients_running():
        print('Note: Discord or Vesktop is open on this computer, so copies loaded before are kept on purpose.')
    else:
        check(not old_copy.exists(), f'the {old_version} copy is removed by the next successful update')

    step('7. Two installers at once')
    busy = {**environment, 'CORSU_LOCK_WAIT': '0'}
    command = [python_of(current), str(current / 'src/installer.py'), '--yes']
    # Another Corsu task holds the lock (as a running installation or update would): the installer must stop, busy.
    holder = subprocess.Popen([python_of(current), '-c', 'import sys, time; sys.path.insert(0, sys.argv[1]); import corsu\n'
                               'with corsu.lock("test"):\n    print("held", flush=True); time.sleep(60)',
                               str(current / 'src')], env=environment, stdout=subprocess.PIPE, text=True)
    try:
        check(holder.stdout.readline().strip() == 'held', 'another task holds the lock')
        before = json.dumps(state(home), sort_keys=True)
        blocked = subprocess.run(command, cwd=current, env=busy, capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', timeout=900)
        print(blocked.stdout[-2000:] + blocked.stderr[-2000:])
        check(blocked.returncode == 75, f'stopped as busy while another task runs: exit {blocked.returncode}')
        check('already busy' in blocked.stdout + blocked.stderr, 'the busy message names it')
        check(json.dumps(state(home), sort_keys=True) == before, 'nothing written while busy')
    finally:
        holder.kill()
        holder.wait(timeout=30)
    # Two at once: either the second finds the lock (75), or the first was already done and it runs after it (0);
    # never both writing together, and the record stays whole.
    runs = [subprocess.Popen(command, cwd=current, env=busy, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding='utf-8', errors='replace') for _ in range(2)]
    outputs = [process.communicate(timeout=900) for process in runs]
    codes = sorted(process.returncode for process in runs)
    for output in outputs:
        print(output[0][-3000:])
    check(codes in ([0, 75], [0, 0]), f'one after the other, or the other stopped as busy: exit codes {codes}')
    if codes == [0, 75]:
        check(any('already busy' in output[0] for output in outputs), 'the busy message names it')
    check(recorded(home) == current.name and len(state(home)['files']) >= 1, 'state consistent after both')

    step('8. Uninstall')
    run(current, environment, 'src/installer.py', '--uninstall', '--yes')
    check(state(home)['files'] == {}, 'nothing left recorded')
    for launcher in launchers(home):
        check(not launcher.exists(), f'launcher removed: {launcher.name}')
    if instance:
        text = options.read_text(encoding='utf-8')
        check('lang:en_us' in text and 'guiScale:3' in text, 'Minecraft options: original language, own change kept')
        check(not list((instance / 'resourcepacks').glob('corsu*.zip')), 'Corsu pack removed')
    print(f'\nPASS: update from {old_version} to {new_version}, repair, refusal, recovery, lock, uninstall', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--archives', type=Path, required=True)
    parser.add_argument('--from', dest='versions', nargs='+', default=['0.21.0', '0.22.0'])
    parser.add_argument('--keep', action='store_true', help='Keep the temporary folder (to look at a failure)')
    args = parser.parse_args()
    archives = args.archives.resolve()
    check(sha256(archives / ARCHIVE) == (archives / (ARCHIVE + '.sha256')).read_text(encoding='utf-8').split()[0].lower(),
          f'{ARCHIVE} matches its .sha256')
    work = Path(tempfile.mkdtemp(prefix='corsu-update-'))
    try:
        for version in args.versions:
            scenario(version, archives, work)
    finally:
        if args.keep:
            print(f'Kept: {work}')
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    main()
