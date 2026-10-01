"""Tests for the translation engine and the catalog formats it writes."""
from pathlib import Path
import unittest

import corsu
import engine


class TranslationTests(unittest.TestCase):
    def test_placeholder_templates_keep_every_argument(self):
        self.assertEqual(engine.translate('Redémarrer { -brand-short-name }'), 'Rilancià { -brand-short-name }')
        self.assertEqual(engine.translate('Page %1 de %2'), 'Pagina %1 di %2')
        self.assertEqual(engine.translate('Obtenir { -mozilla-vpn-brand-name }'),
                         'Ottene { -mozilla-vpn-brand-name }')

    def test_accelerator_marker_is_preserved(self):
        self.assertEqual(engine.translate('&Cancel'), '&Abbandunà')
        self.assertEqual(engine.translate('Co&uper'), 'Ta&glià')
        self.assertEqual(engine.translate('_Save'), 'Arregi_strà')

    def test_letter_case_and_trailing_punctuation(self):
        self.assertEqual(engine.translate('inconnu'), 'scunnisciutu')
        self.assertEqual(engine.translate('Enregistrer…'), 'Arregistrà…')
        self.assertEqual(engine.translate('Erreur :'), 'Sbagliu:')

    def test_composed_labels_need_every_part(self):
        self.assertEqual(engine.translate('Paramètres — Général'), 'Parametri — Generale')
        self.assertEqual(engine.translate('Paramètres — Zorglub'), 'Paramètres — Zorglub')

    def test_unknown_and_unsafe_labels_are_returned_unchanged(self):
        self.assertEqual(engine.translate('Message privé de Jean à Marie'), 'Message privé de Jean à Marie')
        self.assertEqual(engine.translate(''), '')
        self.assertEqual(engine.translate('   '), '   ')

    def test_lexicon_rows_are_well_formed(self):
        for number, line in enumerate(engine.LEXICON.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.startswith('#'):
                continue
            fields = line.split('|')
            self.assertEqual(len(fields), 3, f'lexicon.tsv:{number}')
            self.assertTrue(fields[2].strip(), f'lexicon.tsv:{number}: missing Corsican')
            for source in fields[:2]:
                if source.strip():
                    self.assertEqual(engine.signature(source), engine.signature(fields[2]),
                                     f'lexicon.tsv:{number}: placeholders differ')


class CatalogTests(unittest.TestCase):
    def test_gettext_round_trip_with_context_and_plural(self):
        entries = {b'': b'Language: co\n', b'Save': 'Arregistrà'.encode(),
                   b'button\x04Close': 'Chjode'.encode(), b'file\x00files': 'schedariu\x00schedarii'.encode()}
        self.assertEqual(engine.read_mo(engine.make_mo(entries)), entries)

    def test_qt_round_trip_and_hash_index(self):
        messages = [{'context': 'KStandardGuiItem', 'source': '&Cancel', 'translations': ['&Abbandunà']},
                    {'source': 'Files', 'comment': 'plural', 'translations': ['Schedariu', 'Schedarii']}]
        catalog = engine.read_qm(engine.make_qm(messages))
        self.assertEqual(catalog['language'], 'co')
        self.assertEqual(catalog['messages'][0]['translations'], ['&Abbandunà'])
        self.assertEqual(catalog['messages'][1]['translations'], ['Schedariu', 'Schedarii'])

    def test_qt_hash_matches_the_installed_french_catalogs(self):
        """Qt finds a message by hash; reproduce its own index from system catalogs."""
        sources = sorted(corsu.FRENCH_CATALOGS.glob('*_qt.qm'))[:5]
        if not sources:
            self.skipTest('No Qt catalogs installed')
        checked = 0
        for source in sources:
            data = source.read_bytes()
            catalog = engine.read_qm(data)
            rebuilt = engine.read_qm(engine.make_qm(catalog['messages']))
            self.assertEqual([message.get('source') for message in rebuilt['messages']],
                             [message.get('source') for message in catalog['messages']])
            for message in catalog['messages']:
                key = (message.get('source', '') + message.get('comment', '')).encode()
                self.assertIn(engine.elf_hash(key).to_bytes(4, 'big'), data)
                checked += 1
        self.assertGreater(checked, 100)


class FluentTests(unittest.TestCase):
    def test_multiline_values_are_translated_as_one_label(self):
        source = 'a = Fermer\n    le panneau latéral\nb = Enregistrer\n'
        translated, count = corsu.patch_ftl(source)
        self.assertEqual(count, 2)
        self.assertIn('a = Chjode u pannellu laterale\n', translated)
        self.assertIn('b = Arregistrà\n', translated)

    def test_attributes_selectors_and_access_keys_are_respected(self):
        source = ('save =\n    .label = Enregistrer\n    .accesskey = S\n'
                  'many = { $count ->\n    [one] Enregistrer\n   *[other] Fermer\n  }\n')
        translated, count = corsu.patch_ftl(source)
        self.assertIn('.label = Arregistrà', translated)
        self.assertIn('.accesskey = S', translated)
        self.assertIn('[one] Arregistrà', translated)
        self.assertIn('*[other] Chjode', translated)
        self.assertEqual(count, 3)


if __name__ == '__main__':
    unittest.main()
