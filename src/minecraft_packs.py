"""Corsican for any Minecraft: Java Edition release from 1.6.1: one resource pack per game version, built offline.

The translation is kept once, for the newest release (minecraft/java/co_fr.json, the base). Each release's pack is
made from committed data only, never from Mojang's files (minecraft/java/MULTIVERSION.md):

- keys.tsv: every (key, hash of the English text) of every handled release and the releases showing it;
- versions.json: per release, the language file format and name, the language code, the pack format and the style
  of pack.mcmeta, and whether the pack is supported (built and checked);
- history.json (optional): Corsican for (key, hash) pairs that differ from the base.

For a key k whose English has hash h in release V: history[k][h] when present, else the base translation when the
base release's English for k has the same hash, else nothing (the game shows its English for that key).
"""
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib

SOURCE = Path(__file__).resolve().parent.parent / 'minecraft/java'
NAME, REGION = 'Corsu', 'Corsica'
DATE = (2026, 1, 1, 0, 0, 0)


def digest(text):
    """The hash keys.tsv keeps for an English text: first 12 hex digits of SHA-1 of its UTF-8 bytes."""
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def png(size=64):
    """pack.png: the white field and black band colours of the Corsican flag (same image as src/minecraft.py)."""
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


def parse_versions(field, order):
    """keys.tsv's versions column: comma-separated items, each a release id or "first..last", a run of consecutive
    releases in versions.json order. Returns the set of positions in `order`."""
    position = {version: index for index, version in enumerate(order)}
    found = set()
    for item in field.split(','):
        item = item.strip()
        if not item:
            continue
        first, dots, last = item.partition('..')
        if first not in position or (dots and last not in position):
            raise ValueError(f'keys.tsv: unknown release in {item!r}')
        found.update(range(position[first], position[last if dots else first] + 1))
    return found


def compact_versions(positions, order):
    """The inverse of parse_versions: runs of 3 or more consecutive releases become "first..last"."""
    items, run = [], []
    for index in sorted(positions) + [None]:
        if run and (index is None or index != run[-1] + 1):
            items.append(f'{order[run[0]]}..{order[run[-1]]}' if len(run) > 2 else ','.join(order[i] for i in run))
            run = []
        if index is not None:
            run.append(index)
    return ','.join(items)


class Data:
    """The committed data of one folder (minecraft/java by default; tests use small fixtures)."""

    def __init__(self, folder=SOURCE):
        self.folder = Path(folder)
        self._loaded = False

    def load(self):
        if self._loaded:
            return self
        folder = self.folder
        self.versions = json.loads((folder / 'versions.json').read_text(encoding='utf-8'))
        self.order = list(self.versions)
        self.base = (folder / 'VERSION').read_text(encoding='utf-8').strip() if (folder / 'VERSION').exists() else self.order[-1]
        self.translation = json.loads((folder / 'co_fr.json').read_text(encoding='utf-8'))
        history = folder / 'history.json'
        self.history = json.loads(history.read_text(encoding='utf-8') or '{}') if history.exists() else {}
        self.license = (folder / 'LICENSE.txt').read_bytes()
        base_position = self.order.index(self.base)
        self.rows, self.base_hash = [], {}
        lines = (folder / 'keys.tsv').read_text(encoding='utf-8').splitlines()
        if not lines or lines[0].split('\t') != ['key', 'hash', 'versions']:
            raise ValueError('keys.tsv: header must be key, hash, versions')
        for line in lines[1:]:
            if not line or line.startswith('#'):
                continue
            key, sha, field = line.split('\t')
            positions = frozenset(parse_versions(field, self.order))
            self.rows.append((key, sha, positions))
            if base_position in positions:
                self.base_hash[key] = sha
        self._loaded = True
        return self

    def pairs(self, version):
        """(key, hash) of every text of a release, in key order."""
        position = self.order.index(version)
        return sorted((key, sha) for key, sha, positions in self.rows if position in positions)

    def resolve(self, key, sha):
        """The Corsican for one (key, English hash) pair, or None."""
        entry = self.history.get(key, {}).get(sha)
        if isinstance(entry, dict) and isinstance(entry.get('co'), str):
            return entry['co']
        if self.base_hash.get(key) == sha and isinstance(self.translation.get(key), str):
            return self.translation[key]
        return None


DEFAULT = Data()


def known(data=None):
    return (data or DEFAULT).load().order


def target(version, data=None):
    """The versions.json entry of a release when Corsu supports it (its pack is built and checked), else None.
    Accepts the ids launchers show (see base_version)."""
    data = (data or DEFAULT).load()
    release = base_version(version, data)
    entry = data.versions.get(release) if release else None
    if not entry or not entry.get('supported'):
        return None
    return dict(entry, version=release)


