"""The keyboard vocabulary lists keyboard/data/{shared,cismuntincu,pumuntincu}.tsv: their format, their sources,
no token that cannot be a Corsican word, and everyday words that stay among the first suggestions."""
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'keyboard/data'
HEADER = ['word', 'weight', 'variant', 'source', 'license', 'status']


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, DATA / f'tools/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


make_vocab = load_module('make_vocab')
simulate = load_module('simulate')


def rows(name):
    lines = (DATA / f'{name}.tsv').read_text(encoding='utf-8').splitlines()
    return lines[0].split('\t'), [dict(zip(HEADER, line.split('\t'))) for line in lines[1:]]


class KeyboardVocabularyTests(unittest.TestCase):
    def test_format(self):
        documented = (ROOT / 'docs/keyboard-sources.md').read_text(encoding='utf-8')
        for name in ('shared', 'cismuntincu', 'pumuntincu'):
            header, entries = rows(name)
            self.assertEqual(header, HEADER, name)
            words = [entry['word'] for entry in entries]
            self.assertEqual(len(words), len(set(words)), f'{name}: a word is listed twice')
            for entry in entries:
                self.assertRegex(entry['weight'], r'^[1-9]\d*$', entry)
                self.assertIn(entry['status'], {'attested', 'corsu-lexicon', 'ai-proposal'}, entry)
                self.assertIn(entry['variant'], {'shared', 'cismuntincu', 'pumuntincu'}, entry)
                if name == 'shared':
                    self.assertEqual(entry['variant'], 'shared', entry)
                source = entry['source'].split(':')[0]
                self.assertIn(f'`{source}`', documented, f'source {source} is not described')
                self.assertEqual(entry['license'], make_vocab.LICENSES[source], entry)

    def test_honest_status(self):
        # A word that only Corsu's own lexicon has is never "attested", whatever lexicon file it comes from.
        for name in ('shared', 'cismuntincu', 'pumuntincu'):
            for entry in rows(name)[1]:
                self.assertEqual(entry['status'] == 'corsu-lexicon', entry['source'] == 'corsu-lexicon', entry)
                self.assertEqual(entry['status'] == 'ai-proposal', entry['source'] == 'ai', entry)

    def test_no_impossible_tokens(self):
        # The published 0.24.0 model had "ycbcr", "yyyy" and a Japanese "ディスコード" among its words.
        for token in ('ycbcr', 'yyyy', 'ディスコード', 'ctrl', 'json', 'entrée', 'mm', 'www'):
            self.assertTrue(make_vocab.shape_problem(token) or token in make_vocab.NOT_WORDS, token)
        for word in ('aghjunghje', 'inghjò', "l'instradamentu", 'cerchju', "nant'à", 'ghjacaru', 'perchè'):
            self.assertIsNone(make_vocab.shape_problem(word), word)
        for name in ('shared', 'cismuntincu', 'pumuntincu'):
            for entry in rows(name)[1]:
                word = entry['word']
                low = word.lower()
                self.assertNotIn(low, make_vocab.NOT_WORDS | make_vocab.PRODUCT_NAMES, word)
                # Official commune names are spelled as INSEE writes them (Ajaccio, Zévaco, Tox); curated acronyms
                # are written in capitals (BDLC).
                if entry['source'] == 'acronyms':
                    self.assertEqual(word, word.upper(), word)
                    continue
                # Official commune names, and the French, Italian and Latin spellings of historical place names
                # (sources/historical-places.tsv), are spelled as their source writes them.
                if entry['source'] != 'wiktionary' and not entry['source'].startswith(
                        ('cog:', 'historical-places:fr:', 'historical-places:it:', 'historical-places:la:')):
                    self.assertIsNone(make_vocab.shape_problem(low), word)
                if "'" in word and word.partition("'")[0] == low.partition("'")[0]:
                    # An elided form keeps the case of its listed second part: d'Aiacciu, l'Italia, l'ADECEC.
                    tail = word.partition("'")[2]
                    self.assertTrue(tail in (tail.lower(), tail[0].upper() + tail[1:].lower(), tail.upper()), word)
                    continue
                self.assertTrue(word == low or word == low[0].upper() + low[1:], word)

    def test_everyday_words_come_first(self):
        for variety in ('shared', 'cismuntincu', 'pumuntincu'):
            words = simulate.load(variety)
            checks = dict(simulate.CHECKS['shared'])
            checks.update(simulate.CHECKS.get(variety, []) if variety != 'shared' else {})
            for prefix, expected in checks.items():
                self.assertIn(expected, simulate.top3(words, prefix), f'{variety} {prefix!r}')

    def test_place_names(self):
        # Corsican place names from Wikidata (sources/places.tsv): known with their capital, so that auto-correction
        # keeps them (Zicavu was once replaced by "Cavu"), and never above the everyday words' lowest floor.
        shared = {entry['word']: entry for entry in rows('shared')[1]}
        for name in ('Zicavu', 'Aiacciu', 'Bastia', 'Portivechju', 'Corti', 'Calvi', 'Bunifaziu', 'Sartè',
                     'Bastilicaccia', 'Balagna', 'Niolu', 'Golu', 'Cintu'):
            self.assertIn(name, shared)
        for entry in shared.values():
            if entry['source'].startswith('wikidata:'):
                self.assertRegex(entry['source'], r'^wikidata:Q\d+$', entry)
                self.assertLessEqual(int(entry['weight']), make_vocab.PLACE_CAP, entry)
        words = simulate.load('shared')
        for prefix, name in (('zicav', 'Zicavu'), ('portiv', 'Portivechju'), ('bunif', 'Bunifaziu')):
            self.assertIn(name, simulate.top3(words, prefix))
        # A name never takes the place of an everyday word: ghjucà (1,000) stays ahead of Ghjuvanni.
        self.assertGreater(int(shared['ghjucà']['weight']), int(shared['Ghjuvanni']['weight']))

    def test_official_names(self):
        # A legitimate spelling typed on purpose is known, so auto-correction keeps it: the official (INSEE) name
        # Bastelicaccia next to the Corsican Bastilicaccia. The Corsican name keeps the higher weight, and no
        # official-name word outranks a Corsican place name's floor.
        shared = {entry['word']: entry for entry in rows('shared')[1]}
        for name in ('Bastelicaccia', 'Zicavo', 'Ajaccio', 'Bonifacio', 'Sartène', 'Propriano', 'Vescovato',
                     'Ghisonaccia', 'Solenzara'):
            self.assertIn(name, shared)
        for corsican, official in (('Bastilicaccia', 'Bastelicaccia'), ('Zicavu', 'Zicavo'),
                                   ('Bunifaziu', 'Bonifacio'), ('Aiacciu', 'Ajaccio')):
            self.assertGreater(int(shared[corsican]['weight']), int(shared[official]['weight']), official)
        for entry in shared.values():
            if entry['source'].startswith('cog:'):
                self.assertRegex(entry['source'], r'^cog:2[AB]\d{3}$', entry)
                self.assertLessEqual(int(entry['weight']), make_vocab.PLACE_FLOOR, entry)
                self.assertEqual(entry['word'][0], entry['word'][0].upper(), entry)
        # Vizzani (Vikipedia title, sources/place-titles.tsv) next to the Wikidata label Vezzani, never instead.
        self.assertIn('Vizzani', shared)
        self.assertIn('Vezzani', shared)
        # Same search key as a word already known: left to that word (Calvi, Corti's Corte is a common word).
        self.assertNotIn('Calvi', [e['word'] for e in shared.values() if e['source'].startswith('cog:')])

    def test_variety_forms(self):
        cismuntincu = {entry['word']: entry for entry in rows('cismuntincu')[1]}
        pumuntincu = {entry['word']: entry for entry in rows('pumuntincu')[1]}
        # Each variety's own form outranks the other's, which stays known.
        for north, south in (('simu', 'semi'), ('induve', 'induva'), ('fratellu', 'frateddu'), ('eranu', 'erani')):
            self.assertGreater(int(cismuntincu[north]['weight']), int(cismuntincu[south]['weight']))
            self.assertGreater(int(pumuntincu[south]['weight']), int(pumuntincu[north]['weight']))
        # semu is given for both groups (Vikipedia's table and U Cunghjugarellu): neither list overrides it.
        self.assertNotIn('semu', cismuntincu)
        self.assertNotIn('semu', pumuntincu)


    def test_common_words_next_to_names(self):
        # Keyman keeps a word typed exactly as the list has it. A common word written like a name is listed in
        # lowercase next to the name, so neither is turned into the other: corti (short, plural) / Corti, orsu / Orsu.
        shared = {entry['word']: entry for entry in rows('shared')[1]}
        for word in ('corti', 'orsu', 'argentu', 'mansu', 'cagna', 'magnu'):
            self.assertIn(word, shared)
            self.assertIn(word.capitalize(), shared)
            self.assertLessEqual(int(shared[word]['weight']), int(shared[word.capitalize()]['weight']), word)
        # No source yet for calvi (bald): only the name. It comes back when a source attests it (REVIEW.md).
        self.assertNotIn('calvi', shared)
        self.assertIn('Calvi', shared)
        # Curated acronyms, kept in capitals at a low weight.
        for word in ('ADECEC', 'INFCOR', 'BDLC'):
            self.assertEqual(int(shared[word]['weight']), make_vocab.ACRONYM_WEIGHT, word)
            self.assertEqual(shared[word]['source'], 'acronyms')

    def test_prose_leaves_out_foreign_passages(self):
        # Steps 5b and 5d count Vikipedia's Corsican prose only: not a title in italics, a quotation, a list of
        # references, an Italian or French sentence, a poem in Italian (keyboard/data/REVIEW.md).
        prose = make_vocab.Prose()

        def clean(text):
            return re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r'\1', text).replace("''", '')

        prose.add('A', '\n'.join([
            "U '''libru''' ''Storia di i secoli'' parla di i seculi.",
            'Ellu disse: «I secoli sò longhi».',
            'La calligrafia insegnata nelle scuole (secoli XX-XXI).',
            ':Noi siamo da secoli',
            ':Calpesti, derisi, secoli',
            '',
            ':Ghjè u ventu di i seculi',  # a Corsican verse (its own block) counts as prose
            '== Bibliugrafia ==',
            '* Secoli di storia, Roma',
            '== Storia ==',
            'I seculi passanu.']), clean)
        self.assertEqual(prose.counts['secoli'], 0)
        self.assertEqual(prose.counts['seculi'], 3)
        self.assertEqual(dict(prose.left_out['secoli']), {'italics': 1, 'quotation': 1, 'foreign-sentence': 1,
                                                          'foreign-verse': 2, 'list-section': 1})

    def test_held_back_forms(self):
        shared = {entry['word']: entry for entry in rows('shared')[1]}
        lines = [line for line in (DATA / 'held-back.tsv').read_text(encoding='utf-8').splitlines()
                 if not line.startswith('#')]
        header = lines[0].split('\t')
        held = [dict(zip(header, line.split('\t'))) for line in lines[1:]]
        self.assertEqual(header[:3], ['word', 'step', 'form_of'])
        self.assertTrue(held)
        for row in held:
            # Held back means not shipped, with a reason and the passages a reviewer can check.
            self.assertNotIn(row['word'], shared, row['word'])
            self.assertTrue(row['reason'] and row['passages'], row['word'])
        words = {row['word'] for row in held}
        # Italian quoted by Vikipedia (an image caption, the Italian anthem), and a table legend.
        self.assertIn('secoli', words)
        self.assertIn('prodottu', words)
        # Kept: Corsican prose in several articles (polvere, plural of polvera), and a form a reference writes.
        self.assertIn('polvere', shared)
        self.assertIn('ghjocanu', shared)
        self.assertNotIn('vedemu', shared)

    def test_historical_place_names(self):
        # sources/historical-places.tsv (step 8): only accepted rows are shipped, as the words of their name, in the
        # three packages alike; Vallerustie (micro-region of Castagniccia) was missing from every source before.
        places = make_vocab.historical_places()
        self.assertTrue(places)
        shared = {entry['word']: entry for entry in rows('shared')[1]}
        accepted = {row['canonical'] for row in places if row['status'] == 'accepted'}
        lists = {model: {line.split('\t')[0] for line in (ROOT / f'keyboard/{model}/source/wordlist.tsv')
                         .read_text(encoding='utf-8').splitlines() if not line.startswith('#')}
                 for model in ('platykalt.co.corsu', 'platykalt.co.corsu_cismuntincu', 'platykalt.co.corsu_pumuntincu')}
        keys = {make_vocab.fold(word) for word in shared}
        for row in places:
            if row['status'] != 'accepted':
                continue
            for word in make_vocab.name_words(row['name']):
                # Listed as written, or (a word of a longer name, Monti in Diquà da i Monti) left to the listed word
                # of the same search key, which Keyman keeps in any case typed (audit/historical-places.tsv).
                self.assertTrue(word in shared or make_vocab.fold(word) in keys, f'{row["name"]}: {word}')
                for model, words in lists.items():
                    self.assertEqual(word in words, word in shared, f'{model}: {word}')
        historical = [entry for entry in shared.values() if entry['source'].startswith('historical-places:')]
        for entry in historical:
            usage, canonical = entry['source'].split(':')[1:3]
            self.assertIn(canonical.replace('_', ' '), accepted, entry)
            self.assertEqual(entry['license'], 'GPL-3.0-or-later')
        self.assertEqual(shared['Vallerustie']['source'], 'historical-places:co:Vallerustie')
        words = simulate.load('shared')
        self.assertEqual(simulate.top3(words, 'vallerus')[:1], ['Vallerustie'])
        # Weighed as the forms added to be known: below every other word of the top 3 of each prefix of its key,
        # so a name never pushes a listed word out of the first suggestions.
        others = [(simulate.key(e['word']), int(e['weight'])) for e in shared.values()
                  if not e['source'].startswith('historical-places:')]
        for entry in historical:
            key, weight = simulate.key(entry['word']), int(entry['weight'])
            for end in range(1, len(key) + 1):
                ahead = sorted((w for k, w in others if k.startswith(key[:end])), reverse=True)[:3]
                self.assertTrue(all(w >= weight for w in ahead), f'{entry["word"]} at {key[:end]!r}: {ahead}')

    def test_historical_entries_rules(self):
        # The rules of step 8 on a small example (names chosen for the test; only the mechanism is checked here).
        entries = {'serra': dict(word='serra', weight=354), 'San': dict(word='San', weight=13802),
                   'Lurenzu': dict(word='Lurenzu', weight=429), 'terra': dict(word='terra', weight=5591),
                   'di': dict(word='di', weight=715753), 'u': dict(word='u', weight=495279),
                   'cumunu': dict(word='cumunu', weight=908)}
        before = {key: dict(entry) for key, entry in entries.items()}

        def row(name, canonical, usage='co', status='accepted', note=''):
            return dict(name=name, canonical=canonical, usage=usage, category='micro-region', period='', status=status,
                        reference='https://example.org', note=note)

        rows = [row('Vallerustie', 'Vallerustie', note='micro-region of Castagniccia'),
                row('San Lurenzu di Vallerustie', 'San Lurenzu di Vallerustie'),
                row('Terra di u Cumunu', 'Terra di u Cumunu', usage='co', status='accepted'),
                row('Serra', 'Serra'),
                row('Vallerustia', 'Vallerustie', usage='it'),
                row("Pieve d'Orezzu", "Pieve d'Orezzu", status='uncertain'),
                row('Nebbiolu', 'Nebbiolu', status='deferred')]
        new, audit = make_vocab.historical_entries(rows, entries, lambda low: 1000 if low == 'vallerustie' else 0)
        self.assertEqual(entries, before)  # listed words keep their entry and weight (serra, terra, San)
        # Words of the name only: not the note (Castagniccia), not the function words, not a word already listed.
        self.assertEqual(sorted(new), ['Serra', 'Vallerustia', 'Vallerustie'])
        self.assertEqual(new['Vallerustie']['weight'], make_vocab.PLACE_CAP)
        # A one-word name written like a common word: its own capitalised entry, below the common one.
        self.assertLess(new['Serra']['weight'], entries['serra']['weight'])
        # Another spelling weighs less than the canonical, before and after the final weights.
        self.assertLessEqual(new['Vallerustia']['weight'], make_vocab.OFFICIAL_CAP)
        new['Vallerustie']['weight'] = 30
        new['Vallerustia']['weight'] = 30
        self.assertEqual(make_vocab.cap_historical_variants(new, lambda w: new[w]['weight'] if w in new else None), 1)
        self.assertLess(new['Vallerustia']['weight'], new['Vallerustie']['weight'])
        shipped = {r['name']: r['shipped'] for r in audit}
        self.assertEqual(shipped["Pieve d'Orezzu"], 'no')
        self.assertEqual(shipped['Nebbiolu'], 'no')
        self.assertEqual(shipped['Terra di u Cumunu'], 'known')
        self.assertNotIn('Nebbiolu', new)
        self.assertNotIn('Orezzu', new)
        # Spaces and hyphens split a name; an elided word gives its name; capitals and accents are kept.
        self.assertEqual(make_vocab.name_words("San Ghjuvanni-di-Moriani (pieve) d'Orezza Pètra"),
                         ['San', 'Ghjuvanni', 'Moriani', 'Orezza', 'Pètra'])

    def test_added_forms_push_out_no_listed_word(self):
        # The forms added to be known (steps 5b-5e) weigh less than the listed words of every prefix's top 3: with
        # a cap of 100 alone, utilizatu pushed utile (92) out of "uti".
        shared = {entry['word']: (int(entry['weight']), None) for entry in rows('shared')[1]}
        for prefix, word in (('uti', 'utile'), ('ecc', 'eccezziunale'), ('urig', 'urigine')):
            self.assertIn(word, simulate.top3(shared, prefix), prefix)


if __name__ == '__main__':
    unittest.main()
