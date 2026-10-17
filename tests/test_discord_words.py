"""The words the Discord plugin gets (engine.application_words('Discord', 'Vencord')): labels Discord shows in its own
sense, not the sense another program gave the same French or English text."""
import unittest

import engine


class DiscordWordsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.words = engine.application_words('Discord', 'Vencord')

    def test_bio_is_the_profile_bio(self):
        # "Bio" is the profile's description in Discord; Chrome's list of image styles has "Bio" for "organic".
        self.assertEqual(self.words['Bio'], 'Bio')
        self.assertNotIn('Organicu', self.words.values())
        self.assertEqual(engine.WORDS['Bio'], 'Organicu')

    def test_in_a_call(self):
        self.assertEqual(self.words['Dans un appel'], 'In una chjama')
        self.assertEqual(self.words['In a call'], 'In una chjama')

    def test_labels_taken_from_other_programs_follow_discord(self):
        expected = {
            'Créer un salon': 'Creà un canale', 'Salons vocaux': 'Canali vucali', 'Envoyer': 'Mandà',
            'Événements': 'Avvenimenti', 'Couper': 'Taglià', 'Anglais': 'Inglese', 'Français': 'Francese',
            'Réinitialiser': 'Reinizializà', 'Ignorer': 'Ignurà', 'Modifier le profil': 'Mudificà u prufilu',
        }
        for key, value in expected.items():
            self.assertEqual(self.words[key], value, key)

    def test_templates_keep_their_placeholders(self):
        key = engine.normalize('Effacer après \u00001\u0000 heures')
        self.assertEqual(self.words[key], 'Squassà dopu \u00001\u0000 ore')


if __name__ == '__main__':
    unittest.main()
