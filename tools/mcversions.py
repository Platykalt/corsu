#!/usr/bin/env python3
"""Corsican for every Minecraft: Java Edition release from 1.6.1: formats, key index, packs and their checks.

    python3 tools/mcversions.py fetch [VERSION|all]    Mojang's English and format facts of releases (network)
    python3 tools/mcversions.py index                  rewrite minecraft/java/keys.tsv from the fetched English
    python3 tools/mcversions.py formats                rewrite minecraft/java/versions.json (and other-versions.md)
    python3 tools/mcversions.py build [VERSION|all]    write dist/corsu-minecraft-java-<VERSION>.zip
    python3 tools/mcversions.py verify [VERSION|all]   check each pack, with the game's own code where possible

The contract is minecraft/java/MULTIVERSION.md. Mojang's texts are never committed: `fetch` keeps them in
~/.cache/corsu/minecraft/<VERSION>/multiversion (or $CORSU_CACHE/minecraft/<VERSION>/multiversion). It reads only
the needed files of each client jar with HTTP range requests, so it cannot check the jar's SHA-1 (that needs the
whole file): it checks the version JSON's SHA-1 against Mojang's manifest, the asset index's and every asset's SHA-1,
and each file read from a jar against the CRC-32 the jar itself records; it records the jar's SHA-1 and size as the
version JSON gives them. `verify` downloads whole jars and checks their SHA-1 before running any of their code.
"""
import argparse
import collections
import concurrent.futures
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'minecraft/java'
sys.path.insert(0, str(ROOT / 'src'))
import minecraft_packs as packs  # noqa: E402

MANIFEST = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
RESOURCES = 'https://resources.download.minecraft.net/{}/{}'
FIRST = '1.6.1'   # the first release with resource packs (13w24a); before it a language needs another mechanism
BASE = (HERE / 'VERSION').read_text().strip() if (HERE / 'VERSION').exists() else '26.3'
KEYS = HERE / 'keys.tsv'
VERSIONS = HERE / 'versions.json'
OTHERS = HERE / 'other-versions.md'
JAVA = ROOT / 'tools/minecraft'

# Resource pack formats of the releases whose jar has no version.json (before 1.14). Source: minecraft.wiki,
# "Template:Resource pack format" (rows "releaseonly"), revision 3784632 of 2026-09-19, shown on the page
# "Pack format" (https://minecraft.wiki/w/Pack_format). From 1.14 the jar's own version.json gives it.
WIKI_PACK_FORMAT = [(1, '1.6.1', '1.8.9'), (2, '1.9', '1.10.2'), (3, '1.11', '1.12.2'), (4, '1.13', '1.14.4')]
WIKI_SOURCE = 'minecraft.wiki Template:Resource pack format rev 3784632 (2026-09-19)'
# pack.mcmeta history, minecraft.wiki "Pack.mcmeta" revision 3821904 (2026-10-05): supported_formats added in
# 1.20.2 (23w31a); min_format/max_format added and supported_formats refused for resource formats >= 65 in 1.21.9
# (25w31a). The jars agree: version.json's pack_version becomes {resource_major, resource_minor, ...} in 1.21.9.
SUPPORTED_FORMATS_FROM = '1.20.2'


# ---------------------------------------------------------------------------------------------------- downloads

def cache_base():
    return Path(os.environ.get('CORSU_CACHE', Path.home() / '.cache/corsu')) / 'minecraft'


def cache(version):
    """This tool's files for one release; tools/minecraft.py keeps its own next to it, in the parent folder."""
    return cache_base() / version / 'multiversion'


def download(url, sha1=None, headers=None, attempts=4):
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(request, timeout=300) as response:
                data = response.read()
            break
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(2 * (attempt + 1))
    if sha1 and hashlib.sha1(data).hexdigest() != sha1:
        raise SystemExit(f'checksum mismatch for {url}')
    return data


class RangeFile(io.RawIOBase):
    """A remote file read with HTTP range requests, enough for zipfile to read one member of a jar."""

    def __init__(self, url, size):
        self.url, self.size, self.pos = url, size, 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        return self.pos

    def readinto(self, buffer):
        if self.pos >= self.size:
            return 0
        end = min(self.pos + len(buffer), self.size) - 1
        data = download(self.url, headers={'Range': f'bytes={self.pos}-{end}'})
        if len(data) != end - self.pos + 1:
            raise OSError(f'{self.url}: the server ignored the range request')
        buffer[:len(data)] = data
        self.pos += len(data)
        return len(data)


