#!/usr/bin/env python3
"""Corsican for the English texts of older Minecraft: Java Edition releases (1.6.1 to the release before the base).

    python3 tools/mchistory.py classify [--english DIR] [--list CLASS]  classes of every (key, English) pair
    python3 tools/mchistory.py propose  [--english DIR] OUT.tsv         renamed pairs: 26.3 translation of the
                                                                        same text under a key of the same family
    python3 tools/mchistory.py todo     [--english DIR] OUT.tsv         pairs without a decision in history.json
    python3 tools/mchistory.py apply    FILE.tsv [--english DIR]        record decisions (rows of a reviewed TSV)
    python3 tools/mchistory.py check    [--english DIR]                 placeholders, empty, English left, schema
    python3 tools/mchistory.py placeholders [--english DIR]             rewrite history-placeholders.tsv
    python3 tools/mchistory.py measure  [--english DIR] [VERSION ...]   reused / adapted / new / missing per version

The contract is minecraft/java/MULTIVERSION.md. `history.json` holds Corsican for every (key, English hash) pair
of a handled release that differs from the 26.3 base: {key: {hash: {co, kind, from, review, note}}}; the hash is
the first 12 hex digits of the SHA-1 of the UTF-8 English text. Mojang's English is never committed: DIR holds one
`<release id>.json` per release ({"texts": {key: english}, "info": {...}}), by default $CORSU_MC_ENGLISH or
~/.cache/corsu/minecraft/en. Without it, `check` validates against history-placeholders.tsv (key, hash and
placeholder signature only).

TSV rows for `apply` (tab-separated, header optional): key, hash, co, kind, from, note. `\\n` in `co` is a line
break, `\\t` a tab. `apply` writes `review: ai`; human review is recorded by hand, never by a tool.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'minecraft/java'
BASE = HERE / 'co_fr.json'
HISTORY = HERE / 'history.json'
SIGNATURES = HERE / 'history-placeholders.tsv'
KEEP = HERE / 'same-as-english.txt'
BASE_VERSION = (HERE / 'VERSION').read_text().strip() if (HERE / 'VERSION').exists() else '26.3'
KINDS = ('reused', 'renamed', 'adapted', 'new')
REVIEWS = ('ai', 'human')
FIELDS = ('co', 'kind', 'from', 'review', 'note')
TARGETS = ('26.2', '26.1.2', '1.21.11', '1.21.1', '1.20.1', '1.16.5', '1.12.2', '1.8.9')

# java.util.Formatter (old .lang files, I18n.format) and Minecraft's TranslatableContents (JSON files) specifiers.
SPEC = re.compile(r'%(?:(\d+)\$)?([-#+ 0,(<]*)(\d+)?(\.\d+)?([a-zA-Z%])')
STYLE = re.compile('§.')
# English left untranslated: three ASCII letters in a row outside placeholders, codes and <arguments>.
WORDISH = re.compile(r'[A-Za-z]{3,}')
# Names and words that stay as they are in Corsican (same-as-english.txt lists whole keys; these are words).
KEEP_WORDS = {
    'minecraft', 'realms', 'mojang', 'microsoft', 'xbox', 'twitch', 'java', 'edition', 'ender', 'end', 'nether',
    'creeper', 'enderman', 'endermen', 'ghast', 'blaze', 'wither', 'shulker', 'slime', 'endermite', 'vex', 'redstone',
    'tnt', 'gui', 'fps', 'vsync', 'vbo', 'vbos', 'opengl', 'glsl', 'lwjgl', 'nbt', 'uuid', 'json', 'url', 'http',
    'https', 'www', 'net', 'com', 'help', 'ops', 'id', 'xp', 'hud', 'api', 'cpu', 'gpu', 'ram', 'mib', 'snooper',
    'netherite', 'purpur', 'chorus', 'calcite', 'andesite', 'diorite', 'terracotta', 'podzol', 'lava', 'magma',
    'taiga', 'panda', 'ocelot', 'cactus', 'azalea', 'golem', 'illager', 'piglin', 'hoglin', 'zoglin', 'strider',
    'axolotl', 'allay', 'breeze', 'sculk', 'acacia', 'nausea', 'magenta', 'dns', 'srv', 'ipv', 'tcp', 'udp',
    'ssl', 'utc', 'ping', 'lan', 'pvp', 'ctrl', 'alt', 'shift', 'tab', 'esc', 'hdr', 'aaa', 'ogg', 'png', 'zip',
    'mcfunction', 'datapack', 'sha', 'rgb', 'srgb', 'max', 'min', 'beta', 'alpha', 'pre', 'release', 'snapshot',
    'realm', 'video', 'post', 'bit', 'via', 'mac', 'osx', 'windows', 'vista', 'lion', 'cmd', 'amd', 'cjk', 'sdk',
    'ext', 'arb', 'framebuffer', 'soundflower', 'apple', 'notch', 'tundra', 'stereo', 'bonus', 'buffet', 'true',
    'false', 'create', 'future', 'and', 'per', 'coordinate', 'totem', 'standard', 'shaders', 'include',
    'boss', 'bossbar', 'mob', 'gamerule', 'tellraw', 'title', 'trigger', 'scoreboard', 'tick', 'ticks', 'stats',
    'clone', 'fill', 'give', 'kill', 'list', 'locate', 'say', 'seed', 'spreadplayers', 'stop', 'summon', 'tell',
    'teleport', 'testfor', 'testforblock', 'testforblocks', 'time', 'toggledownfall', 'weather', 'whitelist', 'xp',
}


def digest(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def signature(text):
    """What a translation must keep: format arguments by position and conversion, %% count, § codes, line breaks."""
    used, implicit, percent, bad = collections.Counter(), 0, 0, []
    for match in SPEC.finditer(text):
        index, flags, width, precision, kind = match.groups()
        if kind == '%':
            percent += 1
            continue
        if index:
            position = int(index)
        else:
            implicit += 1
            position = implicit
        used[f'{position}:{flags or ""}{width or ""}{precision or ""}{kind}'] += 1
    parts = [f'{name}x{count}' if count > 1 else name for name, count in sorted(used.items())]
    if percent:
        parts.append(f'%%x{percent}')
    for code, count in sorted(collections.Counter(STYLE.findall(text)).items()):
        parts.append(f'{code}x{count}')
    if text.count('\n'):
        parts.append(f'nl{text.count(chr(10))}')
    return ' '.join(parts) or '-'


def english_dir(value=None):
    return Path(value or os.environ.get('CORSU_MC_ENGLISH') or Path.home() / '.cache/corsu/minecraft/en')


def release_order(folder):
    """Release ids, newest first: releases.json next to DIR when present, else the files in DIR."""
    for candidate in (folder / 'releases.json', folder.parent / 'releases.json'):
        if candidate.exists():
            data = json.loads(candidate.read_text(encoding='utf-8'))
            ids = data['rel'] if isinstance(data, dict) else data
            return [v for v in ids if (folder / f'{v}.json').exists()]
    def key(name):
        return [int(part) if part.isdigit() else 0 for part in re.split(r'[.\-]', name)]
    return sorted((p.stem for p in folder.glob('*.json')), key=key, reverse=True)


class English:
    def __init__(self, folder):
        self.folder = Path(folder)
        if not (self.folder / f'{BASE_VERSION}.json').exists():
            raise SystemExit(f'no English texts in {self.folder} (set --english or CORSU_MC_ENGLISH)')
        self.order = release_order(self.folder)
        self._cache = {}

    def texts(self, version):
        if version not in self._cache:
            data = json.loads((self.folder / f'{version}.json').read_text(encoding='utf-8'))
            lang = data.get('info', {}).get('lang_file') or ['en_us.json']
            self._cache[version] = (data['texts'], 'lang' if lang[0].endswith('.lang') else 'json')
        return self._cache[version]

    def base(self):
        return self.texts(BASE_VERSION)[0]

    def pairs(self):
        """Every (key, English) pair of an older release that is not 26.3's own (key, English)."""
        base = self.base()
        found = collections.OrderedDict()
        for version in self.order:
            if version == BASE_VERSION:
                continue
            texts, family = self.texts(version)
            for key, text in texts.items():
                if base.get(key) == text:
                    continue
                pair = found.setdefault((key, text), {'versions': [], 'family': set()})
                pair['versions'].append(version)
                pair['family'].add(family)
        return found


