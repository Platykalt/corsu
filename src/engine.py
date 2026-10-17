#!/usr/bin/env python3
"""Corsican translation engine: lexicon lookup, placeholder templates and catalog formats.

Everything is local and deterministic. No network access, no machine translation and no
access to user documents or messages. Only whole interface labels are translated; when a
label is unknown it is returned unchanged.
"""
import json
import os
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEXICON = ROOT / 'lexicon/lexicon.tsv'


def user_lexicon():
    """Corrections made in the Corsu app's Review page, kept with Corsu's own data so updates keep them."""
    if os.environ.get('CORSU_USER_LEXICON'):
        return Path(os.environ['CORSU_USER_LEXICON'])
    home = Path.home()
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', home / 'AppData/Local')) / 'corsu/lexicon-user.tsv'
    if sys.platform == 'darwin':
        return home / 'Library/Application Support/corsu/lexicon-user.tsv'
    return home / '.local/share/corsu/lexicon-user.tsv'


# The person's own corrections load first, then Corsu's corrections, then reviewed translations from other
# projects, whose wording wins over draft rows.
USER = user_lexicon()
FIXES = ROOT / 'lexicon/lexicon-fixes.tsv'
REVIEWED = [ROOT / 'lexicon/lexicon-mozilla.tsv', ROOT / 'lexicon/lexicon-upstream.tsv']
LEXICONS = [USER, FIXES, *REVIEWED, LEXICON]
# Contextual translation memory: one JSON object per string, with its application, key, context and provenance
# (lexicon/memory/README.md). Used by lookup() and application_words(); translate() keeps the flat tables above.
MEMORY = ROOT / 'lexicon/memory'
# How far a translation was checked, from the least to the most trusted.
REVIEW_RANK = {'to-review': 0, 'untranslated': 0, 'corsu-draft': 1, 'ai-reviewed': 2, 'upstream-reviewed': 3,
               'human-reviewed': 4}
# Toolkits whose reviewed labels are generic interface words, valid in any application.
GENERIC_APPS = {'wxwidgets'}

# Placeholders that must survive translation untouched: Fluent placeables, printf
# specifiers (with Mozilla's %S and %1$S, used by Firefox's .properties files, but not Nyquist's ~% line break),
# Qt/KDE numbered arguments and shell-style variables.
PLACEHOLDER = re.compile(
    r'\{\s*[$-]?[\w.-]+(?:\([^{}]*\))?\s*\}'
    r'|%(?:\d+\$)?[0-9]*\.?[0-9]*(?:ll|l|h)?[sdiufgexXop]'
    r'|(?<!~)%(?:\d+\$)?S'
    r'|%[Ln]?\d+'
    r'|%[Ln]\b'
    r'|\$\{[A-Za-z_]\w*\}'
    r'|\$[A-Za-z_]\w*'
    r'|\{\d+\}'
    r'|\$\d'
)
# Markup and entities are contracts with the application, never translated content.
SIGNATURE = re.compile(r'\$\d|%(?:\d+\$)?[0-9]*\.?[0-9]*(?:ll|l|h)?[sdiufgexXop]|(?<!~)%(?:\d+\$)?S|%[Ln]?\d+|</?[A-Za-z][^>]*>|&[a-zA-Z]+;|\{[^{}]*\}')
ACCELERATOR = re.compile(r'(?<![&\w])&(?=[^\W\d_])|(?<![_\w])_(?=[^\W\d_])')
TRAILING = re.compile(r'^(.*?)([\s  ]*(?:\.\.\.|…|:|\?|!|;|\.))$', re.S)
WRAPPERS = (('«', '»'), ('"', '"'), ('“', '”'), ('(', ')'), ('[', ']'), ("'", "'"))
SEPARATORS = re.compile(r'(\s*[   ]?[:—–/·|]\s+|\n|\s+-\s+)')
TOKEN = re.compile('\x00(\\d+)\x00')


def normalize(text):
    """Fold spelling variants that differ only in typography, never meaning."""
    return (text.replace('’', "'").replace('ʼ', "'")
                .replace(' ', ' ').replace(' ', ' ').replace(' ', ' '))


