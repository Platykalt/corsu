#!/usr/bin/env python3
"""Corsican for Minecraft: Java Edition, as a resource pack that adds the language "Corsu (Corsica)".

    python3 tools/minecraft.py fetch [VERSION]      download the game's English, French and Italian texts
    python3 tools/minecraft.py check [VERSION]      completeness, placeholders, formatting codes, glossary
    python3 tools/minecraft.py diff OLD NEW         keys added, removed or changed between two versions
    python3 tools/minecraft.py inventory [VERSION]  rewrite minecraft/java/inventory.tsv
    python3 tools/minecraft.py build [VERSION]      write dist/corsu-minecraft-java-<VERSION>.zip
    python3 tools/minecraft.py status               counts per category and status from inventory.tsv
    python3 tools/minecraft.py texts [VERSION]      write the optional pack of splash texts and End Poem
    python3 tools/minecraft.py verify [VERSION]     render every string with the game's own code (needs a JDK)

The translation lives in minecraft/java/co_fr.json. Mojang's own texts are never committed: `fetch` puts them in
~/.cache/corsu/minecraft/<VERSION> (or $CORSU_CACHE/minecraft/<VERSION>), and the inventory keeps only a hash
of each English text, which is enough to tell when Mojang changes a sentence.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
import minecraft as game_pack  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'minecraft/java'
TRANSLATION = HERE / 'co_fr.json'
INVENTORY = HERE / 'inventory.tsv'
GLOSSARY = HERE / 'glossary.tsv'
KEEP = HERE / 'same-as-english.txt'
VERSION = (HERE / 'VERSION').read_text().strip() if (HERE / 'VERSION').exists() else '26.3'
LANGUAGE = 'co_fr'
MANIFEST = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
RESOURCES = 'https://resources.download.minecraft.net/{}/{}'
# Minecraft's own pattern (net.minecraft.network.chat.contents.TranslatableContents): %s, %1$s and %%.
# Language.loadFromJson first turns %d, %.1f and %1$d into %s / %1$s.
FORMAT = re.compile(r'%(?:(\d+)\$)?([A-Za-z%]|$)')
NUMERIC = re.compile(r'%(\d+\$)?[\d.]*[df]')
STYLE = re.compile('§.')


def cache(version):
    base = Path(os.environ.get('CORSU_CACHE', Path.home() / '.cache/corsu'))
    return base / 'minecraft' / version


def download(url, sha1=None):
    with urllib.request.urlopen(url, timeout=300) as response:
        data = response.read()
    if sha1 and hashlib.sha1(data).hexdigest() != sha1:
        raise SystemExit(f'checksum mismatch for {url}')
    return data


def fetch(version):
    """Mojang's client jar holds en_us.json; the other languages come from the asset index."""
    folder = cache(version)
    if (folder / 'en_us.json').exists():
        return folder
    folder.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(download(MANIFEST))
    entry = next((v for v in manifest['versions'] if v['id'] == version), None)
    if entry is None:
        raise SystemExit(f'unknown Minecraft version {version}')
    meta = json.loads(download(entry['url'], entry.get('sha1')))
    (folder / 'version.json').write_text(json.dumps(meta, indent=1))
    client = meta['downloads']['client']
    jar = download(client['url'], client['sha1'])
    with zipfile.ZipFile(__import__('io').BytesIO(jar)) as archive:
        (folder / 'en_us.json').write_bytes(archive.read('assets/minecraft/lang/en_us.json'))
        (folder / 'game-version.json').write_bytes(archive.read('version.json'))
        for name in archive.namelist():
            if name.startswith('assets/minecraft/texts/') or name == 'assets/minecraft/lang/deprecated.json':
                (folder / Path(name).name).write_bytes(archive.read(name))
    index = json.loads(download(meta['assetIndex']['url'], meta['assetIndex']['sha1']))['objects']
    for key, target in (('minecraft/lang/fr_fr.json', 'fr_fr.json'), ('minecraft/lang/it_it.json', 'it_it.json'),
                        ('realms/lang/en_us.json', 'realms_en_us.json'), ('pack.mcmeta', 'languages.mcmeta')):
        if key in index:
            digest = index[key]['hash']
            (folder / target).write_bytes(download(RESOURCES.format(digest[:2], digest), digest))
    print(f'Minecraft {version}: texts in {folder}')
    return folder


def strict(path):
    """JSON as Minecraft reads it, refusing duplicate keys, which Gson would silently overwrite."""
    def pairs(items):
        seen = {}
        for key, value in items:
            if key in seen:
                raise ValueError(f'{path}: duplicate key {key}')
            seen[key] = value
        return seen
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs)


