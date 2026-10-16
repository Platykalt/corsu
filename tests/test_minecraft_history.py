"""Offline checks of minecraft/java/history.json (Corsican for older Minecraft releases).

Mojang's English is never committed: placeholders are checked against history-placeholders.tsv, which keeps only
the key, the English hash and the placeholder signature of each pair.
"""
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('mchistory', ROOT / 'tools/mchistory.py')
mchistory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mchistory)

HISTORY = ROOT / 'minecraft/java/history.json'
SIGNATURES = ROOT / 'minecraft/java/history-placeholders.tsv'
HEX12 = re.compile(r'[0-9a-f]{12}')


class HistorySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = mchistory.load_json(HISTORY)  # refuses duplicate keys
        cls.signatures = mchistory.load_signatures()

    def entries(self):
        for key, hashes in self.history.items():
            for h, entry in hashes.items():
                yield key, h, entry

    def test_schema(self):
        self.assertGreater(len(self.history), 0)
        for key, h, entry in self.entries():
            with self.subTest(key=key, hash=h):
                self.assertRegex(h, HEX12)
                self.assertLessEqual(set(entry), set(mchistory.FIELDS))
                self.assertIsInstance(entry['co'], str)
                self.assertTrue(entry['co'].strip())
                self.assertIn(entry['kind'], mchistory.KINDS)
                self.assertIn(entry['review'], mchistory.REVIEWS)
                if entry['kind'] == 'new':
                    self.assertIsNone(entry.get('from'))
                else:
                    self.assertIsInstance(entry.get('from'), str)
                    self.assertTrue(entry['from'])

    def test_no_human_review_written_by_tools(self):
        # Human review is recorded by hand, by a speaker; the AI-written history starts with none.
        reviewed = [(k, h) for k, h, e in self.entries() if e['review'] == 'human' and not e.get('note')]
        self.assertEqual(reviewed, [])

    def test_placeholders_match_english(self):
        for key, h, entry in self.entries():
            with self.subTest(key=key, hash=h):
                self.assertIn((key, h), self.signatures, 'pair missing from history-placeholders.tsv')
                self.assertEqual(mchistory.signature(entry['co']), self.signatures[(key, h)])

    def test_placeholder_file_holds_no_english(self):
        lines = SIGNATURES.read_text(encoding='utf-8').splitlines()
        self.assertEqual(lines[0], 'key\thash\tsignature')
        for line in lines[1:]:
            key, h, sig = line.split('\t')
            self.assertRegex(h, HEX12)
            self.assertRegex(sig, r'^(-|[0-9a-z:%.$§ x+-]+)$', line)

    def test_every_pair_has_a_decision(self):
        missing = [p for p, sig in self.signatures.items() if p[1] not in self.history.get(p[0], {})]
        # Only pairs whose English is empty may stay without Corsican (the game shows nothing either way).
        self.assertLessEqual(len(missing), 3)

    def test_checker_passes_offline(self):
        errors, _ = mchistory.check(None, quiet=True)
        self.assertEqual(errors, [])


class SignatureTests(unittest.TestCase):
    def test_positions_and_conversions(self):
        s = mchistory.signature
        self.assertEqual(s('%s killed %s'), s('%2$s hà tombu à %1$s'))
        self.assertNotEqual(s('%s * %d'), s('%s * %s'))
        self.assertNotEqual(s('%s and %s'), s('%s'))
        self.assertEqual(s('%.2f seconds (%d ticks)'), s('%.2f seconde (%d tick)'))
        self.assertNotEqual(s('100%% sure'), s('100% sure'))
        self.assertNotEqual(s('a\nb'), s('a b'))
        self.assertNotEqual(s('§aGreen'), s('Verde'))

    def test_digest(self):
        # MULTIVERSION.md: first 12 hex digits of the SHA-1 of the UTF-8 English text.
        self.assertEqual(mchistory.digest('Stone'), '029690b00bcd')


if __name__ == '__main__':
    unittest.main()
