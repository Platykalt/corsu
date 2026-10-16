#!/usr/bin/env python3
"""Corsican for Minecraft: Bedrock Edition, as a global resource pack that adds the language "Corsu (Corsica)".
PROTOTYPE: the pack has never been loaded in the game.

    python3 tools/bedrock.py fetch [TAG]   download Mojang's texts from a bedrock-samples release into the cache
    python3 tools/bedrock.py stats [TAG]   count keys per category and the Java translations that could be reused
    python3 tools/bedrock.py seed [TAG]    rewrite minecraft/bedrock/co_FR.lang from the Java translation (exact reuse only)
    python3 tools/bedrock.py check [TAG]   placeholders, § codes, line breaks, duplicate keys, line endings
    python3 tools/bedrock.py build [TAG]   write dist/corsu-minecraft-bedrock-<TAG>.mcpack

Mojang's files are never committed: `fetch` puts them in ~/.cache/corsu/bedrock/<TAG> (or $CORSU_CACHE/bedrock/<TAG>).
They come from https://github.com/Mojang/bedrock-samples, whose LICENSE.md puts them under the Minecraft EULA; they are
used here for local checks only and none of them goes into the pack.
`seed` never translates: it copies a Corsican text from minecraft/java/co_fr.json only when the Bedrock English text is
identical to the Java English text and the two keys belong to corresponding families (block names to block names, …).
Every copied line ends with "\t## from-java:<Java key>". Keys left out show the game's fallback (expected: English).
"""
import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'minecraft/bedrock'
JAVA = ROOT / 'minecraft/java'
TRANSLATION = HERE / 'co_FR.lang'
MANIFEST = HERE / 'manifest.json'
TAG = (HERE / 'VERSION').read_text().strip() if (HERE / 'VERSION').exists() else 'v1.26.50.4'
JAVA_VERSION = (JAVA / 'VERSION').read_text().strip() if (JAVA / 'VERSION').exists() else '26.3'
LANGUAGE = 'co_FR'
LANGUAGE_NAME = 'Corsu (Corsica)'
RAW = 'https://raw.githubusercontent.com/Mojang/bedrock-samples/{tag}/{path}'
TEXTS = ['en_US.lang', 'fr_FR.lang', 'it_IT.lang', 'languages.json', 'language_names.json']
EXTRA = ['LICENSE.md', 'version.json', 'resource_pack/manifest.json']
MARKER = '\t## from-java:'
# Bedrock's placeholders: %s %d %.2f, numbered %1$s %2$d, bare numbered %1 %2, and the literal %%.
PLACEHOLDER = re.compile(r'%%|%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdifxX]|%\d+')
STYLE = re.compile('§.', re.S)
LINEBREAK = re.compile(r'~LINEBREAK~|\\n')
# Bedrock key family (first part of the key) -> Java key families whose texts mean the same kind of thing.
FAMILIES = {
    'tile': {'block', 'item'},
    'item': {'item', 'block', 'jukebox_song', 'trim_pattern', 'trim_material', 'instrument', 'filled_map', 'color'},
    'entity': {'entity'},
    'potion': {'effect', 'item'},
    'tipped_arrow': {'item'},
    'effect': {'effect'},
    'enchantment': {'enchantment'},
    'subtitles': {'subtitles'},
    'death': {'death'},
    'stat': {'stat'},
    'attribute': {'attribute'},
    'container': {'container'},
    'key': {'key'},
    'keyboard': {'key'},
    'achievement': {'advancements'},
    'options': {'options'},
    'selectWorld': {'selectWorld'},
    'createWorld': {'createWorld', 'selectWorld'},
    'createWorldScreen': {'createWorld', 'selectWorld'},
    'gui': {'gui'},
    'chat': {'chat'},
    'book': {'book'},
    'demo': {'demo'},
    'structure_block': {'structure_block'},
    'jigsaw': {'jigsaw_block'},
    'commands': {'commands'},
    'menu': {'menu'},
}


def cache(tag):
    base = Path(os.environ.get('CORSU_CACHE', Path.home() / '.cache/corsu'))
    return base / 'bedrock' / tag


def download(url):
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read()


