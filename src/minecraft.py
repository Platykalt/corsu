"""Minecraft: Java Edition in Corsican: the resource pack, and Corsican as the game's language.

Corsu finds every Minecraft game folder (the official launcher's and the folders its profiles point to, the
instances of Prism Launcher, PolyMC and MultiMC wherever their settings put them) and the game version each one plays,
under a mod loader too. Where minecraft_packs has a pack for that version (minecraft/java/MULTIVERSION.md), it copies
that version's pack, always under the same file name, adds it to the active resource packs and sets the language to
Corsican as that version writes it in options.txt. Only those settings are recorded and reverted: Minecraft rewrites
options.txt itself, so the rest of the file is never put back. Minecraft must be closed, because it writes
options.txt again when it quits.
"""
import io
import json
import os
from pathlib import Path
import re
import struct
import zipfile
import zlib

import corsu

SOURCE = corsu.ROOT / 'minecraft/java'
PACK = 'corsu-minecraft-java.zip'
PACK_ID = 'file/' + PACK
LANGUAGE = 'co_fr'
# The pack goes in resourcePacks only. Listing it in incompatibleResourcePacks too (earlier versions did, to keep it on
# in other game versions) made 26.3 skip it at the next start: Options.loadSelectedResourcePacks only takes a
# compatible pack off that list and does not select it, so the person had to pick it by hand once.
LIST_OPTIONS = ('resourcePacks', 'incompatibleResourcePacks')


def png(size=64):
    """pack.png: the white field and black band colours of the Corsican flag, without an image library."""
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            row += bytes((30, 30, 30)) if abs(x - y) < size // 8 else bytes((245, 245, 245))
        rows.append(bytes(row))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b''.join(rows), 9)) + chunk(b'IEND', b''))


