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
    """The page's markup and its scripts (src/app/<name>.js in the page's order), as one program. Scripts another part
    of the work adds (appearance.js) are skipped while they do not exist yet."""
    html = PAGE.read_text(encoding='utf-8')
    names = re.findall(r'<script src="([\w.-]+\.js)"></script>', html)
    return html, '\n'.join((PAGE.parent / name).read_text(encoding='utf-8') for name in names if (PAGE.parent / name).exists())


def texts(name='texts.js', variable='text'):
    """{language: {key: value}} read from the page's `text` dictionary (or another texts file of the same shape)."""
    code = (PAGE.parent / name).read_text(encoding='utf-8')
    block = code[code.index(f'const {variable} = {{'):code.index('\n};\n')]
    found = {}
    for language, body in re.findall(r'\n  (co|fr|en): \{\n(.*?)\n  \},', block + '\n  },', re.S):
        found[language] = dict(re.findall(r'(?:^|[\s,])(\w+): "((?:[^"\\]|\\.)*)"', body))
    return found


def all_texts():
    """The page's texts and, once it exists, the Appearance page's (texts-appearance.js): t() reads both."""
    found = texts()
    if (PAGE.parent / 'texts-appearance.js').exists():
        for language, values in texts('texts-appearance.js', 'textsAppearance').items():
            found[language] = {**values, **found[language]}
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
        for language, values in all_texts().items():
            self.assertFalse(used - set(values), language)


