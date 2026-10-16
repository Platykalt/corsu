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


def launcher_roots():
    """Folders of launchers that keep several game folders (instances)."""
    home = corsu.HOME
    if corsu.PLATFORM == 'windows':
        appdata = Path(os.environ.get('APPDATA', home / 'AppData/Roaming'))
        return [appdata / 'PrismLauncher/instances', appdata / 'MultiMC/instances']
    if corsu.PLATFORM == 'macos':
        support = home / 'Library/Application Support'
        return [support / 'PrismLauncher/instances', support / 'MultiMC/instances']
    data = Path(os.environ.get('XDG_DATA_HOME', home / '.local/share'))
    return [data / 'PrismLauncher/instances', data / 'multimc/instances',
            home / '.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances']


def game_directories():
    """Every Minecraft game folder on this computer: the one with options.txt, saves/ and resourcepacks/."""
    home = corsu.HOME
    if corsu.PLATFORM == 'windows':
        found = [Path(os.environ.get('APPDATA', home / 'AppData/Roaming')) / '.minecraft']
    elif corsu.PLATFORM == 'macos':
        found = [home / 'Library/Application Support/minecraft']
    else:
        found = [home / '.minecraft', home / '.var/app/com.mojang.Minecraft/.minecraft']
    for root in launcher_roots():
        if root.is_dir():
            for instance in sorted(root.iterdir()):
                # Prism Launcher plays in minecraft/, or in .minecraft/ only when minecraft/ does not exist.
                found.append(instance / 'minecraft' if (instance / 'minecraft').is_dir() else instance / '.minecraft')
    return [folder for folder in found if folder.is_dir()]


def read_options(path):
    """options.txt as ordered (key, value) lines; lines without a colon are kept as they are."""
    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        key, colon, value = line.partition(':')
        lines.append((key, value) if colon else (line, None))
    return lines


def write_options(lines):
    return ''.join(f'{key}:{value}\n' if value is not None else f'{key}\n' for key, value in lines)


def packs(value):
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (TypeError, ValueError):
        return []


def switch_on(lines):
    """Corsican as the language, and Corsu's pack active (last, so it wins over other packs for its texts)."""
    values = dict((key, value) for key, value in lines if value is not None)
    changes = {'lang': LANGUAGE}
    for option in LIST_OPTIONS:
        current = packs(values.get(option)) if option in values else (['vanilla'] if option == 'resourcePacks' else [])
        # Written like Minecraft writes it: no spaces.
        changes[option] = json.dumps([name for name in current if name != PACK_ID] + [PACK_ID],
                                     separators=(',', ':'))
    result, seen = [], set()
    for key, value in lines:
        if value is not None and key in changes:
            result.append((key, changes[key]))
            seen.add(key)
        else:
            result.append((key, value))
    result += [(key, value) for key, value in changes.items() if key not in seen]
    return result, {key: values.get(key) for key in changes}


def switch_off(lines, original):
    """Undo only what Corsu set: the language if it is still Corsican, and Corsu's pack in the lists."""
    result = []
    for key, value in lines:
        if value is not None and key == 'lang' and value == LANGUAGE:
            if original.get('lang') is None:
                continue
            value = original['lang']
        elif value is not None and key in LIST_OPTIONS:
            remaining = [name for name in packs(value) if name != PACK_ID]
            if original.get(key) is None and remaining in ([], ['vanilla']):
                continue
            value = json.dumps(remaining, separators=(',', ':'))
        result.append((key, value))
    return result


def install(installer):
    """Copy the pack and switch each game folder to Corsican. Returns what was done, for the report."""
    data = pack_from_sources()
    folders = game_directories()
    for folder in folders:
        target = folder / 'resourcepacks' / PACK
        record = installer.state['files'].get(str(target))
        if record and target.exists() and corsu.digest(target.read_bytes()) != record['installed_sha256']:
            # A pack of the same name that someone changed: leave it, as for every other file.
            print(corsu.t(f'Left alone because you changed it: {target}',
                          f'Laissé tel quel car vous l\'avez modifié : {target}'))
            continue
        installer.write(target, data)
        installer.state['files'][str(target)]['component'] = 'minecraft'
        options = folder / 'options.txt'
        lines, original = switch_on(read_options(options))
        key = str(options)
        previous = installer.state['files'].get(key)
        if previous:
            # Minecraft rewrites options.txt; only the settings Corsu set are tracked, never the whole file.
            original = previous.get('options_original', original)
            if options.exists():
                previous['installed_sha256'] = corsu.digest(options.read_bytes())
        installer.write(options, write_options(lines), toggle=True)
        installer.state['files'][key].update(component='minecraft', options_original=original)
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    if folders:
        print(corsu.t('Minecraft: close it before this change and start it again afterwards; the language is Corsu.',
                      'Minecraft : fermez-le avant ce changement et relancez-le ensuite ; la langue est Corsu.'))
    return {'folders': [str(folder) for folder in folders], 'pack': PACK, 'language': LANGUAGE}


def revert(path, record):
    """Switch one options.txt back: Corsu's settings only, whatever else Minecraft wrote meanwhile."""
    if path.exists():
        path.write_text(write_options(switch_off(read_options(path), record.get('options_original', {}))),
                        encoding='utf-8')
