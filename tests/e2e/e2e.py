#!/usr/bin/env python3
"""End-to-end installer checks in an isolated home directory. Never touches the real user's apps.

Usage: e2e.py firefox|discord|chromium|archive [--root EXTRACTED_RELEASE]

archive: copy the extracted release to a folder with a space and an accent, install, delete that folder, check
         status, update from CORSU_ARCHIVES (file://, checksum checked) and uninstall with the installed copy.

firefox: install, launch the translated Firefox and read real strings, disable, enable, uninstall.
chromium: translate a throwaway browser copy (CORSU_CHROMIUM, e.g. Chrome for Testing), read the
          rendered error page and chrome://version, switch off/on, uninstall, and check the original pack is back.
discord: lay out a fake Discord for this platform, patch it with the real official Vencord installer,
         check the custom build is injected, then uninstall and check the original archive is back.
"""
import argparse
import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
PLATFORM = 'windows' if sys.platform == 'win32' else 'macos' if sys.platform == 'darwin' else 'linux'


def isolated_environment(home):
    environment = {**os.environ, 'HOME': str(home), 'USERPROFILE': str(home), 'PYTHONUTF8': '0',
                   'XDG_CONFIG_HOME': str(home / '.config'), 'APPDATA': str(home / 'AppData/Roaming'),
                   'LOCALAPPDATA': str(home / 'AppData/Local')}
    for name in ('XDG_CONFIG_HOME', 'APPDATA', 'LOCALAPPDATA'):
        Path(environment[name]).mkdir(parents=True, exist_ok=True)
    return environment


def run(root, environment, *arguments, capture=False):
    command = [sys.executable, *arguments]
    print('+ ' + ' '.join(map(str, command)), flush=True)
    result = subprocess.run(command, cwd=root, env=environment, text=True, encoding='utf-8',
                            stdout=subprocess.PIPE if capture else None, check=False)
    if result.returncode:
        raise SystemExit(f'Command failed ({result.returncode}): {arguments}')
    return result.stdout


def data_directory(home):
    return {'windows': home / 'AppData/Local/corsu', 'macos': home / 'Library/Application Support/corsu'}.get(
        PLATFORM, home / '.local/share/corsu')


def launchers(home):
    if PLATFORM == 'windows':
        menu = home / 'AppData/Roaming/Microsoft/Windows/Start Menu/Programs'
        return [menu / 'Firefox Corsu.lnk', menu / 'Corsu.lnk']
    if PLATFORM == 'macos':
        return [home / 'Applications/Firefox Corsu.app', home / 'Applications/Corsu.app']
    return [home / '.local/bin/firefox-corsu', home / '.local/share/applications/corsu-setup.desktop']


def launcher_icons(home):
    """The icon file each installed launcher shows, so a missing or deleted icon fails here, not on the desktop."""
    icons = {}
    for launcher in launchers(home):
        if launcher.suffix == '.desktop':
            match = re.search(r'^Icon=(.+)$', launcher.read_text(encoding='utf-8'), re.M)
            icons[launcher] = Path(match[1]) if match else None
        elif launcher.suffix == '.lnk':
            script = '(New-Object -ComObject WScript.Shell).CreateShortcut($env:CORSU_LINK).IconLocation'
            location = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script], text=True,
                                      capture_output=True, check=True, env={**os.environ, 'CORSU_LINK': str(launcher)})
            path = location.stdout.strip().rsplit(',', 1)[0]
            # Both shortcuts set an icon; an empty one would show python.exe's.
            icons[launcher] = Path(path) if path else None
        elif launcher.suffix == '.app':
            icons[launcher] = launcher / 'Contents/Resources/applet.icns'
    return icons


def state(home):
    return json.loads((data_directory(home) / 'installation.json').read_text(encoding='utf-8'))


