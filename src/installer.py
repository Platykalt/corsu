#!/usr/bin/env python3
"""Consent-based installer for the open-source Corsu UI overlay: Linux, Windows and macOS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
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
    import minecraft
    if minecraft.game_directories():
        result.append('minecraft')
    import apps
    result += apps.found()
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
# What src/minecraft.py reads to build and offer the pack. Missing from the installed copy, Minecraft stopped the
# installation (pack.mcmeta not found) although the extracted archive had it.
DEPLOYED_MINECRAFT = tuple(f'minecraft/java/{name}' for name in ('pack.mcmeta', 'co_fr.json', 'LICENSE.txt', 'VERSION',
                                                                # minecraft_packs: one pack per game version, offline.
                                                                'keys.tsv', 'versions.json', 'history.json'))


def deploy_release():
    """Keep launchers/builds working even after the downloaded archive is removed."""
    # Compare real paths: Windows short names (RUNNER~1) and macOS /var -> /private/var differ otherwise,
    # and the installer would re-run itself forever. The environment flag is a second guard.
    if ROOT.is_relative_to((corsu.DATA / 'releases').resolve()) or os.environ.get('CORSU_DEPLOYED') == str(ROOT):
        return ROOT
    fingerprint = hashlib.sha256()
    printed = sorted([*(path for path in (ROOT / 'src').rglob('*') if path.is_file() and '__pycache__' not in path.parts),
                      *(ROOT / name for name in DEPLOYED_FILES + DEPLOYED_MINECRAFT if (ROOT / name).is_file()),
                      *(ROOT / 'lexicon').glob('*.tsv'), *(ROOT / 'Vencord/dist').glob('*.*')])
    for path in printed:
        fingerprint.update(path.relative_to(ROOT).as_posix().encode() + b'\0' + path.read_bytes())
    target = corsu.DATA / 'releases' / fingerprint.hexdigest()[:16]
    if target.exists():
        # Earlier versions deleted old copies file by file; one in use on Windows could be left half deleted.
        relative = [path.relative_to(ROOT) for path in printed]
        if all((target / name).is_file() and (target / name).stat().st_size == (ROOT / name).stat().st_size
               for name in relative):
            return target
        if not discard(target):
            raise RuntimeError(t(f'{target} is incomplete and in use; close Corsu and the programs it translates, then retry.',
                                 f'{target} est incomplet et utilisé ; fermez Corsu et les logiciels traduits, puis réessayez.'))
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='stage-', dir=target.parent))
    try:
        for name in DEPLOYED_FILES + DEPLOYED_MINECRAFT:
            if (ROOT / name).is_file():
                (stage / name).parent.mkdir(parents=True, exist_ok=True)
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


def machine():
    """The processor name used for the bundled Python folders: x86_64 or aarch64."""
    name = platform.machine().lower()
    return {'amd64': 'x86_64', 'x64': 'x86_64', 'arm64': 'aarch64'}.get(name, name)


def runtime_python(root):
    """The bundled Python's interpreter under `root` (runtime/<processor>/python, or a copy of it)."""
    python = root / 'python'
    return python / 'python.exe' if corsu.PLATFORM == 'windows' else python / 'bin/python3'


def deploy_runtime():
    """Release archives carry their own Python for computers without one. When Corsu runs on it, copy it once to
    Corsu's data folder, shared by every copy of Corsu, so launchers keep working after the archive is deleted.
    Returns the interpreter later steps and launchers should use."""
    bundled = ROOT / 'runtime' / machine()
    current = Path(sys.executable).resolve()
    if not bundled.is_dir() or not current.is_relative_to(bundled.resolve()):
        return Path(sys.executable)
    version = json.loads((ROOT / 'src/release.json').read_text(encoding='utf-8'))['python_runtime']['version']
    target = corsu.DATA / 'runtime' / version.replace('+', '-')
    if not runtime_python(target).exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix='stage-', dir=target.parent))
        try:
            shutil.copytree(bundled / 'python', stage / 'python', symlinks=True,
                            ignore=shutil.ignore_patterns('__pycache__'))
            shutil.rmtree(target, ignore_errors=True)
            stage.rename(target)
        except BaseException:
            shutil.rmtree(stage, ignore_errors=True)
            raise
    return runtime_python(target)