def remote_zip(url, size):
    # zipfile checks each member's CRC-32 against the jar's own record as it reads it.
    return zipfile.ZipFile(io.BufferedReader(RangeFile(url, size), 1 << 16))


def manifest(refresh=False):
    path = cache_base() / 'manifest.json'
    if refresh or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(download(MANIFEST))
    return json.loads(path.read_text())


def split(versions, first=FIRST):
    """Releases from FIRST in release order, and the other entries (snapshots, pre-releases, old alphas…)."""
    ordered = sorted(versions, key=lambda v: v['releaseTime'])
    start = next(v['releaseTime'] for v in ordered if v['id'] == first)
    releases = [v for v in ordered if v['type'] == 'release' and v['releaseTime'] >= start]
    others = [v for v in ordered if v not in releases]
    return releases, others


def releases():
    return [v['id'] for v in split(manifest()['versions'])[0]]


def strict_json(data, name):
    def pairs(items):
        seen = {}
        for key, value in items:
            if key in seen:
                raise ValueError(f'{name}: duplicate key {key}')
            seen[key] = value
        return seen
    return json.loads(data.decode('utf-8'), object_pairs_hook=pairs)


def parse_lang(data):
    """A .lang file as the game reads it: UTF-8 lines, # comments, key=value split at the first '='."""
    texts = {}
    for line in data.decode('utf-8').splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, _, value = line.partition('=')
            texts[key] = value
    return texts


def parse_language(name, data):
    return strict_json(data, name) if name.endswith('.json') else parse_lang(data)


LANG = re.compile(r'assets/(minecraft|realms)/lang/en_us\.(json|lang)', re.I)


def fetch(version, refresh=False):
    """English (game and Realms), the jar's version.json and pack.mcmeta, Mojang's language list, provenance."""
    folder = cache(version)
    if (folder / 'fetch.json').exists() and not refresh:
        return folder
    folder.mkdir(parents=True, exist_ok=True)
    entry = next((v for v in manifest()['versions'] if v['id'] == version), None)
    if entry is None:
        raise SystemExit(f'unknown Minecraft version {version}')
    meta_bytes = download(entry['url'], entry['sha1'])
    meta = json.loads(meta_bytes)
    (folder / 'version.json').write_bytes(meta_bytes)
    record = {'id': version, 'type': entry['type'], 'releaseTime': entry['releaseTime'],
              'version_json_sha1': entry['sha1'], 'client_sha1': meta['downloads']['client']['sha1'],
              'client_size': meta['downloads']['client']['size'], 'asset_index': meta['assetIndex']['id'],
              'client_mappings': 'client_mappings' in meta['downloads'],
              'checked': 'version JSON SHA-1 (manifest), asset SHA-1s, CRC-32 of each jar member read; '
                         'the client jar SHA-1 is recorded, not checked (range requests read part of the jar)'}
    index = json.loads(download(meta['assetIndex']['url'], meta['assetIndex']['sha1']))['objects']
    if 'pack.mcmeta' in index:
        digest = index['pack.mcmeta']['hash']
        (folder / 'languages.mcmeta').write_bytes(download(RESOURCES.format(digest[:2], digest), digest))
    client = meta['downloads']['client']
    english, realms, sources = {}, {}, {}
    with remote_zip(client['url'], client['size']) as jar:
        names = jar.namelist()
        found = [n for n in names if LANG.fullmatch(n)]
        main = [n for n in found if n.startswith('assets/minecraft/')]
        if len(main) != 1:
            raise SystemExit(f'{version}: expected one English language file in the jar, found {main}')
        record['lang_file'] = main[0]
        english = parse_language(main[0], jar.read(main[0]))
        for name in found:
            if name.startswith('assets/realms/'):
                realms.update(parse_language(name, jar.read(name)))
                sources['realms'] = f'client jar {name}'
        for name, target in (('version.json', 'game-version.json'), ('pack.mcmeta', 'jar-pack.mcmeta')):
            if name in names:
                (folder / target).write_bytes(jar.read(name))
    for library in meta.get('libraries', []):
        if library.get('name', '').startswith('com.mojang:realms:'):
            artifact = library['downloads']['artifact']
            with remote_zip(artifact['url'], artifact['size']) as jar:
                for name in jar.namelist():
                    if LANG.fullmatch(name) and name.startswith('assets/realms/'):
                        realms.update(parse_language(name, jar.read(name)))
                        sources['realms'] = f'library {library["name"]} {name}'
    if 'realms/lang/en_us.json' in index:
        digest = index['realms/lang/en_us.json']['hash']
        realms.update(strict_json(download(RESOURCES.format(digest[:2], digest), digest), 'realms'))
        sources['realms'] = 'asset realms/lang/en_us.json'
    record['realms'] = sources.get('realms')
    record['keys'] = {'minecraft': len(english), 'realms': len(realms)}
    # The game merges every namespace's language file into one table; like tools/minecraft.py, Realms' file wins.
    english.update(realms)
    (folder / 'english.json').write_text(json.dumps(english, ensure_ascii=False, indent=0), encoding='utf-8')
    (folder / 'fetch.json').write_text(json.dumps(record, indent=1))
    print(f'{version}: {len(english)} keys ({record["lang_file"]}, Realms: {record["realms"]})')
    return folder


