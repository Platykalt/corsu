#!/usr/bin/env python3
"""Import reviewed Corsican translations published by other free software projects.

Most of them are the work of Patriccollu di Santa Maria è Sichè
(https://github.com/Patriccollu/Lingua_Corsa-Infurmatica). Each project's own license applies to its rows;
every source below is meant to be compatible with Corsu's GPL-3.0-or-later (HandBrake, GPL-2.0-only, is left out
for that reason).

    python3 tools/import_translations.py

writes the contextual translation memory lexicon/memory/<source>.jsonl (one entry per string, with its key,
context, plural forms, placeholders, origin commit and license; see lexicon/memory/README.md), then derives from it
lexicon/lexicon-mozilla.tsv (MPL-2.0 sources) and lexicon/lexicon-upstream.tsv (the others), whose rows are
`English|French|Corsican`; French comes from the same project's French translation, so that French-only interfaces
(Firefox, Chrome) match as well as English ones (KDE, Qt). Corsu's own lexicon.tsv sections are exported to
lexicon/memory/corsu-<section>.jsonl. Every repository is read at the exact commit its branch pointed to, recorded
in each entry's `version` (set GITHUB_TOKEN to raise the GitHub API rate limit).

    python3 tools/import_translations.py --corsu-only

only re-exports lexicon.tsv's sections, without network access.
"""
import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))
import engine  # noqa: E402
import tm  # noqa: E402

RAW = 'https://raw.githubusercontent.com/{repo}/{ref}/{path}'
API = 'https://api.github.com/repos/{repo}/commits/{branch}'
MEMORY = ROOT / 'lexicon/memory'
TODAY = datetime.date.today().isoformat()
CORSU = 'Platykalt/corsu'


def request(url, timeout=120):
    headers = {'User-Agent': 'corsu-import-translations'}
    if 'api.github.com' in url and os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
        return response.read()


_SHAS = {}


def commit(repo, branch):
    """The commit a branch points to now: files are then fetched from that commit, so an import can be repeated."""
    if (repo, branch) not in _SHAS:
        _SHAS[(repo, branch)] = json.loads(request(API.format(repo=repo, branch=branch)))['sha']
    return _SHAS[(repo, branch)]


def fetch(repo, branch, path):
    return request(RAW.format(repo=repo, ref=commit(repo, branch), path=path))


def android(data):
    """name -> text of the <string> resources (plurals: see tm.android_entries)."""
    return {name: item['text'] for name, item in tm.android_entries(data).items() if item['plural'] is None}


unquote = tm.unquote


def po(data):
    """(msgctxt, msgid) -> entry for translated, non-fuzzy entries, plurals included (see tm.po_entries)."""
    return tm.po_entries(data)


def xliff(data):
    """(file original, trans-unit id) -> (source, target)."""
    return {key: (item['source'], item['target']) for key, item in tm.xliff_entries(data).items() if item['target']}


def notepad(data):
    """Notepad++ native language files: one key per element path and id, value in the `name` attribute."""
    result = {}

    def walk(element, path):
        key = f'{path}/{element.tag}[{element.get("id") or element.get("CMID") or ""}]'
        if element.get('name'):
            result[key] = element.get('name').replace('&', '')
        for child in element:
            walk(child, key)

    walk(ET.fromstring(data), '')
    return result


def freac(data):
    """fre:ac language files: <entry id=… string="English">translation</entry> inside named sections."""
    result = {}

    def walk(element, path):
        for child in element:
            if child.tag == 'entry':
                result[f'{path}#{child.get("id")}'] = (child.get('string') or '', ''.join(child.itertext()))
            else:
                walk(child, f'{path}/{child.tag}:{child.get("name") or ""}')

    walk(ET.fromstring(data), '')
    return result


def isl(data):
    """Inno Setup message files: Key=Value lines, without the [LangOptions] settings."""
    result, section = {}, ''
    for line in data.decode('utf-8-sig', 'replace').splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
        elif '=' in line and not line.startswith(';') and section in ('Messages', 'CustomMessages'):
            key, _, value = line.partition('=')
            result[f'{section}/{key.strip()}'] = value.replace('%n', ' ').strip()
    return result


