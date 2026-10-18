"""Reuse rules of the translation memory on real cases of the repository (lexicon/memory/README.md, "Reuse rules").

- Bio: Discord's correction "Biugrafia" (lexicon.tsv, Discord section) and Chrome's "Organicu" (an image style) are
  the same three letters. Each is reused in its own application, neither is borrowed by another one.
- Profil / Force Profile: VLC's French "Profil" stands for "Force Profile"; a French "Profil" elsewhere never
  becomes "Forzà un Prufilu".
- key.drop: Minecraft's English changed from "Drop Item" (1.7.2 to 1.8.9) to "Drop Selected Item" (1.9 to 26.3);
  a translation and a speaker's validation made for the old text go back to "to re-examine".
The memory of Corsu's own rows is exported from the real lexicon.tsv into a temporary folder.
"""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import engine

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'tools/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tm = load('tm')
import_translations = load('import_translations')


class CorsuRowsCase(unittest.TestCase):
    """lexicon.tsv exported as memory files (tools/import_translations.py --corsu-only), in a temporary folder."""

    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.folder.name)
        with patch.object(import_translations, 'MEMORY', cls.directory):
            import_translations.export_corsu()
        cls.entries = list(engine.memory_entries(cls.directory))
        engine._MEMORY_CACHE.pop((cls.directory, True), None)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def setUp(self):
        patches = [patch.object(engine, 'USER', self.directory / 'none.tsv'),
                   patch.object(engine, 'FIXES', self.directory / 'none.tsv'),
                   patch.object(engine, '_MEMORY_CACHE', {}), patch.object(engine, '_INDEX_CACHE', {})]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def rows(self, source):
        return [entry for entry in self.entries if source in (entry['source'], entry.get('source_fr'))]

    def work(self, source, app, **fields):
        return tm.make_entry(app, 'new.key', source, **fields)


class BioTests(CorsuRowsCase):
    def test_the_real_rows(self):
        found = {(entry['app'], entry['target']) for entry in self.rows('Bio')}
        self.assertEqual(found, {('Discord', 'Biugrafia'), ('Chromium', 'Organicu')})

    def test_correction_reused_in_its_own_application_only(self):
        memory = tm.Memory(self.entries)
        discord = tm.match_entry(self.work('Bio', 'Discord'), memory)
        self.assertEqual((discord['target'], discord['match']['reason']), ('Biugrafia', 'same-app'))
        self.assertEqual(discord['match']['provenance']['origin']['path'], 'lexicon/lexicon.tsv')
        chrome = tm.match_entry(self.work('Bio', 'Chromium'), memory)
        self.assertEqual(chrome['target'], 'Organicu')
        # A third program gets both meanings to choose from, nothing applied.
        other = tm.match_entry(self.work('Bio', 'Thunderbird'), memory)
        self.assertIsNone(other['target'])
        self.assertEqual(other['match']['type'], 'conflict')
        self.assertEqual({option['target']: option['apps'] for option in other['match']['candidates']},
                         {'Biugrafia': ['Discord'], 'Organicu': ['Chromium']})

    def test_a_single_known_translation_of_an_abbreviation_is_not_borrowed(self):
        # The memory as it was before Discord's fix: only Chrome's "Bio". The old rule ("one translation across the
        # memory") gave Discord "Organicu"; now it is a suggestion, held because "Bio" is an abbreviation.
        memory = tm.Memory([entry for entry in self.entries if entry['app'] != 'Discord'])
        result = tm.match_entry(self.work('Bio', 'Discord'), memory)
        self.assertIsNone(result['target'])
        self.assertEqual((result['match']['type'], result['match']['reason']), ('suggestion', 'abbreviation'))
        self.assertEqual([item['target'] for item in result['match']['suggestions']], ['Organicu'])

    def test_sense_collision_is_refused(self):
        # With the sense written on each entry, the right one is reused even for a new program, and the other
        # is listed as refused rather than offered.
        entries = copy.deepcopy(self.entries)
        for entry in entries:
            if entry['source'] == 'Bio' or entry.get('source_fr') == 'Bio':
                entry['sense'] = 'biography' if entry['app'] == 'Discord' else 'organic (image style)'
        memory = tm.Memory(entries)
        result = tm.match_entry(self.work('Bio', 'Thunderbird', sense='Biography'), memory)
        self.assertEqual((result['target'], result['match']['reason']), ('Biugrafia', 'same-sense'))
        self.assertEqual(result['review'], 'corsu-draft')
        self.assertEqual([(item['target'], item['reason']) for item in result['match']['refused']],
                         [('Organicu', 'other-sense')])
        # Even inside Chrome, a "Bio" written for a biography does not take the image style.
        chrome = tm.match_entry(self.work('Bio', 'Chromium', sense='biography'), memory)
        self.assertEqual(chrome['target'], 'Biugrafia')

    def test_engine_lookup_follows_the_same_rules(self):
        with patch.object(engine, 'MEMORY', self.directory):
            self.assertEqual(engine.lookup('Bio', app='Discord'), 'Biugrafia')
            self.assertEqual(engine.lookup('Bio', app='Chromium'), 'Organicu')
            self.assertIsNone(engine.lookup('Bio'))
            self.assertIsNone(engine.lookup('Bio', app='Thunderbird'))

    def test_abbreviations(self):
        for text in ('Bio', 'bio', 'Min', '&Mod', 'Min.', 'Réf.'):
            self.assertTrue(engine.abbreviation(text), text)
        for text in ('Save', 'Biographie', 'Profile', 'Open file', 'OK'):
            self.assertFalse(engine.abbreviation(text), text)