def mask(value):
    """Replace placeholders with ordinal tokens, so one lexicon row covers every argument."""
    tokens = []

    def take(match):
        text = match.group(0)
        if text not in tokens:
            tokens.append(text)
        return f'\x00{tokens.index(text) + 1}\x00'

    return PLACEHOLDER.sub(take, value), tokens


def remask(value, tokens):
    """Mask a translation against the source's tokens; refuse unknown placeholders."""
    unknown = False

    def take(match):
        nonlocal unknown
        if match.group(0) not in tokens:
            unknown = True
            return match.group(0)
        return f'\x00{tokens.index(match.group(0)) + 1}\x00'

    result = PLACEHOLDER.sub(take, value)
    return None if unknown else result


def unmask(template, tokens):
    if any(int(index) > len(tokens) for index in TOKEN.findall(template)):
        return None
    return TOKEN.sub(lambda match: tokens[int(match.group(1)) - 1], template)


WORD = re.compile(r'\w+')


def loose_french(english, french, corsican):
    """True when an imported row's French is much shorter than its English and Corsican.

    Imported rows pair a project's English and French by message id, and some French translations abbreviate:
    VLC's "Force Profile" is just "Profil" in French, so "Profil" alone would have become "Forzà un Prufilu".
    The French side of such a row is not used as a source text; the English side still is."""
    count = lambda text: len(WORD.findall(text))
    return count(french) <= 3 and count(english) > count(french) and count(corsican) >= count(french) + 2


def add_row(words, english, french, corsican):
    """Map both sources of one row (and their placeholder templates) to its Corsican; earlier rows win."""
    for source in (english, french):
        if not source:
            continue
        words.setdefault(normalize(source), corsican)
        skeleton, tokens = mask(source)
        if tokens:
            template = remask(corsican, tokens)
            if template is not None:
                words.setdefault(normalize(skeleton), template)


def rows(source_path, section=None):
    """(english, french, corsican) rows of a lexicon file, or of one `# <section>:` part of it."""
    inside = section is None
    for number, line in enumerate(source_path.read_text(encoding='utf-8').splitlines(), 1):
        # A heading is '# ' (or a lone '#'); '#lounge|#détente|#riposu' is a row about a channel name.
        if line.startswith('#') and (line.startswith('# ') or line.strip() == '#' or line.count('|') != 2):
            if section is not None and line.startswith('# '):
                inside = line.startswith(f'# {section}:')
            continue
        if not line.strip() or not inside:
            continue
        fields = line.split('|')
        if len(fields) != 3:
            raise ValueError(f'{source_path}:{number}: expected English|French|Corsican')
        english, french, corsican = (field.strip() for field in fields)
        if corsican:
            yield english, french, corsican


def load_lexicon(path=None):
    """Read `English|French|Corsican` rows into direct and templated lookup tables."""
    words = {}
    paths = [Path(path)] if path else LEXICONS
    for source_path in paths:
        if not source_path.exists():
            continue
        imported = source_path in REVIEWED
        for english, french, corsican in rows(source_path):
            if imported and english and french and loose_french(english, french, corsican):
                french = ''
            add_row(words, english, french, corsican)
    return words


def application_words(*sections):
    """The words one application sees: corrections first (the person's own, then lexicon-fixes.tsv), then the rows
    written for that application in lexicon.tsv, then everything else. A label translated for Discord is not
    replaced by the same label taken from another program, where it may mean something else."""
    words = {}
    for source_path in (USER, FIXES):
        if source_path.exists():
            for row in rows(source_path):
                add_row(words, *row)
    for section in sections:
        for row in rows(LEXICON, section):
            add_row(words, *row)
    # Reviewed strings recorded in the translation memory for this application by another source than lexicon.tsv
    # itself (whose sections were just read).
    wanted = {section.casefold() for section in sections}
    for entry in memory_entries(exported=False):
        if (entry.get('app') or '').casefold() in wanted and not _from_lexicon(entry) \
                and REVIEW_RANK.get(entry.get('review'), 0) >= REVIEW_RANK['ai-reviewed'] \
                and isinstance(entry.get('target'), str):
            add_row(words, entry['source'] if entry.get('source_lang') == 'en' else '', entry.get('source_fr') or '',
                    entry['target'])
    for key, value in WORDS.items():
        words.setdefault(key, value)
    return words