# A snapshot (24w14a), or a pre-release / release candidate / snapshot of a release (1.21-pre1, 1.20.2-rc1,
# 26.1-snapshot-1, "1.14 Pre-Release 2"): never a release.
SNAPSHOT = re.compile(r'(?<![\w.])\d\dw\d\d[a-z~]', re.I)
DEVELOPMENT = re.compile(r'^[\s_-]*(pre|rc|snapshot|release[\s_-]*candidate|pre[\s_-]*release)', re.I)
NUMBER = re.compile(r'(?<![\d.])\d+(?:\.\d+)+(?![\d.])')


def base_version(text, data=None):
    """The release a launcher's version id plays, or None: "1.21.1", "fabric-loader-0.16.9-1.21.1",
    "1.20.1-forge-47.2.0", "quilt-loader-0.26.0-1.20.1", "1.12.2-OptiFine_HD_U_G5", "neoforge-21.1.77" (NeoForge
    numbers 21.1.x for 1.21.1). Snapshots, pre-releases and release candidates give None, as do ids naming two
    different releases."""
    if not isinstance(text, str) or not text.strip():
        return None
    data = (data or DEFAULT).load()
    text = text.strip()
    if text in data.versions:
        return text
    if SNAPSHOT.search(text):
        return None
    found = set()
    for match in NUMBER.finditer(text):
        if DEVELOPMENT.match(text[match.end():]):
            return None
        if match.group(0) in data.versions:
            found.add(match.group(0))
    if not found and 'neoforge' in text.lower():
        for match in NUMBER.finditer(text):
            parts = match.group(0).split('.')
            if len(parts) >= 3 and parts[0].isdigit() and 20 <= int(parts[0]) < 26:
                release = f'1.{parts[0]}' + (f'.{parts[1]}' if parts[1] != '0' else '')
                if release in data.versions:
                    found.add(release)
    return found.pop() if len(found) == 1 else None


def mcmeta(entry, version):
    """pack.mcmeta for one release, in the style that release reads (versions.json `mcmeta`)."""
    style, number = entry['mcmeta'], entry['pack_format']
    pack = {'description': f'Lingua corsa · {NAME}, Minecraft {version} · NOT AN OFFICIAL MINECRAFT PRODUCT'}
    if style == 'min_max':
        pack.update(min_format=number, max_format=number)
    elif style == 'supported_formats':
        pack.update(pack_format=number, supported_formats=[number, number])
    elif style == 'pack_format':
        pack.update(pack_format=number)
    else:
        raise ValueError(f'{version}: unknown pack.mcmeta style {style!r}')
    meta = {'pack': pack, 'language': {entry['language_code']: {'name': NAME, 'region': REGION, 'bidirectional': False}}}
    # ASCII only (\u escapes, as in Mojang's own pack.mcmeta of 1.6): Gson reads them the same whatever charset a game
    # version opens the file with.
    return (json.dumps(meta, ensure_ascii=True, indent=2) + '\n').encode('utf-8')


def lang_bytes(texts, lang_format):
    """The language file: JSON (1.13 and later) or key=value lines (.lang, up to 1.12.2), UTF-8 without BOM."""
    if lang_format == 'json':
        return (json.dumps(texts, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    lines = []
    for key, value in texts.items():
        if '=' in key or not key or key.startswith('#') or any(c in key + value for c in '\r\n'):
            raise ValueError(f'{key}: cannot be written to a .lang file (=, # or a line break)')
        lines.append(f'{key}={value}\n')
    return ''.join(lines).encode('utf-8')


def zip_bytes(files):
    """Fixed dates and order: the same sources always give the same file (as src/minecraft.make_pack)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, payload in files:
            info = zipfile.ZipInfo(name, DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, payload)
    return buffer.getvalue()


def texts_for(version, data=None):
    """The Corsican texts of one release, by key, and the number of keys that release has."""
    data = (data or DEFAULT).load()
    if version not in data.versions:
        raise ValueError(f'unknown Minecraft release {version!r}')
    pairs = data.pairs(version)
    texts = {}
    for key, sha in pairs:
        text = data.resolve(key, sha)
        if text is not None:
            texts[key] = text
    return texts, len(pairs)


def build_pack(version, data=None):
    """The resource pack of one release as bytes, and a report: translated, total, missing (keys left in English)."""
    data = (data or DEFAULT).load()
    release = base_version(version, data)
    if release is None:
        raise ValueError(f'unknown Minecraft release {version!r}')
    entry = data.versions[release]
    texts, total = texts_for(release, data)
    payload = zip_bytes([
        ('pack.mcmeta', mcmeta(entry, release)),
        ('pack.png', png()),
        (entry['lang_file'], lang_bytes(texts, entry['lang_format'])),
        ('LICENSE.txt', data.license),
    ])
    report = {'version': release, 'translated': len(texts), 'total': total, 'missing': total - len(texts),
              'lang_file': entry['lang_file'], 'language_code': entry['language_code'],
              'pack_format': entry['pack_format'], 'supported': bool(entry.get('supported'))}
    return payload, report


def supported_versions(data=None):
    """Release ids whose pack is supported (versions.json `supported`), newest first."""
    data = (data or DEFAULT).load()
    return [version for version in reversed(data.order) if data.versions[version].get('supported')]
