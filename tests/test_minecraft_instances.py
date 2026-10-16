"""Which game folders Corsu finds, which version each one plays, which pack it gets, and what happens when an
instance moves to another game version. Every folder is a fake under a temporary HOME; minecraft_packs is replaced
by a fake with a few versions, so these tests do not depend on the committed translation data."""
import io
from contextlib import ExitStack, redirect_stdout
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch


class FakePacks:
    """minecraft_packs' interface over a few versions: language code case and pack format as the real ones."""
    VERSIONS = {'26.3': ('co_fr', 97), '1.21.1': ('co_fr', 34), '1.21.4': ('co_fr', 46), '1.20.1': ('co_fr', 15),
                '1.12.2': ('co_fr', 3), '1.10.2': ('co_FR', 2)}

    @classmethod
    def target(cls, version):
        if version == '1.7.10':
            return {'supported': False, 'note': 'not checked in the game yet', 'language_code': 'co_FR'}
        if version not in cls.VERSIONS:
            return None
        code, pack_format = cls.VERSIONS[version]
        return {'lang_format': 'json', 'language_code': code, 'pack_format': pack_format, 'supported': True,
                'coverage': {'translated': 90, 'total': 100}, 'note': ''}

    @classmethod
    def build_pack(cls, version):
        assert cls.target(version) and cls.target(version)['supported'], version
        return f'pack for {version}'.encode(), {'translated': 80, 'total': 100, 'missing': 20}

    @staticmethod
    def base_version(text):
        found = [token for token in re.findall(r'(?<![\w.])(\d+\.\d+(?:\.\d+)?)(?![\w.])', text or '')
                 if token.startswith('1.') or 24 < int(token.split('.')[0]) < 40]
        return found[0] if found else None

    @classmethod
    def supported_versions(cls):
        return list(cls.VERSIONS)


