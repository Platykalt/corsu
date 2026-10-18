#!/usr/bin/env python3
"""Short review sets for Corsican speakers, and their answers as proposals tied to the exact source text.

    python3 tools/review_sets.py build            write review/sets/*.md, *.html and review/sets.json
    python3 tools/review_sets.py build --check    exit 1 when the committed sets differ from what the data gives
    python3 tools/review_sets.py import FILE... [--via TEXT] [--date YYYY-MM-DD]
                                                  add the answers of reply texts or filled-in sets to review/answers.jsonl
    python3 tools/review_sets.py status [--json]  each answer's status against the current texts
    python3 tools/review_sets.py examine SET ITEM accepted|rejected [--note TEXT]
                                                  record the maintainer's decision on an answer

The sets come from the Minecraft review batches (minecraft/java/review-batches/NN-*.md): each batch is cut into sets
of about ten questions (at most 12 texts). Each question keeps its texts (key, English, official French, the
Corsican now in the pack, from co_fr.json), where it appears and its question. Each text carries the hash of its
English source (keys.tsv, the 12-character SHA-1 used everywhere for Minecraft), the game version and the hash of
the Corsican shown, so an answer says exactly what it was about.

A set is answered without Git: the HTML page (one file, no network) gives OK / other form / skip and a comment per
question and makes a reply text to copy, save, or send as a prefilled GitHub issue (opened only on a click); the
Markdown page can be filled in by hand. `import` reads either, plus pasted issue bodies, and stores each answer as
a proposal: nothing changes in the pack. `status` compares every answer with the current data: when the English
source of one of its texts changed (another hash), or the Corsican it approved changed, it is "to-re-examine",
whatever it was before. `examine` records the maintainer's decision; only an accepted answer whose texts are still
the same counts as a speaker's validation (tools/mcmemory.py writes it into the memory).
"""
import argparse
import csv
import datetime
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
JAVA = ROOT / 'minecraft/java'
BATCHES = JAVA / 'review-batches'
OUT = ROOT / 'review'
SETS = OUT / 'sets'
MANIFEST = OUT / 'sets.json'
ANSWERS = OUT / 'answers.jsonl'
APP = 'Minecraft: Java Edition'
ISSUE = 'https://github.com/Platykalt/corsu/issues/new'
MAX_QUESTIONS = 10
MAX_TEXTS = 12
MARK = 'corsu-review v1'
OK_WORDS = {'ok', 'okay', 'oui', 'yes', 'va bè', 'vabè', 'bè', 'iè', 'd accordu', "d'accordu", 'bonu', 'bona'}