def make_pack(mcmeta, translation, license_text):
    """The resource pack as bytes. Fixed dates and order: the same sources always give the same file."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        def add(name, data):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
        add('pack.mcmeta', mcmeta)
        add('pack.png', png())
        add(f'assets/minecraft/lang/{LANGUAGE}.json', translation)
        add('LICENSE.txt', license_text)
    return buffer.getvalue()


def pack_from_sources():
    """The pack built from the committed files (minecraft/java/pack.mcmeta is written by tools/minecraft.py)."""
    return make_pack((SOURCE / 'pack.mcmeta').read_bytes(), (SOURCE / 'co_fr.json').read_bytes(),
                     (SOURCE / 'LICENSE.txt').read_bytes())


DEFAULT_LISTS = {'resourcePacks': ['vanilla'], 'incompatibleResourcePacks': []}

# The packs of every handled game version (minecraft/java/MULTIVERSION.md). Imported on first use and kept as a
# module attribute, so tests replace it with a fake.
minecraft_packs = None


def _packs():
    global minecraft_packs
    if minecraft_packs is None:
        import minecraft_packs as module
        minecraft_packs = module
    return minecraft_packs


def target(version):
    """The versions.json entry of a game version when Corsu builds a pack for it, else None."""
    if not version:
        return None
    entry = _packs().target(version)
    return entry if isinstance(entry, dict) and entry.get('supported') else None


def version_key(version):
    """(1, 20, 2) for '1.20.2', None for a snapshot or anything else that is not a release number."""
    if not isinstance(version, str) or not re.fullmatch(r'\d+(\.\d+)+', version):
        return None
    return tuple(int(part) for part in version.split('.'))


def supported_text():
    """The supported versions, for messages: every one when few, else the range."""
    listing = getattr(_packs(), 'supported_versions', None)
    try:
        versions = sorted(set(listing()), key=lambda version: version_key(version) or ()) if callable(listing) else []
    except Exception:  # an optional helper of the packs module; a message must not stop the installation
        versions = []
    if not versions:
        return corsu.t('the versions listed in minecraft/java/STATUS.md', 'les versions listées dans minecraft/java/STATUS.md')
    if len(versions) <= 6:
        return ', '.join(versions)
    return corsu.t(f'{len(versions)} versions from {versions[0]} to {versions[-1]}',
                   f'{len(versions)} versions de {versions[0]} à {versions[-1]}')


class Folder:
    """One Minecraft game folder, the game version it plays when Corsu can tell (the base version under a mod
    loader), the loader (for display), and why it is skipped if it is. `profiles`: for an official launcher folder,
    every profile using it ({name, id, version, loader, used}), the first being the one used last."""

    def __init__(self, path, launcher, version=None, note='', loader=None, profiles=()):
        self.path, self.launcher, self.version, self.note = Path(path), launcher, version, note
        self.loader, self.profiles = loader, list(profiles)

    @property
    def compatible(self):
        return target(self.version) is not None

    def describe(self):
        version = self.version or corsu.t('version unknown', 'version inconnue')
        if self.loader:
            version += f', {self.loader}'
        return f'{self.path} ({self.launcher}, {version})'


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


# Prism Launcher and the launchers it comes from (PolyMC, MultiMC) keep their settings in one INI file in their data
# folder; InstanceDir there says where the instances are (default "instances"), relative to the data folder or
# absolute, and Prism Launcher 9 adds AdditionalInstanceDirs. Source: PrismLauncher/PrismLauncher, launcher/Application.cpp
# (registerSetting("InstanceDir", "instances"), registerSetting("AdditionalInstanceDirs", QStringList()); the data
# folder is the current directory when they are read, so a relative path is relative to it; the configuration file is
# BuildConfig.LAUNCHER_CONFIGFILE, then "polymc.cfg", then "multimc.cfg").
CONFIG_FILES = ('prismlauncher.cfg', 'polymc.cfg', 'multimc.cfg')


def launcher_data_dirs():
    """Data folders of Prism Launcher, PolyMC and MultiMC installed the usual way, with the launcher's name.
    A portable Prism Launcher (portable.txt or UserData/ next to the program) keeps its data beside the program:
    it is found only when PRISMLAUNCHER_DATA_DIR names it, Corsu has no way to know where it was unpacked."""
    home = corsu.HOME
    found = []
    if os.environ.get('PRISMLAUNCHER_DATA_DIR'):
        found.append((Path(os.environ['PRISMLAUNCHER_DATA_DIR']), 'Prism Launcher'))
    if corsu.PLATFORM == 'windows':
        appdata = Path(os.environ.get('APPDATA', home / 'AppData/Roaming'))
        return found + [(appdata / 'PrismLauncher', 'Prism Launcher'), (appdata / 'PolyMC', 'PolyMC'),
                        (appdata / 'MultiMC', 'MultiMC')]
    if corsu.PLATFORM == 'macos':
        support = home / 'Library/Application Support'
        return found + [(support / 'PrismLauncher', 'Prism Launcher'), (support / 'PolyMC', 'PolyMC'),
                        (support / 'MultiMC', 'MultiMC')]
    data = Path(os.environ.get('XDG_DATA_HOME') or home / '.local/share')
    return found + [(data / 'PrismLauncher', 'Prism Launcher'),
                    (home / '.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher', 'Prism Launcher'),
                    (data / 'PolyMC', 'PolyMC'), (home / '.var/app/org.polymc.PolyMC/data/PolyMC', 'PolyMC'),
                    (data / 'multimc', 'MultiMC')]


def ini_value(raw):
    """One value as Qt's INI format writes it: quoted when it holds special characters, backslashes doubled."""
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        raw = raw[1:-1]
    return re.sub(r'\\(.)', r'\1', raw)


def ini_list(raw):
    """A QStringList in Qt's INI format: comma-separated, each item possibly quoted; @Invalid() when empty."""
    raw = raw.strip()
    if not raw or raw.startswith('@'):
        return []
    return [ini_value(item) for item in re.findall(r'"(?:[^"\\]|\\.)*"|[^,]+', raw) if item.strip()]