def english(version):
    return json.loads((fetch(version) / 'english.json').read_text(encoding='utf-8'))


def fetch_all(versions, refresh=False):
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        for _ in pool.map(lambda v: fetch(v, refresh), versions):
            pass



def client(version):
    """The whole client jar (SHA-1 checked) and the plain Java libraries it needs, in the folder tools/minecraft.py
    uses (~/.cache/corsu/minecraft/<VERSION>/client.jar and libraries/)."""
    folder = cache_base() / version
    meta = json.loads((fetch(version) / 'version.json').read_text())
    jar = folder / 'client.jar'
    expected = meta['downloads']['client']['sha1']
    if not jar.exists() or hashlib.sha1(jar.read_bytes()).hexdigest() != expected:
        jar.write_bytes(download(meta['downloads']['client']['url'], expected))
    classpath = [jar]
    libraries = folder / 'libraries'
    libraries.mkdir(exist_ok=True)
    for library in meta['libraries']:
        artifact = library.get('downloads', {}).get('artifact')
        # Plain Java libraries only: native builds (name:version:natives-…) are not needed to read and format text.
        if not artifact or library['name'].count(':') != 2 or library.get('natives'):
            continue
        target = libraries / Path(artifact['path']).name
        if not target.exists() or hashlib.sha1(target.read_bytes()).hexdigest() != artifact['sha1']:
            target.write_bytes(download(artifact['url'], artifact['sha1']))
        classpath.append(target)
    return classpath


# ---------------------------------------------------------------------------------------------------- index

def index():
    """keys.tsv: one row per (key, English hash), with the releases showing that exact text."""
    order = releases()
    rows = collections.defaultdict(set)
    for position, version in enumerate(order):
        for key, text in english(version).items():
            rows[(key, packs.digest(text))].add(position)
    lines = ['key\thash\tversions']
    for (key, sha), positions in sorted(rows.items(), key=lambda item: (item[0][0], min(item[1]), item[0][1])):
        if any(c in key for c in '\t\r\n'):
            raise SystemExit(f'key {key!r} cannot be written to keys.tsv')
        lines.append(f'{key}\t{sha}\t{packs.compact_versions(positions, order)}')
    KEYS.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{KEYS}: {len(rows)} (key, hash) pairs over {len(order)} releases')


# ---------------------------------------------------------------------------------------------------- formats

