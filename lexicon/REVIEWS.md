# Reviews of the lexicon: what was checked, how, and by whom

Three kinds of checks exist and are never counted as one another:

- **automatic detection**: a script flags rows by a rule (for example `engine.loose_french`);
- **AI review**: a language model reads rows and proposes corrections; it can find mistakes, but it is not a
  validation, and an AI checking an AI's translation is not independent;
- **human validation**: a Corsican speaker confirms or corrects. None of the changes below has been through it yet.

Every change is logged in [corrections.tsv](corrections.tsv) with its status.

## 2026-10-18 — wording and fit of the most common labels: Corsu's window, Discord, Firefox (AI review)

Scope: the window's main texts (src/app/texts.js, about 140 Corsican strings), Discord's most visible paths (message
box, server and channel menus, user settings top level, call buttons, notification settings, close and quit: 166
labels from its public web client, October 2026) and Firefox's main menu, tab context menu, downloads and new tab
(415 labels from Firefox 157 and its French pack). Each label was read for its sense, its function (action, title,
state, question) and its neighbours, against Mozilla's Corsican (lexicon-mozilla.tsv), upstream programs
(lexicon-upstream.tsv) and VLC (contrib/vlc/co.po). No dictionary was queried. The sensitive changes were re-read by a
separate AI agent from the corpora: an AI second opinion, not a validation. Changes and proposals are logged in
corrections.tsv (window, Firefox) and review-discord-2026-10.tsv (Discord).

Applied: "Rilege" → "Rileghje" (misspelling); the window's "{job} compia." which did not agree with masculine jobs
(French had the same bug); Firefox's "Créer un nouveau profil" and "Modifier le profil" taken from another program's
"Save as new profile" and "Profile edition"; "Vue détaillée", "Minimale", "messageria"; the tab context menu and the
synced-tabs panel aligned on Mozilla's own verbs and "apparechju" (they mixed two vocabularies); Discord's "Suppress
Highlights" said "erase". Rejected after the second reading: a global "Supprimer" → "Squassà" (it also means Remove)
and "Tuttu marcà cum'è lettu" → "Marcà tuttu…" (Mozilla's own pattern "Tuttu selezziunà"). Most labels examined were
right, or differed only by legitimate variants (Ammutulisce as Mozilla's -isce infinitives, Espertu, Discunnette,
tastera/tastiera), left as they are.

## 2026-10-17 — Firefox main menu, Settings, downloads and tabs, read in the running copy (automatic detection, AI proposals)

Method: Corsu's Firefox 157 built in a throwaway home, started headless, and its labels read through Marionette (app
menu and its sub-views, Settings > General, downloads panel and about:downloads, tab context menu, list of all tabs,
Firefox View), then compared with Firefox's English and French text; every built message was also compared with the
French pack. Found in French: the browser tools of the main menu (`menus.properties`), the downloads panel's states,
warnings and dialogs (`downloads.properties`, `unknownContentType.properties`). Causes: 31 French labels had no row
(added at the end of the Firefox section of `lexicon.tsv`, new proposals written by an AI, to review), and the engine
did not read Mozilla's `%S` and `%1$S` arguments as placeholders, so rows such as `Fichier %1` never matched
`Fichier %S` (50 more labels translated across Firefox once fixed). "Onglets ouverts", a heading, showed the button
"Apre l’unghjette" from an imported Android row; corrected in `lexicon-fixes.tsv` (logged in corrections.tsv).
Not changed: dates and times follow the copy's `en-US` locale (`11:32 AM` in the downloads list).

## 2026-10-16 — imported French that answered a longer English label (automatic detection)

`tools/import_translations.py` pairs each project's English, French and Corsican by message id. Some French
translations shorten their English: VLC's "Force Profile" is just "Profil", so every French "Profil" (Discord,
Firefox…) became "Forzà un Prufilu". Rule: in the imported files only, a French text of at most 3 words that is shorter
than its English while the Corsican is at least 2 words longer is no longer used as a source (`engine.loose_french`).
89 French labels changed; [imported-french-audit.tsv](imported-french-audit.tsv) gives each one's fate: 18 wrong
senses corrected, 18 replaced by another reviewed translation, 15 faithful ones kept by hand, 26 new AI proposals,
12 left untranslated (French shows).

The same release also stops a label written for one application from being replaced by the same label taken from
another program: Discord and Google now see corrections first, then their own rows, then the rest
(`engine.application_words`). 55 Discord labels changed this way, 6 of which were then corrected in
`lexicon-fixes.tsv`. The Inno Setup import leaves out short labels translated much longer ("Setup" →
"Assistente d'installazione"), which would have replaced the general French word "Installation".

Still open: [ambiguous-sources.tsv](ambiguous-sources.tsv) lists 1,172 short labels that have several Corsican
translations across programs, where the one in use comes from an imported program. They are a review queue, not
errors.

## 2026-10-16 — Discord short labels (AI review)

Scope: the 9,942 rows of the Discord section of `lexicon.tsv` whose French (or English) has 1 to 5 words and no
placeholder. Not covered: longer sentences, labels with placeholders, the Vencord section.

Method: two AI passes, each over half of the rows, looking for wrong sense, verb/noun role on buttons, calques,
agreement, terminology against the project's choices, untranslated text. Each flag has a confidence. Rows marked high
or medium (110) were applied if the row was unchanged; the 64 low-confidence suggestions are logged, not applied.

## 2026-10-16 — three variant families (AI review, by meaning)

`almacenamentu`/`allucamentu`, `scurciatoghja`/`accurtatoghju`, `scandagliu`/`sundaghju`: rows grouped by the concept
they translate, evidence searched in the reviewed Mozilla and Patriccollu translations and the local resources.
337 rows changed; method, evidence and the cases left for a speaker are in [variants.md](variants.md).