# (title, license, repository, branch, English path, French path, Corsican path, parser)
ANDROID = [
    ('Thunderbird for Android', 'Apache-2.0', 'thunderbird/thunderbird-android', 'main',
     ['app-common/src/main/res', 'app-k9mail/src/main/res', 'app-thunderbird/src/main/res',
      'legacy/ui/legacy/src/main/res', 'feature/account/setup/src/main/res', 'feature/settings/import/src/main/res']),
    ('VLC for Android', 'GPL-2.0-or-later', 'videolan/vlc-android', 'master',
     ['application/resources/src/main/res', 'medialibrary/res']),
    ('OpenTracks', 'Apache-2.0', 'OpenTracksApp/OpenTracks', 'main', ['src/main/res']),
]
PO = [
    ('Audacity', 'GPL-2.0-or-later', 'audacity/audacity', 'master', 'au3/locale/fr.po', 'au3/locale/co.po'),
    ('Poedit', 'MIT', 'vslavik/poedit', 'master', 'locales/fr.po', 'locales/co.po'),
    ('WinMerge', 'GPL-2.0-or-later', 'WinMerge/winmerge', 'master', 'Translations/WinMerge/French.po',
     'Translations/WinMerge/Corsican.po'),
    ('VLC media player', 'GPL-2.0-or-later', 'videolan/vlc', 'master', 'po/fr.po', 'po/co.po'),
    # HandBrake is left out: GPL-2.0-only cannot be combined with Corsu's GPL-3.0-or-later.
    ('Tenacity', 'GPL-2.0-or-later', 'tenacityteam/tenacity', 'main', 'locale/fr.po', 'locale/co.po'),
    ('wxWidgets', 'wxWindows-exception-3.1', 'wxWidgets/wxWidgets', 'master', 'locale/fr.po', 'locale/co.po'),
]


def clean(text):
    return re.sub(r'\s+', ' ', text.replace('|', '/')).strip()


def usable(english, french, corsican):
    if not corsican or corsican in (english, french) or not (english or french):
        return False
    # A row starting with '#' would read as a comment (WinMerge's sample replacement lists do).
    if any(text.startswith('#') for text in (english, french, corsican)):
        return False
    # A lone letter or symbol is a format code or a shortcut, never an interface label.
    if any(source and not re.search(r'[^\W\d_].*[^\W\d_]', source) for source in (english, french)):
        return False
    return all(engine.signature(source) == engine.signature(corsican) for source in (english, french) if source)


def write(path, header, sections):
    seen, lines, count = set(), [*header, ''], 0
    for title, license, rows in sections:
        lines.append(f'# {title} ({license})')
        for english, french, corsican in rows:
            english, french, corsican = clean(english), clean(french), clean(corsican)
            # The French interface shows "…"; keep the Corsican in step when the translation typed three dots.
            if corsican.endswith('...') and (french.endswith('…') or english.endswith('…')):
                corsican = corsican[:-3] + '…'
            if not usable(english, french, corsican) or (english, french) in seen:
                continue
            seen.add((english, french))
            lines.append(f'{english}|{french}|{corsican}')
            count += 1
        lines.append('')
    path.parent.mkdir(exist_ok=True)
    path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'{path.relative_to(ROOT)}: {count} rows')


class Source:
    """One imported project: where its files come from, and how its entries are recorded."""

    def __init__(self, ident, title, license, repo, branch):
        self.ident, self.title, self.license, self.repo, self.branch = ident, title, license, repo, branch
        self.version = commit(repo, branch)
        self.entries = []

    def add(self, component, key, english, french, corsican, path, context=None, plural=None):
        english, french = english or '', french or ''
        if not (english or french) or not corsican:
            return
        context = {name: value for name, value in (context or {}).items() if value}
        self.entries.append(tm.make_entry(
            self.title, key, english or french, corsican, component=component, context=context or None,
            source_lang='en' if english else 'fr', source_fr=french or None, plural=plural,
            origin={'repo': self.repo, 'branch': self.branch, 'path': path}, version=self.version,
            license=self.license, review='upstream-reviewed', fetched=TODAY))


def android_resources(source, component, path, english, french, corsican):
    """Entries of one Android resource folder: strings and plurals, keyed by resource name."""
    for name, item in corsican.items():
        source_item, french_item = english.get(name), french.get(name)
        context = {'comment': (source_item or {}).get('comment') or item.get('comment')}
        if item['plural']:
            quantities = list(item['plural'])
            source_forms = (source_item or {}).get('plural') or {}
            french_forms = (french_item or {}).get('plural') or {}
            plural = {'source_plural': source_forms.get('other', ''), 'forms': quantities}
            source.add(component, name, source_forms.get('one') or source_forms.get('other', ''),
                       french_forms.get('one') or french_forms.get('other', ''),
                       [item['plural'][quantity] for quantity in quantities], path, context, plural)
        else:
            source.add(component, name, (source_item or {}).get('text', ''), (french_item or {}).get('text', ''),
                       item['text'], path, context)