def prune_runtimes():
    """Delete copies of the bundled Python that neither this run nor any launcher uses any more."""
    folder = corsu.DATA / 'runtime'
    if not folder.is_dir():
        return
    keep = folders_in_use(folder)
    current = Path(sys.executable).resolve()
    for runtime in folder.iterdir():
        if runtime.is_dir() and runtime.name not in keep and not current.is_relative_to(runtime.resolve()):
            shutil.rmtree(runtime, ignore_errors=True)


def releases_in_use():
    """Release folders something still loads: Discord's patched app.asar, Vesktop, and every launcher or shortcut
    Corsu wrote (the Firefox launcher, the Corsu entry, Windows .cmd files, macOS applets). Installing one part
    leaves the others on the copy they were written with, so that copy must stay."""
    return folders_in_use(corsu.DATA / 'releases')


def managed_places(state=None):
    state = corsu.load_state() if state is None else state
    return [Path(name) for name in state.get('files', {})] + [corsu.CONFIG / 'vesktop/state.json']


def folders_in_use(parent, places=None):
    """Names of the folders of `parent` that a file Corsu wrote (or Vesktop's settings) refers to."""
    used = set()
    # Written paths may use either form of the same folder (C:\Users\RUNNER~1 or C:\Users\runneradmin).
    prefixes = {str(form).replace('\\', '/') for form in (parent, parent.resolve())}
    # Windows paths ignore case, and shortcuts do not always keep it.
    fold = str.lower if corsu.PLATFORM == 'windows' else str
    prefixes = {fold(prefix) for prefix in prefixes}
    places = managed_places() if places is None else places
    files = []
    for place in places:
        if place.is_dir():
            files.extend(path for path in place.rglob('*') if path.is_file())
        else:
            files.append(place)
    for path in files:
        try:
            # Large files (translation packs, browser archives) never hold a launcher path.
            if path.stat().st_size > 4_000_000:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        # Compiled AppleScript keeps its strings in UTF-16.
        for encoding in ('utf-8', 'utf-16-be', 'utf-16-le'):
            text = fold(data.decode(encoding, 'replace').replace('\\\\', '/').replace('\\', '/'))
            for prefix in prefixes:
                start = text.find(prefix)
                while start != -1:
                    used.add(text[start + len(prefix) + 1:].split('/', 1)[0])
                    start = text.find(prefix, start + 1)
    return used


RELEASE_NAME = re.compile(r'[0-9a-f]{16}')
# The Corsu entry of the applications menu: the copy it opens is the installed one.
CORSU_ENTRIES = ('corsu-setup.desktop', 'Corsu.lnk', 'Corsu.app')


def version_tuple(text):
    return tuple(int(part) for part in str(text or '').lstrip('v').split('.') if part.isdigit())


def release_version(folder):
    """The version a Corsu copy (a release folder, an extracted archive, a source folder) says it is, or None."""
    try:
        return json.loads((Path(folder) / 'src/release.json').read_text(encoding='utf-8'))['version']
    except (OSError, ValueError, KeyError, TypeError):
        return None


def genuine_release(folder):
    """A copy Corsu deployed itself: a fingerprint name in corsu.DATA/releases and its release.json inside. Nothing
    else there is ever deleted."""
    folder = Path(folder)
    return bool(RELEASE_NAME.fullmatch(folder.name)) and folder.is_dir() and release_version(folder) is not None


def folder_name(text):
    """The last part of a path written on any system (C:\\...\\abc or /home/.../abc)."""
    return re.split(r'[\\/]', str(text).rstrip('\\/'))[-1]


def installed_release(state=None):
    """The installed Corsu release: {'version', 'folder', 'installed_at'}, or None when Corsu is not installed.

    Recorded in installation.json → 'release' from 0.23 on. Versions 0.21 and 0.22 did not record it: the copy their
    launchers start is the installed one, the Corsu menu entry first; when launchers point at several copies
    (installations made over time), the newest version among them."""
    state = corsu.load_state() if state is None else state
    releases = corsu.DATA / 'releases'
    recorded = state.get('release')
    if isinstance(recorded, dict) and recorded.get('folder'):
        folder = releases / folder_name(recorded['folder'])
        if genuine_release(folder):
            return {'version': release_version(folder), 'folder': str(folder),
                    'installed_at': recorded.get('installed_at'), 'python': recorded.get('python')}
    places = [place for place in managed_places(state) if place.name != 'app.asar']
    entries = [place for place in places if place.name in CORSU_ENTRIES]
    for group in (entries, places):
        candidates = [releases / name for name in folders_in_use(releases, group) if genuine_release(releases / name)]
        if candidates:
            folder = max(candidates, key=lambda path: (version_tuple(release_version(path)), path.stat().st_mtime))
            return {'version': release_version(folder), 'folder': str(folder), 'installed_at': folder.stat().st_mtime}
    return None


