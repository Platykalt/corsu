#!/usr/bin/env python3
"""Minecraft review decisions as entries of the contextual translation memory.

    python3 tools/mcmemory.py           write lexicon/memory/minecraft-java.jsonl
    python3 tools/mcmemory.py --check   exit 1 when the committed file differs from what the data gives

One entry per Corsican text that a recorded decision of the October 2026 review touches: every key of
minecraft/java/review-2026-10/APPLIED.tsv (rounds 1 and 2) and every key of round3.tsv (decisions re-examined in
round 3, including kept and deferred ones) and of round4.tsv and round5.tsv (phrasings and fit to the interface). Each entry keeps the key, the component, the versions that show it (from
keys.tsv), the sense in the game, the current Corsican, the decision with its references, and three separate
validation levels (AI proposal, AI review, human validation: `none`, or a speaker's answer from
review/answers.jsonl that the maintainer accepted, for that exact English text; `to-re-examine` once the text changed).

Mojang's English is not stored (see minecraft/java/LICENSING.md): an entry has no `source`, only `source_hash`, the
same 12-character SHA-1 that keys.tsv and history.json use. Without a source text the engine cannot offer the entry
for another program, and `"reuse": "same-app"` says so explicitly (engine.app_only).
"""
import argparse
import csv
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import tm  # noqa: E402
import review_sets  # noqa: E402

DATA = ROOT / 'minecraft/java'
REVIEW = DATA / 'review-2026-10'
OUT = ROOT / 'lexicon/memory/minecraft-java.jsonl'
APP = 'Minecraft: Java Edition'
# The commit at which each round's changes were applied.
COMMITS = {1: 'e9e3252', 2: '38d3dce', 3: None, 4: None, 5: None}
PROPOSERS = {1: 'AI review agents of 2026-10-18 (concrete names: concrete.tsv; language: language.tsv)',
             2: 'AI agent of round 2 (2026-10-18)', 3: 'AI agent E of round 3 (2026-10-18)',
             4: 'AI agent E of round 4 (2026-10-18), main-menu pair proposed by the maintainer',
             5: 'AI agent A of round 5 (2026-10-19)'}
REVIEWERS = {1: 'separate AI verifier, 2026-10-18 (verdict in APPLIED.tsv)',
             2: 'same AI agent as the proposal, against the cited sources (round 2)'}


