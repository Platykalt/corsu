"""The settings page (src/app/index.html): its texts in the three languages, and the Programs rows
rendered from the per-program status (activation, coverage, validation, installations)."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / 'src' / 'app' / 'index.html'
NEW_KEYS = [
    'activation_active', 'activation_partial', 'activation_inactive', 'activation_blocked', 'activation_failed',
    'activation_restart_required', 'coverage_complete', 'coverage_partial', 'coverage_count', 'tested', 'tested_none',
    'tested_simulated', 'tested_real', 'tested_no_real', 'tested_visual', 'tested_no_visual', 'tested_review',
    'tested_no_review', 'instances_one', 'instances_many', 'status_as_of',
]


def script():
    html = PAGE.read_text(encoding='utf-8')
    return html, re.search(r'<script>\n(.*)</script>', html, re.S).group(1)


def texts():
    """{language: {key: value}} read from the page's `text` dictionary."""
    _, code = script()
    block = code[code.index('const text = {'):code.index('\n};\n')]
    found = {}
    for language, body in re.findall(r'\n  (co|fr|en): \{\n(.*?)\n  \},', block + '\n  },', re.S):
        found[language] = dict(re.findall(r'(?:^|[\s,])(\w+): "((?:[^"\\]|\\.)*)"', body))
    return found


class TextTests(unittest.TestCase):
    def test_every_language_has_the_same_keys(self):
        found = texts()
        self.assertEqual(set(found), {'co', 'fr', 'en'})
        self.assertEqual(set(found['co']), set(found['fr']))
        self.assertEqual(set(found['en']), set(found['fr']))

    def test_new_status_texts_exist_everywhere(self):
        for language, values in texts().items():
            for key in NEW_KEYS:
                self.assertTrue(values.get(key), f'{key} missing in {language}')
            # The same placeholders in every translation.
            for key in NEW_KEYS:
                self.assertEqual(set(re.findall(r'\{\w+\}', values[key])),
                                 set(re.findall(r'\{\w+\}', texts()['en'][key])), f'{key} in {language}')

    def test_every_key_used_by_the_page_exists(self):
        html, code = script()
        used = set(re.findall(r'\bt\("(\w+)"\s*[,)]', code)) | set(re.findall(r'data-t="(\w+)"', html))
        # t(condition ? "a" : "b"): both sides are keys.
        for pair in re.findall(r'\bt\([^()"]*\? "(\w+)" : "(\w+)"', code):
            used |= set(pair)
        self.assertTrue(set(NEW_KEYS) - {'activation_' + name for name in
                        ('active', 'partial', 'inactive', 'blocked', 'failed', 'restart_required')} <= used)
        for language, values in texts().items():
            self.assertFalse(used - set(values), language)


