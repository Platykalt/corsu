"""Tests for the contextual translation memory: PO parsing, engine.lookup and the tools/tm.py pipeline."""
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
spec = importlib.util.spec_from_file_location('tm', ROOT / 'tools/tm.py')
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)

PO = r'''msgid ""
msgstr ""
"Language: co\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"

#. Menu entry that opens a profile
#: src/menu.c:10 src/menu.c:12
msgctxt "menu"
msgid "Profile"
msgstr "Prufilu"

#: src/codec.c:40
msgctxt "encoding"
msgid "Profile"
msgstr "Prufilu di cudificazione"

msgid "Profile"
msgstr "Prufilu generale"

#, fuzzy
msgid "Delete"
msgstr "Squassà"

#, c-format
msgid "%d file"
msgid_plural "%d files"
msgstr[0] "%d schedariu"
msgstr[1] "%d schedarii"

msgid "Long "
"label"
msgstr "Etichetta "
"longa"

#, fuzzy
#~ msgid "Obsolete"
#~ msgstr "Antiquatu"

msgid "After an obsolete fuzzy entry"
msgstr "Dopu"
'''


def entry(app, source, target, review='upstream-reviewed', **fields):
    return tm.make_entry(app, source, source, target, review=review, **fields)


class MemoryCase(unittest.TestCase):
    """A temporary lexicon/memory directory, with no corrections file in the way."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.directory = Path(self.folder.name)
        patches = [patch.object(engine, 'MEMORY', self.directory),
                   patch.object(engine, 'USER', self.directory / 'none.tsv'),
                   patch.object(engine, 'FIXES', self.directory / 'none.tsv'),
                   patch.object(engine, '_MEMORY_CACHE', {}), patch.object(engine, '_INDEX_CACHE', {})]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(self.folder.cleanup)

    def memory(self, name, entries):
        tm.write_memory(self.directory / f'{name}.jsonl', entries,
                        {'app': entries[0]['app'], 'review': entries[0]['review'], 'source_lang': 'en'})


class PoTests(unittest.TestCase):
    def test_same_msgid_in_two_contexts_stays_two_entries(self):
        entries = tm.po_entries(PO.encode())
        self.assertEqual(entries[('menu', 'Profile')]['msgstr'], 'Prufilu')
        self.assertEqual(entries[('encoding', 'Profile')]['msgstr'], 'Prufilu di cudificazione')
        self.assertEqual(entries[(None, 'Profile')]['msgstr'], 'Prufilu generale')
        self.assertEqual(entries[('menu', 'Profile')]['comments'], ['Menu entry that opens a profile'])
        self.assertEqual(entries[('menu', 'Profile')]['references'], ['src/menu.c:10', 'src/menu.c:12'])

    def test_plurals_kept_fuzzy_and_obsolete_skipped(self):
        entries = tm.po_entries(PO.encode())
        plural = entries[(None, '%d file')]
        self.assertEqual(plural['msgid_plural'], '%d files')
        self.assertEqual(plural['msgstr'], ['%d schedariu', '%d schedarii'])
        self.assertNotIn((None, 'Delete'), entries)
        self.assertNotIn((None, 'Obsolete'), entries)
        # The obsolete entry's fuzzy flag does not leak into the next one.
        self.assertEqual(entries[(None, 'After an obsolete fuzzy entry')]['msgstr'], 'Dopu')
        self.assertEqual(entries[(None, 'Long label')]['msgstr'], 'Etichetta longa')

    def test_extract_and_po_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'app.po'
            source.write_text(PO, encoding='utf-8')
            work = tm.extract('po', source, 'Demo')
            keys = {item['key'] for item in work}
            self.assertIn('menu\x04Profile', keys)
            self.assertIn('encoding\x04Profile', keys)
            plural = next(item for item in work if item['plural'])
            self.assertEqual(plural['plural']['source_plural'], '%d files')
            self.assertEqual(plural['params'], ['%d'])
            again = tm.po_entries(tm.to_po(work).encode())
        self.assertEqual(again[('encoding', 'Profile')]['msgstr'], 'Prufilu di cudificazione')
        self.assertEqual(again[(None, '%d file')]['msgstr'], ['%d schedariu', '%d schedarii'])
        self.assertEqual(again[('menu', 'Profile')]['references'], ['src/menu.c:10', 'src/menu.c:12'])

    def test_memory_file_defaults_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'demo.jsonl'
            entries = [entry('Demo', 'Save %s', 'Arregistrà %s', origin={'repo': 'a/b', 'path': 'co.po'}),
                       entry('Demo', 'Open', 'Apre', origin={'repo': 'a/b', 'path': 'other.po'})]
            tm.write_memory(path, entries, {'app': 'Demo', 'review': 'upstream-reviewed', 'source_lang': 'en',
                                            'origin': {'repo': 'a/b', 'path': 'co.po'}})
            lines = path.read_text(encoding='utf-8').splitlines()
            self.assertNotIn('"app"', lines[1])
            back = tm.read_memory(path)
        self.assertEqual(back[0]['params'], ['%s'])
        self.assertEqual(back[0]['key'], 'Save %s')
        self.assertEqual(back[1]['origin'], {'repo': 'a/b', 'path': 'other.po'})
        self.assertEqual(back[1]['app'], 'Demo')


class LookupTests(MemoryCase):
    def setUp(self):
        super().setUp()
        self.memory('vlc', [entry('VLC media player', 'Profile', 'Prufilu di cudificazione',
                                  context={'msgctxt': 'encoding'}),
                            entry('VLC media player', 'Force Profile', 'Forzà un Prufilu', source_fr='Profil')])
        self.memory('discord', [entry('Discord', 'Profile', 'Prufilu', review='corsu-draft', source_fr='Profil')])
        self.memory('firefox', [entry('Firefox', 'Bookmarks', 'Indette'),
                                entry('Firefox for iOS', 'Bookmarks', 'Indette …')])

    def test_conflicting_translation_from_another_app_is_refused(self):
        self.assertIsNone(engine.lookup('Profile'))
        self.assertIsNone(engine.lookup('Profile', app='Firefox'))

    def test_same_app_then_same_context_wins(self):
        self.assertEqual(engine.lookup('Profile', app='Discord'), 'Prufilu')
        self.assertEqual(engine.lookup('Profile', app='VLC media player'), 'Prufilu di cudificazione')
        self.assertEqual(engine.lookup('Profile', context='encoding'), 'Prufilu di cudificazione')

    def test_abbreviated_imported_french_is_not_a_source(self):
        # VLC's "Force Profile" is "Profil" in French: only Discord's row answers "Profil".
        self.assertEqual(engine.lookup('Profil'), 'Prufilu')

    def test_agreeing_candidates_are_reused(self):
        self.assertIn(engine.lookup('Bookmarks'), ('Indette', 'Indette …'))
        self.assertIsNone(engine.lookup('Unknown label'))

    def test_generic_toolkit_decides(self):
        self.memory('wx', [entry('wxWidgets', 'Profile', 'Prufilu')])
        engine._MEMORY_CACHE.clear()
        engine._INDEX_CACHE.clear()
        self.assertEqual(engine.lookup('Profile'), 'Prufilu')

    def test_app_only_entry_answers_only_its_application(self):
        # A Minecraft decision ("Sign" = a wooden sign) must not become the Corsican of "Sign" elsewhere.
        self.memory('minecraft', [entry('Minecraft: Java Edition', 'Sign', 'Cartella', review='ai-reviewed',
                                        reuse='same-app')])
        engine._MEMORY_CACHE.clear()
        engine._INDEX_CACHE.clear()
        self.assertIsNone(engine.lookup('Sign'))
        self.assertIsNone(engine.lookup('Sign', app='Discord'))
        self.assertEqual(engine.lookup('Sign', app='Minecraft: Java Edition'), 'Cartella')

    def test_application_words_reads_reviewed_memory_of_the_application(self):
        self.memory('discord-reviewed', [entry('Discord', 'Go Live', 'In direttu', review='human-reviewed')])
        engine._MEMORY_CACHE.clear()
        lexicon = self.directory / 'lexicon.tsv'
        lexicon.write_text('# Discord: labels\n', encoding='utf-8')
        with patch.object(engine, 'WORDS', {'Go Live': 'Altru'}), patch.object(engine, 'LEXICON', lexicon):
            self.assertEqual(engine.application_words('Discord')['Go Live'], 'In direttu')
            self.assertEqual(engine.application_words('Firefox')['Go Live'], 'Altru')


class MatchTests(MemoryCase):
    def setUp(self):
        super().setUp()
        self.memory('apps', [
            entry('VLC media player', 'Profile', 'Prufilu di cudificazione', context={'msgctxt': 'encoding'}),
            entry('Discord', 'Profile', 'Prufilu'),
            entry('Firefox', 'Save', 'Arregistrà'),
            entry('Audacity', 'Save', 'Arregistrà'),
            entry('Firefox', 'Delete %s', 'Squassà %s'),
            entry('Firefox', 'Download the file', 'Scaricà u schedariu'),
        ])
        self.store = tm.Memory(directory=self.directory)

    def work(self, source, app='NewApp', **fields):
        return tm.make_entry(app, source, source, **fields)

    def test_exact_unambiguous_reuse(self):
        result = tm.match_entry(self.work('Save'), self.store)
        self.assertEqual(result['target'], 'Arregistrà')
        self.assertEqual(result['match']['reason'], 'unambiguous')
        self.assertEqual(result['review'], 'corsu-draft')

    def test_conflict_is_listed_not_applied(self):
        result = tm.match_entry(self.work('Profile'), self.store)
        self.assertIsNone(result['target'])
        self.assertEqual(result['match']['type'], 'conflict')
        self.assertEqual({app for option in result['match']['candidates'] for app in option['apps']},
                         {'VLC media player', 'Discord'})

    def test_same_app_or_context_decides_a_conflict(self):
        self.assertEqual(tm.match_entry(self.work('Profile', app='Discord'), self.store)['target'], 'Prufilu')
        result = tm.match_entry(self.work('Profile', context={'msgctxt': 'encoding'}), self.store)
        self.assertEqual(result['target'], 'Prufilu di cudificazione')
        self.assertEqual(result['match']['reason'], 'same-context')

    def test_fuzzy_match_is_only_a_suggestion(self):
        result = tm.match_entry(self.work('Download the files'), self.store)
        self.assertIsNone(result['target'])
        self.assertEqual(result['match']['type'], 'suggestion')
        self.assertEqual(result['match']['suggestions'][0]['target'], 'Scaricà u schedariu')
        self.assertGreaterEqual(result['match']['suggestions'][0]['ratio'], 0.85)

    def test_app_only_entry_is_neither_reused_nor_suggested_elsewhere(self):
        self.memory('minecraft', [entry('Minecraft: Java Edition', 'Rail', 'Ragliu', review='ai-reviewed',
                                        reuse='same-app'),
                                  entry('Minecraft: Java Edition', 'Detector Rails', 'Ragliu rilevatore',
                                        review='ai-reviewed', reuse='same-app')])
        engine._MEMORY_CACHE.clear()
        store = tm.Memory(directory=self.directory)
        result = tm.match_entry(self.work('Rail'), store)
        self.assertIsNone(result['target'])
        self.assertNotIn('match', result)
        self.assertNotIn('match', tm.match_entry(self.work('Detector Rail'), store))
        mine = tm.match_entry(self.work('Rail', app='Minecraft: Java Edition'), store)
        self.assertEqual((mine['target'], mine['match']['reason']), ('Ragliu', 'same-app'))

    def test_placeholders_must_match(self):
        self.assertEqual(tm.match_entry(self.work('Delete %s'), self.store)['target'], 'Squassà %s')

    def test_stats(self):
        work = [self.work('Save'), self.work('Profile'), self.work('Download the files'), self.work('Nothing alike')]
        counts = tm.stats(tm.match(work, self.store))
        self.assertEqual(counts['unique source strings'], 4)
        self.assertEqual(counts['exact compatible reuses'], 1)
        self.assertEqual(counts['conflicts'], 1)
        self.assertEqual(counts['suggestions'], 1)
        self.assertEqual(counts['untranslated'], 3)


class UpdateTests(unittest.TestCase):
    def test_changed_added_removed(self):
        old = [tm.make_entry('A', 'save', 'Save', 'Arregistrà', component='strings.xml', review='human-reviewed'),
               tm.make_entry('A', 'open', 'Open', 'Apre', component='strings.xml', review='human-reviewed'),
               tm.make_entry('A', 'gone', 'Gone', 'Andatu', component='strings.xml')]
        new = [tm.make_entry('A', 'save', 'Save as', None, component='strings.xml'),
               tm.make_entry('A', 'open', 'Open', None, component='strings.xml'),
               tm.make_entry('A', 'new', 'New', None, component='strings.xml')]
        result = {item['key']: item for item in tm.update(old, new)}
        self.assertEqual(result['save']['change'], 'changed')
        self.assertEqual(result['save']['review'], 'to-review')
        self.assertEqual(result['save']['previous_source'], 'Save')
        self.assertEqual(result['open']['change'], 'unchanged')
        self.assertEqual(result['open']['target'], 'Apre')
        self.assertEqual(result['new']['change'], 'added')
        self.assertEqual(result['gone']['change'], 'removed')
        # A changed source is written as fuzzy, never as a finished translation.
        self.assertIn('#, fuzzy\nmsgctxt "save"\nmsgid "Save as"', tm.to_po(list(result.values())))

    def test_command_line_pipeline(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'en.json').write_text(json.dumps({'menu': {'save': 'Save', 'open': 'Open'}}), encoding='utf-8')
            work = folder / 'work.jsonl'
            tm.main(['extract', 'json', str(folder / 'en.json'), '--app', 'Demo', '--out', str(work)])
            entries = tm.read_memory(work)
            self.assertEqual({item['key'] for item in entries}, {'menu.save', 'menu.open'})
            tm.main(['po', str(work), '--out', str(folder / 'x.po')])
            parsed = tm.po_entries((folder / 'x.po').read_bytes(), translated=False)
            self.assertIn(('menu.save', 'Save'), parsed)


if __name__ == '__main__':
    unittest.main()