def launcher_settings(data_dir):
    for name in CONFIG_FILES:
        try:
            text = (data_dir / name).read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        values = {}
        for line in text.splitlines():
            key, equals, value = line.partition('=')
            if equals and not key.startswith(('[', ';', '#')):
                values.setdefault(key.strip(), value)
        return values
    return {}


def instance_dirs(data_dir):
    """The instance folders of one launcher data folder, from its settings (default: instances/)."""
    settings = launcher_settings(data_dir)
    names = [ini_value(settings.get('InstanceDir', '')) or 'instances'] + ini_list(settings.get('AdditionalInstanceDirs', ''))
    result = []
    for name in names:
        path = Path(name)
        path = path if path.is_absolute() else data_dir / path
        if path not in result:
            result.append(path)
    return result


def launcher_roots():
    """Folders of launchers that keep several game folders (instances), with the launcher's name."""
    roots = []
    for data_dir, launcher in launcher_data_dirs():
        if data_dir.is_dir():
            roots += [(path, launcher) for path in instance_dirs(data_dir) if (path, launcher) not in roots]
    return roots


def official_roots():
    home = corsu.HOME
    if corsu.PLATFORM == 'windows':
        return [Path(os.environ.get('APPDATA', home / 'AppData/Roaming')) / '.minecraft']
    if corsu.PLATFORM == 'macos':
        return [home / 'Library/Application Support/minecraft']
    return [home / '.minecraft', home / '.var/app/com.mojang.Minecraft/.minecraft']


# Components of a Prism Launcher / MultiMC instance (mmc-pack.json) that load mods; the game version is always
# net.minecraft's.
LOADERS = {'net.fabricmc.fabric-loader': 'Fabric', 'org.quiltmc.quilt-loader': 'Quilt',
           'net.minecraftforge': 'Forge', 'net.neoforged': 'NeoForge', 'com.mumfrey.liteloader': 'LiteLoader'}


def instance_details(instance):
    """(game version, loader) of a Prism Launcher or MultiMC instance: mmc-pack.json, or instance.cfg for old ones."""
    version = loader = None
    pack = read_json(instance / 'mmc-pack.json')
    if isinstance(pack, dict) and isinstance(pack.get('components'), list):
        for component in pack['components']:
            if not isinstance(component, dict):
                continue
            if component.get('uid') == 'net.minecraft' and isinstance(component.get('version'), str):
                version = component['version']
            elif component.get('uid') in LOADERS and loader is None:
                loader = LOADERS[component['uid']]
                if isinstance(component.get('version'), str):
                    loader += ' ' + component['version']
    if version is None:
        try:
            lines = (instance / 'instance.cfg').read_text(encoding='utf-8', errors='replace').splitlines()
        except OSError:
            lines = []
        for line in lines:
            if line.startswith('IntendedVersion='):
                version = line.partition('=')[2].strip() or None
    return version, loader


def instance_version(instance):
    return instance_details(instance)[0]


def instance_game_folder(instance):
    """Where an instance plays: minecraft/, or .minecraft/ when only that one exists. As Prism Launcher decides it:
    PrismLauncher/PrismLauncher, launcher/minecraft/MinecraftInstance.cpp, MinecraftInstance::gameRoot()
    (".minecraft" if it exists and "minecraft" does not, else "minecraft")."""
    if (instance / '.minecraft').is_dir() and not (instance / 'minecraft').is_dir():
        return instance / '.minecraft'
    return instance / 'minecraft'


def loader_of(version_id, data):
    """The mod loader of an official launcher version, from its id and its libraries, or None for the plain game."""
    text = (version_id or '').lower()
    libraries = ' '.join(str(library.get('name', '')) for library in (data or {}).get('libraries', [])
                         if isinstance(library, dict)).lower() if isinstance(data, dict) else ''
    if 'neoforge' in text or 'net.neoforged' in libraries:
        return 'NeoForge'
    if 'quilt' in text or 'org.quiltmc:quilt-loader' in libraries:
        return 'Quilt'
    if 'fabric' in text or 'net.fabricmc:fabric-loader' in libraries:
        return 'Fabric'
    if 'forge' in text or 'net.minecraftforge' in libraries:
        return 'Forge'
    if 'optifine' in text or 'optifine:' in libraries:
        return 'OptiFine'
    return None