def fetch(tag):
    """resource_pack/texts files of one release tag, plus the repository's licence and version list for the record."""
    folder = cache(tag)
    if (folder / 'en_US.lang').exists():
        return folder
    folder.mkdir(parents=True, exist_ok=True)
    record = {'repository': 'https://github.com/Mojang/bedrock-samples', 'tag': tag, 'files': {}}
    for name in TEXTS + EXTRA:
        path = name if name in EXTRA else f'resource_pack/texts/{name}'
        url = RAW.format(tag=tag, path=path)
        try:
            data = download(url)
        except OSError as error:
            if name == 'en_US.lang':
                raise SystemExit(f'cannot download {url}: {error}')
            print(f'not found, skipped: {url}')
            continue
        target = folder / name.replace('/', '_')
        target.write_bytes(data)
        record['files'][target.name] = {'url': url, 'sha256': hashlib.sha256(data).hexdigest()}
    (folder / 'fetched.json').write_text(json.dumps(record, indent=1) + '\n')
    print(f'bedrock-samples {tag}: texts in {folder}')
    return folder


def parse(text, name='lang'):
    """A .lang file as [(line number, key, value, comment)], plus format problems. The value stops at the first
    "##" (the game reads the rest as a comment); the comment keeps the whitespace before "##" and the rest."""
    rows, problems = [], []
    if text.startswith('﻿'):
        text = text[1:]
    for number, line in enumerate(text.split('\n'), 1):
        line = line.rstrip('\r')
        if not line.strip() or line.lstrip().startswith('##'):
            continue
        key, equals, value = line.partition('=')
        if not equals or not key:
            problems.append(f'{name}:{number}: not key=value: {line[:60]!r}')
            continue
        comment = ''
        if '##' in value:
            head = value[:value.index('##')]
            value = head.rstrip(' \t')
            comment = line.partition('=')[2][len(value):]
        rows.append((number, key, value, comment))
    return rows, problems


def read_lang(path):
    rows, _ = parse(Path(path).read_text(encoding='utf-8'), Path(path).name)
    return {key: value for _, key, value, _ in rows}


def placeholders(text):
    return collections.Counter(PLACEHOLDER.findall(text))


def family(key):
    return key.split('.')[0]


def corresponds(bedrock_key, java_key):
    return family(java_key) in FAMILIES.get(family(bedrock_key), set())


def line_problems(key, english, text):
    """What makes one translated value unusable in place of the English one."""
    problems = []
    if not text.strip() and english.strip():
        problems.append(f'{key}: empty')
    if placeholders(english) != placeholders(text):
        problems.append(f'{key}: placeholders {sorted(placeholders(english).elements())} '
                        f'became {sorted(placeholders(text).elements())}')
    if collections.Counter(STYLE.findall(english)) != collections.Counter(STYLE.findall(text)):
        problems.append(f'{key}: formatting codes § changed')
    if len(LINEBREAK.findall(english)) != len(LINEBREAK.findall(text)):
        problems.append(f'{key}: line breaks (~LINEBREAK~ or \\n) changed')
    if '\n' in text or '\r' in text:
        problems.append(f'{key}: raw line break inside the value')
    if '##' in text:
        problems.append(f'{key}: "##" inside the value (the game would cut it there)')
    return problems


def seed(english, java_english, java_corsican):
    """[(Bedrock key, Corsican text, Java key)] for every Bedrock key whose English text is identical to a Java
    English text of a corresponding family, and the reasons the other identical texts were not reused."""
    by_text = collections.defaultdict(list)
    for java_key, text in java_english.items():
        if text.strip() and java_corsican.get(java_key, '').strip():
            by_text[text].append(java_key)
    reused, skipped = [], collections.Counter()
    for key, text in english.items():
        if not text.strip() or text not in by_text:
            continue
        candidates = [java_key for java_key in by_text[text] if corresponds(key, java_key)]
        if not candidates:
            skipped['identical English, other family'] += 1
            continue
        translations = {java_corsican[java_key] for java_key in candidates}
        if len(translations) > 1:
            skipped['identical English, Java translations disagree'] += 1
            continue
        java_key = sorted(candidates)[0]
        corsican = java_corsican[java_key]
        if line_problems(key, text, corsican):
            skipped['identical English, Corsican fails Bedrock checks'] += 1
            continue
        reused.append((key, corsican, java_key))
    return reused, skipped