def mozilla_android():
    """Firefox for Android, Focus and Android Components, from mozilla-l10n/android-l10n."""
    source = Source('mozilla-android', 'Firefox for Android, Focus and Android Components', 'MPL-2.0',
                    'mozilla-l10n/android-l10n', 'main')
    archive = zipfile.ZipFile(io.BytesIO(request(
        f'https://github.com/{source.repo}/archive/{source.version}.zip', timeout=300)))
    names = set(archive.namelist())
    for name in sorted(names):
        if name.endswith('/values-co/strings.xml'):
            base = name[:-len('values-co/strings.xml')]
            read = lambda path: tm.android_entries(archive.read(path)) if path in names else {}
            relative = name.split('/', 1)[1]
            android_resources(source, base.split('/', 1)[1].rstrip('/'), relative, read(base + 'values/strings.xml'),
                              read(base + 'values-fr/strings.xml'), read(name))
    return source


def mozilla_xliff(ident, title, repo, branch, file):
    source = Source(ident, title, 'MPL-2.0', repo, branch)
    corsican = tm.xliff_entries(fetch(repo, branch, f'co/{file}'))
    french = tm.xliff_entries(fetch(repo, branch, f'fr/{file}'))
    for (original, unit), item in corsican.items():
        if item['target']:
            source.add(original, unit, item['source'], (french.get((original, unit)) or {}).get('target'),
                       item['target'], f'co/{file}', {'note': item['note']})
    return source


def upstream_android(ident, title, license, repo, branch, directories):
    source = Source(ident, title, license, repo, branch)
    for directory in directories:
        try:
            corsican = tm.android_entries(fetch(repo, branch, f'{directory}/values-co/strings.xml'))
        except OSError:
            continue
        english = tm.android_entries(fetch(repo, branch, f'{directory}/values/strings.xml'))
        try:
            french = tm.android_entries(fetch(repo, branch, f'{directory}/values-fr/strings.xml'))
        except OSError:
            french = {}
        android_resources(source, directory, f'{directory}/values-co/strings.xml', english, french, corsican)
    return source


def upstream_po(ident, title, license, repo, branch, french_path, corsican_path):
    """Entries keyed by (msgctxt, msgid): the same English in two contexts stays two entries; plurals kept."""
    source = Source(ident, title, license, repo, branch)
    corsican = tm.po_entries(fetch(repo, branch, corsican_path))
    french = tm.po_entries(fetch(repo, branch, french_path))
    # When the French catalog has the message under another context (or none), its msgid alone still decides,
    # provided all its contexts agree.
    by_msgid = {}
    for (_, msgid), item in french.items():
        by_msgid.setdefault(msgid, []).append(item['msgstr'])
    for key, item in corsican.items():
        msgctxt, msgid = key
        french_value = (french.get(key) or {}).get('msgstr')
        if french_value is None:
            values = by_msgid.get(msgid, [])
            if values and all(value == values[0] for value in values):
                french_value = values[0]
        plural = None
        if item['msgid_plural']:
            plural = {'source_plural': item['msgid_plural'], 'forms': [str(index) for index in range(len(item['msgstr']))]}
            french_value = french_value[0] if isinstance(french_value, list) else None
        elif isinstance(french_value, list):
            french_value = None
        context = {'msgctxt': msgctxt, 'comments': item['comments'] or None, 'references': item['references'] or None}
        source.add(Path(corsican_path).name, msgid if msgctxt is None else f'{msgctxt}\x04{msgid}', msgid,
                   french_value, item['msgstr'], corsican_path, context, plural)
    return source


def freac_files():
    base = 'i18n/freac/'
    source = Source('freac', 'fre:ac', 'GPL-2.0-or-later', 'enzo1982/freac', 'master')
    corsican = freac(fetch(source.repo, source.branch, base + 'freac_co.xml'))
    french = freac(fetch(source.repo, source.branch, base + 'freac_fr.xml'))
    for key, (english, value) in corsican.items():
        source.add('freac', key, english, french.get(key, ('', ''))[1], value, base + 'freac_co.xml')
    return source


def inno_tsv(english, french, corsican):
    """Window titles such as "Setup" are "Assistente d'installazione" here: right for an installer, wrong as a
    general label, so short labels translated much longer stay out of the flat lexicon (they stay in the memory,
    with their key)."""
    count = lambda text: len(re.findall(r'\w+', text))
    return not (count(corsican) >= max(count(english), count(french)) + 2 and max(count(english), count(french)) <= 2)