def version_details(root, version):
    """(game version, loader) of an official launcher profile's version: latest-release / latest-snapshot are the
    newest of that type installed in versions/; a modded version (Fabric, Quilt, Forge, NeoForge, OptiFine) is the
    version it inherits from (inheritsFrom) or whose game it runs (jar); an id without its JSON is read by
    minecraft_packs.base_version."""
    versions = root / 'versions'
    if version in ('latest-release', 'latest-snapshot'):
        kind = 'release' if version == 'latest-release' else 'snapshot'
        newest = None
        if versions.is_dir():
            for folder in versions.iterdir():
                data = read_json(folder / f'{folder.name}.json')
                if isinstance(data, dict) and data.get('type') == kind and data.get('releaseTime'):
                    if newest is None or data['releaseTime'] > newest[0]:
                        newest = (data['releaseTime'], folder.name)
        return (newest[1] if newest else None), None
    if not isinstance(version, str) or not version:
        return None, None
    loader, seen, current = None, set(), version
    while True:
        if current in seen or len(seen) > 8:
            return None, loader
        seen.add(current)
        data = read_json(versions / current / f'{current}.json')
        loader = loader or loader_of(current, data)
        parent = None
        if isinstance(data, dict):
            parent = data.get('inheritsFrom') or (data.get('jar') if data.get('jar') != current else None)
        if not isinstance(parent, str) or not parent:
            break
        current = parent
    if loader or not isinstance(data, dict):
        return _packs().base_version(current) or current, loader
    return current, loader


def resolve_version(root, version):
    return version_details(root, version)[0]


def official_folders(root):
    """The official launcher's folder and the game folders its profiles point to. Several profiles may share a folder
    with different versions; the folder follows the profile used last, the one the launcher starts again, and the
    others are kept for the report."""
    launcher = corsu.t('official launcher', 'lanceur officiel')
    profiles = read_json(root / 'launcher_profiles.json')
    if not isinstance(profiles, dict) or not isinstance(profiles.get('profiles'), dict):
        return [Folder(root, launcher, None,
                       corsu.t('no launcher profile to tell the version', 'aucun profil du lanceur pour connaître la version'))]
    names = {'latest-release': corsu.t('Latest release', 'Dernière version'),
             'latest-snapshot': corsu.t('Latest snapshot', 'Dernière snapshot')}
    by_folder = {}
    for key, profile in profiles['profiles'].items():
        if not isinstance(profile, dict):
            continue
        folder = Path(profile['gameDir']) if isinstance(profile.get('gameDir'), str) and profile['gameDir'] else root
        version, loader = version_details(root, profile.get('lastVersionId'))
        by_folder.setdefault(folder, []).append({
            'name': profile.get('name') or names.get(profile.get('type')) or key, 'id': profile.get('lastVersionId'),
            'version': version, 'loader': loader, 'used': str(profile.get('lastUsed') or '')})
    found = []
    for folder, entries in by_folder.items():
        if not folder.is_dir():
            continue
        # Sorted is stable: among profiles used at the same time, the first listed wins, as before.
        entries = sorted(entries, key=lambda entry: entry['used'], reverse=True)
        found.append(Folder(folder, launcher, entries[0]['version'], loader=entries[0]['loader'], profiles=entries))
    return found or [Folder(root, launcher)]


