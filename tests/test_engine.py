"""Tests for the translation engine and the catalog formats it writes."""
from pathlib import Path
import unittest
from unittest.mock import patch

import corsu
import engine


class TranslationTests(unittest.TestCase):
    def test_placeholder_templates_keep_every_argument(self):
        self.assertEqual(engine.translate('Redémarrer { -brand-short-name }'), 'Rilancià { -brand-short-name }')
        self.assertEqual(engine.translate('Page %1 de %2'), 'Pagina %1 di %2')
        self.assertEqual(engine.translate('Obtenir { -mozilla-vpn-brand-name }'),
                         'Ottene { -mozilla-vpn-brand-name }')

    def test_mozilla_properties_placeholders_are_arguments(self):
        # Firefox's .properties files write their arguments %S and %1$S; rows written with %1 cover them.
        self.assertEqual(engine.translate('Fichier %S'), 'Schedariu %S')
        self.assertEqual(engine.translate('Ouverture de %S'), 'Apertura di %S')
        self.assertEqual(engine.translate('Le fichier a été bloqué car %1$S n’est pas accessible.'),
                         'U schedariu hè statu bluccatu perchè %1$S ùn hè micca accessibile.')
        self.assertEqual(engine.signature('Fichier %1$S'), ['%1$S'])

    def test_mozilla_arguments_keep_their_values(self):
        """Firefox gives the n-th %S, or %n$S, the n-th value: a translation must give each value the same place."""
        rows = {}
        for english, corsican in (
                ('Copy %S to %S', 'Cupià %S in %S'),
                ('Move %1$S to %2$S', 'In %2$S, mette %1$S'),
                ('Profile: %S, path: %S', 'Chjassu: %2$S, prufilu: %1$S'),
                ('Uploading %S of %S', 'Mandata di %S'),
                ('Opening %S (%S%%)', 'Apertura di %S (%S%%)'),
                ('Saved %S (%S)', 'Arregistratu %S (%1$S)'),
                ('Error.~%Line %S', 'Sbagliu.~%Linea %S'),
                ('%s has %d files', '%d schedarii in %s'),
                ('%1$s has %2$d files', '%2$d schedarii in %1$s'),
                ('Downloading %S', 'Scaricamentu di %1$S %2$S')):
            engine.add_row(rows, english, '', corsican)
        with patch.dict(engine.WORDS, rows):
            # Plain arguments in the same order, and a template applied to %1$S: every value where it was.
            self.assertEqual(engine.translate('Copy %S to %S'), 'Cupià %S in %S')
            self.assertEqual(engine.translate('Move %1$S to %2$S'), 'In %2$S, mette %1$S')
            self.assertEqual(engine.translate('Move %2$S to %1$S'), 'In %1$S, mette %2$S')
            # Reordered plain %S written with numbers: Mozilla's formatter reads them the same way, so it is kept.
            self.assertEqual(engine.translate('Profile: %S, path: %S'), 'Chjassu: %2$S, prufilu: %1$S')
            self.assertEqual(engine.signature('%S then %S'), engine.signature('%2$S, then %1$S'))
            # A dropped or added value, or plain and numbered arguments mixed together, is refused.
            self.assertEqual(engine.translate('Uploading %S of %S'), 'Uploading %S of %S')
            self.assertEqual(engine.translate('Downloading %S'), 'Downloading %S')
            self.assertEqual(engine.translate('Saved %S (%S)'), 'Saved %S (%S)')
            self.assertNotEqual(engine.signature('%S and %1$S'), engine.signature('%1$S and %2$S'))
            # %% is a literal percent sign beside the arguments; Nyquist's ~% is a line break, not an argument.
            self.assertEqual(engine.translate('Opening %S (%S%%)'), 'Apertura di %S (%S%%)')
            self.assertEqual(engine.signature('100%%S'), [])
            self.assertEqual(engine.signature('%%%S'), ['%1$S'])
            self.assertEqual(engine.translate('Error.~%Line %S'), 'Sbagliu.~%Linea %S')
            # Unnumbered C or Python arguments are read in order: swapping %s and %d would hand a number to %s.
            self.assertEqual(engine.translate('%s has %d files'), '%s has %d files')
            self.assertNotEqual(engine.signature('%s %d'), engine.signature('%d %s'))
            # Numbered ones may move; Python has no %1$s, so plain %s never becomes numbered.
            self.assertEqual(engine.translate('%1$s has %2$d files'), '%2$d schedarii in %1$s')
            self.assertNotEqual(engine.signature('%s'), engine.signature('%1$s'))

    def test_firefox_labels_found_in_french_by_the_audit(self):
        # Firefox 157's French text for the main menu's browser tools and the downloads panel and dialogs.
        for french in ('Débogage distant', 'Console du navigateur', 'Boîte à outils du navigateur', 'Vue adaptative',
                       'Fichier supprimé', 'Fichier déplacé ou manquant', 'Fichier supprimé (bloqué)', 'Taille inconnue',
                       'Bloqué par les contrôles parentaux', 'Ce fichier est rarement téléchargé.',
                       'Voulez-vous vraiment autoriser ce téléchargement\xa0?', '%S (par défaut)'):
            with self.subTest(french=french):
                self.assertNotEqual(engine.translate(french), french)
        # A heading in Firefox View, the sidebar and Settings, not the button "open the tabs".
        self.assertEqual(engine.translate('Onglets ouverts'), 'Unghjette aperte')
        self.assertEqual(engine.normalize(engine.translate('Ouvrir les onglets')), "Apre l'unghjette")

    def test_accelerator_marker_is_preserved(self):
        self.assertEqual(engine.translate('&Cancel'), '&Abbandunà')
        self.assertEqual(engine.translate('Co&uper'), 'Ta&glià')
        # Without a row for '_Save' itself, the marker stays on the source's letter.
        self.assertEqual(engine.translate('_Save'), 'Arregi_strà')

    def test_letter_case_and_trailing_punctuation(self):
        self.assertEqual(engine.translate('inconnu'), 'scunnisciutu')
        self.assertEqual(engine.translate('Enregistrer…'), 'Arregistrà…')
        self.assertEqual(engine.normalize(engine.translate('Erreur\xa0:')), 'Sbagliu :')

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
