#!/usr/bin/env python3
"""Inventory of the Discord French strings the Corsu plugin translates, for a linguistic reviewer.

Usage: python3 -I tools/discord_inventory.py CLIENT_DIR DICTIONARY_JSON OUTPUT_TSV
CLIENT_DIR holds a copy of Discord's public web client, downloaded beforehand by hand or by a small script (never by
this one): web.<hash>.js and its lazy chunks under CLIENT_DIR/all/ named as the client's own chunk map names them
(<id>.<hash>.js or <hash>.js). Those files are untrusted data: they are only read as text here, never run.
DICTIONARY_JSON is the built plugin's dictionary (Vencord/src/userplugins/corsu/dictionary.json after
installer.prepare_build()). One row per French catalogue string whose text (or its placeholder template) is a key of
that dictionary, with the English, the Corsican, where the client code uses the key, the lexicon row it comes from
(the first source application_words('Discord', 'Vencord') reads it from, a person's own corrections left out) and a
cross-application flag. See docs/discord-inventory-0.28.2.md.
"""
import csv
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
import engine  # noqa: E402

PAIR = re.compile(r'"([A-Za-z0-9+/]{6})":(\[.*?\])(?=,"[A-Za-z0-9+/]{6}":|\})')
USE = re.compile(r'\.(?:t|default)(?:\.([A-Za-z0-9_$]{6})\b|\["([A-Za-z0-9+/]{6})"\])')
PROP = re.compile(r'(?:"([\w-]+)"|\b(\w+)):\s*(?:\(0,\s*)?\w+\.intl\.\w+\)?\(\s*\w+$')
NAV = re.compile(r'navId:"([\w-]+)"|displayName="(\w+)"|analyticsName:"(\w+)"|location:"([\w -]+)"')

# Priority order asked by the maintainer: one batch per action verb (French stems), then the removal and leaving
# labels, then the rest by 400 rows.
VERBS = [('rechercher', r'\b(re)?cherch'), ('envoyer', r'\benvo[iy]'), ('ajouter', r'\bajout'),
         ('retirer', r'\bretir'), ('supprimer', r'\bsupprim'), ('quitter', r'\bquitt'), ('rejoindre', r'\brejoi'),
         ('inviter', r'\binvit'), ('bloquer', r'\bbloqu'), ('signaler', r'\bsignal'), ('épingler', r'épingl'),
         ('modifier', r'\bmodifi'), ('enregistrer', r'\benregistr'), ('réinitialiser', r'\bréinitialis')]
REMOVAL = re.compile(r'\b(exclu|expuls|banni|bannir|débanni|révoqu)', re.I)
CROSS_SECTIONS = ('Firefox', 'Chrome', 'Opera', 'KDE', 'Qt', 'Google', 'Installed', 'File types')


def flat(node):
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        if node and node[0] == 1 and len(node) >= 2 and isinstance(node[1], str):
            return '{' + node[1] + '}'
        if node and node[0] == 8 and len(node) >= 3:
            return flat(node[2])
        if node and isinstance(node[0], int):
            return '{' + str(node[1]) + '}' if len(node) > 1 else ''
        return ''.join(flat(n) for n in node)
    return ''


def catalogue(files):
    out = {}
    for name in files:
        text = Path(name).read_text(encoding='utf-8', errors='replace')
        for key, value in PAIR.findall(text):
            if key in out:
                continue
            try:
                out[key] = flat(json.loads(re.sub(r'\\x([0-9a-fA-F]{2})', r'\\u00\1', value).replace("\\'", "'")))
            except ValueError:
                continue
    return out


def locale_files(client, web, locale):
    u = web[web.index('.u=e=>'):]
    u = u[:u.index(';')]
    special = dict(re.findall(r'"(\d+)"===e\?""\+e\+"\.([0-9a-f]{16})\.js"', u))
    table = dict(re.findall(r'(\d+):"([0-9a-f]{16})"', u))
    ids = set(re.findall(r'"?' + re.escape(locale) + r'"?:\(\)=>[a-zA-Z.]+\("(\d+)"\)', web))
    return [Path(client, 'all', f'{i}.{special[i]}.js' if i in special else f'{table[i]}.js') for i in ids]


