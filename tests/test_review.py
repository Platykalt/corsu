import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import corsu
import engine
import review
import update


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        lexicon = root / 'lexicon.tsv'
        lexicon.write_text('Save|Enregistrer|Arregistrà\n# Discord: test\nFriends|Amis|Amichi\nAdd Friend|Ajouter un ami|Aghjunghje un amicu\n'
                           '# Google: test\nImages|Images|Fiure\n', encoding='utf-8')
        config = root / 'config'
        (config / 'Vencord/settings').mkdir(parents=True)
        (config / 'Vencord/settings/settings.json').write_text('{"plugins": {"Corsu": {"enabled": true}}}')
        review.rows.cache_clear()
        self.patches = [patch.object(engine, 'LEXICON', lexicon), patch.object(engine, 'USER', root / 'data/lexicon-user.tsv'),
                        patch.object(corsu, 'DATA', root / 'data'), patch.object(corsu, 'STATE', root / 'data/state.json'),
                        patch.object(corsu, 'CONFIG', config)]
        for item in self.patches:
            item.start()
        self.config = config

    def tearDown(self):
        for item in self.patches:
            item.stop()
        review.rows.cache_clear()
        self.directory.cleanup()

    def test_sections_shortest_first_and_progress(self):
        self.assertEqual([row[1] for row in review.rows('Discord')], ['Amis', 'Ajouter un ami'])
        self.assertEqual(review.next_item('Discord'), {'english': 'Friends', 'french': 'Amis', 'corsican': 'Amichi'})
        review.record('Amis', 'Friends', 'ok')
        self.assertEqual(review.next_item('Discord')['french'], 'Ajouter un ami')
        self.assertEqual(review.progress('Discord'), {'total': 2, 'done': 1, 'fixed': 0})

    def test_fix_goes_to_user_lexicon_and_discord_settings(self):
        review.record('Ajouter un ami', 'Add Friend', 'fix', 'Aghjunghje un amicu novu')
        self.assertIn('Add Friend|Ajouter un ami|Aghjunghje un amicu novu', engine.USER.read_text(encoding='utf-8'))
        settings = json.loads((self.config / 'Vencord/settings/settings.json').read_text())
        self.assertEqual(json.loads(settings['plugins']['Corsu']['corrections'])['Ajouter un ami'], 'Aghjunghje un amicu novu')
        self.assertIn('Ajouter+un+ami', review.issue_link()['url'])

    def test_fix_must_keep_placeholders_and_one_line(self):
        for bad in ('', 'two\nlines', 'a|b'):
            with self.assertRaises(ValueError):
                review.record('Amis', 'Friends', 'fix', bad)
        with self.assertRaises(ValueError):
            review.record('Redémarrer %1', 'Restart %1', 'fix', 'Rilancià')

    def test_show_original_option(self):
        self.assertEqual(review.set_option('showOriginal', True), {'showOriginal': True})
        settings = json.loads((self.config / 'Vencord/settings/settings.json').read_text())
        self.assertTrue(settings['plugins']['Corsu']['showOriginal'])
        self.assertEqual(corsu.review_options(), {'showOriginal': True})


class UpdateTests(unittest.TestCase):
    def test_versions_compare_as_numbers(self):
        self.assertGreater(update.version_tuple('0.10.0'), update.version_tuple('0.9.2'))
        self.assertEqual(update.version_tuple('v1.2.3'), (1, 2, 3))


if __name__ == '__main__':
    unittest.main()