def find_folders():
    """Every Minecraft game folder on this computer, with its version when it can be known."""
    found = []
    for root in official_roots():
        if root.is_dir():
            found += official_folders(root)
    for root, launcher in launcher_roots():
        if not root.is_dir():
            continue
        for instance in sorted(root.iterdir()):
            if not instance.is_dir() or not ((instance / 'instance.cfg').exists() or (instance / 'mmc-pack.json').exists()):
                continue
            folder = instance_game_folder(instance)
            if folder.is_dir():
                version, loader = instance_details(instance)
                found.append(Folder(folder, launcher, version, loader=loader))
    unique = {}
    for folder in found:
        unique.setdefault(folder.path.resolve(), folder)
    return list(unique.values())


def game_directories():
    return [folder.path for folder in find_folders()]


GAME_CLASSES = ('net.minecraft.client.main.Main', 'org.prismlauncher.EntryPoint', 'org.multimc.EntryPoint')


def running_folders():
    """Game folders of running Minecraft clients, or None when Minecraft runs and its folder cannot be told
    (every folder then counts as in use). An empty set when no game runs."""
    commands = []
    if corsu.PLATFORM == 'linux':
        for process in Path('/proc').iterdir():
            if not process.name.isdigit():
                continue
            try:
                arguments = (process / 'cmdline').read_bytes().decode('utf-8', 'replace').split('\0')
                cwd = os.readlink(process / 'cwd')
            except OSError:
                continue
            commands.append((arguments, cwd))
    else:
        import subprocess
        command = (['powershell', '-NoProfile', '-Command',
                    "Get-CimInstance Win32_Process -Filter \"Name like 'java%'\" | ForEach-Object { $_.CommandLine }"]
                   if corsu.PLATFORM == 'windows' else ['ps', '-axww', '-o', 'command='])
        try:
            output = subprocess.run(command, **corsu.hidden(capture_output=True, text=True, timeout=20)).stdout
        except (OSError, subprocess.SubprocessError):
            return set()
        # Command lines are flat text here: a path with spaces cannot be cut out reliably, so a running game counts
        # for every folder.
        running = any('java' in line.lower() and any(name in line for name in GAME_CLASSES)
                      for line in output.splitlines())
        return None if running else set()
    folders = set()
    for arguments, cwd in commands:
        program = Path(arguments[0]).name.lower() if arguments and arguments[0] else ''
        # A Java process with the game's main class; a shell whose command line merely mentions it does not count.
        if not program.startswith('java') or not any(name in arguments for name in GAME_CLASSES):
            continue
        if '--gameDir' in arguments and arguments.index('--gameDir') + 1 < len(arguments):
            folders.add(Path(arguments[arguments.index('--gameDir') + 1]).resolve())
        elif cwd:
            folders.add(Path(cwd).resolve())
        else:
            return None
    return folders


def in_use(path, running):
    return running is None or Path(path).resolve() in running


def read_options(path):
    """options.txt as (lines, newline). Raises ValueError when the file is not text Corsu can safely rewrite."""
    if not path.exists():
        return [], '\n'
    data = path.read_bytes()
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('not UTF-8') from None
    newline = '\r\n' if '\r\n' in text else '\n'
    lines = []
    for line in text.splitlines():
        key, colon, value = line.partition(':')
        lines.append((key, value) if colon else (line, None))
    return lines, newline


def write_options(lines, newline='\n'):
    return ''.join((f'{key}:{value}' if value is not None else key) + newline for key, value in lines)


def packs(value):
    """A pack list as Minecraft writes it. Raises ValueError for anything else: Corsu never rewrites what it cannot
    read, or another pack could be lost."""
    result = json.loads(value)
    if not isinstance(result, list) or not all(isinstance(name, str) for name in result):
        raise ValueError('not a list of packs')
    return result


def ours(name):
    # Minecraft also accepts the file name without "file/".
    return name in (PACK_ID, PACK)


def corsican(language):
    """Corsu's language in any game version: co_fr, or co_FR as versions up to 1.10.2 write it."""
    return isinstance(language, str) and language.lower() == LANGUAGE


