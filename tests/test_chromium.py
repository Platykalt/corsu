import struct
import unittest

import chromium
import engine


def pak(strings, aliases=None, version=5):
    ids = sorted(strings)
    data = [strings[key].encode() for key in ids]
    if version == 4:
        offset = 9 + 6 * (len(ids) + 1)
        output = struct.pack('<IIB', 4, len(ids), 1)
    else:
        aliases = aliases or {}
        offset = 12 + 6 * (len(ids) + 1) + 4 * len(aliases)
        output = struct.pack('<IIHH', 5, 1, len(ids), len(aliases))
    for key, value in zip(ids, data):
        output += struct.pack('<HI', key, offset)
        offset += len(value)
    output += struct.pack('<HI', 0, offset)
    for alias, target in sorted((aliases or {}).items()):
        output += struct.pack('<HH', alias, ids.index(target))
    return output + b''.join(data)


class ChromiumTests(unittest.TestCase):
    def test_pak_round_trip_keeps_aliases(self):
        data = pak({10: 'Paramètres', 11: 'x'}, aliases={12: 10})
        parsed = engine.read_pak(data)
        self.assertEqual(parsed['aliases'], {12: 10})
        self.assertEqual(engine.make_pak(parsed), data)
        self.assertEqual(engine.read_pak(pak({1: 'a'}, version=4))['resources'], {1: b'a'})

    def test_edge_wide_pak_round_trip(self):
        strings = {70000: 'Paramètres', 70001: 'b'}
        ids = sorted(strings)
        offset = 16 + 8 * 3 + 8
        data = struct.pack('<IIII', 5, 1, 2, 1)
        for key in ids:
            data += struct.pack('<II', key, offset)
            offset += len(strings[key].encode())
        data += struct.pack('<II', 0, offset) + struct.pack('<II', 70002, 0)
        data += b''.join(strings[key].encode() for key in ids)
        parsed = engine.read_pak(data)
        self.assertEqual(parsed['aliases'], {70002: 70000})
        self.assertEqual(engine.make_pak(parsed), data)
        translated, changed = chromium.translate_pak(data)
        self.assertEqual((changed, engine.read_pak(translated)['wide']), (1, True))

    def test_pack_strings_are_translated_with_placeholders(self):
        data = pak({1: 'Paramètres', 2: 'Rilancià $1', 3: 'zzz unknown'}, aliases={4: 1})
        translated, changed = chromium.translate_pak(data)
        result = engine.read_pak(translated)
        self.assertEqual(changed, 1)
        self.assertEqual(result['resources'][1].decode(), engine.translate('Paramètres'))
        self.assertEqual(result['resources'][3], b'zzz unknown')
        self.assertEqual(result['aliases'], {4: 1})

    def test_icu_branches_translate_separately(self):
        text = '{COUNT, plural, =1 {Paramètres} other {zzz}}'
        self.assertEqual(chromium.translate_text(text),
                         '{COUNT, plural, =1 {' + engine.translate('Paramètres') + '} other {zzz}}')
        self.assertEqual(chromium.pack_texts(text), ['Paramètres', 'zzz'])

    def test_chromium_placeholders_survive(self):
        skeleton, tokens = engine.mask('Ouvrir $1 dans $2')
        self.assertEqual(tokens, ['$1', '$2'])

    def test_test_browser_hides_real_installations(self):
        import os
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'CORSU_CHROMIUM': directory}):
            (Path(directory) / 'locales').mkdir()
            (Path(directory) / 'locales/fr.pak').write_bytes(pak({1: 'Paramètres'}))
            found = chromium.browsers()
            self.assertEqual([browser.id for browser in found], ['test'])
            self.assertEqual([path.name for path in found[0].packs()], ['fr.pak'])


if __name__ == '__main__':
    unittest.main()
