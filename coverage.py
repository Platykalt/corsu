#!/usr/bin/env python3
"""Collect untranslated system interface labels; never read messages or profiles."""
import argparse
from collections import Counter
import gettext
import json
from pathlib import Path
import re
import zipfile

import corsu


def firefox_labels():
    source = Path('/usr/lib/firefox')
    french_path = corsu.ROOT / 'vendor/firefox-fr.xpi'
    french = zipfile.ZipFile(french_path) if french_path.exists() else None
    try:
        for archive in ('omni.ja', 'browser/omni.ja'):
            if not (source / archive).exists():
                continue
            with corsu.read_zip(source / archive) as bundle:
                for info in bundle.infolist():
                    if not info.filename.endswith('.ftl') or '/en-US/' not in info.filename:
                        continue
                    data = bundle.read(info)
                    name = ('browser/' if archive.startswith('browser/') else '') + info.filename.replace('/en-US/', '/fr/')
                    if french and name in french.namelist():
                        data = french.read(name)
                    for line in data.decode().splitlines():
                        match = re.match(r'^\s*(?:[\w-]+|\.[\w-]+)\s*=\s*(.+)$', line)
                        if match and not re.search(r'\.(?:accesskey|key|style)\s*=', line):
                            value = match[1].strip()
                            if len(value) > 1 and not re.fullmatch(r'[\d\W]+', value):
                                yield value
    finally:
        if french:
            french.close()


def qt_labels():
    """Qt-style catalogs: framework dialogs, standard buttons and file choosers."""
    for source in sorted(list(corsu.FRENCH_CATALOGS.glob('*.qm')) + list(corsu.QT_TRANSLATIONS.glob('*_fr.qm'))):
        try:
            catalog = corsu.read_qm(source.read_bytes())
        except (ValueError, IndexError):
            continue
        for message in catalog['messages']:
            if message.get('source') and message['translations'] and message['translations'][0]:
                yield message['source'], message['translations'][0]


def kde_labels():
    for source in sorted(Path('/usr/share/locale/fr/LC_MESSAGES').glob('*.mo')):
        with source.open('rb') as stream:
            catalog = gettext.GNUTranslations(stream)._catalog
        for key, value in catalog.items():
            if isinstance(key, str) and key and isinstance(value, str):
                yield key.split('\x04', 1)[-1], value


def collect(limit=1000):
    result = {'note': 'Counts cover single-line Fluent patterns and singular gettext entries, not full UI coverage. '
                      'Unchanged brand names/technical values may appear in the review queue. '
                      'Discord labels require manual review of its UI; no account data is collected.'}
    for name, labels in [('firefox', ((value, value) for value in firefox_labels())),
                         ('kde', kde_labels()), ('qt', qt_labels())]:
        count = translated = 0
        missing = Counter()
        for english, fallback in labels:
            count += 1
            if corsu.translate(english) != english or corsu.translate(fallback) != fallback:
                translated += 1
            else:
                missing[fallback] += 1
        result[name] = {'examined_entries': count, 'translated_entries': translated,
                        'untranslated_entries': count - translated, 'unique_untranslated': len(missing),
                        'review_queue': [{'source': label, 'occurrences': frequency} for label, frequency in missing.most_common(limit)]}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--limit', type=int, default=1000)
    args = parser.parse_args()
    result = collect(args.limit)
    data = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data)
        print(f'Review queue saved to {args.output}')
        for name in ('firefox', 'kde', 'qt'):
            print(name + ': ' + json.dumps({key: value for key, value in result[name].items() if key != 'review_queue'}))
    else:
        print(data)


if __name__ == '__main__':
    main()
