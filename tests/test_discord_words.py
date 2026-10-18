"""The words the Discord plugin gets (engine.application_words('Discord', 'Vencord')): labels Discord shows in its own
sense, not the sense another program gave the same French or English text."""
import unittest

import engine


class DiscordWordsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.words = engine.application_words('Discord', 'Vencord')

    def test_bio_is_the_profile_bio(self):
        # "Bio" is the profile's description in Discord (the title of the bio in profiles and in Settings > Profiles);
        # Chrome's list of image styles has "Bio" for "organic". It is written out as "Biugrafia", the spelling of the
        # section titles of Corsican Wikipedia and a variant given by INFCOR (headword "biografia").
        self.assertEqual(self.words['Bio'], 'Biugrafia')
        self.assertEqual(self.words['Bio du serveur'], 'Biugrafia di u servore')
        self.assertEqual(self.words['Server Bio'], 'Biugrafia di u servore')
        self.assertEqual(self.words[engine.normalize('Bio du serveur de \u00001\u0000')],
                         'Biugrafia di u servore di \u00001\u0000')
        self.assertNotIn('Organicu', self.words.values())
        self.assertEqual(engine.WORDS['Bio'], 'Organicu')

    def test_message_is_a_noun(self):
        # "Message" alone is a noun in Discord's French (the role of every message for screen readers, a channel
        # icon); the button is "Envoyer un message" / "Envoyer un MP".
        self.assertEqual(self.words['Message'], 'Messaghju')
        self.assertEqual(self.words['Envoyer un MP'], 'Mandà un MP')
        self.assertEqual(self.words['Envoyer un message'], 'Mandà un messaghju')

    def test_abbreviations_in_their_discord_sense(self):
        # "sec" is seconds, not "dry"; "Sync" a button (Synchroniser); "Playing" the activity header (Joue à), not a
        # media player's state; abbreviations of maximum and minimum written out where they fit; "min" for minutes
        # stays the unit.
        expected = {
            'sec': 's', 'Sync': 'Sincrunizà', 'Playing': 'Ghjoca à', 'Watch': 'Fighjà', 'Go': 'Andà',
            'Max : \u00001\u0000': 'Massimu : \u00001\u0000', 'min. requis': 'minimu richiestu',
            'Longueur max du message atteinte': 'Lunghezza massima di u messaghju righjunta',
            "Nombre max. d'utilisateurs affichés": "Numeru massimu d'utilizatori affissati",
            "Durée max d'inactivité": "Durata massima d'inattività",
            'Minimum de \u00001\u0000': 'Minimu di \u00001\u0000',
        }
        for key, value in expected.items():
            self.assertEqual(self.words[engine.normalize(key)], value, key)
        self.assertEqual(self.words[engine.normalize('Actif il y a \u00001\u0000 min')], 'Attivu \u00001\u0000 min fà')

    def test_other_senses_fixed(self):
        expected = {
            'Arcade': 'Arcade', 'mode': 'moda', 'Cri': 'Brionu', 'Bannière': 'Bandera',
            'Fermer la fenêtre': 'Chjode a finestra', 'Aucune commande trouvée': 'Nisuna cumanda trovata',
        }
        for key, value in expected.items():
            self.assertEqual(self.words[key], value, key)
        # Polysemous in Discord: left as they were (see docs/discord-review-2026-10.md).
        self.assertEqual(self.words['Mars'], 'Marzu')
        self.assertEqual(self.words['Quitter'], 'Abbandunà')

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

    def test_tray_menu(self):
        # The menu of Discord's notification-area icon: texts the page sends to the desktop app (setSystemTrayStrings),
        # as Discord writes them in French and English. "Quitter Discord" ends the app ("Esce da", as Mozilla's
        # "Esce da Mozilla VPN"); "Quitter" alone stays the leave of a server or group.
        expected = {
            'Ouvrir Discord': 'Apre Discord', 'Open Discord': 'Apre Discord',
            'Quitter Discord': 'Esce da Discord', 'Quit Discord': 'Esce da Discord',
            'Rendre muet': 'Ammutulisce', 'Mettre en sourdine': "Disattivà l'ascoltu",
            'Interdit': 'Difesu', 'Suppressed': 'Difesu',
            'Ouvrir les paramètres vocaux et vidéo': 'Apre i parametri vucali è videò',
            'Open Voice && Video Settings': 'Apre i parametri vucali è videò',
            'Rechercher les mises à jour…': "Circà l'aghjurnamenti…", 'Check For Updates...': "Circà l'aghjurnamenti…",
            'Remerciements': 'Ringraziamenti', 'Acknowledgements': 'Ringraziamenti',
        }
        for key, value in expected.items():
            self.assertEqual(self.words[key], value, key)
        self.assertEqual(self.words['Quitter'], 'Abbandunà')
        # Found by the bounded search of Discord's settings (docs/untranslated-inventory.md).
        self.assertEqual(self.words['Durée minimale des notifications'], 'Durata minima di e nutificazioni')

    def test_suppress_means_turn_off_and_pin_stays_discords(self):
        # "Suppress Highlights" stops a kind of notification, it erases nothing (October 2026 review).
        self.assertEqual(self.words['Supprimer les moments notables'], 'Disattivà i mumenti nutevuli')
        # Puntà/Spuntà is Discord's own pair; it no longer leaks into other programs (Firefox follows Mozilla).
        self.assertEqual(self.words['Épingler'], 'Puntà')
        self.assertEqual(self.words['Désépingler'], 'Spuntà')
        self.assertEqual(engine.WORDS['Épingler'], 'Spirlà')

    def test_templates_keep_their_placeholders(self):
        key = engine.normalize('Effacer après \u00001\u0000 heures')
        self.assertEqual(self.words[key], 'Squassà dopu \u00001\u0000 ore')


if __name__ == '__main__':
    unittest.main()