# A small DOM, enough for the page's make() and render functions, so they run in node as written.
HARNESS = r'''
const fs = require("fs"), vm = require("vm");
const [page, fixturePath] = process.argv.slice(2);
const code = fs.readFileSync(page, "utf8").match(/<script>\r?\n([\s\S]*)<\/script>/)[1];
class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.attributes = {}; this.children = []; this.listeners = {};
    this.style = {}; this.dataset = {}; this.hidden = false; this.disabled = false; this.classList = { toggle() {} }; }
  setAttribute(name, value) { this.attributes[name] = String(value); if (name === "id") this.id = String(value); if (name === "open") this.open = true; }
  getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; }
  removeAttribute(name) { delete this.attributes[name]; }
  addEventListener(name, listener) { (this.listeners[name] = this.listeners[name] || []).push(listener); }
  append(...children) { for (const child of children) this.children.push(typeof child === "string" ? { text: child } : child); }
  replaceChildren(...children) { this.children = []; this.append(...children); }
  contains() { return false; }
  focus() {}
  showModal() {} close() {}
  set textContent(value) { this.children = [{ text: String(value) }]; }
  get textContent() { return this.children.map(child => child instanceof Element ? child.textContent : child.text).join(""); }
  find(predicate) { const all = []; const walk = node => { for (const child of node.children) if (child instanceof Element) { if (predicate(child)) all.push(child); walk(child); } }; walk(this); return all; }
}
const ids = new Map();
const document = {
  createElement: tag => new Element(tag),
  getElementById: id => { if (!ids.has(id)) ids.set(id, new Element("div")); return ids.get(id); },
  querySelectorAll: () => [], querySelector: () => new Element("main"), documentElement: new Element("html"), activeElement: null,
};
const context = vm.createContext({ document, localStorage: { getItem: () => null, setItem() {} }, fetch: () => new Promise(() => {}),
  setInterval() {}, alert() {}, window: {}, navigator: {}, console, Intl, Date, Math, Number, JSON, Object, Array, Map, Set, String, Boolean, Promise });
vm.runInContext(code, context);
context.fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
context.Element = Element;
const out = vm.runInContext(`
  const clean = value => value == null ? value : value.replace(/[\\u00a0\\u202f]/g, " ");
  const rowsOf = list => $(list).children.map(row => {
    const input = row.find(node => node.tagName === "INPUT")[0];
    const details = row.find(node => node.tagName === "DETAILS")[0];
    const status = row.find(node => node.attributes.class === "status")[0];
    const tested = row.find(node => node.attributes.class === "tested")[0];
    // The restart hint sits directly in the label; installers' actions sit in the details.
    const label = row.children.find(node => node.attributes && node.attributes.class === "label");
    const hint = label ? label.children.filter(node => node.attributes && node.attributes.class === "hint") : [];
    return { name: input ? input.id.replace(/^(switch|pick)-/, "") : null, class: row.attributes.class || null,
      checked: input ? "checked" in input.attributes : null, describedby: input ? input.attributes["aria-describedby"] || null : null,
      status: status ? clean(status.textContent) : null, tested: tested ? tested.textContent : null,
      details: details ? { open: Boolean(details.open), text: clean(details.textContent), summary: details.children[0].textContent } : null,
      hints: hint.map(node => node.textContent), text: clean(row.textContent) };
  });
  const result = {};
  for (const lang of ["en", "fr", "co"]) {
    language = lang;
    result[lang] = {
      partial: clean(coverageText({ state: "partial", translated: 4443, total: 6203 })),
      almost: clean(coverageText({ state: "partial", translated: 6202, total: 6203 })),
      complete: coverageText({ state: "complete", translated: null, total: null }),
      vague: coverageText({ state: "partial", translated: null, total: null }),
      unknown: coverageText({ state: "unknown", translated: null, total: null }),
      none: coverageText(null),
      tested: validationText({ simulated: true, real_app: ["windows"], visual: false, linguistic_review: false }),
      untested: validationText({ simulated: false, real_app: [], visual: false, linguistic_review: false }),
      labels: ["active", "partial", "inactive", "blocked", "failed", "restart_required"].map(activationLabel),
    };
  }
  language = "en";
  result.derived = [activationOf({ on: true, installed: true, switchable: true }), activationOf({ on: false, installed: true, switchable: true }),
    activationOf({ on: false, installed: true, switchable: false }), activationOf({ on: true, activation: "failed" })];
  state = fixture;
  restartHints.set("vlc", "restart vlc"); restartHints.set("winmerge", "restart winmerge");
  render();
  result.programs = rowsOf("switches");
  result.add = rowsOf("choices");
  // The person closes 7-Zip's details: the next refresh keeps them closed.
  const zip = $("switches").children.find(row => row.find(node => node.id === "switch-7zip").length);
  const details = zip.find(node => node.tagName === "DETAILS")[0];
  details.open = false;
  details.listeners.toggle.forEach(listener => listener({ target: details }));
  // A switch that failed: the server says off, the row says off.
  state = JSON.parse(JSON.stringify(fixture));
  Object.assign(state.items.find(item => item.name === "vlc"), { on: false, activation: "failed" });
  render();
  result.after = rowsOf("switches");
  JSON.stringify(result);
`, context);
process.stdout.write(out);
'''

