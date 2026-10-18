"""Review sets for speakers and their answers (tools/review_sets.py, review/)."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'tools/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mcmemory = load('mcmemory')
# The module mcmemory reads the answers through, so that the tests' temporary answers file is the one it sees.
review_sets = mcmemory.review_sets
# What the HTML page's reply() writes (same format), for a speaker who answered three questions.
REPLY = '''Réponse à la relecture mc01-1 · Reply to review mc01-1

```text
corsu-review v1
set: mc01-1
data: Minecraft: Java Edition 26.3
item: 01.01
texts: menu.singleplayer@e28ffad47afc:643fbb38b677
answer: ok
proposal:
comment:
item: 01.02
texts: menu.multiplayer@{multi}
answer: other
proposal: Ghjucà inseme
comment: più cortu / nant'à u buttone
item: 01.03
texts: menu.options@{options}
answer: skip
proposal:
comment:
end
```
'''


class SetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(review_sets.MANIFEST.read_text(encoding='utf-8'))
        cls.co = review_sets.corsican()
        cls.sources = review_sets.current_sources()

    def test_committed_sets_are_up_to_date(self):
        files = review_sets.render()
        for name, text in files.items():
            self.assertEqual((review_sets.OUT / name).read_text(encoding='utf-8'), text, f'{name}: run python3 tools/review_sets.py build')

    def test_every_batch_question_once_in_small_sets(self):
        asked = []
        for path in sorted(review_sets.BATCHES.glob('[0-9][0-9]-*.md')):
            asked += [(path.name, question['id']) for question in review_sets.parse_batch(path)[2]]
        found = [(entry['batch'], item['id']) for entry in self.data['sets'] for item in entry['items']]
        self.assertEqual(found, asked)
        for entry in self.data['sets']:
            texts = sum(len(item['texts']) for item in entry['items'])
            self.assertLessEqual(len(entry['items']), review_sets.MAX_QUESTIONS, entry['id'])
            self.assertTrue(texts <= review_sets.MAX_TEXTS or len(entry['items']) == 1, entry['id'])

    def test_each_text_says_exactly_what_is_asked(self):
        for entry in self.data['sets']:
            self.assertEqual((entry['app'], entry['version']), ('Minecraft: Java Edition', '26.3'))
            for item in entry['items']:
                self.assertTrue(item['question'] and item['where'], item['id'])
                for text in item['texts']:
                    self.assertEqual(text['source_hash'], self.sources[text['key']], text['key'])
                    self.assertEqual(text['corsican'], review_sets.shown(self.co[text['key']]), text['key'])
                    self.assertEqual(text['corsican_hash'], review_sets.digest(self.co[text['key']]), text['key'])

    def test_a_question_written_for_an_older_corsican_says_so(self):
        item = next(item for entry in self.data['sets'] for item in entry['items'] if item['id'] == '01.18')
        self.assertEqual(item['texts'][0]['asked'], 'Apre à a reta LAN')
        self.assertIn('The question was written for:* Apre à a reta LAN',
                      (review_sets.SETS / 'mc01-3.md').read_text(encoding='utf-8'))

    def test_pages_send_nothing_by_themselves(self):
        page = (review_sets.SETS / 'mc01-1.html').read_text(encoding='utf-8')
        # No fetch, no form posting anywhere, no outside script or style: the issue opens only on a click.
        for word in ('fetch(', 'XMLHttpRequest', '<form', 'src="http', 'href="http', '@import'):
            self.assertNotIn(word, page)
        self.assertEqual(page.count('window.open('), 1)
        self.assertIn('document.getElementById("issue").addEventListener("click"', page)


class AnswerCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.answers = Path(self.folder.name) / 'answers.jsonl'
        item = patch.object(review_sets, 'ANSWERS', self.answers)
        item.start()
        self.addCleanup(item.stop)
        data = json.loads(review_sets.MANIFEST.read_text(encoding='utf-8'))
        self.items = {item['id']: item for entry in data['sets'] for item in entry['items']}
        field = lambda item: review_sets.texts_field(self.items[item]).split('@', 1)[1]
        self.reply = REPLY.replace('{multi}', field('01.02')).replace('{options}', field('01.03'))

    def write(self, name, text):
        path = Path(self.folder.name) / name
        path.write_text(text, encoding='utf-8')
        return path


class AnswerTests(AnswerCase):
    def test_reply_is_imported_as_proposals_once(self):
        path = self.write('issue.txt', self.reply)
        self.assertEqual(review_sets.import_answers([path], via='issue #1', date='2026-10-19'), (2, 0))
        self.assertEqual(review_sets.import_answers([path], via='issue #1', date='2026-10-19'), (0, 2))
        answers = review_sets.read_answers()
        self.assertEqual([(a['item'], a['answer'], a['proposal'], a['status']) for a in answers],
                         [('01.01', 'ok', None, 'proposal'), ('01.02', 'other', 'Ghjucà inseme', 'proposal')])
        self.assertEqual(answers[0]['texts'], [{'key': 'menu.singleplayer', 'source_hash': 'e28ffad47afc',
                                                'corsican_hash': '643fbb38b677', 'corsican': 'Ghjucà solu'}])
        self.assertEqual((answers[0]['version'], answers[0]['via'], answers[0]['texts_from']), ('26.3', 'issue #1', 'answer'))
        self.assertEqual(answers[1]['comment'], "più cortu / nant'à u buttone")
        # A proposal is not a validation.
        self.assertEqual(review_sets.human_validations(), {})

    def test_filled_in_markdown_set(self):
        text = (review_sets.SETS / 'mc01-1.md').read_text(encoding='utf-8')
        marker = '**Réponse · Answer** (OK, ou votre forme · or your form):\n\n> \n'
        filled = text.replace(marker, marker[:-1] + 'OK\n', 1).replace(marker, marker[:-1] + 'Ghjucà inseme\n', 1)
        found = review_sets.parse_markdown(filled)
        self.assertEqual([(a['item'], a['answer'], a['proposal']) for a in found],
                         [('01.01', 'ok', None), ('01.02', 'other', 'Ghjucà inseme')])
        self.assertEqual(found[0]['texts'][0]['source_hash'], 'e28ffad47afc')

    def test_examined_answer_becomes_the_validation_of_that_text(self):
        review_sets.import_answers([self.write('issue.txt', self.reply)], date='2026-10-19')
        self.assertEqual(review_sets.examine('mc01-1', '01.01', 'accepted', 'checked by the maintainer'), 1)
        self.assertEqual(review_sets.examine('mc01-1', '01.02', 'rejected'), 1)
        found = review_sets.human_validations()
        self.assertEqual(list(found), [('menu.singleplayer', 'e28ffad47afc')])
        self.assertIn('accepted (set mc01-1, question 01.01, source e28ffad47afc', found[('menu.singleplayer', 'e28ffad47afc')])
        # Written into the memory for that key only, still apart from the AI levels.
        entries = {entry['key']: entry for entry in mcmemory.entries()}
        validation = entries['menu.singleplayer']['validation']
        self.assertIn('speaker answer ok accepted', validation['human'])
        self.assertTrue(validation['ai_proposal'] and validation['ai_review'])
        self.assertEqual(entries['menu.multiplayer']['validation']['human'], 'none')


class ChangedTextTests(AnswerCase):
    """Real case: key.drop was "Drop Item" (hash dd60ae90b685, 1.7.2 to 1.8.9) before "Drop Selected Item"
    (cd76d09030c8, 1.9 to 26.3)."""

    def answer(self, source_hash, corsican_hash, kind='ok'):
        return {'set': 'mc02-19', 'item': '02.74', 'app': 'Minecraft: Java Edition', 'version': '1.8.9', 'answer': kind,
                'proposal': None, 'comment': None, 'received': '2026-10-19', 'via': None, 'status': 'accepted',
                'examined': {'date': '2026-10-19', 'note': None},
                'texts': [{'key': 'key.drop', 'source_hash': source_hash, 'corsican_hash': corsican_hash}]}

    def test_validation_of_an_older_english_text_is_to_re_examine(self):
        stale = self.answer('dd60ae90b685', review_sets.digest("Lampà l'ogettu"))
        status, reasons = review_sets.status_of(stale)
        self.assertEqual(status, 'to-re-examine')
        self.assertIn('English source changed (dd60ae90b685 -> cd76d09030c8)', reasons[0])
        review_sets.write_answers([stale])
        self.assertEqual(review_sets.human_validations(),
                         {('key.drop', 'cd76d09030c8'): 'to-re-examine (answer mc02-19 02.74 accepted for source '
                                                        'dd60ae90b685, Minecraft: Java Edition 1.8.9)'})

    def test_ok_on_a_corsican_that_changed_since(self):
        status, reasons = review_sets.status_of(self.answer('cd76d09030c8', review_sets.digest("Lampà l'ogettu")))
        self.assertEqual((status, reasons), ('to-re-examine', ["key.drop: Corsican changed since this OK"]))
        current = review_sets.digest(review_sets.corsican()['key.drop'])
        self.assertEqual(review_sets.status_of(self.answer('cd76d09030c8', current)), ('accepted', []))
        # A proposed other form is about the English, not about the Corsican it replaces.
        self.assertEqual(review_sets.status_of(self.answer('cd76d09030c8', '0' * 12, 'other'))[0], 'accepted')

    def test_command_line_status(self):
        review_sets.write_answers([self.answer('dd60ae90b685', '0' * 12)])
        with patch('sys.stdout') as out:
            self.assertEqual(review_sets.main(['status']), 0)
        printed = ''.join(call.args[0] for call in out.write.call_args_list)
        self.assertIn('mc02-19 02.74: ok [to-re-examine]', printed)
        self.assertIn('to-re-examine: 1', printed)


if __name__ == '__main__':
    unittest.main()
