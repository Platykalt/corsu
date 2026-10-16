# Corsu web: Corsican interface labels on selected websites

Status: prototype, 2026-10-16. Code in `src/webext/`. Tests in `tests/test_webext.py` and `src/webext/test/`.

## 1. How Firefox Corsu translates Google today

`src/firefox/CorsuChild.sys.mjs` is loaded into every Google page by `corsu.cfg` (a process script that
matches the host against `GOOGLE_DOMAINS`, the `HOSTS` list that `google_labels()` writes in). Its dictionary,
`dictionary.mjs`, is built by `google_modules()` from two sources: the labels listed in `google-labels.txt`
that have a lexicon row, plus every row of the `# Google:` section of `lexicon.tsv` (read by
`lexicon_section()`, with both English and French keys and their placeholder skeletons).

The decision rules:

| Rule | What it does |
|---|---|
| Protected elements | `script, style, pre, code, textarea, [contenteditable], [data-corsu-ignore]` are never touched. |
| UI zone `*` | **Every** text node outside those is a candidate. Its only filter is that the text must be a dictionary label. |
| Results area `#search,#rso,#botstuff` | Only the fixed `resultLabels` set and the number `patterns` change there, never inside `<a>`. |
| Length | `translateLabel` skips any text over 100 characters. |
| Matching | Exact key, then `{…}`/`%s` placeholder skeleton, then trailing punctuation (`…`, `:`, `?`), then the other letter case, then segments split on `: — / · |`. Every segment must be known. |
| Number patterns | Google-only regexes ("About N results", "N degrees Celsius", ratings, "Opens in a new tab"). |
| Attributes | `aria-label`, `title` and `placeholder` on **every** element outside the results. |
| Timing | A synchronous `MutationObserver` on the whole document, so no English flashes before paint. |
| Original text | Optional bubble on hover (`corsu.showOriginal` pref), found through a WeakMap of changed text nodes. |

**Google-specific parts:** the `*` UI zone, the results selectors, `resultLabels`, the regex `patterns`, the
French/English pairs (Google already has a partial Corsican UI that falls back to French), and the host list.
The `*` zone is safe on Google because the search results are fenced off and almost all the rest is chrome.

**Why the rules cannot be reused as they are.** On a site full of user content, "short and in the dictionary"
does not mean "interface":

- a README heading `Documentation`, an issue label `docs`, a branch called `Code`, a user named `Open`,
  a video called `Settings`, a commit message `Fix`;
- `title` attributes on GitHub mostly carry **file names** (`title="README.md"`), and topic tags (`title="Topic: ai"`);
- the case and segment fallbacks multiply matches (`Code` → `code`, `Security: policy` → two labels);
- translating `aria-label` can break things: our zone selectors use
  `nav[aria-label="Repository"]`, and the site's own CSS or scripts may too (found while testing, see §4);
- the whole-lexicon dictionary (≈119 000 rows) would match random words in content.

So the extension goes the other way: nothing is translated unless an adapter says where the interface is.

## 2. Design

A Manifest V3 WebExtension, the same files for Firefox and Chromium.

```
src/webext/
  manifest.json            MV3; permissions: storage; host_permissions: https://github.com/* only
  background.js            serves glossary JSON to the content script; relays the keyboard toggle
  content.js               bootstrap: settings, adapter choice, MutationObserver, toggle
  core/engine.js           pure logic: glossary lookup, zones, attributes, batching, revert
  adapters/github.js       the pilot adapter
  glossary/github.json     site glossary (101 entries + 3 contextual exceptions)
  glossary/shared.json     generated: 52 generic labels (tools/build_shared.py)
  glossary/shared-labels.txt  curated list shared.json is generated from
  options/                 per-site switches, original-text mode
  test/                    Node tests + a fake DOM
```

**Adapters** (`adapters/<site>.js`) declare, as data:

- `hosts` (exact host names) and `matches` (manifest patterns);
- `ui`: CSS selectors of interface zones (header, `nav[aria-label]`, footer, buttons, menus, tabs,
  headings of type `data-component="Heading"`, table heads). No catch-all `*`;