ROOT = 'C:\\Users\\Someone\\AppData\\Local\\Programs\\' + 'VeryLongFolder\\' * 6


def entry(name, **fields):
    label = {'co': [name, 'detail'], 'fr': [name, 'détail'], 'en': [name, 'detail']}
    return {'name': name.lower().replace('-', ''), 'text': label, 'installed': True, 'switchable': True, 'on': True, **fields}


def instance(activation, reason=None, action=None, coverage=None, kind='installer', location='C:\\Program Files\\X'):
    return {'kind': kind, 'location': location, 'version': '1.0', 'activation': activation, 'reason': reason, 'action': action,
            'coverage': coverage or {'state': 'unknown', 'translated': None, 'total': None, 'note': None}}


PARTIAL = {'state': 'partial', 'translated': 4443, 'total': 6203, 'note': None}
TESTED = {'simulated': True, 'real_app': ['windows'], 'visual': False, 'linguistic_review': False}
FIXTURE = {
    'version': '0', 'platform': 'windows', 'installed': True, 'everything_off': False, 'terminal_paused_until': None,
    'firefox_profile': None, 'lexicon_entries': 1, 'options': {}, 'update': None, 'problem': None,
    'job': {'title': None, 'lines': [], 'running': False, 'ok': None, 'progress': None},
    'items': [
        entry('Firefox', activation='active', instances=[], coverage=None, validation=None, updated=None),
        entry('VLC', activation='active', instances=[instance('active', coverage=PARTIAL)], coverage=PARTIAL, validation=TESTED, updated=1.7e9),
        entry('7-Zip', activation='partial', coverage=None, validation=TESTED, updated=1.7e9, instances=[
            instance('active'), instance('blocked', 'Son fichier corse est absent.', 'Réinstallez Corsu.', kind='portable', location=ROOT + '7z.mo')]),
        entry('FileZilla', activation='active', coverage=None, validation=None, updated=None, instances=[
            instance('active', 'FileZilla est ouvert : Corsu reste actif jusqu’à sa fermeture.', 'Fermez FileZilla.')]),
        entry('WinMerge', on=False, activation='failed', coverage=None, validation=None, updated=None, instances=[
            instance('failed', 'Erreur : permission refusée.', 'Consultez le journal.')]),
        entry('Old'),
        entry('Audacity', installed=False, switchable=False, on=False, activation='blocked', coverage=None, validation=None, updated=None,
              instances=[instance('blocked', "Audacity n'a pas encore créé son fichier de réglages.", 'Ouvrez Audacity une fois.')]),
        entry('Discord', installed=False, switchable=False, on=False, activation=None, instances=[], coverage=None, validation=None, updated=None),
    ],
}


