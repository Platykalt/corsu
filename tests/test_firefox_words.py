"""Firefox labels of the October 2026 review (main menu, tab context menu, new tab): one vocabulary per menu, the
sense of the button rather than another program's noun (lexicon/corrections.tsv)."""
import unittest

import engine


class FirefoxWordsTests(unittest.TestCase):
    def test_buttons_are_actions_in_their_own_sense(self):
        self.assertEqual(engine.translate('Créer un nouveau profil'), 'Creà un novu prufilu')
        self.assertEqual(engine.translate('Modifier le profil'), 'Mudificà u prufilu')
        self.assertEqual(engine.translate('Vue détaillée'), 'Vista detagliata')
        self.assertEqual(engine.translate('Minimale'), 'Minima')

    def test_tab_menu_speaks_mozillas_corsican(self):
        expected = {
            'Actualiser': 'Attualizà', 'Actualiser l’onglet': "Attualizà l'unghjetta",
            'Dupliquer l’onglet': 'Duppià l’unghjetta', 'Dupliquer les onglets': "Duppià l'unghjette",
            'Déplacer l’onglet': "Dispiazzà l'unghjetta", 'Déplacer vers le début': 'Dispiazzà à u principiu',
            'Épingler': 'Spirlà', 'Désépingler': 'Dispirlà', 'Épingler cet onglet': "Spirlà st'unghjetta",
            'Désépingler cet onglet': "Dispirlà st'unghjetta",
        }
        for french, corsican in expected.items():
            self.assertEqual(engine.translate(french), corsican, french)
        self.assertEqual(engine.translate('Connecter un appareil'), 'Cunnette un apparechju')


if __name__ == '__main__':
    unittest.main()
