# Contextual translation memory

`lexicon/memory/*.jsonl` keeps every imported or written Corsican string **with its context and provenance**, so
that a translation made for one program is not silently reused in another one where the same words mean something
else (VLC's "Profile" is an encoding profile, Discord's is a user profile).

The flat files `lexicon-mozilla.tsv` and `lexicon-upstream.tsv` (`English|French|Corsican`) are still written, for
`engine.translate()` and the existing builds, but they are now **derived from this memory**.

## Files

| File | Written by | Content |
|---|---|---|
| `<source>.jsonl` (`audacity`, `vlc-media-player`, `mozilla-android`, …) | `tools/import_translations.py` | translations published by each project's Corsican translators |
| `corsu-<section>.jsonl` (`corsu-discord`, `corsu-firefox`, …) | `tools/import_translations.py` (also `--corsu-only`, offline) | Corsu's own rows, one file per `# ` section of `lexicon.tsv` | Not committed: rebuild with `--corsu-only`.
| `minecraft-java.jsonl` | `tools/mcmemory.py` (`--check` in the tests) | the decisions of the Minecraft review of October 2026 (`minecraft/java/review-2026-10/`): one entry per Corsican text a decision touched, with the decision, its sources and three validation levels; app-only (`reuse`), no English text (Mojang's, see `minecraft/java/LICENSING.md`), only its hash |

| `abbreviations.tsv` | by hand | short labels whose form does not tell their sense (`Bio`, `Min`, `Mod`…), with the senses each can stand for: never reused from another application automatically (see "Reuse rules") |

The text stays plain JSON lines (no gzip), so that changes stay diffable in git.

## Format

One JSON object per line and per string. Fields:

| Field | Meaning |
|---|---|
| `app` | application (imported project title, or the `lexicon.tsv` section name) |
| `component` | catalog or module: PO file name, Android resource folder, XLIFF `<file original>`, `lexicon.tsv` |
| `key` | message identity: PO `msgctxt` + `\u0004` + `msgid` (just `msgid` without context), Android resource name, XLIFF `trans-unit` id, Notepad++/fre:ac/Inno Setup path |
| `context` | object: `msgctxt`, `comments` (PO `#.`), `references` (PO `#:`), `comment` (Android XML comment), `note` (XLIFF); for Corsu rows, the section heading (a string) |
| `source_lang`, `source` | language (`en` or `fr`) and text of the source string |
| `source_fr` | the French translation of the same entry, when the project has one |
| `target` | Corsican; a list of forms for plurals |
| `plural` | `null`, or `{"source_plural": "...", "forms": [...]}` — PO form indices (`"0"`, `"1"`) or Android quantities (`"one"`, `"other"`), in the order of `target` |
| `params` | placeholders of the source (`%s`, `%1$d`, `{ $count }`…) |
| `origin` | `{"repo", "branch", "path"}` of the Corsican file |
| `version` | exact commit SHA the file was read at (Corsu rows: Corsu's HEAD, `+uncommitted` when `lexicon.tsv` had local changes) |
| `license` | license of the strings (SPDX when there is one) |
| `review` | `upstream-reviewed` (published by the project's translators), `corsu-draft`, `ai-reviewed` (an applied correction of `corrections.tsv`), `human-reviewed`, `to-review` (source changed since) |
| `fetched` | import date |
| `reuse` | `same-app`: the entry answers only for its own `app`; `engine.lookup` and `tm.py match` never offer it to another program, not even as a suggestion (`engine.app_only`). Used for decisions whose sense belongs to one program (Minecraft's "Sign" is a wooden sign, not a signature) |
| `sense` | optional: the sense the string was written for, a short phrase (`biography`, `user profile`, `encoding profile`); `context.sense` is read the same way (Minecraft decisions). Set by hand or by an extractor that knows it; an entry without one has an unknown sense, not "any sense" |
| `source_hash` | 12-character SHA-1 of the source text, when the source itself is not stored (Minecraft) |
| `decision` | for review decisions: `id` (row of the review file), `round`, `previous` text, `references` (exact entry or page), `justification`, `verdict`, and `round3` when a later round re-examined it |
| `validation` | three levels kept apart: `ai_proposal` (who proposed it), `ai_review` (which AI verification, with its verdict), `human` (a speaker's validation; `none` until one exists, `to-re-examine` when the source text changed after it, the earlier value then kept in `human_before`). A human validation holds for one source text (its `source_hash`) and is never carried to another application. An AI review is never written as a human validation |

### Size: omitted fields

To keep the memory near 20 MB without compression, redundant values are left out and restored by the reader
(`engine.read_memory`, `tools/tm.py`):

- the **first line** of a file may be `{"_defaults": {...}}`: values shared by most entries (application, license,
  version, review, date, origin…). An entry without a field takes the default; `origin` merges one level deep;
- `key` is omitted when it equals `source`; `params` when it equals the placeholders found in `source`;
  `source_fr` when the source is already French;
- empty values (`null`, `[]`, `""`) are omitted.

Always read the files through `engine.read_memory(path)` (or `engine.memory_entries()`), never line by line by hand.

## Use in the engine

- `engine.translate()` and `engine.WORDS` are unchanged (flat lexicon files).
- `engine.lookup(text, app=None, context=None)` answers from the memory: corrections (`lexicon-user.tsv`,
  `lexicon-fixes.tsv`) first, then an entry of the same application, then one with the same context (msgctxt,
  file, section, key), then a reviewed entry of a generic toolkit (wxWidgets). When the candidates for that exact
  text disagree in meaning between applications and nothing above decides, it returns `None`: the source is kept
  rather than another program's sense. Imported French that abbreviates a longer English label
  (`engine.loose_french`) is not used as a source.
- `engine.application_words(*sections)` also takes the reviewed memory entries recorded for those applications by a
  source other than `lexicon.tsv` (placed after the application's own rows).

## Pipeline for a new integration (`tools/tm.py`)

```sh
python3 tools/tm.py extract po app.pot --app "App" --out work.jsonl     # or android / xliff / json
python3 tools/tm.py match work.jsonl                                   # fills safe reuses, in place
python3 tools/tm.py stats work.jsonl                                   # counts, and the first conflicts
python3 tools/tm.py po work.jsonl --out co.po                          # native catalog (msgctxt, plurals, comments)
python3 tools/tm.py update old-work.jsonl new-work.jsonl               # after an upstream string update
```

- `extract` keeps each string's key, context, plural and placeholders.
- `match` reuses a translation only for the **same source text** under the rules below ("Reuse rules"). The entry
  records `match: {type: "exact", reason, from, review, provenance}`; a translation reused from another application
  is marked `corsu-draft`. Close texts (difflib ratio ≥ 0.85) are recorded as `suggestion`s and never applied.
  Different translations of the same text in different applications are recorded as a `conflict` with one option
  per meaning. It also compares each string with what the memory already holds for its application: `change:
  "added"` (new key) or `"changed"` (same key, other source text or `source_hash`: the earlier text and translation
  go to `match.previous`, never applied, and the entry is `to-review`).
- `stats` prints unique source strings, exact compatible reuses, suggestions, conflicts, strings held (abbreviation
  or unknown sense), strings with a refused candidate (other sense), added and changed strings, and untranslated ones.
- `update` marks each new entry `added`, `changed` (the source text, or its `source_hash`, changed: previous
  translation kept for reference, `review: "to-review"`, written `#, fuzzy` by `po`, a speaker's validation turned
  into `to-re-examine`) or `unchanged` (translation, review and validation kept), and appends `removed` ones.
- `po` writes `msgctxt` (or the Android/XLIFF key when there is no msgctxt, so equal texts stay apart),
  `msgid_plural`/`msgstr[n]` with Corsican's `nplurals=2; plural=(n != 1)`, and the `#.`/`#:` comments.

## Reuse rules

A translation fills a string by itself (`match.type: "exact"`) only when all of these hold:

1. **Same source text** (normalised) and the same placeholders, singular with singular, plural with plural.
2. **Not kept for its own application** (`reuse: "same-app"`), unless the string is of that application.
3. **No other sense**: when the string names its `sense`, a candidate written for another sense is never used; it is
   listed under `match.refused` (`reason: "other-sense"`).
4. And one of, in this order: the **same application** (`same-app`, its review status kept); the **same context**
   (msgctxt, file, section: `same-context`); the **same named sense** (`same-sense`); or a **single translation**
   across the memory (`unambiguous`), except for an **abbreviation** (`abbreviations.tsv`, or up to five letters and
   a period) and except when the string names a sense that no candidate states (`sense-unknown`).

Everything else stays for a person: one `suggestion` per application for a held text (`reason: "abbreviation"` or
`"sense-unknown"`), a `conflict` with one option per meaning (and the applications and senses of each), close texts
as suggestions. Reused from another application, a translation is `corsu-draft` whatever its status there: an AI
review stays an AI review, and a speaker's validation belongs to its own application and source text
(`match.provenance` says where it came from: application, key, origin, version, license, review, human validation).
`engine.lookup(text, app, context, sense=…)` follows the same rules.

Real cases, as tests (`tests/test_tm_cases.py`, run on the real `lexicon.tsv`, VLC catalog and Minecraft data):

| Case | What happens |
|---|---|
| "Bio": Discord's correction *Biugrafia* (profile) and Chrome's *Organicu* (image style) | reused as *Biugrafia* for a new Discord string and *Organicu* for Chrome (`same-app`); a third program gets both as a `conflict`, nothing applied. With only Chrome's row in the memory (as before the Discord fix), the previous rule gave Discord *Organicu* (`unambiguous`); now it is a suggestion held as an abbreviation |
| "Bio" with senses written (`biography`, `organic (image style)`) | a new program's "Bio" for a biography takes *Biugrafia* (`same-sense`), *Organicu* is listed as refused |
| "Profil" / VLC's "Force Profile" (French "Profil") | a French "Profil" elsewhere gets VLC's *Prufilu* (its "Profile"), never *Forzà un Prufilu*: abbreviated imported French is not a source |
| Minecraft `key.drop`: "Drop Item" (1.7.2–1.8.9) became "Drop Selected Item" (1.9–26.3) | `update` and `match` mark it `changed`, `to-review`; *Lampà l'ogettu* stays as the previous translation only; a speaker's validation of the old text becomes `to-re-examine` |

Limits: a PO string whose msgid changed has a new key (msgctxt + msgid), so it shows as `added`, with the old text as
a close suggestion when it is similar enough. Senses are only as good as what is written: most entries have none, and
then only the application and context protect them. The abbreviation list is short and written by hand.

## Refreshing

```sh
GITHUB_TOKEN=... python3 tools/import_translations.py      # network; every repository read at its current commit
python3 tools/import_translations.py --corsu-only          # offline; re-exports lexicon.tsv's sections only
```