@unittest.skipUnless(shutil.which('node'), 'node is not installed')
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            harness, fixture = Path(folder) / 'harness.js', Path(folder) / 'fixture.json'
            harness.write_text(HARNESS, encoding='utf-8')
            fixture.write_text(json.dumps(FIXTURE), encoding='utf-8')
            done = subprocess.run(['node', str(harness), str(PAGE), str(fixture)], capture_output=True, text=True, timeout=60)
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.result = json.loads(done.stdout)

    def row(self, name, rows='programs'):
        return next(row for row in self.result[rows] if row['name'] == name)

    def test_page_script_parses(self):
        subprocess.run(['node', '--check', '-'], input=script()[1], text=True, check=True, timeout=60)

    def test_coverage_is_counted_in_the_page_language(self):
        self.assertEqual(self.result['en']['partial'], 'Translated: 4,443 / 6,203 (72%)')
        self.assertEqual(self.result['fr']['partial'], 'Traduit : 4 443 / 6 203 (72 %)')
        self.assertEqual(self.result['co']['partial'], 'Traduttu : 4 443 / 6 203 (72 %)')
        self.assertIn('(99%)', self.result['en']['almost'])
        self.assertEqual(self.result['en']['complete'], 'Fully translated')
        self.assertEqual(self.result['en']['vague'], 'Partly translated')
        self.assertIsNone(self.result['en']['unknown'])
        self.assertIsNone(self.result['en']['none'])

    def test_validation_and_labels(self):
        self.assertEqual(self.result['en']['tested'], 'Tested: simulated · real app (Windows) · no visual check · no linguistic review')
        self.assertEqual(self.result['en']['untested'], 'Not tested yet')
        for language in ('co', 'fr', 'en'):
            labels = self.result[language]['labels']
            self.assertEqual(len(set(labels)), 6)
            self.assertFalse([label for label in labels if label.startswith('activation_')])

    def test_old_states_are_read_from_on(self):
        self.assertEqual(self.result['derived'], ['active', 'inactive', None, 'failed'])

    def test_active_with_partial_coverage_is_not_a_problem(self):
        vlc = self.row('vlc')
        self.assertEqual(vlc['status'], 'In Corsican · Translated: 4,443 / 6,203 (72%)')
        self.assertNotIn('problem', vlc['class'] or '')
        self.assertNotIn('attention', vlc['class'] or '')
        self.assertIsNone(vlc['details'])
        self.assertTrue(vlc['checked'])
        self.assertEqual(vlc['describedby'], 'status-vlc')
        self.assertEqual(vlc['hints'], ['restart vlc'])
        self.assertIn('real app (Windows)', vlc['tested'])

    def test_partial_activation_lists_each_installation(self):
        zip_ = self.row('7zip')
        self.assertTrue(zip_['status'].startswith('Partly in Corsican'))
        self.assertIn('attention', zip_['class'])
        self.assertTrue(zip_['details']['open'])
        self.assertEqual(zip_['details']['summary'], 'Details of the 2 installations')
        self.assertIn('portable', zip_['details']['text'])
        self.assertIn('Blocked', zip_['details']['text'])
        self.assertIn('Son fichier corse est absent.', zip_['details']['text'])
        self.assertIn('Réinstallez Corsu.', zip_['details']['text'])
        self.assertIn(ROOT + '7z.mo', zip_['details']['text'])

    def test_deferred_switch_off_shows_why(self):
        filezilla = self.row('filezilla')
        self.assertTrue(filezilla['status'].startswith('In Corsican'))
        self.assertTrue(filezilla['checked'])
        self.assertTrue(filezilla['details']['open'])
        self.assertIn('reste actif', filezilla['details']['text'])

    def test_failure_is_marked_and_drops_the_restart_hint(self):
        winmerge = self.row('winmerge')
        self.assertTrue(winmerge['status'].startswith('Failed'))
        self.assertIn('problem', winmerge['class'])
        self.assertFalse(winmerge['checked'])
        self.assertEqual(winmerge['hints'], [])
        self.assertIn('Consultez le journal.', winmerge['details']['text'])

    def test_fixed_parts_and_old_states_look_as_before(self):
        for name in ('firefox', 'old'):
            row = self.row(name)
            self.assertIsNone(row['status'], name)
            self.assertIsNone(row['details'], name)
            self.assertIsNone(row['class'], name)
            self.assertTrue(row['checked'], name)

    def test_add_page_says_why_the_last_attempt_did_nothing(self):
        audacity = self.row('audacity', 'add')
        self.assertTrue(audacity['status'].startswith('Blocked'))
        self.assertIn('problem', audacity['class'])
        self.assertIn('Ouvrez Audacity une fois.', audacity['details']['text'])
        discord = self.row('discord', 'add')
        self.assertIsNone(discord['status'])
        self.assertIsNone(discord['details'])

    def test_rows_follow_the_server_after_each_refresh(self):
        vlc = next(row for row in self.result['after'] if row['name'] == 'vlc')
        self.assertFalse(vlc['checked'])
        self.assertTrue(vlc['status'].startswith('Failed'))
        self.assertEqual(vlc['hints'], [])
        # Details the person closed stay closed.
        zip_ = next(row for row in self.result['after'] if row['name'] == '7zip')
        self.assertFalse(zip_['details']['open'])


if __name__ == '__main__':
    unittest.main()