def write_seed(reused, tag, java_version):
    lines = [f'## Corsu: Minecraft Bedrock Edition in Corsican (lingua corsa). PROTOTYPE, never loaded in the game.',
             f'## Keys of bedrock-samples {tag} resource_pack/texts/en_US.lang. Written by tools/bedrock.py seed:',
             f'## each line reuses minecraft/java/co_fr.json (Java {java_version}) where the English text is identical',
             '## and the key families correspond; "## from-java:<key>" names the Java key. Other keys are left out.']
    lines += [f'{key}={text}{MARKER}{java_key}' for key, text, java_key in reused]
    return '\n'.join(lines) + '\n'


def check_text(raw, english):
    """Errors in a co_FR.lang file (as bytes) against the English keys and texts."""
    errors = []
    if raw.startswith(b'\xef\xbb\xbf'):
        errors.append('byte order mark: write UTF-8 without BOM')
    if b'\r' in raw:
        errors.append('CR line endings: use LF only, like en_US.lang')
    if raw and not raw.endswith(b'\n'):
        errors.append('no final line break')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as error:
        return errors + [f'not UTF-8: {error}']
    rows, problems = parse(text, LANGUAGE + '.lang')
    errors += problems
    seen = {}
    for number, key, value, comment in rows:
        if key in seen:
            errors.append(f'line {number}: duplicate key {key} (first on line {seen[key]})')
            continue
        seen[key] = number
        if key != key.strip() or ' ' in key:
            errors.append(f'line {number}: spaces in key {key!r}')
        if key not in english:
            errors.append(f'line {number}: {key} is not in en_US.lang')
            continue
        if comment and not comment.startswith('\t##'):
            # Spaces before "##" stay in the text (wiki.bedrock.dev); Mojang's localisation rules ask for a tab.
            errors.append(f'line {number}: inline comment must be preceded by one tab, not spaces')
        errors += [f'line {number}: {problem}' for problem in line_problems(key, english[key], value)]
    return errors


def java_sources(java_version):
    """Java English and Corsican, read from the Java tool's cache and the committed translation."""
    spec = importlib.util.spec_from_file_location('corsu_java_tool', ROOT / 'tools/minecraft.py')
    java = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(java)
    return java.source(java_version), java.strict(java.TRANSLATION)


def categories(keys):
    return collections.Counter(family(key) for key in keys)


def stats(tag):
    folder = fetch(tag)
    english = read_lang(folder / 'en_US.lang')
    java_english, java_corsican = java_sources(JAVA_VERSION)
    java_texts = set(java_english.values())
    identical = [key for key, text in english.items() if text.strip() and text in java_texts]
    reused, skipped = seed(english, java_english, java_corsican)
    reused_by = categories(key for key, _, _ in reused)
    identical_by = categories(identical)
    print(f'bedrock-samples {tag}: {len(english)} keys in en_US.lang '
          f'({sum(1 for t in english.values() if not t.strip())} empty)')
    for name in ('fr_FR.lang', 'it_IT.lang'):
        if (folder / name).exists():
            print(f'  {name}: {len(read_lang(folder / name))} keys')
    print(f'identical English text in Java {JAVA_VERSION} en_us.json (any key): {len(identical)}')
    print(f'reusable (identical text, corresponding family, one Corsican text, passes checks): {len(reused)}')
    for reason, count in skipped.most_common():
        print(f'  not reused, {reason}: {count}')
    print('| family | keys | identical text in Java | reused |')
    print('| --- | ---: | ---: | ---: |')
    total = categories(english)
    for name, count in total.most_common():
        if count >= 50 or reused_by[name]:
            print(f'| {name} | {count} | {identical_by[name]} | {reused_by[name]} |')
    rest = [n for n, c in total.items() if c < 50 and not reused_by[n]]
    print(f'| {len(rest)} other families | {sum(total[n] for n in rest)} | {sum(identical_by[n] for n in rest)} | 0 |')
    return english, reused


