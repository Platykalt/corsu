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

    def test_suppress_means_turn_off_and_pin_follows_mozilla(self):
        # "Suppress Highlights" stops a kind of notification, it erases nothing (October 2026 review).
        self.assertEqual(self.words['Supprimer les moments notables'], 'Disattivà i mumenti nutevuli')
        # Pin and unpin follow Mozilla's Corsican (Spirlà / Dispirlà) in Discord too: "Spuntà" also means to rise or
        # appear ("Spuntà di u sole"), "Puntà" to aim (round of 2026-10-19, lexicon/review-discord-2026-10.tsv).
        self.assertEqual(self.words['Épingler'], 'Spirlà')
        self.assertEqual(self.words['Désépingler'], 'Dispirlà')
        self.assertEqual(self.words['Messages épinglés'], 'Messaghji spirlati')
        self.assertEqual(engine.WORDS['Épingler'], 'Spirlà')
        self.assertNotIn('Spuntà', self.words.values())

    def test_labels_of_the_october_inventory(self):
        # docs/untranslated-inventory.md: a game rank left in French; "Clips" taken from an audio editor ("Pezzi",
        # pieces) where Discord's own rows say "clip"; "solu" before what it restricts, as Mozilla's Corsican writes
        # it ("Bluccà solu l'audio"); a presence status that does not agree with a list of people ("Cunnessu").
        expected = {
            'Non classé': 'Senza classifica', 'Unranked': 'Senza classifica', 'Clips': 'Clip',
            '@mentions seulement': 'Solu e @mintuvate', 'Only @mentions': 'Solu e @mintuvate',
            'En ligne': 'In linea', 'Online': 'In linea', 'Hors ligne': 'Fora di linea',
        }
        for key, value in expected.items():
            self.assertEqual(self.words[key], value, key)
        # The Delete key: Corsu's own key name ("Squas", as "Suppr (pavé num.)"), not the Spanish key cap "Supr".
        self.assertEqual(self.words['Suppr'], 'Squas')

    def test_search_fields_say_circa(self):
        # Discord's search boxes (October 2026, seen on the maintainer's Discord): the bare "Rechercher" took Firefox's
        # "Ricercà" where Discord's own rows say "Circà"; the placeholder over a conversation or a server keeps the
        # name Discord inserts ("Rechercher EnzoParisi, Moz_One"). Provenance in lexicon/review-discord-2026-10.tsv.
        expected = {
            'Rechercher': 'Circà', 'Search': 'Circà',
            'Rechercher \u00001\u0000': 'Circà \u00001\u0000', 'Search \u00001\u0000': 'Circà \u00001\u0000',
            'Rechercher dans \u00001\u0000': 'Circà in \u00001\u0000', 'Search in \u00001\u0000': 'Circà in \u00001\u0000',
            'Rechercher des messages dans tes serveurs': 'Circà messaghji in i to servori',
            'Rechercher dans tes messages privés': 'Circà in i to messaghji privati',
            'Recherche dans tous les MP': 'Circà in tutti i messaghji privati',
            # Bars that search friends or users (the friends list, the "new DM"/"add member" pickers): all already in
            # the Discord section, so the field-attribute fix of fix-discord-search reaches them without a new word.
            'Rechercher des amis': 'Circà amichi',
            'Rechercher des amis ou des membres de serveur': 'Circà amichi o membri di servore',
            'Rechercher des amis et des utilisateurs dans : \u00001\u0000': 'Circà amichi è utilizatori in : \u00001\u0000',
        }
        for key, value in expected.items():
            self.assertEqual(self.words[engine.normalize(key)], value, key)

    def test_pin_system_message_and_its_link(self):
        # Discord's pin notice in a channel, "{author} a épinglé un message dans ce salon. Voir tous les messages
        # épinglés.", with "Voir tous les messages épinglés." the action link. It sits in the message list, a name area
        # where only templates and dates were applied, so both the sentence and the link stayed in French (the
        # translator now looks these phrases up there too; src/discord-plugin/translate.ts systemLabels). The author's
        # name is a separate element and stays. "Voir tous les" follows "Voir tous les onglets" (Vede tutte
        # l'unghjette); "messages épinglés" the rows Messages épinglés|Messaghji spirlati. Provenance in
        # lexicon/review-discord-2026-10.tsv (Corsu usage, not read by a speaker). NE traduit jamais un vrai message.
        expected = {
            'a épinglé un message dans ce salon.': 'hà spirlatu un messaghju in stu canale.',
            'Voir tous les messages épinglés.': 'Vede tutti i messaghji spirlati.',
            'a épinglé un message dans ce salon. Voir tous les messages épinglés.':
                'hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati.',
        }
        for key, value in expected.items():
            self.assertEqual(self.words[engine.normalize(key)], value, key)
        # If Discord draws the author's name inside the sentence's own text node, the translator (nameLabel) falls back
        # to a template that keeps the name as a protected value (\u00001\u0000) and translates the fixed parts, so a
        # name that is a dictionary word ("Error") stays as written. Both forms, for one node or a separate link.
        templates = {
            '\u00001\u0000 a épinglé un message dans ce salon. Voir tous les messages épinglés.':
                '\u00001\u0000 hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati.',
            '\u00001\u0000 a épinglé un message dans ce salon.':
                '\u00001\u0000 hà spirlatu un messaghju in stu canale.',
        }
        for key, value in templates.items():
            self.assertEqual(self.words[key], value, key)

    def test_templates_keep_their_placeholders(self):
        key = engine.normalize('Effacer après \u00001\u0000 heures')
        self.assertEqual(self.words[key], 'Squassà dopu \u00001\u0000 ore')


if __name__ == '__main__':
    unittest.main()