def inno_setup():
    source = Source('inno-setup', 'Inno Setup', 'Inno Setup License', 'jrsoftware/issrc', 'main')
    corsican = isl(fetch(source.repo, source.branch, 'Files/Languages/Corsican.isl'))
    english = isl(fetch(source.repo, source.branch, 'Files/Default.isl'))
    french = isl(fetch(source.repo, source.branch, 'Files/Languages/French.isl'))
    for key, value in corsican.items():
        source.add(key.split('/')[0], key, english.get(key, ''), french.get(key, ''), value,
                   'Files/Languages/Corsican.isl')
    return source


def notepad_plus_plus():
    base = 'PowerEditor/installer/nativeLang/'
    source = Source('notepad-plus-plus', 'Notepad++', 'GPL-3.0-or-later', 'notepad-plus-plus/notepad-plus-plus', 'master')
    corsican = notepad(fetch(source.repo, source.branch, base + 'corsican.xml'))
    english = notepad(fetch(source.repo, source.branch, base + 'english.xml'))
    french = notepad(fetch(source.repo, source.branch, base + 'french.xml'))
    for key, value in corsican.items():
        source.add('nativeLang', key, english.get(key, ''), french.get(key, ''), value, base + 'corsican.xml')
    return source


def common_defaults(entries):
    """The value most entries share for each field, stored once in the file's `_defaults` line."""
    defaults = {}
    for field in ('app', 'component', 'context', 'source_lang', 'license', 'version', 'review', 'fetched'):
        values = [json.dumps(entry.get(field), sort_keys=True) for entry in entries]
        if values:
            value = json.loads(max(set(values), key=values.count))
            if value is not None and not isinstance(value, dict):
                defaults[field] = value
    origins = [json.dumps(entry.get('origin'), sort_keys=True) for entry in entries if entry.get('origin')]
    if origins:
        defaults['origin'] = json.loads(max(set(origins), key=origins.count))
    return defaults


def save(ident, entries):
    path = MEMORY / f'{ident}.jsonl'
    tm.write_memory(path, entries, common_defaults(entries))
    return path


def tsv_rows(entries, keep=None):
    """English|French|Corsican rows of singular memory entries (plural forms stay in the memory only)."""
    for entry in entries:
        if entry.get('plural') or not isinstance(entry.get('target'), str):
            continue
        english = entry['source'] if entry.get('source_lang') == 'en' else ''
        french = entry.get('source_fr') or ''
        if keep is None or keep(english, french, entry['target']):
            yield english, french, entry['target']


# lexicon.tsv headings -> (application, file name). `# Name:` headings are the sections engine.rows() reads.
CORSU_SECTIONS = [
    ('Current Firefox, Discord and Plasma', 'Corsu general', 'general'),
    ('Qt and KDE framework dialogs', 'Qt and KDE', 'qt-kde'),
    ('Firefox interface', 'Firefox', 'firefox'),
    ('Chrome, Chromium and Opera', 'Chromium', 'chromium'),
    ('Opera GX', 'Opera GX', 'opera-gx'),
    ('KDE Plasma desktop', 'KDE Plasma', 'kde-plasma'),
    ('Installed applications', 'Desktop applications', 'applications'),
    ('File types, keyboard layouts', 'System and terminal', 'system'),
]


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.casefold()).strip('-')[:40] or 'section'


def section_name(heading):
    if re.match(r'^[^:|—]{1,40}:', heading):
        name = heading.split(':', 1)[0].strip()
        return name, slug(name)
    for prefix, name, ident in CORSU_SECTIONS:
        if heading.startswith(prefix):
            return name, ident
    name = re.split(r'[—:,(]', heading)[0].strip()
    return name, slug(name)


def corsu_version():
    try:
        sha = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.strip()
        dirty = subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', 'lexicon/lexicon.tsv'], cwd=ROOT).returncode
        return sha + ('+uncommitted' if dirty else '')
    except (OSError, subprocess.CalledProcessError):
        return None


def applied_corrections():
    """(source, Corsican) pairs that an AI review changed (lexicon/corrections.tsv, status `applied…`)."""
    pairs = set()
    path = ROOT / 'lexicon/corrections.tsv'
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines()[1:]:
            fields = line.split('\t')
            if len(fields) >= 9 and fields[8].startswith('applied'):
                pairs.add((engine.normalize(fields[2].strip()), engine.normalize(fields[4].strip())))
    return pairs