def facts(version, order):
    """The format facts of one release, each from the jar or Mojang's files when they carry it."""
    folder = fetch(version)
    record = json.loads((folder / 'fetch.json').read_text())
    jar_lang = record['lang_file'].rsplit('/', 1)[1]          # en_US.lang, en_us.lang or en_us.json
    stem, extension = jar_lang.split('.')
    upper = stem == 'en_US'
    code = 'co_FR' if upper else 'co_fr'
    sources = {'lang_file': f'client jar {record["lang_file"]}'}
    if (folder / 'languages.mcmeta').exists():
        listed = json.loads((folder / 'languages.mcmeta').read_text(encoding='utf-8'))['language']
        if ('en_US' in listed) != upper or ('en_us' in listed) == upper:
            raise SystemExit(f'{version}: language list and jar disagree on the case of language codes')
        sources['language_code'] = (f'Mojang\'s language list (asset pack.mcmeta) uses {"en_US" if upper else "en_us"}'
                                    f', jar file {jar_lang}')
    game = json.loads((folder / 'game-version.json').read_text()) if (folder / 'game-version.json').exists() else None
    pack_version = game.get('pack_version') if game else None
    minor = None
    if isinstance(pack_version, int):
        number, sources['pack_format'] = pack_version, 'client jar version.json pack_version'
    elif isinstance(pack_version, dict) and 'resource_major' in pack_version:
        number, minor = pack_version['resource_major'], pack_version.get('resource_minor', 0)
        sources['pack_format'] = 'client jar version.json pack_version.resource_major'
    elif isinstance(pack_version, dict):
        number, sources['pack_format'] = pack_version['resource'], 'client jar version.json pack_version.resource'
    else:
        number = next((n for n, first, last in WIKI_PACK_FORMAT
                       if order.index(first) <= order.index(version) <= order.index(last)), None)
        if number is None:
            raise SystemExit(f'{version}: no pack format known')
        sources['pack_format'] = WIKI_SOURCE
    jar_meta = folder / 'jar-pack.mcmeta'
    if jar_meta.exists():
        built_in = json.loads(jar_meta.read_text(encoding='utf-8'))
        # 1.6.x jars hold the default resource pack's pack.mcmeta (with the language list); 1.13+ the data pack's.
        if 'language' in built_in:
            if built_in['pack'].get('pack_format') != number:
                raise SystemExit(f'{version}: the jar\'s own resource pack says format {built_in["pack"]["pack_format"]}')
            sources['pack_format'] += '; agrees with the jar\'s own pack.mcmeta (resource pack with a language block)'
    for n, first, last in WIKI_PACK_FORMAT:
        if order.index(first) <= order.index(version) <= order.index(last) and n != number:
            raise SystemExit(f'{version}: the jar says pack format {number}, minecraft.wiki {n}')
    if isinstance(pack_version, dict) and 'resource_major' in pack_version:
        style = 'min_max'
    elif order.index(version) >= order.index(SUPPORTED_FORMATS_FROM):
        style = 'supported_formats'
    else:
        style = 'pack_format'
    sources['mcmeta'] = ('version.json pack_version is {resource_major, resource_minor} (1.21.9 and later); '
                         if style == 'min_max' else '') + 'minecraft.wiki Pack.mcmeta rev 3821904'
    entry = {
        'lang_format': 'json' if extension == 'json' else 'lang',
        'lang_file': f'assets/minecraft/lang/{code}.{extension}',
        'language_code': code,
        'pack_format': number,
    }
    if minor is not None:
        entry['pack_format_minor'] = minor
    entry.update(mcmeta=style, client_sha1=record['client_sha1'], realms=record['realms'], sources=sources)
    return entry


