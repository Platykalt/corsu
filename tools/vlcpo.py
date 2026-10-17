#!/usr/bin/env python3
"""VLC's Corsican catalogue (contrib/vlc): check every entry, track reviews, build an experimental vlc.mo.

  vlcpo.py check                 msgfmt with the fuzzy drafts included (--use-fuzzy -c --check-format) and Corsu's own
                                 rules on every draft: plural forms, printf / %@ / %1 arguments, markup tags, menu
                                 accelerators, surrounding spaces and line breaks; no draft may reuse an accelerator
                                 letter of its VLC menu (MENUS; clashes between upstream translations are only
                                 reported as NOTE). Exit 1 on any error.
  vlcpo.py status                counts per provenance and review status.
  vlcpo.py export OUT.jsonl      the drafts with their id, references and flags, for reviewing in batches.
  vlcpo.py merge PROPOSALS...    apply review proposals (JSONL: id, verdict keep|fix|uncertain, msgstr, note) to co.po
                                 and review.json; nothing else in co.po changes.
  vlcpo.py build OUT.mo [--include=STATUS,...]
                                 the experimental catalogue: upstream translations plus the drafts whose review status
                                 is listed in BUILD_STATUSES; uncertain drafts are left out. Never installed by this tool.

Provenance and review stay apart. co.po keeps upstream translations byte for byte; every Corsu draft keeps "#, fuzzy"
until a speaker validates it (gettext's own signal), and a "# Corsu:" comment saying its status. review.json records,
per draft id, the original draft, each review (who, when, verdict, note) and the current status:
ai_draft, ai_reviewed, uncertain, human. A speaker's validation removes the fuzzy flag but never the review record.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FOLDER = Path(os.environ.get('CORSU_VLC_FOLDER') or ROOT / 'contrib' / 'vlc')
CATALOG = FOLDER / 'co.po'
REVIEW = FOLDER / 'review.json'
BUILD_STATUSES = ('ai_reviewed', 'human')
COMMENT = '# Corsu: '
STATUS_COMMENT = {
    'ai_draft': 'AI draft, not reviewed',
    'ai_reviewed': 'AI draft, reviewed by AI, not validated by a speaker',
    'uncertain': 'AI draft, uncertain after AI review, left out of the experimental build',
    'human': 'AI draft, validated by a speaker',
}
# po/co.po of videolan/vlc 3.0.x at e66842dbd5223d41a8ad88f85ffce3637c57aa23: what co.po gives back without Corsu's
# entries (upstream(), checked by check()).
UPSTREAM_SHA256 = '40a245053d37537dcc377b69c50ca9d5da46e6f6d20eadcd57a169d95c17cddd'

sys.path.insert(0, str(ROOT / 'tools'))
from tm import unquote  # noqa: E402


class Entry:
    """One block of the catalogue, its lines kept as they are."""

    def __init__(self, lines):
        self.lines = lines
        self.fields = {}
        self.flags = []
        self.references = []
        self.corsu = None
        field = None
        for line in lines:
            if line.startswith('#,'):
                self.flags += [flag.strip() for flag in line[2:].split(',')]
            elif line.startswith('#:'):
                self.references += line[2:].split()
            elif line.startswith(COMMENT):
                self.corsu = line[len(COMMENT):]
            elif line.startswith('#'):
                continue
            elif line.startswith(('msgctxt ', 'msgid ', 'msgid_plural ', 'msgstr ', 'msgstr[')):
                field, _, value = line.partition(' ')
                self.fields[field] = unquote(value)
            elif line.startswith('"') and field:
                self.fields[field] += unquote(line)

    msgctxt = property(lambda self: self.fields.get('msgctxt'))
    msgid = property(lambda self: self.fields.get('msgid'))
    plural = property(lambda self: self.fields.get('msgid_plural'))
    fuzzy = property(lambda self: 'fuzzy' in self.flags)
    draft = property(lambda self: self.corsu is not None)

    @property
    def translations(self):
        if self.plural is None:
            return [self.fields.get('msgstr', '')]
        return [value for key, value in sorted(self.fields.items()) if key.startswith('msgstr[')]

    @property
    def id(self):
        key = (self.msgctxt + '\x04' if self.msgctxt is not None else '') + self.msgid
        return hashlib.sha1(key.encode('utf-8')).hexdigest()[:12]


def read(path=None):
    """(blocks, entries): blocks are line lists, entries the parsed blocks that have a msgid (the header included)."""
    blocks, current = [], []
    for line in (path or CATALOG).read_text(encoding='utf-8').split('\n'):
        if line:
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks, [Entry(block) for block in blocks if any(line.startswith('msgid ') for line in block)]


def write(blocks, path=None):
    (path or CATALOG).write_text('\n\n'.join('\n'.join(block) for block in blocks) + '\n', encoding='utf-8')


def po_string(text, prefix):
    """msgstr lines as gettext tools write them: one line when short, else "" then pieces cut after spaces or \\n."""
    escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\t', '\\t')
    pieces = []
    for part in re.split(r'(?<=\n)', escaped):
        if not part:
            continue
        part = part.replace('\n', '\\n')
        while len(part) > 77:
            cut = part.rfind(' ', 0, 77)
            cut = cut + 1 if cut > 0 else 77
            pieces.append(part[:cut])
            part = part[cut:]
        pieces.append(part)
    if len(pieces) == 1 and len(prefix) + len(pieces[0]) + 3 <= 79:
        return [f'{prefix} "{pieces[0]}"']
    return [f'{prefix} ""'] + [f'"{piece}"' for piece in pieces]


def load_review():
    return json.loads(REVIEW.read_text(encoding='utf-8')) if REVIEW.exists() else {}


def save_review(review):
    REVIEW.write_text(json.dumps(review, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')


def status(entry, review):
    if not entry.draft:
        return 'upstream'
    return review.get(entry.id, {}).get('status', 'ai_draft')


# Checks ---------------------------------------------------------------------------------------------------------

PRINTF = re.compile(r'%(?:%|(?:\d+\$)?[-+ #0\']*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|h|ll|l|L|q|j|z|t|I64|I32)?'
                    r'[diouxXeEfFgGaAcspn@]|(?:"PRI\w+"))')
QT_ARG = re.compile(r'%(\d{1,2})(?!\d)')
HTML = {'a', 'b', 'big', 'body', 'br', 'center', 'code', 'div', 'em', 'font', 'h1', 'h2', 'h3', 'h4', 'head', 'hr',
        'html', 'i', 'img', 'li', 'meta', 'nobr', 'ol', 'p', 'pre', 'qt', 's', 'small', 'span', 'strong', 'style',
        'sub', 'sup', 'table', 'td', 'th', 'tr', 'tt', 'u', 'ul'}
TAG = re.compile(r'</?([a-zA-Z][a-zA-Z0-9]*)\b[^<>]*?/?>')


def tags(text):
    return sorted(name.lower() for name in TAG.findall(text) if name.lower() in HTML)
ENTITY = re.compile(r'&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);')
ACCELERATOR = re.compile(r'&(?=[^\s&;])')


def arguments(text):
    """printf-like conversions as a multiset; positional ones (%1$s) by position, the rest in order."""
    found = []
    for match in PRINTF.finditer(text):
        token = match.group(0)
        if token == '%%':
            continue
        positional = re.match(r'%(\d+)\$', token)
        conversion = re.sub(r'[-+ #0\'\d.*$]|hh|ll|[hlLqjzt]|I64|I32', '', token[1:]) or token
        found.append((positional.group(1) if positional else None, conversion))
    return found


def same_arguments(source, target):
    """Same conversions: positional ones may move, unnumbered ones keep their order."""
    a, b = arguments(source), arguments(target)
    if any(position for position, _ in a + b):
        def table(items):
            return sorted((position or str(index + 1), conversion) for index, (position, conversion) in enumerate(items))
        return table(a) == table(b)
    return a == b


def accelerators(text):
    return len(ACCELERATOR.findall(ENTITY.sub('', text)))


def problems(entry, nplurals):
    """Corsu's rules for one translated entry; msgfmt checks C formats on top."""
    found = []
    sources = [entry.msgid] if entry.plural is None else [entry.msgid] + [entry.plural] * (nplurals - 1)
    targets = entry.translations
    if entry.plural is not None and len(targets) != nplurals:
        found.append(f'{len(targets)} plural forms, the header says {nplurals}')
    if not all(targets):
        found.append('empty translation')
        return found
    for index, (source, target) in enumerate(zip(sources, targets)):
        where = f' (form {index})' if entry.plural is not None else ''
        if not same_arguments(source, target) and not (entry.plural is not None and index == 0 and
                                                          same_arguments(entry.plural, target)):
            # Singular forms may drop the count ("One file"), as gettext allows; anything else is an error.
            if not (entry.plural is not None and index == 0 and
                    set(arguments(target)) <= set(arguments(entry.plural))):
                found.append(f'arguments differ{where}: {arguments(source)} / {arguments(target)}')
        if sorted(QT_ARG.findall(source)) != sorted(QT_ARG.findall(target)) and '%' not in re.sub(QT_ARG, '', source):
            found.append(f'%1-style arguments differ{where}')
        if tags(source) != tags(target):
            found.append(f'markup tags differ{where}: {tags(source)} / {tags(target)}')
        if sorted(ENTITY.findall(source)) != sorted(ENTITY.findall(target)):
            found.append(f'entities differ{where}')
        if min(accelerators(source), 1) != min(accelerators(target), 1):
            found.append(f'menu accelerator (&) {"missing" if accelerators(source) else "added"}{where}')
        for mark in ('\n', ' '):
            if source.startswith(mark) != target.startswith(mark):
                found.append(f'leading {mark!r} differs{where}')
        for mark, accepted in (('\n', ('\n',)), (' ', (' ',)), (':', (':',)), ('...', ('...', '…')), ('…', ('...', '…'))):
            if source.endswith(mark) and not target.endswith(accepted):
                found.append(f'trailing {mark!r} missing{where}')
        if any(ord(c) < 32 and c not in '\n\t' for c in target):
            found.append(f'control character{where}')
    return found


