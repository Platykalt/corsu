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
    """The risks of changing someone's Minecraft folders: wrong version, lost settings or packs, files Corsu
    does not own, a running game rewriting options.txt."""

    def setUp(self):
        import io
        from contextlib import ExitStack, redirect_stdout
        import corsu
        import minecraft as game
        self.corsu, self.game = corsu, game
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / 'Pròva spaziu'
        self.root.mkdir()
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(corsu, 'HOME', self.root))
        self.stack.enter_context(patch.object(corsu, 'DATA', self.root / 'data'))
        self.stack.enter_context(patch.object(corsu, 'STATE', self.root / 'data/state.json'))
        self.stack.enter_context(patch.object(corsu, 'CONFIG', self.root / 'config'))
        self.stack.enter_context(patch.object(corsu, 'PLATFORM', 'linux'))
        self.running = set()
        self.stack.enter_context(patch.object(game, 'running_folders', lambda: self.running))
        self.stack.enter_context(patch.dict(os.environ, {'XDG_DATA_HOME': str(self.root / 'share')}))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def tearDown(self):
        self.stack.close()
        self.directory.cleanup()

    def instance(self, name, version, options=None):
        instance = self.root / 'share/PrismLauncher/instances' / name
        (instance / 'minecraft').mkdir(parents=True)
        (instance / 'mmc-pack.json').write_text(json.dumps({'components': [{'uid': 'net.minecraft', 'version': version}]}))
        if options is not None:
            (instance / 'minecraft/options.txt').write_bytes(options)
        return instance / 'minecraft'

    def install(self):
        installer = self.corsu.Installer()
        report = self.game.install(installer)
        installer.state['components'] = ['minecraft']
        self.corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
        return report

    def test_only_folders_playing_the_supported_version(self):
        good = self.instance('Corsu 26.3', '26.3', b'lang:fr_fr\n')
        old = self.instance('Vechju', '1.21.4', b'lang:fr_fr\n')
        official = self.root / '.minecraft'
        official.mkdir()
        (official / 'options.txt').write_text('lang:fr_fr\n')
        report = self.install()
        self.assertIn('lang:co_fr', (good / 'options.txt').read_text())
        self.assertEqual((old / 'options.txt').read_text(), 'lang:fr_fr\n')
        self.assertFalse((old / 'resourcepacks').exists())
        # The official folder has no launcher profile, so its version is unknown: left alone.
        self.assertEqual((official / 'options.txt').read_text(), 'lang:fr_fr\n')
        self.assertEqual(len(report['skipped']), 2)

    def test_official_launcher_follows_the_profile_used_last(self):
        official = self.root / '.minecraft'
        for version, kind, inherits in (('26.3', 'release', None), ('26.2', 'release', None),
                                        ('fabric-26.3', 'release', '26.3')):
            folder = official / 'versions' / version
            folder.mkdir(parents=True)
            data = {'id': version, 'type': kind, 'releaseTime': f'2026-0{9 if version == "26.3" else 6}-01'}
            if inherits:
                data = {'id': version, 'inheritsFrom': inherits}
            (folder / f'{version}.json').write_text(json.dumps(data))
        profiles = {'profiles': {'a': {'lastVersionId': '26.2', 'lastUsed': '2026-01-01T00:00:00Z'},
                                 'b': {'lastVersionId': 'fabric-26.3', 'lastUsed': '2026-10-01T00:00:00Z'}}}
        (official / 'launcher_profiles.json').write_text(json.dumps(profiles))
        [folder] = self.game.find_folders()
        self.assertEqual(folder.version, '26.3')
        self.assertEqual(self.game.resolve_version(official, 'latest-release'), '26.3')

    def test_settings_packs_and_line_endings_survive_on_off_and_uninstall(self):
        folder = self.instance('Corsu', '26.3', b'lang:fr_fr\r\nresourcePacks:["vanilla","file/A.zip","file/B.zip"]\r\nfov:0.0\r\n')
        options = folder / 'options.txt'
        self.install()
        self.install()
        text = options.read_bytes().decode()
        self.assertIn('resourcePacks:["vanilla","file/A.zip","file/B.zip","file/corsu-minecraft-java.zip"]\r\n', text)
        # Only the selected list: listed as incompatible too, the game skipped it at the next start (26.3).
        self.assertEqual(text.count('corsu-minecraft-java.zip'), 1)
        self.assertNotIn('incompatibleResourcePacks', text)
        self.assertNotIn('\n', text.replace('\r\n', ''))
        # The player changes settings and adds a pack while Corsu is on: all of it must survive.
        options.write_bytes(text.replace('fov:0.0', 'fov:0.5').replace('"file/B.zip",', '"file/B.zip","file/C.zip",').encode())
        self.corsu.disable(['minecraft'])
        text = options.read_bytes().decode()
        self.assertIn('lang:fr_fr\r\n', text)
        self.assertIn('resourcePacks:["vanilla","file/A.zip","file/B.zip","file/C.zip"]\r\n', text)
        self.assertIn('fov:0.5', text)
        self.assertNotIn('corsu-minecraft-java', text)
        self.corsu.install(['minecraft'])
        # The player picks English while Corsu is on: switching off must not force French back.
        options.write_bytes(options.read_bytes().replace(b'lang:co_fr', b'lang:en_us'))
        self.corsu.uninstall()
        text = options.read_bytes().decode()
        self.assertIn('lang:en_us', text)
        self.assertFalse((folder / 'resourcepacks/corsu-minecraft-java.zip').exists())

    def test_pack_listed_as_incompatible_by_0_22_0_is_taken_off_that_list(self):
        # What Corsu 0.22.0 wrote: Minecraft 26.3 then took the pack off the incompatible list without selecting it.
        folder = self.instance('Old', '26.3', b'lang:co_fr\nresourcePacks:["file/corsu-minecraft-java.zip"]\n'
                                              b'incompatibleResourcePacks:["file/corsu-minecraft-java.zip"]\n')
        self.install()
        text = (folder / 'options.txt').read_text()
        self.assertIn('resourcePacks:["file/corsu-minecraft-java.zip"]\n', text)
        self.assertIn('incompatibleResourcePacks:[]\n', text)

    def test_unreadable_options_are_never_rewritten(self):
        broken = self.instance('Broken', '26.3', b'lang:fr_fr\nresourcePacks:[vanilla, oops\n')
        latin = self.instance('Latin', '26.3', 'lang:fr_fr\nlastServer:café\n'.encode('latin-1'))
        report = self.install()
        self.assertEqual((broken / 'options.txt').read_bytes(), b'lang:fr_fr\nresourcePacks:[vanilla, oops\n')
        self.assertEqual((latin / 'options.txt').read_bytes(), 'lang:fr_fr\nlastServer:café\n'.encode('latin-1'))
        self.assertFalse((broken / 'resourcepacks').exists())
        self.assertEqual(len(report['skipped']), 2)

    def test_a_pack_or_language_the_player_had_before_stays(self):
        folder = self.instance('Hand', '26.3', b'lang:co_fr\nresourcePacks:["vanilla","corsu-minecraft-java.zip"]\n')
        pack = folder / 'resourcepacks/corsu-minecraft-java.zip'
        pack.parent.mkdir()
        pack.write_bytes(self.game.pack_from_sources())
        self.install()
        text = (folder / 'options.txt').read_text()
        self.assertIn('resourcePacks:["vanilla","corsu-minecraft-java.zip"]', text)  # no duplicate
        self.corsu.uninstall()
        self.assertTrue(pack.exists())  # it was there before Corsu: put back, not deleted
        self.assertIn('lang:co_fr', (folder / 'options.txt').read_text())
        self.assertIn('"corsu-minecraft-java.zip"', (folder / 'options.txt').read_text())

    def test_a_different_pack_with_the_same_name_is_left_alone(self):
        folder = self.instance('Other', '26.3', b'lang:fr_fr\n')
        pack = folder / 'resourcepacks/corsu-minecraft-java.zip'
        pack.parent.mkdir()
        pack.write_bytes(b'somebody else')
        report = self.install()
        self.assertEqual(pack.read_bytes(), b'somebody else')
        self.assertEqual((folder / 'options.txt').read_text(), 'lang:fr_fr\n')
        self.assertEqual(len(report['skipped']), 1)

    def test_running_game_is_left_alone_and_switching_off_waits_for_it(self):
        folder = self.instance('Live', '26.3', b'lang:fr_fr\n')
        self.running = {folder.resolve()}
        self.install()
        self.assertEqual((folder / 'options.txt').read_text(), 'lang:fr_fr\n')
        self.running = set()
        self.install()
        self.running = {folder.resolve()}
        self.corsu.disable(['minecraft'])
        self.assertIn('lang:co_fr', (folder / 'options.txt').read_text())  # not changed under a running game
        self.running = set()
        self.corsu.disable(['minecraft'])
        self.assertIn('lang:fr_fr', (folder / 'options.txt').read_text())

    def test_unwritable_folder_does_not_stop_the_others(self):
        locked = self.instance('A locked', '26.3', b'lang:fr_fr\n')
        good = self.instance('B good', '26.3', b'lang:fr_fr\n')
        real = self.corsu.Installer.write

        def write(installer, path, data, **kwargs):
            if 'A locked' in str(path):
                raise PermissionError(13, 'Permission denied')
            return real(installer, path, data, **kwargs)
        with patch.object(self.corsu.Installer, 'write', write):
            report = self.install()
        self.assertEqual((locked / 'options.txt').read_text(), 'lang:fr_fr\n')
        self.assertIn('lang:co_fr', (good / 'options.txt').read_text())
        self.assertEqual(len(report['skipped']), 1)

    def test_new_folder_without_options_starts_in_corsican(self):
        lines, original = self.game.switch_on([])
        self.assertEqual(dict(lines)['lang'], 'co_fr')
        self.assertEqual(json.loads(dict(lines)['resourcePacks']), ['vanilla', self.game.PACK_ID])
        self.assertEqual(self.game.switch_off(lines, original), [])