def switch_on(lines, language=LANGUAGE):
    """Corsican as the language (in the case the game version writes it) and Corsu's pack active. Other packs keep
    their order; Corsu's pack is added once, last (so it wins for its texts), or left where it already was."""
    values = {key: value for key, value in lines if value is not None}
    original = {'lang': values.get('lang')}
    changes = {'lang': language}
    for option, default in DEFAULT_LISTS.items():
        current = packs(values[option]) if option in values else list(default)
        had = any(ours(name) for name in current)
        original[option] = {'present': option in values, 'had_pack': had}
        if option == 'incompatibleResourcePacks':
            # Corsu only switches folders of the pack's own version, where it is compatible.
            if had:
                changes[option] = json.dumps([name for name in current if not ours(name)], separators=(',', ':'))
            continue
        if not had:
            current.append(PACK_ID)
        changes[option] = json.dumps(current, separators=(',', ':'))
    result, seen = [], set()
    for key, value in lines:
        if value is not None and key in changes and key not in seen:
            result.append((key, changes[key]))
            seen.add(key)
        else:
            result.append((key, value))
    result += [(key, value) for key, value in changes.items() if key not in seen]
    return result, original


def switch_off(lines, original):
    """Undo only what Corsu set. The language goes back only while it is still Corsican, so a language chosen since
    stays; Corsu's pack leaves the lists only if Corsu added it; every other pack and setting stays as it is now.
    `original` is what switch_on returned, as recorded by any Corsu version (0.22.0 included)."""
    result = []
    for key, value in lines:
        if value is not None and key == 'lang' and corsican(value) and not corsican(original.get('lang')):
            if original.get('lang') is None:
                continue
            value = original['lang']
        elif value is not None and key in DEFAULT_LISTS and not original.get(key, {}).get('had_pack'):
            try:
                remaining = [name for name in packs(value) if not ours(name)]
            except ValueError:
                result.append((key, value))
                continue
            if not original.get(key, {}).get('present') and remaining == DEFAULT_LISTS[key]:
                continue
            value = json.dumps(remaining, separators=(',', ':'))
        result.append((key, value))
    return result


def atomic_write(path, data):
    temp = path.with_name(path.name + '.corsu-tmp')
    temp.write_bytes(data)
    temp.replace(path)


def install_folder(installer, folder, data, language=LANGUAGE, version=None):
    """Copy the pack and switch one game folder. Returns None when done, else why it was left alone.
    The pack file is replaced (another game version's pack, say) only while it is the file Corsu wrote."""
    target_path = folder / 'resourcepacks' / PACK
    key = str(target_path)
    record = installer.state['files'].get(key)
    if target_path.exists():
        current = target_path.read_bytes()
        if record and corsu.digest(current) != record['installed_sha256']:
            return corsu.t('the Corsu pack there was changed since; left alone',
                           'le pack Corsu a été modifié depuis ; laissé tel quel')
        if not record and current != data:
            return corsu.t(f'a different {PACK} is already there (installed by hand?); left alone',
                           f'un autre {PACK} s\'y trouve déjà (installé à la main ?) ; laissé tel quel')
    options = folder / 'options.txt'
    try:
        lines, newline = read_options(options)
        new_lines, original = switch_on(lines, language)
    except ValueError:
        return corsu.t('options.txt could not be read safely (not UTF-8 or a malformed pack list); not changed',
                       'options.txt illisible sans risque (pas en UTF-8 ou liste de packs malformée) ; non modifié')
    # The pack goes in first; an identical file found there is recorded with a backup, so uninstalling puts it back.
    installer.write(target_path, data)
    installer.state['files'][key]['component'] = 'minecraft'
    previous = installer.state['files'].get(str(options))
    if previous and previous.get('options_original') is not None:
        original = previous['options_original']
    # Recorded before writing: an interrupted run can still be undone.
    installer.state['files'][str(options)] = {
        'backup': None, 'mode': None, 'toggle': True, 'component': 'minecraft', 'options_original': original,
        'installed_sha256': corsu.digest(options.read_bytes()) if options.exists() else corsu.digest(b''),
        'language': language, 'version': version,
    }
    corsu.save_state(installer.state)
    content = write_options(new_lines, newline).encode('utf-8')
    options.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(options, content)
    installer.state['files'][str(options)]['installed_sha256'] = corsu.digest(content)
    corsu.save_state(installer.state)
    return None