def load_json(path):
    def pairs(items):
        seen = {}
        for key, value in items:
            if key in seen:
                raise ValueError(f'{path}: duplicate key {key}')
            seen[key] = value
        return seen
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs)


def load_history():
    return load_json(HISTORY) if HISTORY.exists() else {}


def save_history(history):
    ordered = {key: {h: {f: history[key][h][f] for f in FIELDS if f in history[key][h]}
                     for h in sorted(history[key])} for key in sorted(history)}
    HISTORY.write_text(json.dumps(ordered, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


# Old (.lang, up to 1.12.2) key prefixes and the 1.13+ families their texts moved to.
FAMILIES = {
    'tile': ('block', 'item'), 'block': ('block', 'item'), 'item': ('item', 'block'), 'entity': ('entity',), 'enchantment': ('enchantment',),
    'effect': ('effect',), 'potion': ('effect', 'item'), 'splash_potion': ('item',), 'lingering_potion': ('item',),
    'tipped_arrow': ('item',), 'achievement': ('advancements',), 'stat': ('stat', 'stat_type'),
    'attribute': ('attribute',), 'biome': ('biome',), 'death': ('death',), 'commands': ('commands', 'argument'),
    'key': ('key',), 'container': ('container', 'block'), 'gui': ('gui',), 'options': ('options',),
}


def family(key):
    return key.split('.')[0]


def compatible(old_key, new_key):
    wanted = FAMILIES.get(family(old_key), (family(old_key),))
    return family(new_key) in wanted


TRIVIAL = str.maketrans({'’': "'", '‘': "'", '“': '"', '”': '"', '…': '...'})


def normal(text):
    text = text.translate(TRIVIAL).casefold()
    return re.sub(r'[\s.!:,]+', ' ', text).strip()


def classify(english, history=None):
    """One class per pair: trivial, renamed, absent, changed, ambiguous (see history-report.md)."""
    history = history if history is not None else load_history()
    base = english.base()
    corsican = load_json(BASE)
    by_text = collections.defaultdict(list)
    for key, text in base.items():
        by_text[text].append(key)
    result = collections.OrderedDict()
    for (key, text), info in english.pairs().items():
        h = digest(text)
        entry = history.get(key, {}).get(h)
        row = {'key': key, 'hash': h, 'en': text, 'versions': info['versions'],
               'family': 'json' if 'json' in info['family'] else 'lang', 'candidates': [], 'flag': ''}
        if not text.strip():
            row['class'] = 'empty'
        elif key in base:
            same = normal(text) == normal(base[key]) and signature(text) == signature(base[key])
            row['class'] = 'trivial' if same else 'changed'
            row['candidates'] = [key]
        elif text in by_text:
            keys = by_text[text]
            fitting = [k for k in keys if compatible(key, k)]
            row['class'] = 'renamed'
            row['candidates'] = fitting or keys
            if not fitting:
                row['flag'] = 'family'
            elif len({corsican.get(k) for k in fitting}) > 1:
                row['flag'] = 'several'
        else:
            row['class'] = 'absent'
        if entry and 'ambiguous' in (entry.get('note') or ''):
            row['class'] = 'ambiguous'
        row['entry'] = entry
        result[(key, h)] = row
    return result


def best_candidate(old_key, candidates):
    """The 26.3 key whose name is closest to the old key (shared words), for renamed pairs."""
    def words(key):
        parts = re.split(r'[._]|(?<=[a-z])(?=[A-Z])', key)
        return {p.lower() for p in parts if p and p not in ('name', 'minecraft', 'tile', 'item', 'block')}
    old = words(old_key)
    return max(candidates, key=lambda k: (len(old & words(k)), -len(k)))


def read_tsv(path):
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip() or line.startswith('#') or line.startswith('key\thash'):
            continue
        cells = line.split('\t')
        if len(cells) < 4:
            raise SystemExit(f'{path}:{number}: expected key, hash, co, kind[, from, note]')
        cells += [''] * (6 - len(cells))
        key, h, co, kind, source, note = cells[:6]
        co = co.replace('\\n', '\n').replace('\\t', '\t')
        rows.append({'key': key, 'hash': h, 'co': co, 'kind': kind, 'from': source or None, 'note': note})
    return rows


def escape(text):
    return text.replace('\t', '\\t').replace('\n', '\\n')


def apply(path, english=None):
    history = load_history()
    known = None
    if english:
        known = {(k, digest(t)) for (k, t) in english.pairs()}
    count = 0
    for row in read_tsv(path):
        if row['kind'] not in KINDS:
            raise SystemExit(f"{row['key']}: unknown kind {row['kind']!r}")
        if known is not None and (row['key'], row['hash']) not in known:
            raise SystemExit(f"{row['key']} {row['hash']}: not a pair of the handled releases")
        entry = {'co': row['co'], 'kind': row['kind'], 'from': row['from'], 'review': 'ai'}
        if row['note']:
            entry['note'] = row['note']
        old = history.get(row['key'], {}).get(row['hash'])
        if old and old.get('review') == 'human' and old.get('co') != row['co']:
            raise SystemExit(f"{row['key']} {row['hash']}: reviewed by a speaker; change it by hand")
        history.setdefault(row['key'], {})[row['hash']] = entry
        count += 1
    save_history(history)
    print(f'{count} decisions recorded in {HISTORY.relative_to(ROOT)}')


def keep_keys():
    if not KEEP.exists():
        return set()
    return {line.strip() for line in KEEP.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.startswith('#')}


def leftover_english(english, corsican):
    """Words of the English found unchanged in the Corsican (outside placeholders and <arguments>)."""
    def words(text):
        text = SPEC.sub(' ', text)
        text = STYLE.sub(' ', text)
        return {w.lower() for w in WORDISH.findall(text)}
    same = words(english) & words(corsican)
    return sorted(w for w in same if w not in KEEP_WORDS)


def load_signatures():
    table = {}
    if SIGNATURES.exists():
        for line in SIGNATURES.read_text(encoding='utf-8').splitlines()[1:]:
            if line.strip():
                key, h, sig = line.split('\t')
                table[(key, h)] = sig
    return table


def check(english=None, quiet=False):
    """Errors that make history.json unusable; warnings are leads for review."""
    errors, warnings = [], []
    try:
        history = load_history()
    except ValueError as error:
        return [str(error)], []
    texts = {}
    if english:
        texts = {(k, digest(t)): t for (k, t) in english.pairs()}
    signatures = load_signatures()
    keep = keep_keys()
    for key, hashes in history.items():
        if not isinstance(hashes, dict):
            errors.append(f'{key}: not an object')
            continue
        for h, entry in hashes.items():
            where = f'{key} {h}'
            if not re.fullmatch(r'[0-9a-f]{12}', h):
                errors.append(f'{where}: hash is not 12 hex digits')
            if not isinstance(entry, dict) or set(entry) - set(FIELDS):
                errors.append(f'{where}: unexpected fields')
                continue
            co = entry.get('co')
            if not isinstance(co, str) or not co.strip():
                errors.append(f'{where}: empty or missing Corsican')
                continue
            if entry.get('kind') not in KINDS:
                errors.append(f'{where}: kind {entry.get("kind")!r}')
            if entry.get('review') not in REVIEWS:
                errors.append(f'{where}: review {entry.get("review")!r}')
            if entry.get('kind') in ('reused', 'renamed', 'adapted') and not entry.get('from'):
                errors.append(f'{where}: {entry.get("kind")} without "from"')
            if entry.get('kind') == 'new' and entry.get('from'):
                errors.append(f'{where}: new with "from"')
            if (key, h) in texts:
                original = texts[(key, h)]
                want = signature(original)
            elif (key, h) in signatures:
                original, want = None, signatures[(key, h)]
            else:
                errors.append(f'{where}: not a known pair (English or history-placeholders.tsv)')
                continue
            if signature(co) != want:
                errors.append(f'{where}: placeholders {signature(co)!r}, English {want!r}')
            if original is not None:
                lead = lambda t: (t[:len(t) - len(t.lstrip())], t[len(t.rstrip()):])
                if lead(co) != lead(original):
                    errors.append(f'{where}: leading or trailing white space differs from English')
                if '%' in original and not SPEC.search(original) and co.count('%') != original.count('%'):
                    warnings.append(f'{where}: % signs changed')
                note = entry.get('note') or ''
                kept = key in keep or entry.get('from') in keep or 'same as English' in note or 'command syntax' in note
                if co == original and not kept and re.search(r'[a-z]{3}', original):
                    errors.append(f'{where}: same as English: {original!r}')
                left = leftover_english(original, co)
                if left and not kept and entry.get('kind') in ('new', 'adapted'):
                    warnings.append(f'{where}: English words left {left}: {co!r}')
    if english:
        missing = [p for p, t in texts.items() if t.strip() and p[1] not in history.get(p[0], {})]
        if missing:
            warnings.append(f'{len(missing)} pairs without a decision yet')
    if not quiet:
        for line in warnings:
            print('warning:', line)
        for line in errors:
            print('error:', line)
        total = sum(len(v) for v in history.values() if isinstance(v, dict))
        print(f'history.json: {total} entries, {len(errors)} errors, {len(warnings)} warnings')
    return errors, warnings


def write_signatures(english):
    rows = sorted((k, digest(t), signature(t)) for (k, t) in english.pairs())
    lines = ['key\thash\tsignature'] + [f'{k}\t{h}\t{s}' for k, h, s in rows]
    SIGNATURES.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(rows)} pairs in {SIGNATURES.relative_to(ROOT)}')


def resolve(version_texts, history, base_texts, corsican):
    """MULTIVERSION.md resolution: history pair, else the base when 26.3 has the same English, else nothing."""
    found = {}
    for key, text in version_texts.items():
        entry = history.get(key, {}).get(digest(text))
        if entry:
            found[key] = ('history', entry)
        elif base_texts.get(key) == text and key in corsican:
            found[key] = ('base', None)
    return found


def measure(english, versions=TARGETS):
    history = load_history()
    base = english.base()
    corsican = load_json(BASE)
    rows = []
    for version in versions:
        texts, fam = english.texts(version)
        counts = collections.Counter()
        for key, text in texts.items():
            entry = history.get(key, {}).get(digest(text))
            if base.get(key) == text and key in corsican:
                counts['base'] += 1
            elif entry:
                kind = entry['kind']
                counts['reused' if kind in ('reused', 'renamed') else kind] += 1
            elif not text.strip():
                counts['base'] += 1
            else:
                counts['missing'] += 1
        rows.append((version, fam, len(texts), counts))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('classify', 'propose', 'todo', 'apply', 'check', 'placeholders',
                                            'measure'))
    parser.add_argument('args', nargs='*')
    parser.add_argument('--english', help='folder of <release>.json English texts')
    parser.add_argument('--list', help='classify: print the pairs of this class')
    options = parser.parse_args(argv)
    folder = english_dir(options.english)
    have = (folder / f'{BASE_VERSION}.json').exists()
    english = English(folder) if have else None
    if options.command in ('classify', 'propose', 'todo', 'placeholders', 'measure') and not english:
        raise SystemExit(f'no English texts in {folder} (set --english or CORSU_MC_ENGLISH)')
    if options.command == 'classify':
        table = classify(english)
        counts = collections.Counter((r['family'], r['class']) for r in table.values())
        for (fam, cls), n in sorted(counts.items()):
            print(f'{fam}\t{cls}\t{n}')
        print(f'total\t\t{len(table)}')
        if options.list:
            for r in table.values():
                if r['class'] == options.list or r['flag'] == options.list:
                    print(r['key'], r['hash'], repr(r['en']), r['candidates'], r['flag'], sep='\t')
    elif options.command == 'propose':
        corsican = load_json(BASE)
        out = []
        for r in classify(english).values():
            if r['class'] != 'renamed' or r['entry']:
                continue
            source = best_candidate(r['key'], r['candidates'])
            note = {'family': 'family differs', 'several': 'several 26.3 translations'}.get(r['flag'], '')
            out.append('\t'.join([r['key'], r['hash'], escape(corsican[source]), 'renamed', source, note,
                                  escape(r['en']), ','.join(r['candidates'])]))
        Path(options.args[0]).write_text('\n'.join(out) + '\n', encoding='utf-8')
        print(f'{len(out)} proposals in {options.args[0]}')
    elif options.command == 'todo':
        corsican = load_json(BASE)
        base = english.base()
        out = []
        for r in classify(english).values():
            if r['entry'] or r['class'] == 'empty':
                continue
            old = r['candidates'][0] if r['class'] in ('trivial', 'changed') else ''
            out.append('\t'.join([r['key'], r['hash'], r['class'], r['family'], r['versions'][-1] + '-' +
                                  r['versions'][0], escape(r['en']), escape(base.get(old, '')),
                                  escape(corsican.get(old, ''))]))
        Path(options.args[0]).write_text('\n'.join(out) + '\n', encoding='utf-8')
        print(f'{len(out)} pairs without a decision in {options.args[0]}')
    elif options.command == 'apply':
        apply(options.args[0], english)
    elif options.command == 'check':
        errors, _ = check(english)
        sys.exit(1 if errors else 0)
    elif options.command == 'placeholders':
        write_signatures(english)
    elif options.command == 'measure':
        print('| Version | Format | Keys | 26.3 as is | Reused (other key or same text) | Adapted | New | Missing |')
        print('| --- | --- | --- | --- | --- | --- | --- | --- |')
        for version, fam, total, c in measure(english, options.args or TARGETS):
            print(f"| {version} | {fam} | {total} | {c['base']} | {c['reused']} | {c['adapted']} | {c['new']} | "
                  f"{c['missing']} |")


if __name__ == '__main__':
    main()