# Menus of VLC 3.0.x's Qt interface whose entries are shown together (modules/gui/qt/menus.cpp and the I_MENU_*
# strings of include/vlc_intf_strings.h): within one menu, an accelerator letter should open one entry only. Qt
# accepts a letter twice (pressing it cycles between the entries) but Alt+letter in the menu bar then opens the
# first one only. A Corsu draft must not add such a clash; the clashes between upstream translations are reported.
MENUS = {
    'menu bar (createMenuBar)': ['&Media', 'P&layback', '&Audio', '&Video', 'Subti&tle', 'Tool&s', 'V&iew', '&Help'],
    'right-click menu (PopupMenu)': ['&Play', 'Pause', '&Stop', 'Pre&vious', 'Ne&xt', 'Record', 'Leave Fullscreen',
                                     '&Audio', '&Video', 'Subti&tle', '&Playback', 'Tool&s', 'V&iew', 'Playlist',
                                     'Open Media', 'Quit'],
    'Media (FileMenu)': ['Open &File...', '&Open Multiple Files...', 'Open D&irectory...', 'Open &Disc...',
                         'Open &Network Stream...', 'Open &Capture Device...', 'Open &Location from clipboard',
                         'Open &Recent Media', 'Save Playlist to &File...', 'Conve&rt / Save...', '&Stream...',
                         'Quit at the end of playlist', 'Close to systray', '&Quit'],
    'Playback (NavigMenu)': ['T&itle', '&Chapter', '&Program', 'Custom &Bookmarks', '&Renderer', 'Sp&eed',
                             '&Jump Forward', 'Jump Bac&kward', 'Jump to Specific &Time', '&Play', '&Stop',
                             'Pre&vious', 'Ne&xt', 'Record'],
    'Audio (AudioMenu)': ['Audio &Track', 'Audio &Device', '&Stereo Mode', '&Visualizations', '&Increase Volume',
                          'D&ecrease Volume', '&Mute'],
    'Video (VideoMenu)': ['Video &Track', '&Fullscreen', 'Always Fit &Window', 'Set as Wall&paper', '&Zoom',
                          '&Aspect Ratio', '&Crop', '&Deinterlace', '&Deinterlace mode', 'Take &Snapshot'],
    'Subtitle (SubtitleMenu)': ['Add &Subtitle File...', 'Sub &Track'],
    'Tools (ToolsMenu)': ['&Effects and Filters', '&Track Synchronization', 'Media &Information', '&Codec Information',
                          '&VLM Configuration', 'Program Guide', '&Messages', 'Plu&gins and extensions',
                          'Customi&ze Interface...', '&Preferences'],
    'View (ViewMenu)': ['Play&list', 'Docked Playlist', 'Always on &top', 'Mi&nimal Interface',
                        '&Fullscreen Interface', '&Advanced Controls', 'Status Bar', 'Visualizations selector'],
    'Help (HelpMenu)': ['&Help', 'Check for &Updates...', '&About'],
}


