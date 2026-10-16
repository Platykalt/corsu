import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import engine

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('minecraft', ROOT / 'tools/minecraft.py')
minecraft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(minecraft)


class ImportedFrenchTests(unittest.TestCase):
    def test_abbreviated_french_is_not_a_source(self):
        # VLC: "Force Profile" is "Profil" in French; "Profil" must not become "Forzà un Prufilu".
        self.assertTrue(engine.loose_french('Force Profile', 'Profil', 'Forzà un Prufilu'))
        self.assertFalse(engine.loose_french('Profile', 'Profil', 'Prufilu'))
        self.assertFalse(engine.loose_french('Not enough space', 'Espace insuffisant', 'Spaziu insufficiente'))

    def test_profile_label(self):
        self.assertEqual(engine.WORDS['Profil'], 'Prufilu')
        self.assertEqual(engine.WORDS['Force Profile'], 'Forzà un Prufilu')

    def test_loose_french_only_applies_to_imported_files(self):
        with tempfile.TemporaryDirectory() as directory:
            own = Path(directory) / 'lexicon.tsv'
            own.write_text('Force Profile|Profil|Forzà un Prufilu\n', encoding='utf-8')
            self.assertEqual(engine.load_lexicon(own)['Profil'], 'Forzà un Prufilu')
            with patch.object(engine, 'REVIEWED', [own]):
                self.assertNotIn('Profil', engine.load_lexicon(own))


class MinecraftTests(unittest.TestCase):
    def test_arguments_follow_minecraft_rules(self):
        self.assertEqual(minecraft.arguments('%s killed %s'), ({1, 2}, []))
        self.assertEqual(minecraft.arguments('%2$s hà tombu à %1$s'), ({1, 2}, []))
        self.assertEqual(minecraft.arguments('%d%% done'), ({1}, []))
        self.assertEqual(minecraft.arguments('%x')[1], ['%x'])
        self.assertEqual(minecraft.arguments('50%')[1], ['%'])

    def fake_version(self, home, english, corsican):
        folder = home / 'minecraft' / '0.0'
        folder.mkdir(parents=True)
        (folder / 'en_us.json').write_text(json.dumps(english))
        (folder / 'game-version.json').write_text(json.dumps({'pack_version': {'resource_major': 97}}))
        translation = home / 'co_fr.json'
        translation.write_text(json.dumps(corsican, ensure_ascii=False), encoding='utf-8')
        return translation

    def test_check_reports_missing_keys_and_broken_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            translation = self.fake_version(home, {'a': 'Stone', 'b': '%s fell', 'c': '§eGold'},
                                            {'a': 'Petra', 'b': 'Hè cascatu'})
            with patch.dict(os.environ, {'CORSU_CACHE': directory}), \
                    patch.object(minecraft, 'TRANSLATION', translation), \
                    patch.object(minecraft, 'GLOSSARY', home / 'none.tsv'):
                errors, _ = minecraft.check('0.0', quiet=True)
        self.assertIn('missing: c', errors)
        self.assertTrue(any(line.startswith('b: arguments') for line in errors))

    def test_build_writes_a_resource_pack_with_the_language(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            translation = self.fake_version(home, {'a': 'Stone'}, {'a': 'Petra', 'old': 'x'})
            license_file = home / 'LICENSE.txt'
            license_file.write_text('license')
            with patch.dict(os.environ, {'CORSU_CACHE': directory}), \
                    patch.object(minecraft, 'TRANSLATION', translation), \
                    patch.object(minecraft, 'HERE', home), \
                    patch.object(minecraft, 'ROOT', home), \
                    patch.object(minecraft, 'GLOSSARY', home / 'none.tsv'):
                target = minecraft.build('0.0')
            with zipfile.ZipFile(target) as archive:
                meta = json.loads(archive.read('pack.mcmeta'))
                lang = json.loads(archive.read('assets/minecraft/lang/co_fr.json'))
        self.assertEqual(meta['language']['co_fr']['name'], 'Corsu')
        self.assertEqual(meta['pack']['min_format'], 97)
        self.assertEqual(lang, {'a': 'Petra'})


if __name__ == '__main__':
    unittest.main()