def table(path):
    with open(path, encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def key_list(cell):
    cell = re.sub(r'^\d+ texts?:\s*', '', cell.strip())
    return [key.strip() for key in cell.split(',') if key.strip()]


def load():
    co = json.loads((DATA / 'co_fr.json').read_text(encoding='utf-8'))
    history = json.loads((DATA / 'history.json').read_text(encoding='utf-8'))
    versions = {}
    for row in table(DATA / 'keys.tsv'):
        versions.setdefault(row['key'], {})[row['hash']] = row['versions']
    return co, history, versions


def locate(name, co, history, versions):
    """(component, key, hash, versions, Corsican) of `key` (26.3) or `key@hash` (history.json)."""
    if '@' in name:
        key, digest = name.split('@', 1)
        target = history[key][digest]['co']
        return 'minecraft/java/history.json', name, digest, versions.get(key, {}).get(digest), target
    hashes = versions.get(name, {})
    digest = next((value for value, span in hashes.items() if span.endswith('26.3')), None)
    return 'minecraft/java/co_fr.json', name, digest, hashes.get(digest), co[name]


def entries():
    co, history, versions = load()
    third = {}
    for row in table(REVIEW / 'round3.tsv'):
        third[row['id']] = row
    result = {}

    def add(name, decision, round_, validation):
        component, key, digest, span, target = locate(name, co, history, versions)
        entry = tm.make_entry(APP, key, '', target, component=component, review='ai-reviewed', reuse='same-app',
                              source_hash=digest, license='GPL-3.0-or-later',
                              origin={'repo': 'Platykalt/corsu', 'path': component},
                              version=COMMITS.get(round_), fetched='2026-10-18')
        entry['params'] = None
        entry['context'] = {'versions': span, 'sense': decision.get('sense')}
        entry['decision'] = {name: value for name, value in decision.items() if name != 'sense' and value}
        entry['validation'] = dict(validation)
        result[key] = entry

    for row in table(REVIEW / 'APPLIED.tsv'):
        round_ = 2 if row['id'].startswith('R2-') else 1
        decision = {'id': row['id'], 'round': round_, 'sense': row['sense'], 'previous': row['old'],
                    'references': row['reference'], 'justification': row['justification'],
                    'verdict': row['verdict']}
        validation = {'ai_proposal': PROPOSERS[round_], 'ai_review': f"{REVIEWERS[round_]}: {row['verdict']}",
                      'human': 'none'}
        for name in key_list(row['key(s)']):
            add(name, decision, round_, validation)
    applied = {row['id']: key_list(row['key(s)']) for row in table(REVIEW / 'APPLIED.tsv')}
    for row in third.values():
        names = []
        for name in key_list(row['keys']):
            # "=B15" stands for every key of that APPLIED.tsv row.
            names += applied[name[1:]] if name.startswith('=') else [name]
        for name in names:
            key = name
            if key in result:
                entry = result[key]
                # The analysis and the full justification stay in round3.tsv (same id), once per decision.
                entry['decision']['round3'] = {'id': row['id'], 'verdict': row['verdict'],
                                               'references': row['references'], 'uncertainty': row['uncertainty'],
                                               'details': 'minecraft/java/review-2026-10/round3.tsv'}
                entry['validation']['ai_review'] += f"; round 3: {row['validation']}"
            else:
                decision = {'id': row['id'], 'round': 3, 'sense': row['sense'], 'previous': row['old'],
                            'references': row['references'], 'analysis': row['analysis'],
                            'justification': row['justification'], 'uncertainty': row['uncertainty'],
                            'verdict': row['verdict']}
                add(name, decision, 3, {'ai_proposal': 'none in round 3 (the text was kept as it was)',
                                        'ai_review': row['validation'], 'human': 'none'})
    # Rounds 4 and 5: full phrasings and fit to the interface (round4.tsv, round5.tsv). Applied rows record the
    # change; kept or open rows record the decision not to change.
    for round_ in (4, 5):
        for row in table(REVIEW / f'round{round_}.tsv'):
            applied = not row['category'].startswith(('preference (not', 'open'))
            record = {'id': row['id'], 'category': row['category'], 'previous': row['old'] if applied else None,
                      'references': row['references'], 'justification': row['justification'],
                      'uncertainty': row['uncertainty'], 'screen': row['screen'],
                      'details': f'minecraft/java/review-2026-10/round{round_}.tsv'}
            record = {name: value for name, value in record.items() if value}
            for name in key_list(row['keys']):
                if name in result:
                    result[name]['decision'][f'round{round_}'] = record
                    result[name]['validation']['ai_review'] += f"; round {round_}: {row['validation']}"
                else:
                    add(name, {'id': row['id'], 'round': round_, 'sense': row['intended_sense'], **{
                        k: v for k, v in record.items() if k != 'id'}}, round_,
                        {'ai_proposal': PROPOSERS[round_] if applied
                         else f'none in round {round_} (the text was kept as it was)',
                         'ai_review': row['validation'], 'human': 'none'})
    # Speakers' answers (review/answers.jsonl, tools/review_sets.py) count only once the maintainer accepted them,
    # and only for the exact English text they were given for.
    speakers = review_sets.human_validations()
    for name, entry in result.items():
        found = speakers.get((name.split('@', 1)[0], entry['source_hash']))
        if found:
            entry['validation']['human'] = found
    return [result[key] for key in sorted(result)]


def render():
    items = entries()
    defaults = {'app': APP, 'review': 'ai-reviewed', 'reuse': 'same-app', 'source_lang': 'en',
                'license': 'GPL-3.0-or-later', 'fetched': '2026-10-18', 'origin': {'repo': 'Platykalt/corsu'}}
    dump = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    lines = [dump({'_defaults': defaults})] + [dump(tm.compact(entry, defaults)) for entry in items]
    return '\n'.join(lines) + '\n', len(items)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--check', action='store_true', help='exit 1 if the committed file is not up to date')
    args = parser.parse_args(argv)
    text, count = render()
    if args.check:
        current = OUT.read_text(encoding='utf-8') if OUT.exists() else ''
        if current != text:
            print(f'{OUT.relative_to(ROOT)} is not up to date: run python3 tools/mcmemory.py')
            return 1
        print(f'{OUT.relative_to(ROOT)}: up to date ({count} entries)')
        return 0
    OUT.write_text(text, encoding='utf-8')
    print(f'{OUT.relative_to(ROOT)}: {count} entries')
    return 0


if __name__ == '__main__':
    sys.exit(main())
