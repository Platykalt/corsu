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

    def test_application_rows_win_over_other_programs(self):
        # The same label imported from another program must not replace the one written for the application,
        # and a correction must win over both.
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            own = folder / 'lexicon.tsv'
            own.write_text('# Discord: labels\nNow Playing|En cours|In traccia di ghjucà\nMute|Rendre muet|Ammutulisce\n'
                           '# Firefox: other\nNow Playing||Altra cosa\n', encoding='utf-8')
            fixes = folder / 'fixes.tsv'
            fixes.write_text('Mute||Ammutulì\n', encoding='utf-8')
            words = {'Now Playing': 'Ripruduzzione in corsu', 'Mute': 'Silenziu', 'Other': 'Altru'}
            with patch.object(engine, 'LEXICON', own), patch.object(engine, 'FIXES', fixes), \
                    patch.object(engine, 'USER', folder / 'none.tsv'), patch.object(engine, 'WORDS', words):
                discord = engine.application_words('Discord')
        self.assertEqual(discord['Now Playing'], 'In traccia di ghjucà')
        self.assertEqual(discord['En cours'], 'In traccia di ghjucà')
        self.assertEqual(discord['Mute'], 'Ammutulì')
        self.assertEqual(discord['Other'], 'Altru')

    def test_known_contaminations_stay_fixed(self):
        # Imported rows whose French was an abbreviation of a longer English label (see lexicon/corrections.tsv).
        for french, wrong in (('Profil', 'Forzà un Prufilu'), ('Actuellement', 'Ripruduzzione in Corsu'),
                              ('Police :', 'Ozzioni di grafia'), ('Remonter', 'Navigazione in daretu'),
                              ('URL', "Metadata d'URL"), ('Curseur', 'Parametri di cursore'),
                              ('Installation', 'Assistente d’installazione')):
            self.assertNotEqual(engine.WORDS.get(french), wrong, french)
        self.assertEqual(engine.application_words('Discord', 'Vencord').get('Profil'), 'Prufilu')


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
        # The file goes in as committed, byte for byte, so the installer builds the same pack.
        self.assertEqual(lang, {'a': 'Petra', 'old': 'x'})

    def test_build_is_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            translation = self.fake_version(home, {'a': 'Stone'}, {'a': 'Petra'})
            (home / 'LICENSE.txt').write_text('license')
            with patch.dict(os.environ, {'CORSU_CACHE': directory}), \
                    patch.object(minecraft, 'TRANSLATION', translation), patch.object(minecraft, 'HERE', home), \
                    patch.object(minecraft, 'ROOT', home), patch.object(minecraft, 'GLOSSARY', home / 'none.tsv'):
                first = minecraft.build('0.0').read_bytes()
                second = minecraft.build('0.0').read_bytes()
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()


class MinecraftInstallTests(unittest.TestCase):
    def test_language_and_pack_switch_on_off_and_uninstall(self):
        import io
        from contextlib import redirect_stdout
        import corsu
        import minecraft as game
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / '.minecraft'
            folder.mkdir()
            options = folder / 'options.txt'
            options.write_text('version:4555\nlang:fr_fr\nresourcePacks:["vanilla","file/Faithful.zip"]\nfov:0.0\n')
            with patch.object(corsu, 'HOME', root), patch.object(corsu, 'DATA', root / 'data'), \
                    patch.object(corsu, 'STATE', root / 'data/state.json'), patch.object(corsu, 'CONFIG', root / 'config'), \
                    patch.object(corsu, 'PLATFORM', 'linux'), patch.dict(os.environ, {'XDG_DATA_HOME': str(root / 'share')}), \
                    redirect_stdout(io.StringIO()):
                installer = corsu.Installer()
                game.install(installer)
                installer.state['components'] = ['minecraft']
                corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
                pack = folder / 'resourcepacks' / game.PACK
                self.assertEqual(pack.read_bytes(), game.pack_from_sources())
                text = options.read_text()
                self.assertIn('lang:co_fr\n', text)
                self.assertIn('resourcePacks:["vanilla","file/Faithful.zip","file/corsu-minecraft-java.zip"]', text)
                # Minecraft rewrites the file while it runs; Corsu must keep those changes.
                options.write_text(text.replace('fov:0.0', 'fov:0.5'))
                corsu.disable(['minecraft'])
                text = options.read_text()
                self.assertIn('lang:fr_fr\n', text)
                self.assertIn('fov:0.5', text)
                self.assertNotIn(game.PACK_ID, text)
                self.assertTrue(pack.exists())
                corsu.install(['minecraft'])
                self.assertIn('lang:co_fr\n', options.read_text())
                corsu.uninstall()
                text = options.read_text()
                self.assertFalse(pack.exists())
                self.assertIn('lang:fr_fr\n', text)
                self.assertIn('resourcePacks:["vanilla","file/Faithful.zip"]', text)
                self.assertIn('fov:0.5', text)

    def test_new_game_folder_starts_in_corsican(self):
        import minecraft as game
        lines, original = game.switch_on(game.read_options(Path('/nonexistent/options.txt')))
        self.assertEqual(dict(lines)['lang'], 'co_fr')
        self.assertEqual(json.loads(dict(lines)['resourcePacks']), ['vanilla', game.PACK_ID])
        self.assertEqual(game.switch_off(lines, original), [])