def function_of(prop, around):
    prop = (prop or '').lower()
    if prop in ('placeholder',):
        return 'placeholder'
    if prop in ('aria-label', 'arialabel', 'accessibilitylabel'):
        return 'accessibility label'
    if prop in ('title', 'header', 'heading', 'modaltitle'):
        return 'title'
    if prop in ('description', 'subtitle', 'body', 'helptext', 'note', 'subtext', 'hint', 'instructions'):
        return 'description / instruction'
    if prop in ('tooltip', 'tooltiptext', 'text') and 'toast' in around.lower():
        return 'notification (toast)'
    if prop in ('tooltip', 'tooltiptext'):
        return 'tooltip'
    if prop == 'label' and ('menuitem' in around.lower() or 'navId' in around or '.iD,' in around or 'MenuItem' in around):
        return 'menu item'
    if prop == 'label':
        return 'label (option, field or menu item)'
    if prop in ('children', 'text', 'buttontext', 'submittext', 'confirmtext', 'canceltext'):
        return 'button or text' if 'button' in around.lower() or prop != 'children' else 'text'
    if prop:
        return 'prop ' + prop
    return 'formatted text'


def usages(client, keys):
    found = {}
    for name in [*glob.glob(os.path.join(client, 'web*.js')), *glob.glob(os.path.join(client, 'all', '*.js'))]:
        text = Path(name).read_text(encoding='utf-8', errors='replace')
        if '.intl.' not in text:
            continue
        for match in USE.finditer(text):
            key = match.group(1) or match.group(2)
            if key not in keys:
                continue
            if len(found.get(key, [])) >= 3:
                continue
            before = text[max(0, match.start() - 160):match.start()]
            prop = PROP.search(before)
            around = text[max(0, match.start() - 600):match.end() + 200]
            nav = None
            for nav in NAV.finditer(text, max(0, match.start() - 3000), match.start()):
                pass
            where = Path(name).name.split('.')[0] + ('' if nav is None else ' ' + next(g for g in nav.groups() if g))
            found.setdefault(key, []).append((function_of(prop and (prop.group(1) or prop.group(2)), around), where))
    return found


def provenance():
    """normalized source (or its template) -> (path:line, section, english, french, corsican), first reader wins,
    in application_words('Discord', 'Vencord') order (a person's own corrections left out)."""
    origin = {}

    def add(path, number, section, english, french, corsican):
        for source in (english, french):
            if not source:
                continue
            row = (f'{Path(path).relative_to(ROOT)}:{number}', section, english, french, corsican)
            origin.setdefault(engine.normalize(source), row)
            skeleton, tokens = engine.mask(source)
            if tokens and engine.remask(corsican, tokens) is not None:
                origin.setdefault(engine.normalize(skeleton), row)

    def lines(path, only=None, imported=False):
        section, inside, heading = '', only is None, False
        for number, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
            if line.startswith('#') and (line.startswith('# ') or line.strip() == '#' or line.count('|') != 2):
                if line.startswith('# '):
                    # A heading's first line names the section; the lines under it continue its text.
                    if not heading and not line.startswith('# English | French'):
                        section = re.split(r'[:—(]', line[2:])[0].strip()[:60]
                    if only is not None:
                        inside = line.startswith(f'# {only}:')
                heading = not line.startswith('# English | French')
                continue
            heading = False
            if not line.strip() or not inside:
                continue
            fields = [field.strip() for field in line.split('|')]
            if len(fields) != 3 or not fields[2]:
                continue
            english, french, corsican = fields
            if imported and english and french and engine.loose_french(english, french, corsican):
                french = ''
            yield number, section, english, french, corsican

    for number, section, *row in lines(engine.FIXES):
        add(engine.FIXES, number, 'lexicon-fixes', *row)
    for name in ('Discord', 'Vencord'):
        for number, section, *row in lines(engine.LEXICON, name):
            add(engine.LEXICON, number, name, *row)
    for entry in engine.memory_entries(exported=False):
        if (entry.get('app') or '').casefold() in ('discord', 'vencord') and not engine._from_lexicon(entry) \
                and engine.REVIEW_RANK.get(entry.get('review'), 0) >= engine.REVIEW_RANK['ai-reviewed'] \
                and isinstance(entry.get('target'), str):
            path = (entry.get('origin') or {}).get('path') or 'lexicon/memory'
            add(ROOT / 'lexicon/memory/x', 0, 'memory ' + path, entry['source'] if entry.get('source_lang') == 'en' else '',
                entry.get('source_fr') or '', entry['target'])
    for path in [engine.FIXES, *engine.REVIEWED, engine.LEXICON]:
        for number, section, *row in lines(path, imported=path in engine.REVIEWED):
            add(path, number, section or Path(path).name, *row)
    return origin


