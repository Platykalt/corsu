"""Minecraft: Java Edition in Corsican: the resource pack, and Corsican as the game's language.

Corsu copies its pack into every Minecraft game folder it finds (the official launcher's, and the instances of
Prism Launcher and MultiMC), adds it to the active resource packs and sets the language to Corsican in options.txt.
Only those settings are recorded and reverted: Minecraft rewrites options.txt itself, so the rest of the file is
never put back. Minecraft must be closed, because it writes options.txt again when it quits.
"""
import io
import json
import os
from pathlib import Path
import struct
import zipfile
import zlib

import corsu

SOURCE = corsu.ROOT / 'minecraft/java'
PACK = 'corsu-minecraft-java.zip'
PACK_ID = 'file/' + PACK
LANGUAGE = 'co_fr'
# Older and newer game versions show the pack as "made for an older/newer version"; listing it here as well keeps
# it active instead of asking again.
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


SUPPORTED = {(SOURCE / 'VERSION').read_text(encoding='utf-8').strip()} if (SOURCE / 'VERSION').exists() else set()
DEFAULT_LISTS = {'resourcePacks': ['vanilla'], 'incompatibleResourcePacks': []}


class Folder:
    """One Minecraft game folder, the version it plays when Corsu can tell, and why it is skipped if it is."""

    def __init__(self, path, launcher, version=None, note=''):
        self.path, self.launcher, self.version, self.note = Path(path), launcher, version, note

    @property
    def compatible(self):
        return self.version in SUPPORTED

    def describe(self):
        version = self.version or corsu.t('version unknown', 'version inconnue')
        return f'{self.path} ({self.launcher}, {version})'


def launcher_roots():
    """Folders of launchers that keep several game folders (instances), with the launcher's name."""
    home = corsu.HOME
    if corsu.PLATFORM == 'windows':
        appdata = Path(os.environ.get('APPDATA', home / 'AppData/Roaming'))
        return [(appdata / 'PrismLauncher/instances', 'Prism Launcher'), (appdata / 'MultiMC/instances', 'MultiMC')]
    if corsu.PLATFORM == 'macos':
        support = home / 'Library/Application Support'
        return [(support / 'PrismLauncher/instances', 'Prism Launcher'), (support / 'MultiMC/instances', 'MultiMC')]
    data = Path(os.environ.get('XDG_DATA_HOME', home / '.local/share'))
    return [(data / 'PrismLauncher/instances', 'Prism Launcher'), (data / 'multimc/instances', 'MultiMC'),
            (home / '.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances', 'Prism Launcher')]


def official_roots():
    home = corsu.HOME
    if corsu.PLATFORM == 'windows':
        return [Path(os.environ.get('APPDATA', home / 'AppData/Roaming')) / '.minecraft']
    if corsu.PLATFORM == 'macos':
        return [home / 'Library/Application Support/minecraft']
    return [home / '.minecraft', home / '.var/app/com.mojang.Minecraft/.minecraft']


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def instance_version(instance):
    """The Minecraft version of a Prism Launcher or MultiMC instance: mmc-pack.json, or instance.cfg for old ones."""
    pack = read_json(instance / 'mmc-pack.json')
    if isinstance(pack, dict):
        for component in pack.get('components', []):
            if isinstance(component, dict) and component.get('uid') == 'net.minecraft':
                return component.get('version')
    try:
        for line in (instance / 'instance.cfg').read_text(encoding='utf-8', errors='replace').splitlines():
            if line.startswith('IntendedVersion='):
                return line.partition('=')[2].strip() or None
    except OSError:
        pass
    return None


def resolve_version(root, version):
    """A launcher profile's version as a game version: latest-release / latest-snapshot are the newest of that type
    installed in versions/, and a modded version (Fabric, Forge…) is the version it inherits from."""
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
        return newest[1] if newest else None
    for _ in range(5):
        data = read_json(versions / version / f'{version}.json') if version else None
        if not isinstance(data, dict) or not data.get('inheritsFrom'):
            return version
        version = data['inheritsFrom']
    return None


def official_folders(root):
    """The official launcher's folder and the game folders its profiles point to. Several profiles may share a folder
    with different versions; the folder follows the profile used last, the one the launcher starts again."""
    profiles = read_json(root / 'launcher_profiles.json')
    if not isinstance(profiles, dict) or not isinstance(profiles.get('profiles'), dict):
        return [Folder(root, corsu.t('official launcher', 'lanceur officiel'), None,
                       corsu.t('no launcher profile to tell the version', 'aucun profil du lanceur pour connaître la version'))]
    last = {}
    for profile in profiles['profiles'].values():
        if not isinstance(profile, dict):
            continue
        folder = Path(profile['gameDir']) if profile.get('gameDir') else root
        used = str(profile.get('lastUsed') or '')
        if folder not in last or used > last[folder][0]:
            last[folder] = (used, profile.get('lastVersionId'))
    found = []
    for folder, (_, version) in last.items():
        if folder.is_dir():
            found.append(Folder(folder, corsu.t('official launcher', 'lanceur officiel'), resolve_version(root, version)))
    return found or [Folder(root, corsu.t('official launcher', 'lanceur officiel'))]


