"""tools/vlcpo.py: VLC's Corsican catalogue, its AI drafts, their reviews and the experimental build."""
import gettext
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import vlcpo  # noqa: E402

HEADER = '''msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: co\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"
'''

UPSTREAM = '''#: src/a.c:1
msgid "Open"
msgstr "Apre"
'''


def draft(msgid, msgstr, flags='fuzzy'):
    return f'''# Corsu: AI draft, not reviewed (source: new)
#: modules/b.c:2
#, {flags}
msgid "{msgid}"
msgstr "{msgstr}"
'''


@unittest.skipUnless(shutil.which('msgfmt'), 'gettext tools not installed')
class CatalogTest(unittest.TestCase):
    def setUp(self):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder)
        self.catalog = folder / 'co.po'
        self.review = folder / 'review.json'
        for name, value in (('CATALOG', self.catalog), ('REVIEW', self.review)):
            patch = mock.patch.object(vlcpo, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        upstream = mock.patch.object(vlcpo, 'upstream', lambda blocks: '')
        upstream.start()
        self.addCleanup(upstream.stop)
        hashed = mock.patch.object(vlcpo, 'UPSTREAM_SHA256', vlcpo.hashlib.sha256(b'').hexdigest())
        hashed.start()
        self.addCleanup(hashed.stop)

    def write(self, *entries):
        self.catalog.write_text('\n'.join((HEADER,) + entries), encoding='utf-8')

    def errors(self):
        with mock.patch('builtins.print') as printed:
            code = vlcpo.check(self.catalog)
        return code, [' '.join(map(str, call.args)) for call in printed.call_args_list if call.args[0] == 'ERROR']

    def test_a_plain_compilation_skips_drafts_the_check_does_not(self):
        self.write(UPSTREAM, draft('Volume: %i %%', 'Vulume : %s %%', 'fuzzy, c-format'))
        self.assertEqual(vlcpo.msgfmt(self.catalog, self.catalog.with_suffix('.mo'), use_fuzzy=False).returncode, 0)
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any('arguments differ' in error for error in errors), errors)
        self.assertTrue(any('msgfmt --use-fuzzy' in error for error in errors), errors)

    def test_rules(self):
        cases = {
            ('&Open', 'Apre'): 'accelerator',
            ('<b>Bold</b>', 'Grassu'): 'markup tags',
            ('Name:', 'Nome'): "trailing ':'",
            ('More...', 'Di più'): "trailing '...'",
            ('Media as %@', 'Media'): 'arguments differ',
            ('%1 of %2', '%1'): '%1-style',
        }
        for (source, target), expected in cases.items():
            with self.subTest(source=source):
                self.write(draft(source, target))
                code, errors = self.errors()
                self.assertEqual(code, 1)
                self.assertTrue(any(expected in error for error in errors), errors)
        for source, target in (('&Open', '&Apre'), ('Name:', 'Nome :'), ('More...', 'Di più…'),
                               ('%1$s of %2$s', '%2$s di %1$s'), ('<left>,<right> Seek', '←,→ Circà')):
            with self.subTest(source=source):
                self.write(draft(source, target))
                self.assertEqual(self.errors(), (0, []))

    def test_a_draft_without_fuzzy_needs_a_speaker(self):
        self.write(draft('Open', 'Apre', 'c-format'))
        code, errors = self.errors()
        self.assertEqual(code, 1)
        self.assertIn('validated by a speaker', errors[0])

    def proposals(self, *items):
        path = self.catalog.parent / f'proposals{len(list(self.catalog.parent.glob("proposals*")))}.jsonl'
        path.write_text(''.join(json.dumps(item) + '\n' for item in items), encoding='utf-8')
        return str(path)

    def test_merge_and_build(self):
        self.write(UPSTREAM, draft('Close', 'Chjude'), draft('Save', 'Carcà'), draft('Seek', 'Circà'))
        _, entries = vlcpo.read(self.catalog)
        close, save, seek = (entry.id for entry in entries[2:])
        before = self.catalog.read_text(encoding='utf-8')
        merged = vlcpo.merge([self.proposals({'id': close, 'verdict': 'keep'},
                                             {'id': save, 'verdict': 'fix', 'msgstr': 'Arregistrà',
                                              'note': 'save is not load'}),
                              self.proposals({'id': seek, 'verdict': 'uncertain', 'note': 'seek or search?'})],
                             'ai', '2026-10-17')
        self.assertEqual(merged, 3)
        after = self.catalog.read_text(encoding='utf-8')
        self.assertIn('msgstr "Arregistrà"', after)
        self.assertNotIn('Carcà', after)
        self.assertEqual(after.count('#, fuzzy'), 3)
        self.assertIn(UPSTREAM, after)
        self.assertEqual(before.replace('Carcà', 'Arregistrà').count('\n'), after.count('\n'))
        review = json.loads(self.review.read_text(encoding='utf-8'))
        self.assertEqual(review[save]['draft'], 'Carcà')
        self.assertEqual(review[save]['status'], 'ai_reviewed')
        self.assertEqual(review[save]['reviews'][0]['note'], 'save is not load')
        self.assertEqual(review[seek]['status'], 'uncertain')
        self.assertEqual(self.errors(), (0, []))

        mo = self.catalog.parent / 'vlc.mo'
        counts = vlcpo.build(mo)
        self.assertEqual((counts['drafts_included'], counts['drafts_left_out']), (2, 1))
        with open(mo, 'rb') as stream:
            catalog = gettext.GNUTranslations(stream)
        self.assertEqual([catalog.gettext(text) for text in ('Open', 'Close', 'Save', 'Seek')],
                         ['Apre', 'Chjude', 'Arregistrà', 'Seek'])

    def test_merge_refuses_two_reviewers_and_unknown_entries(self):
        self.write(draft('Close', 'Chjude'))
        _, entries = vlcpo.read(self.catalog)
        name = entries[1].id
        with self.assertRaisesRegex(SystemExit, 'twice'):
            vlcpo.merge([self.proposals({'id': name, 'verdict': 'keep'}),
                         self.proposals({'id': name, 'verdict': 'keep'})], 'ai', '2026-10-17')
        with self.assertRaisesRegex(SystemExit, 'not a Corsu draft'):
            vlcpo.merge([self.proposals({'id': '000000000000', 'verdict': 'keep'})], 'ai', '2026-10-17')


@unittest.skipUnless(shutil.which('msgfmt'), 'gettext tools not installed')
class RealCatalogTest(unittest.TestCase):
    def test_contrib_catalogue_passes_and_keeps_upstream(self):
        with mock.patch('builtins.print') as printed:
            code = vlcpo.check()
        self.assertEqual(code, 0, [call.args for call in printed.call_args_list])

    def test_status_counts(self):
        counts = vlcpo.counts()
        self.assertEqual(counts['upstream'], 4443)
        self.assertEqual(sum(value for key, value in counts.items() if key != 'upstream'), 1760)


if __name__ == '__main__':
    unittest.main()