def check_firefox(root, home, environment):
    run(root, environment, 'src/installer.py', '--components', 'firefox', '--yes')
    for launcher in launchers(home):
        assert launcher.exists(), f'Missing launcher: {launcher}'
    for launcher, icon in launcher_icons(home).items():
        assert icon and icon.is_file(), f'{launcher} shows a missing icon: {icon}'
        print(f'PASS: {launcher.name} icon {icon}')
        if launcher.name == 'Corsu.lnk':
            # Updates delete old release folders, so the icon must live outside them.
            assert 'releases' not in icon.parts, f'Corsu.lnk icon is inside a release folder: {icon}'
    applet = home / 'Applications/Firefox Corsu.app/Contents/Resources/applet.icns'
    if PLATFORM == 'macos':
        firefox_icon = Path(os.environ.get('CORSU_FIREFOX', '/Applications/Firefox.app')) / 'Contents/Resources/firefox.icns'
        assert applet.read_bytes() == firefox_icon.read_bytes(), 'Firefox Corsu.app does not show the Firefox logo'
    report = json.loads((data_directory(home) / 'report.json').read_text(encoding='utf-8'))
    stats = report['firefox']
    print(json.dumps(stats, indent=2))
    assert stats['french_pack'], 'The French language pack was not applied'
    assert stats['french_messages'] > 5000, stats
    executable = run(root, environment, 'src/corsu.py', 'prepare-firefox', capture=True).splitlines()[0].strip()
    run(root, environment, str(HERE / 'check_firefox.py'), executable)
    if PLATFORM == 'linux':
        run(root, {**environment, 'XDG_DATA_HOME': str(home / '.local/share')}, str(HERE / 'check_firefox_default.py'),
            str(launchers(home)[0]))
    status = json.loads(run(root, environment, 'src/corsu.py', 'status', capture=True))
    assert status['enabled'] and status['installation']['missing'] == [] and status['installation']['changed'] == [], status
    run(root, environment, 'src/installer.py', '--disable')
    assert not state(home)['enabled']
    run(root, environment, 'src/installer.py', '--enable')
    assert state(home)['enabled']
    run(root, environment, 'src/installer.py', '--uninstall', '--yes')
    assert state(home)['files'] == {}, state(home)
    for launcher in launchers(home):
        assert not launcher.exists(), f'Launcher left behind: {launcher}'
    print('PASS: Firefox install, launch, disable, enable and uninstall')


def fake_discord(home):
    original = b'original Discord archive ' + os.urandom(16)
    if PLATFORM == 'windows':
        location = home / 'AppData/Local/Discord'
        archive = location / 'app-1.0.9999/resources/app.asar'
    elif PLATFORM == 'macos':
        location = home / 'Applications/Discord.app'
        archive = location / 'Contents/Resources/app.asar'
    else:
        location = home / 'discord'
        archive = location / 'resources/app.asar'
    archive.parent.mkdir(parents=True)
    archive.write_bytes(original)
    return location, archive, original


def check_bundled_python(root, home, environment):
    """Run from a release archive's own Python: it is copied to Corsu's data folder, the shortcuts use that copy,
    and it carries what Corsu's window needs."""
    if not Path(sys.executable).resolve().is_relative_to((Path(root) / 'runtime').resolve()):
        return
    copies = list((data_directory(home) / 'runtime').glob('*/python'))
    assert copies, 'The bundled Python was not copied to the data folder'
    shortcut = launchers(home)[1]
    if PLATFORM == 'linux':
        assert str(copies[0]) in shortcut.read_text(encoding='utf-8'), 'The Corsu shortcut does not use the copied Python'
    elif PLATFORM == 'windows':
        # The shortcut keeps the long form of the path (runneradmin, not RUNNER~1), in UTF-16 or the ANSI code page.
        data = shortcut.read_bytes().lower()
        forms = {str(copies[0]).lower(), str(copies[0].resolve()).lower()}
        assert any(form.encode(encoding) in data for form in forms for encoding in ('utf-16-le', 'mbcs')), \
            'The Corsu shortcut does not use the copied Python'
    if PLATFORM != 'linux':
        python = copies[0] / ('python.exe' if PLATFORM == 'windows' else 'bin/python3')
        binding = 'import clr' if PLATFORM == 'windows' else 'import AppKit, WebKit'
        subprocess.run([str(python), '-c', f'import webview; {binding}'], check=True)
    print('PASS: bundled Python copied, used by the shortcuts and able to open the window')


