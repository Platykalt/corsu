#!/usr/bin/env python3
"""End-to-end installer checks in an isolated home directory. Never touches the real user's apps.

Usage: e2e.py firefox|discord|chromium [--root EXTRACTED_RELEASE]

firefox: install, launch the translated Firefox and read real strings, disable, enable, uninstall.
chromium: translate a throwaway browser copy (CORSU_CHROMIUM, e.g. Chrome for Testing), read the
          rendered error page and chrome://version, switch off/on, uninstall, and check the original pack is back.
discord: lay out a fake Discord for this platform, patch it with the real official Vencord installer,
         check the custom build is injected, then uninstall and check the original archive is back.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
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
        return [menu / 'Firefox Corsu.lnk', menu / 'Corsu Setup.lnk']
    if PLATFORM == 'macos':
        return [home / 'Applications/Firefox Corsu.app', home / 'Applications/Corsu Setup.app']
    return [home / '.local/bin/firefox-corsu', home / '.local/share/applications/corsu-setup.desktop']


def state(home):
    return json.loads((data_directory(home) / 'installation.json').read_text(encoding='utf-8'))


def check_firefox(root, home, environment):
    run(root, environment, 'src/installer.py', '--components', 'firefox', '--yes')
    for launcher in launchers(home):
        assert launcher.exists(), f'Missing launcher: {launcher}'
    report = json.loads((data_directory(home) / 'report.json').read_text(encoding='utf-8'))
    stats = report['firefox']
    print(json.dumps(stats, indent=2))
    assert stats['french_pack'], 'The French language pack was not applied'
    assert stats['french_messages'] > 5000, stats
    executable = run(root, environment, 'src/corsu.py', 'prepare-firefox', capture=True).splitlines()[0].strip()
    run(root, environment, str(HERE / 'check_firefox.py'), executable)
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


def check_discord(root, home, environment):
    location, archive, original = fake_discord(home)
    run(root, environment, 'src/installer.py', '--components', 'discord', '--discord-path', str(location), '--yes')
    patched = archive.read_bytes()
    assert patched != original and b'patcher.js' in patched, 'Discord archive was not patched'
    settings = home / {'windows': 'AppData/Roaming', 'macos': 'Library/Application Support'}.get(PLATFORM, '.config')
    plugin = json.loads((settings / 'Vencord/settings/settings.json').read_text(encoding='utf-8'))
    assert plugin['plugins']['Corsu']['enabled'] and plugin['autoUpdate'] is False, plugin
    assert launchers(home)[1].exists(), 'Missing Corsu Setup shortcut'
    run(root, environment, 'src/installer.py', '--uninstall', '--yes')
    assert archive.read_bytes() == original, 'Original Discord archive was not restored'
    assert not archive.with_name('_app.asar').exists(), 'Backup archive left next to Discord'
    assert not launchers(home)[1].exists(), 'Setup shortcut left behind'
    print('PASS: Discord patch with the official Vencord installer and restore')


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
    parser.add_argument('check', choices=['firefox', 'discord', 'chromium'])
    parser.add_argument('--root', type=Path, default=HERE.parent)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='corsu-home-', ignore_cleanup_errors=True) as directory:
        home = Path(directory)
        environment = isolated_environment(home)
        checks = {'firefox': check_firefox, 'discord': check_discord, 'chromium': check_chromium}
        checks[args.check](args.root.resolve(), home, environment)


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    main()
