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
- `match` reuses a translation only for the **same source text** and (same application, or same context, or a
  single unambiguous translation across the memory), with matching placeholders. The entry records
  `match: {type: "exact", reason, from, review}`; a translation reused from another application is marked
  `corsu-draft`. Close texts (difflib ratio ≥ 0.85) are recorded as `suggestion`s and never applied. Different
  translations of the same text in different applications are recorded as a `conflict` with one option per meaning.
- `stats` prints unique source strings, exact compatible reuses, suggestions, conflicts and untranslated strings.
- `update` marks each new entry `added`, `changed` (the source text changed: previous translation kept for
  reference, `review: "to-review"`, written `#, fuzzy` by `po`) or `unchanged`, and appends `removed` ones.
- `po` writes `msgctxt` (or the Android/XLIFF key when there is no msgctxt, so equal texts stay apart),
  `msgid_plural`/`msgstr[n]` with Corsican's `nplurals=2; plural=(n != 1)`, and the `#.`/`#:` comments.

## Refreshing

```sh
GITHUB_TOKEN=... python3 tools/import_translations.py      # network; every repository read at its current commit
python3 tools/import_translations.py --corsu-only          # offline; re-exports lexicon.tsv's sections only
```