class InstancesTests(unittest.TestCase):
    def setUp(self):
        import corsu
        import minecraft as game
        self.corsu, self.game = corsu, game
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / 'Pròva spaziu'
        self.root.mkdir()
        self.share = self.root / 'share'
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(corsu, 'HOME', self.root))
        self.stack.enter_context(patch.object(corsu, 'DATA', self.root / 'data'))
        self.stack.enter_context(patch.object(corsu, 'STATE', self.root / 'data/state.json'))
        self.stack.enter_context(patch.object(corsu, 'CONFIG', self.root / 'config'))
        self.stack.enter_context(patch.object(corsu, 'PLATFORM', 'linux'))
        self.stack.enter_context(patch.object(game, 'minecraft_packs', FakePacks))
        self.running = set()
        self.stack.enter_context(patch.object(game, 'running_folders', lambda: self.running))
        environment = {key: value for key, value in os.environ.items() if key != 'PRISMLAUNCHER_DATA_DIR'}
        environment['XDG_DATA_HOME'] = str(self.share)
        self.stack.enter_context(patch.dict(os.environ, environment, clear=True))
        self.output = self.stack.enter_context(redirect_stdout(io.StringIO()))

    def tearDown(self):
        self.stack.close()
        self.directory.cleanup()

    def instance(self, name, version, options=None, loader=None, instances=None, game_folder='minecraft'):
        instance = (instances or self.share / 'PrismLauncher/instances') / name
        (instance / game_folder).mkdir(parents=True)
        components = [{'uid': 'org.lwjgl3', 'version': '3.3.3'}, {'uid': 'net.minecraft', 'version': version}]
        if loader:
            components.append({'uid': loader[0], 'version': loader[1]})
        (instance / 'mmc-pack.json').write_text(json.dumps({'components': components, 'formatVersion': 1}))
        (instance / 'instance.cfg').write_text(f'[General]\nInstanceType=OneSix\nname={name}\n')
        if options is not None:
            (instance / game_folder / 'options.txt').write_bytes(options)
        return instance / game_folder

    def set_version(self, folder, version):
        pack = json.loads((folder.parent / 'mmc-pack.json').read_text())
        for component in pack['components']:
            if component['uid'] == 'net.minecraft':
                component['version'] = version
        (folder.parent / 'mmc-pack.json').write_text(json.dumps(pack))

    def install(self):
        installer = self.corsu.Installer()
        report = self.game.install(installer)
        installer.state['components'] = ['minecraft']
        self.corsu.STATE.write_text(json.dumps(installer.state), encoding='utf-8')
        return report

    def instance_report(self, report, folder):
        return next(item for item in report['result']['instances'] if Path(item['location']) == folder)

    # Detection

    def test_prism_fabric_and_neoforge_instances_play_their_base_version(self):
        fabric = self.instance('Fabric', '1.21.1', b'lang:en_us\n', ('net.fabricmc.fabric-loader', '0.16.9'))
        neoforge = self.instance('NeoForge', '1.20.1', b'lang:en_us\n', ('net.neoforged', '47.1.106'))
        folders = {folder.path: folder for folder in self.game.find_folders()}
        self.assertEqual((folders[fabric].version, folders[fabric].loader), ('1.21.1', 'Fabric 0.16.9'))
        self.assertEqual((folders[neoforge].version, folders[neoforge].loader), ('1.20.1', 'NeoForge 47.1.106'))
        report = self.install()
        self.assertEqual((fabric / 'resourcepacks/corsu-minecraft-java.zip').read_bytes(), b'pack for 1.21.1')
        self.assertEqual((neoforge / 'resourcepacks/corsu-minecraft-java.zip').read_bytes(), b'pack for 1.20.1')
        self.assertIn('lang:co_fr', (fabric / 'options.txt').read_text())
        item = self.instance_report(report, fabric)
        self.assertEqual(item['activation'], 'active')
        self.assertEqual(item['loader'], 'Fabric 0.16.9')
        self.assertEqual((item['coverage']['translated'], item['coverage']['total'], item['coverage']['state']),
                         (80, 100, 'partial'))
        self.assertEqual(report['result']['activation'], 'active')

    def test_old_instance_without_mmc_pack_uses_instance_cfg(self):
        instance = self.share / 'multimc/instances/Old'
        (instance / 'minecraft').mkdir(parents=True)
        (instance / 'instance.cfg').write_text('InstanceType=Legacy\nIntendedVersion=1.12.2\n')
        [folder] = self.game.find_folders()
        self.assertEqual((folder.version, folder.launcher), ('1.12.2', 'MultiMC'))

    def test_custom_instance_folder_relative_and_absolute(self):
        data = self.share / 'PrismLauncher'
        data.mkdir(parents=True)
        elsewhere = self.root / 'Ghjochi Minecraft'
        (data / 'prismlauncher.cfg').write_text(
            # QSettings writes paths with forward slashes (or doubled backslashes), never single backslashes.
            f'[General]\nConfigVersion=1.3\nInstanceDir=Mes instances\nAdditionalInstanceDirs="{elsewhere.as_posix()}"\n')
        relative = self.instance('A', '26.3', instances=data / 'Mes instances')
        absolute = self.instance('B', '1.21.1', instances=elsewhere)
        ignored = self.instance('C', '26.3')  # instances/ is no longer where Prism Launcher looks
        paths = [folder.path for folder in self.game.find_folders()]
        self.assertEqual(paths, [relative, absolute])
        self.assertNotIn(ignored, paths)
        (data / 'prismlauncher.cfg').write_text(f'[General]\nInstanceDir={elsewhere.as_posix()}\n')
        self.assertEqual([folder.path for folder in self.game.find_folders()], [absolute])

    def test_flatpak_and_data_dir_variable(self):
        flatpak = self.instance('F', '26.3', instances=self.root / '.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances')
        portable = self.root / 'Prism portable/UserData'
        own = self.instance('P', '26.3', instances=portable / 'instances')
        self.assertEqual([folder.path for folder in self.game.find_folders()], [flatpak])
        os.environ['PRISMLAUNCHER_DATA_DIR'] = str(portable)
        self.assertEqual({folder.path for folder in self.game.find_folders()}, {flatpak, own})

    def test_dot_minecraft_only_when_minecraft_does_not_exist(self):
        dot = self.instance('Dot', '26.3', b'lang:en_us\n', game_folder='.minecraft')
        both = self.instance('Both', '26.3', b'lang:en_us\n')
        (both.parent / '.minecraft').mkdir()
        paths = {folder.path for folder in self.game.find_folders()}
        self.assertEqual(paths, {dot, both})
        self.install()
        self.assertIn('lang:co_fr', (dot / 'options.txt').read_text())
        self.assertFalse((both.parent / '.minecraft/resourcepacks').exists())

    def official(self, profiles, versions):
        official = self.root / '.minecraft'
        for version, data in versions.items():
            (official / 'versions' / version).mkdir(parents=True)
            (official / 'versions' / version / f'{version}.json').write_text(json.dumps({'id': version, **data}))
        official.mkdir(exist_ok=True)
        (official / 'launcher_profiles.json').write_text(json.dumps({'profiles': profiles}))
        return official

    def test_official_launcher_fabric_profile_inherits_its_version(self):
        official = self.official(
            {'f': {'name': 'Fabric', 'lastVersionId': 'fabric-loader-0.16.9-1.21.1', 'lastUsed': '2026-10-01T00:00:00Z'}},
            {'1.21.1': {'type': 'release', 'releaseTime': '2024-08-08'},
             'neoforge-21.1.77': {'inheritsFrom': '1.21.1', 'libraries': [{'name': 'net.neoforged:neoforge:21.1.77'}]},
             'fabric-loader-0.16.9-1.21.1': {'inheritsFrom': '1.21.1', 'mainClass': 'net.fabricmc.loader.impl.launch.knot.KnotClient',
                                             'libraries': [{'name': 'net.fabricmc:fabric-loader:0.16.9'}]}})
        (official / 'options.txt').write_text('lang:fr_fr\n')
        [folder] = self.game.find_folders()
        self.assertEqual((folder.version, folder.loader), ('1.21.1', 'Fabric'))
        self.assertEqual(self.game.version_details(official, '1.20.1-forge-47.2.0'), ('1.20.1', 'Forge'))  # no JSON
        self.assertEqual(self.game.version_details(official, 'neoforge-21.1.77'), ('1.21.1', 'NeoForge'))
        self.install()
        self.assertIn('lang:co_fr', (official / 'options.txt').read_text())
        self.assertEqual((official / 'resourcepacks/corsu-minecraft-java.zip').read_bytes(), b'pack for 1.21.1')

    def test_official_launcher_jar_field_and_inheritance_loop(self):
        official = self.official({}, {'1.12.2-OptiFine_HD_U_G5': {'jar': '1.12.2'}, '1.12.2': {'type': 'release'},
                                      'a': {'inheritsFrom': 'b'}, 'b': {'inheritsFrom': 'a'}})
        self.assertEqual(self.game.version_details(official, '1.12.2-OptiFine_HD_U_G5'), ('1.12.2', 'OptiFine'))
        self.assertEqual(self.game.version_details(official, 'a')[0], None)

    def test_shared_game_folder_follows_the_last_profile_and_says_what_the_others_see(self):
        shared = self.root / 'Shared'
        shared.mkdir()
        self.official({'new': {'name': 'Nova', 'lastVersionId': '1.21.1', 'gameDir': str(shared), 'lastUsed': '2026-10-02T00:00:00Z'},
                       'old': {'name': 'Vechja', 'lastVersionId': '1.20.1', 'gameDir': str(shared), 'lastUsed': '2026-01-01T00:00:00Z'},
                       'same': {'name': 'Listessa', 'lastVersionId': '1.21.1', 'gameDir': str(shared), 'lastUsed': '2025-01-01T00:00:00Z'}},
                      {'1.21.1': {'type': 'release'}, '1.20.1': {'type': 'release'}})
        report = self.install()
        self.assertEqual((shared / 'resourcepacks/corsu-minecraft-java.zip').read_bytes(), b'pack for 1.21.1')
        item = self.instance_report(report, shared)
        self.assertEqual(item['activation'], 'active')
        self.assertIn('pack built for 1.21.1', item['note'])
        self.assertIn('"Vechja" (1.20.1) will show it as incompatible', item['note'])
        self.assertNotIn('Listessa', item['note'])
        self.assertNotIn('overlays', item['note'])  # 1.20.1 is older than 1.20.2

    def test_shared_folder_of_recent_versions_mentions_overlays(self):
        self.official({'new': {'name': 'Nova', 'lastVersionId': '26.3', 'lastUsed': '2026-10-02T00:00:00Z'},
                       'old': {'name': 'Vechja', 'lastVersionId': '1.21.4', 'lastUsed': '2026-01-01T00:00:00Z'}},
                      {'26.3': {'type': 'release'}, '1.21.4': {'type': 'release'}})
        report = self.install()
        self.assertIn('overlays', report['result']['instances'][0]['note'])

    # Version changes

    def test_version_change_reinstalls_and_changes_the_language_case(self):
        folder = self.instance('Moving', '1.10.2', b'lang:fr_FR\nresourcePacks:["vanilla","file/A.zip"]\n')
        options = folder / 'options.txt'
        pack = folder / 'resourcepacks/corsu-minecraft-java.zip'
        self.install()
        self.assertIn('lang:co_FR\n', options.read_text())
        self.assertEqual(pack.read_bytes(), b'pack for 1.10.2')
        self.set_version(folder, '1.12.2')
        report = self.install()
        text = options.read_text()
        self.assertIn('lang:co_fr\n', text)
        self.assertIn('resourcePacks:["vanilla","file/A.zip","file/corsu-minecraft-java.zip"]\n', text)
        self.assertEqual(pack.read_bytes(), b'pack for 1.12.2')
        self.assertEqual(self.instance_report(report, folder)['version'], '1.12.2')
        self.corsu.uninstall()
        text = options.read_text()
        self.assertIn('lang:fr_FR\n', text)  # what the player had before the first installation
        self.assertIn('resourcePacks:["vanilla","file/A.zip"]\n', text)
        self.assertFalse(pack.exists())

    def test_a_pack_changed_by_the_player_is_not_replaced_for_another_version(self):
        folder = self.instance('Moving', '1.21.1', b'lang:fr_fr\n')
        self.install()
        pack = folder / 'resourcepacks/corsu-minecraft-java.zip'
        pack.write_bytes(b'edited by the player')
        self.set_version(folder, '26.3')
        report = self.install()
        self.assertEqual(pack.read_bytes(), b'edited by the player')
        self.assertIn('changed since', self.instance_report(report, folder)['reason'])

    def test_moving_to_a_version_without_pack_switches_the_folder_off(self):
        folder = self.instance('Moving', '1.21.1', b'lang:fr_fr\nresourcePacks:["vanilla","file/A.zip"]\nfov:0.0\n')
        options = folder / 'options.txt'
        self.install()
        # The player adds a pack after Corsu's, then moves the instance to 1.7.10.
        options.write_text(options.read_text().replace('"file/corsu-minecraft-java.zip"', '"file/corsu-minecraft-java.zip","file/B.zip"'))
        self.set_version(folder, '1.7.10')
        report = self.install()
        text = options.read_text()
        self.assertIn('lang:fr_fr\n', text)
        self.assertIn('resourcePacks:["vanilla","file/A.zip","file/B.zip"]\n', text)
        self.assertIn('fov:0.0', text)
        item = self.instance_report(report, folder)
        self.assertEqual(item['activation'], 'blocked')
        self.assertIn('plays 1.7.10', item['reason'])
        self.assertIn('not checked in the game yet', item['reason'])
        self.assertIn('taken off', item['reason'])
        state = self.corsu.load_state()
        self.assertNotIn(str(options), state['files'])
        # The inactive pack file stays recorded, so uninstalling still removes it.
        self.corsu.uninstall()
        self.assertFalse((folder / 'resourcepacks/corsu-minecraft-java.zip').exists())
        self.assertIn('lang:fr_fr\n', options.read_text())

    def test_switching_off_keeps_a_language_chosen_since(self):
        folder = self.instance('Moving', '1.21.1', b'lang:fr_fr\n')
        options = folder / 'options.txt'
        self.install()
        options.write_text(options.read_text().replace('lang:co_fr', 'lang:en_us'))
        self.set_version(folder, '1.21.9')
        self.install()
        self.assertIn('lang:en_us', options.read_text())
        self.assertNotIn('corsu-minecraft-java', options.read_text())

    def test_unsupported_folder_never_switched_is_not_touched(self):
        folder = self.instance('Other', '1.21.9', b'lang:fr_fr\nresourcePacks:["file/corsu-minecraft-java.zip"]\n')
        report = self.install()
        self.assertEqual((folder / 'options.txt').read_text(), 'lang:fr_fr\nresourcePacks:["file/corsu-minecraft-java.zip"]\n')
        self.assertIn('Corsu has a pack for 1.10.2, 1.12.2, 1.20.1', report['skipped'][0]['reason'])

    def test_running_folder_is_left_alone_even_when_its_version_changed(self):
        folder = self.instance('Live', '1.21.1', b'lang:fr_fr\n')
        self.install()
        self.set_version(folder, '1.7.10')
        self.running = {folder.resolve()}
        report = self.install()
        self.assertIn('lang:co_fr', (folder / 'options.txt').read_text())
        item = self.instance_report(report, folder)
        self.assertEqual(item['activation'], 'blocked')
        self.assertIn('close it and run Corsu again', item['reason'])
        self.assertTrue(item['action'])

    # Records written by Corsu 0.22.0

    def old_state(self, folder, options_text):
        options = folder / 'options.txt'
        options.write_text(options_text)
        pack = folder / 'resourcepacks/corsu-minecraft-java.zip'
        pack.parent.mkdir()
        pack.write_bytes(b'0.22.0 pack')
        state = {'files': {
            str(pack): {'backup': None, 'mode': None, 'toggle': False, 'installed_sha256': self.corsu.digest(b'0.22.0 pack'),
                        'component': 'minecraft'},
            str(options): {'backup': None, 'mode': None, 'toggle': True, 'component': 'minecraft',
                           'options_original': {'lang': 'fr_fr',
                                                'resourcePacks': {'present': True, 'had_pack': False},
                                                'incompatibleResourcePacks': {'present': False, 'had_pack': False}},
                           'installed_sha256': self.corsu.digest(options.read_bytes())}},
            'components': ['minecraft'], 'enabled': True}
        self.corsu.STATE.parent.mkdir(parents=True, exist_ok=True)
        self.corsu.STATE.write_text(json.dumps(state), encoding='utf-8')
        return options, pack

    def test_0_22_0_records_install_over_and_uninstall(self):
        folder = self.instance('Old', '26.3')
        options, pack = self.old_state(folder, 'lang:co_fr\nresourcePacks:["vanilla","file/corsu-minecraft-java.zip"]\n'
                                               'incompatibleResourcePacks:["file/corsu-minecraft-java.zip"]\n')
        self.install()
        text = options.read_text()
        self.assertIn('incompatibleResourcePacks:[]\n', text)
        self.assertEqual(pack.read_bytes(), b'pack for 26.3')
        self.corsu.uninstall()
        text = options.read_text()
        self.assertIn('lang:fr_fr\n', text)
        self.assertIn('resourcePacks:["vanilla"]\n', text)
        self.assertNotIn('corsu', text)
        self.assertFalse(pack.exists())

    def test_0_22_0_records_switch_off_when_the_version_has_no_pack(self):
        folder = self.instance('Old', '1.7.10')
        options, pack = self.old_state(folder, 'lang:co_fr\nresourcePacks:["vanilla","file/corsu-minecraft-java.zip"]\n'
                                               'incompatibleResourcePacks:["file/corsu-minecraft-java.zip"]\n')
        self.install()
        text = options.read_text()
        self.assertEqual(text, 'lang:fr_fr\nresourcePacks:["vanilla"]\n')
        self.assertEqual(pack.read_bytes(), b'0.22.0 pack')  # not rebuilt for a version without a pack

    def test_0_22_0_records_uninstall_directly(self):
        folder = self.instance('Old', '26.3')
        options, pack = self.old_state(folder, 'lang:co_fr\nresourcePacks:["vanilla","file/corsu-minecraft-java.zip"]\n'
                                               'incompatibleResourcePacks:["file/corsu-minecraft-java.zip"]\n')
        self.corsu.uninstall()
        self.assertEqual(options.read_text(), 'lang:fr_fr\nresourcePacks:["vanilla"]\n')
        self.assertFalse(pack.exists())

    # The report

    def test_result_has_the_status_shape(self):
        good = self.instance('Good', '26.3', b'lang:fr_fr\n')
        self.instance('Unknown', '1.99', b'lang:fr_fr\n')
        report = self.install()
        result = report['result']
        self.assertEqual(result['activation'], 'partial')
        self.assertEqual(result['operation'], 'install')
        for item in result['instances']:
            self.assertLessEqual({'kind', 'location', 'version', 'activation', 'reason', 'action', 'coverage', 'loader'}, set(item))
            self.assertLessEqual({'state', 'translated', 'total', 'note'}, set(item['coverage']))
        self.assertEqual(result['coverage']['translated'], 80)
        self.assertEqual([item['folder'] for item in report['installed']], [str(good)])
        self.assertEqual(len(report['skipped']), 1)
        json.dumps(report)

    def test_the_pack_is_built_once_per_version(self):
        for name in ('A', 'B', 'C'):
            self.instance(name, '26.3', b'lang:fr_fr\n')
        with patch.object(FakePacks, 'build_pack', wraps=FakePacks.build_pack) as build:
            self.install()
        self.assertEqual(build.call_count, 1)


if __name__ == '__main__':
    unittest.main()
