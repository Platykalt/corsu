# Reviews of the lexicon: what was checked, how, and by whom

Three kinds of checks exist and are never counted as one another:

- **automatic detection**: a script flags rows by a rule (for example `engine.loose_french`);
- **AI review**: a language model reads rows and proposes corrections; it can find mistakes, but it is not a
  validation, and an AI checking an AI's translation is not independent;
- **human validation**: a Corsican speaker confirms or corrects. None of the changes below has been through it yet.

Every change is logged in [corrections.tsv](corrections.tsv) with its status.

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