def version_policy(running, installed):
    """What running this copy does: 'install' (nothing installed), 'update' (newer), 'repair' (same version) or
    'downgrade' (older: refused unless asked for explicitly)."""
    if not installed:
        return 'install'
    if version_tuple(running) > version_tuple(installed):
        return 'update'
    if version_tuple(running) == version_tuple(installed):
        return 'repair'
    return 'downgrade'


def record_release(before):
    """The installed release is now this copy; the one it replaces is kept until the next successful update."""
    state = corsu.load_state()
    if before and folder_name(before['folder']) != ROOT.name:
        state['previous_release'] = before
    # The window restarts Corsu from here: the copy, and the Python its launchers use (this run's, which is the
    # copied bundled runtime when there is one).
    state['release'] = {'version': release_version(ROOT), 'folder': str(ROOT), 'python': str(Path(sys.executable)),
                        'installed_at': time.time()}
    corsu.save_state(state)


def restore_launchers(before, target):
    """The new copy's installer stopped: point the launchers back at the copy that worked before (complete, and
    never deleted before a successful update). The new copy stays; the next run reuses it."""
    if not before or folder_name(before['folder']) == Path(target).name:
        return
    previous = corsu.DATA / 'releases' / folder_name(before['folder'])
    if not genuine_release(previous):
        return
    try:
        corsu.refresh_launchers(corsu.Installer(), previous)
        print(t(f'The launchers still open Corsu {before["version"]}.',
                f'Les raccourcis ouvrent toujours Corsu {before["version"]}.'), file=sys.stderr)
    except (OSError, RuntimeError) as error:
        print(t(f'Note: the launchers could not all be pointed back ({error}).',
                f'Note : les raccourcis n\'ont pas tous pu être remis ({error}).'), file=sys.stderr)


DAY = 24 * 3600


def discard(path):
    """Delete a folder without ever leaving half of one in use: it is renamed first, which Windows refuses while a
    program uses a file in it (it then stays, and a later run tries again)."""
    trash = path.with_name(f'trash-{path.name}-{os.getpid()}')
    try:
        path.rename(trash)
    except OSError:
        return False
    shutil.rmtree(trash, ignore_errors=True)
    return True


def clean_leftovers(folder):
    """Remove what interrupted runs left: copies being made (stage-*) a day old, folders being deleted (trash-*)."""
    if not folder.is_dir():
        return
    for path in folder.iterdir():
        try:
            old = time.time() - path.stat().st_mtime > DAY
        except OSError:
            continue
        if path.is_dir() and (path.name.startswith('trash-') or (path.name.startswith('stage-') and old)):
            shutil.rmtree(path, ignore_errors=True)


CLIENTS = ('Discord', 'DiscordPTB', 'DiscordCanary', 'Vesktop', 'vesktop')


def clients_running():
    """Whether Discord or Vesktop is open: an open client keeps using the Corsu copy it started with."""
    try:
        if corsu.PLATFORM == 'linux':
            for comm in Path('/proc').glob('[0-9]*/comm'):
                try:
                    if comm.read_text().strip() in CLIENTS:
                        return True
                except OSError:
                    continue
            return False
        if corsu.PLATFORM == 'windows':
            output = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, check=False).stdout
            return any(f'"{name}.exe"'.lower() in output.lower() for name in CLIENTS)
        return any(subprocess.run(['pgrep', '-x', name], capture_output=True, check=False).returncode == 0
                   for name in CLIENTS)
    except OSError:
        # Unknown: keeping a copy one run longer is harmless, deleting one in use is not.
        return True


def prune_releases(current, loaded=()):
    """Delete the copies of earlier Corsu versions, keeping the current one, the one it replaced (until the next
    successful update), any still in use, and the ones an open Discord or Vesktop loaded before this run (its new
    windows and style reloads still read them). Only Corsu's own release folders are ever deleted."""
    folder = corsu.DATA / 'releases'
    if not folder.is_dir():
        return
    clean_leftovers(folder)
    keep = releases_in_use() | {Path(current).name}
    # The Corsu app that started this installation keeps running from its own copy.
    if os.environ.get('CORSU_APP_ROOT'):
        keep.add(folder_name(os.environ['CORSU_APP_ROOT']))
    state = corsu.load_state()
    for name in ('release', 'previous_release'):
        if isinstance(state.get(name), dict) and state[name].get('folder'):
            keep.add(folder_name(state[name]['folder']))
    running = set(state.get('running_releases', [])) | set(loaded)
    running = {name for name in running if (folder / name).is_dir()} if clients_running() else set()
    keep |= running
    if state.get('running_releases', []) != sorted(running) and corsu.STATE.exists():
        state['running_releases'] = sorted(running)
        corsu.save_state(state)
    for release in folder.iterdir():
        if release.name not in keep and genuine_release(release):
            discard(release)


