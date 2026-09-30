#!/usr/bin/env python3
"""Consent-based Linux installer for the open-source Corsu UI overlay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request

import corsu

ROOT = Path(__file__).resolve().parent


def discord_location():
    host = corsu.CONFIG / 'discord/Discord'
    if host.exists():
        candidate = host.resolve().parent
        if (candidate / 'resources/app.asar').exists():
            return candidate
    for candidate in map(Path, ['/opt/discord', '/usr/share/discord', '/usr/lib/discord']):
        if (candidate / 'resources/app.asar').exists():
            return candidate
    return None


def available_components():
    result = []
    if Path('/usr/lib/firefox/application.ini').exists():
        result.append('firefox')
    if shutil.which('plasmashell') and Path('/usr/share/locale/fr/LC_MESSAGES').exists():
        result.append('desktop')
    if discord_location():
        result.append('discord')
    if shutil.which('vesktop'):
        result.append('vesktop')
    if list(corsu.QT_TRANSLATIONS.glob('*_fr.qm')):
        result.append('qt')
    return result


def run(command, **kwargs):
    print('+ ' + ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), check=True, **kwargs)


def prepare_build():
    source = ROOT / 'Vencord'
    manifest = json.loads((ROOT / 'release.json').read_text())
    if not source.exists():
        run(['git', 'clone', 'https://github.com/Vendicated/Vencord.git', source])
        run(['git', 'checkout', '--detach', manifest['vencord_revision']], cwd=source)
    corsu.generate()
    if not (source / 'dist/patcher.js').exists():
        if not shutil.which('node') or not shutil.which('pnpm'):
            raise RuntimeError('Building requires Node.js >=22 and pnpm. Use the bundled Linux release to install without building.')
        run(['pnpm', 'install', '--frozen-lockfile'], cwd=source)
        run(['node', 'scripts/build/build.mjs', '--dev', '--disable-updater'], cwd=source,
            env={**os.environ, 'VENCORD_HASH': manifest['vencord_revision'][:7]})


def deploy_release():
    """Keep launchers/builds working even after the downloaded archive is removed."""
    if ROOT.is_relative_to(corsu.DATA / 'releases'):
        return ROOT
    fingerprint = hashlib.sha256()
    for name in ('corsu.py', 'engine.py', 'installer.py', 'lexicon.tsv', 'plugin/index.ts', 'plugin/translate.ts',
                 'release.json'):
        fingerprint.update((ROOT / name).read_bytes())
    for path in sorted((ROOT / 'Vencord/dist').glob('*.*')):
        fingerprint.update(path.read_bytes())
    target = corsu.DATA / 'releases' / fingerprint.hexdigest()[:16]
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='stage-', dir=target.parent))
    try:
        for name in ('corsu.py', 'engine.py', 'installer.py', 'lexicon.tsv', 'LICENSE', 'README.md',
                     'release.json', 'CONTRIBUTING.md', 'coverage.py', 'install.sh'):
            if (ROOT / name).exists():
                shutil.copy2(ROOT / name, stage / name)
        for name in ('plugin', 'vendor', 'Vencord'):
            if (ROOT / name).exists():
                shutil.copytree(ROOT / name, stage / name,
                                ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', 'Installer'))
        stage.rename(target)
        return target
    except BaseException:
        shutil.rmtree(stage)
        raise


def install_discord(location):
    binary = ROOT / 'vendor/VencordInstallerCli-linux'
    manifest = json.loads((ROOT / 'release.json').read_text())
    if platform.machine() not in ('x86_64', 'amd64'):
        raise RuntimeError('The bundled Discord installer supports Linux x86_64. Use Vesktop or build the official installer for your architecture.')
    if not binary.exists():
        print('Downloading the pinned official Vencord installer...', flush=True)
        with urllib.request.urlopen(manifest['installer_url'], timeout=60) as response:
            downloaded = response.read()
        if hashlib.sha256(downloaded).hexdigest() != manifest['installer_sha256']:
            raise RuntimeError('Downloaded installer checksum mismatch; nothing executed.')
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(downloaded)
        binary.chmod(0o755)
    if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest['installer_sha256']:
        raise RuntimeError('Official Vencord installer missing or checksum mismatch; extract a fresh release.')
    app = location / 'resources/app.asar'
    backup = location / 'resources/_app.asar'
    installer = corsu.Installer()
    record = installer.state['files'].get(str(app))
    if record and corsu.digest(app.read_bytes()) != record['installed_sha256']:
        raise RuntimeError(f'Discord changed since installation. Preserving it: {app}. Uninstall/review before reinstalling.')
    # The official installer keeps the unmodified archive in _app.asar.
    original = backup.read_bytes() if backup.exists() else app.read_bytes()
    command = [str(binary), '-install', '-location', str(location)]
    environment = {**os.environ, 'VENCORD_USER_DATA_DIR': str(ROOT / 'Vencord'), 'VENCORD_DEV_INSTALL': '1'}
    if not os.access(app.parent, os.W_OK):
        command = ['pkexec', 'env', f'VENCORD_USER_DATA_DIR={ROOT / "Vencord"}', 'VENCORD_DEV_INSTALL=1', *command]
    run(command, env=environment)
    if str(ROOT / 'Vencord/dist/patcher.js').encode() not in app.read_bytes():
        raise RuntimeError('The official installer did not inject the expected custom build.')
    installer.external_file(app, original)
    installer.state['files'][str(app)]['discord_location'] = str(location)
    corsu.STATE.write_text(json.dumps(installer.state, indent=2))
    installer.json_settings(corsu.CONFIG / 'Vencord/settings/settings.json', {
        'plugins/Corsu/enabled': True, 'autoUpdate': False, 'autoUpdateNotification': False})
    report_path = corsu.DATA / 'report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    report['discord_native'] = {'location': str(location), 'plugin': 'Corsu', 'partial': True}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', nargs='+', choices=['firefox', 'desktop', 'discord', 'vesktop', 'qt'],
                        help='Default: all supported integrations already installed on this computer.')
    parser.add_argument('--discord-path', type=Path, help='Native Discord directory containing resources/app.asar')
    parser.add_argument('--yes', action='store_true', help='Accept the displayed installation plan')
    parser.add_argument('--dry-run', action='store_true', help='Display the plan without downloading or changing anything')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--disable', action='store_true',
                        help='Return every application to its previous language, keeping the built catalogs')
    parser.add_argument('--enable', action='store_true', help='Switch Corsican back on after --disable')
    args = parser.parse_args(argv)
    if sys.platform != 'linux':
        parser.error('This release supports Linux. The desktop integration targets KDE Plasma.')
    if args.disable and args.enable:
        parser.error('Choose either --disable or --enable.')
    if args.disable or args.enable:
        action = 'Switch Corsican on' if args.enable else 'Switch Corsican off, keeping catalogs and builds'
        print(f'{action} for Firefox, Discord and Plasma.')
        if args.dry_run:
            return 0
        corsu.enable() if args.enable else corsu.disable()
        return 0
    if args.uninstall:
        print('Restore managed files/settings, preserving later user edits. Retain source and local builds.')
        if args.dry_run:
            return 0
        if not args.yes and input('Uninstall Corsu? [y/N] ').strip().lower() not in ('y', 'yes'):
            return 0
        corsu.uninstall()
        return 0
    available = available_components()
    components = args.components if args.components is not None else available
    location = args.discord_path.resolve() if args.discord_path else discord_location()
    if args.discord_path and 'discord' not in components and args.components is None:
        components = [*components, 'discord']
    if not components:
        parser.error('No supported applications detected. Install Firefox, native Discord/Vesktop or KDE Plasma first.')
    for component in components:
        if component not in available and not (component == 'discord' and location and (location / 'resources/app.asar').exists()):
            parser.error(f'{component} is not installed/supported here. Install it with your distribution package manager first.')
    print('Corsu — Corsican interface setup (Linux)\n')
    print('Selected: ' + ', '.join(components))
    if 'firefox' in components:
        print('• Build a local Firefox copy, translate its interface, and replace your user Firefox launcher. Keep the existing profile.')
    if 'desktop' in components:
        print('• Add user KDE translation catalogs and set interface language to co:fr. A new login is required.')
    if 'discord' in components:
        print(f'• Patch Discord at {location} with the official Vencord installer; enable Corsu. Administrator authentication may be requested.')
    if 'vesktop' in components:
        print('• Point Vesktop at the custom Vencord build and enable Corsu.')
    if 'qt' in components:
        print(f'• Build Corsican Qt catalogs and copy them into {corsu.QT_TRANSLATIONS}, so Qt dialog'
              ' buttons and file choosers are translated. Administrator authentication is requested.')
    if {'discord', 'vesktop'} & set(components):
        print('• Disable Vencord automatic updates to protect the custom plugin. Rebuild Corsu manually for updates.')
        print('• Use bundled Vencord when available; otherwise download/build the pinned source and dependencies. The official installer may check GitHub for updates.')
    print('• Save backups under ~/.local/share/corsu. Uninstall restores managed settings and preserves unrelated app settings.')
    print('Translation coverage is partial. Untranslated labels retain the original language. Messages, websites and typed text are preserved.\n')
    if args.dry_run:
        return 0
    if not args.yes and input('Accept these changes and install? [y/N] ').strip().lower() not in ('y', 'yes'):
        print('Cancelled; no changes made.')
        return 0
    target = deploy_release()
    if target != ROOT:
        command = [sys.executable, str(target / 'installer.py'), '--yes', '--components', *components]
        if 'discord' in components:
            command.extend(['--discord-path', str(location)])
        run(command)
        return 0
    if {'discord', 'vesktop'} & set(components):
        prepare_build()
    local = set(components) - {'discord', 'qt'}
    if 'qt' in components:
        local.add('desktop')
    if local:
        corsu.install(local, qt_system='qt' in components)
    if 'discord' in components:
        install_discord(location)
    if shutil.which('update-desktop-database'):
        run(['update-desktop-database', str(corsu.HOME / '.local/share/applications')])
    print('\nInstalled. Fully quit and reopen Firefox and Discord/Vesktop. Log out and back in for Plasma.\n'
          'Health: python3 corsu.py status\nSwitch off: python3 installer.py --disable\n'
          'Switch on: python3 installer.py --enable\nUninstall: python3 installer.py --uninstall')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f'Installation stopped: {error}\nManaged changes can be restored with: python3 installer.py --uninstall', file=sys.stderr)
        raise SystemExit(1)