def check_discord(root, home, environment):
    location, archive, original = fake_discord(home)
    run(root, environment, 'src/installer.py', '--components', 'discord', '--discord-path', str(location), '--yes')
    patched = archive.read_bytes()
    assert patched != original and b'patcher.js' in patched, 'Discord archive was not patched'
    settings = home / {'windows': 'AppData/Roaming', 'macos': 'Library/Application Support'}.get(PLATFORM, '.config')
    plugin = json.loads((settings / 'Vencord/settings/settings.json').read_text(encoding='utf-8'))
    assert plugin['plugins']['Corsu']['enabled'] and plugin['autoUpdate'] is False, plugin
    assert launchers(home)[1].exists(), 'Missing Corsu shortcut'
    check_bundled_python(root, home, environment)
    run(root, environment, 'src/installer.py', '--uninstall', '--yes')
    assert archive.read_bytes() == original, 'Original Discord archive was not restored'
    assert not archive.with_name('_app.asar').exists(), 'Backup archive left next to Discord'
    assert not launchers(home)[1].exists(), 'Setup shortcut left behind'
    print('PASS: Discord patch with the official Vencord installer and restore')


def installed_copy(home):
    copies = sorted((data_directory(home) / 'releases').glob('*/src/corsu.py'), key=lambda path: path.stat().st_mtime)
    assert copies, 'No installed copy of Corsu in the data folder'
    return copies[-1].parent.parent


def mentions(path, text):
    """Whether a launcher (file, or every file of an application bundle) holds this path, in any encoding."""
    files = [path] if path.is_file() else [file for file in path.rglob('*') if file.is_file()]
    forms = {text, text.replace('\\', '/')}
    encodings = ('utf-8', 'utf-16-le', 'utf-16-be') + (('mbcs',) if PLATFORM == 'windows' else ())
    return any(form.encode(encoding, errors='ignore') in file.read_bytes()
               for file in files for form in forms for encoding in encodings)


REQUIRED = ['src/app/index.html', 'src/app/corsu.svg', 'src/app/corsu.ico', 'src/release.json', 'src/installer.py',
            'src/update.py', 'lexicon/lexicon.tsv', 'vendor/firefox-fr.xpi', 'Vencord/dist/vencordDesktopRenderer.js']


def fake_prism_instance(home, version):
    """A Prism Launcher instance of the supported version, as a person who just created it has (no pack, English)."""
    base = {'windows': home / 'AppData/Roaming', 'macos': home / 'Library/Application Support'}.get(PLATFORM, home / '.local/share')
    instance = base / 'PrismLauncher/instances' / version
    (instance / 'minecraft/resourcepacks').mkdir(parents=True)
    (instance / 'mmc-pack.json').write_text(json.dumps({'components': [{'uid': 'net.minecraft', 'version': version}],
                                                        'formatVersion': 1}), encoding='utf-8')
    (instance / 'minecraft/options.txt').write_text('version:4671\nlang:en_us\nresourcePacks:[]\n', encoding='utf-8')
    return instance / 'minecraft'