def vencord_installer():
    """Return the checksum-verified official Vencord installer, downloading the pinned build if absent."""
    manifest = json.loads((ROOT / 'src/release.json').read_text(encoding='utf-8'))
    entry = manifest['installers'][corsu.PLATFORM]
    binary = ROOT / 'vendor' / entry['file']
    if corsu.PLATFORM == 'linux' and platform.machine().lower() not in ('x86_64', 'amd64'):
        raise RuntimeError('The official Discord installer supports Linux x86_64. Use Vesktop on this architecture.')
    if not binary.exists() or hashlib.sha256(binary.read_bytes()).hexdigest() != entry['sha256']:
        # Missing, or cut short by an interrupted download: fetch the pinned build again.
        print('Downloading the official Vencord installer...', flush=True)
        try:
            with urllib.request.urlopen(manifest['installer_base_url'] + entry['file'], timeout=60) as response:
                downloaded = response.read()
        except OSError as error:
            raise RuntimeError(f'Official Vencord installer missing or checksum mismatch, and it could not be '
                               f'downloaded again ({error}); nothing executed. Check the connection and retry.') from None
        if hashlib.sha256(downloaded).hexdigest() != entry['sha256']:
            raise RuntimeError('Downloaded installer checksum mismatch; nothing executed.')
        binary.parent.mkdir(parents=True, exist_ok=True)
        temp = binary.with_name(binary.name + '.corsu-tmp')
        temp.write_bytes(downloaded)
        temp.chmod(0o755)
        temp.replace(binary)
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
        corsu.save_state(state)


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
    corsu.save_state(installer.state)
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
    'minecraft': ('Minecraft Java Edition: Corsican as the game language', 'Minecraft Java Edition : le corse comme langue du jeu'),
}


def apps_ids():
    import apps
    return list(apps.registry())


def describe(name):
    if name in DESCRIPTIONS:
        return t(*DESCRIPTIONS[name])
    import apps
    app = apps.registry()[name]
    return t(app.description['en'][1], app.description['fr'][1])


def choose(available):
    """Ask which detected applications to translate. Rerun the setup later to add more."""
    installed, state = set(), {}
    if corsu.STATE.exists():
        state = corsu.load_state()
        installed = set(state.get('components', []))
    # Running the installer again keeps what was chosen: only installed parts are ticked, new ones are offered.
    selected = {name: (name in installed) if installed else True for name in available}
    while True:
        print(t('Select what you want to translate:', 'Choisissez ce que vous voulez traduire :'))
        for number, name in enumerate(available, 1):
            mark = 'x' if selected[name] else ' '
            note = ''
            if name in installed:
                note = (t('  (installed, switched off)', '  (installé, désactivé)') if corsu.is_disabled(name, state)
                        else t('  (installed)', '  (déjà installé)'))
            print(f'  [{mark}] {number}. {describe(name)}{note}')
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
    if 'minecraft' in components:
        import minecraft
        print(t('  Minecraft Java Edition: in each game folder playing a supported version, add the Corsican resource pack,'
                ' turn it on and choose Corsu as the language in options.txt. Close Minecraft first.',
                '  Minecraft Java Edition : dans chaque dossier de jeu qui joue une version prise en charge, ajouter le pack'
                ' de ressources corse, l\'activer et choisir Corsu comme langue dans options.txt. Fermez Minecraft d\'abord.'))
        for folder in minecraft.find_folders():
            state = t('yes', 'oui') if folder.compatible else t('no: version not supported or unknown',
                                                                  'non : version non prise en charge ou inconnue')
            print(f'    - {folder.describe()} : {state}')
    import apps
    for app_id in [name for name in components if name in apps.registry()]:
        for installation in apps.registry()[app_id].find():
            state = (t('switch to Corsican', 'passer en corse') if installation.usable
                     else t('left alone: ', 'laissé tel quel : ') + installation.reason)
            print(f'  {installation.describe()} : {state}')
    print(t(f'\nA copy of every file Corsu changes is kept in {corsu.DATA}, and the Corsu app can undo everything.',
            f'\nUne copie de chaque fichier modifié est gardée dans {corsu.DATA}, et l\'application Corsu peut tout annuler.'))
    print(t('Text without a Corsican translation yet stays in French. Messages are never changed.\n',
            'Le texte sans traduction corse reste en français. Les messages ne sont jamais modifiés.\n'))


