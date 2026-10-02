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
from corsu import french, t  # noqa: F401  (app.py and tests use them from here)

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
        for branch in ('discord', 'discordptb', 'discordcanary'):
            # Recent Discord packages keep the program in ~/.config/discord/app-<version>; the
            # `Discord` link there can still point at the previous version, so take the newest.
            versions = sorted((path for path in (corsu.CONFIG / branch).glob('app-*') if (path / 'resources/app.asar').exists()),
                              key=lambda path: version_key(path.name[4:]))
            candidates += versions[-1:]
        candidates += map(Path, ['/opt/discord', '/usr/share/discord', '/usr/lib/discord'])
    return next((candidate for candidate in candidates if discord_archive(candidate).exists()), None)


def sibling_versions(location):
    """The other app-<version> folders next to a Linux Discord. The launcher may still start an older one
    until Discord restarts on the newest, so every version present gets the plugin."""
    location = Path(location)
    if corsu.PLATFORM != 'linux' or not location.name.startswith('app-'):
        return []
    return sorted(path for path in location.parent.glob('app-*')
                  if path != location and (path / 'resources/app.asar').exists())


def vesktop_installed():
    if shutil.which('vesktop') or (corsu.CONFIG / 'vesktop').is_dir() or (corsu.DATA / 'vesktop').is_dir():
        return True
    if corsu.PLATFORM == 'windows':
        return (Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/vesktop').is_dir()
    return corsu.PLATFORM == 'macos' and Path('/Applications/Vesktop.app').exists()


def available_components():
    # Firefox is offered even when missing: Corsu then downloads Mozilla's French Firefox first.
    result = ['firefox']
    if corsu.PLATFORM == 'linux' and shutil.which('plasmashell') and corsu.FRENCH_CATALOGS.exists():
        result.append('desktop')
    if discord_location():
        result.append('discord')
    # Without Discord or Vesktop, Corsu offers to download Vesktop, a Discord app that already includes Vencord.
    if vesktop_installed() or not discord_location():
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
               for name in ('lexicon/lexicon.tsv', 'lexicon/lexicon-fixes.tsv', 'lexicon/lexicon-mozilla.tsv', 'lexicon/lexicon-upstream.tsv',
                            'src/discord-plugin/index.ts', 'src/discord-plugin/translate.ts'))


def prepare_build():
    source = ROOT / 'Vencord'
    manifest = json.loads((ROOT / 'src/release.json').read_text(encoding='utf-8'))
    if not source.exists():
        run(['git', 'clone', 'https://github.com/Vendicated/Vencord.git', source])
        run(['git', 'checkout', '--detach', manifest['vencord_revision']], cwd=source)
    corsu.generate()
    if not stale_build(source):
        return
    if not shutil.which('node'):
        if not (source / 'dist/patcher.js').exists():
            raise RuntimeError('Building requires Node.js >=22. Use a release archive to install without building.')
        print('Note: the Discord plugin was built before the latest translations; Discord keeps the older ones.', flush=True)
        return
    if not (source / 'node_modules/esbuild').exists():
        if not shutil.which('pnpm'):
            if (source / 'dist/patcher.js').exists():
                # An installed copy has the built plugin but not the build tools: use what is there.
                print(t('Note: the Discord plugin was built before the latest translations; Discord keeps the older ones.',
                        'Note : le plugin Discord a été construit avant les dernières traductions ; Discord garde les anciennes.'), flush=True)
                return
            raise RuntimeError('Installing Vencord dependencies requires pnpm. Use a release archive instead.')
        run(['pnpm', 'install', '--frozen-lockfile'], cwd=source)
    run(['node', 'scripts/build/build.mjs', '--dev', '--disable-updater'], cwd=source,
        env={**os.environ, 'VENCORD_HASH': manifest['vencord_revision'][:7]})


DEPLOYED_FILES = ('LICENSE', 'README.md', 'CONTRIBUTING.md')
DEPLOYED_DIRECTORIES = ('src', 'lexicon', 'install', 'vendor', 'Vencord')