def check_archive(root, home, environment):
    """The route of a person who downloads an archive: extract it to a folder with a space and an accent, install from
    there, delete that folder, then use, update (from the same archives, checksum checked) and remove Corsu with only
    what was installed."""
    archives = Path(os.environ['CORSU_ARCHIVES']).resolve()
    extracted = home / 'Téléchargements corsu' / 'corsu'
    shutil.copytree(root, extracted, symlinks=True)
    missing = [name for name in REQUIRED if not (extracted / name).is_file()]
    assert not missing, f'Archive lacks: {missing}'
    instance = fake_prism_instance(home, (extracted / 'minecraft/java/VERSION').read_text(encoding='utf-8').strip())
    # An old release: its pack is built by the installed copy from the shared data, in the .lang format.
    legacy = fake_prism_instance(home, '1.12.2')
    run(extracted, environment, 'src/installer.py', '--components', 'firefox', 'minecraft', '--yes')
    shutil.rmtree(extracted.parent)
    options = (instance / 'options.txt').read_text(encoding='utf-8')
    assert 'lang:co_fr' in options and (instance / 'resourcepacks/corsu-minecraft-java.zip').is_file(), options
    import zipfile
    with zipfile.ZipFile(legacy / 'resourcepacks/corsu-minecraft-java.zip') as pack:
        assert 'assets/minecraft/lang/co_fr.lang' in pack.namelist(), pack.namelist()
        assert '"pack_format": 3' in pack.read('pack.mcmeta').decode(), pack.read('pack.mcmeta')
    assert 'lang:co_fr' in (legacy / 'options.txt').read_text(encoding='utf-8')
    copy = installed_copy(home)
    missing = [name for name in REQUIRED if not (copy / name).is_file() and not name.startswith('vendor/')]
    assert not missing, f'Installed copy lacks: {missing}'
    for launcher in launchers(home):
        assert launcher.exists(), f'Missing launcher: {launcher}'
        assert not mentions(launcher, str(extracted.parent)), f'{launcher} still points into the extracted folder'
    for launcher, icon in launcher_icons(home).items():
        assert icon and icon.is_file(), f'{launcher} shows a missing icon: {icon}'
    status = json.loads(run(copy, environment, 'src/corsu.py', 'status', capture=True))
    assert status['installation']['missing'] == [] and status['installation']['changed'] == [], status
    run(copy, environment, 'src/corsu.py', 'prepare-firefox', capture=True)
    update = {**environment, 'CORSU_DOWNLOAD_BASE': archives.as_uri()}
    run(copy, update, 'src/update.py', '--install')
    copy = installed_copy(home)
    for launcher, icon in launcher_icons(home).items():
        assert icon and icon.is_file(), f'After the update, {launcher} shows a missing icon: {icon}'
    status = json.loads(run(copy, environment, 'src/corsu.py', 'status', capture=True))
    assert status['installation']['missing'] == [], status
    run(copy, environment, 'src/installer.py', '--uninstall', '--yes')
    assert state(home)['files'] == {}, state(home)
    assert 'lang:en_us' in (instance / 'options.txt').read_text(encoding='utf-8'), 'Minecraft language not given back'
    assert not list((instance / 'resourcepacks').glob('corsu*.zip')), 'Corsu pack left in the instance'
    assert not list((legacy / 'resourcepacks').glob('corsu*.zip')), 'Corsu pack left in the 1.12.2 instance'
    for launcher in launchers(home):
        assert not launcher.exists(), f'Launcher left behind: {launcher}'
    print(f'PASS: installed from an extracted archive, used after deleting it, updated from {archives.as_uri()}, removed')


def check_chromium(root, home, environment):
    import hashlib
    browser = Path(os.environ['CORSU_CHROMIUM'])
    executable = next(browser / name for name in ('chrome.exe', 'chrome') if (browser / name).exists())
    pack = next(path for path in browser.rglob('fr.pak') if path.parent.name in ('locales', 'Locales'))
    original = hashlib.sha256(pack.read_bytes()).hexdigest()
    run(root, environment, 'src/installer.py', '--components', 'chromium', '--yes')
    assert hashlib.sha256(pack.read_bytes()).hexdigest() != original, 'French pack was not translated'
    run(root, environment, str(HERE / 'check_chromium.py'), str(executable))
    run(root, environment, 'src/installer.py', '--disable')
    assert hashlib.sha256(pack.read_bytes()).hexdigest() == original, 'Disable did not restore the French pack'
    run(root, environment, 'src/installer.py', '--enable')
    assert hashlib.sha256(pack.read_bytes()).hexdigest() != original, 'Enable did not translate again'
    run(root, environment, 'src/installer.py', '--uninstall', '--yes')
    assert hashlib.sha256(pack.read_bytes()).hexdigest() == original, 'Uninstall did not restore the French pack'
    assert state(home)['files'] == {}, state(home)
    print('PASS: Chromium pack translated, rendered in Corsican, switched off/on and restored')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check', choices=['firefox', 'discord', 'chromium', 'archive'])
    parser.add_argument('--root', type=Path, default=PROJECT)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='corsu-home-', ignore_cleanup_errors=True) as directory:
        home = Path(directory)
        environment = isolated_environment(home)
        checks = {'firefox': check_firefox, 'discord': check_discord, 'chromium': check_chromium,
                  'archive': check_archive}
        checks[args.check](args.root.resolve(), home, environment)


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    main()