class ProfileTests(unittest.TestCase):
    """VLC's imported catalog, as committed (lexicon/memory/vlc-media-player.jsonl)."""

    @classmethod
    def setUpClass(cls):
        cls.vlc = list(engine.read_memory(ROOT / 'lexicon/memory/vlc-media-player.jsonl'))

    def test_force_profile_french_is_not_a_source(self):
        force = next(entry for entry in self.vlc if entry['source'] == 'Force Profile')
        self.assertEqual((force['source_fr'], force['target']), ('Profil', 'Forzà un Prufilu'))
        work = tm.make_entry('Discord', 'profile', 'Profil', source_lang='fr')
        result = tm.match_entry(work, tm.Memory(self.vlc))
        self.assertNotEqual(result['target'], 'Forzà un Prufilu')
        self.assertEqual(result['target'], 'Prufilu')
        self.assertEqual(result['match']['provenance']['app'], 'VLC media player')

    def test_named_sense_without_a_known_sense_is_only_a_suggestion(self):
        work = tm.make_entry('Discord', 'profile', 'Profile', sense='user profile')
        result = tm.match_entry(work, tm.Memory(self.vlc))
        self.assertIsNone(result['target'])
        self.assertEqual(result['match']['reason'], 'sense-unknown')


class ChangedSourceTests(unittest.TestCase):
    """Minecraft's key.drop across versions: keys.tsv (hash and versions of each English text), history.json
    (the Corsican of older texts) and co_fr.json (the current one). Mojang's English itself is not stored."""

    @classmethod
    def setUpClass(cls):
        java = ROOT / 'minecraft/java'
        with open(java / 'keys.tsv', encoding='utf-8', newline='') as handle:
            cls.texts = [row for row in csv.DictReader(handle, delimiter='\t') if row['key'] == 'key.drop']
        cls.history = json.loads((java / 'history.json').read_text(encoding='utf-8'))['key.drop']
        cls.current = json.loads((java / 'co_fr.json').read_text(encoding='utf-8'))['key.drop']

    def entry(self, row, target, **fields):
        return tm.make_entry('Minecraft: Java Edition', 'key.drop', '', target, source_hash=row['hash'],
                             component='co_fr.json', version=row['versions'], **fields)

    def test_real_versions(self):
        self.assertEqual([row['versions'] for row in self.texts], ['1.6.1..1.6.4', '1.7.2..1.8.9', '1.9..26.3'])

    def test_validation_of_the_old_text_goes_back_to_re_examine(self):
        old_row, new_row = self.texts[1], self.texts[2]
        old = self.entry(old_row, self.history[old_row['hash']]['co'], review='human-reviewed',
                         validation={'ai_proposal': 'AI', 'ai_review': 'AI', 'human': 'speaker answer, set mc02-3'})
        new = self.entry(new_row, None)
        result = tm.update([old], [new])[0]
        self.assertEqual(result['change'], 'changed')
        self.assertEqual(result['previous_source_hash'], old_row['hash'])
        self.assertEqual(result['review'], 'to-review')
        self.assertEqual(result['validation']['human'], 'to-re-examine')
        self.assertEqual(result['validation']['human_before'], 'speaker answer, set mc02-3')
        # The old translation is kept for reference only: the pack's text for 26.3 is a different one.
        self.assertEqual(result['target'], "Lampà l'ogettu")
        self.assertNotEqual(result['target'], self.current)

    def test_unchanged_text_keeps_its_validation(self):
        row = self.texts[2]
        validation = {'human': 'speaker answer, set mc02-3'}
        old = self.entry(row, self.current, review='human-reviewed', validation=validation)
        result = tm.update([old], [self.entry(row, None)])[0]
        self.assertEqual((result['change'], result['review'], result['validation']), ('unchanged', 'human-reviewed', validation))

    def test_match_detects_a_changed_key_against_the_memory(self):
        old_row, new_row = self.texts[1], self.texts[2]
        memory = tm.Memory([self.entry(old_row, "Lampà l'ogettu", review='ai-reviewed')])
        result = tm.match_entry(self.entry(new_row, None), memory)
        self.assertEqual(result['change'], 'changed')
        self.assertEqual(result['review'], 'to-review')
        self.assertIsNone(result['target'])
        self.assertEqual(result['match']['previous']['source_hash'], old_row['hash'])
        added = tm.match_entry(tm.make_entry('Minecraft: Java Edition', 'key.other', '', source_hash='0' * 12), memory)
        self.assertEqual(added['change'], 'added')


if __name__ == '__main__':
    unittest.main()
