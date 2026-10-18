#!/usr/bin/env python3
"""Contextual translation memory: extract, match, measure, update and export the strings of one integration.

    tm.py extract <po|android|xliff|json> <file> --app NAME [--lang en] [--out work.jsonl]
    tm.py match <work.jsonl> [--out matched.jsonl] [--memory lexicon/memory]
    tm.py stats <work.jsonl>
    tm.py update <old.jsonl> <new.jsonl> [--out updated.jsonl]
    tm.py po <work.jsonl> --out x.po

A working file uses the format of lexicon/memory/*.jsonl (see lexicon/memory/README.md): one JSON object per
string, with its key, context, placeholders and origin. `match` only fills a target when the reuse is safe: same
source text and (same application, or same context, or one unambiguous translation whose placeholders match).
Close matches are listed as suggestions and never applied; different translations of the same text from different
programs are listed as conflicts.
"""
import argparse
from collections import Counter, defaultdict
import datetime
import difflib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
import engine  # noqa: E402

FIELDS = ('app', 'component', 'key', 'context', 'source_lang', 'source', 'source_fr', 'target', 'plural', 'params',
          'origin', 'version', 'license', 'review', 'fetched')
REVIEWED = engine.REVIEW_RANK
FUZZY = 0.85


# --- native formats -------------------------------------------------------------------------------------------------

def unquote(value):
    """A PO string literal; JSON reads nearly all of them, the rest get the usual C escapes."""
    try:
        return json.loads(value)
    except ValueError:
        body = value.strip()[1:-1] if value.strip().endswith('"') else value.strip()[1:]
        return body.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')


def po_entries(data, translated=True):
    """Entries of a PO catalog keyed by (msgctxt, msgid): context, plurals and comments kept, fuzzy ones skipped.

    Each value is {msgctxt, msgid, msgid_plural, msgstr (a string, or a list of plural forms), comments, references}.
    With translated=True (the default) untranslated entries are left out."""
    if isinstance(data, bytes):
        data = data.decode('utf-8', 'replace')
    result = {}
    entry, field, fuzzy = {}, None, False

    def flush():
        if 'msgid' not in entry or fuzzy or not entry['msgid']:
            return
        if 'msgid_plural' in entry:
            forms = [entry['msgstr[]'][index] for index in sorted(entry.get('msgstr[]', {}))]
            value = forms if forms and all(forms) else None
        else:
            value = entry.get('msgstr') or None
        if translated and value is None:
            return
        result[(entry.get('msgctxt'), entry['msgid'])] = {
            'msgctxt': entry.get('msgctxt'), 'msgid': entry['msgid'], 'msgid_plural': entry.get('msgid_plural'),
            'msgstr': value, 'comments': entry.get('comments', []), 'references': entry.get('references', [])}

    for line in data.splitlines() + ['']:
        line = line.strip()
        if not line:
            # Flags and comments never outlive their block, even an obsolete (#~) one without msgid.
            flush()
            entry, field, fuzzy = {}, None, False
            continue
        if ('msgstr' in entry or 'msgstr[]' in entry) and line.startswith(('#', 'msgctxt ', 'msgid ')):
            # A new entry without a blank line before it.
            flush()
            entry, field, fuzzy = {}, None, False
        if line.startswith('#~'):
            field = None
            continue
        if line.startswith('#,'):
            fuzzy = fuzzy or 'fuzzy' in line
        elif line.startswith('#.'):
            entry.setdefault('comments', []).append(line[2:].strip())
        elif line.startswith('#:'):
            entry.setdefault('references', []).extend(line[2:].split())
        elif line.startswith('#'):
            continue
        elif line.startswith('msgstr['):
            index, _, value = line[len('msgstr['):].partition(']')
            field = ('msgstr[]', int(index))
            entry.setdefault('msgstr[]', {})[int(index)] = unquote(value.strip())
        elif line.startswith(('msgid_plural ', 'msgid ', 'msgstr ', 'msgctxt ')):
            name, _, value = line.partition(' ')
            field = name
            entry[name] = unquote(value.strip())
        elif line.startswith('"') and field:
            if isinstance(field, tuple):
                entry['msgstr[]'][field[1]] += unquote(line)
            else:
                entry[field] += unquote(line)
    return result