class Refused(RuntimeError):
    """This copy is older than the installed Corsu: nothing was changed."""


# Exit codes: another Corsu process is busy (EX_TEMPFAIL), or the version policy refused this copy.
BUSY, REFUSED = 75, 3


def keep_choices(components, available, location, state):
    """The parts to (re)install now, and why the others are left as they are.

    A part installed and switched off stays off: an update or a repair never switches it back on (the Corsu app's
    switch or --enable does). A part installed earlier whose program is gone is left alone, not an error."""
    recorded = set(state.get('components', [])) | ({'qt'} if state.get('qt_system') else set())
    kept, notes = [], []
    for component in dict.fromkeys(components):
        part = 'desktop' if component == 'qt' else component
        name = corsu.component_names([part])
        if component in recorded and corsu.is_disabled(part, state):
            notes.append(t(f'{name}: switched off, stays off (switch it on in the Corsu app).',
                           f'{name} : désactivé, le reste (activez-le dans l\'application Corsu).'))
            continue
        found = component in available or (component == 'discord' and location and discord_archive(location).exists())
        if component in recorded and not found:
            notes.append(t(f'{name}: no longer found on this computer; left as it is.',
                           f'{name} : introuvable sur cet ordinateur ; laissé tel quel.'))
            continue
        kept.append(component)
    return kept, notes


def announce(action, running, installed):
    if action == 'update':
        print(t(f'Corsu {installed} is installed: updating it to {running}. Your choices are kept.',
                f'Corsu {installed} est installé : mise à jour vers {running}. Vos choix sont gardés.'))
    elif action == 'repair':
        print(t(f'Corsu {running} is already installed: repairing it. Your choices are kept.',
                f'Corsu {running} est déjà installé : réparation. Vos choix sont gardés.'))
    elif action == 'downgrade':
        print(t(f'Corsu {installed} is installed: going back to the older {running}, as asked.',
                f'Corsu {installed} est installé : retour à la version antérieure {running}, comme demandé.'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', nargs='+', choices=['firefox', 'chromium', 'desktop', 'discord', 'vesktop', 'qt', 'minecraft', *apps_ids()],
                        help='Default: the parts already installed, or on a first installation every supported integration found on this computer.')
    parser.add_argument('--discord-path', type=Path,
                        help='Native Discord location: folder with resources/ (Linux), %%LOCALAPPDATA%%\\Discord (Windows) or Discord.app (macOS)')
    parser.add_argument('--yes', action='store_true', help='Accept the displayed installation plan')
    parser.add_argument('--dry-run', action='store_true', help='Display the plan without downloading or changing anything')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--allow-downgrade', action='store_true',
                        help='Install this copy even though a newer Corsu is installed')
    # The Windows launcher cannot drop its own --text option before passing the rest on.
    parser.add_argument('--text', action='store_true', help=argparse.SUPPRESS)
    parts = ['firefox', 'chromium', 'discord', 'vesktop', 'desktop', 'terminal', 'minecraft', *apps_ids()]
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
        with corsu.lock('enable' if args.enable is not None else 'disable'):
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
        with corsu.lock('uninstall'):
            corsu.uninstall()
        return 0
    # The copy started by the installer that deployed it: that one already decided, holds the lock and showed the plan.
    child = bool(os.environ.get('CORSU_DEPLOYED')) and os.environ.get('CORSU_DEPLOYED') == str(ROOT)
    state = corsu.load_state()
    installed = installed_release(state)
    running = release_version(ROOT)
    action = version_policy(running, installed and installed['version'])
    if not child:
        if action == 'downgrade' and not args.allow_downgrade:
            raise Refused(t(
                f'Corsu {installed["version"]} is installed and this copy is the older {running}; nothing was changed. '
                'To go back to it anyway, run the installer again with --allow-downgrade.',
                f'Corsu {installed["version"]} est installé et cette copie est la version antérieure {running} ; rien n\'a été '
                'modifié. Pour y revenir quand même, relancez l\'installeur avec --allow-downgrade.'))
        announce(action, running, installed and installed['version'])
    available = available_components()
    location = args.discord_path.resolve() if args.discord_path else discord_location()
    if args.discord_path and not discord_archive(location).exists():
        # A path remembered from before a Discord update; Discord has removed that version since.
        print(t(f'Note: {location} no longer exists; using the Discord found on this computer.',
                f'Note : {location} n\'existe plus ; utilisation du Discord trouvé sur cet ordinateur.'))
        location = discord_location()
    forget_removed_discord()
    state = corsu.load_state()
    if args.discord_path and 'discord' not in available and discord_archive(location).exists():
        available = [*available, 'discord']
    recorded = [name for name in state.get('components', []) if name != 'terminal']
    if state.get('qt_system'):
        recorded.append('qt')
    # Without a list, running the installer again repairs what is installed; it never adds parts nobody chose.
    components = args.components if args.components is not None else (recorded or available)
    if args.components is None and available and not (args.yes or args.dry_run) and sys.stdin.isatty():
        components = choose(available)
        if not components:
            print(t('Nothing selected, nothing was changed.', 'Rien de sélectionné, rien n\'a été modifié.'))
            return 0
    requested = list(components)
    components, notes = keep_choices(components, available, location, state)
    if not child:
        for note in notes:
            print(note)
    if not requested:
        parser.error(t('Corsu found nothing to translate here. Install Firefox, a Chromium browser, Discord or KDE Plasma first.',
                       'Corsu n\'a rien trouvé à traduire ici. Installez d\'abord Firefox, un navigateur Chromium, Discord ou KDE Plasma.'))
    for component in components:
        if component not in available and not (component == 'discord' and location and discord_archive(location).exists()):
            if component in ('desktop', 'qt') and corsu.PLATFORM != 'linux':
                parser.error(f'{component} is for KDE Plasma on Linux.')
            parser.error(f'{component} was not found on this computer.')
    # The Corsu app shows the plan before starting; its log only needs what happens next.
    if not os.environ.get('CORSU_SETUP_WINDOW') and not child:
        show_plan(components, location)
    if args.dry_run:
        return 0
    if not args.yes and input(t('Go ahead? [y/N] ', 'On y va ? [o/N] ')).strip().lower() not in ('y', 'yes', 'o', 'oui'):
        print(t('Nothing was changed.', 'Rien n\'a été modifié.'))
        return 0
    with corsu.lock(action if action in corsu.ACTIONS else 'install'):
        return apply(args, requested, components, location)