- `never`: user content — README/comment bodies (`.markdown-body`), issue titles, file and folder names,
  commit messages, user/repo names (`[data-hovercard-type]`), label and topic names, code views.
  Built-in for every site: `script, style, textarea, input, select, pre, code, kbd, [contenteditable],
  [role="textbox"], [translate="no"], [data-corsu-ignore]`;
- `uiInsideNever`: interface widgets the site nests inside user content (GitHub's copy button in READMEs);
- `attributes`: `aria-label`, `title`; `placeholder` only on `searchFields` (search inputs).

`never` always wins over `ui`, except for an `uiInsideNever` widget nested inside the never zone.

**Glossaries**: the site glossary is looked up first, then `shared.json`. An entry is
`{source, co, status, origin, within?, note?}`: `within` restricts it to a context (`Code` only in the
repository nav and buttons); `exceptions` give another form in a context (`Open` is `Aperti` as an issue
filter, `Apertu` on a single issue's state icon) or `skip`. Placeholders: `{n}` matches a number
(`1,204`, `68.2k`), any other `{name}` matches any text and is copied unchanged (`Filter by label {label}`).
Matching is exact after whitespace/apostrophe normalisation; the only fallback is a final `…`, `...` or `:`.
No case folding, no segment splitting, 120 characters at most.

**Runtime**: a first pass at `document_idle`, then a `MutationObserver` (child list, character data, the
translated attributes) whose records are batched into one `requestIdleCallback` (timeout 150 ms). A `WeakSet`
marks processed nodes; the engine recognises its own writes and does not re-queue them; a site re-render of a
label is translated again. Attribute values that any selector depends on (`nav[aria-label="Repository"]`)
are pinned and never translated.

**Original text**: in `tooltip` mode (default) the element of a translated label gets a `title` with the
original, only when it has none (marked `data-corsu-title`, removed on revert). `Alt+Shift+O` (manifest
`commands`) toggles the whole page between the site's text and Corsican. Switching a site off in the options
page reverts the open tabs at once.

**Privacy**: no remote translation, no analytics. Permissions: `storage` and the pilot host only; settings in
`storage.local` (not `storage.sync`). The glossary is read by the background script from the package, so no
`web_accessible_resources` are exposed to pages. Firefox manifest declares
`data_collection_permissions: {required: ["none"]}`.

**Firefox vs Chromium MV3**: `background` lists both `service_worker` (Chromium) and `scripts` (Firefox,
which runs MV3 backgrounds as event pages; Chromium 121+ ignores `scripts` with a warning, Firefox 121+ ignores
`service_worker`). Firefox needs `browser_specific_settings.gecko.id` for signing; `strict_min_version` is 140
(first ESR that knows `data_collection_permissions`). In Firefox MV3, host permissions are shown at install but
the user can withdraw them in about:addons; the content script then simply does not run. Both browsers accept
`chrome.*` with promises in MV3; the code uses `browser ?? chrome`. Content scripts are classic scripts (no ES
modules), so `engine.js` and adapters register on `globalThis.CorsuWeb` and also export for Node.

## 3. Pilot site: GitHub

Pages fetched without login on 2026-10-16: a repository (`torvalds/linux`, `Platykalt/corsu`), a file view,
the issue and pull request lists of `python/cpython`, and `/explore`.

| | GitHub | YouTube | Steam |
|---|---|---|---|
| Corsican offered by the site | no (English-only UI) | no (`?hl=co` falls back to `fr-FR`) | no (29 languages, no Corsican) |
| Interface in served HTML | yes, server-rendered React with ARIA | no, built by JS from `ytInitialData`, custom elements | partly, few ARIA labels |
| Stable hooks | `nav[aria-label]`, `role`, `data-testid`, `data-component` | custom element names, frequent changes | legacy class names |
| Source language | always English | user's language (fr) | user's language |
| Separation UI / user content | clear (`.markdown-body`, hovercards, label classes) | mixed (titles, channel names everywhere) | mixed (game names, reviews) |

GitHub was chosen: one source language, inspectable HTML, stable ARIA/test hooks and a clear boundary
around user content. Its CSS-module classes carry hashes (`sidebarSection__oqw6Y8`), so the adapter only
matches their stable prefix (`[class*="sidebarSection"]`).

Glossary: `github.json` has 101 entries: 11 `reviewed` (exact rows of lexicon-mozilla/upstream, e.g.
Issues → Prublemi, Actions → Azzioni, Changelog), 5 `draft` (rows of `lexicon.tsv`), 85 `proposal` (new,
built from reviewed terms: *dipositu* for repository, *fusione* for merge, *liame*, *listinu* for menu,
*preme'papei*, *canistrelli* for cookies, *Affissà*, *Allargà/Riduce*). "commit" is kept as the git term.
Proposals need a speaker's review before any release. `shared.json` holds 52 generic labels (47 reviewed, 5 draft).

## 4. What works, and how it was tested

- `node --test src/webext/test/engine.test.js` (Node 26, 13 tests, all pass) on a fake DOM
  (`test/fake-dom.js`, a CSS selector subset): exact/placeholder matching; nothing guessed (case, partial,
  long, digits); `within` contexts; interface vs user content (README heading, label names, user names,
  `pre/code`, contenteditable, file names in the file table); attributes (aria-label, title; placeholder
  only on search fields; values never touched); pinned attribute values; contextual exceptions;
  `uiInsideNever`; batching (one idle callback per burst), own writes ignored, site re-renders
  re-translated; tooltip and revert; host matching; selectors parseable.
- `python3 -m unittest tests.test_webext` (10 tests): manifest (MV3, only `storage` + https host patterns,
  no web-accessible resources, files exist, adapters' hosts in the manifest), every glossary entry keeps its
  placeholders, statuses and origins, no duplicates, 60–120 site entries, `shared.json` up to date with the
  lexicon (`build_shared.py --check`), adapters declare `ui` and at least 5 `never` zones and no `*`/`body`
  zone, and the Node tests (skipped when `node` is missing).
- Smoke run (not committed, pages are not stored in the repo): the six fetched pages, parsed with Python's
  `html.parser` into the fake DOM and run through the engine: 40–102 distinct labels changed per page
  (navigation, footer, sidebar headings, file table head, issue filters, `Filter by label {label}`,
  `Page {n}`, `{n} comments`, search placeholders), 0 changes inside `never` zones; README headings,
  label names, file names and user names unchanged.

Bug found and fixed by the tests: translating the nav's `aria-label="Repository"` removed the zone that
the adapter selects on (and that the site's own CSS or scripts may use). Such values are now pinned.

## 5. Not done

- Not loaded in a real browser yet: the run in Firefox/Chromium (timing, flashes, GitHub's client-side
  navigation, the logged-in header and menus in `#__primerPortalRoot__`) is untested.
- Not packaged or signed, and not installed by Corsu. Firefox release builds need AMO signing (listed or
  unlisted; `web-ext lint` / `web-ext sign`); until then: `about:debugging` → *Load Temporary Add-on* →
  `src/webext/manifest.json`. Chromium: `chrome://extensions` → Developer mode → *Load unpacked* →
  `src/webext`.
- No icons, no localisation of the options page beyond Corsican/English text.
- Google is not ported as an adapter; Firefox Corsu keeps doing Google through `CorsuChild.sys.mjs`.
- Logged-in pages (dashboard, settings, notifications, PR review) were not inspected; their labels are
  missing from the glossary.
- 85 proposals await review.

## 6. Next steps

1. Load unpacked in Firefox and Chromium, check the logged-in UI and Turbo/React navigation, adjust
   `ui`/`never` from what is seen; add a CI check that fetches a few public pages and fails when a
   `never` zone disappears (GitHub markup drift).
2. Review the proposals with a speaker; move the confirmed ones to a `# GitHub:` section of `lexicon.tsv` and
   generate `github.json` from it, as `google_modules()` does for Google.
3. Port Google as a second adapter (`ui: ["*"]`, `never` = results, the regex patterns as glossary
   templates), so one engine serves both.
4. Package with `web-ext build`, sign on AMO, and let the Corsu app offer the extension.
5. Then add a second site only through a new adapter + glossary, with the same tests.