def find_folders():
    """Every Minecraft game folder on this computer, with its version when it can be known."""
    found = []
    for root in official_roots():
        if root.is_dir():
            found += official_folders(root)
    for root, launcher in launcher_roots():
        if root.is_dir():
            for instance in sorted(root.iterdir()):
                if not instance.is_dir():
                    continue
                # Prism Launcher plays in minecraft/, or in .minecraft/ only when minecraft/ does not exist.
                folder = instance / 'minecraft' if (instance / 'minecraft').is_dir() else instance / '.minecraft'
                if folder.is_dir():
                    found.append(Folder(folder, launcher, instance_version(instance)))
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
            output = subprocess.run(command, capture_output=True, text=True, timeout=20).stdout
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


def switch_on(lines):
    """Corsican as the language and Corsu's pack active. Other packs keep their order; Corsu's pack is added once,
    last (so it wins for its texts), or left where it already was."""
    values = {key: value for key, value in lines if value is not None}
    original = {'lang': values.get('lang')}
    changes = {'lang': LANGUAGE}
    for option, default in DEFAULT_LISTS.items():
        current = packs(values[option]) if option in values else list(default)
        had = any(ours(name) for name in current)
        original[option] = {'present': option in values, 'had_pack': had}
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
    stays; Corsu's pack leaves the lists only if Corsu added it; every other pack and setting stays as it is now."""
    result = []
    for key, value in lines:
        if value is not None and key == 'lang' and value == LANGUAGE and original.get('lang') != LANGUAGE:
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


def install_folder(installer, folder, data):
    """Copy the pack and switch one game folder. Returns None when done, else why it was left alone."""
    target = folder / 'resourcepacks' / PACK
    key = str(target)
    record = installer.state['files'].get(key)
    if target.exists():
        current = target.read_bytes()
        if record and corsu.digest(current) != record['installed_sha256']:
            return corsu.t('the Corsu pack there was changed since; left alone',
                           'le pack Corsu a été modifié depuis ; laissé tel quel')
        if not record and current != data:
            return corsu.t(f'a different {PACK} is already there (installed by hand?); left alone',
                           f'un autre {PACK} s\'y trouve déjà (installé à la main ?) ; laissé tel quel')
    options = folder / 'options.txt'
    try:
        lines, newline = read_options(options)
        new_lines, original = switch_on(lines)
    except ValueError:
        return corsu.t('options.txt could not be read safely (not UTF-8 or a malformed pack list); not changed',
                       'options.txt illisible sans risque (pas en UTF-8 ou liste de packs malformée) ; non modifié')
    # The pack goes in first; an identical file found there is recorded with a backup, so uninstalling puts it back.
    installer.write(target, data)
    installer.state['files'][key]['component'] = 'minecraft'
    previous = installer.state['files'].get(str(options))
    if previous and previous.get('options_original') is not None:
        original = previous['options_original']
    # Recorded before writing: an interrupted run can still be undone.
    installer.state['files'][str(options)] = {
        'backup': None, 'mode': None, 'toggle': True, 'component': 'minecraft', 'options_original': original,
        'installed_sha256': corsu.digest(options.read_bytes()) if options.exists() else corsu.digest(b''),
    }
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    content = write_options(new_lines, newline).encode('utf-8')
    options.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(options, content)
    installer.state['files'][str(options)]['installed_sha256'] = corsu.digest(content)
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    return None


def install(installer):
    """Switch every compatible game folder to Corsican. Folders playing another version, whose version is unknown,
    or where Minecraft is running are left alone and listed."""
    data = pack_from_sources()
    running = running_folders()
    done, skipped = [], []
    for folder in find_folders():
        if not folder.compatible:
            reason = folder.note or corsu.t(f'plays {folder.version or "an unknown version"}; the pack is for '
                                            + ', '.join(sorted(SUPPORTED)),
                                            f'joue {folder.version or "une version inconnue"} ; le pack est pour '
                                            + ', '.join(sorted(SUPPORTED)))
        elif in_use(folder.path, running):
            reason = corsu.t('Minecraft is running there; close it and run Corsu again',
                             'Minecraft y est lancé ; fermez-le et relancez Corsu')
        else:
            try:
                reason = install_folder(installer, folder.path, data)
            except OSError as error:
                reason = corsu.t(f'could not write ({error.strerror or error})',
                                 f'écriture impossible ({error.strerror or error})')
        if reason:
            skipped.append({'folder': str(folder.path), 'version': folder.version, 'reason': reason})
            print(corsu.t(f'Minecraft, left alone: {folder.describe()}: {reason}',
                          f'Minecraft, laissé tel quel : {folder.describe()} : {reason}'))
        else:
            done.append({'folder': str(folder.path), 'version': folder.version})
            print(corsu.t(f'Minecraft in Corsican: {folder.describe()}', f'Minecraft en corse : {folder.describe()}'))
    return {'installed': done, 'skipped': skipped, 'pack': PACK, 'language': LANGUAGE}


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