def source(version):
    folder = fetch(version)
    english = strict(folder / 'en_us.json')
    if (folder / 'realms_en_us.json').exists():
        english.update(strict(folder / 'realms_en_us.json'))
    return english


def arguments(text):
    """The arguments a string consumes, as Minecraft numbers them, plus any format it would refuse."""
    text = NUMERIC.sub(lambda m: f'%{m.group(1) or ""}s', text)
    used, implicit, bad = collections.Counter(), 0, []
    for match in FORMAT.finditer(text):
        index, kind = match.groups()
        if kind == '%':
            continue
        if kind != 's':
            bad.append(match.group(0))
            continue
        if index:
            used[int(index)] += 1
        else:
            implicit += 1
            used[implicit] += 1
    return set(used), bad


def category(key):
    head = key.split('.')[0]
    groups = {
        'block': 'blocks', 'item': 'items', 'entity': 'creatures', 'subtitles': 'subtitles',
        'effect': 'effects', 'potion': 'effects', 'enchantment': 'enchantments',
        'advancements': 'advancements', 'biome': 'biomes', 'death': 'death messages',
        'commands': 'commands', 'argument': 'commands', 'arguments': 'commands', 'parsing': 'commands',
        'command': 'commands', 'snbt': 'commands', 'gamerule': 'game rules', 'editGamerule': 'game rules',
        'mco': 'Realms', 'realms': 'Realms', 'stat': 'statistics', 'stat_type': 'statistics',
        'key': 'controls', 'options': 'options', 'painting': 'paintings', 'jukebox_song': 'music',
        'music': 'music', 'trim_pattern': 'armour trims', 'trim_material': 'armour trims',
        'attribute': 'attributes', 'telemetry': 'telemetry', 'telemetry_info': 'telemetry',
        'narration': 'narration', 'narrator': 'narration', 'debug': 'debug screen', 'test': 'game tests',
        'test_instance': 'game tests', 'test_block': 'game tests', 'test_instance_block': 'game tests',
    }
    return groups.get(head, 'interface')


def load_glossary():
    rows = []
    if GLOSSARY.exists():
        lines = GLOSSARY.read_text(encoding='utf-8').splitlines()
        header = lines[0].split('\t')
        for line in lines[1:]:
            if line.strip() and not line.startswith('#'):
                rows.append(dict(zip(header, line.split('\t'))))
    return rows


def check(version, quiet=False):
    english = source(version)
    corsican = strict(TRANSLATION)
    keep = {line.strip() for line in KEEP.read_text(encoding='utf-8').splitlines() if line.strip() and not line.startswith('#')} if KEEP.exists() else set()
    errors, warnings = [], []
    missing = [key for key in english if key not in corsican]
    extra = [key for key in corsican if key not in english]
    errors += [f'missing: {key}' for key in missing]
    warnings += [f'not in {version} (kept for older versions): {key}' for key in extra]
    for key, text in corsican.items():
        if key not in english:
            continue
        original = english[key]
        if not isinstance(text, str):
            errors.append(f'{key}: not a string')
            continue
        if original.strip() and not text.strip():
            errors.append(f'{key}: empty')
        want, bad_source = arguments(original)
        have, bad = arguments(text)
        if bad != bad_source:
            errors.append(f'{key}: format Minecraft refuses {bad}')
        if want != have:
            errors.append(f'{key}: arguments {sorted(want)} became {sorted(have)}')
        if collections.Counter(STYLE.findall(original)) != collections.Counter(STYLE.findall(text)):
            errors.append(f'{key}: formatting codes § changed')
        if original.count('\n') != text.count('\n'):
            warnings.append(f'{key}: line breaks {original.count(chr(10))} -> {text.count(chr(10))}')
        if text == original and original.strip() and key not in keep and re.search(r'[a-z]{3}', original):
            warnings.append(f'{key}: same as English: {original!r}')
    # A glossary term in the English text should come out with its Corsican term (a hint for review, never a rule).
    for row in load_glossary():
        term, wanted = row.get('english', ''), row.get('corsican', '')
        if not term or not wanted or row.get('check') != 'yes':
            continue
        forms = [form.strip().lower() for form in wanted.split('/') + row.get('forms', '').split('/') if form.strip()]
        pattern = re.compile(rf'\b{re.escape(term)}\b', re.I)
        for key, original in english.items():
            if pattern.search(original) and key in corsican:
                text = corsican[key].lower()
                if not any(form in text for form in forms):
                    warnings.append(f'{key}: glossary "{term}" -> "{wanted}" not found in {corsican[key]!r}')
    translated = sum(1 for key in english if corsican.get(key, '').strip() or not english[key].strip())
    if not quiet:
        for line in warnings:
            print('warning:', line)
        for line in errors:
            print('error:', line)
        print(f'Minecraft Java {version}: {translated}/{len(english)} keys translated, '
              f'{len(errors)} errors, {len(warnings)} warnings')
    return errors, warnings