# A small DOM, enough for the page's make() and render functions, so they run in node as written.
HARNESS = r'''
const fs = require("fs"), vm = require("vm");
const [page, fixturePath] = process.argv.slice(2);
const path = require("path");
const html = fs.readFileSync(page, "utf8");
const code = [...html.matchAll(/<script src="([\w.-]+\.js)"><\/script>/g)].map(found => path.join(path.dirname(page), found[1]))
  .filter(file => fs.existsSync(file)).map(file => fs.readFileSync(file, "utf8")).join("\n");
class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.attributes = {}; this.children = []; this.listeners = {};
    this.style = { setProperty(name, value) { this[name] = value; }, removeProperty(name) { delete this[name]; }, getPropertyValue(name) { return this[name] || ""; } };
    this.dataset = {}; this.hidden = false; this.disabled = false; this.classList = { toggle() {}, add() {}, remove() {}, contains: () => false }; }
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
const ids = new Map(), events = [];
class CustomEvent { constructor(type, options = {}) { this.type = type; this.detail = options.detail; } }
const document = {
  createElement: tag => new Element(tag), createElementNS: (namespace, tag) => new Element(tag),
  getElementById: id => { if (!ids.has(id)) ids.set(id, new Element("div")); return ids.get(id); },
  querySelectorAll: () => [], querySelector: () => new Element("main"), documentElement: new Element("html"), activeElement: null,
  dispatchEvent: event => { events.push({ type: event.type, detail: event.detail }); return true; }, addEventListener() {}, readyState: "loading",
};
const context = vm.createContext({ document, localStorage: { getItem: () => null, setItem() {} }, fetch: () => new Promise(() => {}),
  sessionStorage: { getItem: () => null, setItem() {} }, location: { hash: "", pathname: "/", search: "" }, history: { replaceState() {} },
  URLSearchParams,
  setInterval() {}, setTimeout() {}, clearTimeout() {}, alert() {}, window: { addEventListener() {}, matchMedia: () => ({ matches: false, addEventListener() {} }) }, navigator: {}, console, Intl, Date, Math, Number, JSON, Object, Array, Map, Set, String, Boolean, Promise,
  CustomEvent, events });
vm.runInContext(code, context);
context.fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
context.Element = Element;
const out = vm.runInContext(`
  const clean = value => value == null ? value : value.replace(/[\\u00a0\\u202f]/g, " ");
  const rowsOf = list => $(list).children.map(row => {
    const input = row.find(node => node.tagName === "INPUT")[0];
    const details = row.find(node => node.tagName === "DETAILS")[0];
    // The state chip beside the name (icon + word), when the row has something unusual to say.
    const status = input ? row.find(node => node.id === "status-" + input.id.replace(/^(switch|pick)-/, ""))[0] : null;
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
      never: t("update_never"),
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
  const textOf = id => clean($(id).textContent);
  result.summary = { on: textOf("summary-on-value"), off: textOf("summary-on-sub"), attention: textOf("summary-attention-value"),
    jumps: $("summary-attention-list").children.map(node => clean(node.textContent)), attentionClass: $("summary-attention").className,
    update: textOf("summary-update-text"), hidden: Boolean($("summary").hidden) };
  // The page redraws itself every 1.5 s: what did not change keeps its nodes (focus stays on a link or button, live
  // regions are not announced again); what changed is redrawn.
  const redrawn = ["summary-attention-list", "guides", "practice", "facts", "update-facts", "update-status"];
  const firsts = () => redrawn.map(id => $(id).children[0]);
  let before = firsts();
  render();
  result.unchangedKept = firsts().map((node, index) => Boolean(node) && node === before[index]);
  before = firsts();
  language = "fr"; render();
  result.changedRedrawn = firsts().map((node, index) => node !== before[index]);
  language = "en"; render();
  // The hooks the Appearance page (appearance.js) relies on.
  result.renderEvents = events.filter(event => event.type === "corsu:render").map(event => event.detail);
  show("appearance");
  result.pageEvent = events.filter(event => event.type === "corsu:page").map(event => event.detail).pop();
  result.hooks = Object.keys(window.corsu).sort();
  result.hookLanguage = window.corsu.language();
  // texts-appearance.js once it is there, a stand-in of the same shape before.
  if (typeof textsAppearance === "undefined") {
    globalThis.textsAppearance = { co: { ap_probe: "Pruvà {n}" }, fr: { ap_probe: "Essai {n}" }, en: { ap_probe: "Test {n}" } };
    result.appearanceText = [window.corsu.t("ap_probe", { n: 2 }), "Test 2"];
  } else {
    const key = Object.keys(textsAppearance.en).find(name => !(name in text.en));
    result.appearanceText = [window.corsu.t(key), textsAppearance.en[key]];
  }
  result.ownTextFirst = window.corsu.t("nav_appearance");
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
            done = subprocess.run(['node', str(harness), str(PAGE), str(fixture)], capture_output=True, text=True, encoding='utf-8', timeout=60)
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.result = json.loads(done.stdout)

    def row(self, name, rows='programs'):
        return next(row for row in self.result[rows] if row['name'] == name)

    def test_page_script_parses(self):
        subprocess.run(['node', '--check', '-'], input=script()[1], text=True, encoding='utf-8', check=True, timeout=60)

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
        # Nothing unusual: no chip, coverage and tests on demand, closed.
        self.assertIsNone(vlc['status'])
        self.assertNotIn('problem', vlc['class'] or '')
        self.assertNotIn('attention', vlc['class'] or '')
        self.assertFalse(vlc['details']['open'])
        self.assertEqual(vlc['details']['summary'], 'Installation details')
        self.assertIn('Translated: 4,443 / 6,203 (72%)', vlc['details']['text'])
        self.assertTrue(vlc['checked'])
        self.assertEqual(vlc['describedby'], 'desc-vlc')
        self.assertEqual(vlc['hints'], ['restart vlc'])
        self.assertIn('real app (Windows)', vlc['tested'])

    def test_partial_activation_lists_each_installation(self):
        zip_ = self.row('7zip')
        self.assertEqual(zip_['status'], 'Partly in Corsican')
        self.assertEqual(zip_['describedby'], 'status-7zip desc-7zip')
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

    def test_problems_first_then_attention_then_the_usual_order(self):
        self.assertEqual([row['name'] for row in self.result['programs']], ['winmerge', '7zip', 'filezilla', 'firefox', 'vlc', 'old'])

    def test_summary_counts_and_names_what_needs_the_person(self):
        summary = self.result['summary']
        self.assertFalse(summary['hidden'])
        self.assertEqual(summary['on'], '5 of 6 in Corsican')
        self.assertEqual(summary['off'], '1 in the original language')
        self.assertEqual(summary['attention'], '3 programs need attention')
        self.assertIn('tone-danger', summary['attentionClass'])
        self.assertEqual(summary['jumps'][0], 'WinMerge Failed')
        self.assertEqual(summary['jumps'][1], '7-Zip Partly in Corsican')
        # Active but deferred: the installer's advice says what to do.
        self.assertEqual(summary['jumps'][2], 'FileZilla Fermez FileZilla')
        self.assertEqual(summary['update'], self.result['en']['never'])

    def test_unchanged_parts_keep_their_nodes_across_refreshes(self):
        self.assertEqual(self.result['unchangedKept'], [True] * 6)
        self.assertEqual(self.result['changedRedrawn'], [True] * 6)

    def test_hooks_for_the_appearance_page(self):
        self.assertEqual(self.result['renderEvents'][-1], 'en')
        self.assertEqual(self.result['pageEvent'], 'appearance')
        self.assertEqual(self.result['hooks'], ['call', 'icon', 'language', 'make', 't'])
        self.assertEqual(self.result['hookLanguage'], 'en')
        self.assertEqual(self.result['appearanceText'][0], self.result['appearanceText'][1])
        self.assertEqual(self.result['ownTextFirst'], 'Appearance')

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


STYLE = PAGE.parent / 'style.css'
PALETTES = ('maquis', 'mare', 'granitu', 'tramontu', 'notte')
TOKENS = ('bg', 'surface', 'surface-2', 'line', 'text', 'muted', 'accent', 'on-accent', 'accent-soft', 'track', 'knob', 'focus')
STATUS = ('ok', 'warn', 'danger', 'info')


def luminance(colour):
    """WCAG relative luminance of #rrggbb."""
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    light, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def palettes():
    """{palette: {'l'|'d': {token: #hex}}} from style.css, status colours (the same for all) merged into each."""
    css = STYLE.read_text(encoding='utf-8')
    status = re.search(r'/\* @status[^*]*\*/\s*:root \{([^}]*)\}', css).group(1)
    found = {}
    for name, body in re.findall(r'/\* @palette (\w+) \*/\s*[^{]+\{([^}]*)\}', css):
        found[name] = {theme: {key: value.lower() for key, value in re.findall(rf'--{theme}-([\w-]+):\s*(#[0-9a-fA-F]{{6}})', body + status)}
                       for theme in ('l', 'd')}
    return found


class ContrastTests(unittest.TestCase):
    """WCAG AA in every palette and theme: text 4.5:1, interface parts 3:1, status colours on the surfaces."""

    def test_every_palette_defines_every_token(self):
        found = palettes()
        self.assertEqual(set(found), set(PALETTES))
        for name, themes in found.items():
            for theme, tokens in themes.items():
                for token in TOKENS + STATUS + tuple(s + '-soft' for s in STATUS) + ('on-danger',):
                    self.assertIn(token, tokens, f'{name} {theme} {token}')

    def test_ratios(self):
        text = [(fg, bg) for bg in ('bg', 'surface', 'surface-2', 'accent-soft') for fg in ('text', 'muted')]
        text += [('accent', 'surface'), ('accent', 'surface-2'), ('accent', 'bg'), ('accent', 'accent-soft'), ('on-accent', 'accent'),
                 ('on-danger', 'danger')]
        for status in STATUS:
            text += [(status, 'surface'), (status, 'surface-2'), (status, 'bg'), (status, status + '-soft'), ('text', status + '-soft')]
        parts = [('track', 'surface'), ('track', 'surface-2'), ('knob', 'track'), ('knob', 'accent'), ('accent', 'surface'),
                 ('focus', 'bg'), ('focus', 'surface'), ('focus', 'surface-2')]
        failures, lowest = [], {}
        for name, themes in palettes().items():
            for theme, tokens in themes.items():
                for pairs, need in ((text, 4.5), (parts, 3.0)):
                    for fg, bg in pairs:
                        ratio = contrast(tokens[fg], tokens[bg])
                        lowest[name, theme] = min(lowest.get((name, theme), 99), ratio)
                        if ratio < need:
                            failures.append(f'{name} {theme}: {fg} on {bg} {ratio:.2f} < {need}')
        self.assertEqual(failures, [])

    def test_known_ratio(self):
        self.assertAlmostEqual(contrast('#000000', '#ffffff'), 21.0)
        self.assertAlmostEqual(contrast('#767676', '#ffffff'), 4.54, places=2)


class PageStructureTests(unittest.TestCase):
    def test_appearance_page_and_its_entry(self):
        html = PAGE.read_text(encoding='utf-8')
        self.assertRegex(html, r'<section id="appearance" data-page-panel[^>]*>\s*<header class="page-head">\s*<h1 data-t="nav_appearance">')
        self.assertIn('data-page="appearance"', html)
        found = texts()
        self.assertEqual((found['co']['nav_appearance'], found['fr']['nav_appearance'], found['en']['nav_appearance']),
                         ('Aspettu', 'Apparence', 'Appearance'))

    def test_every_icon_used_is_in_the_sprite(self):
        html, code = script()
        symbols = set(re.findall(r'<symbol id="i-([\w-]+)"', html))
        used = set(re.findall(r'href="#i-([\w-]+)"', html)) | set(re.findall(r'icon\("([\w-]+)"', code))
        app = (PAGE.parent / 'app.js').read_text(encoding='utf-8')
        for table in re.findall(r'(?:programIcons|tones) = \{(.*?)\};', app, re.S):
            used |= set(re.findall(r'"([\w-]+)"\]?(?:,|\s*\})', table)) - set(re.findall(r'(\w+):', table))
        used |= set(re.findall(r'(?:up_to_date|available|unknown|ahead|none): "([\w-]+)"', app))
        # The tones table also names tones (ok, warn…): only names that are not tones must be icons.
        self.assertFalse(used - symbols - {'neutral', 'danger', 'info'})
        for glyph in ('ok', 'warn', 'error', 'blocked', 'partial', 'off', 'restart', 'clock', 'update', 'chevron', 'external', 'app'):
            self.assertIn(glyph, symbols)


UPDATE_KEYS = [
    'update_heading', 'update_current', 'update_latest', 'update_checked', 'update_never', 'update_checking',
    'update_up_to_date', 'update_available', 'update_unknown', 'update_unknown_plain', 'update_ahead', 'update_check',
    'update_install', 'update_restart', 'update_auto', 'update_auto_detail', 'update_auto_started', 'update_updated',
    'update_repaired', 'update_unchanged', 'update_failed', 'update_failed_plain', 'update_waiting_one',
    'update_waiting_many', 'update_restart_text', 'update_restarting', 'update_restart_failed', 'activation_waiting',
    'minecraft_switch_new', 'busy',
]


class UpdateTextTests(unittest.TestCase):
    def test_update_texts_exist_everywhere_with_the_same_placeholders(self):
        found = texts()
        for language, values in found.items():
            for key in UPDATE_KEYS:
                self.assertTrue(values.get(key), f'{key} missing in {language}')
                self.assertEqual(set(re.findall(r'\{\w+\}', values[key])), set(re.findall(r'\{\w+\}', found['en'][key])),
                                 f'{key} in {language}')


# The same small DOM, then each update scenario rendered in the three languages.
UPDATE_HARNESS = HARNESS[:HARNESS.index('const out = vm.runInContext(`')] + r'''
const out = vm.runInContext(`
  const clean = value => value == null ? value : value.replace(/[\\u00a0\\u202f]/g, " ");
  const button = id => ({ hidden: Boolean($(id).hidden), disabled: Boolean($(id).disabled) });
  const result = {};
  for (const lang of ["en", "fr", "co"]) {
    language = lang;
    result[lang] = {};
    for (const [name, scenario] of Object.entries(fixture)) {
      state = scenario;
      restarting = scenario.restarting_now ? { pid: 1, until: Date.now() + 45000 } : null;
      savingPreference = false;
      render();
      const minecraft = $("switches").children.map(row => row.find(node => node.id === "activate-minecraft")[0]).find(Boolean);
      result[lang][name] = {
        facts: clean($("update-facts").textContent),
        status: clean($("update-status").textContent), statusClass: $("update-status").className,
        result: $("update-result").hidden ? null : $("update-result").children.map(line => clean(line.textContent)),
        resultClass: $("update-result").className,
        now: button("update-now"), restart: button("update-restart"), check: button("update-check"),
        auto: { checked: Boolean($("switch-auto-update").checked), disabled: Boolean($("switch-auto-update").disabled) },
        banner: $("update-banner").hidden ? null : clean($("update-text").textContent),
        bannerInstall: button("update-install"), bannerRestart: button("update-banner-restart"),
        activity: clean($("activity-text").textContent),
        minecraft: minecraft ? { text: minecraft.textContent, disabled: "disabled" in minecraft.attributes } : null,
        minecraftDetails: clean($("switches").children.map(row => row.find(node => node.tagName === "DETAILS")[0]).filter(Boolean).map(node => node.textContent).join(" | ")),
      };
    }
  }
  JSON.stringify(result);
`, context);
process.stdout.write(out);
'''

IDLE = {'title': None, 'lines': [], 'running': False, 'ok': None, 'progress': None, 'result': None, 'busy': False}
NO_RESTART = {'available': False, 'version': None, 'error': None}


def scenario(status=None, latest='0.23.0', error=None, checking=False, job=None, restart=None, auto=False, auto_started=None,
             items=None, restarting_now=False):
    return {**FIXTURE, 'version': '0.22.0', 'pid': 1, 'preferences': {'auto_update': auto}, 'restarting_now': restarting_now,
            'items': items if items is not None else FIXTURE['items'][:1],
            'update': {'current': '0.22.0', 'latest': latest if status else None, 'status': status, 'checked': 1.7e9 if status else None,
                       'error': error, 'checking': checking, 'auto_started': auto_started, 'restart': restart or NO_RESTART},
            'job': {**IDLE, **(job or {})}}


WAITING_ITEMS = [
    entry('Firefox', activation='blocked', coverage=None, validation=None, updated=None, instances=[
        instance('blocked', 'Firefox est ouvert.', 'Fermez Firefox.')]),
    entry('Minecraft', activation='active', coverage=None, validation=None, updated=None, waiting=1, instances=[
        instance('active', kind='Prism', location='/games/a'),
        {**instance('waiting', 'New game folder: Corsu has not switched it yet.', kind='Prism', location='/games/new'), 'version': '1.21.4'}]),
]
UPDATED = {'title': 'update', 'ok': True, 'result': {'corsu': 'updated', 'from': '0.22.0', 'to': '0.23.0', 'restart_app': True, 'error': None}}
UPDATE_SCENARIOS = {
    'never': scenario(),
    'checking': scenario(checking=True),
    'up_to_date': scenario('up_to_date', latest='0.22.0', auto=True),
    'available': scenario('available'),
    'unknown': scenario('unknown', latest=None, error='GitHub could not be reached.'),
    'unknown_plain': scenario('unknown', latest=None),
    'ahead': scenario('ahead', latest='0.21.0'),
    'running': scenario('available', job={'title': 'update', 'running': True, 'progress': {'percent': 30, 'label': 'x'}}),
    'auto': scenario('available', auto=True, auto_started='0.23.0', job={'title': 'update', 'running': True}),
    'updated': scenario('up_to_date', job=UPDATED, items=WAITING_ITEMS,
                        restart={'available': True, 'version': '0.23.0', 'error': None}),
    'repaired': scenario('up_to_date', latest='0.22.0', job={'title': 'update', 'ok': True, 'result': {'corsu': 'repaired', 'to': '0.22.0'}}),
    'unchanged': scenario('up_to_date', latest='0.22.0', job={'title': 'update', 'ok': True, 'result': {'corsu': 'unchanged', 'to': '0.22.0'}}),
    'failed': scenario('available', job={'title': 'update', 'ok': False, 'result': {'corsu': 'failed', 'error': 'Checksum mismatch', 'restart_app': False}}),
    'failed_plain': scenario('available', job={'title': 'update', 'ok': False}),
    'busy': scenario('available', job={'title': 'update', 'ok': False, 'busy': True}),
    'restart_failed': scenario('up_to_date', restart={'available': True, 'version': '0.23.0', 'error': 'la nouvelle copie n\'a pas répondu'}),
    'restarting': scenario('up_to_date', restart={'available': True, 'version': '0.23.0', 'error': None}, restarting_now=True),
}


@unittest.skipUnless(shutil.which('node'), 'node is not installed')
class UpdateRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            harness, fixture = Path(folder) / 'harness.js', Path(folder) / 'fixture.json'
            harness.write_text(UPDATE_HARNESS, encoding='utf-8')
            fixture.write_text(json.dumps(UPDATE_SCENARIOS), encoding='utf-8')
            done = subprocess.run(['node', str(harness), str(PAGE), str(fixture)], capture_output=True, text=True, encoding='utf-8', timeout=60)
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.result = json.loads(done.stdout)
        cls.en = cls.result['en']

    def test_no_key_shows_through_in_any_language(self):
        for language, scenarios in self.result.items():
            for name, view in scenarios.items():
                shown = json.dumps(view, ensure_ascii=False)
                self.assertNotRegex(shown, r'\b(update|activation|minecraft)_[a-z_]+\b', f'{language} {name}')
                self.assertNotIn('undefined', shown, f'{language} {name}')
                self.assertNotIn('{', view['status'], f'{language} {name}')

    def test_each_status_reads_differently(self):
        statuses = {name: self.en[name]['status'] for name in ('never', 'checking', 'up_to_date', 'available', 'unknown', 'ahead')}
        self.assertEqual(len(set(statuses.values())), len(statuses))
        self.assertEqual(statuses['up_to_date'], 'Corsu is up to date.')
        self.assertEqual(statuses['available'], 'Corsu 0.23.0 is available (you have 0.22.0).')
        self.assertEqual(statuses['unknown'], 'Could not check for updates: GitHub could not be reached.')
        self.assertEqual(self.en['unknown_plain']['status'], 'Could not check for updates.')
        self.assertIn('development version', statuses['ahead'])
        self.assertEqual(statuses['checking'], 'Checking for updates…')
        self.assertEqual(self.en['ahead']['statusClass'], 'update-status ahead')
        self.assertEqual(self.en['unknown']['statusClass'], 'update-status unknown')
        self.assertIn('0.22.0', self.en['available']['facts'])
        self.assertIn('0.23.0', self.en['available']['facts'])
        self.assertIn('Last check—', self.en['never']['facts'])
        for language in ('fr', 'co'):
            views = self.result[language]
            self.assertEqual(len({views[name]['status'] for name in statuses}), len(statuses), language)

    def test_update_button_only_for_an_available_release_and_no_job(self):
        self.assertFalse(self.en['available']['now']['disabled'])
        for name in ('never', 'checking', 'up_to_date', 'unknown', 'ahead', 'running', 'auto'):
            self.assertTrue(self.en[name]['now']['disabled'], name)
        self.assertTrue(self.en['checking']['check']['disabled'])
        self.assertTrue(self.en['running']['check']['disabled'])
        self.assertFalse(self.en['unknown']['check']['disabled'])
        self.assertTrue(self.en['available']['restart']['hidden'])
        self.assertTrue(self.en['restarting']['restart']['disabled'])

    def test_banner(self):
        self.assertEqual(self.en['available']['banner'], 'Corsu 0.23.0 is available (you have 0.22.0).')
        self.assertFalse(self.en['available']['bannerInstall']['hidden'])
        self.assertTrue(self.en['available']['bannerRestart']['hidden'])
        for name in ('never', 'up_to_date', 'unknown', 'ahead', 'running', 'restarting'):
            self.assertIsNone(self.en[name]['banner'], name)
        self.assertIn('Automatic update to Corsu 0.23.0', self.en['auto']['banner'])
        self.assertTrue(self.en['auto']['bannerInstall']['hidden'])
        self.assertEqual(self.en['updated']['banner'], 'Corsu 0.23.0 is installed. Restart Corsu to use it.')
        self.assertFalse(self.en['updated']['bannerRestart']['hidden'])

    def test_automatic_updates_switch(self):
        self.assertTrue(self.en['up_to_date']['auto']['checked'])
        self.assertFalse(self.en['available']['auto']['checked'])
        self.assertFalse(self.en['available']['auto']['disabled'])
        self.assertIn('Automatic update to Corsu 0.23.0', self.en['auto']['result'][0])

    def test_result_after_an_update_names_what_waits_and_offers_the_restart(self):
        updated = self.en['updated']
        self.assertEqual(updated['result'][0], 'Corsu was updated to version 0.23.0.')
        self.assertEqual(updated['result'][1], '2 parts are waiting: Firefox (Fermez Firefox); Minecraft (New game folder: Corsu has not switched it yet).')
        self.assertEqual(len(updated['result']), 2)
        self.assertEqual(updated['status'], 'Corsu 0.23.0 is installed. Restart Corsu to use it.')
        self.assertIn('attention', updated['resultClass'])
        self.assertFalse(updated['restart']['hidden'])
        self.assertFalse(updated['restart']['disabled'])
        self.assertTrue(updated['now']['hidden'])
        self.assertEqual(updated['activity'], 'Update finished.')
        self.assertIn('2 parties attendent', self.result['fr']['updated']['result'][1])
        self.assertIn('2 parti aspettanu', self.result['co']['updated']['result'][1])
        self.assertEqual(self.en['repaired']['result'], ['Corsu 0.22.0 was repaired.'])
        self.assertEqual(self.en['unchanged']['result'], ['Corsu 0.22.0 was already installed: nothing changed.'])

    def test_failures_are_understandable(self):
        self.assertEqual(self.en['failed']['result'], ['The update did not complete: Checksum mismatch. The previous version stays in place.'])
        self.assertIn('problem', self.en['failed']['resultClass'])
        self.assertIn('details are in the log', self.en['failed_plain']['result'][0])
        self.assertEqual(self.en['busy']['result'], ['Corsu is busy (another window or the installer is working).'])
        self.assertEqual(self.en['busy']['activity'], 'Corsu is busy (another window or the installer is working).')
        self.assertIn("Corsu could not restart: la nouvelle copie n'a pas répondu.", self.en['restart_failed']['result'])
        self.assertEqual(self.en['restarting']['result'], ['Corsu is restarting…'])
        self.assertFalse(self.en['restart_failed']['restart']['hidden'])

    def test_new_minecraft_folders_wait_for_activation(self):
        updated = self.en['updated']
        self.assertEqual(updated['minecraft'], {'text': 'Switch the new folders to Corsican', 'disabled': False})
        self.assertIn('Waiting for activation', updated['minecraftDetails'])
        self.assertIn('1.21.4', updated['minecraftDetails'])
        self.assertIsNone(self.en['available']['minecraft'])
        self.assertEqual(self.result['fr']['updated']['minecraft']['text'], 'Passer les nouveaux dossiers en corse')


if __name__ == '__main__':
    unittest.main()