def run_seed(tag):
    folder = fetch(tag)
    english = read_lang(folder / 'en_US.lang')
    java_english, java_corsican = java_sources(JAVA_VERSION)
    reused, skipped = seed(english, java_english, java_corsican)
    TRANSLATION.write_text(write_seed(reused, tag, JAVA_VERSION), encoding='utf-8', newline='\n')
    print(f'{TRANSLATION}: {len(reused)} / {len(english)} keys reused from Java; {dict(skipped)}')


def check(tag, quiet=False):
    english = read_lang(fetch(tag) / 'en_US.lang')
    errors = check_text(TRANSLATION.read_bytes(), english)
    errors += check_manifest(json.loads(MANIFEST.read_text(encoding='utf-8')))
    if not quiet:
        for line in errors:
            print('error:', line)
        count = len(read_lang(TRANSLATION))
        print(f'Minecraft Bedrock {tag}: {count}/{len(english)} keys in {TRANSLATION.name}, {len(errors)} errors')
    return errors


def check_manifest(manifest):
    errors = []
    uuid = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
    header = manifest.get('header', {})
    if manifest.get('format_version') != 2:
        errors.append('manifest: format_version must be 2')
    for field in ('name', 'description', 'uuid', 'version', 'min_engine_version'):
        if field not in header:
            errors.append(f'manifest: header.{field} missing')
    modules = manifest.get('modules', [])
    if [module.get('type') for module in modules] != ['resources']:
        errors.append('manifest: exactly one module of type "resources" expected')
    ids = [header.get('uuid')] + [module.get('uuid') for module in modules]
    if not all(isinstance(i, str) and uuid.match(i) for i in ids) or len(set(ids)) != len(ids):
        errors.append('manifest: header and module need distinct version-4 UUIDs')
    for version in [header.get('version'), header.get('min_engine_version')] + [m.get('version') for m in modules]:
        if not (isinstance(version, list) and len(version) == 3 and all(isinstance(n, int) for n in version)):
            errors.append(f'manifest: version {version!r} is not [major, minor, patch]')
    return errors


def make_pack(manifest, translation, license_text, icon):
    """The .mcpack (a zip) as bytes. Fixed dates and order: the same sources always give the same file."""
    buffer = io.BytesIO()
    files = [
        ('manifest.json', manifest),
        ('pack_icon.png', icon),
        ('texts/languages.json', json.dumps([LANGUAGE], indent=2) + '\n'),
        ('texts/language_names.json', json.dumps([[LANGUAGE, LANGUAGE_NAME]], ensure_ascii=False, indent=2) + '\n'),
        (f'texts/{LANGUAGE}.lang', translation),
        ('LICENSE.txt', license_text),
    ]
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in files:
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def icon():
    sys.path.insert(0, str(ROOT / 'src'))
    import minecraft as game_pack  # src/minecraft.py: the same generated flag-coloured icon as the Java pack
    return game_pack.png(128)


def build_path(tag):
    return ROOT / 'dist' / f'corsu-minecraft-bedrock-{tag}.mcpack'


def build(tag):
    errors = check(tag, quiet=True)
    if errors:
        raise SystemExit(f'{len(errors)} errors: run `python3 tools/bedrock.py check {tag}` first')
    target = build_path(tag)
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(make_pack(MANIFEST.read_bytes(), TRANSLATION.read_bytes(), (HERE / 'LICENSE.txt').read_bytes(),
                                 icon()))
    print(f'{target} ({len(read_lang(TRANSLATION))} texts, sha256 {hashlib.sha256(target.read_bytes()).hexdigest()})')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('command', choices=['fetch', 'stats', 'seed', 'check', 'build'])
    parser.add_argument('tag', nargs='?', default=TAG)
    args = parser.parse_args()
    if args.command == 'fetch':
        fetch(args.tag)
    elif args.command == 'stats':
        stats(args.tag)
    elif args.command == 'seed':
        run_seed(args.tag)
    elif args.command == 'check':
        sys.exit(1 if check(args.tag) else 0)
    else:
        build(args.tag)


if __name__ == '__main__':
    main()