def switch_folder_off(installer, folder):
    """A folder Corsu switched earlier now plays a version without a pack: take Corsu's pack off the active packs
    and put the language back if it is still Corsu's, so no incompatible pack stays selected unnoticed. The pack file
    stays in resourcepacks/ (inactive, removed on uninstall). Returns what was done, or None when Corsu had not
    switched this folder; raises ValueError when options.txt cannot be read safely."""
    options = folder / 'options.txt'
    record = installer.state['files'].get(str(options))
    if not record or record.get('options_original') is None:
        return None
    if options.exists():
        lines, newline = read_options(options)
        atomic_write(options, write_options(switch_off(lines, record['options_original']), newline).encode('utf-8'))
    installer.state['files'].pop(str(options))
    corsu.save_state(installer.state)
    return corsu.t('Corsu\'s pack was taken off the active packs and the language put back',
                   'le pack de Corsu a été retiré des packs actifs et la langue remise')


def coverage_of(counts):
    from apps import coverage_record
    if isinstance(counts, dict) and isinstance(counts.get('translated'), int) and isinstance(counts.get('total'), int):
        return coverage_record(f"{counts['translated']}/{counts['total']}")
    return coverage_record(None)


def shared_note(folder):
    """For an official launcher folder used by profiles of different game versions: what the others will see."""
    chosen = target(folder.version)
    notes, overlays = [], True
    for profile in folder.profiles[1:]:
        if profile['version'] == folder.version:
            continue
        other = target(profile['version'])
        if chosen and other and other.get('pack_format') == chosen.get('pack_format') \
                and other.get('language_code') == chosen.get('language_code'):
            continue
        key = version_key(profile['version'])
        overlays = overlays and key is not None and key >= (1, 20, 2)
        notes.append(corsu.t(f'profile "{profile["name"]}" ({profile["version"] or "version unknown"}) will show it as incompatible',
                             f'le profil « {profile["name"]} » ({profile["version"] or "version inconnue"}) le montrera comme incompatible'))
    if not notes:
        return None
    note = corsu.t(f'shared folder: pack built for {folder.version}; ', f'dossier partagé : pack fait pour {folder.version} ; ') \
        + '; '.join(notes)
    if overlays and version_key(folder.version) and version_key(folder.version) >= (1, 20, 2):
        note += corsu.t(' (one pack for all of them, with overlays, is a possible later improvement)',
                        ' (un seul pack pour toutes, avec des overlays, est une amélioration possible plus tard)')
    return note


