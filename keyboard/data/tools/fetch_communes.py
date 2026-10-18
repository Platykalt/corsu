#!/usr/bin/env python3
"""Fetch the official names of Corsica's 360 communes into keyboard/data/sources/communes-official.tsv.

    python3 keyboard/data/tools/fetch_communes.py            # two requests, rewrites communes-official.tsv
    python3 keyboard/data/tools/fetch_communes.py --dry-run  # print the count only

The names come from the French government's geographic API (https://geo.api.gouv.fr), which serves INSEE's Code
officiel géographique under the Licence Ouverte / Etalab 2.0. Two requests are made, one per department (2A, 2B);
nothing else is downloaded.

Why: an official name such as Bastelicaccia is a legitimate spelling, even when the Corsican name differs
(Bastilicaccia). tools/make_vocab.py adds its words at a low weight so that Keyman knows them and auto-correction
keeps them as typed, while the Corsican names keep the higher place weight (keyboard/data/REVIEW.md, "Place names").
"""
import argparse
import datetime
import json
from pathlib import Path
import urllib.request

DATA = Path(__file__).resolve().parents[1]
TARGET = DATA / 'sources/communes-official.tsv'
URL = 'https://geo.api.gouv.fr/departements/{}/communes?fields=nom,code&format=json'
USER_AGENT = 'Corsu keyboard vocabulary (https://github.com/Platykalt/corsu)'


def fetch(department):
    request = urllib.request.Request(URL.format(department), headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dry-run', action='store_true', help='print the count without writing the file')
    args = parser.parse_args()
    communes = sorted((c['code'], c['nom']) for department in ('2A', '2B') for c in fetch(department))
    if args.dry_run:
        print(len(communes), 'communes')
        return
    today = datetime.date.today().isoformat()
    lines = [
        '# Official names of the communes of Corse-du-Sud (2A) and Haute-Corse (2B), INSEE Code officiel géographique,',
        f'# fetched by keyboard/data/tools/fetch_communes.py from https://geo.api.gouv.fr on {today}',
        '# (Licence Ouverte / Etalab 2.0). Used so that Keyman knows the official spellings (Bastelicaccia, Zicavo) next',
        '# to the Corsican names of places.tsv; see keyboard/data/REVIEW.md, "Place names".',
        'code\tname',
    ] + [f'{code}\t{name}' for code, name in communes]
    TARGET.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{TARGET}: {len(communes)} communes')


if __name__ == '__main__':
    main()
