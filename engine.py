#!/usr/bin/env python3
"""Corsican translation engine: lexicon lookup, placeholder templates and catalog formats.

Everything is local and deterministic. No network access, no machine translation and no
access to user documents or messages. Only whole interface labels are translated; when a
label is unknown it is returned unchanged.
"""
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEXICON = ROOT / 'lexicon.tsv'

# Placeholders that must survive translation untouched: Fluent placeables, printf
# specifiers, Qt/KDE numbered arguments and shell-style variables.
PLACEHOLDER = re.compile(
    r'\{\s*[$-]?[\w.-]+(?:\([^{}]*\))?\s*\}'
    r'|%(?:\d+\$)?[0-9]*\.?[0-9]*(?:ll|l|h)?[sdiufgexXop]'
    r'|%[Ln]?\d+'
    r'|%[Ln]\b'
    r'|\$\{[A-Za-z_]\w*\}'
    r'|\$[A-Za-z_]\w*'
    r'|\{\d+\}'
)
# Markup and entities are contracts with the application, never translated content.
SIGNATURE = re.compile(r'%(?:\d+\$)?[0-9]*\.?[0-9]*(?:ll|l|h)?[sdiufgexXop]|%[Ln]?\d+|</?[A-Za-z][^>]*>|&[a-zA-Z]+;|\{[^{}]*\}')
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


def load_lexicon(path=None):
    """Read `English|French|Corsican` rows into direct and templated lookup tables."""
    words = {}
    lines = Path(path or LEXICON).read_text(encoding='utf-8').splitlines()
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.startswith('#'):
            continue
        fields = line.split('|')
        if len(fields) != 3:
            raise ValueError(f'{LEXICON}:{number}: expected English|French|Corsican')
        english, french, corsican = (field.strip() for field in fields)
        if not corsican:
            continue
        for source in (english, french):
            if not source:
                continue
            words.setdefault(normalize(source), corsican)
            skeleton, tokens = mask(source)
            if tokens:
                template = remask(corsican, tokens)
                if template is not None:
                    words.setdefault(normalize(skeleton), template)
    return words


WORDS = load_lexicon()


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
            # Italian-style spacing for the colon separator as well.
            output.append(part.lstrip(' \u00a0\u202f') if ':' in part else part)
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
            # Corsican follows Italian spacing: no blank before `:`, `?`, `!` or `;`.
            return inner + trailing[2].lstrip(' \u00a0\u202f\t')
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
