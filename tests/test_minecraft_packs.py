import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import minecraft_packs as packs

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('mcversions', ROOT / 'tools/mcversions.py')
mcversions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcversions)

h = packs.digest
ENGLISH = {
    # Same English in every version: the base translation serves them all.
    'gui.done': 'Done',
    # The English changed in 1.21: the old text is another pair, never given the base's translation.
    'death.attack.fall': '%1$s hit the ground too hard',
    # A key only in old versions (renamed since): Corsican only through history.json.
    'tile.stone.name': 'Stone',
}
OLD_FALL = '%s fell too hard'


def entry(lang_format, code, number, style, supported=True):
    extension = 'json' if lang_format == 'json' else 'lang'
    return {'lang_format': lang_format, 'lang_file': f'assets/minecraft/lang/{code}.{extension}',
            'language_code': code, 'pack_format': number, 'mcmeta': style, 'supported': supported,
            'coverage': None, 'note': ''}


class Fixture:
    """A small minecraft/java folder: four releases, one per format family."""

    def __init__(self, history=None):
        self.folder = Path(tempfile.mkdtemp())
        versions = {
            '1.8.9': entry('lang', 'co_FR', 1, 'pack_format'),
            '1.12.2': entry('lang', 'co_fr', 3, 'pack_format', supported=False),
            '1.20.2': entry('json', 'co_fr', 18, 'supported_formats'),
            '26.3': entry('json', 'co_fr', 97, 'min_max'),
        }
        order = list(versions)
        (self.folder / 'versions.json').write_text(json.dumps(versions))
        (self.folder / 'VERSION').write_text('26.3\n')
        rows = [('gui.done', h('Done'), {0, 1, 2, 3}), ('death.attack.fall', h(OLD_FALL), {0, 1, 2}),
                ('death.attack.fall', h(ENGLISH['death.attack.fall']), {3}), ('tile.stone.name', h('Stone'), {0, 1})]
        lines = ['key\thash\tversions'] + [f'{k}\t{s}\t{packs.compact_versions(p, order)}' for k, s, p in rows]
        (self.folder / 'keys.tsv').write_text('\n'.join(lines) + '\n')
        (self.folder / 'co_fr.json').write_text(json.dumps({'gui.done': 'Fattu', 'death.attack.fall':
                                                            '%1$s hà toccu a terra troppu forte'}, ensure_ascii=False))
        (self.folder / 'LICENSE.txt').write_text('licence')
        if history is not None:
            (self.folder / 'history.json').write_text(json.dumps(history, ensure_ascii=False))
        self.data = packs.Data(self.folder)

    def build(self, version):
        payload, report = packs.build_pack(version, self.data)
        return zipfile.ZipFile(io.BytesIO(payload)), report, payload


class FormatsTest(unittest.TestCase):
    def test_json_and_lang_files(self):
        fixture = Fixture()
        archive, report, _ = fixture.build('26.3')
        self.assertEqual(archive.namelist(), ['pack.mcmeta', 'pack.png', 'assets/minecraft/lang/co_fr.json', 'LICENSE.txt'])
        self.assertEqual(json.loads(archive.read('assets/minecraft/lang/co_fr.json')),
                         {'death.attack.fall': '%1$s hà toccu a terra troppu forte', 'gui.done': 'Fattu'})
        archive, report, _ = fixture.build('1.12.2')
        self.assertIn('assets/minecraft/lang/co_fr.lang', archive.namelist())
        self.assertEqual(archive.read('assets/minecraft/lang/co_fr.lang').decode('utf-8'), 'gui.done=Fattu\n')
        self.assertEqual((report['translated'], report['total'], report['missing']), (1, 3, 2))

    def test_code_case(self):
        archive, _, _ = Fixture().build('1.8.9')
        self.assertIn('assets/minecraft/lang/co_FR.lang', archive.namelist())
        self.assertEqual(list(json.loads(archive.read('pack.mcmeta'))['language']), ['co_FR'])
        archive, _, _ = Fixture().build('26.3')
        self.assertEqual(list(json.loads(archive.read('pack.mcmeta'))['language']), ['co_fr'])

    def test_mcmeta_per_style(self):
        fixture = Fixture()
        packs_of = {v: json.loads(fixture.build(v)[0].read('pack.mcmeta'))['pack'] for v in ('1.8.9', '1.20.2', '26.3')}
        self.assertEqual(packs_of['1.8.9']['pack_format'], 1)
        self.assertEqual(set(packs_of['1.8.9']), {'description', 'pack_format'})
        self.assertEqual((packs_of['1.20.2']['pack_format'], packs_of['1.20.2']['supported_formats']), (18, [18, 18]))
        self.assertEqual(packs_of['26.3'], {'description': packs_of['26.3']['description'], 'min_format': 97, 'max_format': 97})
        for version in ('1.8.9', '1.20.2', '26.3'):
            raw = fixture.build(version)[0].read('pack.mcmeta')
            self.assertTrue(raw.isascii())  # escapes only: old versions do not read pack.mcmeta as UTF-8
            meta = json.loads(raw)
            self.assertEqual(mcversions.mcmeta_problems(meta, fixture.data.load().versions[version]), [])
        meta = json.loads(fixture.build('1.20.2')[0].read('pack.mcmeta'))
        meta['pack']['min_format'] = 18
        self.assertTrue(mcversions.mcmeta_problems(meta, fixture.data.versions['1.20.2']))

    def test_lang_file_refuses_what_it_cannot_hold(self):
        with self.assertRaises(ValueError):
            packs.lang_bytes({'a=b': 'x'}, 'lang')
        with self.assertRaises(ValueError):
            packs.lang_bytes({'a': 'two\nlines'}, 'lang')
        self.assertEqual(packs.lang_bytes({'a': 'x=y'}, 'lang'), b'a=x=y\n')  # split at the first '=' only


