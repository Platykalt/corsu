"""The window's « On the phone » page (src/app/phone.js, texts-phone.js, qr/) and its QR codes (tools/make_qr.py):
texts in the three languages, public addresses only, released files only, and codes that really read back."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / 'src' / 'app'
sys.path.insert(0, str(ROOT / 'tools'))
import make_qr  # noqa: E402
from tests.test_app_ui import texts  # noqa: E402

RELEASED_KMP = 'https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp'


class TextTests(unittest.TestCase):
    def test_same_keys_and_placeholders_in_every_language(self):
        found = texts('texts-phone.js', 'textsPhone')
        self.assertEqual(set(found), {'co', 'fr', 'en'})
        for language in ('co', 'en'):
            self.assertEqual(set(found[language]), set(found['fr']), language)
            for key, value in found[language].items():
                self.assertEqual(set(re.findall(r'\{\w+\}', value)), set(re.findall(r'\{\w+\}', found['fr'][key])), key)
                self.assertTrue(value.strip(), f'{key} empty in {language}')

    def test_no_key_clashes_with_the_window_texts(self):
        # t() in app.js reads texts.js first: a phone key with the same name would be hidden.
        self.assertFalse(set(texts('texts-phone.js', 'textsPhone')['fr']) & set(texts()['fr']))

    def test_every_key_used_exists(self):
        code = (APP / 'phone.js').read_text(encoding='utf-8')
        used = set(re.findall(r'\bt\("(\w+)"', code)) | set(re.findall(r'"(ph_\w+)"', code))
        html = (APP / 'index.html').read_text(encoding='utf-8')
        used |= {key for key in re.findall(r'data-t="(\w+)"', html) if key.startswith(('ph_', 'nav_phone'))}
        own = texts('texts-phone.js', 'textsPhone')
        window = texts()
        for language in ('co', 'fr', 'en'):
            self.assertFalse(used - set(own[language]) - set(window[language]), language)

    def test_corsican_texts_are_marked_unreviewed(self):
        self.assertIn('AI proposals, not reviewed', (APP / 'texts-phone.js').read_text(encoding='utf-8'))


class WiringTests(unittest.TestCase):
    def test_page_entry_section_and_scripts(self):
        html = (APP / 'index.html').read_text(encoding='utf-8')
        self.assertIn('data-page="phone"', html)
        self.assertIn('<symbol id="i-phone"', html)
        self.assertRegex(html, r'<section id="phone" data-page-panel hidden>\s*<header class="page-head">\s*<h1 data-t="nav_phone">')
        scripts = re.findall(r'<script src="([\w.-]+\.js)"></script>', html)
        # Loaded before app.js, so their listeners hear the window's first corsu:render.
        self.assertLess(scripts.index('texts-phone.js'), scripts.index('phone.js'))
        self.assertLess(scripts.index('phone.js'), scripts.index('app.js'))
        # The window's key comes first, untouched.
        self.assertEqual(scripts[0], 'key.js')
        self.assertIn('href="phone.css"', html)

    def test_server_serves_every_file_of_the_page(self):
        sys.path.insert(0, str(ROOT / 'src'))
        import app
        for name in ('phone.js', 'phone.css', 'texts-phone.js', *(f'qr/{target}' for target in make_qr.TARGETS)):
            self.assertIn(name, app.STATIC)
            self.assertTrue((APP / name).is_file(), name)
        self.assertEqual(app.STATIC['qr/android-fr.svg'], 'image/svg+xml')


class QrTests(unittest.TestCase):
    def test_committed_codes_match_the_generator(self):
        self.assertEqual(make_qr.main(['--check']), 0)

    def test_addresses_are_public_guides_on_main(self):
        for name, url in make_qr.TARGETS.items():
            self.assertTrue(url.startswith('https://github.com/Platykalt/corsu/blob/main/docs/'), url)
            self.assertNotRegex(url, r'localhost|127\.0\.0\.1|\[::1\]')
            self.assertTrue((ROOT / url.split('/blob/main/', 1)[1]).is_file(), url)
            platform, language = name[:-4].split('-')
            self.assertIn(platform, url)
            self.assertIn('/fr/telephone/' if language == 'fr' else '/en/phone/', url)
            svg = (make_qr.FOLDER / name).read_text(encoding='utf-8')
            self.assertIn(f'<title>{url}</title>', svg)

    def test_known_symbol(self):
        # "HELLO" in byte mode, level M: version 1, 21 modules, with finder patterns at three corners.
        rows = make_qr.encode('HELLO')
        self.assertEqual(len(rows), 21)
        for x, y in ((0, 0), (14, 0), (0, 14)):
            self.assertTrue(all(rows[y][x + i] and rows[y + 6][x + i] for i in range(7)))
        self.assertTrue(rows[21 - 8][8])   # the module that is always dark

    @unittest.skipUnless(shutil.which('qrencode'), 'qrencode is not installed')
    def test_same_modules_as_an_independent_encoder(self):
        """libqrencode (another implementation) with the same mask gives the very same symbol."""
        for url in make_qr.TARGETS.values():
            out = subprocess.run(['qrencode', '-l', 'M', '-8', '-m', '0', '-t', 'ASCII', url],
                                 capture_output=True, text=True, check=True, timeout=30).stdout
            rows = [[c == '#' for c in line[::2]] for line in out.splitlines() if line]
            bits = sum(rows[i][8] << i for i in range(6)) | rows[7][8] << 6 | rows[8][8] << 7 | rows[8][7] << 8
            bits |= sum(rows[8][14 - i] << i for i in range(9, 15))
            mask = ((bits ^ 0x5412) >> 10) & 7
            self.assertEqual(make_qr.encode(url, mask=mask), rows, url)

    @unittest.skipUnless(shutil.which('zbarimg'), 'zbarimg is not installed')
    def test_codes_decode_to_their_address(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, url in make_qr.TARGETS.items():
                picture = Path(folder) / name.replace('.svg', '.png')
                picture.write_bytes(make_qr.png(url))
                done = subprocess.run(['zbarimg', '-q', '--raw', str(picture)], capture_output=True, text=True, timeout=30)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(done.stdout.strip(), url)


RELEASED = ('corsu-keyboard.kmp', 'corsu-keyboard-cismuntincu.kmp', 'corsu-keyboard-pumuntincu.kmp')


class ReleasedFilesTests(unittest.TestCase):
    def test_only_the_released_dictionary_is_offered(self):
        code = (APP / 'phone.js').read_text(encoding='utf-8')
        variants = re.search(r'const VARIANTS = \[(.*?)\];', code, re.S).group(1)
        self.assertEqual(re.findall(r'file: "([\w.-]+)"', variants), list(RELEASED))
        # Nothing announced for a next version: the three files are attached to the release (0.26.0).
        coming = re.findall(r'file: "([\w.-]+)"', re.search(r'const COMING = \[(.*?)\];', code, re.S).group(1))
        self.assertEqual(coming, [])
        self.assertNotIn('RELEASE + COMING', code)
        for path in ('docs/fr/telephone/android.md', 'docs/fr/telephone/iphone.md', 'docs/en/phone/android.md',
                     'docs/en/phone/iphone.md', 'README.md'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertIn(RELEASED_KMP, text, path)
            self.assertLessEqual(set(re.findall(r'releases/latest/download/([\w.-]+\.kmp)', text)), set(RELEASED), path)

    def test_window_never_offers_an_unpublished_or_local_file(self):
        # The candidate packages (CI artifacts) are for testers who follow the guides, not a download in the window;
        # a path on the maintainer's computer is never a download at all.
        for name in ('phone.js', 'texts-phone.js'):
            code = (APP / name).read_text(encoding='utf-8')
            self.assertNotRegex(code, r'actions/runs|/artifacts/|/tmp/|file:/|releases/download/v', name)
        code = (APP / 'phone.js').read_text(encoding='utf-8')
        coming = re.search(r'const COMING = \[(.*?)\];', code, re.S).group(1)
        self.assertNotRegex(coming, r'https?:|url|href', 'COMING entries carry no address')

    def test_guides_have_no_local_path_or_unfilled_placeholder(self):
        for path in ('docs/fr/telephone/android.md', 'docs/fr/telephone/iphone.md', 'docs/en/phone/android.md',
                     'docs/en/phone/iphone.md', 'docs/fr/telephone/essai-5-minutes.md'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertNotRegex(text, r'\]\((/tmp/|file:|/home/)|@@\w+@@', path)
            # A candidate is only ever offered through a CI artifact page, never as a release asset.
            for link in re.findall(r'https://github\.com/Platykalt/corsu/actions/runs/[^)\s]+', text):
                self.assertRegex(link, r'^https://github\.com/Platykalt/corsu/actions/runs/\d+/artifacts/\d+$', path)


# A small DOM, enough for phone.js's render, so it runs in node as written.
HARNESS = r'''
const fs = require("fs"), vm = require("vm"), path = require("path");
const folder = process.argv[2];
class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.attributes = {}; this.children = []; this.listeners = {}; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  addEventListener(name, listener) { (this.listeners[name] = this.listeners[name] || []).push(listener); }
  append(...children) { for (const child of children) this.children.push(typeof child === "string" ? { text: child } : child); }
  replaceChildren(...children) { this.children = []; this.append(...children); }
  focus() {}
  set textContent(value) { this.children = [{ text: String(value) }]; }
  get textContent() { return this.children.map(child => child instanceof Element ? child.textContent : child.text).join(""); }
  find(predicate) { const all = []; const walk = node => { for (const child of node.children) if (child instanceof Element) { if (predicate(child)) all.push(child); walk(child); } }; walk(this); return all; }
}
const body = new Element("div"), listeners = {};
const document = { createElement: tag => new Element(tag), createElementNS: (ns, tag) => new Element(tag),
  getElementById: id => id === "phone-body" ? body : null, querySelector: () => null,
  addEventListener: (name, listener) => { (listeners[name] = listeners[name] || []).push(listener); } };
let lang = "fr";
function make(tag, attributes = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (name === "text") node.textContent = value;
    else if (name.startsWith("on")) node.addEventListener(name.slice(2), value);
    else if (value === true) node.setAttribute(name, "");
    else if (value !== false && value != null) node.setAttribute(name, value);
  }
  node.append(...children.filter(child => child != null));
  return node;
}
const stored = {};
const window = { corsu: { make, icon: name => make("svg", { "data-icon": name }), language: () => lang,
  t: name => ({ opens_browser: "(opens in your browser)" })[name] || name } };
const context = vm.createContext({ document, window, localStorage: { getItem: key => stored[key] || null, setItem: (key, value) => { stored[key] = value; } }, console });
for (const name of ["texts-phone.js", "phone.js"]) vm.runInContext(fs.readFileSync(path.join(folder, name), "utf8"), context);
const result = {};
const snapshot = () => ({
  text: body.textContent,
  img: body.find(node => node.tagName === "IMG").map(node => node.attributes),
  links: body.find(node => node.tagName === "A").map(node => ({ href: node.attributes.href, target: node.attributes.target, rel: node.attributes.rel, text: node.textContent })),
  steps: body.find(node => node.tagName === "OL")[0].children.length,
  radios: body.find(node => node.tagName === "INPUT").map(node => ({ value: node.attributes.value, checked: "checked" in node.attributes, type: node.attributes.type })),
  group: body.find(node => node.attributes.role === "radiogroup").map(node => node.attributes["aria-labelledby"]),
  labelled: body.find(node => node.attributes.id === "ph-choose").length,
});
for (const language of ["co", "fr", "en"]) {
  lang = language;
  listeners["corsu:render"].forEach(listener => listener({ detail: language }));
  result[language + "-android"] = snapshot();
  const before = body.children[0];
  listeners["corsu:render"].forEach(listener => listener({ detail: language }));
  result[language + "-kept"] = body.children[0] === before;
  const iphone = body.find(node => node.tagName === "INPUT" && node.attributes.value === "iphone")[0];
  iphone.listeners.change.forEach(listener => listener({}));
  result[language + "-iphone"] = snapshot();
  body.find(node => node.tagName === "INPUT" && node.attributes.value === "android")[0].listeners.change.forEach(listener => listener({}));
}
result.stored = stored;
process.stdout.write(JSON.stringify(result));
'''


@unittest.skipUnless(shutil.which('node'), 'node is not installed')
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            harness = Path(folder) / 'harness.js'
            harness.write_text(HARNESS, encoding='utf-8')
            done = subprocess.run(['node', str(harness), str(APP)], capture_output=True, text=True, encoding='utf-8', timeout=60)
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.result = json.loads(done.stdout)

    def test_qr_points_to_the_public_guide_of_the_platform_and_language(self):
        expected = {('co', 'android'): 'android-fr', ('fr', 'android'): 'android-fr', ('en', 'android'): 'android-en',
                    ('co', 'iphone'): 'iphone-fr', ('fr', 'iphone'): 'iphone-fr', ('en', 'iphone'): 'iphone-en'}
        for (language, platform), name in expected.items():
            image = self.result[f'{language}-{platform}']['img'][0]
            self.assertEqual(image['src'], f'qr/{name}.svg')
            url = make_qr.TARGETS[name + '.svg']
            # The alternative text gives the address in full.
            self.assertIn(url, image['alt'])
            self.assertIn(url, self.result[f'{language}-{platform}']['text'])

    def test_links_open_outside_and_are_public(self):
        for key, shot in self.result.items():
            if not isinstance(shot, dict) or 'links' not in shot:
                continue
            hrefs = [link['href'] for link in shot['links']]
            self.assertIn(RELEASED_KMP, hrefs)
            for link in shot['links']:
                self.assertTrue(link['href'].startswith('https://'), link)
                self.assertNotRegex(link['href'], r'localhost|127\.0\.0\.1')
                self.assertEqual((link['target'], link['rel']), ('_blank', 'noopener noreferrer'))
                self.assertIn('(opens in your browser)', link['text'])
        self.assertIn('https://play.google.com/store/apps/details?id=com.tavultesoft.kmapro',
                      [link['href'] for link in self.result['fr-android']['links']])
        self.assertIn('https://apps.apple.com/app/keyman/id933676545', [link['href'] for link in self.result['fr-iphone']['links']])

    def test_platform_choice_is_a_named_radio_group(self):
        shot = self.result['en-android']
        self.assertEqual([(radio['value'], radio['checked'], radio['type']) for radio in shot['radios']],
                         [('android', True, 'radio'), ('iphone', False, 'radio')])
        self.assertEqual(shot['group'], ['ph-choose'])
        self.assertEqual(shot['labelled'], 1)
        self.assertTrue(self.result['en-iphone']['radios'][1]['checked'])
        self.assertEqual(self.result['stored'], {'corsu-phone-platform': 'android'})

    def test_steps_and_texts(self):
        self.assertEqual(self.result['fr-android']['steps'], 6)
        self.assertEqual(self.result['fr-iphone']['steps'], 5)
        self.assertIn('Keyman', self.result['co-android']['text'])
        self.assertNotIn('ph_', self.result['co-iphone']['text'])
        self.assertIn('corsu-keyboard.kmp', self.result['en-android']['text'])
        self.assertNotIn('In the next version',        self.result['en-android']['text'])
        self.assertIn('corsu-keyboard-pumuntincu.kmp', self.result['en-android']['text'])

    def test_unchanged_page_keeps_its_nodes_across_refreshes(self):
        self.assertTrue(all(self.result[f'{language}-kept'] for language in ('co', 'fr', 'en')))


if __name__ == '__main__':
    unittest.main()