def accelerator(text):
    """The letter after the first '&' (lower case), or ''."""
    match = ACCELERATOR.search(ENTITY.sub('', text))
    return text[match.end()].lower() if match else ''


def menu_clashes(entries):
    """[(menu, letter, [msgid, ...], whether a Corsu draft is among them)] for letters used twice in one menu."""
    by_msgid = {entry.msgid: entry for entry in entries if entry.msgctxt is None and entry.msgid}
    clashes = []
    for menu, msgids in MENUS.items():
        letters = {}
        for msgid in dict.fromkeys(msgids):
            entry = by_msgid.get(msgid)
            letter = accelerator(entry.translations[0]) if entry and entry.translations[0] else ''
            if letter:
                letters.setdefault(letter, []).append(entry)
        for letter, found in letters.items():
            if len(found) > 1:
                clashes.append((menu, letter, [entry.msgid for entry in found], any(entry.draft for entry in found)))
    return clashes


def nplurals(entries):
    header = next(entry for entry in entries if entry.msgid == '')
    return int(re.search(r'nplurals=(\d+)', header.fields['msgstr']).group(1))


def msgfmt(path, output, use_fuzzy):
    command = ['msgfmt', '-c', '--check-format', '-o', str(output), str(path)]
    if use_fuzzy:
        command.insert(1, '--use-fuzzy')
    return subprocess.run(command, capture_output=True, text=True, encoding='utf-8')


