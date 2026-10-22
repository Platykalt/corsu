"""src/hyprland/translations/co.json: Noctalia 5.3's Corsican catalogue keeps the keys, placeholders and plural
pairs of the English, has no empty value (Noctalia shows "!!key!!" for one) and no French or English left in it."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
TRANSLATIONS = ROOT / 'src' / 'hyprland' / 'translations'
INSTALLED_EN = Path('/usr/share/noctalia/assets/translations/en.json')
TOKENS = re.compile(r'\{[^}]*\}|<[^>]+>|%s')


def flatten(node, prefix=''):
    """Dotted keys, as Noctalia's i18n service flattens nested catalogues."""
    for key, value in node.items():
        path = f'{prefix}.{key}' if prefix else key
        if isinstance(value, dict):
            yield from flatten(value, path)
        else:
            yield path, value


def tokens(text):
    return sorted(TOKENS.findall(text) + ['\\n'] * text.count('\n'))


def sources():
    """co.source-hashes.tsv: key -> (hash of the English text, its placeholders and markup)."""
    result = {}
    for line in (TRANSLATIONS / 'co.source-hashes.tsv').read_text(encoding='utf-8').splitlines():
        if line.startswith('#') or not line:
            continue
        key, digest, *rest = line.split('\t')
        result[key] = (digest, sorted(rest[0].split()) if rest and rest[0] else [])
    return result


class Catalogue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((TRANSLATIONS / 'co.json').read_text(encoding='utf-8'))
        cls.co = dict(flatten(data))
        cls.sources = sources()

    def test_values_are_non_empty_strings(self):
        for key, value in self.co.items():
            self.assertIsInstance(value, str, key)
            self.assertTrue(value.strip(), key)

    def test_keys_are_noctalia_keys(self):
        self.assertEqual(len(self.sources), 3126)
        self.assertLessEqual(set(self.co), set(self.sources))

    def test_coverage(self):
        self.assertGreaterEqual(len(self.co) / len(self.sources), 0.99)

    def test_placeholders_and_markup_kept(self):
        for key, value in self.co.items():
            self.assertEqual(tokens(value), self.sources[key][1], key)

    def test_plural_pairs_complete(self):
        for key in self.co:
            if key.endswith('-plural'):
                self.assertIn(key[:-len('-plural')], self.co)
            elif key + '-plural' in self.sources:
                self.assertIn(key + '-plural', self.co)

    def test_plural_forms_differ(self):
        # "{count} finestra" / "{count} finestre": a plural identical to its singular is a missed form.
        for key, value in self.co.items():
            if key.endswith('-plural'):
                singular = self.co[key[:-len('-plural')]]
                if re.search(r'[A-Za-zÀ-ÿ]', value):
                    self.assertNotEqual(value, singular, key)

    def test_no_french_or_english_left(self):
        french = re.compile(r'\b(le|les|des|est|pour|avec|vous|votre|une|du|sur|dans|cette|être|pas)\b')
        english = re.compile(r'\b(the|and|with|your|when|this|that|from|will|is|are|of|to)\b')
        for key, value in self.co.items():
            # Placeholders, paths, commands and quoted config values are not interface text.
            text = re.sub(r'\{[^}]*\}|`[^`]*`|"[^"]*"|\'[^\']*\'|\S*/\S*', ' ', value)
            self.assertIsNone(french.search(text), f'{key}: {value}')
            self.assertIsNone(english.search(text), f'{key}: {value}')

    def test_sample_is_translated(self):
        for key, expected in (('settings.window.title', 'Parametri'), ('session.actions.logout', 'Chjode a sessione'),
                              ('session.actions.shutdown', 'Spenghje'), ('clipboard.title', 'Preme’papei'),
                              ('window-switcher.count-plural', '{count} finestre')):
            self.assertEqual(self.co[key], expected)

    def test_corsican_punctuation_spacing(self):
        # CONTRIBUTING rule 5: a space before ; : ? ! in running text (not in URLs, times or key chords).
        for key, value in self.co.items():
            text = re.sub(r'\S*://\S*|\d+:\d+|\{[^}]*\}', ' ', value)
            self.assertIsNone(re.search(r'[A-Za-zÀ-ÿ][;?!](\s|$)', text), f'{key}: {value}')

    @unittest.skipUnless(INSTALLED_EN.exists(), 'Noctalia is not installed')
    def test_installed_english_matches_recorded_sources(self):
        # A failure here means Noctalia changed its English: Corsu's generated catalogue drops the changed keys
        # (see LOADING.md) until they are translated again.
        en = dict(flatten(json.loads(INSTALLED_EN.read_text(encoding='utf-8'))))
        changed = [k for k, (digest, _) in self.sources.items()
                   if k not in en or hashlib.sha1(en[k].encode()).hexdigest()[:10] != digest]
        self.assertEqual(changed, [])


if __name__ == '__main__':
    unittest.main()