class ResolutionTest(unittest.TestCase):
    def test_history_before_base_and_changed_english_not_reused(self):
        texts = packs.texts_for('1.20.2', Fixture().data)[0]
        self.assertEqual(texts, {'gui.done': 'Fattu'})  # the old English of death.attack.fall is another pair
        history = {
            'death.attack.fall': {h(OLD_FALL): {'co': '%s hè cascatu troppu forte', 'kind': 'adapted'}},
            'tile.stone.name': {h('Stone'): {'co': 'Petra', 'kind': 'renamed', 'from': 'block.minecraft.stone'}},
            'gui.done': {h('Done'): {'co': 'Fattu !', 'kind': 'adapted'}},
        }
        data = Fixture(history).data
        self.assertEqual(packs.texts_for('1.8.9', data)[0], {'death.attack.fall': '%s hè cascatu troppu forte',
                                                              'gui.done': 'Fattu !', 'tile.stone.name': 'Petra'})
        # The history entry belongs to the old English only: 26.3 keeps its own translation.
        self.assertEqual(packs.texts_for('26.3', data)[0]['death.attack.fall'], '%1$s hà toccu a terra troppu forte')

    def test_empty_history_file(self):
        fixture = Fixture()
        (fixture.folder / 'history.json').write_text('')
        self.assertEqual(packs.texts_for('26.3', packs.Data(fixture.folder))[0]['gui.done'], 'Fattu')

    def test_deterministic(self):
        self.assertEqual(Fixture().build('1.8.9')[2], Fixture().build('1.8.9')[2])
        archive = Fixture().build('26.3')[0]
        self.assertTrue(all(info.date_time == packs.DATE for info in archive.infolist()))


class VersionsTest(unittest.TestCase):
    def test_ranges(self):
        order = ['a', 'b', 'c', 'd', 'e', 'f']
        for positions in ({0}, {0, 1}, {0, 1, 2}, {0, 2, 3, 4}, {1, 2, 3, 5}, set(range(6))):
            field = packs.compact_versions(positions, order)
            self.assertEqual(packs.parse_versions(field, order), positions)
        self.assertEqual(packs.compact_versions({0, 2, 3, 4}, order), 'a,c..e')
        with self.assertRaises(ValueError):
            packs.parse_versions('zz', order)

    def test_base_version(self):
        data = Fixture().data
        cases = {'26.3': '26.3', 'fabric-loader-0.16.9-1.20.2': '1.20.2', '1.12.2-forge-14.23.5.2860': '1.12.2',
                 '1.8.9-OptiFine_HD_U_M5': '1.8.9', 'quilt-loader-0.26.0-1.20.2': '1.20.2',
                 '1.12.2-pre1': None, '26.3-rc-1': None, '26.3-snapshot-2': None, '24w14a': None,
                 '1.8.9 and 1.12.2': None, '': None, None: None, '1.7.10': None, 'neoforge-20.2.88': '1.20.2'}
        for text, wanted in cases.items():
            self.assertEqual(packs.base_version(text, data), wanted, text)

    def test_target_only_when_supported(self):
        data = Fixture().data
        self.assertEqual(packs.target('fabric-loader-0.16.9-1.8.9', data)['language_code'], 'co_FR')
        self.assertIsNone(packs.target('1.12.2', data))
        self.assertEqual(packs.supported_versions(data), ['26.3', '1.20.2', '1.8.9'])


class PlaceholderTest(unittest.TestCase):
    def check(self, english, text, lang_format='json'):
        return mcversions.text_problems('k', english, text, lang_format)[0]

    def test_accepted(self):
        self.assertEqual(self.check('%s hit %s', '%2$s culpitu da %1$s'), [])
        self.assertEqual(self.check('%d items', '%s ogetti'), [])      # the game reads %d as %s
        self.assertEqual(self.check('Speed %.1f%%', 'Vitezza %.1f%%'), [])
        self.assertEqual(self.check('§eYes', '§eIè'), [])

    def test_caught(self):
        self.assertTrue(self.check('%s hit %s', '%s culpitu'))            # an argument lost
        self.assertTrue(self.check('%s hit %s', '%1$s culpitu da %1$s'))  # the second never shown
        self.assertTrue(self.check('%s', '%s %x'))                        # a format the game refuses
        self.assertTrue(self.check('100%%', '100 %'))                     # a lone % refused
        self.assertTrue(self.check('50%% off', '50 % menu'))
        self.assertTrue(self.check('§eYes', 'Iè'))                        # formatting code lost
        self.assertTrue(self.check('a', 'two\nlines', 'lang'))           # cannot be written in a .lang file
        self.assertTrue(self.check('a', ''))


class RealDataTest(unittest.TestCase):
    """The committed data: the base release's pack is the one src/minecraft.py builds today."""

    def test_base_pack_same_as_current(self):
        payload, report = packs.build_pack(packs.DEFAULT.load().base)
        self.assertEqual(mcversions.base_equivalent(payload), [])
        self.assertEqual(report['missing'], 0)

    def test_every_release_builds(self):
        data = packs.Data()
        for version in packs.known(data):
            payload, report = packs.build_pack(version, data)
            self.assertGreater(report['translated'], 0, version)


if __name__ == '__main__':
    unittest.main()