def batch_of(french):
    lower = french.lower()
    for index, (verb, stem) in enumerate(VERBS, 1):
        if re.search(stem, lower):
            return f'{index:02d}', verb
    if REMOVAL.search(lower):
        return f'{len(VERBS) + 1:02d}', 'exclure/expulser/bannir'
    return None, ''


def main(client, dictionary_path, output):
    web_name = sorted(glob.glob(os.path.join(client, 'web.*.js')))[0]
    web = Path(web_name).read_text(encoding='utf-8', errors='replace')
    french = catalogue(locale_files(client, web, 'fr'))
    english = catalogue(locale_files(client, web, 'en-US'))
    words = json.loads(Path(dictionary_path).read_text(encoding='utf-8'))
    origin = provenance()
    used = usages(client, french)
    rows = []
    for key, text in french.items():
        source = engine.normalize(text)
        how = 'direct' if source in words else None
        lookup = source
        if how is None:
            skeleton, tokens = engine.mask(text)
            if tokens and engine.normalize(skeleton) in words:
                how, lookup = 'template', engine.normalize(skeleton)
        if how is None:
            continue
        corsican = words[lookup]
        if how == 'template':
            corsican = engine.unmask(corsican, engine.mask(text)[1]) or corsican
        row = origin.get(lookup)
        where = used.get(key, [])
        functions = sorted({f for f, _ in where}) or ['not found in the client code']
        places = sorted({w for _, w in where})
        cross, reason = '', ''
        if row and row[1] not in ('Discord', 'Vencord', 'lexicon-fixes'):
            cross = 'cross-app'
            reasons = [f'Corsican from section "{row[1]}" ({row[0]})']
            discord_english = english.get(key, '')
            if row[2] and discord_english and engine.normalize(row[2]).casefold() != engine.normalize(discord_english).casefold():
                reasons.append(f'that row\'s English is "{row[2]}", Discord\'s is "{discord_english}"')
            if len(text.split()) <= 2:
                reasons.append('short label: its sense depends on where Discord shows it')
            reason = '; '.join(reasons)
        number, verb = batch_of(text)
        rows.append({'batch': number, 'priority': verb, 'key': key, 'english': english.get(key, ''), 'french': text,
                     'corsican': corsican.replace('\x00', ''), 'match': how, 'function': '; '.join(functions),
                     'component': '; '.join(places), 'lexicon_row': row[0] if row else '',
                     'lexicon_section': row[1] if row else '', 'cross_app': cross, 'cross_app_reason': reason})
    rest = sorted((r for r in rows if r['batch'] is None), key=lambda r: (r['cross_app'] == '', r['french'].lower()))
    start = len(VERBS) + 2
    for index, row in enumerate(rest):
        row['batch'] = f'{start + index // 400:02d}'
    rows.sort(key=lambda r: (r['batch'], r['cross_app'] == '', r['french'].lower()))
    with open(output, 'w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n',
                                quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)
    counts = {}
    for row in rows:
        counts[row['batch'], row['priority']] = counts.get((row['batch'], row['priority']), 0) + 1
    print(f'{len(rows)} rows ({len(french)} French strings in the catalogue), '
          f'{sum(1 for r in rows if r["cross_app"])} cross-app')
    for (number, verb), count in sorted(counts.items()):
        print(f'batch {number} {verb or "rest"}: {count}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
