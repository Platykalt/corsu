#!/usr/bin/env python3
"""Consent-based installer for the open-source Corsu UI overlay: Linux, Windows and macOS."""
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

ROOT = Path(__file__).resolve().parent.parent


def version_key(name):
    return [int(part) if part.isdigit() else part for part in name.replace('-', '.').split('.')]


def discord_archive(location):
    """The app.asar the official installer patches for a Discord location on this platform.

    The location is what `VencordInstallerCli -location` expects: the folder holding
    `resources/` on Linux, `%LOCALAPPDATA%\\Discord` on Windows and `Discord.app` on macOS.
    """
    location = Path(location)
    if corsu.PLATFORM == 'macos':
        return location / 'Contents/Resources/app.asar'
    if corsu.PLATFORM == 'windows':
        versions = sorted((path for path in location.glob('app-*') if (path / 'resources/app.asar').exists()),
                          key=lambda path: version_key(path.name[4:]))
        return versions[-1] / 'resources/app.asar' if versions else location / 'app-0/resources/app.asar'
    return location / 'resources/app.asar'


def discord_location():
    if corsu.PLATFORM == 'windows':
        candidates = [Path(os.environ.get('LOCALAPPDATA', corsu.HOME / 'AppData/Local')) / 'Discord']
    elif corsu.PLATFORM == 'macos':
        candidates = [Path('/Applications/Discord.app'), corsu.HOME / 'Applications/Discord.app']
    else:
        candidates = []
        host = corsu.CONFIG / 'discord/Discord'
        if host.exists():
            candidates.append(host.resolve().parent)
        candidates += map(Path, ['/opt/discord', '/usr/share/discord', '/usr/lib/discord'])
    return next((candidate for candidate in candidates if discord_archive(candidate).exists()), None)


