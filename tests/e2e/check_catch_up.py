#!/usr/bin/env python3
"""Catching up from an old Corsu without its update button (docs/update-diagnosis.md), in an isolated home folder.
Never touches the real user's Corsu, launchers or programs.

Usage: check_catch_up.py [--from 0.24.0] [--archives DIR]

A person whose window says "up to date" while a newer release is out runs the one-line install again
(install/get.sh, get.ps1). Without --archives, this is the real public path: get.sh downloads the latest release from
GitHub. With --archives DIR, it installs the archives of DIR (CORSU_DOWNLOAD_BASE) instead. Steps:

 1. the published --from version is installed (Firefox), then the person's own state is made: Firefox switched off,
    preferences.json (automatic updates on), a background picture and a review in the data folder, and the saved
    answer of an old check (update.json: "latest 0.24.0, checked now");
 2. the one-line install is run: the new version is installed, Firefox stays off, the preferences and personal files
    are unchanged, one copy is in use, the previous one is kept once;
 3. running it again is a repair: nothing recorded twice, the same copy;
 4. the old copy's installer is then refused (no downgrade);
 5. without --archives, a saved answer older than the installed copy (as the old version leaves it) is asked again by
    this source tree's update.py --check, which asks GitHub once.

Firefox must be installed (CORSU_FIREFOX names its folder on Linux, as in the CI and the test containers).
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PROJECT / 'src'))
from check_update import (ARCHIVE, PLATFORM, check, check_launchers_complete, copies_in_use, extract,  # noqa: E402
                          fetch_published, recorded, releases, run, sha256, step)
from e2e import data_directory, isolated_environment, state  # noqa: E402


def one_line_install(environment, archives):
    """install/get.sh (get.ps1 on Windows) from this source tree, as `curl … | sh` runs it, answering yes."""
    if archives:
        environment = {**environment, 'CORSU_DOWNLOAD_BASE': archives.as_uri()}
    if PLATFORM == 'windows':
        command = ['pwsh', '-NoProfile', '-File', str(PROJECT / 'install/get.ps1'), '--text', '--yes']
    else:
        command = ['sh', str(PROJECT / 'install/get.sh'), '--text', '--yes']
    print('+ ' + ' '.join(command), flush=True)
    result = subprocess.run(command, env=environment, text=True, encoding='utf-8', errors='replace',
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    print(result.stdout[-6000:], flush=True)
    check(result.returncode == 0, f'the one-line install ended with code 0 (got {result.returncode})')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--from', dest='version', default='0.24.0')
    parser.add_argument('--archives', type=Path, help='Install these archives instead of the latest public release')
    parser.add_argument('--keep', action='store_true', help='Keep the temporary folder (to look at a failure)')
    args = parser.parse_args()
    archives = args.archives.resolve() if args.archives else None
    if archives:
        check(sha256(archives / ARCHIVE) == (archives / (ARCHIVE + '.sha256')).read_text(encoding='utf-8').split()[0].lower(),
              f'{ARCHIVE} matches its .sha256')
    work = Path(tempfile.mkdtemp(prefix='corsu-catch-up-'))
    try:
        home = work / 'home'
        (home / 'tmp').mkdir(parents=True)
        environment = {**isolated_environment(home), 'CORSU_LANG': 'en', 'TMPDIR': str(home / 'tmp')}
        for name in ('CORSU_LOCK_TOKEN', 'CORSU_DEPLOYED', 'CORSU_APP_ROOT', 'CORSU_DOWNLOAD_BASE', 'CORSU_SETUP_WINDOW',
                     'DBUS_SESSION_BUS_ADDRESS', 'DISPLAY', 'WAYLAND_DISPLAY', 'XDG_DATA_HOME', 'XDG_DATA_DIRS',
                     'XDG_CONFIG_DIRS', 'XDG_RUNTIME_DIR'):
            environment.pop(name, None)
        data = data_directory(home)

        step(f'1. Corsu {args.version} installed, with the person\'s own state')
        old_root = extract(fetch_published(args.version, work / 'published'), work / 'old')
        run(old_root, environment, 'src/installer.py', '--yes', '--components', 'firefox')
        old_copy = releases(home) / recorded(home)
        run(old_copy, environment, 'src/installer.py', '--disable', 'firefox')
        check('firefox' in state(home).get('disabled', []), 'Firefox switched off')
        preferences = {'auto_update': True, 'vlc_complement': False}
        (data / 'preferences.json').write_text(json.dumps(preferences), encoding='utf-8')
        personal = {data / 'appearance' / 'background.jpg': os.urandom(4096),
                    data / 'review.json': json.dumps({'Discord': {'Bio': 'Biografia'}}).encode()}
        for path, content in personal.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (data / 'update.json').write_text(json.dumps({'format': 2, 'checked': time.time(), 'latest': args.version,
                                                      'tag': 'v' + args.version, 'url': 'u'}), encoding='utf-8')
        files_before = set(state(home)['files'])

        step('2. The one-line install, over it')
        one_line_install(environment, archives)
        after = state(home)
        new_version = after.get('release', {}).get('version')
        check(new_version and new_version != args.version, f'installation.json records a new version: {new_version}')
        current = releases(home) / recorded(home)
        check(current != old_copy and (current / 'src/app.py').is_file(), f'new copy {current.name} installed')
        check('firefox' in after.get('disabled', []), 'Firefox is still switched off')
        check(set(after.get('components', [])) == {'firefox'}, f'the same parts are recorded: {after.get("components")}')
        check(json.loads((data / 'preferences.json').read_text(encoding='utf-8')) == preferences, 'preferences kept')
        for path, content in personal.items():
            check(path.read_bytes() == content, f'personal file kept: {path.relative_to(data)}')
        check(files_before <= set(after['files']), 'nothing recorded before is forgotten')
        check_launchers_complete(home, current.name)
        check(old_copy.is_dir(), 'the previous copy is kept until the next successful update')

        step('3. Again: a repair')
        count = len(state(home)['files'])
        one_line_install(environment, archives)
        check(recorded(home) == current.name, 'the same copy is installed')
        check(len(state(home)['files']) == count, 'a repair records nothing twice')
        check('firefox' in state(home).get('disabled', []), 'Firefox is still switched off after the repair')
        check(copies_in_use(home) == {current.name}, 'one copy in use')
        copies = sorted(path.name for path in releases(home).iterdir() if path.is_dir())
        check(len(copies) <= 2, f'at most the installed copy and the previous one are kept: {copies}')

        step(f'4. The old {args.version} installer is refused')
        run(old_root, environment, 'src/installer.py', '--yes', expect=3)
        check(recorded(home) == current.name, 'nothing changed after the refusal')

        step('5. A saved answer older than the installed copy is not trusted')
        saved = {'format': 2, 'checked': time.time() - 60, 'latest': args.version, 'tag': 'v' + args.version, 'url': 'u'}
        (data / 'update.json').write_text(json.dumps(saved), encoding='utf-8')
        if archives:
            print('Skipped: --archives given, GitHub is not asked.', flush=True)
        else:
            # What the installed copy's own update.py says (for the record: 0.25.1 and earlier reuse the saved answer).
            result = run(current, environment, 'src/update.py', '--check')
            print('installed copy:', result.stdout.strip().splitlines()[-1], flush=True)
            (data / 'update.json').write_text(json.dumps(saved), encoding='utf-8')
            # This source tree's update.py on the same data folder asks GitHub again.
            result = run(PROJECT, environment, 'src/update.py', '--check')
            info = json.loads(result.stdout.strip().splitlines()[-1])
            check(info['fresh'] is True or info['status'] == 'unknown',
                  f'GitHub asked again (fresh {info["fresh"]}, status {info["status"]}, error {info["error"]})')
            check(info['status'] != 'ahead', f'not called a development version: {info["status"]}, latest {info["latest"]}')
            check(info['installed'] == new_version, f'the installed copy is seen: {info["installed"]}')
    finally:
        if args.keep:
            print(f'Kept: {work}')
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    main()