def upstream(blocks):
    """The upstream catalogue the drafts were added to: Corsu's comments, fuzzy flags and translations taken out."""
    result = []
    for block in blocks:
        entry = Entry(block)
        if entry.draft:
            block = [line.replace('#, fuzzy, ', '#, ') for line in block
                     if not line.startswith(COMMENT) and line != '#, fuzzy']
            block = set_translation(block, entry, '' if entry.plural is None else [''] * len(entry.translations))
        result.append('\n'.join(block))
    return '\n\n'.join(result) + '\n'


def check(path=None):
    path = path or CATALOG
    blocks, entries = read(path)
    review = load_review()
    count = nplurals(entries)
    errors = []
    drafts = [entry for entry in entries if entry.draft]
    for entry in drafts:
        if not entry.fuzzy and review.get(entry.id, {}).get('status') != 'human':
            errors.append(f'{entry.id}: a Corsu entry without the fuzzy flag must be validated by a speaker')
        for problem in problems(entry, count):
            errors.append(f'{entry.id} {entry.msgid[:50]!r}: {problem}')
    if hashlib.sha256(upstream(blocks).encode('utf-8')).hexdigest() != UPSTREAM_SHA256:
        errors.append('the upstream translations or header changed: co.po without the Corsu entries is no longer '
                      'upstream\'s file (UPSTREAM_SHA256)')
    notes = []
    for menu, letter, msgids, draft in menu_clashes(entries):
        text = f'{menu}: accelerator {letter.upper()} on {", ".join(repr(msgid) for msgid in msgids)}'
        (errors if draft else notes).append(text + (' (a Corsu draft adds it)' if draft else ' (upstream)'))
    unknown = set(review) - {entry.id for entry in drafts}
    errors += [f'review.json names {name}, which is not a Corsu entry of co.po' for name in sorted(unknown)]
    with tempfile.TemporaryDirectory() as folder:
        result = msgfmt(path, Path(folder) / 'all.mo', use_fuzzy=True)
    if result.returncode:
        errors.append('msgfmt --use-fuzzy -c --check-format:\n' + result.stderr)
    kept = [entry for entry in entries if not entry.draft and entry.msgid]
    print(f'checked: {len(drafts)} Corsu drafts with msgfmt (fuzzy included) and Corsu rules; '
          f'{len(kept)} upstream entries unchanged')
    for note in notes:
        print('NOTE', note)
    for error in errors:
        print('ERROR', error)
    return 1 if errors else 0


def counts(path=None):
    _, entries = read(path)
    review = load_review()
    total = {}
    for entry in entries:
        if not entry.msgid:
            continue
        name = status(entry, review) if entry.draft else ('upstream' if all(entry.translations) and not entry.fuzzy
                                                         else 'upstream untranslated')
        total[name] = total.get(name, 0) + 1
    return total


def export(output, path=None):
    _, entries = read(path)
    review = load_review()
    with open(output, 'w', encoding='utf-8') as stream:
        for entry in entries:
            if entry.draft:
                stream.write(json.dumps({
                    'id': entry.id, 'msgctxt': entry.msgctxt, 'msgid': entry.msgid, 'msgid_plural': entry.plural,
                    'msgstr': entry.translations if entry.plural is not None else entry.translations[0],
                    'flags': [flag for flag in entry.flags if flag != 'fuzzy'], 'references': entry.references,
                    'status': status(entry, review)}, ensure_ascii=False) + '\n')


