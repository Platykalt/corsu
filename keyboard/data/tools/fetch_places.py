#!/usr/bin/env python3
"""Fetch the Corsican names of Corsica's communes and main places from Wikidata into keyboard/data/sources/places.tsv.

    python3 keyboard/data/tools/fetch_places.py            # run the three queries and rewrite places.tsv
    python3 keyboard/data/tools/fetch_places.py --dry-run  # print the counts only

Wikidata's data is CC0 (public domain dedication). Three targeted queries go to the official query service
(https://query.wikidata.org/sparql), a few seconds apart; nothing else is downloaded:

  1. the communes of Haute-Corse and Corse-du-Sud (INSEE code 2A... or 2B...), with their label in Corsican (`co`);
  2. towns, villages, pievi, natural regions, mountains, passes, rivers, lakes, islands and capes located in Corsica
     (administrative location, physical feature or "part of" Corsica), with a Corsican label;
  3. the rivers whose French description says they are in Corsica (most rivers have no location statement).

Only the Corsican label (`rdfs:label`, language `co`) is kept, never an alias or another language's name: aliases
mix in French and Italian spellings (Coggia, Ucciani, Roglianu). The French label is copied next to it only to help
a reviewer. tools/make_vocab.py splits the labels into words and cross-checks them with the Vikipedia dump.
"""
import argparse
import datetime
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

DATA = Path(__file__).resolve().parents[1]
TARGET = DATA / 'sources/places.tsv'
ENDPOINT = 'https://query.wikidata.org/sparql'
USER_AGENT = 'Corsu keyboard vocabulary (https://github.com/Platykalt/corsu)'
PAUSE = 5  # seconds between two queries
# Kinds of places kept from query 2, by Wikidata class (the query returns every class; the others are dropped here). Towers, chapels, archaeological sites, cantons and
# arrondissements are left out: they are monuments or administrative units named after a commune.
KINDS = {
    'Q515': 'city', 'Q3957': 'town', 'Q532': 'village', 'Q486972': 'settlement', 'Q22674925': 'former settlement',
    'Q3388233': 'pieve', 'Q572995': 'region', 'Q1970725': 'region', 'Q82794': 'region', 'Q6465': 'department',
    'Q8502': 'mountain', 'Q207326': 'mountain', 'Q46831': 'mountain range', 'Q133056': 'pass', 'Q2231510': 'pass',
    'Q4022': 'river', 'Q47521': 'river', 'Q23397': 'lake', 'Q211302': 'lake', 'Q3253281': 'lagoon',
    'Q23442': 'island', 'Q33837': 'islands', 'Q1402592': 'islands', 'Q185113': 'cape', 'Q1026259': 'calanque',
}
COMMUNES = '''
SELECT ?item ?co ?fr WHERE {
  ?item wdt:P31 wd:Q484170 ; wdt:P374 ?insee .
  FILTER(STRSTARTS(?insee, "2A") || STRSTARTS(?insee, "2B"))
  ?item rdfs:label ?co FILTER(LANG(?co) = "co")
  OPTIONAL { ?item rdfs:label ?fr FILTER(LANG(?fr) = "fr") }
}'''
PLACES = '''
SELECT DISTINCT ?item ?co ?fr ?class WHERE {
  { VALUES ?area { wd:Q3335 wd:Q3336 wd:Q14112 } ?item wdt:P131+ ?area }
  UNION { ?item wdt:P706 wd:Q14112 } UNION { ?item wdt:P361 wd:Q14112 }
  UNION { ?item wdt:P31 wd:Q3388233 }
  ?item rdfs:label ?co FILTER(LANG(?co) = "co")
  ?item wdt:P31 ?class .
  OPTIONAL { ?item rdfs:label ?fr FILTER(LANG(?fr) = "fr") }
}'''
RIVERS = '''
SELECT DISTINCT ?item ?co ?fr WHERE {
  VALUES ?class { wd:Q4022 wd:Q47521 }
  ?item wdt:P31 ?class ; wdt:P17 wd:Q142 ; schema:description ?description .
  FILTER(LANG(?description) = "fr" && CONTAINS(?description, "Corse"))
  ?item rdfs:label ?co FILTER(LANG(?co) = "co")
  OPTIONAL { ?item rdfs:label ?fr FILTER(LANG(?fr) = "fr") }
}'''


def query(sparql):
    url = ENDPOINT + '?' + urllib.parse.urlencode({'query': sparql, 'format': 'json'})
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT,
                                                   'Accept': 'application/sparql-results+json'})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)['results']['bindings']


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dry-run', action='store_true', help='print the counts, do not write places.tsv')
    args = parser.parse_args()
    places = {}  # qid -> (label, kind, French label)
    for number, (sparql, kind) in enumerate(((COMMUNES, 'commune'), (PLACES, None), (RIVERS, 'river'))):
        if number:
            time.sleep(PAUSE)
        for row in query(sparql):
            qid = row['item']['value'].rsplit('/', 1)[1]
            row_kind = kind or KINDS.get(row['class']['value'].rsplit('/', 1)[1])
            if row_kind is None:
                continue
            if qid in places and places[qid][1] == 'commune':
                continue  # a commune also found as a village or a pieve stays a commune
            places[qid] = (row['co']['value'].strip(), row_kind, row.get('fr', {}).get('value', ''))
    kinds = {}
    for _, kind, _ in places.values():
        kinds[kind] = kinds.get(kind, 0) + 1
    print(f'{len(places)} places:', ', '.join(f'{kind} {count}' for kind, count in sorted(kinds.items())))
    if args.dry_run:
        return
    today = datetime.date.today().isoformat()
    lines = [
        '# Corsican names (Wikidata label in language "co") of the communes and main places of Corsica, fetched by',
        f'# keyboard/data/tools/fetch_places.py from {ENDPOINT} on {today}. Wikidata data is CC0 1.0.',
        '# label = the Corsican label as Wikidata has it; label_fr = the French label, for reviewers only (not used).',
        '# tools/make_vocab.py splits each label into words; see keyboard/data/REVIEW.md, "Place names".',
        'qid\tlabel\tkind\tlabel_fr',
    ]
    for qid, (label, kind, french) in sorted(places.items(), key=lambda item: (item[1][1], item[1][0], item[0])):
        lines.append(f'{qid}\t{label}\t{kind}\t{french}')
    TARGET.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(TARGET)


if __name__ == '__main__':
    main()