def deploy_release():
    """Keep launchers/builds working even after the downloaded archive is removed."""
    # Compare real paths: Windows short names (RUNNER~1) and macOS /var -> /private/var differ otherwise,
    # and the installer would re-run itself forever. The environment flag is a second guard.
    if ROOT.is_relative_to((corsu.DATA / 'releases').resolve()) or os.environ.get('CORSU_DEPLOYED') == str(ROOT):
        return ROOT
    fingerprint = hashlib.sha256()
    for path in sorted([*(path for path in (ROOT / 'src').rglob('*') if path.is_file() and '__pycache__' not in path.parts),
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


def releases_in_use():
    """Release folders something still loads: Discord's patched app.asar and Vesktop point into one."""
    used = set()
    releases = str(corsu.DATA / 'releases')
    state = corsu.load_state()
    places = [Path(name) for name in state.get('files', {}) if name.endswith('app.asar')]
    places.append(corsu.CONFIG / 'vesktop/state.json')
    for place in places:
        try:
            text = place.read_bytes().decode('utf-8', 'replace').replace('\\\\', '/').replace('\\', '/')
        except OSError:
            continue
        start = text.find(releases.replace('\\', '/'))
        while start != -1:
            name = text[start + len(releases) + 1:].split('/', 1)[0]
            used.add(name)
            start = text.find(releases.replace('\\', '/'), start + 1)
    return used


def prune_releases(current):
    """Delete the copies of earlier Corsu versions, keeping the current one and any still in use."""
    folder = corsu.DATA / 'releases'
    if not folder.is_dir():
        return
    keep = releases_in_use() | {Path(current).name}
    for release in folder.iterdir():
        if release.is_dir() and release.name not in keep:
            shutil.rmtree(release, ignore_errors=True)


def vencord_installer():
    """Return the checksum-verified official Vencord installer, downloading the pinned build if absent."""
    manifest = json.loads((ROOT / 'src/release.json').read_text(encoding='utf-8'))
    entry = manifest['installers'][corsu.PLATFORM]
    binary = ROOT / 'vendor' / entry['file']
    if corsu.PLATFORM == 'linux' and platform.machine().lower() not in ('x86_64', 'amd64'):
        raise RuntimeError('The official Discord installer supports Linux x86_64. Use Vesktop on this architecture.')
    if not binary.exists():
        print('Downloading the official Vencord installer...', flush=True)
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


def forget_removed_discord():
    """Discord deletes old app-<version> folders when it updates. Drop Corsu's records of files that went with them,
    so installing, switching and uninstalling do not fail on a file that no longer exists."""
    if not corsu.STATE.exists():
        return
    state = corsu.load_state()
    gone = [name for name, record in state['files'].items()
            if record.get('discord_location') and not Path(record['discord_location']).exists()]
    for name in gone:
        state['files'].pop(name)
        print(t(f'Forgetting {name}: Discord removed that version.', f'Oubli de {name} : Discord a supprimé cette version.'))
    if gone:
        corsu.STATE.write_text(json.dumps(state, indent=2), encoding='utf-8')


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
    installer.state['components'] = sorted(set(installer.state.get('components', [])) | {'discord'})
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    installer.json_settings(corsu.CONFIG / 'Vencord/settings/settings.json', {
        'plugins/Corsu/enabled': True, 'autoUpdate': False, 'autoUpdateNotification': False})
    report_path = corsu.DATA / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    report['discord_native'] = {'location': str(location), 'plugin': 'Corsu', 'partial': True}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


DESCRIPTIONS = {
    'firefox': ('Firefox: menus, settings and error pages', 'Firefox : menus, réglages et pages d\'erreur'),
    'desktop': ('KDE Plasma: desktop, KDE apps and application menu', 'KDE Plasma : bureau, applications KDE et menu'),
    'qt': ('System translations: GTK programs, terminal commands and Qt dialogs (asks for your password)',
           'Traductions système : programmes GTK, commandes du terminal et boîtes de dialogue Qt (demande votre mot de passe)'),
    'discord': ('Discord: interface through Vencord', 'Discord : interface, grâce à Vencord'),
    'vesktop': ('Vesktop: interface through Vencord', 'Vesktop : interface, grâce à Vencord'),
    'chromium': ('Chrome, Opera GX and other Chromium browsers', 'Chrome, Opera GX et autres navigateurs Chromium'),
}


def choose(available):
    """Ask which detected applications to translate. Rerun the setup later to add more."""
    installed = set()
    if corsu.STATE.exists():
        installed = set(json.loads(corsu.STATE.read_text(encoding='utf-8')).get('components', []))
    selected = {name: True for name in available}
    while True:
        print(t('Select what you want to translate:', 'Choisissez ce que vous voulez traduire :'))
        for number, name in enumerate(available, 1):
            mark = 'x' if selected[name] else ' '
            note = t('  (installed)', '  (déjà installé)') if name in installed else ''
            print(f'  [{mark}] {number}. {t(*DESCRIPTIONS[name])}{note}')
        answer = input(t('Enter installs everything ticked. Type a number to tick or untick it, a for all, n for none, q to quit: ',
                         'Entrée installe tout ce qui est coché. Tapez un numéro pour le cocher ou le décocher, '
                         'a pour tout, n pour rien, q pour quitter : ')).strip().lower()
        if answer in ('q', 'quit'):
            return []
        if not answer:
            return [name for name in available if selected[name]]
        if answer in ('a', 'all', 'tout', 't'):
            selected = {name: True for name in available}
        elif answer in ('n', 'none', 'rien', 'r'):
            selected = {name: False for name in available}
        for token in answer.replace(',', ' ').split():
            if token.isdigit() and 1 <= int(token) <= len(available):
                name = available[int(token) - 1]
                selected[name] = not selected[name]
        print()


def show_plan(components, location):
    print(t('Corsu will make these changes:\n', 'Corsu va faire ces changements :\n'))
    if 'firefox' in components and not corsu.firefox_install():
        print(t('  Firefox: not found, so download Mozilla\'s French Firefox (about 90 MB) from archive.mozilla.org and check'
                ' it against Mozilla\'s published checksum first.',
                '  Firefox : introuvable, donc télécharger d\'abord le Firefox français de Mozilla (environ 90 Mo) depuis'
                ' archive.mozilla.org et le vérifier avec la somme publiée par Mozilla.'))
    if 'firefox' in components:
        where = {'windows': t('a "Firefox Corsu" shortcut in the Start menu', 'un raccourci "Firefox Corsu" du menu Démarrer'),
                 'macos': t('a "Firefox Corsu" app in ~/Applications', 'une application "Firefox Corsu" dans ~/Applications')
                 }.get(corsu.PLATFORM, t('your Firefox menu entry', 'votre entrée Firefox habituelle du menu'))
        print(t(f'  Firefox: make a translated copy of Firefox, opened from {where}. It uses your usual profile.',
                f'  Firefox : faire une copie traduite de Firefox, ouverte depuis {where}. Elle utilise votre profil habituel.'))
    if 'chromium' in components:
        import chromium
        names = ', '.join(browser.label for browser in chromium.browsers()) or 'none found'
        print(t(f'  {names}: replace the French language file with a Corsican one.'
                ' Browsers installed for all users will ask for administrator rights, now and after each update.',
                f'  {names} : remplacer le fichier de langue française par un fichier corse.'
                ' Les navigateurs installés pour tous les utilisateurs demanderont les droits administrateur, maintenant et après chaque mise à jour.'))
    if 'discord' in components:
        print(t(f'  Discord: patch {location} with the official Vencord installer and turn on the Corsu plugin.'
                ' Vencord updates are turned off so they do not remove it. Set Discord to French or English.',
                f'  Discord : modifier {location} avec l\'installeur officiel de Vencord et activer le plugin Corsu.'
                ' Les mises à jour de Vencord sont coupées pour ne pas l\'effacer. Réglez Discord en français ou en anglais.'))
    if 'vesktop' in components and not vesktop_installed():
        print(t('  Vesktop: download Vesktop (about 130 MB) from its GitHub page, check its published checksum, install it'
                ' and set it up with the Corsu plugin. Vesktop is a Discord app that includes Vencord.',
                '  Vesktop : télécharger Vesktop (environ 130 Mo) depuis sa page GitHub, vérifier sa somme de contrôle,'
                ' l\'installer et le régler avec le plugin Corsu. Vesktop est une application Discord qui contient Vencord.'))
    elif 'vesktop' in components:
        print(t('  Vesktop: use the Vencord build that includes the Corsu plugin.',
                '  Vesktop : utiliser la version de Vencord qui contient le plugin Corsu.'))
    if 'desktop' in components:
        print(t('  KDE Plasma: add Corsican translation files to your home folder and set the language to Corsican,'
                ' with French for anything not yet translated. Log out and back in afterwards.',
                '  KDE Plasma : ajouter les fichiers de traduction corse dans votre dossier personnel et passer la langue en corse,'
                ' avec le français pour ce qui n\'est pas encore traduit. Déconnectez-vous et reconnectez-vous ensuite.'))
    if 'qt' in components:
        print(t(f'  System translations: copy the Corsican files into {corsu.SYSTEM_LOCALE.parent.parent} and'
                f' {corsu.QT_TRANSLATIONS}, so GTK programs, terminal commands and Qt dialogs use them too.'
                ' This asks for your password once.',
                f'  Traductions du système : copier les fichiers corses dans {corsu.SYSTEM_LOCALE.parent.parent} et'
                f' {corsu.QT_TRANSLATIONS}, pour que les programmes GTK, les commandes du terminal et les fenêtres Qt'
                ' les utilisent aussi. Votre mot de passe est demandé une fois.'))
    print(t(f'\nA copy of every file Corsu changes is kept in {corsu.DATA}, and the Corsu app can undo everything.',
            f'\nUne copie de chaque fichier modifié est gardée dans {corsu.DATA}, et l\'application Corsu peut tout annuler.'))
    print(t('Text without a Corsican translation yet stays in French. Messages are never changed.\n',
            'Le texte sans traduction corse reste en français. Les messages ne sont jamais modifiés.\n'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', nargs='+', choices=['firefox', 'chromium', 'desktop', 'discord', 'vesktop', 'qt'],
                        help='Default: all supported integrations already installed on this computer.')
    parser.add_argument('--discord-path', type=Path,
                        help='Native Discord location: folder with resources/ (Linux), %%LOCALAPPDATA%%\\Discord (Windows) or Discord.app (macOS)')
    parser.add_argument('--yes', action='store_true', help='Accept the displayed installation plan')
    parser.add_argument('--dry-run', action='store_true', help='Display the plan without downloading or changing anything')
    parser.add_argument('--uninstall', action='store_true')
    # The Windows launcher cannot drop its own --text option before passing the rest on.
    parser.add_argument('--text', action='store_true', help=argparse.SUPPRESS)
    parts = ['firefox', 'chromium', 'discord', 'vesktop', 'desktop', 'terminal']
    parser.add_argument('--disable', nargs='*', choices=parts, metavar='PART',
                        help='Go back to the previous language, for everything or for the parts listed: ' + ', '.join(parts))
    parser.add_argument('--enable', nargs='*', choices=parts, metavar='PART', help='Switch Corsican back on, for everything or the parts listed')
    parser.add_argument('--hours', type=float, help='With --disable terminal: switch the terminal back on after this many hours')
    args = parser.parse_args(argv)
    if args.disable is not None and args.enable is not None:
        parser.error('Choose either --disable or --enable.')
    if args.disable is not None or args.enable is not None:
        if args.dry_run:
            return 0
        if args.enable is not None:
            corsu.enable(args.enable or None)
        else:
            corsu.disable(args.disable or None, hours=args.hours)
        return 0
    if args.uninstall:
        print(t('This puts back the original files and settings. Files you changed yourself since are left alone.',
                'Les fichiers et réglages d\'origine vont être remis. Ceux que vous avez modifiés vous-même depuis ne sont pas touchés.'))
        if args.dry_run:
            return 0
        if not args.yes and input(t('Uninstall Corsu? [y/N] ', 'Désinstaller Corsu ? [o/N] ')).strip().lower() not in ('y', 'yes', 'o', 'oui'):
            return 0
        corsu.uninstall()
        return 0
    available = available_components()
    location = args.discord_path.resolve() if args.discord_path else discord_location()
    if args.discord_path and not discord_archive(location).exists():
        # A path remembered from before a Discord update; Discord has removed that version since.
        print(t(f'Note: {location} no longer exists; using the Discord found on this computer.',
                f'Note : {location} n\'existe plus ; utilisation du Discord trouvé sur cet ordinateur.'))
        location = discord_location()
    forget_removed_discord()
    if args.discord_path and 'discord' not in available and discord_archive(location).exists():
        available = [*available, 'discord']
    components = args.components if args.components is not None else available
    if args.components is None and available and not (args.yes or args.dry_run) and sys.stdin.isatty():
        components = choose(available)
        if not components:
            print(t('Nothing selected, nothing was changed.', 'Rien de sélectionné, rien n\'a été modifié.'))
            return 0
    if not components:
        parser.error(t('Corsu found nothing to translate here. Install Firefox, a Chromium browser, Discord or KDE Plasma first.',
                       'Corsu n\'a rien trouvé à traduire ici. Installez d\'abord Firefox, un navigateur Chromium, Discord ou KDE Plasma.'))
    for component in components:
        if component not in available and not (component == 'discord' and location and discord_archive(location).exists()):
            if component in ('desktop', 'qt') and corsu.PLATFORM != 'linux':
                parser.error(f'{component} is for KDE Plasma on Linux.')
            parser.error(f'{component} was not found on this computer.')
    # The Corsu app shows the plan before starting; its log only needs what happens next.
    if not os.environ.get('CORSU_SETUP_WINDOW'):
        show_plan(components, location)
    if args.dry_run:
        return 0
    if not args.yes and input(t('Go ahead? [y/N] ', 'On y va ? [o/N] ')).strip().lower() not in ('y', 'yes', 'o', 'oui'):
        print(t('Nothing was changed.', 'Rien n\'a été modifié.'))
        return 0
    corsu.progress(3, 'Preparing', 'Préparation')
    target = deploy_release()
    if target != ROOT:
        command = [sys.executable, str(target / 'src/installer.py'), '--yes', '--components', *components]
        if 'discord' in components:
            command.extend(['--discord-path', str(location)])
        run(command, env={**os.environ, 'CORSU_DEPLOYED': str(target.resolve())})
        return 0
    if {'discord', 'vesktop'} & set(components):
        corsu.progress(5, 'Preparing the Discord plugin', 'Préparation du plugin Discord')
        prepare_build()
    if 'vesktop' in components and not vesktop_installed():
        import vesktop
        vesktop.install()
    if 'firefox' in components and not corsu.firefox_install():
        import firefox_download
        firefox_download.install()
    local = set(components) - {'discord', 'qt'}
    if 'qt' in components:
        local.add('desktop')
    if local:
        corsu.install(local, qt_system='qt' in components)
    if 'discord' in components:
        corsu.progress(85, 'Installing the Discord plugin', 'Installation du plugin Discord')
        install_discord(location)
        for other in sibling_versions(location):
            install_discord(other)
    corsu.progress(95, 'Creating shortcuts', 'Création des raccourcis')
    corsu.setup_shortcut(corsu.Installer())
    if ROOT.is_relative_to((corsu.DATA / 'releases').resolve()):
        prune_releases(ROOT)
    applications = corsu.HOME / '.local/share/applications'
    if corsu.PLATFORM == 'linux' and shutil.which('update-desktop-database') and applications.is_dir():
        # Only refreshes the menu cache; menus still update on the next login when it fails.
        subprocess.run(['update-desktop-database', str(applications)], check=False)
    if os.environ.get('CORSU_SETUP_WINDOW'):
        print(t('\nDone. Close Firefox, your browsers and Discord completely, then open them again.',
                '\nC\'est fait. Fermez complètement Firefox, vos navigateurs et Discord, puis rouvrez-les.'))
        return 0
    print(t('\nDone. Close Firefox, your browsers and Discord completely, then open them again.'
            + (' Log out and back in for the Plasma desktop.' if 'desktop' in components else '')
            + '\nTo add programs, go back to French or uninstall, open the Corsu app.',
            '\nC\'est fait. Fermez complètement Firefox, vos navigateurs et Discord, puis rouvrez-les.'
            + (' Déconnectez-vous et reconnectez-vous pour le bureau Plasma.' if 'desktop' in components else '')
            + '\nPour ajouter des logiciels, revenir au français ou tout retirer, ouvrez l\'application Corsu.'))
    return 0


if __name__ == '__main__':
    # Windows consoles default to a legacy code page; never crash on Corsican letters.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    import logbook
    logbook.start('installer')
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print(t('\nNo answer received; nothing was changed.', '\nAucune réponse reçue ; rien n\'a été modifié.'), file=sys.stderr)
        raise SystemExit(1)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        logbook.failure(error)
        print(t(f'Corsu stopped: {error}\nDetails: {logbook.path()}\nAnything already changed can be undone with the Corsu app.',
                f'Corsu s\'est arrêté : {error}\nDétails : {logbook.path()}\nCe qui a déjà été modifié peut être annulé avec l\'application Corsu.'),
              file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:  # Any other error: keep the full details in the log instead of a bare traceback.
        print(logbook.failure(error), file=sys.stderr)
        raise SystemExit(1)