def formats():
    order = releases()
    previous = json.loads(VERSIONS.read_text(encoding='utf-8')) if VERSIONS.exists() else {}
    result = {}
    for version in order:
        entry = facts(version, order)
        old = previous.get(version, {})
        entry.update(supported=bool(old.get('supported')), coverage=old.get('coverage'), note=old.get('note', ''))
        result[version] = entry
    VERSIONS.write_text(json.dumps(result, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{VERSIONS}: {len(result)} releases')
    others()


def family(entry):
    identifier = entry['id']
    if entry['type'] in ('old_alpha', 'old_beta'):
        return entry['type'].replace('_', ' ')
    if entry['type'] == 'release':
        return 'release before 1.6.1'
    if re.search(r'-snapshot-\d+$', identifier):
        return 'snapshot (N.N-snapshot-N)'
    if re.search(r'(-pre-?\d*| Pre-[Rr]elease( \d+)?)$', identifier) and not identifier.startswith('1.RV'):
        return 'pre-release'
    if re.search(r'(-rc-?\d+| Release Candidate \d+)$', identifier):
        return 'release candidate'
    if re.fullmatch(r'\d\dw\d\d[a-z~]', identifier):
        return 'weekly snapshot (YYwWWx)'
    if re.fullmatch(r'\d\dw\d\d.+|1\.RV-Pre1|3D Shareware v1\.34', identifier):
        return 'April Fools build'
    if re.fullmatch(r'1\.\d+(\.\d+)?', identifier):
        return 'pre-release named like a release'
    return f'other {entry["type"]}'


REASONS = {
    'weekly snapshot (YYwWWx)': 'development builds; texts and formats change from week to week; nobody keeps playing '
                                'them, and a pack would claim checks made on a moving target',
    'snapshot (N.N-snapshot-N)': 'the same, under the naming Mojang uses since 26.1',
    'pre-release': 'replaced within days by the release, whose pack is the one kept up to date',
    'release candidate': 'the same as pre-releases',
    'release before 1.6.1': 'no resource packs before 1.6.1 (13w24a): adding a language needs another mechanism',
    'April Fools build': 'joke versions, played for a day; a few predate 1.6.1',
    'pre-release named like a release': 'pre-releases of 1.3 to 1.7.1 published under the release\'s number as '
                                        '"snapshot"; their final release is the one claimed (when 1.6.1 or later)',
    'old alpha': 'no resource packs and no language files',
    'old beta': 'no resource packs; no language a pack could add',
}


def others():
    data = manifest()
    claimed, rest = split(data['versions'])
    groups = collections.defaultdict(list)
    for entry in rest:
        groups[family(entry)].append(entry)
    lines = ['# Minecraft Java: versions not claimed', '',
             'Generated by `python3 tools/mcversions.py formats` from Mojang\'s version manifest '
             f'({len(data["versions"])} entries; latest release {data["latest"]["release"]}, latest snapshot '
             f'{data["latest"]["snapshot"]}). Corsu claims only the {len(claimed)} releases from {FIRST} to '
             f'{claimed[-1]["id"]} listed in `versions.json` (a release is supported only once its pack is built and '
             'verified). Everything below is inventoried and not claimed: a launcher id naming one of these gives no '
             'pack (`minecraft_packs.base_version` returns None).', '',
             '| Family | Count | First | Last | Why not claimed |', '| --- | --- | --- | --- | --- |']
    for name in sorted(groups, key=lambda n: (-len(groups[n]), n)):
        items = groups[name]
        lines.append(f'| {name} | {len(items)} | {items[0]["id"]} | {items[-1]["id"]} | {REASONS.get(name, "")} |')
    years = collections.Counter('20' + e['id'][:2] for e in groups['weekly snapshot (YYwWWx)'])
    lines += ['', 'Weekly snapshots per year: ' + ', '.join(f'{y}: {n}' for y, n in sorted(years.items())) + '.', '']
    lines += ['Pre-releases and release candidates per release line (the release they announce):', '']
    lines.append(', '.join(f'{release}: {n}' for release, n in sorted(collections.Counter(
        re.split(r'-pre|-rc| Pre-[Rr]elease| Release Candidate', e['id'])[0]
        for e in groups['pre-release'] + groups['release candidate']).items(),
        key=lambda item: [int(x) for x in re.findall(r'\d+', item[0])])) + '.')
    OTHERS.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{OTHERS}: {len(rest)} entries not claimed')


# ---------------------------------------------------------------------------------------------------- checks

# Every language loader checked (1.6.4, 1.8.9, 1.12.2, 1.13.2, 1.16.5, 1.20.1, 1.21.x, 26.x) turns %d, %.1f, %1$d…
# into %s / %1$s with this very pattern as it reads the file; text components then accept only %s, %n$s and %%.
NUMERIC = re.compile(r'%(\d+\$)?[\d.]*[df]')
COMPONENT = re.compile(r'%(?:(\d+)\$)?([A-Za-z%]|$)')
STYLE = re.compile('§.')


def arguments(text):
    """The arguments a text shows, numbered as the game numbers them, and any format the game would refuse."""
    text = NUMERIC.sub(lambda m: f'%{m.group(1) or ""}s', text)
    used, implicit, bad = set(), 0, []
    for match in COMPONENT.finditer(text):
        index, kind = match.groups()
        if kind == '%':
            continue
        if kind != 's':
            bad.append(match.group(0))
            continue
        if index:
            used.add(int(index))
        else:
            implicit += 1
            used.add(implicit)
    if '%' in COMPONENT.sub('', text):
        bad.append('%')  # a % the pattern does not take (as in "50 % off"): the component shows its raw template
    return used, bad


def text_problems(key, original, text, lang_format):
    """Errors and warnings for one translated text against the English of the same version."""
    errors, warnings = [], []
    if not isinstance(text, str):
        return [f'{key}: not a string'], []
    try:
        text.encode('utf-8')
    except UnicodeEncodeError:
        errors.append(f'{key}: not valid Unicode (lone surrogate)')
    if original.strip() and not text.strip():
        errors.append(f'{key}: empty')
    want, bad_source = arguments(original)
    have, bad = arguments(text)
    if bad and bad != bad_source:
        errors.append(f'{key}: format the game refuses {bad}')
    if want != have:
        errors.append(f'{key}: arguments {sorted(want)} became {sorted(have)}')
    if collections.Counter(STYLE.findall(original)) != collections.Counter(STYLE.findall(text)):
        errors.append(f'{key}: formatting codes § changed')
    if lang_format == 'lang':
        if '\n' in text or '\r' in text:
            errors.append(f'{key}: a line break cannot be written in a .lang file')
        if '=' in key or key.startswith('#') or not key:
            errors.append(f'{key}: key cannot be written in a .lang file')
    elif original.count('\n') != text.count('\n'):
        warnings.append(f'{key}: line breaks {original.count(chr(10))} -> {text.count(chr(10))}')
    return errors, warnings


def mcmeta_problems(meta, entry):
    errors = []
    pack, language = meta.get('pack'), meta.get('language')
    number, style = entry['pack_format'], entry['mcmeta']
    expected = {'pack_format': {'description', 'pack_format'},
                'supported_formats': {'description', 'pack_format', 'supported_formats'},
                'min_max': {'description', 'min_format', 'max_format'}}[style]
    if not isinstance(pack, dict) or set(pack) != expected:
        return [f'pack.mcmeta: "pack" must have exactly {sorted(expected)} for this version']
    if not isinstance(pack['description'], str):
        errors.append('pack.mcmeta: description must be a string (a text component only from 1.7.4)')
    if style == 'min_max':
        if pack['min_format'] != number or pack['max_format'] != number:
            errors.append(f'pack.mcmeta: min_format/max_format must be {number}')
    else:
        if pack['pack_format'] != number:
            errors.append(f'pack.mcmeta: pack_format must be {number}')
        if style == 'supported_formats' and pack['supported_formats'] != [number, number]:
            errors.append(f'pack.mcmeta: supported_formats must be [{number}, {number}]')
    wanted = {entry['language_code']: {'name': packs.NAME, 'region': packs.REGION, 'bidirectional': False}}
    if language != wanted:
        errors.append(f'pack.mcmeta: language must be {wanted}')
    return errors


SCAN = {'numeric': (b'%(\\d+\\$)?[\\d\\.]*[df]', b'%(\\d+\\$)?[\\d.]*[df]'), 'format_error': (b'Format error: ',),
        'client': (b'lang/%s.json',), 'lang_loader': (b'lang/%s.lang', b'lang/%s.json'),
        'language_meta': (b'bidirectional',), 'pack_meta': (b'pack_format',),
        'supported_formats': (b'supported_formats',), 'min_format': (b'min_format',)}


def scan(jar):
    """Classes of a jar holding each string constant of SCAN (cached next to the jar)."""
    stamp = jar.with_name('client-strings.json')
    size = jar.stat().st_size
    if stamp.exists():
        saved = json.loads(stamp.read_text())
        if saved.get('size') == size and set(saved['found']) == set(SCAN):
            return saved['found']
    found = {name: [] for name in SCAN}
    with zipfile.ZipFile(jar) as archive:
        for member in archive.namelist():
            if not member.endswith('.class'):
                continue
            data = archive.read(member)
            for name, needles in SCAN.items():
                if any(needle in data for needle in needles):
                    found[name].append(member[:-6].replace('/', '.'))
    stamp.write_text(json.dumps({'size': size, 'found': found}))
    return found


def java_run(classpath, program, arguments, folder):
    separator = os.pathsep
    path = separator.join(str(item) for item in classpath)
    subprocess.run(['javac', '-nowarn', '-cp', path, '-d', folder, str(JAVA / program)], check=True,
                   capture_output=True)
    # The game's logging may write logs/ in the working directory: keep it in the temporary folder.
    main = 'corsu.' + program[:-5] if program == 'LegacyFormatCheck.java' else program[:-5]
    result = subprocess.run(['java', '-cp', folder + separator + path, main] + [str(a) for a in arguments],
                            cwd=folder, capture_output=True, text=True, timeout=900)
    return result.returncode, result.stdout + result.stderr


def engine_check(version, entry, payload, texts_en):
    """Run the version's own client code on the pack. Returns (ok, summary lines, raw log)."""
    classpath = client(version)
    found = scan(classpath[0])
    summary, ok = [], True
    style = entry['mcmeta']
    has_supported, has_min = bool(found['supported_formats']), bool(found['min_format'])
    if (style == 'min_max') != has_min or (style == 'supported_formats' and not has_supported) or \
            (style == 'pack_format' and has_supported):
        summary.append(f'jar strings disagree with pack.mcmeta style {style}: supported_formats {has_supported}, '
                       f'min_format {has_min}')
        ok = False
    else:
        summary.append(f'jar strings agree with pack.mcmeta style {style} (supported_formats {has_supported}, '
                       f'min_format {has_min})')
    loaders = sorted(found['numeric'], key=lambda name: name not in found['lang_loader'])
    i18ns = [name for name in found['format_error'] if name not in loaders]
    log = []
    with tempfile.TemporaryDirectory() as folder:
        work = Path(folder)
        (work / 'english.json').write_text(json.dumps(texts_en, ensure_ascii=False), encoding='utf-8')
        if entry['lang_format'] == 'json':
            game = json.dumps(texts_en, ensure_ascii=False)
        else:
            game = ''.join(f'{key}={value}\n' for key, value in texts_en.items())
        (work / 'english-game').write_text(game, encoding='utf-8')
        (work / 'pack.zip').write_bytes(payload)
        joined = lambda names: ','.join(names) or '-'  # noqa: E731
        code, output = java_run(classpath, 'LegacyFormatCheck.java', [
            work / 'english.json', work / 'english-game', work / 'pack.zip', entry['lang_file'],
            entry['language_code'], entry['pack_format'], joined(loaders), joined(i18ns), joined(found['client']),
            joined(found['language_meta']), joined(found['pack_meta'])], folder)
        log.append(output)
        lines = output.splitlines()
        summary += [line for line in lines if line.startswith(('engine\t', 'metadata\t', 'rendered '))]
        # Printed for the English file, then for the Corsican one: the last is the pack's.
        summary += [line for line in lines if line.startswith('note\tUnicode')][-1:]
        summary += [line for line in lines if line.startswith(('render\t', 'extra\t', 'problem\t'))][:20]
        if code != 0:
            ok = False
            if code == 2:
                summary.append('the game\'s language code could not be found or run in this jar')
        metadata = [line for line in lines if line.startswith('metadata\t')]
        if not any('\taccepted\t' in line and line.split('\t')[1] == 'language' for line in metadata):
            summary.append('the language block was not read by the game\'s own code')
            ok = False
        if version.split('.')[0].isdigit() and int(version.split('.')[0]) >= 26:
            # 26.x jars are not obfuscated: LangCheck (the 26.3 check) also renders every text component.
            translated = {key: texts_en[key] for key in json.loads(zipfile.ZipFile(io.BytesIO(payload)).read(
                entry['lang_file'])) if key in texts_en}
            (work / 'english-translated.json').write_text(json.dumps(translated, ensure_ascii=False), encoding='utf-8')
            code, output = java_run(classpath, 'LangCheck.java', [
                work / 'english-translated.json', work / 'pack.zip', entry['pack_format'],
                entry.get('pack_format_minor', 0)], folder)
            log.append(output)
            summary += ['LangCheck: ' + line for line in output.splitlines()
                        if line.startswith(('pack.mcmeta', 'rendered', 'render\t', 'missing\t', 'no language'))][:20]
            ok = ok and code == 0
    return ok, summary, '\n'.join(log)


def base_equivalent(payload):
    """For the base release: the same pack, semantically, as the one src/minecraft.py builds today."""
    import minecraft as game_pack  # src/minecraft.py, needs src/corsu.py
    current = zipfile.ZipFile(io.BytesIO(game_pack.pack_from_sources()))
    built = zipfile.ZipFile(io.BytesIO(payload))
    problems = []
    if sorted(current.namelist()) != sorted(built.namelist()):
        problems.append(f'files {current.namelist()} != {built.namelist()}')
    for name in current.namelist():
        if name not in built.namelist():
            continue
        a, b = current.read(name), built.read(name)
        if name.endswith(('.json', '.mcmeta')):
            a, b = json.loads(a), json.loads(b)
        if a != b:
            problems.append(f'{name} differs from src/minecraft.py\'s pack')
    return problems


def verify(version, engine=True, record=True):
    data = packs.Data(HERE).load()
    if version not in data.versions:
        raise SystemExit(f'{version}: not in versions.json')
    entry = data.versions[version]
    texts_en = english(version)
    errors, warnings = [], []
    pairs = dict(data.pairs(version))
    if set(pairs) != set(texts_en):
        errors.append(f'keys.tsv lists {len(pairs)} keys for {version}, Mojang\'s English has {len(texts_en)}: '
                      'run `index`')
    errors += [f'{key}: English hash differs from keys.tsv (run `index`)' for key, text in texts_en.items()
               if key in pairs and pairs[key] != packs.digest(text)][:5]
    payload, report = packs.build_pack(version, data)
    if packs.build_pack(version, data)[0] != payload:
        errors.append('building twice gave different bytes')
    archive = zipfile.ZipFile(io.BytesIO(payload))
    names = archive.namelist()
    if names != ['pack.mcmeta', 'pack.png', entry['lang_file'], 'LICENSE.txt']:
        errors.append(f'zip holds {names}')
    if any(info.date_time != packs.DATE for info in archive.infolist()):
        errors.append('zip dates are not fixed')
    raw_meta = archive.read('pack.mcmeta')
    if not raw_meta.isascii():
        errors.append('pack.mcmeta is not ASCII (before 1.19.3 the game expects escapes, minecraft.wiki Pack.mcmeta)')
    errors += mcmeta_problems(json.loads(raw_meta), entry)
    raw = archive.read(entry['lang_file'])
    if raw.startswith(b'\xef\xbb\xbf'):
        errors.append('language file starts with a BOM')
    try:
        raw.decode('utf-8')
        loaded = parse_language(entry['lang_file'], raw)
    except (UnicodeDecodeError, ValueError) as error:
        errors.append(f'language file unreadable: {error}')
        loaded = {}
    expected, _ = packs.texts_for(version, data)
    if loaded != expected:
        errors.append('the language file does not read back as the texts it was built from')
    for key, text in loaded.items():
        if key not in texts_en:
            errors.append(f'{key}: not a key of {version}')
            continue
        e, w = text_problems(key, texts_en[key], text, entry['lang_format'])
        errors += e
        warnings += w
    if version == data.base:
        errors += base_equivalent(payload)
    summary, engine_ok = [], None
    if engine and not errors:
        engine_ok, summary, log = engine_check(version, entry, payload, texts_en)
        logs = ROOT / 'dist' / 'verify'
        logs.mkdir(parents=True, exist_ok=True)
        (logs / f'{version}.log').write_text(log, encoding='utf-8')
    print(f'== Minecraft {version}: {report["translated"]}/{report["total"]} keys translated '
          f'({report["missing"]} left in English), {entry["lang_file"]}, code {entry["language_code"]}, '
          f'pack format {entry["pack_format"]} ({entry["mcmeta"]})')
    for line in errors[:40]:
        print('  error:', line)
    if len(errors) > 40:
        print(f'  … {len(errors) - 40} more errors')
    print(f'  {len(errors)} errors, {len(warnings)} warnings (line breaks differing from English)')
    for line in summary:
        print('  game code:', line.replace('\t', ' '))
    supported = not errors and engine_ok is True
    if record and engine:
        stored = json.loads(VERSIONS.read_text(encoding='utf-8'))
        stored[version]['supported'] = supported
        stored[version]['coverage'] = {'translated': report['translated'], 'total': report['total']}
        engine_line = next((line for line in summary if line.startswith('rendered ')), 'game code not run')
        stored[version]['note'] = (f'verify {datetime.date.today().isoformat()}: {len(errors)} errors; {engine_line}'
                                   + ('' if supported else '; NOT SUPPORTED'))
        VERSIONS.write_text(json.dumps(stored, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return supported if engine else not errors


def build(version):
    payload, report = packs.build_pack(version, packs.Data(HERE).load())
    target = ROOT / 'dist' / f'corsu-minecraft-java-{version}.zip'
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(payload)
    print(f'{target}: {report["translated"]}/{report["total"]} keys')
    return target


# The first releases built and verified (MULTIVERSION.md): the newest, the last of each popular line, one per family.
TARGETS = ['26.3', '26.2', '26.1.2', '1.21.11', '1.21.1', '1.20.1', '1.16.5', '1.12.2', '1.8.9']


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('command', choices=['fetch', 'index', 'formats', 'build', 'verify'])
    parser.add_argument('versions', nargs='*', help='release ids, "all", or "targets" (the first targets)')
    parser.add_argument('--refresh', action='store_true', help='fetch again even when cached')
    parser.add_argument('--no-engine', action='store_true', help='verify without running the game\'s code')
    args = parser.parse_args()
    if args.command == 'fetch':
        manifest(refresh=True)
    names = args.versions or [BASE]
    if names == ['all']:
        names = releases()
    elif names == ['targets']:
        names = TARGETS
    if args.command == 'fetch':
        fetch_all(names, args.refresh)
    elif args.command == 'index':
        index()
    elif args.command == 'formats':
        formats()
    elif args.command == 'build':
        for version in names:
            build(version)
    else:
        results = {version: verify(version, engine=not args.no_engine) for version in names}
        if not args.no_engine:
            print('supported:', ', '.join(v for v, ok in results.items() if ok) or 'none')
        sys.exit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    main()