def vesktop_installed():
    if shutil.which('vesktop') or (corsu.CONFIG / 'vesktop').is_dir():
        return True
    if corsu.PLATFORM == 'windows':
        return (Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/vesktop').is_dir()
    return corsu.PLATFORM == 'macos' and Path('/Applications/Vesktop.app').exists()


def available_components():
    result = []
    if corsu.firefox_install():
        result.append('firefox')
    if corsu.PLATFORM == 'linux' and shutil.which('plasmashell') and corsu.FRENCH_CATALOGS.exists():
        result.append('desktop')
    if discord_location():
        result.append('discord')
    if vesktop_installed():
        result.append('vesktop')
    if corsu.PLATFORM != 'macos':
        import chromium
        if chromium.browsers():
            result.append('chromium')
    if corsu.PLATFORM == 'linux' and list(corsu.QT_TRANSLATIONS.glob('*_fr.qm')):
        result.append('qt')
    return result


def run(command, **kwargs):
    command = list(map(str, command))
    print('+ ' + ' '.join(command), flush=True)
    # Windows only runs `.cmd` shims such as pnpm.cmd when given their full path.
    command[0] = shutil.which(command[0]) or command[0]
    subprocess.run(command, check=True, **kwargs)


def stale_build(source):
    """The dictionary is compiled into the bundle, so lexicon changes need a rebuild."""
    builds = list((source / 'dist').glob('*.js'))
    if not builds:
        return True
    built = min(path.stat().st_mtime for path in builds)
    return any((ROOT / name).stat().st_mtime > built
               for name in ('lexicon/lexicon.tsv', 'lexicon/lexicon-mozilla.tsv', 'lexicon/lexicon-upstream.tsv',
                            'discord-plugin/index.ts', 'discord-plugin/translate.ts'))


def prepare_build():
    source = ROOT / 'Vencord'
    manifest = json.loads((ROOT / 'release.json').read_text(encoding='utf-8'))
    if not source.exists():
        run(['git', 'clone', 'https://github.com/Vendicated/Vencord.git', source])
        run(['git', 'checkout', '--detach', manifest['vencord_revision']], cwd=source)
    corsu.generate()
    if not stale_build(source):
        return
    if not shutil.which('node'):
        if not (source / 'dist/patcher.js').exists():
            raise RuntimeError('Building requires Node.js >=22. Use a release archive to install without building.')
        print('Warning: the Vencord bundle is older than the lexicon; Discord keeps the previous labels.', flush=True)
        return
    if not (source / 'node_modules/esbuild').exists():
        if not shutil.which('pnpm'):
            raise RuntimeError('Installing Vencord dependencies requires pnpm. Use a release archive instead.')
        run(['pnpm', 'install', '--frozen-lockfile'], cwd=source)
    run(['node', 'scripts/build/build.mjs', '--dev', '--disable-updater'], cwd=source,
        env={**os.environ, 'VENCORD_HASH': manifest['vencord_revision'][:7]})


DEPLOYED_FILES = ('LICENSE', 'README.md', 'README.fr.md', 'CONTRIBUTING.md', 'release.json', 'install.sh', 'install.cmd')
DEPLOYED_DIRECTORIES = ('src', 'lexicon', 'discord-plugin', 'vendor', 'Vencord')


def deploy_release():
    """Keep launchers/builds working even after the downloaded archive is removed."""
    # Compare real paths: Windows short names (RUNNER~1) and macOS /var -> /private/var differ otherwise,
    # and the installer would re-run itself forever. The environment flag is a second guard.
    if ROOT.is_relative_to((corsu.DATA / 'releases').resolve()) or os.environ.get('CORSU_DEPLOYED') == str(ROOT):
        return ROOT
    fingerprint = hashlib.sha256()
    for path in sorted([*(ROOT / 'src').glob('*.py'), *(ROOT / 'discord-plugin').glob('*.ts'),
                        *(ROOT / name for name in DEPLOYED_FILES if (ROOT / name).is_file()),
                        *(ROOT / 'lexicon').glob('*.tsv'), *(ROOT / 'Vencord/dist').glob('*.*')]):
        fingerprint.update(path.relative_to(ROOT).as_posix().encode() + b'\0' + path.read_bytes())
    target = corsu.DATA / 'releases' / fingerprint.hexdigest()[:16]
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='stage-', dir=target.parent))
    try:
        for name in DEPLOYED_FILES:
            if (ROOT / name).is_file():
                shutil.copy2(ROOT / name, stage / name)
        for name in DEPLOYED_DIRECTORIES:
            if (ROOT / name).is_dir():
                shutil.copytree(ROOT / name, stage / name,
                                ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', 'Installer'))
        stage.rename(target)
        return target
    except BaseException:
        shutil.rmtree(stage)
        raise


def vencord_installer():
    """Return the checksum-verified official Vencord installer, downloading the pinned build if absent."""
    manifest = json.loads((ROOT / 'release.json').read_text(encoding='utf-8'))
    entry = manifest['installers'][corsu.PLATFORM]
    binary = ROOT / 'vendor' / entry['file']
    if corsu.PLATFORM == 'linux' and platform.machine().lower() not in ('x86_64', 'amd64'):
        raise RuntimeError('The official Discord installer supports Linux x86_64. Use Vesktop on this architecture.')
    if not binary.exists():
        print('Downloading the pinned official Vencord installer...', flush=True)
        with urllib.request.urlopen(manifest['installer_base_url'] + entry['file'], timeout=60) as response:
            downloaded = response.read()
        if hashlib.sha256(downloaded).hexdigest() != entry['sha256']:
            raise RuntimeError('Downloaded installer checksum mismatch; nothing executed.')
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(downloaded)
        binary.chmod(0o755)
    if hashlib.sha256(binary.read_bytes()).hexdigest() != entry['sha256']:
        raise RuntimeError('Official Vencord installer missing or checksum mismatch; extract a fresh release.')
    return binary


def install_discord(location):
    binary = vencord_installer()
    app = discord_archive(location)
    backup = app.with_name('_app.asar')
    installer = corsu.Installer()
    record = installer.state['files'].get(str(app))
    if record and corsu.digest(app.read_bytes()) != record['installed_sha256']:
        raise RuntimeError(f'Discord changed since installation. Preserving it: {app}. Uninstall/review before reinstalling.')
    # The official installer keeps the unmodified archive in _app.asar.
    original = backup.read_bytes() if backup.exists() else app.read_bytes()
    command = [str(binary), '-install', '-location', str(location)]
    environment = {**os.environ, 'VENCORD_USER_DATA_DIR': str(ROOT / 'Vencord'), 'VENCORD_DEV_INSTALL': '1'}
    if not os.access(app.parent, os.W_OK):
        if corsu.PLATFORM != 'linux':
            raise RuntimeError(f'Discord is read-only for this account: {location}. Rerun the installer as administrator.')
        command = ['pkexec', 'env', f'VENCORD_USER_DATA_DIR={ROOT / "Vencord"}', 'VENCORD_DEV_INSTALL=1', *command]
    run(command, env=environment)
    # The installer writes `require("<dir>/dist/patcher.js")` as a JSON string; Windows escapes backslashes.
    patched = app.read_bytes()
    if not any(form.encode() in patched for form in (str(ROOT / 'Vencord'), json.dumps(str(ROOT / 'Vencord'))[1:-1])):
        raise RuntimeError('The official installer did not inject the expected custom build.')
    installer.external_file(app, original)
    installer.state['files'][str(app)]['discord_location'] = str(location)
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    installer.json_settings(corsu.CONFIG / 'Vencord/settings/settings.json', {
        'plugins/Corsu/enabled': True, 'autoUpdate': False, 'autoUpdateNotification': False})
    report_path = corsu.DATA / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    report['discord_native'] = {'location': str(location), 'plugin': 'Corsu', 'partial': True}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


DESCRIPTIONS = {
    'firefox': 'Firefox: menus, settings and error pages',
    'desktop': 'KDE Plasma: desktop, KDE apps and application menu',
    'qt': 'Qt dialogs: standard buttons and file choosers (asks for administrator rights)',
    'discord': 'Discord: interface through Vencord',
    'vesktop': 'Vesktop: interface through Vencord',
    'chromium': 'Chrome, Opera GX and other Chromium browsers',
}


def choose(available):
    """Ask which detected applications to translate. Rerun the setup later to add more."""
    installed = set()
    if corsu.STATE.exists():
        installed = set(json.loads(corsu.STATE.read_text(encoding='utf-8')).get('components', []))
    selected = {name: True for name in available}
    while True:
        print('Select what you want to translate:')
        for number, name in enumerate(available, 1):
            mark = 'x' if selected[name] else ' '
            note = '  (installed)' if name in installed else ''
            print(f'  [{mark}] {number}. {DESCRIPTIONS[name]}{note}')
        answer = input('Type numbers to toggle (e.g. "2 3"), Enter to continue, q to quit: ').strip().lower()
        if answer in ('q', 'quit'):
            return []
        if not answer:
            return [name for name in available if selected[name]]
        for token in answer.replace(',', ' ').split():
            if token.isdigit() and 1 <= int(token) <= len(available):
                name = available[int(token) - 1]
                selected[name] = not selected[name]
        print()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', nargs='+', choices=['firefox', 'chromium', 'desktop', 'discord', 'vesktop', 'qt'],
                        help='Default: all supported integrations already installed on this computer.')
    parser.add_argument('--discord-path', type=Path,
                        help='Native Discord location: folder with resources/ (Linux), %%LOCALAPPDATA%%\\Discord (Windows) or Discord.app (macOS)')
    parser.add_argument('--yes', action='store_true', help='Accept the displayed installation plan')
    parser.add_argument('--dry-run', action='store_true', help='Display the plan without downloading or changing anything')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--disable', action='store_true',
                        help='Return every application to its previous language, keeping the built catalogs')
    parser.add_argument('--enable', action='store_true', help='Switch Corsican back on after --disable')
    args = parser.parse_args(argv)
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
    location = args.discord_path.resolve() if args.discord_path else discord_location()
    if args.discord_path and 'discord' not in available and discord_archive(location).exists():
        available = [*available, 'discord']
    components = args.components if args.components is not None else available
    if args.components is None and available and not (args.yes or args.dry_run) and sys.stdin.isatty():
        components = choose(available)
        if not components:
            print('Nothing selected; no changes made.')
            return 0
    if not components:
        parser.error('No supported applications detected. Install Firefox, native Discord/Vesktop or KDE Plasma first.')
    for component in components:
        if component not in available and not (component == 'discord' and location and discord_archive(location).exists()):
            if component in ('desktop', 'qt') and corsu.PLATFORM != 'linux':
                parser.error(f'{component} translates KDE Plasma and Qt on Linux; it is not available on {corsu.PLATFORM}.')
            parser.error(f'{component} is not installed/supported here. Install it first.')
    print(f'Corsu setup ({corsu.PLATFORM})\n')
    print('Selected: ' + ', '.join(components))
    if 'firefox' in components:
        launcher = {'windows': 'add a "Firefox Corsu" Start menu shortcut', 'macos': 'add "Firefox Corsu" to ~/Applications'}
        print('• Build a local Firefox copy, translate its interface, and '
              + launcher.get(corsu.PLATFORM, 'replace your user Firefox launcher') + '. Keep the existing profile.')
    if 'desktop' in components:
        print('• Add user KDE translation catalogs and set interface language to co:fr. A new login is required.')
    if 'discord' in components:
        print(f'• Patch Discord at {location} with the official Vencord installer; enable Corsu. Administrator authentication may be requested.')
    if 'vesktop' in components:
        print('• Point Vesktop at the custom Vencord build and enable Corsu.')
    if 'chromium' in components:
        import chromium
        names = ', '.join(browser.label for browser in chromium.browsers()) or 'none detected'
        print(f'• Translate the French interface pack of: {names}. Each browser then shows Corsican where'
              ' French would appear. System-wide browsers ask for administrator rights, again after browser updates.')
    if 'qt' in components:
        print(f'• Build Corsican Qt catalogs and copy them into {corsu.QT_TRANSLATIONS}, so Qt dialog'
              ' buttons and file choosers are translated. Administrator authentication is requested.')
    if {'discord', 'vesktop'} & set(components):
        print('• Disable Vencord automatic updates to protect the custom plugin. Rebuild Corsu manually for updates.')
        print('• Use bundled Vencord when available; otherwise download/build the pinned source and dependencies. The official installer may check GitHub for updates.')
    print(f'• Save backups under {corsu.DATA}. Uninstall restores managed settings and preserves unrelated app settings.')
    print('Translation coverage is partial. Untranslated labels retain the original language. Messages, websites and typed text are preserved.\n')
    if args.dry_run:
        return 0
    if not args.yes and input('Accept these changes and install? [y/N] ').strip().lower() not in ('y', 'yes'):
        print('Cancelled; no changes made.')
        return 0
    target = deploy_release()
    if target != ROOT:
        command = [sys.executable, str(target / 'src/installer.py'), '--yes', '--components', *components]
        if 'discord' in components:
            command.extend(['--discord-path', str(location)])
        run(command, env={**os.environ, 'CORSU_DEPLOYED': str(target.resolve())})
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
    corsu.setup_shortcut(corsu.Installer())
    applications = corsu.HOME / '.local/share/applications'
    if corsu.PLATFORM == 'linux' and shutil.which('update-desktop-database') and applications.is_dir():
        # Only refreshes the menu cache; menus still update on the next login when it fails.
        subprocess.run(['update-desktop-database', str(applications)], check=False)
    python = 'py -3' if corsu.PLATFORM == 'windows' else 'python3'
    print('\nInstalled. Fully quit and reopen Firefox and Discord/Vesktop.'
          + (' Log out and back in for Plasma.' if 'desktop' in components else '') + '\n'
          f'Health: {python} corsu.py status\nSwitch off: {python} installer.py --disable\n'
          f'Switch on: {python} installer.py --enable\nUninstall: {python} installer.py --uninstall')
    return 0


if __name__ == '__main__':
    # Windows consoles default to a legacy code page; never crash on Corsican letters.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print('\nNo answer received; nothing was changed.', file=sys.stderr)
        raise SystemExit(1)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f'Installation stopped: {error}\nManaged changes can be restored with: python3 installer.py --uninstall', file=sys.stderr)
        raise SystemExit(1)
