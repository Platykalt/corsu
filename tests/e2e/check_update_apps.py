#!/usr/bin/env python3
"""Updating from a published Corsu to the archives being checked, with the programs of src/apps (Linux).

Usage: check_update_apps.py --archives DIR [--from 0.23.0]

Needs VLC from the system's packages with its Corsican catalogue (Debian/Ubuntu: vlc, vlc-l10n); fre:ac from the
system's packages is used when present. Everything happens in a throwaway home folder:
 1. the published version is installed with VLC; VLC's menu entry starts it with Corsican first;
 2. the installed copy's own update.py installs the archives of DIR: the same parts are recorded (fre:ac, found on
    the computer, is not added), the installed copy carries Audacity, Tenacity, fre:ac and the VLC complement, and the
    complement is off: the menu entry has no VLC_DATA_PATH;
 3. --vlc-complement on: the menu entry points VLC to Corsu's folder; a repair and a later update keep it on;
 4. VLC switched off then on keeps the complement; --vlc-complement off goes back to VLC's own catalogue, Corsican
    still first, Corsu's VLC folder removed;
 5. fre:ac added and switched on (when installed), then uninstalling puts every recorded original back.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_update  # noqa: E402
from check_update import check, extract, fetch_published, releases, run, step  # noqa: E402
from e2e import isolated_environment, state  # noqa: E402
import update  # noqa: E402


def entry(home):
    path = home / '.local/share/applications/vlc.desktop'
    return path.read_text(encoding='utf-8') if path.exists() else ''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archives', type=Path, required=True)
    parser.add_argument('--from', dest='version', default='0.23.0')
    arguments = parser.parse_args()
    check(Path('/usr/share/locale/co/LC_MESSAGES/vlc.mo').exists(), "VLC's Corsican catalogue is installed")
    freac = shutil.which('freac') is not None
    work = Path(tempfile.mkdtemp(prefix='corsu-update-apps-'))
    home = work / 'home'
    (home / 'tmp').mkdir(parents=True)
    environment = {**isolated_environment(home), 'CORSU_LANG': 'en', 'TMPDIR': str(home / 'tmp')}
    for name in ('CORSU_LOCK_TOKEN', 'CORSU_DEPLOYED', 'CORSU_APP_ROOT', 'CORSU_DOWNLOAD_BASE', 'CORSU_SETUP_WINDOW',
                 'DBUS_SESSION_BUS_ADDRESS', 'DISPLAY', 'WAYLAND_DISPLAY', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME',
                 'XDG_RUNTIME_DIR'):
        environment.pop(name, None)
    old_root = extract(fetch_published(arguments.version, work / 'published'), work / 'old')
    new_root = extract(arguments.archives / check_update.ARCHIVE, work / 'new')
    new_version = update.installer.release_version(new_root)

    step(f'1. Corsu {arguments.version} installed with VLC')
    if freac:
        # fre:ac writes its settings at its first start; this is what it leaves.
        settings = home / '.config/freac/freac.xml'
        settings.parent.mkdir(parents=True)
        settings.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<ConfigFile>\n  <configuration name="default">\n'
                            '    <section name="Settings">\n      <value name="Language">freac_fr.xml</value>\n'
                            '      <value name="StartCount">1</value>\n    </section>\n  </configuration>\n</ConfigFile>\n',
                            encoding='utf-8')
        original_freac = settings.read_bytes()
    run(old_root, environment, 'src/installer.py', '--yes', '--components', 'vlc')
    old_copy = releases(home) / next(iter(path.name for path in releases(home).iterdir()))
    check('LANGUAGE=co' in entry(home) and 'VLC_DATA_PATH' not in entry(home), 'VLC starts with Corsican first')

    step(f'2. Update {arguments.version} → {new_version} by the installed copy\'s update.py')
    run(old_copy, {**environment, 'CORSU_DOWNLOAD_BASE': arguments.archives.as_uri()}, 'src/update.py', '--install')
    after = state(home)
    check(after.get('release', {}).get('version') == new_version, f'installation.json records {new_version}')
    check(after.get('components') == ['vlc'], f'the same parts are recorded, nothing added: {after.get("components")}')
    copy = Path(after['release']['folder'])
    for name in ('src/apps/audacity.py', 'src/apps/freac.py', 'src/apps/vlc_complement.py', 'contrib/vlc/co.po',
                 'contrib/vlc/review.json'):
        check((copy / name).is_file(), f'the installed copy has {name}')
    check('VLC_DATA_PATH' not in entry(home) and 'LANGUAGE=co' in entry(home),
          'the complement is off after the update; VLC still Corsican')
    preferences = home / '.local/share/corsu/preferences.json'
    check(not preferences.exists() or not json.loads(preferences.read_text()).get('vlc_complement'),
          'no complement preference was turned on')

    step('3. Complement on, then a repair')
    run(copy, environment, 'src/installer.py', '--yes', '--vlc-complement', 'on')
    check('VLC_DATA_PATH=' in entry(home), 'the menu entry gives VLC_DATA_PATH')
    tree = home / '.local/share/corsu/vlc/share/locale/co/LC_MESSAGES/vlc.mo'
    check(tree.is_file(), "the complement is in Corsu's folder")
    run(copy, environment, 'src/installer.py', '--yes')
    check('VLC_DATA_PATH=' in entry(home) and tree.is_file(), 'a repair keeps the complement on')
    # A later release: the same files saying 99.0.0, packed as the release archives are.
    later = work / 'later'
    bumped = check_update.bumped(new_root, '99.0.0', later / 'corsu')
    (later / 'dist').mkdir()
    with tarfile.open(later / 'dist' / check_update.ARCHIVE, 'w:gz') as archive:
        archive.add(bumped, arcname='corsu')
    (later / 'dist' / (check_update.ARCHIVE + '.sha256')).write_text(
        f'{check_update.sha256(later / "dist" / check_update.ARCHIVE)}  {check_update.ARCHIVE}\n', encoding='utf-8')
    run(copy, {**environment, 'CORSU_DOWNLOAD_BASE': (later / 'dist').as_uri()}, 'src/update.py', '--install',
        '--version', '99.0.0')
    check(state(home)['release']['version'] == '99.0.0', 'updated again, to 99.0.0')
    copy = Path(state(home)['release']['folder'])
    check('VLC_DATA_PATH=' in entry(home) and tree.is_file(), 'an update keeps the complement on')

    step('4. VLC off and on, then the complement off')
    run(copy, environment, 'src/installer.py', '--disable', 'vlc')
    check(entry(home) == '', 'VLC switched off: no menu entry of Corsu')
    run(copy, environment, 'src/installer.py', '--enable', 'vlc')
    check('VLC_DATA_PATH=' in entry(home), 'VLC switched on again with the complement')
    run(copy, environment, 'src/installer.py', '--yes', '--vlc-complement', 'off')
    check('VLC_DATA_PATH' not in entry(home) and 'LANGUAGE=co' in entry(home),
          "complement off: VLC's own catalogue, Corsican still first")
    check(not (home / '.local/share/corsu/vlc').exists(), "complement off: Corsu's VLC folder removed")

    step('5. fre:ac, then uninstall')
    if freac:
        run(copy, environment, 'src/installer.py', '--yes', '--components', 'vlc', 'freac')
        check('freac_co.xml' in settings.read_text(encoding='utf-8'), 'fre:ac set to Corsican')
    run(copy, environment, 'src/installer.py', '--uninstall', '--yes')
    check(entry(home) == '', 'uninstalled: no VLC menu entry left')
    if freac:
        check(settings.read_bytes() == original_freac, "uninstalled: fre:ac's settings are back as they were")
    print('PASS: update from', arguments.version, 'with the programs of src/apps')
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
