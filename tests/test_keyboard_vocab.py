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
                if entry['source'] != 'wiktionary' and not entry['source'].startswith('cog:'):
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

    def test_added_forms_push_out_no_listed_word(self):
        # The forms added to be known (steps 5b-5e) weigh less than the listed words of every prefix's top 3: with
        # a cap of 100 alone, utilizatu pushed utile (92) out of "uti".
        shared = {entry['word']: (int(entry['weight']), None) for entry in rows('shared')[1]}
        for prefix, word in (('uti', 'utile'), ('ecc', 'eccezziunale'), ('urig', 'urigine')):
            self.assertIn(word, simulate.top3(shared, prefix), prefix)


if __name__ == '__main__':
    unittest.main()