def digest(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def version():
    return (JAVA / 'VERSION').read_text(encoding='utf-8').strip()


def current_sources():
    """key -> hash of the English of the current version (keys.tsv row whose versions end with it)."""
    base = version()
    found = {}
    with open(JAVA / 'keys.tsv', encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle, delimiter='\t'):
            if row['versions'].split('..')[-1].split(',')[-1] == base:
                found[row['key']] = row['hash']
    return found


def corsican():
    return json.loads((JAVA / 'co_fr.json').read_text(encoding='utf-8'))


def shown(text):
    """A game text as the batches show it: line breaks as ¶."""
    return text.replace('\n', ' ¶ ')


# --- batches --------------------------------------------------------------------------------------------------------

def parse_batch(path):
    """(title, description fr, description en, [question]) of one review batch file."""
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    title = lines[0].lstrip('# ').strip()
    description = (lines[2].strip(), lines[3].strip())
    questions = []
    for block in re.split(r'^### ', text, flags=re.M)[1:]:
        heading, _, body = block.partition('\n')
        number, _, name = heading.partition(' — ')
        where = re.search(r'^\*\*Où / Where:\*\* (.*)$', body, re.M)
        question = re.search(r'^\*\*Question:\*\* (.*)$', body, re.M)
        rows = []
        for line in body.splitlines():
            if line.startswith('| `'):
                cells = [cell.strip() for cell in line.strip().strip('|').split(' | ')]
                key, english, french, corsican_then = cells
                rows.append({'key': key.strip('`'), 'english': english, 'french': french,
                             'asked': corsican_then.strip('*')})
        questions.append({'id': number.strip(), 'title': name.strip(), 'where': where.group(1).strip() if where else '',
                          'question': question.group(1).strip() if question else '', 'texts': rows})
    return title, description, questions


def build_sets():
    sources, co, base = current_sources(), corsican(), version()
    sets = []
    for path in sorted(BATCHES.glob('[0-9][0-9]-*.md')):
        title, description, questions = parse_batch(path)
        batch = path.name[:2]
        groups, group = [], []
        for question in questions:
            texts = sum(len(item['texts']) for item in group)
            if group and (len(group) >= MAX_QUESTIONS or texts + len(question['texts']) > MAX_TEXTS):
                groups.append(group)
                group = []
            group.append(question)
        if group:
            groups.append(group)
        for number, group in enumerate(groups, 1):
            items = []
            for question in group:
                texts = []
                for row in question['texts']:
                    key = row['key']
                    if key not in sources or key not in co:
                        raise SystemExit(f'{path.name} {question["id"]}: {key} is not in keys.tsv or co_fr.json for {base}')
                    now = co[key]
                    texts.append({'key': key, 'english': row['english'], 'french': row['french'],
                                  'corsican': shown(now), 'source_hash': sources[key], 'corsican_hash': digest(now),
                                  # The question was written about another Corsican: say so beside it.
                                  'asked': row['asked'] if row['asked'] != shown(now) else None})
                items.append({'id': question['id'], 'title': question['title'], 'where': question['where'],
                              'question': question['question'], 'texts': texts})
            sets.append({'id': f'mc{batch}-{number}', 'batch': path.name, 'title': title,
                         'description': description, 'part': number, 'parts': len(groups),
                         'app': APP, 'version': base, 'items': items})
    return sets


# --- pages ----------------------------------------------------------------------------------------------------------

def texts_field(item):
    return ' '.join(f"{text['key']}@{text['source_hash']}:{text['corsican_hash']}" for text in item['texts'])


def markdown(entry):
    count = sum(len(item['texts']) for item in entry['items'])
    lines = [f"# Relecture {entry['id']} · Review {entry['id']}", '',
             f"{entry['title']} — partie {entry['part']}/{entry['parts']} · part {entry['part']}/{entry['parts']}", '',
             entry['description'][0], entry['description'][1], '',
             f"**{len(entry['items'])} questions, {count} textes · texts.** {APP} {entry['version']}.", '',
             '> **Fr.** Ces traductions ont été produites puis revues par une IA, sans relecture humaine. Votre réponse '
             'sera enregistrée comme une **proposition**, examinée ensuite : rien ne change dans le jeu sans cet examen.',
             '>',
             '> **En.** These translations were produced and revised by an AI, with no human review. Your answer is '
             'recorded as a **proposal**, examined afterwards: nothing changes in the game without that.', '',
             '## Répondre · How to answer', '',
             f"- **Le plus simple · Easiest:** téléchargez [{entry['id']}.html]({entry['id']}.html) (bouton « Download raw "
             "file »), ouvrez-le dans votre navigateur, répondez, puis copiez la réponse ou ouvrez le ticket prérempli. "
             "Download the HTML page, open it in your browser, answer, then copy the reply or open the prefilled issue.",
             '- **Ou ici · Or here:** copiez ce fichier, écrivez « OK » ou la forme que vous utiliseriez sous chaque '
             '« Réponse », et envoyez-le dans un [ticket](' + ISSUE + '). Copy this file, write "OK" or your own form '
             'under each "Answer", and send it in an issue.',
             '- Vous pouvez sauter une question · You may skip any question. « ¶ » = retour à la ligne · line break; '
             '`%s` = rempli par le jeu · filled in by the game.', '', '---', '']
    for item in entry['items']:
        lines += [f"### {item['id']} — {item['title']}", '',
                  f"<!-- {MARK} set={entry['id']} item={item['id']} version={entry['version']} texts={texts_field(item)} -->", '',
                  f"**Où · Where:** {item['where']}", '',
                  '| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |', '| --- | --- | --- | --- |']
        for text in item['texts']:
            lines.append(f"| `{text['key']}` | {text['english']} | {text['french']} | **{text['corsican']}** |")
        lines.append('')
        for text in item['texts']:
            if text['asked']:
                lines += [f"*La question a été écrite pour · The question was written for:* {text['asked']} "
                          f"(`{text['key']}`)", '']
        lines += [f"**Question:** {item['question']}", '',
                  '**Réponse · Answer** (OK, ou votre forme · or your form):', '', '> ', '',
                  '**Remarque · Comment** (facultatif · optional):', '', '> ', '']
    return '\n'.join(lines).rstrip() + '\n'


PAGE = r'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relecture __ID__</title>
<style>
:root { --bg: #f7f5f0; --surface: #fff; --line: #d9d4c8; --text: #1f2421; --muted: #5b625d; --accent: #1d6b5a;
  --on-accent: #fff; --soft: #e3f0ec; --warn: #8a5300; --warn-soft: #fbefd9; color-scheme: light dark; }
@media (prefers-color-scheme: dark) { :root { --bg: #151917; --surface: #1e2421; --line: #36403b; --text: #e8ece9;
  --muted: #a7b0ab; --accent: #6cc3ad; --on-accent: #0f1513; --soft: #203a33; --warn: #f0b867; --warn-soft: #3a2e1b; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 1rem/1.5 system-ui, sans-serif; }
main { max-width: 52rem; margin: 0 auto; padding: 1.5rem 1rem 4rem; }
h1 { font-size: 1.5rem; margin: 0 0 .25rem; } h2 { font-size: 1.1rem; margin: 2rem 0 .75rem; }
.muted { color: var(--muted); } .note { background: var(--soft); border-radius: .5rem; padding: .75rem 1rem; }
article { background: var(--surface); border: 1px solid var(--line); border-radius: .75rem; padding: 1rem; margin: 1rem 0; }
article h3 { margin: 0 0 .5rem; font-size: 1rem; }
table { border-collapse: collapse; width: 100%; font-size: .9rem; margin: .5rem 0; display: block; overflow-x: auto; }
th, td { text-align: left; border-bottom: 1px solid var(--line); padding: .35rem .5rem; vertical-align: top; }
td.co { font-weight: 600; } code { font-size: .8rem; overflow-wrap: anywhere; }
.asked { background: var(--warn-soft); color: var(--warn); border-radius: .4rem; padding: .25rem .5rem; font-size: .875rem; }
fieldset { border: 0; padding: 0; margin: .75rem 0 0; display: flex; flex-wrap: wrap; gap: .5rem 1rem; }
label { cursor: pointer; } input[type=text], textarea { width: 100%; font: inherit; padding: .4rem .5rem;
  border: 1px solid var(--line); border-radius: .4rem; background: var(--bg); color: var(--text); }
.field { display: block; margin-top: .5rem; font-size: .9rem; }
button { font: inherit; padding: .5rem .9rem; border-radius: .5rem; border: 1px solid var(--line); background: var(--surface);
  color: var(--text); cursor: pointer; } button.main { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.buttons { display: flex; flex-wrap: wrap; gap: .5rem; margin: .75rem 0; }
#reply { font-family: ui-monospace, monospace; font-size: .8rem; min-height: 12rem; }
#said { min-height: 1.5rem; }
</style>
</head>
<body>
<main>
<h1>Relecture __ID__ · Review __ID__</h1>
<p class="muted" id="intro"></p>
<p class="note"><b>Fr.</b> Ces traductions ont été produites puis revues par une IA, sans relecture humaine. Votre réponse
est une <b>proposition</b>, examinée ensuite : rien ne change dans le jeu sans cet examen. Rien n'est envoyé tant que vous
ne cliquez pas sur « Ouvrir un ticket » ; aucun nom n'est demandé.<br><b>En.</b> These translations were produced and
revised by an AI, with no human review. Your answer is a <b>proposal</b>, examined afterwards. Nothing is sent unless you
click "Open an issue"; no name is asked.</p>
<p class="muted">« ¶ » = retour à la ligne · line break ; <code>%s</code> = rempli par le jeu · filled in by the game.</p>
<div id="items"></div>
<h2>Votre réponse · Your reply</h2>
<p class="muted">Relisez-la avant de l'envoyer · Read it before sending it. Par courriel, en fichier ou par ticket GitHub (compte GitHub
nécessaire) · By e-mail, as a file or as a GitHub issue (needs a GitHub account).</p>
<textarea id="reply" readonly aria-label="Réponse à copier · Reply to copy"></textarea>
<div class="buttons">
<button type="button" class="main" id="copy">Copier · Copy</button>
<button type="button" id="save">Enregistrer le fichier · Save as a file</button>
<button type="button" id="issue">Ouvrir un ticket GitHub · Open a GitHub issue</button>
</div>
<p id="said" role="status" class="muted"></p>
</main>
<script type="application/json" id="data">__DATA__</script>
<script>
"use strict";
const set = JSON.parse(document.getElementById("data").textContent);
const STORE = "corsu-review-" + set.id;
let saved = {};
try { saved = JSON.parse(localStorage.getItem(STORE) || "{}"); } catch (error) {}
const el = (tag, attributes = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (name === "text") node.textContent = value; else if (name.startsWith("on")) node.addEventListener(name.slice(2), value);
    else if (value !== false && value != null) node.setAttribute(name, value === true ? "" : value);
  }
  node.append(...children.filter(child => child != null));
  return node;
};
// *word* in the questions is emphasis; everything else is plain text.
const rich = text => text.split(/(\*[^*]+\*)/).map(part => /^\*[^*]+\*$/.test(part) ? el("em", { text: part.slice(1, -1) }) : part);
const answers = () => set.items.map(item => saved[item.id] || {});
function remember() { try { localStorage.setItem(STORE, JSON.stringify(saved)); } catch (error) {} reply(); }
const line = value => (value || "").replace(/\s*\n\s*/g, " / ").trim();
function reply() {
  const lines = ["__MARK__", "set: " + set.id, "data: " + set.app + " " + set.version];
  set.items.forEach((item, index) => {
    const answer = answers()[index];
    lines.push("item: " + item.id, "texts: " + item.texts.map(text => `${text.key}@${text.source_hash}:${text.corsican_hash}`).join(" "),
      "answer: " + (answer.kind || "skip"), "proposal: " + (answer.kind === "other" ? line(answer.proposal) : ""), "comment: " + line(answer.comment));
  });
  lines.push("end");
  document.getElementById("reply").value = lines.join("\n");
}
const count = set.items.reduce((sum, item) => sum + item.texts.length, 0);
document.getElementById("intro").textContent = `${set.title} — ${set.part}/${set.parts}. ${set.items.length} questions, ${count} textes · texts. ${set.app} ${set.version}.`;
const box = document.getElementById("items");
for (const item of set.items) {
  const state = saved[item.id] = saved[item.id] || {};
  const name = "q-" + item.id;
  const proposal = el("input", { type: "text", id: name + "-proposal", value: state.proposal || "", disabled: state.kind !== "other",
    oninput: event => { state.proposal = event.target.value; remember(); } });
  const choice = (kind, label) => el("label", {}, el("input", { type: "radio", name, value: kind, checked: (state.kind || "skip") === kind,
    onchange: () => { state.kind = kind; proposal.disabled = kind !== "other"; if (kind === "other") proposal.focus(); remember(); } }), " " + label);
  box.append(el("article", { "aria-labelledby": name + "-title" },
    el("h3", { id: name + "-title", text: `${item.id} — ${item.title}` }),
    el("p", {}, el("b", { text: "Où · Where : " }), ...rich(item.where)),
    el("table", {}, el("thead", {}, el("tr", {}, ...["Clé · Key", "English", "Français (officiel)", "Corse actuel · Corsican now"].map(text => el("th", { scope: "col", text })))),
      el("tbody", {}, ...item.texts.map(text => el("tr", {}, el("td", {}, el("code", { text: text.key })), el("td", { text: text.english }),
        el("td", { text: text.french }), el("td", { class: "co", lang: "co", text: text.corsican }))))),
    ...item.texts.filter(text => text.asked).map(text => el("p", { class: "asked", text: `La question a été écrite pour · The question was written for : ${text.asked} (${text.key})` })),
    el("p", {}, el("b", { text: "Question : " }), ...rich(item.question)),
    el("fieldset", {}, el("legend", { class: "muted", text: "Votre avis · Your view" }),
      choice("ok", "OK, naturel · natural"), choice("other", "J'écrirais autrement · I would write it otherwise"), choice("skip", "Passer · Skip")),
    el("label", { class: "field", for: name + "-proposal", text: "Votre forme · Your form" }), proposal,
    el("label", { class: "field", for: name + "-comment", text: "Remarque (facultatif) · Comment (optional)" }),
    el("textarea", { id: name + "-comment", rows: "2", oninput: event => { state.comment = event.target.value; remember(); } }, state.comment || "")));
}
reply();
const say = text => { document.getElementById("said").textContent = text; };
document.getElementById("copy").addEventListener("click", async () => {
  const area = document.getElementById("reply");
  try { await navigator.clipboard.writeText(area.value); say("Copié · Copied."); }
  catch (error) { area.select(); say("Sélectionnée : Ctrl+C pour copier · Selected: Ctrl+C to copy."); }
});
document.getElementById("save").addEventListener("click", () => {
  const link = el("a", { href: URL.createObjectURL(new Blob([document.getElementById("reply").value], { type: "text/plain" })), download: `relecture-${set.id}.txt` });
  document.body.append(link); link.click(); link.remove();
});
document.getElementById("issue").addEventListener("click", () => {
  const body = "Réponse à la relecture " + set.id + " · Reply to review " + set.id + "\n\n```text\n" + document.getElementById("reply").value + "\n```\n";
  let url = "__ISSUE__?" + new URLSearchParams({ title: "Relecture " + set.id, body });
  // Browsers and GitHub refuse very long addresses: then the issue opens empty and the reply is pasted by hand.
  if (url.length > 7500) { url = "__ISSUE__?" + new URLSearchParams({ title: "Relecture " + set.id }); say("Réponse trop longue pour l'adresse : copiez-la dans le ticket · Reply too long for the address: paste it into the issue."); }
  window.open(url, "_blank", "noopener");
});
</script>
</body>
</html>
'''


def page(entry):
    data = json.dumps(entry, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return (PAGE.replace('__ID__', html.escape(entry['id'])).replace('__MARK__', MARK)
            .replace('__ISSUE__', ISSUE).replace('__DATA__', data))


def index(sets):
    lines = ['# Lots de relecture · Review sets', '',
             'Généré par `tools/review_sets.py build` depuis `minecraft/java/review-batches/`. Ne pas modifier à la main.',
             'Generated by `tools/review_sets.py build` from `minecraft/java/review-batches/`. Do not edit by hand.', '',
             '| Lot · Set | Thème · Topic | Questions | Textes · Texts | Pages |', '| --- | --- | --- | --- | --- |']
    for entry in sets:
        texts = sum(len(item['texts']) for item in entry['items'])
        lines.append(f"| {entry['id']} | {entry['title'].split(' — ', 1)[-1]} ({entry['part']}/{entry['parts']}) | "
                     f"{len(entry['items'])} | {texts} | [Markdown]({entry['id']}.md) · [HTML]({entry['id']}.html) |")
    return '\n'.join(lines) + '\n'


def render():
    """{relative path: text} of every generated file."""
    sets = build_sets()
    files = {'sets.json': json.dumps({'generated_by': 'tools/review_sets.py', 'app': APP, 'version': version(),
                                      'sets': sets}, ensure_ascii=False, indent=1) + '\n',
             'sets/README.md': index(sets)}
    for entry in sets:
        files[f"sets/{entry['id']}.md"] = markdown(entry)
        files[f"sets/{entry['id']}.html"] = page(entry)
    return files


def build(check=False):
    files = render()
    stale = []
    for name, text in files.items():
        path = OUT / name
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            stale.append(name)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
    extra = [path.relative_to(OUT).as_posix() for path in SETS.glob('*') if path.relative_to(OUT).as_posix() not in files]
    if check:
        if stale or extra:
            print(f'review/ is not up to date ({len(stale)} changed, {len(extra)} extra): run python3 tools/review_sets.py build')
            return 1
        print(f'review/: up to date ({len(files)} files)')
        return 0
    for name in extra:
        (OUT / name).unlink()
    print(f'review/: {len(files)} files, {len(stale)} written, {len(extra)} removed')
    return 0


# --- answers --------------------------------------------------------------------------------------------------------

def parse_texts(value):
    texts = []
    for part in value.split():
        match = re.match(r'^(.+)@([0-9a-f]{12}):([0-9a-f]{12})$', part)
        if match:
            texts.append({'key': match.group(1), 'source_hash': match.group(2), 'corsican_hash': match.group(3)})
    return texts


def parse_reply(text):
    """Answers of the reply blocks in a text (the HTML page's reply, as pasted in an issue or saved to a file)."""
    found = []
    for block in re.findall(re.escape(MARK) + r'\n(.*?)(?:\nend\b|\Z)', text.replace('\r\n', '\n'), re.S):
        header, current = {}, None
        for line in block.splitlines():
            name, separator, value = line.partition(':')
            if not separator:
                continue
            name, value = name.strip(), value.strip()
            if name == 'item':
                current = {'item': value}
                found.append((header, current))
            elif current is None:
                header[name] = value
            else:
                current[name] = value
        for _, item in found:
            item.setdefault('set', header.get('set'))
            item.setdefault('data', header.get('data'))
    answers = []
    for _, item in found:
        kind = item.get('answer', 'skip').lower()
        answers.append({'set': item['set'], 'item': item['item'], 'answer': kind if kind in ('ok', 'other', 'skip') else 'other',
                        'proposal': item.get('proposal') or None, 'comment': item.get('comment') or None,
                        'texts': parse_texts(item.get('texts', '')), 'data': item.get('data')})
    return answers


def quoted(body, label):
    """The text of the '> ' lines after the line that starts with `label` in a filled-in Markdown set."""
    match = re.search(r'^\*\*' + label + r'.*?$\n+((?:^>.*\n?)+)', body, re.M)
    if not match:
        return ''
    return ' / '.join(line[1:].strip() for line in match.group(1).splitlines() if line[1:].strip())


def parse_markdown(text):
    """Answers written into a Markdown set (under « Réponse · Answer » and « Remarque · Comment »)."""
    answers = []
    for match in re.finditer(r'<!-- ' + re.escape(MARK) + r' set=(\S+) item=(\S+) version=(\S+) texts=(.*?) -->(.*?)(?=<!-- '
                             + re.escape(MARK) + r'|\Z)', text, re.S):
        set_id, item, data_version, texts, body = match.groups()
        answer, comment = quoted(body, 'Réponse'), quoted(body, 'Remarque')
        normal = re.sub(r'[\s.!]+$', '', answer).casefold()
        kind = 'skip' if not answer else 'ok' if normal in OK_WORDS else 'other'
        if kind == 'skip' and not comment:
            continue
        answers.append({'set': set_id, 'item': item, 'answer': kind, 'proposal': answer if kind == 'other' else None,
                        'comment': comment or None, 'texts': parse_texts(texts), 'data': f'{APP} {data_version}'})
    return answers


def read_answers():
    if not ANSWERS.exists():
        return []
    return [json.loads(line) for line in ANSWERS.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_answers(answers):
    ANSWERS.parent.mkdir(parents=True, exist_ok=True)
    ANSWERS.write_text(''.join(json.dumps(answer, ensure_ascii=False, sort_keys=True) + '\n' for answer in answers),
                       encoding='utf-8')


def manifest_items():
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    return {(entry['id'], item['id']): (entry, item) for entry in data['sets'] for item in entry['items']}


def import_answers(paths, via=None, date=None):
    """Stores each new answer as a proposal, with the hashes it was given for (or, when the text lost them, the
    set's hashes at import time, said so in `texts_from`). Returns (added, skipped) counts."""
    known = manifest_items()
    answers = read_answers()
    seen = {(answer['set'], answer['item'], answer['answer'], answer.get('proposal'), answer.get('comment'),
             json.dumps(answer['texts'], sort_keys=True)) for answer in answers}
    added = skipped = 0
    for path in paths:
        text = Path(path).read_text(encoding='utf-8')
        for found in parse_reply(text) + parse_markdown(text):
            if found['answer'] == 'skip' and not found.get('comment'):
                continue
            if (found['set'], found['item']) not in known:
                print(f'{path}: unknown set or question {found["set"]} {found["item"]}, left out', file=sys.stderr)
                skipped += 1
                continue
            entry, item = known[(found['set'], found['item'])]
            texts_from = 'answer'
            if not found['texts']:
                found['texts'] = [{name: text[name] for name in ('key', 'source_hash', 'corsican_hash')} for text in item['texts']]
                texts_from = 'set at import'
            corsican_now = {text['key']: text['corsican'] for text in item['texts']}
            for text in found['texts']:
                if text['corsican_hash'] == next((t['corsican_hash'] for t in item['texts'] if t['key'] == text['key']), None):
                    text['corsican'] = corsican_now.get(text['key'])
            identity = (found['set'], found['item'], found['answer'], found.get('proposal'), found.get('comment'),
                        json.dumps(found['texts'], sort_keys=True))
            if identity in seen:
                skipped += 1
                continue
            seen.add(identity)
            answers.append({'set': found['set'], 'item': found['item'], 'app': entry['app'],
                            'version': (found.get('data') or '').rsplit(' ', 1)[-1] or entry['version'],
                            'answer': found['answer'], 'proposal': found.get('proposal'), 'comment': found.get('comment'),
                            'texts': found['texts'], 'texts_from': texts_from,
                            'received': date or datetime.date.today().isoformat(), 'via': via,
                            'status': 'proposal', 'examined': None})
            added += 1
    write_answers(answers)
    return added, skipped


def status_of(answer, sources=None, co=None):
    """(status, reasons) of one answer against the current texts. A changed English source, or a changed Corsican
    under an OK, sends any answer back to 'to-re-examine'; otherwise its recorded status (proposal, accepted,
    rejected) stands."""
    sources = current_sources() if sources is None else sources
    co = corsican() if co is None else co
    reasons = []
    for text in answer['texts']:
        now = sources.get(text['key'])
        if now != text['source_hash']:
            reasons.append(f"{text['key']}: English source changed ({text['source_hash']} -> {now or 'gone'})")
        elif answer['answer'] == 'ok' and digest(co.get(text['key'], '')) != text['corsican_hash']:
            reasons.append(f"{text['key']}: Corsican changed since this OK")
    if reasons:
        return 'to-re-examine', reasons
    return answer.get('status') or 'proposal', []


def human_validations():
    """(key, source hash) -> the speaker validation of that exact text: accepted answers whose source (and, for an
    OK, Corsican) is unchanged. When an accepted answer no longer holds, the key's current text maps to
    'to-re-examine (…)'. Proposals and rejected answers give nothing: they are not validations."""
    sources, co = current_sources(), corsican()
    found = {}
    for answer in read_answers():
        if answer.get('status') != 'accepted':
            continue
        status, _ = status_of(answer, sources, co)
        for text in answer['texts']:
            if status == 'to-re-examine':
                if sources.get(text['key']):
                    found.setdefault((text['key'], sources[text['key']]), (
                        f"to-re-examine (answer {answer['set']} {answer['item']} accepted for source "
                        f"{text['source_hash']}, {answer['app']} {answer['version']})"))
            else:
                found[(text['key'], text['source_hash'])] = (
                    f"speaker answer {answer['answer']} accepted (set {answer['set']}, question {answer['item']}, "
                    f"source {text['source_hash']}, {answer['app']} {answer['version']}, received {answer['received']})")
    return found


def examine(set_id, item, decision, note=None, date=None):
    answers = read_answers()
    changed = 0
    for answer in answers:
        if answer['set'] == set_id and answer['item'] == item and answer.get('status') in ('proposal', None):
            answer['status'] = decision
            answer['examined'] = {'date': date or datetime.date.today().isoformat(), 'note': note}
            changed += 1
    write_answers(answers)
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('build')
    command.add_argument('--check', action='store_true')
    command = commands.add_parser('import')
    command.add_argument('files', nargs='+')
    command.add_argument('--via', help='where the answer came from, e.g. "issue #12" (no names)')
    command.add_argument('--date')
    command = commands.add_parser('status')
    command.add_argument('--json', action='store_true')
    command = commands.add_parser('examine')
    command.add_argument('set')
    command.add_argument('item')
    command.add_argument('decision', choices=('accepted', 'rejected'))
    command.add_argument('--note')
    args = parser.parse_args(argv)
    if args.command == 'build':
        return build(args.check)
    if args.command == 'import':
        added, skipped = import_answers(args.files, args.via, args.date)
        print(f'{ANSWERS.relative_to(ROOT)}: {added} answers added as proposals, {skipped} left out')
        return 0
    if args.command == 'status':
        sources, co = current_sources(), corsican()
        rows = []
        for answer in read_answers():
            status, reasons = status_of(answer, sources, co)
            rows.append({'set': answer['set'], 'item': answer['item'], 'answer': answer['answer'],
                         'proposal': answer.get('proposal'), 'status': status, 'reasons': reasons})
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for row in rows:
                proposal = f" -> {row['proposal']}" if row['proposal'] else ''
                print(f"{row['set']} {row['item']}: {row['answer']}{proposal} [{row['status']}]"
                      + ''.join(f'\n    {reason}' for reason in row['reasons']))
            counts = {}
            for row in rows:
                counts[row['status']] = counts.get(row['status'], 0) + 1
            print(', '.join(f'{name}: {count}' for name, count in sorted(counts.items())) or 'no answers yet')
        return 0
    if args.command == 'examine':
        changed = examine(args.set, args.item, args.decision, args.note)
        print(f'{changed} answer(s) marked {args.decision}')
        return 0 if changed else 1
    return 2


if __name__ == '__main__':
    sys.exit(main())
