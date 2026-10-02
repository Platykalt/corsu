#!/usr/bin/env python3
"""Import reviewed Corsican translations published by other free software projects.

Most of them are the work of Patriccollu di Santa Maria è Sichè
(https://github.com/Patriccollu/Lingua_Corsa-Infurmatica). Each project's own license applies to its rows;
every source below is compatible with Corsu's GPL-3.0-or-later.

    python3 tools/import_translations.py

writes lexicon/lexicon-mozilla.tsv (MPL-2.0 sources) and lexicon/lexicon-upstream.tsv (the others).
Rows are `English|French|Corsican`; French comes from the same project's French translation, so that
French-only interfaces (Firefox, Chrome) match as well as English ones (KDE, Qt).
"""
import io
import json
from pathlib import Path
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
import engine  # noqa: E402

RAW = 'https://raw.githubusercontent.com/{repo}/{branch}/{path}'


def fetch(repo, branch, path):
    url = RAW.format(repo=repo, branch=branch, path=path)
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def android(data):
    result = {}
    for element in ET.fromstring(data).iter('string'):
        text = ''.join(element.itertext()).strip()
        if len(text) > 1 and text[0] == text[-1] == '"':
            text = text[1:-1]
        text = text.replace("\\'", "'").replace('\\"', '"').replace('\\n', ' ').replace('\\@', '@')
        result[element.get('name')] = text
    return result


def unquote(value):
    """A PO string literal; JSON reads nearly all of them, the rest get the usual C escapes."""
    try:
        return json.loads(value)
    except ValueError:
        body = value.strip()[1:-1] if value.strip().endswith('"') else value.strip()[1:]
        return body.replace('\\n', ' ').replace('\\t', ' ').replace('\\"', '"').replace('\\\\', '\\')


def po(data):
    """msgid -> msgstr for singular, non-fuzzy entries."""
    result, entry, field, fuzzy = {}, {}, None, False

    def flush():
        if entry.get('msgid') and entry.get('msgstr') and not fuzzy:
            result[entry['msgid']] = entry['msgstr']

    for line in data.decode('utf-8', 'replace').splitlines() + ['']:
        line = line.strip()
        if not line:
            flush()
            entry, field, fuzzy = {}, None, False
        elif line.startswith('#,') and 'fuzzy' in line:
            fuzzy = True
        elif line.startswith('#'):
            continue
        elif line.startswith(('msgid ', 'msgstr ', 'msgctxt ')):
            field, _, value = line.partition(' ')
            entry[field] = unquote(value) if value.startswith('"') else ''
        elif line.startswith('msgid_plural') or line.startswith('msgstr['):
            field = None
        elif line.startswith('"') and field:
            entry[field] += unquote(line)
    return result


def xliff(data):
    """trans-unit id -> (source, target)."""
    result = {}
    root = ET.fromstring(data)
    for unit in root.iter():
        if not unit.tag.endswith('trans-unit'):
            continue
        source = target = None
        for child in unit:
            if child.tag.endswith('source'):
                source = ''.join(child.itertext())
            elif child.tag.endswith('target'):
                target = ''.join(child.itertext())
        if source and target:
            result[unit.get('id')] = (source, target)
    return result


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


def triples(english, french, corsican):
    for key, value in corsican.items():
        yield english.get(key, ''), french.get(key, ''), value


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
    ('HandBrake', 'GPL-2.0-only', 'HandBrake/HandBrake', 'master', 'gtk/po/fr.po', 'gtk/po/co.po'),
    ('Tenacity', 'GPL-2.0-or-later', 'tenacityteam/tenacity', 'main', 'locale/fr.po', 'locale/co.po'),
]


def clean(text):
    return re.sub(r'\s+', ' ', text.replace('|', '/')).strip()


def usable(english, french, corsican):
    if not corsican or corsican in (english, french) or not (english or french):
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


def mozilla_android():
    """Firefox for Android, Focus and Android Components, from mozilla-l10n/android-l10n."""
    archive = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(
        'https://github.com/mozilla-l10n/android-l10n/archive/refs/heads/main.zip', timeout=300).read()))
    names = set(archive.namelist())
    for name in sorted(names):
        if name.endswith('/values-co/strings.xml'):
            base = name[:-len('values-co/strings.xml')]
            english = android(archive.read(base + 'values/strings.xml')) if base + 'values/strings.xml' in names else {}
            french = android(archive.read(base + 'values-fr/strings.xml')) if base + 'values-fr/strings.xml' in names else {}
            yield from triples(english, french, android(archive.read(name)))


def mozilla_xliff(repo, branch, file):
    corsican = xliff(fetch(repo, branch, f'co/{file}'))
    french = xliff(fetch(repo, branch, f'fr/{file}'))
    for key, (english, target) in corsican.items():
        yield english, french.get(key, ('', ''))[1], target


def upstream_android(repo, branch, directories):
    for directory in directories:
        try:
            corsican = android(fetch(repo, branch, f'{directory}/values-co/strings.xml'))
        except OSError:
            continue
        english = android(fetch(repo, branch, f'{directory}/values/strings.xml'))
        try:
            french = android(fetch(repo, branch, f'{directory}/values-fr/strings.xml'))
        except OSError:
            french = {}
        yield from triples(english, french, corsican)


def upstream_po(repo, branch, french_path, corsican_path):
    corsican = po(fetch(repo, branch, corsican_path))
    french = po(fetch(repo, branch, french_path))
    for english, value in corsican.items():
        yield english, french.get(english, ''), value


def notepad_plus_plus():
    base = 'PowerEditor/installer/nativeLang/'
    repo, branch = 'notepad-plus-plus/notepad-plus-plus', 'master'
    corsican = notepad(fetch(repo, branch, base + 'corsican.xml'))
    english = notepad(fetch(repo, branch, base + 'english.xml'))
    french = notepad(fetch(repo, branch, base + 'french.xml'))
    yield from triples(english, french, corsican)


def main():
    credit = ['# Corsican translations by Patriccollu di Santa Maria è Sichè and fellow translators,',
              '# imported by tools/import_translations.py. Each section keeps its project\'s license.',
              '# English | French | Corsican']
    write(ROOT / 'lexicon/lexicon-mozilla.tsv', [*credit, '# All rows: Mozilla Public License 2.0, https://mozilla.org/MPL/2.0/'], [
        ('Firefox for Android, Focus and Android Components', 'MPL-2.0', list(mozilla_android())),
        ('Firefox for iOS', 'MPL-2.0', list(mozilla_xliff('mozilla-l10n/firefoxios-l10n', 'main', 'firefox-ios.xliff'))),
        ('Mozilla VPN', 'MPL-2.0', list(mozilla_xliff('mozilla-l10n/mozilla-vpn-client-l10n', 'main', 'mozillavpn.xliff'))),
        ('Firefox Focus for iOS', 'MPL-2.0', list(mozilla_xliff('mozilla-l10n/focusios-l10n', 'main', 'focus-ios.xliff'))),
    ])
    sections = [(title, license, list(upstream_android(repo, branch, directories)))
                for title, license, repo, branch, directories in ANDROID]
    sections += [(title, license, list(upstream_po(repo, branch, french, corsican)))
                 for title, license, repo, branch, french, corsican in PO]
    sections.append(('Notepad++', 'GPL-3.0-or-later', list(notepad_plus_plus())))
    write(ROOT / 'lexicon/lexicon-upstream.tsv', credit, sections)


if __name__ == '__main__':
    main()
