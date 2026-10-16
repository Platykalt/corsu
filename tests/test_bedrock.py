import importlib.util
import io
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('bedrock', ROOT / 'tools/bedrock.py')
bedrock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bedrock)

ENGLISH = {
    'tile.stone.name': 'Stone',
    'item.apple.name': 'Apple',
    'entity.zombie.name': 'Zombie',
    'options.done': 'Stone',            # same English as a block, but a different family: never reused
    'death.attack.fall': '%1$s hit the ground too hard',
    'item.dye.black.name': 'Black Dye',
    'tile.unknown.name': 'Mystery Block',
    'subtitles.ambiguous': 'Door creaks',
}
JAVA_ENGLISH = {
    'block.minecraft.stone': 'Stone',
    'item.minecraft.apple': 'Apple',
    'entity.minecraft.zombie': 'Zombie',
    'death.attack.fall': '%1$s hit the ground too hard',
    'item.minecraft.black_dye': 'Black dye',  # not identical (case): not reused
    'subtitles.block.door.creak': 'Door creaks',
    'subtitles.block.iron_door.creak': 'Door creaks',
}
JAVA_CORSICAN = {
    'block.minecraft.stone': 'Petra',
    'item.minecraft.apple': 'Mela',
    'entity.minecraft.zombie': 'Zombi',
    'death.attack.fall': '%1$s hà toccu a terra troppu forte',
    'item.minecraft.black_dye': 'Tintura nera',
    'subtitles.block.door.creak': 'Porta scricchjuleghja',
    'subtitles.block.iron_door.creak': 'Porta di ferru scricchjuleghja',
}


class SeedTests(unittest.TestCase):
    def setUp(self):
        self.reused, self.skipped = bedrock.seed(ENGLISH, JAVA_ENGLISH, JAVA_CORSICAN)
        self.by_key = {key: (text, java) for key, text, java in self.reused}

    def test_reuses_identical_english_in_matching_family(self):
        self.assertEqual(self.by_key['tile.stone.name'], ('Petra', 'block.minecraft.stone'))
        self.assertEqual(self.by_key['item.apple.name'], ('Mela', 'item.minecraft.apple'))
        self.assertEqual(self.by_key['entity.zombie.name'], ('Zombi', 'entity.minecraft.zombie'))
        self.assertIn('death.attack.fall', self.by_key)

    def test_other_family_different_text_or_disagreement_left_out(self):
        self.assertNotIn('options.done', self.by_key)
        self.assertNotIn('item.dye.black.name', self.by_key)
        self.assertNotIn('tile.unknown.name', self.by_key)
        self.assertNotIn('subtitles.ambiguous', self.by_key)
        self.assertEqual(self.skipped['identical English, other family'], 1)
        self.assertEqual(self.skipped['identical English, Java translations disagree'], 1)

    def test_written_lines_carry_provenance(self):
        text = bedrock.write_seed(self.reused, 'vTEST', 'J')
        lines = [line for line in text.splitlines() if not line.startswith('##')]
        self.assertEqual(len(lines), len(self.reused))
        self.assertIn('tile.stone.name=Petra\t## from-java:block.minecraft.stone', lines)
        rows, problems = bedrock.parse(text)
        self.assertEqual(problems, [])
        self.assertEqual({key: value for _, key, value, _ in rows}['tile.stone.name'], 'Petra')
        self.assertEqual(bedrock.check_text(text.encode('utf-8'), ENGLISH), [])

    def test_translation_failing_checks_not_reused(self):
        reused, skipped = bedrock.seed({'death.attack.fall': '%1$s hit the ground too hard'},
                                       {'death.attack.fall': '%1$s hit the ground too hard'},
                                       {'death.attack.fall': 'Hà toccu a terra troppu forte'})
        self.assertEqual(reused, [])
        self.assertEqual(skipped['identical English, Corsican fails Bedrock checks'], 1)


class CheckTests(unittest.TestCase):
    english = {'a.b': 'Hello %s and %1$d', 'c.d': '§eYellow~LINEBREAK~next', 'e.f': 'Page %1 of %2'}

    def errors(self, text):
        return bedrock.check_text(text.encode('utf-8'), self.english)

    def test_valid_file(self):
        self.assertEqual(self.errors('## comment\na.b=Bonghjornu %s è %1$d\t## note\nc.d=§eGhjallu~LINEBREAK~dopu\n'
                                     'e.f=Pagina %1 di %2\n'), [])

    def test_placeholder_changes(self):
        self.assertTrue(any('placeholders' in e for e in self.errors('a.b=Bonghjornu %s\n')))
        self.assertTrue(any('placeholders' in e for e in self.errors('a.b=Bonghjornu %s è %1$s\n')))
        self.assertTrue(any('placeholders' in e for e in self.errors('e.f=Pagina %1 di 2\n')))

    def test_style_linebreak_duplicates_endings(self):
        self.assertTrue(any('§' in e for e in self.errors('c.d=Ghjallu~LINEBREAK~dopu\n')))
        self.assertTrue(any('line breaks' in e for e in self.errors('c.d=§eGhjallu dopu\n')))
        self.assertTrue(any('duplicate' in e for e in self.errors('e.f=Pagina %1 di %2\ne.f=Pagina %1 di %2\n')))
        self.assertTrue(any('CR' in e for e in self.errors('e.f=Pagina %1 di %2\r\n')))
        self.assertTrue(any('final line break' in e for e in self.errors('e.f=Pagina %1 di %2')))
        self.assertTrue(any('not in en_US' in e for e in self.errors('x.y=Iè\n')))
        self.assertTrue(any('tab' in e for e in self.errors('e.f=Pagina %1 di %2 ## note\n')))


class BuildTests(unittest.TestCase):
    def test_pack_contents(self):
        manifest = (ROOT / 'minecraft/bedrock/manifest.json').read_bytes()
        self.assertEqual(bedrock.check_manifest(json.loads(manifest)), [])
        data = bedrock.make_pack(manifest, 'tile.stone.name=Petra\n', 'licence', b'\x89PNG')
        self.assertEqual(data, bedrock.make_pack(manifest, 'tile.stone.name=Petra\n', 'licence', b'\x89PNG'))
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            self.assertEqual(sorted(names), sorted(['manifest.json', 'pack_icon.png', 'texts/languages.json',
                                                    'texts/language_names.json', 'texts/co_FR.lang', 'LICENSE.txt']))
            parsed = json.loads(archive.read('manifest.json'))
            self.assertEqual(parsed['format_version'], 2)
            self.assertEqual(parsed['modules'][0]['type'], 'resources')
            self.assertEqual(json.loads(archive.read('texts/languages.json')), ['co_FR'])
            self.assertEqual(json.loads(archive.read('texts/language_names.json')), [['co_FR', 'Corsu (Corsica)']])
            self.assertTrue(all(info.date_time == (2026, 1, 1, 0, 0, 0) for info in archive.infolist()))

    def test_manifest_problems_caught(self):
        bad = {'format_version': 1, 'header': {'uuid': 'x'}, 'modules': [{'type': 'data', 'uuid': 'x'}]}
        errors = bedrock.check_manifest(bad)
        self.assertTrue(any('format_version' in e for e in errors))
        self.assertTrue(any('resources' in e for e in errors))
        self.assertTrue(any('UUID' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