def install(installer):
    """Switch every game folder playing a version Corsu has a pack for to Corsican, with that version's pack. Folders
    playing another version, whose version is unknown, or where Minecraft is running are left alone and listed; a
    folder Corsu switched before and now playing a version without a pack is switched off.

    Returns {'installed', 'skipped'} (the earlier report's lists) and 'result', the status in the shape of
    apps.install's (state['results'][...]): {activation, operation, time, instances, coverage}, each instance
    {kind, location, version, loader, activation, reason, action, coverage, note}."""
    from apps import aggregate, total_coverage
    running = running_folders()
    built, done, skipped, instances, languages = {}, [], [], [], set()
    for folder in find_folders():
        entry = target(folder.version)
        instance = {'kind': folder.launcher, 'location': str(folder.path), 'version': folder.version,
                    'loader': folder.loader, 'activation': 'blocked', 'reason': None, 'action': None,
                    'coverage': coverage_of(entry and entry.get('coverage')), 'note': None}
        if folder.version is None:
            reason = folder.note or corsu.t('the game version could not be told; left alone',
                                            'la version du jeu est inconnue ; laissé tel quel')
        elif in_use(folder.path, running):
            reason = corsu.t('Minecraft is running there; close it and run Corsu again',
                             'Minecraft y est lancé ; fermez-le et relancez Corsu')
            instance['action'] = corsu.t('Close Minecraft and run Corsu again', 'Fermez Minecraft et relancez Corsu')
        elif entry is None:
            note = (_packs().target(folder.version) or {}).get('note')
            reason = corsu.t(f'plays {folder.version}; Corsu has a pack for {supported_text()}',
                             f'joue {folder.version} ; Corsu a un pack pour {supported_text()}')
            if note:
                reason += f' ({note})'
            try:
                switched = switch_folder_off(installer, folder.path)
            except ValueError:
                switched = corsu.t('Corsu had switched it on, but options.txt cannot be read safely now; not changed',
                                   'Corsu l\'avait activé, mais options.txt est illisible sans risque ; non modifié')
            except OSError as error:
                switched = corsu.t(f'could not switch it off ({error.strerror or error})',
                                   f'désactivation impossible ({error.strerror or error})')
            if switched:
                reason += '; ' + switched
        else:
            try:
                if folder.version not in built:
                    built[folder.version] = _packs().build_pack(folder.version)
                data, counts = built[folder.version]
                instance['coverage'] = coverage_of(counts)
                reason = install_folder(installer, folder.path, data, entry['language_code'], folder.version)
                if reason is None:
                    instance['activation'] = 'active'
                    languages.add(entry['language_code'])
            except RuntimeError as error:
                reason = str(error)
            except OSError as error:
                reason = corsu.t(f'could not write ({error.strerror or error})',
                                 f'écriture impossible ({error.strerror or error})')
                instance['activation'] = 'failed'
            except (ValueError, KeyError, TypeError) as error:
                reason = corsu.t(f'the pack for {folder.version} could not be built ({error})',
                                 f'le pack pour {folder.version} n\'a pas pu être fait ({error})')
                instance['activation'] = 'failed'
        if folder.profiles:
            instance['note'] = shared_note(folder)
        instance['reason'] = reason
        instances.append(instance)
        line = {'folder': str(folder.path), 'version': folder.version, 'loader': folder.loader,
                'coverage': instance['coverage']}
        if reason:
            skipped.append({**line, 'reason': reason})
            print(corsu.t(f'Minecraft, left alone: {folder.describe()}: {reason}',
                          f'Minecraft, laissé tel quel : {folder.describe()} : {reason}'))
        else:
            done.append(line)
            coverage = instance['coverage']
            counts = f" ({coverage['translated']}/{coverage['total']})" if coverage['total'] else ''
            print(corsu.t(f'Minecraft in Corsican: {folder.describe()}{counts}',
                          f'Minecraft en corse : {folder.describe()}{counts}'))
        if instance['note']:
            print(f'  {instance["note"]}')
    result = {'activation': aggregate(instances), 'operation': 'install', 'time': __import__('time').time(),
              'instances': instances, 'coverage': total_coverage(instances)}
    return {'installed': done, 'skipped': skipped, 'pack': PACK, 'language': LANGUAGE,
            'languages': sorted(languages), 'result': result}


def revert(path, record):
    """Switch one options.txt back: Corsu's settings only, whatever else Minecraft or the player wrote meanwhile.
    False when it cannot be done now (the game is running, or the file cannot be read), so the record is kept."""
    path = Path(path)
    if not path.exists():
        return True
    if in_use(path.parent, running_folders()):
        print(corsu.t(f'Minecraft is running in {path.parent}: close it, then switch Minecraft off again.',
                      f'Minecraft est lancé dans {path.parent} : fermez-le, puis désactivez Minecraft à nouveau.'))
        return False
    try:
        lines, newline = read_options(path)
    except ValueError:
        print(corsu.t(f'Left alone because it cannot be read safely: {path}',
                      f'Laissé tel quel car illisible sans risque : {path}'))
        return False
    atomic_write(path, write_options(switch_off(lines, record.get('options_original', {})), newline).encode('utf-8'))
    return True
