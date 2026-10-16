#!/usr/bin/env python3
"""Look up Corsican words in the downloaded resources (run tools/fetch_resources.py first).

    python3 tools/corsican_words.py index               build words.tsv from the resources
    python3 tools/corsican_words.py lookup WORD [...]   where each word is attested, with Wiktionary glosses

A word found here is attested somewhere; a word missing here is not therefore wrong. Vikipedia counts show usage,
not correctness, and the Pontoon terms are the Mozilla Corsican team's choices for software.
"""
import bz2
import collections
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

BASE = Path(os.environ.get('CORSU_RESOURCES', Path.home() / '.local/share/corsu/resources'))
INDEX = BASE / 'words.tsv'
WORD = re.compile(r"[a-zàèìòùáéíóúâêîôûäëïöüçA-ZÀÈÌÒÙÁÉÍÓÚÂÊÎÔÛ]+(?:'[a-zàèìòù]+)?")


def wiki_words(path):
    counts = collections.Counter()
    with bz2.open(path, 'rt', encoding='utf-8', errors='replace') as stream:
        inside = False
        for line in stream:
            if '<text' in line:
                inside = True
            if inside:
                for word in WORD.findall(line):
                    counts[word.lower()] += 1
            if '</text>' in line:
                inside = False
    return counts


def build():
    sources = collections.defaultdict(dict)
    wiki = BASE / 'wikimedia/cowiki-latest-pages-articles.xml.bz2'
    if wiki.exists():
        for word, count in wiki_words(wiki).items():
            sources[word]['vikipedia'] = count
    dix = BASE / 'apertium/apertium-cos.cos.dix'
    if dix.exists():
        for match in re.finditer(r'<e[^>]*lm="([^"]+)"', dix.read_text(encoding='utf-8')):
            sources[match.group(1).lower()]['apertium'] = 1
    tbx = BASE / 'pontoon/co.v2.tbx'
    if tbx.exists():
        for term in ET.parse(tbx).iter():
            if term.tag.endswith('term') and term.text:
                for word in WORD.findall(term.text):
                    sources[word.lower()]['pontoon'] = sources[word.lower()].get('pontoon', 0) + 1
    kaikki = BASE / 'kaikki/kaikki.org-dictionary-Corsican.jsonl'
    if kaikki.exists():
        for line in kaikki.read_text(encoding='utf-8').splitlines():
            entry = json.loads(line)
            glosses = '; '.join(g for sense in entry.get('senses', []) for g in sense.get('glosses', []))[:200]
            sources[entry['word'].lower()]['wiktionary'] = f"{entry.get('pos', '')}: {glosses}"
    with INDEX.open('w', encoding='utf-8') as out:
        out.write('word\tvikipedia\tapertium\tpontoon\twiktionary\n')
        for word in sorted(sources):
            s = sources[word]
            out.write(f"{word}\t{s.get('vikipedia', 0)}\t{s.get('apertium', 0)}\t{s.get('pontoon', 0)}\t"
                      f"{s.get('wiktionary', '')}\n")
    print(f'{INDEX}: {len(sources):,} words')


def lookup(words):
    table = {}
    for line in INDEX.read_text(encoding='utf-8').splitlines()[1:]:
        fields = line.split('\t')
        table[fields[0]] = fields[1:]
    for word in words:
        row = table.get(word.lower())
        if row:
            print(f'{word}: vikipedia {row[0]}, apertium {"yes" if row[1] == "1" else "no"}, pontoon {row[2]}'
                  + (f', wiktionary {row[3]}' if row[3] else ''))
        else:
            print(f'{word}: not found')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'index':
        build()
    elif len(sys.argv) > 2 and sys.argv[1] == 'lookup':
        lookup(sys.argv[2:])
    else:
        print(__doc__)
