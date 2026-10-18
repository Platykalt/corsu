"""The window's « Report a translation » page (src/app/report.js, texts-report.js, report.css): texts in the three
languages, wiring, the report and the prefilled issue built from the form, nothing sent or kept by itself, personal
paths and addresses left out, and no new server route (the window's key model stays as it is)."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.parse

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / 'src' / 'app'
sys.path.insert(0, str(ROOT / 'src'))
from tests.test_app_ui import texts  # noqa: E402

CODE = (APP / 'report.js').read_text(encoding='utf-8')


class TextTests(unittest.TestCase):
    def test_same_keys_and_placeholders_in_every_language(self):
        found = texts('texts-report.js', 'textsReport')
        self.assertEqual(set(found), {'co', 'fr', 'en'})
        for language in ('co', 'en'):
            self.assertEqual(set(found[language]), set(found['fr']), language)
            for key, value in found[language].items():
                self.assertEqual(set(re.findall(r'\{\w+\}', value)), set(re.findall(r'\{\w+\}', found['fr'][key])), key)
                self.assertTrue(value.strip(), f'{key} empty in {language}')

    def test_no_key_clashes_with_the_other_texts(self):
        own = set(texts('texts-report.js', 'textsReport')['fr'])
        self.assertFalse(own & set(texts()['fr']))
        self.assertFalse(own & set(texts('texts-phone.js', 'textsPhone')['fr']))
        self.assertFalse(own & set(texts('texts-appearance.js', 'textsAppearance')['fr']))

    def test_every_key_used_exists(self):
        used = set(re.findall(r'\bt\("(\w+)"', CODE)) | set(re.findall(r'"(rp_\w+)"', CODE))
        html = (APP / 'index.html').read_text(encoding='utf-8')
        used |= {key for key in re.findall(r'data-t="(\w+)"', html) if key.startswith(('rp_', 'nav_report'))}
        own, window = texts('texts-report.js', 'textsReport'), texts()
        for language in ('co', 'fr', 'en'):
            self.assertFalse(used - set(own[language]) - set(window[language]), language)

    def test_corsican_texts_are_marked_unreviewed(self):
        self.assertIn('AI proposals, not reviewed', (APP / 'texts-report.js').read_text(encoding='utf-8'))


class WiringTests(unittest.TestCase):
    def test_page_entry_section_and_scripts(self):
        html = (APP / 'index.html').read_text(encoding='utf-8')
        self.assertIn('data-page="report"', html)
        self.assertIn('<symbol id="i-flag"', html)
        self.assertRegex(html, r'<section id="report" data-page-panel hidden>\s*<header class="page-head">\s*<h1 data-t="nav_report">')
        scripts = re.findall(r'<script src="([\w.-]+\.js)"></script>', html)
        self.assertLess(scripts.index('texts-report.js'), scripts.index('report.js'))
        self.assertLess(scripts.index('report.js'), scripts.index('app.js'))
        self.assertEqual(scripts[0], 'key.js')
        self.assertIn('href="report.css"', html)

    def test_server_serves_every_file_of_the_page(self):
        import app
        for name in ('report.js', 'report.css', 'texts-report.js'):
            self.assertIn(name, app.STATIC)
            self.assertTrue((APP / name).is_file(), name)

    def test_the_issue_form_has_every_field_the_page_fills(self):
        form = (ROOT / '.github/ISSUE_TEMPLATE/translation.yml').read_text(encoding='utf-8')
        ids = set(re.findall(r'^\s+id: (\w+)$', form, re.M))
        self.assertLessEqual({'app', 'version', 'seen', 'where', 'key', 'proposal', 'notes', 'corsu'}, ids)

    def test_nothing_is_sent_or_kept_by_the_page(self):
        for word in ('fetch(', 'XMLHttpRequest', 'sendBeacon', 'WebSocket', 'call(', 'localStorage', 'sessionStorage',
                     'indexedDB', 'corsuAccess', 'document.cookie'):
            self.assertNotIn(word, CODE)
        self.assertEqual(set(re.findall(r'https?://[^\s"`]+', CODE)), {'https://github.com/Platykalt/corsu/issues/new'})
        # One way out, and only from the button's click handler.
        self.assertEqual(CODE.count('window.open('), 1)


class SecurityTests(unittest.TestCase):
    """Served with the window's own server: the page's files are static (the same for everyone, nothing of the
    person in them) and no route was added: every /api/ path still needs the key, and none answers a report."""

    def setUp(self):
        from tests.test_app import WindowKeyTests
        self.helper = WindowKeyTests
        self.chunk = WindowKeyTests.chunk
        WindowKeyTests.setUp(self)

    def request(self, *arguments, **options):
        return self.helper.request(self, *arguments, **options)

    def test_page_files_are_static(self):
        import app
        for name in ('report.js', 'texts-report.js', 'report.css'):
            status, body = self.request('GET', '/' + name)
            self.assertEqual(status, 200)
            self.assertEqual(body, (APP / name).read_bytes())
        self.assertNotIn('/api/report', (ROOT / 'src/app.py').read_text(encoding='utf-8'))
        self.assertTrue(app.ACCESS.key)

    def test_no_report_route_with_or_without_the_key(self):
        import app
        for path in ('/api/report', '/api/report/issue', '/api/issue', '/api/translation'):
            for method in ('GET', 'POST'):
                with self.subTest(path=path, method=method):
                    self.assertEqual(self.request(method, path, body={'seen': 'x'})[0], 403)
                    self.assertEqual(self.request(method, path, key=app.ACCESS.key, body={'seen': 'x'})[0], 404)


# A small DOM, enough for report.js to render and run its handlers in node as written.
HARNESS = r'''
const fs = require("fs"), vm = require("vm"), path = require("path");
const folder = process.argv[2];
class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.attributes = {}; this.children = []; this.listeners = {};
    this.value = ""; this.disabled = false; this.hidden = false; this.focused = 0; }
  setAttribute(name, value) { this.attributes[name] = String(value); if (name === "id") this.id = String(value); if (name === "hidden") this.hidden = true; }
  addEventListener(name, listener) { (this.listeners[name] = this.listeners[name] || []).push(listener); }
  append(...children) { for (const child of children) this.children.push(typeof child === "string" ? { text: child } : child); }
  replaceChildren(...children) { this.children = []; this.append(...children); }
  focus() { this.focused += 1; } select() { this.selected = true; }
  set textContent(value) { this.children = [{ text: String(value) }]; }
  get textContent() { return this.children.map(child => child instanceof Element ? child.textContent : child.text).join(""); }
  find(predicate) { const all = []; const walk = node => { for (const child of node.children) if (child instanceof Element) { if (predicate(child)) all.push(child); walk(child); } }; walk(this); return all; }
}
const body = new Element("div"), listeners = {};
const byId = id => id === "report-body" ? body : body.find(node => node.id === id)[0] || null;
const document = { createElement: tag => new Element(tag), getElementById: byId,
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
const opened = [], copied = [];
let clipboardWorks = true;
const state = { version: "0.27.0", platform: "linux", items: [
  { name: "discord", text: { co: ["Discord", ""], fr: ["Discord", ""], en: ["Discord", ""] } },
  { name: "firefox", text: { co: ["Firefox", ""], fr: ["Firefox", ""], en: ["Firefox", ""] } }] };
const window = { corsu: { make, icon: name => make("svg", { "data-icon": name }), language: () => lang, state: () => state,
  t: name => ({ opens_browser: "(s'ouvre dans le navigateur)" })[name] || name },
  open: (...args) => { opened.push(args); } };
const navigator = { clipboard: { writeText: async text => { if (!clipboardWorks) throw new Error("denied"); copied.push(text); } } };
const context = vm.createContext({ document, window, navigator, URLSearchParams, console });
for (const name of ["texts-report.js", "report.js"]) vm.runInContext(fs.readFileSync(path.join(folder, name), "utf8"), context);
const fire = (name, detail) => (listeners[name] || []).forEach(listener => listener({ detail }));
const type = (id, value) => { const node = byId(id); node.value = value; node.listeners.input.forEach(listener => listener({ target: node })); };
const choose = (id, value) => { const node = byId(id); node.value = value; node.listeners.change.forEach(listener => listener({ target: node })); };
const click = async id => { for (const listener of byId(id).listeners.click) await listener({}); };
(async () => {
  const result = {};
  fire("corsu:page", "report");
  result.options = byId("rp-app").find(node => node.tagName === "OPTION").map(node => [node.attributes.value, node.textContent]);
  result.emptyDisabled = [byId("rp-issue").disabled, byId("rp-copy").disabled];
  result.emptyMissing = byId("rp-missing").textContent;
  result.openedBefore = opened.length;
  choose("rp-app", "discord");
  type("rp-version", "1.0.162");
  type("rp-seen", "Bio du serveur");
  type("rp-where", "Profil du serveur, titre de section");
  type("rp-proposal", "Biugrafia di u servore");
  type("rp-notes", "Vu dans /home/alice/.config/discord et C:\\Users\\Alice\\AppData ; écrire à alice@example.org");
  result.ready = [byId("rp-issue").disabled, byId("rp-copy").disabled, byId("rp-missing").textContent];
  result.report = byId("rp-text").value;
  result.replacedShown = !byId("rp-replaced").hidden;
  const formNode = byId("rp-seen");
  fire("corsu:render", "fr");
  result.keptOnRefresh = byId("rp-seen") === formNode;
  await click("rp-copy");
  result.copied = copied.slice();
  await click("rp-issue");
  result.opened = opened.map(args => args.slice());
  // Another program: its name is asked for.
  choose("rp-app", "other");
  result.otherRow = !byId("rp-app-name-row").hidden;
  result.otherMissing = byId("rp-missing").textContent;
  type("rp-app-name", "Thunderbird");
  result.otherReport = byId("rp-text").value.split("\n")[1];
  // A long report opens the issue without its long fields, and is copied for pasting.
  type("rp-notes", "x".repeat(9000));
  copied.length = 0;
  await click("rp-issue");
  result.longOpened = opened[opened.length - 1][0];
  result.longCopied = copied.length;
  result.longSaid = byId("rp-said").textContent;
  // Copy refused by the browser: the text is selected instead.
  clipboardWorks = false;
  await click("rp-copy");
  result.copyRefused = [byId("rp-text").selected === true, byId("rp-said").textContent];
  // Language change: rebuilt in the new language, with what was typed.
  lang = "co";
  fire("corsu:render", "co");
  result.coReport = byId("rp-text").value.split("\n").slice(0, 3);
  result.coKept = byId("rp-seen").value;
  lang = "en";
  fire("corsu:render", "en");
  result.enFirst = byId("rp-text").value.split("\n").slice(0, 2);
  await click("rp-clear");
  result.cleared = [byId("rp-seen").value, byId("rp-issue").disabled];
  process.stdout.write(JSON.stringify(result));
})().catch(error => { console.error(error); process.exit(1); });
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

    def test_programs_to_choose_from(self):
        self.assertEqual(self.result['options'], [['corsu', 'Corsu (cette fenêtre)'], ['discord', 'Discord'],
                                                  ['firefox', 'Firefox'], ['other', 'Autre logiciel…']])

    def test_required_fields_before_any_way_out(self):
        self.assertEqual(self.result['emptyDisabled'], [True, True])
        self.assertEqual(self.result['emptyMissing'], 'Il manque : Texte vu, Où il apparaît.')
        self.assertEqual(self.result['openedBefore'], 0)
        self.assertEqual(self.result['ready'], [False, False, ''])

    def test_report_to_read_with_private_parts_replaced(self):
        report = self.result['report']
        self.assertEqual(report.split('\n')[:5], ['Traduction à corriger', 'Logiciel : Discord 1.0.162', 'Texte vu : Bio du serveur',
                                                  'Où il apparaît : Profil du serveur, titre de section',
                                                  'Corse proposé : Biugrafia di u servore'])
        self.assertIn('Remarques : Vu dans ~/.config/discord et ~\\AppData ; écrire à […]', report)
        self.assertEqual(report.split('\n')[-1], 'Corsu 0.27.0 sous Linux')
        for private in ('alice', 'Alice', 'example.org'):
            self.assertNotIn(private, report)
        self.assertTrue(self.result['replacedShown'])
        self.assertTrue(self.result['keptOnRefresh'])
        self.assertEqual(self.result['copied'], [report])

    def test_prefilled_issue_opens_only_on_the_click(self):
        (url, target, features), = self.result['opened']
        self.assertEqual((target, features), ('_blank', 'noopener'))
        address, query = url.split('?', 1)
        self.assertEqual(address, 'https://github.com/Platykalt/corsu/issues/new')
        fields = dict(urllib.parse.parse_qsl(query))
        self.assertEqual(fields, {'template': 'translation.yml', 'title': 'Discord : Bio du serveur', 'app': 'Discord',
                                  'version': '1.0.162', 'where': 'Profil du serveur, titre de section',
                                  'corsu': 'Corsu 0.27.0 sous Linux', 'seen': 'Bio du serveur',
                                  'proposal': 'Biugrafia di u servore',
                                  'notes': 'Vu dans ~/.config/discord et ~\\AppData ; écrire à […]'})
        self.assertNotIn('alice', url.lower())

    def test_another_program(self):
        self.assertTrue(self.result['otherRow'])
        self.assertEqual(self.result['otherMissing'], 'Il manque : Logiciel.')
        self.assertEqual(self.result['otherReport'], 'Logiciel : Thunderbird 1.0.162')

    def test_long_report(self):
        fields = dict(urllib.parse.parse_qsl(self.result['longOpened'].split('?', 1)[1]))
        self.assertNotIn('notes', fields)
        self.assertNotIn('seen', fields)
        self.assertEqual(fields['app'], 'Thunderbird')
        self.assertEqual(self.result['longCopied'], 1)
        self.assertIn('trop long', self.result['longSaid'])
        self.assertEqual(self.result['copyRefused'], [True, 'Copie impossible ici : le texte est sélectionné, copiez-le avec Ctrl+C.'])

    def test_languages_and_clearing(self):
        self.assertEqual(self.result['coReport'], ['Traduzzione da currege', 'Prugramma : Thunderbird 1.0.162',
                                                   'Testu vistu : Bio du serveur'])
        self.assertEqual(self.result['coKept'], 'Bio du serveur')
        self.assertEqual(self.result['enFirst'], ['Translation to correct', 'Program: Thunderbird 1.0.162'])
        self.assertEqual(self.result['cleared'], ['', True])


if __name__ == '__main__':
    unittest.main()