WORDS = load_lexicon()


# --- translation memory ---------------------------------------------------------------------------------------------

def placeholders(text):
    found = []
    for value in PLACEHOLDER.findall(text or ''):
        if value not in found:
            found.append(value)
    return found


def read_memory(path):
    """Entries of one memory file with every field filled in: a `{"_defaults": {...}}` line gives the values its
    following entries leave out (nested one level for `origin` and `context`), `key` defaults to the source text,
    `params` to the source's placeholders and `source_fr` to the source when the source is French."""
    defaults = {}
    with open(path, encoding='utf-8') as lines:
        for line in lines:
            if not line.strip():
                continue
            entry = json.loads(line)
            if '_defaults' in entry:
                defaults = entry['_defaults']
                continue
            for field, value in defaults.items():
                if field not in entry:
                    entry[field] = value
                elif isinstance(value, dict) and isinstance(entry[field], dict):
                    entry[field] = {**value, **entry[field]}
            entry.setdefault('source', '')
            entry.setdefault('key', entry['source'])
            entry.setdefault('source_lang', 'en')
            if entry['source_lang'] == 'fr':
                entry.setdefault('source_fr', entry['source'])
            if 'params' not in entry:
                entry['params'] = placeholders(entry['source'])
            for field in ('app', 'component', 'context', 'source_fr', 'target', 'plural', 'origin', 'version',
                          'license', 'review', 'fetched'):
                entry.setdefault(field, None)
            yield entry


_MEMORY_CACHE = {}


def memory_entries(directory=None, exported=True):
    """Every entry of lexicon/memory/*.jsonl (read once per directory). exported=False leaves out the corsu-*.jsonl
    files, which are exports of lexicon.tsv itself."""
    directory = Path(directory or MEMORY)
    if (directory, exported) not in _MEMORY_CACHE:
        entries = []
        if directory.is_dir():
            for path in sorted(directory.glob('*.jsonl')):
                if exported or not path.name.startswith('corsu-'):
                    entries.extend(read_memory(path))
        _MEMORY_CACHE[(directory, exported)] = entries
    return _MEMORY_CACHE[(directory, exported)]


def _from_lexicon(entry):
    return ((entry.get('origin') or {}).get('path') or '').endswith('lexicon/lexicon.tsv')