def export_corsu():
    """lexicon.tsv's sections as memory files: app = section name, review corsu-draft, or ai-reviewed for rows an
    applied correction produced."""
    reviewed = applied_corrections()
    version = corsu_version()
    sections, heading = {}, None
    for line in engine.LEXICON.read_text(encoding='utf-8').splitlines():
        if line.startswith('#'):
            # Only `# ` starts a heading (as in corsu.lexicon_section); `#lounge|…` rows are skipped like comments.
            if line.startswith('# ') and not line.startswith('# English | French | Corsican'):
                heading = line[2:].strip()
            continue
        fields = line.split('|')
        if len(fields) != 3 or not fields[2].strip() or heading is None:
            continue
        english, french, corsican = (field.strip() for field in fields)
        if not (english or french):
            continue
        name, ident = section_name(heading)
        section = sections.setdefault(ident, (name, heading, [], set()))
        if (english, french, corsican) in section[3]:
            continue
        section[3].add((english, french, corsican))
        review = 'ai-reviewed' if any((engine.normalize(text), engine.normalize(corsican)) in reviewed
                                      for text in (english, french) if text) else 'corsu-draft'
        section[2].append(tm.make_entry(
            name, english or french, english or french, corsican, component='lexicon.tsv', context=heading,
            source_lang='en' if english else 'fr', source_fr=french or None,
            origin={'repo': CORSU, 'path': 'lexicon/lexicon.tsv'}, version=version, license='GPL-3.0-or-later',
            review=review, fetched=TODAY))
    for old in MEMORY.glob('corsu-*.jsonl'):
        old.unlink()
    counts = {}
    for ident, (name, heading, entries, _) in sections.items():
        save(f'corsu-{ident}', entries)
        counts[f'corsu-{ident}'] = (name, len(entries), sum(entry['review'] == 'ai-reviewed' for entry in entries))
    return counts


def report(sources):
    print(f'{"source":<28}{"entries":>9}{"msgctxt":>9}{"context":>9}{"plurals":>9}  commit')
    for source in sources:
        entries = source.entries
        with_msgctxt = sum(1 for entry in entries if (entry.get('context') or {}).get('msgctxt'))
        with_context = sum(1 for entry in entries if entry.get('context'))
        plurals = sum(1 for entry in entries if entry.get('plural'))
        print(f'{source.ident:<28}{len(entries):>9}{with_msgctxt:>9}{with_context:>9}{plurals:>9}  '
              f'{source.repo}@{source.version[:12]}')


def main():
    MEMORY.mkdir(parents=True, exist_ok=True)
    if '--corsu-only' not in sys.argv:
        mozilla = [
            mozilla_android(),
            mozilla_xliff('firefox-ios', 'Firefox for iOS', 'mozilla-l10n/firefoxios-l10n', 'main', 'firefox-ios.xliff'),
            mozilla_xliff('mozilla-vpn', 'Mozilla VPN', 'mozilla-l10n/mozilla-vpn-client-l10n', 'main', 'mozillavpn.xliff'),
            mozilla_xliff('focus-ios', 'Firefox Focus for iOS', 'mozilla-l10n/focusios-l10n', 'main', 'focus-ios.xliff'),
        ]
        upstream = [upstream_android(slug(title), title, license, repo, branch, directories)
                    for title, license, repo, branch, directories in ANDROID]
        upstream += [upstream_po(slug(title), title, license, repo, branch, french, corsican)
                     for title, license, repo, branch, french, corsican in PO]
        upstream += [notepad_plus_plus(), freac_files(), inno_setup()]
        # The flat files are derived from the memory as written, so both always agree.
        paths = {source.ident: save(source.ident, source.entries) for source in mozilla + upstream}
        derive = lambda sources: [(source.title, source.license,
                                   list(tsv_rows(tm.read_memory(paths[source.ident]),
                                                 inno_tsv if source.ident == 'inno-setup' else None)))
                                  for source in sources]
        credit = ['# Corsican translations by Patriccollu di Santa Maria è Sichè and fellow translators,',
                  '# imported by tools/import_translations.py. Each section keeps its project\'s license.',
                  '# English | French | Corsican']
        write(ROOT / 'lexicon/lexicon-mozilla.tsv',
              [*credit, '# All rows: Mozilla Public License 2.0, https://mozilla.org/MPL/2.0/'], derive(mozilla))
        write(ROOT / 'lexicon/lexicon-upstream.tsv', credit, derive(upstream))
        report(mozilla + upstream)
    for ident, (name, count, reviewed) in export_corsu().items():
        print(f'{ident}: {count} entries ({name}), {reviewed} ai-reviewed')
    total = sum(path.stat().st_size for path in MEMORY.glob('*.jsonl'))
    print(f'lexicon/memory: {total / 1e6:.1f} MB in {len(list(MEMORY.glob("*.jsonl")))} files')


if __name__ == '__main__':
    main()