def android_text(element):
    text = ''.join(element.itertext()).strip()
    if len(text) > 1 and text[0] == text[-1] == '"':
        text = text[1:-1]
    return text.replace("\\'", "'").replace('\\"', '"').replace('\\n', ' ').replace('\\@', '@')


def android_entries(data):
    """name -> {text, comment, plural}: <string> and <plurals> resources (quantity -> text), with the XML comment
    written just before each one."""
    root = ET.fromstring(data, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    result, comment = {}, None
    for element in root:
        if element.tag is ET.Comment:
            comment = (element.text or '').strip() or None
            continue
        name = element.get('name')
        if element.tag == 'string' and name:
            result[name] = {'text': android_text(element), 'comment': comment, 'plural': None}
        elif element.tag == 'plurals' and name:
            forms = {item.get('quantity'): android_text(item) for item in element.iter('item')}
            if forms:
                text = forms.get('one') or forms.get('other') or next(iter(forms.values()))
                result[name] = {'text': text, 'comment': comment, 'plural': forms}
        comment = None
    return result


def xliff_entries(data):
    """(file original, trans-unit id) -> {source, target, note}."""
    result = {}
    root = ET.fromstring(data)
    for file in root.iter():
        if not file.tag.endswith('}file') and file.tag != 'file':
            continue
        original = file.get('original') or ''
        for unit in file.iter():
            if not unit.tag.endswith('trans-unit'):
                continue
            values = {'source': None, 'target': None, 'note': None}
            for child in unit:
                name = child.tag.rsplit('}', 1)[-1]
                if name in values:
                    values[name] = ''.join(child.itertext())
            if values['source']:
                result[(original, unit.get('id'))] = values
    return result


def json_entries(data):
    """Flat or nested JSON string tables: dotted key -> text (Minecraft, i18next, Chrome's {message} objects)."""
    result = {}

    def walk(value, path):
        if isinstance(value, str):
            result[path] = value
        elif isinstance(value, dict):
            if isinstance(value.get('message'), str):
                result[path] = value['message']
                return
            for key, child in value.items():
                walk(child, f'{path}.{key}' if path else key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f'{path}[{index}]')

    walk(json.loads(data), '')
    return result


# --- memory files ---------------------------------------------------------------------------------------------------

def params(text):
    found = []
    for value in engine.PLACEHOLDER.findall(text or ''):
        if value not in found:
            found.append(value)
    return found


def make_entry(app, key, source, target=None, **fields):
    """A memory entry with every field present (None when unknown)."""
    entry = dict.fromkeys(FIELDS)
    entry.update(app=app, key=key, source=source, target=target, source_lang='en', params=params(source))
    entry.update(fields)
    return entry


def compact(entry, defaults):
    """Leave out what the file's defaults already say, and empty values (see lexicon/memory/README.md)."""
    result = {}
    for field, value in entry.items():
        if value in (None, [], {}, ''):
            continue
        default = defaults.get(field)
        if field == 'key' and value == entry.get('source'):
            continue
        if field == 'source_fr' and entry.get('source_lang') == 'fr' and value == entry.get('source'):
            continue
        if field == 'params' and value == params(entry.get('source')):
            continue
        if isinstance(value, dict) and isinstance(default, dict):
            value = {name: item for name, item in value.items() if default.get(name) != item}
            if not value:
                continue
        elif value == default:
            continue
        result[field] = value
    return result


def write_memory(path, entries, defaults=None):
    """Write entries as JSON lines; the first line holds the defaults shared by every entry of the file."""
    defaults = {name: value for name, value in (defaults or {}).items() if value not in (None, [], {}, '')}
    dump = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    lines = [dump({'_defaults': defaults})] if defaults else []
    lines += [dump(compact(entry, defaults)) for entry in entries]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8')


def read_memory(path):
    return list(engine.read_memory(path))


def write_work(path, entries):
    """Working files keep every field on every line: they are short and edited by hand."""
    Path(path).write_text(''.join(json.dumps(entry, ensure_ascii=False) + '\n' for entry in entries), encoding='utf-8')


# --- extract --------------------------------------------------------------------------------------------------------

def extract(kind, file, app, lang='en'):
    path = Path(file)
    data = path.read_bytes()
    today = datetime.date.today().isoformat()
    common = dict(component=path.name, source_lang=lang, origin={'path': str(file)}, fetched=today)
    entries = []
    if kind == 'po':
        for (context, msgid), item in po_entries(data, translated=False).items():
            plural = None
            if item['msgid_plural']:
                plural = {'source_plural': item['msgid_plural'],
                          'forms': [str(index) for index in range(len(item['msgstr'] or [0, 1]))]}
            context_info = {'msgctxt': context, 'comments': item['comments'] or None,
                            'references': item['references'] or None}
            entries.append(make_entry(app, msgid if context is None else f'{context}\x04{msgid}', msgid, item['msgstr'],
                                      context={k: v for k, v in context_info.items() if v}, plural=plural, **common))
    elif kind == 'android':
        for name, item in android_entries(data).items():
            plural = None
            target = None
            if item['plural']:
                plural = {'source_plural': item['plural'].get('other', item['text']), 'forms': list(item['plural'])}
            entries.append(make_entry(app, name, item['text'], target, plural=plural,
                                      context={'file': str(file), **({'comment': item['comment']} if item['comment'] else {})},
                                      **common))
    elif kind == 'xliff':
        for (original, unit), item in xliff_entries(data).items():
            context = {'file': original, **({'note': item['note']} if item['note'] else {})}
            entries.append(make_entry(app, unit, item['source'], item['target'] or None, context=context,
                                      **{**common, 'component': original or path.name}))
    elif kind == 'json':
        for key, text in json_entries(data).items():
            entries.append(make_entry(app, key, text, context={'file': str(file)}, **common))
    else:
        raise ValueError(f'unknown format {kind}')
    for entry in entries:
        entry['review'] = 'untranslated' if not entry['target'] else 'corsu-draft'
    return entries


# --- match ----------------------------------------------------------------------------------------------------------

def context_values(entry):
    context = entry.get('context')
    values = set()
    if isinstance(context, str):
        values.add(context)
    elif isinstance(context, dict):
        for name in ('msgctxt', 'file', 'section'):
            if context.get(name):
                values.add(context[name])
    return values


def first_form(target):
    return target[0] if isinstance(target, list) else target


class Memory:
    """Exact and fuzzy indexes over memory entries (lexicon/memory by default)."""

    def __init__(self, entries=None, directory=None):
        self.entries = list(entries) if entries is not None else engine.memory_entries(directory)
        self.exact = defaultdict(list)
        self.words = defaultdict(set)
        self.sources = []
        for entry in self.entries:
            # Plural sources are not indexed: an entry is matched on its singular source text.
            for source, _ in engine.memory_sources(entry)[:2]:
                if source != (entry.get('plural') or {}).get('source_plural'):
                    self.exact[engine.normalize(source).strip()].append(entry)
        for index, source in enumerate(self.exact):
            self.sources.append(source)
            for word in set(re.findall(r'\w{3,}', source.lower())):
                self.words[word].add(index)

    def similar(self, text, limit=3):
        text = engine.normalize(text).strip()
        words = sorted(set(re.findall(r'\w{3,}', text.lower())), key=lambda word: len(self.words.get(word, ())))
        candidates = set()
        for word in words[:3]:
            candidates |= self.words.get(word, set())
        scored = []
        for index in candidates:
            source = self.sources[index]
            if source == text or not 0.7 <= len(source) / max(len(text), 1) <= 1.4:
                continue
            matcher = difflib.SequenceMatcher(None, text, source)
            if matcher.real_quick_ratio() >= FUZZY and matcher.quick_ratio() >= FUZZY:
                ratio = matcher.ratio()
                if ratio >= FUZZY:
                    scored.append((ratio, source))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return scored[:limit]


def same_placeholders(entry, candidate):
    source = sorted(params(entry['source']))
    target = first_form(candidate['target'])
    return sorted(params(target)) == source and engine.signature(entry['source']) == engine.signature(target)


def match_entry(entry, memory):
    """Fill entry['target'] from compatible exact matches; record suggestions and conflicts in entry['match']."""
    if entry.get('target'):
        return entry
    key = engine.normalize(entry['source']).strip()
    plural = bool(entry.get('plural'))
    candidates = [candidate for candidate in memory.exact.get(key, [])
                  if bool(candidate.get('plural')) == plural and candidate is not entry
                  and not engine.app_only(candidate, entry.get('app'))]
    if candidates:
        app = (entry.get('app') or '').casefold()
        contexts = context_values(entry)
        ranked = sorted(candidates, key=lambda candidate: -REVIEWED.get(candidate.get('review'), 0))
        chosen = reason = None
        for candidate in ranked:
            if app and (candidate.get('app') or '').casefold() == app and same_placeholders(entry, candidate):
                chosen, reason = candidate, 'same-app'
                break
        if chosen is None and contexts:
            for candidate in ranked:
                if contexts & context_values(candidate) and same_placeholders(entry, candidate):
                    chosen, reason = candidate, 'same-context'
                    break
        distinct = {engine.meaning(first_form(candidate['target'])) for candidate in candidates}
        if chosen is None and len(distinct) == 1:
            if same_placeholders(entry, ranked[0]):
                chosen, reason = ranked[0], 'unambiguous'
        if chosen is not None:
            entry['target'] = chosen['target']
            same = reason == 'same-app'
            entry['review'] = chosen.get('review') if same else 'corsu-draft'
            entry['match'] = {'type': 'exact', 'reason': reason, 'from': chosen.get('app'),
                              'review': chosen.get('review')}
            return entry
        if len(distinct) > 1:
            # One option per meaning, with the applications that use it (most trusted wording first).
            options = {}
            for candidate in ranked:
                option = options.setdefault(engine.meaning(first_form(candidate['target'])), {
                    'target': candidate['target'], 'review': candidate.get('review'), 'apps': []})
                if candidate.get('app') not in option['apps']:
                    option['apps'].append(candidate.get('app'))
            entry['match'] = {'type': 'conflict',
                              'candidates': sorted(options.values(), key=lambda option: -len(option['apps']))}
            return entry
    suggestions = []
    for ratio, source in memory.similar(entry['source']):
        usable = [item for item in memory.exact[source] if not engine.app_only(item, entry.get('app'))]
        if not usable:
            continue
        candidate = max(usable, key=lambda item: REVIEWED.get(item.get('review'), 0))
        suggestions.append({'source': candidate.get('source'), 'target': candidate['target'],
                            'app': candidate.get('app'), 'ratio': round(ratio, 3)})
    if suggestions:
        entry['match'] = {'type': 'suggestion', 'suggestions': suggestions}
    return entry


def match(entries, memory):
    return [match_entry(entry, memory) for entry in entries]


def stats(entries):
    kinds = Counter((entry.get('match') or {}).get('type') for entry in entries)
    return {
        'entries': len(entries),
        'unique source strings': len({engine.normalize(entry['source']).strip() for entry in entries}),
        'exact compatible reuses': kinds['exact'],
        'suggestions': kinds['suggestion'],
        'conflicts': kinds['conflict'],
        'untranslated': sum(1 for entry in entries if not entry.get('target')),
    }


# --- update ---------------------------------------------------------------------------------------------------------

def identity(entry):
    context = entry.get('context')
    msgctxt = context.get('msgctxt') if isinstance(context, dict) else None
    return entry.get('component'), entry.get('key'), msgctxt


def update(old, new):
    """Mark each new entry added / changed / unchanged against the old file, and list removed ones. A changed
    source keeps its previous translation for reference, marked to-review."""
    before = {identity(entry): entry for entry in old}
    after = set()
    result = []
    for entry in new:
        key = identity(entry)
        after.add(key)
        previous = before.get(key)
        if previous is None:
            entry['change'] = 'added'
        elif previous.get('source') != entry.get('source') or \
                (previous.get('plural') or {}).get('source_plural') != (entry.get('plural') or {}).get('source_plural'):
            entry['change'] = 'changed'
            entry['previous_source'] = previous.get('source')
            if not entry.get('target') and previous.get('target'):
                entry['target'] = previous['target']
            entry['review'] = 'to-review'
        else:
            entry['change'] = 'unchanged'
            if not entry.get('target') and previous.get('target'):
                entry['target'] = previous['target']
                entry['review'] = previous.get('review')
        result.append(entry)
    for key, entry in before.items():
        if key not in after:
            result.append({**entry, 'change': 'removed'})
    return result


# --- po -------------------------------------------------------------------------------------------------------------

def po_string(text):
    escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\t', '\\t')
    lines = escaped.split('\n')
    if len(lines) == 1:
        return f'"{escaped}"'
    parts = [line + '\\n' for line in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    return '""\n' + '\n'.join(f'"{part}"' for part in parts)


def to_po(entries, language='co'):
    out = ['msgid ""', 'msgstr ""', '"Project-Id-Version: Corsu\\n"', '"MIME-Version: 1.0\\n"',
           '"Content-Type: text/plain; charset=UTF-8\\n"', '"Content-Transfer-Encoding: 8bit\\n"',
           f'"Language: {language}\\n"', '"Plural-Forms: nplurals=2; plural=(n != 1);\\n"', '']
    for entry in entries:
        if entry.get('change') == 'removed' or not entry.get('source'):
            continue
        context = entry.get('context') if isinstance(entry.get('context'), dict) else {}
        for comment in context.get('comments') or []:
            out.append(f'#. {comment}')
        if context.get('comment'):
            out.append(f'#. {context["comment"]}')
        if context.get('references'):
            out.append('#: ' + ' '.join(context['references']))
        flags = []
        if entry.get('review') in ('to-review',):
            flags.append('fuzzy')
        if flags:
            out.append('#, ' + ', '.join(flags))
        msgctxt = context.get('msgctxt')
        if msgctxt is None and entry.get('key') and entry['key'] != entry['source'] and '\x04' not in entry['key']:
            # Android names and XLIFF ids keep strings with the same text apart.
            msgctxt = entry['key']
        if msgctxt is not None:
            out.append('msgctxt ' + po_string(msgctxt))
        out.append('msgid ' + po_string(entry['source']))
        target = entry.get('target')
        if entry.get('plural'):
            out.append('msgid_plural ' + po_string(entry['plural'].get('source_plural') or entry['source']))
            forms = target if isinstance(target, list) else ([target] * 2 if target else ['', ''])
            if isinstance(target, dict):
                forms = [target.get('one', ''), target.get('other', '')]
            for index in range(2):
                value = forms[index] if index < len(forms) else forms[-1]
                out.append(f'msgstr[{index}] ' + po_string(value or ''))
        else:
            out.append('msgstr ' + po_string(first_form(target) or ''))
        out.append('')
    return '\n'.join(out)


# --- command line ---------------------------------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('extract')
    command.add_argument('kind', choices=('po', 'android', 'xliff', 'json'))
    command.add_argument('file')
    command.add_argument('--app', required=True)
    command.add_argument('--lang', default='en')
    command.add_argument('--out')
    command = commands.add_parser('match')
    command.add_argument('work')
    command.add_argument('--out')
    command.add_argument('--memory', help='memory directory (default lexicon/memory)')
    command = commands.add_parser('stats')
    command.add_argument('work')
    command = commands.add_parser('update')
    command.add_argument('old')
    command.add_argument('new')
    command.add_argument('--out')
    command = commands.add_parser('po')
    command.add_argument('work')
    command.add_argument('--out', required=True)
    args = parser.parse_args(argv)

    if args.command == 'extract':
        entries = extract(args.kind, args.file, args.app, args.lang)
        out = args.out or Path(args.file).with_suffix('.work.jsonl').name
        write_work(out, entries)
        print(f'{out}: {len(entries)} strings')
    elif args.command == 'match':
        entries = read_memory(args.work)
        memory = Memory(directory=Path(args.memory) if args.memory else None)
        entries = match(entries, memory)
        write_work(args.out or args.work, entries)
        for name, value in stats(entries).items():
            print(f'{name}: {value}')
    elif args.command == 'stats':
        entries = read_memory(args.work)
        for name, value in stats(entries).items():
            print(f'{name}: {value}')
        conflicts = [entry for entry in entries if (entry.get('match') or {}).get('type') == 'conflict']
        for entry in conflicts[:20]:
            options = ' / '.join(f'{first_form(option["target"])} ({", ".join(map(str, option["apps"]))})'
                                 for option in entry['match']['candidates'])
            print(f'  conflict: {entry["source"]!r} -> {options}')
    elif args.command == 'update':
        entries = update(read_memory(args.old), read_memory(args.new))
        write_work(args.out or args.new, entries)
        counts = Counter(entry['change'] for entry in entries)
        print(', '.join(f'{name}: {counts[name]}' for name in ('added', 'changed', 'removed', 'unchanged')))
    elif args.command == 'po':
        Path(args.out).write_text(to_po(read_memory(args.work)), encoding='utf-8')
        print(args.out)


if __name__ == '__main__':
    main()
