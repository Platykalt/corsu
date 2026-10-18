#!/usr/bin/env python3
"""Rough simulation of the keyboard's top-3 suggestions for a few prefixes.

    python3 keyboard/data/tools/simulate.py                 # shared, cismuntincu and pumuntincu, checks only
    python3 keyboard/data/tools/simulate.py --show          # also print the top 3 of every prefix
    python3 keyboard/data/tools/simulate.py --old           # the same checks on the old generated wordlist.tsv

This is not Keyman: it ranks the words that start with the typed prefix by weight, after folding case and accents
the way Keyman's default search key does (lowercase, accents removed), with no correction of typing mistakes and no
context. It is enough to see whether an everyday word is pushed out of the first three suggestions, for instance by
a software term whose weight comes from interface strings. A variety's list is read as shared.tsv with that
variety's file laid over it (same word: the variety's weight wins). Exit status 1 when a check fails.
"""
import argparse
from pathlib import Path
import sys
import unicodedata

DATA = Path(__file__).resolve().parents[1]
OLD_WORDLIST = DATA.parent / 'platykalt.co.corsu/source/wordlist.tsv'
# Words whose weight comes from software interfaces; they should not hide an everyday word.
COMPUTING = {'schedariu', 'schedarii', 'affissà', 'affissa', 'parametri', 'cartulare', 'cartulari', 'cunnessione',
             'squassà', 'mudificà', 'dati', 'situ', 'siti', 'pagina', 'sistema', 'testu', 'linea', 'chjave',
             'impussibule', 'servore', 'servori', 'screnu', 'attivà', 'disattivà', 'ozzioni', 'unghjetta', 'unghjette',
             'utilizatore', 'applicazione', 'sbagliu', 'fiascu', 'nome', 'statu', 'modu', 'solu', 'vo', 'esse'}
# (prefix, the word that must be among the first three suggestions)
CHECKS = {
    'shared': [
        ('bo', 'bonghjornu'), ('gr', 'grazie'), ('sal', 'salute'), ('ci', 'ciao'), ('ca', 'casa'),
        ('mam', 'mamma'), ('ba', 'babbu'), ('ami', 'amicu'), ('du', 'dumane'), ('og', 'oghje'), ('ag', 'aghju'),
        ('ven', 'vengu'), ('vog', 'vogliu'), ('sc', 'scusate'), ('cum', 'cumu'), ('per', 'perchè'), ('ac', 'acqua'),
        ('pae', 'paese'), ('te', 'tempu'), ('pi', 'piace'), ('su', 'subitu'), ('mi', 'micca'), ('pre', 'prestu'),
        ('tar', 'tardi'), ('Co', 'Corsica'), ('Ai', 'Aiacciu'), ('Bas', 'Bastia'), ('qua', 'quandu'), ('se', 'sera'),
        ('fa', 'facciu'), ('ma', 'manghjà'), ('st', 'stai'), ('ri', 'ringraziu'), ('cun', 'cuntentu'),
        ('fam', 'famiglia'), ('ind', 'induve'), ('sto', 'stò'),
    ],
    'cismuntincu': [('ind', 'induve'), ('in', 'induve'), ('el', 'ellu'), ('frat', 'fratellu'), ('sur', 'surella'), ('zi', 'zitellu'),
                    ('si', 'simu'), ('ma', 'manghjà'), ('sto', 'stò')],
    'pumuntincu': [('ind', 'induva'), ('in', 'induva'), ('ed', 'eddu'), ('frat', 'frateddu'), ('sur', 'suredda'), ('zi', 'ziteddu'),
                   ('so', 'socu'), ('ma', 'magnà'), ('pan', 'pani'), ('sto', 'stocu')],
}


def key(text):
    """Keyman's default search key: lowercase, accents removed."""
    decomposed = unicodedata.normalize('NFD', text.lower())
    return ''.join(c for c in decomposed if not unicodedata.combining(c)).replace('’', "'")


def read(path, status=None):
    words = {}
    for line in path.read_text(encoding='utf-8').splitlines()[1:]:
        if not line or line.startswith('#'):
            continue
        fields = line.split('\t')
        words[fields[0]] = (int(fields[1]), fields[5] if len(fields) > 5 else status)
    return words


def load(variety):
    if variety == 'old':
        return read(OLD_WORDLIST, 'old')
    words = read(DATA / 'shared.tsv')
    if variety != 'shared':
        words.update(read(DATA / f'{variety}.tsv'))
    return words


def top3(words, prefix):
    wanted = key(prefix)
    matches = [(weight, word) for word, (weight, _) in words.items() if key(word).startswith(wanted)]
    return [word for _, word in sorted(matches, key=lambda item: (-item[0], item[1]))[:3]]


def scan():
    """How many two-letter prefixes show a software term (COMPUTING) among the first three suggestions."""
    for variety in ('old', 'shared'):
        words = load(variety)
        prefixes = sorted({key(word)[:2] for word in words if len(key(word)) >= 2 and key(word)[:2].isalpha()})
        hits = []
        for prefix in prefixes:
            found = [w for w in top3(words, prefix) if w.lower() in COMPUTING]
            if found:
                hits.append(f'{prefix}:{"/".join(found)}')
        print(f'{variety:7} {len(hits)} of {len(prefixes)} prefixes: {" ".join(hits)}')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--show', action='store_true', help='print the top 3 of every prefix')
    parser.add_argument('--old', action='store_true', help='run the shared checks on the old wordlist.tsv')
    parser.add_argument('--scan', action='store_true',
                        help='count the two-letter prefixes whose top 3 holds a software term, old list and new')
    args = parser.parse_args()
    if args.scan:
        return scan()
    varieties = ['old'] if args.old else ['shared', 'cismuntincu', 'pumuntincu']
    failures = 0
    for variety in varieties:
        words = load(variety)
        checks = CHECKS['shared'] + ([] if variety in ('shared', 'old') else CHECKS[variety])
        if variety != 'shared':
            # A variety's own checks replace the shared check on the same prefix.
            own = {prefix for prefix, _ in CHECKS.get(variety, [])}
            checks = [c for c in CHECKS['shared'] if c[0] not in own] + CHECKS.get(variety, [])
        for prefix, expected in checks:
            found = top3(words, prefix)
            ok = expected in found or (variety == 'old' and expected.lower() in found)
            computing = [w for w in found if w.lower() in COMPUTING]
            if not ok:
                failures += 1
                blame = f' (pushed out by software terms: {", ".join(computing)})' if computing else ''
                print(f'FAIL {variety:12} {prefix!r:8} expected {expected!r}, got {found}{blame}')
            elif args.show:
                note = f'   software terms: {", ".join(computing)}' if computing else ''
                print(f'ok   {variety:12} {prefix!r:8} {found}{note}')
    print(f'{failures} failure(s)')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