def set_translation(block, entry, value):
    """The block with its msgstr lines replaced; comments, references and flags unchanged."""
    keep = []
    skipping = False
    for line in block:
        if line.startswith('msgstr'):
            skipping = True
            continue
        if skipping and line.startswith('"'):
            continue
        skipping = False
        keep.append(line)
    if entry.plural is None:
        return keep + po_string(value, 'msgstr')
    lines = list(keep)
    for index, form in enumerate(value):
        lines += po_string(form, f'msgstr[{index}]')
    return lines


def set_comment(block, text):
    return [COMMENT + text if line.startswith(COMMENT) else line for line in block]


def merge(proposals, reviewer, date, path=None):
    blocks, _ = read(path)
    review = load_review()
    by_id = {}
    for index, block in enumerate(blocks):
        entry = Entry(block)
        if entry.draft:
            by_id[entry.id] = (index, entry)
    seen = set()
    for file in proposals:
        for number, line in enumerate(Path(file).read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            item = json.loads(line)
            name = item['id']
            if name not in by_id:
                raise SystemExit(f'{file}:{number}: {name} is not a Corsu draft')
            if name in seen:
                raise SystemExit(f'{file}:{number}: {name} reviewed twice; one reviewer per entry')
            seen.add(name)
            index, entry = by_id[name]
            verdict = item['verdict']
            if verdict not in ('keep', 'fix', 'uncertain'):
                raise SystemExit(f'{file}:{number}: verdict must be keep, fix or uncertain')
            record = review.setdefault(name, {'msgid': entry.msgid, 'draft': entry.translations if entry.plural
                                              is not None else entry.translations[0], 'reviews': []})
            if record.get('status') == 'human':
                raise SystemExit(f'{file}:{number}: {name} was validated by a speaker; an AI review cannot change it')
            new = item.get('msgstr')
            if verdict == 'fix' or (verdict == 'uncertain' and new):
                if new is None:
                    raise SystemExit(f'{file}:{number}: a fix needs msgstr')
                old = entry.translations if entry.plural is not None else entry.translations[0]
                if new != old:
                    blocks[index] = set_translation(blocks[index], entry, new)
            record['reviews'].append({'by': reviewer, 'date': date, 'verdict': verdict,
                                      **({'msgstr': new} if new is not None else {}),
                                      **({'note': item['note']} if item.get('note') else {})})
            record['status'] = 'uncertain' if verdict == 'uncertain' else 'ai_reviewed'
            blocks[index] = set_comment(blocks[index], STATUS_COMMENT[record['status']])
    write(blocks, path)
    save_review(review)
    return len(seen)


def build(output, path=None, statuses=BUILD_STATUSES):
    """Compile upstream plus the drafts whose status is in statuses; returns the counts."""
    blocks, _ = read(path)
    review = load_review()
    lines, added, left = [], 0, 0
    for block in blocks:
        entry = Entry(block)
        if entry.draft and entry.msgid:
            if status(entry, review) in statuses:
                block = [line.replace('#, fuzzy, ', '#, ').replace(', fuzzy', '') if line.startswith('#,') else line
                         for line in block if line.strip() != '#, fuzzy']
                added += 1
            else:
                left += 1
        lines.append('\n'.join(block))
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / 'co.po'
        source.write_text('\n\n'.join(lines) + '\n', encoding='utf-8')
        result = msgfmt(source, output, use_fuzzy=False)
        statistics = subprocess.run(['msgfmt', '--statistics', '-o', '/dev/null', str(source)],
                                    capture_output=True, text=True, encoding='utf-8').stderr.strip()
    if result.returncode:
        raise SystemExit('msgfmt failed:\n' + result.stderr)
    return {'drafts_included': added, 'drafts_left_out': left, 'msgfmt': statistics}


def main(argv):
    command = argv[0] if argv else 'check'
    if command == 'check':
        return check()
    if command == 'status':
        print(json.dumps(counts(), indent=1))
        return 0
    if command == 'export':
        export(argv[1])
        return 0
    if command == 'merge':
        reviewer = 'ai'
        date = None
        files = []
        for argument in argv[1:]:
            if argument.startswith('--by='):
                reviewer = argument[5:]
            elif argument.startswith('--date='):
                date = argument[7:]
            else:
                files.append(argument)
        if not date:
            raise SystemExit('merge needs --date=YYYY-MM-DD')
        print(f'merged {merge(files, reviewer, date)} reviews')
        return check()
    if command == 'build':
        include = [argument[10:].split(',') for argument in argv[2:] if argument.startswith('--include=')]
        print(json.dumps(build(Path(argv[1]), statuses=tuple(include[0]) if include else BUILD_STATUSES), indent=1))
        return 0
    raise SystemExit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