def meaning(text):
    """A translation reduced to what distinguishes its meaning: typography, case, access keys and final
    punctuation removed."""
    text = normalize(text or '').replace('…', '...').casefold()
    text = ACCELERATOR.sub('', text)
    text = re.sub(r'[\s.:!?;]+$', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def memory_sources(entry):
    """(source text, Corsican) pairs an entry answers: its source, its French (unless, in an imported entry, the
    French abbreviates a longer English label, see loose_french) and its plural source with the last form."""
    target = entry.get('target')
    if not target:
        return []
    forms = target if isinstance(target, list) else [target]
    pairs = [(entry.get('source'), forms[0])]
    french = entry.get('source_fr')
    english = entry.get('source') if entry.get('source_lang') == 'en' else ''
    if french and french != entry.get('source') and not (
            entry.get('review') == 'upstream-reviewed' and english and loose_french(english, french, forms[0])):
        pairs.append((french, forms[0]))
    if entry.get('plural') and entry['plural'].get('source_plural'):
        pairs.append((entry['plural']['source_plural'], forms[-1]))
    return [(source, value) for source, value in pairs if source and value]


_INDEX_CACHE = {}


def _memory_index(directory=None):
    """Normalised source text (and placeholder template) -> [(entry, translation or template, tokens?)]."""
    directory = Path(directory or MEMORY)
    if directory not in _INDEX_CACHE:
        index = {}
        for entry in memory_entries(directory):
            target = entry.get('target')
            if not target:
                continue
            for source, value in memory_sources(entry):
                if not source or not value:
                    continue
                index.setdefault(normalize(source).strip(), []).append((entry, value, None))
                skeleton, tokens = mask(source)
                if tokens:
                    template = remask(value, tokens)
                    if template is not None:
                        index.setdefault(normalize(skeleton).strip(), []).append((entry, template, len(tokens)))
        _INDEX_CACHE[directory] = index
    return _INDEX_CACHE[directory]


def _corrections():
    """The person's own corrections, then lexicon-fixes.tsv: they win everywhere, as in application_words."""
    if 'corrections' not in _INDEX_CACHE:
        words = {}
        for source_path in (USER, FIXES):
            if Path(source_path).exists() and Path(source_path).is_file():
                for row in rows(Path(source_path)):
                    add_row(words, *row)
        _INDEX_CACHE['corrections'] = words
    return _INDEX_CACHE['corrections']


def _context_matches(entry, context):
    if not context:
        return False
    wanted = set(context.values()) if isinstance(context, dict) else {context}
    wanted.discard(None)
    found = {entry.get('component'), entry.get('key')}
    value = entry.get('context')
    if isinstance(value, str):
        found.add(value)
    elif isinstance(value, dict):
        found.update(item for name, item in value.items() if isinstance(item, str))
    found.discard(None)
    return bool(wanted & found)


def lookup(text, app=None, context=None, directory=None):
    """The Corsican of one exact source text (English or French) chosen with its application and context.

    Order: the person's corrections and lexicon-fixes.tsv; an entry of the same application; an entry with the same
    context (msgctxt, file, section or key); a reviewed entry of a generic toolkit. Otherwise, when the candidates
    disagree in meaning across applications (two or more distinct translations from different applications, none
    of them the requested one), the answer is None: keep the source rather than borrow another program's sense.
    When they agree, the best reviewed one is returned. Unknown text gives None."""
    if not text or not text.strip():
        return None
    core = normalize(text).strip()
    corrections = _corrections()
    if core in corrections:
        return corrections[core]
    skeleton, tokens = mask(core)
    if tokens and normalize(skeleton) in corrections:
        result = unmask(corrections[normalize(skeleton)], tokens)
        if result is not None:
            return result
    index = _memory_index(directory)
    candidates = [(entry, value) for entry, value, _ in index.get(core, [])]
    if not candidates and tokens:
        for entry, template, count in index.get(normalize(skeleton).strip(), []):
            value = unmask(template, tokens) if count == len(tokens) else None
            if value is not None:
                candidates.append((entry, value))
    if not candidates:
        return None
    candidates.sort(key=lambda item: -REVIEW_RANK.get(item[0].get('review'), 0))
    wanted = (app or '').casefold()
    if wanted:
        for entry, value in candidates:
            if (entry.get('app') or '').casefold() == wanted:
                return value
    if context:
        for entry, value in candidates:
            if _context_matches(entry, context):
                return value
    for entry, value in candidates:
        if ((entry.get('app') or '').casefold() in GENERIC_APPS or not entry.get('app')) \
                and REVIEW_RANK.get(entry.get('review'), 0) >= REVIEW_RANK['ai-reviewed']:
            return value
    by_meaning = {}
    for entry, value in candidates:
        by_meaning.setdefault(meaning(value), set()).add((entry.get('app') or '').casefold())
    if len(by_meaning) > 1:
        apps = set().union(*by_meaning.values())
        if len(apps) > 1:
            return None
    # One meaning, or a single application's variants: the most trusted, then the most frequent wording.
    best = REVIEW_RANK.get(candidates[0][0].get('review'), 0)
    top = [value for entry, value in candidates if REVIEW_RANK.get(entry.get('review'), 0) == best]
    counts = {}
    for value in top:
        counts[value] = counts.get(value, 0) + 1
    return max(top, key=lambda value: counts[value])


def signature(text):
    return sorted(SIGNATURE.findall(text))


def _direct(text):
    key = normalize(text)
    if key in WORDS:
        return WORDS[key]
    skeleton, tokens = mask(text)
    if tokens:
        template = WORDS.get(normalize(skeleton))
        if template is not None:
            return unmask(template, tokens)
    return None


def _cased(text):
    """Catalogs mix sentence case and lower case for the same label."""
    if not text[:1].isalpha():
        return None
    swapped = text[0].swapcase() + text[1:]
    result = _direct(swapped)
    if result is None or not result[:1].isalpha():
        return result
    return result[0].upper() + result[1:] if text[0].isupper() else result[0].lower() + result[1:]


def _accelerator(text, resolve):
    """KDE uses `&`, GTK uses `_`. Keep the shortcut letter when the translation has it."""
    marks = list(ACCELERATOR.finditer(text))
    if not marks:
        return None
    letter = text[marks[0].end()]
    result = resolve(ACCELERATOR.sub('', text))
    if result is None:
        return None
    position = result.lower().find(letter.lower())
    if position < 0:
        position = next((index for index, char in enumerate(result) if char.isalpha()), -1)
    if position < 0:
        return result
    return result[:position] + text[marks[0].start():marks[0].end()] + result[position:]


def _segments(text, resolve):
    """Translate composed labels such as `Settings — General` part by part."""
    parts = SEPARATORS.split(text)
    if len(parts) < 3:
        return None
    output = []
    changed = False
    for index, part in enumerate(parts):
        if index % 2:
            # Keep the source's spacing; Corsican, like French, puts a space before `:`.
            output.append(part)
            continue
        if not part.strip() or not re.search(r'[^\W\d_]', normalize(part)):
            output.append(part)
            continue
        result = resolve(part.strip())
        if result is None:
            return None
        changed = True
        output.append(part.replace(part.strip(), result, 1))
    return ''.join(output) if changed else None


def _resolve(text, segments=True):
    result = _direct(text)
    if result is not None:
        return result
    for opening, closing in WRAPPERS:
        if len(text) > 2 and text.startswith(opening) and text.endswith(closing):
            inner = _resolve(text[len(opening):-len(closing)], segments)
            if inner is not None:
                return opening + inner + closing
    trailing = TRAILING.match(text)
    if trailing and trailing[1].strip():
        inner = _resolve(trailing[1].rstrip(), False)
        if inner is not None:
            # Corsican typography, as used by the Mozilla and Weblate translators, keeps a space before
            # `:`, `?`, `!` and `;`, so the source's spacing is kept.
            return inner + trailing[2]
    accelerated = _accelerator(text, lambda value: _resolve(value, False))
    if accelerated is not None:
        return accelerated
    result = _cased(text)
    if result is not None:
        return result
    if segments:
        return _segments(text, lambda value: _resolve(value, False))
    return None


def translate(value):
    """Translate one whole label. Preserve surrounding whitespace and every placeholder."""
    if not value or not value.strip():
        return value
    core = value.strip()
    leading = value[:len(value) - len(value.lstrip())]
    trailing = value[len(value.rstrip()):]
    result = _resolve(core)
    if result is None or result == core or signature(core) != signature(result):
        return value
    return leading + result + trailing


def translated(value):
    return translate(value) != value


def read_mo(data):
    """Parse a gettext catalog into raw msgid/msgstr byte pairs, contexts and plurals kept."""
    if data[:4] == b'\xde\x12\x04\x95':
        order = '<'
    elif data[:4] == b'\x95\x04\x12\xde':
        order = '>'
    else:
        raise ValueError('Not a gettext .mo catalog')
    _, _, count, ids, values = struct.unpack(order + '5I', data[:20])
    entries = {}
    for index in range(count):
        key_length, key_offset = struct.unpack(order + '2I', data[ids + 8 * index:ids + 8 * index + 8])
        value_length, value_offset = struct.unpack(order + '2I', data[values + 8 * index:values + 8 * index + 8])
        entries[data[key_offset:key_offset + key_length]] = data[value_offset:value_offset + value_length]
    return entries


def make_mo(entries):
    """Serialise raw msgid/msgstr byte pairs into a little-endian gettext catalog."""
    pairs = sorted((key if isinstance(key, bytes) else key.encode(),
                    value if isinstance(value, bytes) else value.encode())
                   for key, value in entries.items())
    count = len(pairs)
    ids = b''
    values = b''
    id_table = []
    value_table = []
    start = 28 + 16 * count
    for key, _ in pairs:
        id_table.append((len(key), start + len(ids)))
        ids += key + b'\0'
    for _, value in pairs:
        value_table.append((len(value), start + len(ids) + len(values)))
        values += value + b'\0'
    header = struct.pack('<7I', 0x950412de, 0, count, 28, 28 + 8 * count, 0, 0)
    return header + b''.join(struct.pack('<2I', *row) for row in id_table + value_table) + ids + values


QM_MAGIC = bytes.fromhex('3cb86418caef9c95cd211cbf60a1bddd')
QM_SECTIONS = {'contexts': 0x2f, 'hashes': 0x42, 'messages': 0x69, 'numerus': 0x88,
               'dependencies': 0x96, 'language': 0xa7}
QM_END, QM_OBSOLETE, QM_TRANSLATION = 1, 5, 3
QM_SOURCE, QM_CONTEXT, QM_COMMENT = 6, 7, 8
# nplurals=2; plural=(n != 1): singular only for exactly one, as in Corsican and Italian.
QM_NUMERUS_RULES = b'\x01\x01'


def elf_hash(data):
    """Qt's message hash over source text followed by comment."""
    value = 0
    for byte in data:
        value = (value << 4) + byte
        carry = value & 0xf0000000
        if carry:
            value ^= carry >> 24
        value &= ~carry & 0xffffffff
    return value or 1


def read_qm(data):
    """Parse a Qt catalog into context/source/comment/translation records."""
    if data[:16] != QM_MAGIC:
        raise ValueError('Not a Qt .qm catalog')
    sections = {}
    position = 16
    while position + 5 <= len(data):
        tag = data[position]
        length = struct.unpack('>I', data[position + 1:position + 5])[0]
        sections[tag] = data[position + 5:position + 5 + length]
        position += 5 + length
    block = sections.get(QM_SECTIONS['messages'], b'')
    messages = []
    record = {'translations': []}
    position = 0
    while position < len(block):
        tag = block[position]
        position += 1
        if tag == QM_END:
            messages.append(record)
            record = {'translations': []}
            continue
        if tag == QM_OBSOLETE:
            position += 4
            continue
        length = struct.unpack('>I', block[position:position + 4])[0]
        position += 4
        payload = block[position:position + length]
        position += length
        if tag == QM_TRANSLATION:
            record['translations'].append(payload.decode('utf-16-be'))
        elif tag == QM_SOURCE:
            record['source'] = payload.decode('utf-8')
        elif tag == QM_CONTEXT:
            record['context'] = payload.decode('utf-8')
        elif tag == QM_COMMENT:
            record['comment'] = payload.decode('utf-8')
    return {'language': sections.get(QM_SECTIONS['language'], b'').decode('utf-8'),
            'numerus': sections.get(QM_SECTIONS['numerus'], b''),
            'messages': messages}


def make_qm(messages, language='co'):
    """Serialise Qt messages, including the hash index QTranslator binary searches."""
    block = b''
    index = []

    def entry(tag, payload):
        return bytes([tag]) + struct.pack('>I', len(payload)) + payload

    for message in messages:
        source = message.get('source', '')
        comment = message.get('comment', '')
        offset = len(block)
        record = b''
        for translation in message['translations']:
            record += entry(QM_TRANSLATION, translation.encode('utf-16-be'))
        record += entry(QM_SOURCE, source.encode('utf-8'))
        if 'context' in message:
            record += entry(QM_CONTEXT, message['context'].encode('utf-8'))
        if comment:
            record += entry(QM_COMMENT, comment.encode('utf-8'))
        block += record + bytes([QM_END])
        index.append((elf_hash((source + comment).encode('utf-8')), offset))
    hashes = b''.join(struct.pack('>2I', *row) for row in sorted(index))
    output = QM_MAGIC
    for name, payload in (('language', language.encode('utf-8')),
                          ('hashes', hashes),
                          ('messages', block),
                          ('numerus', QM_NUMERUS_RULES)):
        output += bytes([QM_SECTIONS[name]]) + struct.pack('>I', len(payload)) + payload
    return output


def read_pak(data):
    """Parse a Chromium data pack (version 4 or 5) into encoding, resources and aliases."""
    version = struct.unpack_from('<I', data)[0]
    if version == 5:
        encoding, count, alias_count = struct.unpack_from('<IHH', data, 4)
        table = 12
        wide_count, wide_aliases = struct.unpack_from('<II', data, 8)
        if struct.unpack_from('<I', data, table + 2)[0] != table + 6 * (count + 1) + 4 * alias_count \
                and struct.unpack_from('<I', data, 20)[0] == 16 + 8 * (wide_count + 1) + 8 * wide_aliases:
            return read_wide_pak(data, encoding & 0xff, wide_count, wide_aliases)
    elif version == 4:
        count, encoding = struct.unpack_from('<IB', data, 4)
        alias_count, table = 0, 9
    else:
        raise ValueError(f'Unsupported .pak version {version}')
    entries = [struct.unpack_from('<HI', data, table + 6 * index) for index in range(count + 1)]
    resources = {entries[index][0]: data[entries[index][1]:entries[index + 1][1]] for index in range(count)}
    aliases = {}
    start = table + 6 * (count + 1)
    for index in range(alias_count):
        alias, target = struct.unpack_from('<HH', data, start + 4 * index)
        aliases[alias] = entries[target][0]
    return {'version': version, 'encoding': encoding, 'resources': resources, 'aliases': aliases}


def read_wide_pak(data, encoding, count, alias_count):
    """Microsoft Edge's variant of version 5: 32-bit counts, resource ids and alias entries."""
    entries = [struct.unpack_from('<II', data, 16 + 8 * index) for index in range(count + 1)]
    resources = {entries[index][0]: data[entries[index][1]:entries[index + 1][1]] for index in range(count)}
    start = 16 + 8 * (count + 1)
    aliases = {}
    for index in range(alias_count):
        alias, target = struct.unpack_from('<II', data, start + 8 * index)
        aliases[alias] = entries[target][0]
    return {'version': 5, 'wide': True, 'encoding': encoding, 'resources': resources, 'aliases': aliases}


def make_pak(pak):
    """Write a version 5 data pack; aliases keep pointing at their original resources."""
    if pak.get('wide'):
        return make_wide_pak(pak)
    ids = sorted(pak['resources'])
    position = {resource: index for index, resource in enumerate(ids)}
    aliases = sorted(pak['aliases'].items())
    offset = 12 + 6 * (len(ids) + 1) + 4 * len(aliases)
    header = struct.pack('<IIHH', 5, pak['encoding'], len(ids), len(aliases))
    table, body = [], []
    for resource in ids:
        table.append(struct.pack('<HI', resource, offset))
        body.append(pak['resources'][resource])
        offset += len(pak['resources'][resource])
    table.append(struct.pack('<HI', 0, offset))
    alias_table = [struct.pack('<HH', alias, position[target]) for alias, target in aliases]
    return header + b''.join(table) + b''.join(alias_table) + b''.join(body)


def make_wide_pak(pak):
    ids = sorted(pak['resources'])
    position = {resource: index for index, resource in enumerate(ids)}
    aliases = sorted(pak['aliases'].items())
    offset = 16 + 8 * (len(ids) + 1) + 8 * len(aliases)
    output = [struct.pack('<IIII', 5, pak['encoding'], len(ids), len(aliases))]
    for resource in ids:
        output.append(struct.pack('<II', resource, offset))
        offset += len(pak['resources'][resource])
    output.append(struct.pack('<II', 0, offset))
    output.extend(struct.pack('<II', alias, position[target]) for alias, target in aliases)
    output.extend(pak['resources'][resource] for resource in ids)
    return b''.join(output)
