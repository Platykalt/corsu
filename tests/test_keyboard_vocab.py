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
                if entry['source'] != 'wiktionary':
                    self.assertIsNone(make_vocab.shape_problem(low), word)
                self.assertTrue(word == low or word == low[0].upper() + low[1:], word)

    def test_everyday_words_come_first(self):
        for variety in ('shared', 'cismuntincu', 'pumuntincu'):
            words = simulate.load(variety)
            checks = dict(simulate.CHECKS['shared'])
            checks.update(simulate.CHECKS.get(variety, []) if variety != 'shared' else {})
            for prefix, expected in checks.items():
                self.assertIn(expected, simulate.top3(words, prefix), f'{variety} {prefix!r}')

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


if __name__ == '__main__':
    unittest.main()