def digest(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def inventory(version):
    """key, category, hash of the English text, status. Statuses written by hand (reviewed, verified-in-game)
    survive as long as the English text keeps its hash; a changed sentence drops back to "to review"."""
    english = source(version)
    corsican = strict(TRANSLATION) if TRANSLATION.exists() else {}
    previous = {}
    if INVENTORY.exists():
        for line in INVENTORY.read_text(encoding='utf-8').splitlines()[1:]:
            key, _, sha, status = line.split('\t')[:4]
            previous[key] = (sha, status)
    lines = ['key\tcategory\ten_sha1\tstatus']
    counts = collections.Counter()
    for key, text in english.items():
        sha = digest(text)
        old_sha, old_status = previous.get(key, (None, None))
        if not text.strip():
            status = 'empty in English'
        elif not corsican.get(key, '').strip():
            status = 'missing'
        elif old_sha == sha and old_status not in (None, 'missing', 'to review'):
            status = old_status
        elif old_sha not in (None, sha):
            status = 'to review'
        else:
            status = 'translated'
        counts[status] += 1
        lines.append(f'{key}\t{category(key)}\t{sha}\t{status}')
    INVENTORY.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(dict(counts))


def diff(old, new):
    before, after = source(old), source(new)
    added = [k for k in after if k not in before]
    removed = [k for k in before if k not in after]
    changed = [k for k in after if k in before and before[k] != after[k]]
    for label, keys in (('added', added), ('removed', removed), ('changed', changed)):
        print(f'{label}: {len(keys)}')
        for key in keys:
            print(f'  {key}: {after.get(key, before.get(key))!r}')
    return added, removed, changed


def status():
    """Coverage, review and in-game checks are different things: count each status per category."""
    rows = [line.split('\t') for line in INVENTORY.read_text(encoding='utf-8').splitlines()[1:]]
    statuses = ['missing', 'to review', 'translated', 'reviewed', 'verified in game', 'empty in English']
    table = collections.defaultdict(collections.Counter)
    for _, group, _, state in rows:
        table[group][state] += 1
        table['all'][state] += 1
    print('| category | keys | ' + ' | '.join(statuses) + ' |')
    print('| --- ' * (len(statuses) + 2) + '|')
    for group in sorted(table, key=lambda g: (g == 'all', g)):
        counts = table[group]
        print(f'| {group} | {sum(counts.values())} | ' + ' | '.join(str(counts[s]) for s in statuses) + ' |')


def verify(version):
    """Run tools/minecraft/LangCheck.java against Mojang's client jar: Minecraft's own JSON loader reads
    co_fr.json and its own formatter renders every key with numbered arguments. No game window is opened."""
    import subprocess
    import tempfile
    folder = fetch(version)
    meta = json.loads((folder / 'version.json').read_text())
    libraries = folder / 'libraries'
    libraries.mkdir(exist_ok=True)
    classpath = []
    jar = folder / 'client.jar'
    if not jar.exists():
        client = meta['downloads']['client']
        jar.write_bytes(download(client['url'], client['sha1']))
    classpath.append(jar)
    for library in meta['libraries']:
        artifact = library.get('downloads', {}).get('artifact')
        # Plain Java libraries only: native builds (name:version:natives-…) are not needed to format text.
        if not artifact or library['name'].count(':') != 2:
            continue
        target = libraries / Path(artifact['path']).name
        if not target.exists():
            target.write_bytes(download(artifact['url'], artifact['sha1']))
        classpath.append(target)
    english = folder / 'en_us.json'
    with tempfile.TemporaryDirectory() as build:
        separator = os.pathsep
        path = separator.join(str(item) for item in classpath)
        subprocess.run(['javac', '-nowarn', '-cp', path, '-d', build, str(ROOT / 'tools/minecraft/LangCheck.java')], check=True)
        # The game's logging writes logs/latest.log in the working directory: keep it in the temporary folder.
        command = ['java', '-cp', build + separator + path, 'LangCheck', str(english)]
        result = subprocess.run(command + [str(TRANSLATION)], cwd=build)
        if result.returncode == 0:
            # Then the pack as distributed: metadata through the game's codecs, language file from the zip.
            game = json.loads((folder / 'game-version.json').read_text())['pack_version']
            pack = build_path(version)
            if not pack.exists():
                build(version)
            result = subprocess.run(command + [str(pack), str(game['resource_major']), str(game['resource_minor'])],
                                    cwd=build)
    return result.returncode


def build_path(version):
    return ROOT / 'dist' / f'corsu-minecraft-java-{version}.zip'


def build(version):
    errors, _ = check(version, quiet=True)
    if errors:
        raise SystemExit(f'{len(errors)} errors: run `python3 tools/minecraft.py check {version}` first')
    game = json.loads((cache(version) / 'game-version.json').read_text())
    major = game['pack_version']['resource_major']
    mcmeta = {
        'pack': {
            'description': f'Lingua corsa · Corsu, Minecraft {version} · NOT AN OFFICIAL MINECRAFT PRODUCT',
            'min_format': major,
            'max_format': major,
        },
        'language': {LANGUAGE: {'name': 'Corsu', 'region': 'Corsica', 'bidirectional': False}},
    }
    # Committed next to co_fr.json, so the Corsu installer builds the very same pack without Mojang's files.
    (HERE / 'pack.mcmeta').write_text(json.dumps(mcmeta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    target = build_path(version)
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(game_pack.make_pack((HERE / 'pack.mcmeta').read_bytes(), TRANSLATION.read_bytes(),
                                           (HERE / 'LICENSE.txt').read_bytes()))
    payload = strict(TRANSLATION)
    print(f'{target} ({len(payload)} texts, resource pack format {major})')
    return target


def texts(version):
    """The optional pack: Minecraft reads splashes.txt and end.txt whatever the language, so this pack changes them
    for every language. It is kept apart from the language pack and never installed without being asked for."""
    folder = fetch(version)
    problems = []
    for name in ('splashes.txt', 'end.txt'):
        original = (folder / name).read_text(encoding='utf-8').split('\n')
        corsican = (HERE / 'texts' / name).read_text(encoding='utf-8').split('\n')
        if len(original) != len(corsican):
            problems.append(f'{name}: {len(corsican)} lines, Minecraft has {len(original)}')
        for number, (a, b) in enumerate(zip(original, corsican), 1):
            if sorted(STYLE.findall(a)) != sorted(STYLE.findall(b)) or a.count('PLAYERNAME') != b.count('PLAYERNAME'):
                problems.append(f'{name}:{number}: formatting codes or PLAYERNAME changed')
    if problems:
        raise SystemExit('\n'.join(problems))
    game = json.loads((folder / 'game-version.json').read_text())
    major = game['pack_version']['resource_major']
    mcmeta = {'pack': {'description': f'Corsu: splash texts and End Poem in Corsican, every language · Minecraft {version}'
                                      ' · NOT AN OFFICIAL MINECRAFT PRODUCT', 'min_format': major, 'max_format': major}}
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in (('pack.mcmeta', json.dumps(mcmeta, ensure_ascii=False, indent=2) + '\n'),
                           ('pack.png', game_pack.png()),
                           ('assets/minecraft/texts/splashes.txt', (HERE / 'texts/splashes.txt').read_bytes()),
                           ('assets/minecraft/texts/end.txt', (HERE / 'texts/end.txt').read_bytes()),
                           ('LICENSE.txt', (HERE / 'texts/LICENSE.txt').read_bytes())):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    target = ROOT / 'dist' / f'corsu-minecraft-java-texts-{version}.zip'
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(buffer.getvalue())
    print(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('command', choices=['fetch', 'check', 'diff', 'inventory', 'build', 'status', 'verify', 'texts'])
    parser.add_argument('versions', nargs='*')
    args = parser.parse_args()
    versions = args.versions or [VERSION]
    if args.command == 'fetch':
        for version in versions:
            fetch(version)
    elif args.command == 'check':
        errors, _ = check(versions[0])
        sys.exit(1 if errors else 0)
    elif args.command == 'diff':
        if len(versions) != 2:
            parser.error('diff needs OLD and NEW')
        diff(*versions)
    elif args.command == 'inventory':
        inventory(versions[0])
    elif args.command == 'status':
        status()
    elif args.command == 'verify':
        sys.exit(verify(versions[0]))
    elif args.command == 'texts':
        texts(versions[0])
    else:
        build(versions[0])


if __name__ == '__main__':
    main()