def apply(args, requested, components, location):
    corsu.progress(3, 'Preparing', 'Préparation')
    # The installed copy before this run: kept until the next successful update, and used again if this one fails.
    before = installed_release()
    # What Discord and Vesktop loaded at their start: they keep using it until they restart.
    loaded = releases_in_use()
    target = deploy_release()
    python = deploy_runtime()
    if target != ROOT:
        # The installed copy decides again from the same state: parts switched off stay off.
        command = [str(python), str(target / 'src/installer.py'), '--yes', '--components', *requested]
        if 'discord' in components:
            command.extend(['--discord-path', str(location)])
        if args.allow_downgrade:
            command.append('--allow-downgrade')
        try:
            run(command, env={**os.environ, 'CORSU_DEPLOYED': str(target.resolve())})
        except BaseException:
            restore_launchers(before, target)
            raise
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
    shortcuts = corsu.Installer()
    corsu.setup_shortcut(shortcuts)
    corsu.refresh_launchers(shortcuts)
    if ROOT.is_relative_to((corsu.DATA / 'releases').resolve()):
        record_release(before)
        prune_releases(ROOT, loaded)
    prune_runtimes()
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
    except (corsu.Busy, Refused) as error:
        # Nothing was changed: no "stopped" message, and an exit code callers can tell apart.
        logbook.failure(error)
        print(error, file=sys.stderr)
        raise SystemExit(BUSY if isinstance(error, corsu.Busy) else REFUSED)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        logbook.failure(error)
        print(t(f'Corsu stopped: {error}\nDetails: {logbook.path()}\nAnything already changed can be undone with the Corsu app.',
                f'Corsu s\'est arrêté : {error}\nDétails : {logbook.path()}\nCe qui a déjà été modifié peut être annulé avec l\'application Corsu.'),
              file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:  # Any other error: keep the full details in the log instead of a bare traceback.
        print(logbook.failure(error), file=sys.stderr)
        raise SystemExit(1)
