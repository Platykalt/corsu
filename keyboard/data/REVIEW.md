# Keyboard vocabulary: audit and review

Automated work by an AI agent (2026-10-18). **No human has reviewed these lists.** Nothing here is a speaker's
validation; "attested" only means that an external source writes the word that way.

Files:

| File | Content |
|---|---|
| `shared.tsv` | The base list: 19,228 entries, both varieties' forms included (447 Corsican place names, 221 words of official commune names, 12 lowercase common words next to a name, 3 acronyms, and 6,012 known forms added on 2026-10-19: see "Forms auto-correction replaced" and "Second pass"). |
| `held-back.tsv` | 324 forms the first count of 2026-10-19 took from Vikipedia and Corsican prose does not attest enough: not shipped, each with its counts, class and passages (see "Second pass"). |
| `cismuntincu.tsv` | 354 rows laid over `shared.tsv` for a northern preference. |
| `pumuntincu.tsv` | 357 rows laid over `shared.tsv` for a southern preference. |
| `sources/` | Hand-checked inputs: `daily.tsv` (everyday words, editorial choice), `adecec.tsv`, `cunghjugarellu.tsv`, `variant-pairs.tsv`; `places.tsv`, the Corsican place labels of Wikidata; `communes-official.tsv`, the official (INSEE) commune names; `place-titles.tsv` (Vizzani), `homographs.tsv` (corti) and `acronyms.tsv` (ADECEC), see "Auto-correction"; `forms.tsv`, forms a reference work writes in full (ghjocanu), see "Second pass". |
| `tools/make_vocab.py` | Rebuilds the three lists from the sources (needs the resources of `tools/fetch_resources.py`). |
| `tools/fetch_places.py` | Runs the three Wikidata queries that write `sources/places.tsv`. |
| `tools/fetch_communes.py` | Two requests to geo.api.gouv.fr that write `sources/communes-official.tsv`. |
| `tools/simulate.py` | Top-3 suggestion simulation and checks (also run by `tests/test_keyboard_vocab.py`). |
| `audit/removed.tsv` | Every word of the old list that was dropped, with its reason. |
| `audit/stats.json` | The numbers quoted below. |
| `audit/commune-titles.tsv` | Communes whose Vikipedia title differs from the Wikidata label: candidates, not checked. |

## Reading the files (for the build)

Columns: `word	weight	variant	source	license	status`, UTF-8, tab-separated, one header line.

- **Merging a variety**: take `shared.tsv`, then lay the variety's file over it. When a word is in both, the
  variety's weight replaces the shared one. Words absent from the variety's file keep their shared weight.
- In a variety's file, `variant` says which variety the *form* belongs to: `pumuntincu.tsv` holds the southern forms
  (raised) and the northern counterparts it lowers (`variant` = `cismuntincu`, a quarter of the pair's weight).
  Nothing is deleted: the other variety's words stay suggestible.
- `shared.tsv` alone (no preference) has both forms of each pair, the variety-specific ones at half the pair's weight.
- Words keep their case: lowercase common words, capitalised names (Corsica, Aiacciu, Bastia, Spagna). Apostrophes are
  the ASCII `'` (U+0027); `’` was converted.
- Elided forms are single entries (`nant'à`, `cum'è`, `l'annu`, `ch'è`; 1,705 in `shared.tsv`), because Keyman's
  default word breaker (Unicode word boundaries) does not split a word at an apostrophe between two letters. If the
  build uses a word breaker that splits at the apostrophe, these entries become useless and could be dropped.

### Weight scale

`weight` ≈ occurrences per 10 million words, so weights of different sources can be compared:

1. Vikipedia frequency (botanical stub articles excluded): `count × 10,000,000 / 1,327,560` tokens.
2. Plus 2 % of the Corsu-lexicon frequency on the same scale (1,010,763 tokens). Interface strings repeat "fichier",
   "paramètres", "erreur" thousands of times; this share keeps those words known without letting them outrank
   everyday words.
3. Minimum weights (editorial, an AI choice): daily words of `sources/daily.tsv` tier 1 → 20,000, tier 2 → 5,000,
   tier 3 → 1,000; words of the Tatoeba sentences → 2,000; variety pairs with a tier → the same floors.
4. Place names (Wikidata): their Vikipedia frequency, at least 50 and at most 900 (below the lowest everyday floor).
5. Variety files: the variety's own form gets the pair's weight (the highest weight of the pair's forms, at least
   1,000 or its tier floor); the other variety's form gets 25 % of it, unless the pair says `lower_other = no`.
6. Forms added to be known (steps 5b-5e, "Second pass"): their Vikipedia prose frequency, at most 100, and below every
   other word in the top 3 of each prefix of their search key.

Range: 1 to 715,753 (*di*); median 23; 979 words at 1,000 or more.

### Status

- `attested`: the word is written so in at least one external source. The `source` column cites, in this order:
  wiktionary, tatoeba, vikipedia ≥ 5 occurrences, apertium, then the reference works consulted without a reuse
  licence, cunghjugarellu and adecec, when they are the only ones (place names: wikidata). A variety-specific form
  cites the reference of its pair when no dictionary has it. The order changes no weight; every form checked in
  a reference work stays listed in `sources/`.
- `corsu-lexicon`: only Corsu's own software lexicon has it (6,640 words). This includes words from the Mozilla and
  Patriccollu imports: their file of origin does not make them attested here.
- `ai-proposal`: 11 everyday words found in no source (listed below).

## Audit of the old list

The old list (`keyboard/platykalt.co.corsu/source/wordlist.tsv`, 16,949 words) was generated at version 0.9.0 by
`tools/build_keyboard.py` from the lexicon only:

- **Stale**: it was never regenerated after the lexicon corrections of `lexicon/variants.md`, and still had
  *almacenamentu*, *scurciatoghja*, *accurtatoia*, *ditagli*…
- **"Reviewed" by file of origin**: rows of `lexicon-mozilla.tsv` and `lexicon-upstream.tsv` counted three times, and
  a word seen once there was kept. 3,134 words were kept only by that rule or by two occurrences.
- **Software frequencies**: *schedariu* (file) had 6,153, more than *più*; *impussibule* 5,213, *affissà* 3,257,
  *cartulare* 2,157. *casa*, *grazie*, *bonghjornu*, *aghju*, *mamma*, *dumane* were absent or far behind.
- **Everything lowercased**: *corsica*; *Bastia* and *Aiacciu* missing.
- **Not Corsican**: English words and program names left in the translations (*google*, *firefox*, *audio*, *data*,
  *the*, *of*), format tokens (*yyyy*, *ycbcr*, *ctrl*, *mm*), French spellings (*entrée*, *vérificà*).

### Filtering rules (applied to the old list and to every new candidate)

| Rule | Removed | Examples |
|---|---|---|
| **foreign-or-name**: in the program-name list (Google, Windows, Linux, Firefox, Chrome, Discord, KDE, Plasma, Wi-Fi, Bluetooth, git…), a web/markup token (http, www, html, jpg, url, isbn…), or written at least half as often in the English source strings as in the Corsican ones, and absent from Wiktionary, Apertium, Tatoeba, ADECEC and the daily list | 1,291 | audio (754), data (598), firefox (430), audacity, mozilla, db, alt, media, the, of, and |
| **non-corsican-letters**: a character outside a–z, à è ì ò ù and the apostrophe (other scripts such as Japanese ディスコード, Greek, Cyrillic; ç, ñ, ö…), or k, w, x, y, or a j not in *chj/ghj* — unless Wiktionary has the word as Corsican | 842 | web (1,221), cookies, krita, proxy, pixel, widget, javascript, json, kernel, ycbcr, yyyy |
| **non-corsican-spelling**: an acute accent (Corsican spelling writes grave accents) | 14 | entrée, bézier, vérificà, moiré, periféricu, échap |
| **fragment**: no vowel; five consonants in a row (*ghj* and *chj* count as one, so *aghjunghje*, *inghjò* pass); one letter three times; or one or two letters found in no source | 225 | ctrl (341), mm, ms, qt, ssh, dll, src, dirmngr, ip, ui, tà |
| **gone-from-lexicon**: no longer in the lexicon (corrected since) and in no source | 29 | ditagli, d'almacenamentu, scurciatoghja, accurtatoia |
| **unattested-rare**: fewer than 3 occurrences in the lexicon (all files counted alike) and in no external source | 2,874 | maius, almacenamentu, discunnittitevi, alonghezza, nonstampevule |
| **corpus-name**: a capitalised name known only from Vikipedia or Tatoeba (not a Corsican Wiktionary entry, not a Corsican lexicon word) | 100 | sun, steve, research, foundation, david, Tom (Tatoeba) |

Total removed: **5,375** of 16,949 (`audit/removed.tsv`). Kept: 11,574; added from outside the old list: 955 (daily
words, conjugations, ADECEC words, Vikipedia words with ≥ 30 occurrences that Wiktionary, Apertium or the lexicon
also has). **After: 12,530 words** in `shared.tsv` — 5,879 attested, 6,640 corsu-lexicon, 11 ai-proposal; then
446 place names and 221 words of official commune names (below), then the additions of "Auto-correction" below: **13,213 entries**, 6,562 attested (19,550 since the forms added on 2026-10-19, see "Forms auto-correction replaced"). The audit reads the old list from git (commit 66e7f58,
version 0.9.0), because `tools/build_keyboard.py` now rewrites `wordlist.tsv` from these lists; place names that the
old list had and the corpus-name rule dropped (*ghjuvanni*, *oriente*, *riparata*, *sichè*, *oga*) are no longer
counted as removed.

The `unattested-rare` rule is deliberately strict: it also drops real but rare words (*infelice*, *fidanza*,
*contestu*). They are only missing from suggestions, not marked wrong, and come back when a source attests them.

## Effect of the weights (simulation)

`python3 keyboard/data/tools/simulate.py` ranks the words that start with a prefix (case and accents folded as in
Keyman's default search key; no typo correction, no context). It is a rough model of Keyman, not Keyman.

- 37 shared checks (an everyday word expected in the top 3 for its prefix) plus 9 northern and 10 southern ones:
  **old list 26 of the 37 shared checks fail; new lists 0 failures**. Old examples: *sc* → schedariu, schedarii, screnu (no *scusate*); *ca* → cartulare, carta, cambià (no
  *casa*); *cun* → cunnessione, cunfigurazione, cuntenutu (no *cuntentu*); *gr* → gruppu, grafia, gruppi; *bo* →
  bordu, bordi, bona. New: *sc* → scusa, scusate, scrittu; *ca* → caffè, casa, Calvi; *cun* → cuntenta, cuntentu,
  cuntenti; *gr* → grazie, grande, grandi.
- `--scan`: two-letter prefixes with a software term in the top 3: **old 24 of 481, new 6 of 249** (af: affissà,
  im: impussibule, oz: ozzioni, sb: sbagliu, sq: squassà, st: statu — *statu* is also "state/been").
- Some checks pass on ties (in the variety files *induve*/*induva* and *innò* all weigh 20,000; ties sort
  alphabetically here, and Keyman may order them differently).

## Place names

Auto-correction (Keyman 19, and setting 3 of Keyman 18) replaces a word the model does not know when one close
candidate is much likelier: *Zicavu* once became *Cavu*. A word the model knows is kept as typed. The names of
Corsica's places are therefore in the list, from **Wikidata** (CC0): `tools/fetch_places.py` asks the official query
service three targeted questions (the 360 communes with a Corsican label, of 361; places located in Corsica of the
kinds pieve, natural region, department, mountain, pass, river, lake, island, cape; rivers whose French description
says Corsica) and writes `sources/places.tsv` (548 items). Only the label in Corsican (`co`) is used: the aliases mix
French and Italian spellings.

`make_vocab.py` takes from each label its capitalised words of three letters or more (*Sari è Sulinzara*: Sari,
Sulinzara; *A Munacia d'Orezza*: Munacia, Orezza; a bracketed disambiguation such as "(pieve)" is dropped):

| | Words |
|---|---|
| Added with their capital (*Zicavu*, *Bastilicaccia*, *Ghisunaccia*, *Golu*, *Cintu*, *Nebbiu*, *Cismonte*) | 429 |
| Added in lowercase: Vikipedia writes them mostly in lowercase mid-sentence, so they are also common words (*vescuvatu*, *stazzona*, *valle*, *foce*, *fangu*) | 17 |
| Left to a word already in the list, same search key (*Aiacciu*, *Bastia*, *Corti*, *Sartè*, *Calvi*, *piana*, *lama*, *monte*) | 98 |
| Of the 446 added, seen at least once in the Vikipedia dump (cross-check) | 437 |

Not seen in Vikipedia: *Fughjuchja*, *Pioghjola*, *Figaniedda*, *Speloncatu*, *Ventisari*, *Oga*, *Vegnu*, *Vezzu*,
*Infora* (kept: Wikidata is the source; a speaker should confirm them).

Weight: the Vikipedia frequency, at least 50 (Keyman must know the name) and at most 900, just below the lowest
everyday floor (1,000): an encyclopedia names places far more often than messages do. Names already in the list keep
their weight (*Aiacciu* and *Bastia* 20,000, *Bunifaziu*, *Corti*, *Portivechju* 5,000). Effect on the top 3 of the
simulation: two-letter prefixes with a place name in the top 3: 9 of 249 (az, bu, go, os, up, za, ze, zo, zu, where
few common words start); words of weight ≥ 200 pushed out of a three-letter top 3: *luce* (*luc*: Lucciana),
*originale* (*ori*: Oriente), *russu* (*rus*: Rustinu), *vale* (*val*: valle); four letters: *bastiacciu* (Bastelica).

Seen in the Keyman engine (18.0.254 and 19.0.309 beta, `tests/e2e/check_keyboard.py`, scenarios "places"): *Zicavu,
Aiacciu, Bastia, Portivechju, Corti, Calvi, Bunifaziu, Sartè, Bastilicaccia* typed then space with auto-correction on
stay as typed in the three models, and a lowercase prefix (*zicav*, *portiv*, *bunif*…) offers the name with its
capital first. At that time *Bastelicaccia* (the official spelling) was corrected to *Bastilicaccia*, the Wikidata
Corsican label, because only the latter was in the list; the official names below fix that (to be seen again in the
engine).

### Official names next to the Corsican ones

Rule: a legitimate spelling typed on purpose is kept; the Corsican form may be proposed, never forced. An unknown
name is not a typo. *Bastelicaccia* is the official name of commune 2A032 (INSEE Code officiel géographique);
*Bastilicaccia* is its Corsican name (Wikidata label, title of the Vikipedia article, 5 occurrences in Vikipedia
against 2 for *Bastelicaccia*). Neither makes the other wrong: a Wikidata label is one source among others.

`sources/communes-official.tsv` holds the 360 official names (INSEE, through geo.api.gouv.fr, Licence Ouverte 2.0).
`make_vocab.py` splits them like the Corsican labels and adds the 221 words whose search key the list does not
already have (*Bastelicaccia*, *Zicavo*, *Ajaccio*, *Bonifacio*, *Sartène*, *Propriano*, *Porto*, *Vecchio*,
*Saint*, *Rousse*…), with their capital, at their Vikipedia frequency between 20 and 50 (`OFFICIAL_FLOOR`,
`OFFICIAL_CAP` = the Corsican names' floor): known, so kept as typed, but never above a Corsican place name or an
everyday word. 167 words were already known (*Calvi*, *Bastia*, *Corte*, *Vezzani*…). The Corsican spelling checks
do not apply to them (*Ajaccio* has a *j*, *Zévaco* an acute accent: that is how INSEE writes them). Keyman's word
breaker splits at hyphens, so *Porto-Vecchio* is two words, *Porto* and *Vecchio*.

Measured with `simulate.py`'s ranking on every 1-4 letter prefix (4,962 prefixes; same result in the three models):
196 prefixes get a different top 3, and 19 lose a word, none above weight 20: *dammi* (8; *dam*: Damiano),
*tasse* (20, tie; *tass*: Tasso), *lore* (*lor*: Lorenzo, Loreto), *alarma* (*ala*: Alando), *cogito*, *gio*,
*lucidezza*, *repo*, *flottanti*, *felicitazioni*, *isolata*, *lavatura*, *pioggie*, *cianu*, *ciambuttà*,
*corruption*, *arrotundata*, *sarrimanenti*. A first version weighed them by their Vikipedia frequency up to 200:
*Florent* (158) and *Martino* (136), counted mostly as first names, then pushed *flussi* and *martellu* out, hence
the cap at 50.

Seen in the Keyman engine 18.0.254 (2026-10-18, agent C's `tests/e2e/check_keyboard.py` from its work in progress,
headless Chrome, packages built from this data, setting 3 = auto-correction as the 18.0 engine applies it when
asked; not Keyman 19, not a phone): the 22 cases of `tests/e2e/keyboard_data_cases.tsv` pass in the three models —
*Bastelicaccia*, *Bastilicaccia*, *Zicavo*, *Zicavu*, *Ajaccio*, *Aiacciu*, *Bonifacio*, *Solenzara*,
*Porto-Vecchio*, *Sari-Solenzara* and an unknown *Platykalt* stay as typed; *bastelic* offers *Bastelicaccia*;
*Sartene* offers *Sartène*; *lingua parlle* becomes *lingua parolle*; *paro* still offers *parò*. One warning
then: *Vizzani* (Vikipedia's spelling, not in the list) became *Vezzani*; fixed since (see "Auto-correction").

## Auto-correction: what the data controls and what the engine does

What Keyman does (engines 18.0.254 and 19.0.309 beta, observed by agent C and here in `tests/e2e/check_keyboard.py`,
headless Chrome, outside the apps): a word typed exactly as the dictionary writes it, case included, is kept. A word
the dictionary does not have may be replaced on space by a close word, or by the same word with another case, when
auto-correction is on: setting 3, offered by Keyman 19 (an option, not the default) and applied by the 18.0 engine only
when asked; **the Keyman 18 apps offer no automatic correction**, so on Keyman 18 phones nothing is replaced unless the
suggestion is tapped. The dictionary cannot change that engine rule; it can only contain the right words.

Four cases found with setting 3, and what was done (2026-10-18):

| Typed | Became | Cause | Change | Provenance |
|---|---|---|---|---|
| *Vizzani* | *Vezzani* | data: only the Wikidata label was listed | *Vizzani* added next to *Vezzani* (both kept), place-name weight 50 | Vikipedia article title (*Vezzani* redirects to it), Wikidata sitelink of Q753074 (one page consulted), a quotation in the article; `sources/place-titles.tsv` |
| *corti* | *Corti* | data: only the capitalised name was listed | lowercase *corti* added next to *Corti*, weight 468 (its lowercase uses) | Apertium adjective *cortu* (plural *corti*), 62 lowercase uses in Vikipedia; `sources/homographs.tsv` |
| *calvi* | *Calvi* | data gap, no source | nothing yet: *calvi* (bald) is in no consulted source (no Corsican Wiktionary entry for *calvu*, nothing in Apertium, ADECEC's lexicons or lowercase Vikipedia). Stays a `warn` case | to check by hand in INFCOR |
| *ADECEC* | *DECE* | data: acronyms were filtered as non-words | *ADECEC*, *INFCOR*, *BDLC* kept in capitals, weight 20 | `sources/acronyms.tsv` (editorial list, each with its reference) |

The same rule found 11 more common words written like a name of the list that Wiktionary has as common (non-name)
Corsican forms; they are added in lowercase next to the name: *orsu*, *argentu*, *mansu*, *cagna*, *misericordia*,
*magnu*, *dio*, *alzi*, *forana*, *ritondu*, *rotondu*. Nothing was removed: *Corti*, *Calvi*, *Orsu*, *Vezzani* and the
other names stay as they were. A lowercase word and its capitalised name are two entries with the same search key;
`tools/count_kmp.py` on the built packages: 13,213 entries, 13,213 distinct words, 13,201 ignoring case.

Effect on suggestions (`simulate.py` ranking, every 1-4 letter prefix, 4,970 prefixes, same in the three models): 19
prefixes change; 3 entries leave a top 3: *Cagnano* (20; *cagn*: *cagna*), *Manso* (20; *mans*: *mansu*) and
*l'affissaghju* (1; *l'af*), the last from a lexicon count that changed with the merge, not from this change. The other
changes add the lowercase word next to its name (*ors*: *Orsu*, *orsu*) or fill empty prefixes (*ade*: *ADECEC*;
*viz*: *Vizzani*). Weights elsewhere moved by at most 1 because the project lexicon grew between the two builds.

Remaining limits, by platform and version:

- Keyman 18.0 (stable) apps, Android and iPhone: no automatic correction; nothing is replaced unless tapped.
- Keyman 19 (beta) with auto-correction on, and the 18.0 engine when setting 3 is forced: a word missing from the
  dictionary can still be replaced: *calvi* by *Calvi* until a source attests it; a proper name or a word Corsu does
  not list. *Fesch* (rue Fesch) was kept in the 18.0 engine test but became *Perchè* in the 19.0.309 engine (agent
  C's sentence scenario): an unknown name is an engine limit, not something a word list can solve for every name.

Engine results of `tests/e2e/keyboard_data_cases.tsv` (37 cases, 2026-10-18, packages built from this data, headless
Chrome, not a phone): Keyman 18.0.254, every `fail` case passes in the three models, one warning (*calvi* →
*Calvi*); Keyman 19.0.309 beta, every `fail` case passes, warnings: *calvi* → *Calvi*, *ade* does not offer *ADECEC*
(the banner fills with corrections of higher weight: *avemu*, *andemu*, *de*…), and *Fesch* → *Perchè* in the
sentence scenario.
- Other communes whose Vikipedia title differs from the Wikidata label (98, in `audit/commune-titles.tsv`): not added,
  because a redirect is not always another name of the commune (*Mela* → *Mela (malus domestica)*); each needs a check.
- iPhone: the whole-word replacement of `keyboard/whole-word.js` applies only on Android (see that file).

## Forms auto-correction replaced (2026-10-19)

This section describes the first pass as it was committed; the second pass below changed its Vikipedia count, its
weights and its numbers (19,550 entries then, 19,228 now).

Whole sentences typed key by key in the Keyman engine with auto-correction on (setting 3; 18.0.254 and 19.0.309
beta, `tests/e2e/keyman/harness.mjs`, headless Chrome, not a phone) showed correct words replaced because the list did
not have them: *tradizioni* became *tradizione*, *culturali* *culturale*, *milioni* *milione*, *andati* *andatu*,
*fundata* *fundatu*, *venuta* *venutu*, *zitedda* *ziteddu*, *abitanti* *abitante*, *manghjatu* *manghjà*, *partuti*
*spartuti* (18.0) or *partiti* (19.0), *L'ADECEC* *ADECEC*, *l'abitanti* *abitanti*. The list had 13,215 entries, built from usage; Wiktionary was only cited to
attest words other rules had selected, and a Vikipedia word needed 30 occurrences and a second source. An unknown
word is not a typo: three rules of `tools/make_vocab.py` now add forms that a source writes, as *known* words with a
low weight (they must be kept when typed, not suggested early):

| Step | Rule | Added | Examples |
|---|---|---|---|
| 5b | A form written at least 5 times in Vikipedia, mostly in lowercase, that differs only by its final vowel (-u/-a/-i/-e) from a listed word, or from its own masculine singular in -u also written 5 times (the Corsican ending, which keeps Italian paradigms out) | 3,113 | *abitanti*, *tradizioni*, *fundata*, *andati*, *zitedda*, *partuti* / *partutu* / *partuta* |
| 5c | A word or form of Wiktionary's Corsican entries (names, misspellings, archaic forms and templates left out), conjugation tables included | 2,749 | *manghjatu*, *cantendu*, *parlavamu*, *magneraghju* |
| 5d | An elided form written at least 5 times in Vikipedia whose second part is a listed word (or a curated acronym) and whose first part is an elision the list uses at least 5 times (l', d', un', st', s', ch'); the second part keeps the list's case | 473 | *l'abitanti*, *d'Aiacciu*, *l'Italia*, *l'ADECEC* |

Weight: the Vikipedia frequency, at most that of the listed form (5b) and at most 100 (`INFLECTED_CAP`); most
Wiktionary forms weigh 1. No variety preference changes: *zitedda* and the regional forms of Wiktionary become known
words of `shared.tsv` only, and `cismuntincu.tsv` / `pumuntincu.tsv` are unchanged (no form is raised or lowered
without a source that pairs it, and none was generated by a letter rule). Both steps rest on sources already listed in
`docs/keyboard-sources.md` (Vikipedia, CC BY-SA 4.0; Wiktionary through kaikki.org, CC BY-SA 4.0); this is an
automated selection by an AI agent, not a review: Vikipedia also quotes Italian (*secoli* and *prodottu* passed the
rule; see the second pass, which holds them back), and a speaker may want some forms removed.

Measured (`simulate.py` ranking, every 1-4 letter prefix, 5,575 prefixes; same in the three models): `simulate.py`'s
checks all pass; 1,719 prefixes get a different top 3 and 742 entries leave a top 3, all of weight 100 or less
(*succorsu*, *urigine*, *Scolca*, *Liamone*...); no word above 100 leaves one. Without the cap, *abitanti* (854
Vikipedia occurrences) and *rumani* took the first places of *a* and *r*. `tools/count_kmp.py` on the built packages:
19,550 entries, 19,550 distinct words (19,538 ignoring case). Package size 253 KiB to 344 KiB.

Engine results after the change: the sentences keep every form above (cases in `tests/e2e/keyboard_data_cases.tsv`
and the scenario "apostrophes: an elided word" of `tests/e2e/check_keyboard.py`). Still replaced in the 19.0.309
engine: verb forms neither source has (*ghjocanu* became *ghjovanu*, *vedemu* *vedenu*); U Cunghjugarellu covers 21
verbs in two tenses only. An elided form Vikipedia does not write 5 times stays unknown: the engines' correction
search only follows words of the lexicon, so the model cannot recognise an elided form it does not list (tried in
`keyboard/whole-word.js` and dropped: the engine never asked the model about such a word). In the 19.0.309 engine
the outcome for an unknown word also depends on time: the same typing kept *l'abitanti* (before this list had it) in
five runs of six and replaced it in one, when the correction search had time to reach *abitanti*.

## Second pass (2026-10-19): foreign passages, held-back forms, recognition and suggestion

Automated work by an AI agent, like the rest of this file; no speaker has reviewed it.

### What let foreign text in

Steps 5b and 5d counted every token of the Vikipedia dump outside templates and tables. Corsican articles also hold
text in other languages: titles of works (in italics or in bibliographies), quotations, image captions, Italian,
French and Latin sentences, poems in Italian, and table legends that the table cleaning missed. A form written 5
times there passed, whatever the language. *secoli*: 6 occurrences, among them the caption "La calligrafia corsiva
insegnata nelle scuole italiane (secoli XX-XXI)" (article *Lingua taliana*) and "Noi siamo da secoli / Calpesti,
derisi" (*U Cantu di i Taliani*, the Italian anthem); 4 are in prose, in two articles. *prodottu*: an infobox legend
repeated in four element articles ("DP = prodottu di u decadimentu"), once in prose (*Rombu*).

### The fix: counting Corsican prose only

`make_vocab.py` (class `Prose`) now reads each article and counts a word as Corsican prose only outside:

- the list sections (*Riferimenti*, *Note*, *Bibliugrafia*, *Ligami*, *Da vede dinù*, *Citazioni*, *Opere*,
  *Albumi*…, `LIST_SECTIONS`), where titles, references and quotations are in the language of the work;
- italics (`''…''`: titles of works, foreign words) and text in quotation marks (« », “ ”, " ");
- sentences holding an Italian, French or Latin function word that Corsican does not write (`FOREIGN_MARKERS`: *il*,
  *della*, *nelle*, *sono*, *che*, *con*, *come*…; *les*, *des*, *est*, *une*, *et*…; *sunt*, *quae*…). *più*, *la*,
  *le*, *tra* and *è* are not markers: Corsican texts write them;
- blocks of verse or indented lines (`<br>`, `<poem>`, `<blockquote>`, lines starting with ":") that hold such a word
  anywhere; a block without one (a Corsican song or proverb) counts as prose;
- tables and formulas.

A form is added by step 5b or 5d only when it occurs **5 times in Corsican prose, in at least 3 articles**
(`INFLECTED_ARTICLES`), so that one article cannot add a form on its own. The other form that shows a paradigm in -u
must be written 5 times and at least once in prose. The weight comes from the prose count. A form that passed the old
count and fails the new one is **held back** (`held-back.tsv`), unless another source writes it: Wiktionary (step 5c
then adds it), Tatoeba, Apertium, U Cunghjugarellu or ADECEC. An elided curated acronym keeps the old count:
Vikipedia writes *l'ADECEC* 233 times of 234 in its bibliographies, where it is the publisher's name in Corsican.

The markers decide whether a *sentence* is Corsican, never whether a *word* is: no form was removed because it
looks Italian. Corsican and Italian share many forms, and a form that Corsican prose writes in several articles stays
(*polvere*, below).

### Result

| | First pass | Second pass |
|---|---|---|
| 5b: other forms of a listed word (Vikipedia) | 3,113 | 2,819 |
| 5c: Wiktionary forms | 2,749 | 2,763 (14 forms the prose rule no longer takes from Vikipedia, which Wiktionary has) |
| 5d: elided forms (Vikipedia) | 473 | 429 |
| 5e: forms a reference writes in full (`sources/forms.tsv`) | – | 1 (*ghjocanu*) |
| Held back (`held-back.tsv`, not shipped) | – | 324 (280 from 5b, 44 from 5d) |
| `shared.tsv` entries | 19,550 | 19,228 |

19,550 − 324 held back + 1 (*ghjocanu*) = 19,227; the last entry comes from the project lexicon, which changed
between the two builds (*spirlatu*, *spirlati*, *minuteria* in; *puntate*, *cronumetru* out). `cismuntincu.tsv` and
`pumuntincu.tsv` are unchanged.

Each held-back row gives the counts (all, prose, prose articles), where the other occurrences are, a class (the kind
of passage that holds most of them, computed, not judged) and up to three passages with their article:

| Class | Count | Examples (article: passage) |
|---|---|---|
| `corsican-prose-rare`: mostly prose, fewer than 5 times there | 184 | *secoli* (4 in prose; *Lingue rumaniche*: "un prucessu duratu secoli"); the Corsican plural is *seculi*, listed |
| `corsican-prose-narrow`: 5 times or more in prose, in one or two articles | 106 | *reghjimenti* (22, all in *Prima guerra mundiale*), *cicilianu* (17, two articles), *ucrainiana* |
| `italics` | 16 | *cundiziunali* (the heading of conjugation tables in *Frassetu*, *Gadduresu*…), *candu* (Gallurese and Judeo-Corsican quotations), *l'ami* |
| `title-or-reference` | 13 | *illustrata* ("Galletti, Storia illustrata di a Corsica", bibliographies), *toscani* ("Canti toscani, corsi, illirici, greci"), *paghjelle* ("Inventariu di e paghjelle di Corsica"), *nature* |
| `quotation` | 2 | *soga* (dialogue in quotation marks in day articles) |
| `foreign-sentence` | 1 | *dalla* (*Lucca*: "Panorama di Lucca, vista dalla torre Guinigi") |
| `foreign-verse` | 1 | an Italian poem |
| `table-or-template` | 1 | *prodottu* (the infobox legend above) |

Held back is not a verdict on the word. Many of these are Corsican (*ghjacara*, *soga*, *cicilianu*, *scannata*):
an automatic rule just has too little Corsican prose to list them. A reviewer brings one back by citing a source
(an entry in `sources/forms.tsv` with its reference, or a Wiktionary entry), not by lowering the threshold. Proper
nouns were already kept out of step 5b (a form Vikipedia capitalises mid-sentence half the time or more).

Kept after a look at their passages (still Vikipedia only, so a speaker may disagree): *polvere* (plural of
*polvera*, which the list has; in prose in four articles: *Bandana* "l'inhalazione di polvere", *Cometa* "superficie
secche di polvere o petre", *Manucure*), *hani* (southern 3rd plural of *avè*; *Ricciu* "I pedi hani cinqui
cuscinetti", 15 times in 12 articles), *osse* (17 times in prose, "E so osse sò cunservate"), *offri*. *illa* is now
listed through Wiktionary, not through Vikipedia (its Vikipedia uses are Gallurese, a Latin hymn and a name).

What the prose count does not catch: Gallurese and Sassarese passages (*Tempiu*, *Gadduresu*), Italianising
Corsican (*Lingue rumaniche*), machine-translated articles (*Manucure*), Italian sentences without any of the
markers. Italics also mark Corsican example phrases in linguistics articles (*Frassetu*, *Variità taravesa*); those
are left out too, which errs on the side of holding back.

### ghjocanu and vedemu

Keyman 19.0.309 turned *ghjocanu* into *ghjovanu* and *vedemu* into *vedenu*, because the list had neither.

- *ghjocanu* (3rd plural present of *ghjucà*, "they play"): U Cunghjugarellu writes it in two example sentences ("I
  zitelli chì ghjocanu in a corte brionanu assai", "ci sò i zitelli chì ghjocanu in corte", PDF pages 32 and 37;
  *ghjucà* follows its table 8, *Tuccà*), and Vikipedia 9 times in Corsican prose, in 9 articles. Added through
  `sources/forms.tsv` (step 5e), source cited `vikipedia`, weight 71. Wiktionary's *ghjucà* entry has no conjugation.
- *vedemu*: **not added**. U Cunghjugarellu's table 94 (*vede*, supranacciu) gives the present 1st plural as
  *vidimu/videmu* (both in the list: *videmu* 500, *vidimu* 45; *videmu* is also its past simple), the suttanacciu
  table *vidimu/videmi*. *vedemu* is in no source consulted and occurs once in the Vikipedia dump. A form is never
  made by changing letters of another, so the engine may still replace it (a `warn` case in
  `tests/e2e/keyboard_data_cases.tsv`).

### Added forms no longer push listed words out of the suggestions

`INFLECTED_CAP` (100) alone let a form of weight 100 push listed words lighter than 100 out of a top 3: from 1.1
(v0.26.0) to the first pass, 676 entries of the shared model left the top 3 of a 1-4 letter prefix, 176 of them of
weight 50 or more: *utile* (92) at *uti*, for *utilizatu*, *utilizati*, *utilizatori*; *eccezziunale* (91) at *ecc*;
*urigine* (99), *succorsu* (100), *neutri*, *litri*, *australe*. Each form of steps 5b-5e now weighs less than every
other word of the list in the top 3 of each prefix of its search key (2,297 forms lowered): it only fills places
that the list leaves empty. Recognition does not depend on this weight: Keyman's trie returns the entries whose key
is the typed word first, then the 12 best completions (`Trie.lookup`, the same in the 18.0.254 and 19.0.309 engines),
so a form of weight 1 typed in full is still in the model's answer.

Measured with `simulate.py`'s ranking (every 1-4 letter prefix, the shared model; the variety models give the same
counts):

| | 1.1 → first pass | 1.1 → second pass | first pass → second pass |
|---|---|---|---|
| Entries | 13,213 → 19,550 | 13,213 → 19,228 | 19,550 → 19,228 |
| Prefixes whose top 3 changes | 1,719 of 5,575 | 1,246 of 5,547 | 882 |
| Entries that leave a top 3 | 676 (176 of weight ≥ 50) | 56, all of weight 1 or 2 (ties of weight 1, and *cronumetru*, gone from the lexicon) | 758 (added forms lowered or held back) |
| Entries new since 1.1 in a top 3 | 2,102 | 1,545 (in places 1.1 left empty or filled with weight-1 ties) | – |
| Held-back forms in a top 3 | 156 forms, 201 prefixes (*illustrata* at *il*, *dalla* at *dal*, *candu*, *sacchettu*, *ucrainianu*) | 0 | – |

`simulate.py`'s checks pass, and `tests/test_keyboard_vocab.py` checks *utile*, *eccezziunale* and *urigine*.

### Recognising, suggesting and replacing: what Keyman lets a model set

Three things are distinct for the user: a typed word is **recognised** (kept as typed, not marked as a mistake), a
word is **offered** in the banner, a word **replaces** another automatically. What Keyman lets a lexical model set,
from the developer documentation (https://help.keyman.com/developer/18.0/reference/file-types/model-ts and
.../guides/lexical-models/advanced/, pages for 18.0 and 19.0, read 2026-10-19) and from the predictive-text worker of
the 18.0.254 and 19.0.309 Android engines (`worker-main.wrapped.min.js`, read from the APKs' source maps, functions
named in the code `processSimilarity`, `predictionAutoSelect`, `Trie.lookup`):

- A `trie-1.0` model takes `sources` (words and weights), `wordBreaker` (with `joinWordsAt`), `searchTermToKey`,
  `languageUsesCasing` / `applyCasing` and `punctuation` (`insertAfterWord`, `quotesForKeepSuggestion`). There is no
  per-word flag, no list of known-but-not-offered words, and no setting for auto-correction or its threshold.
- **Recognised** = the engine finds, among the model's predictions for the word as typed, one equal to it
  (`matchesModel`). With a trie model this holds for every listed word, whatever its weight.
- **Offered** = the model's predictions for the typed word and for the engine's corrections of it, ranked by weight
  times correction probability; 3 shown on a phone.
- **Replaced** (auto-correction, setting 3, Keyman 19; the 18.0 engine when asked, the 18.0 apps do not offer it):
  when the typed word is not recognised, the best correction is chosen if it has at least 66 % of the probability of
  the candidates of its level (constant in the engine: `.66`). A recognised word is never replaced.
- The user's settings (suggestions on or off, corrections, auto-correction in 19) apply to every word alike.

The only lever a model has is what `predict` returns, and the engine asks it about its own corrections exactly as about
the typed word (the corrected word is passed as the text to complete). A wrapper such as `keyboard/whole-word.js`
could stop a word being offered as a completion while keeping it recognised (returning it only when it equals the
word being completed), but it cannot tell a correction from what the user typed, so it could not keep that word from
replacing a near miss. That would rest on undocumented engine behaviour, so nothing of the kind was built. Within the
data, the separation that exists is: being listed (recognised, never replaced), weight (how early it is offered, and
how likely it wins as a correction), and not being listed (held back: neither offered nor recognised).

Engine results: see the next commit (runs of `tests/e2e/check_keyboard.py` on these packages).

## Northern and southern preferences

### What the names cover

*Cismuntincu* (Italian *cismontano*, "this side of the mountains") and *pumuntincu* (*oltramontano*) are the two
traditional groups of Corsican varieties, north and south of the island's mountain ridge. They are linguistic
groupings, not the two départements: the line runs roughly from Piana–Vico–Vizzavona–Ghisoni–Ghisonaccia (frwiki,
"Nord de la Corse"), and a **transition zone** (Piana, Calcatoggio, Cinarca, Vizzavona, Fiumorbo, the Ajaccio area,
Gravone, Bastelica, Solenzara) mixes features — Ajaccio says *cane* and *accattà*, the northern words, while having
southern -i feminine plurals. Inside each group there is variation: in the south, **Taravu** (Taravesu) and **Sartè**
(Sartinesu) differ (*eddu*/*iddu*, *piglià*/*piddà*, *famiglia*/*famidda*), the Alta Rocca is close to northern
Sardinia, and the Porto-Vecchio hinterland and Bonifacio area have masculine plurals in -a. In the north, Cap Corse
uses the articles *lu, li, la, le*. **Bunifaziu and Calvi** speak Ligurian dialects inherited from Genoa, not
Corsican: they are not covered by either list. Gallurese, Sassarese and Castellanese (Sardinia) are related but
separate and not covered. U Cunghjugarellu calls the two versions *supranacciu* (north) and *suttanacciu* (south).

### Status: real but partial, experimental as a keyboard setting

The differences are **sourced**, not generated: no letter rule (-ll- → -dd-, -e → -i…) was applied to any word. Every
variety-specific form comes from a cited table or entry. But coverage is narrow — the verbs of 21 conjugation tables,
28 + 7 lexical pairs from two encyclopaedia articles and 19 Wiktionary entries — so these are **preference lists, not
a dialect dictionary**. The weights given to each side (pair weight, 25 % for the other side) are an editorial
choice. Treat the two settings as experimental until a speaker of each area has tried them.

Checked again on 2026-10-18 (by the AI agent, not by a speaker): the 28 rows of Vikipedia's table against the local
Vikipedia dump (same forms, Taravesu and Sartinesu columns as recorded), the Wiktionary pairs against their
Cismontane / Ultramontane tags in the kaikki.org extract (all present; one wrong gloss corrected, question 6 below),
and the 368 U Cunghjugarellu forms against the PDF's text (all present). No weight of the 361 was changed. The
lists only favour a form: neither removes the other variety's forms, and neither stands for a département.

| | Count |
|---|---|
| Words whose weight differs between the merged northern and southern lists | **361** |
| — from U Cunghjugarellu (21 verbs, present and imperfect indicative, 21 of its 100 tables) | 253 |
| — from Vikipedia "Lingua corsa" (Taravesu / Sartinesu table) | 60 |
| — from Wiktionary (Cismontane / Ultramontane entries) | 34 |
| — from Wikipédia "Corse (langue)" | 14 |
| `cismuntincu.tsv`: northern forms raised / southern forms lowered | 175 / 179 |
| `pumuntincu.tsv`: southern forms raised / northern forms lowered | 192 / 165 |

Examples (northern list / southern list weights): *simu* 20,000 / 5,000 and *semi* 5,000 / 20,000 (*semu*, given for
both groups, is untouched); *induve* / *induva*; *eranu* / *erani*; *cantavamu* / *cantavami*; *anu* / *ani*;
*socu* (southern 1st person of *essa* and *sapè*); *ellu* / *eddu*, *iddu*; *fratellu* / *frateddu*; *pane* /
*pani*; *tredeci* / *tredici*.

The pairs *parlate/parleti* and *parlanu/parlani* no longer have a tier (they had tier 2, an editorial choice): every
other verb's plural forms (*andate/andeti*, *avete/aveti*, *cantate/canteti*) have none, and Vikipedia has *parlate* 56
times, *parleti* 0, *parlanu* 26 and *parlani* 11 (*parolle* 47, plus 971 times in the lexicon). With the tier, *parleti*
weighed 2,500 in `shared.tsv`, more than four times *parolle* (546); Keyman's correction gives the typo *parlle* the same
cost for both (one deleted letter to reach *parle-ti*, one inserted letter for *parolle*; a completion costs nothing),
so the weight decided, and auto-correction turned *parlle* into *parleti*. Now *parleti* weighs 500 in `shared.tsv`, 250
in the northern list and 1,000 in the southern one. That still left *parleti* (1,000) above *parolle* (546) in the
southern list, and nearly level with it (500 / 546) in `shared.tsv`. *parolla* and *parolle* ("word", "words") are
therefore daily words of tier 2 (`sources/daily.tsv`, an editorial AI choice like the rest of that list, at the level
of *parla*, *parlà* and *cosa*): 5,000 in the three lists, so the same one-letter typo now leads to *parolle* in every
model. Measured on every 1-4 letter prefix: only *paro* changes, where *parò* (806) leaves the top 3 for *parolle*;
Keyman folds accents, so typing *parò* reaches the same prefix; whether the banner still shows *parò* then is an
engine question, listed as a case to watch.
The engine case is in `tests/e2e/keyboard_data_cases.tsv`.

Pairs where both forms are used in the south, or where a form has another common sense, do not lower the other form
(`lower_other = no`): *piglià/piddà*, *famiglia/famidda*, *paglia/padda*, *figliolu/fiddolu*, *vogliu/voddu* (Taravu
keeps the first form), *manghjà/magnà* (both northern), *accattà/cumprà*, *sì/s'è*, *nove/novi*; and the forms *eri*
(yesterday), *sete* (thirst), *mane* (morning), *sani*, *vani*, *pari*, *sò*, *site*, *deti*, *feti* are never lowered.

### Gaps (not covered, not guessed)

- Future, conditional, subjunctive, imperative and past simple of the verbs; the other 79 tables of the book; the
  Alta Rocca imperfect (*andaghjiu*, *cantaiu*) printed next to the southern one.
- Forms the book writes with a final apostrophe (*da'*, *va'*, *po'*, *sa'*, *vo'*, *a'*) were left out.
- The southern -i of nouns and adjectives (*pastori*, *nazioni*) only for the listed examples; masculine plurals in
  -a (*i letta*); Cap Corse articles; any Ligurian (Bunifaziu, Calvi).
- *eiu*/*iu* and other pronouns: no source consulted pairs them by area.
- Sources disagree on "to arrive": Vikipedia's table gives *ghjugne / ghjugna*, U Cunghjugarellu *ghjunghje /
  ghjunghja*. Both are kept.

## To check by hand (INFCOR, ADECEC or a speaker)

AI proposals (in no source consulted; kept with the daily weight): *ciao*, *saluti*, *auguri*, *evviva*, *cugina*,
*amiche*, *partimu*, *appetitu*, *pigliu*, *stanca*, *malata*.

Left out of the daily list because unsure: *bonasera* (one word, or *bona sera*?), *nonnu*, *nanna*, *minnanna*
(grandparents: which forms are usual, and where? *missiavu* is kept, attested), *fratellucciu*.

Corsu-lexicon-only words that the daily list raises (no external attestation found): *scusate*, *benvenuti*,
*mandu*.

Variety questions:

1. *cane* / *ghjacaru*: Wiktionary marks *cane* "Cismontane, dialectal" and *ghjacaru* "Ultramontane, dialectal",
   Vikipedia's table gives *cane* north, *ghjàcaru* south, and frwiki says Ajaccio uses *cane*. Is *ghjacaru* also
   common in the north (then `lower_other` should be `no`)?
2. *accattà* / *cumprà*: only a preference; both are written in the north.
3. *simu* / *semi*: the southern list lowers *simu* to a quarter; is *simu* heard in the south (Taravu)?
4. Wiktionary *dicessetti* and *diciassetti* (seventeen, Ultramontane): which one is usual?
5. *stai*: the southern 2nd person of *stà* is printed *sta'* in U Cunghjugarellu; it was not paired, so *stai* is
   not lowered in the south.
6. *vindette* / *vindetti* (plural of *vindetta*): Wiktionary's *vindette* entry calls *vindetti* Ultramontane, but its
   *vindetta* entry gives both plurals without a label. The northern list lowers *vindetti*; if it is also usual in
   the north, the pair should get `lower_other = no`. (Its gloss said "sold" until 2026-10-18; corrected.)

Place names:

- *Bastilicaccia* / *Bastelicaccia*: both are now known (above). Still open: which Corsican spelling a speaker of
  the place uses (INFCOR or the commune, by hand). Several Wikidata labels differ from the Vikipedia title (*Zicavu* /
  *Zìcavu*, *Vezzani* / *Vizzani*): the labels were kept; *Vizzani*, the Vikipedia title, is now listed next to
  *Vezzani* (see "Auto-correction"); the other differing titles are in `audit/commune-titles.tsv`, to check one by one.
- *Bonifaziu* (label of the pieve) next to *Bunifaziu* (the commune): both are kept.

Other everyday-word questions:

6. *colazione* (Vikipedia) vs *cullazione* (ADECEC: "déjeuner"), *pesce* (Wiktionary) vs *pesciu* (ADECEC): both
   kept; which should be preferred?
7. *nivulu* (Wiktionary) vs *nuvulu*, *nulu* (ADECEC "nuage"); *tempesta* (lexicon) vs *timpesta* (ADECEC).
8. Product names are removed even when Corsican text writes them (*Google*, *Windows*). If the maintainer wants
   them suggested, they belong in a separate, explicitly listed set.

## Licences

See [docs/keyboard-sources.md](../../docs/keyboard-sources.md), section "U Cunghjugarellu (Canopé de Corse)", for
what the publisher states (book page: CC BY-NC-ND 2.0 FR; PDF: general reproduction reservation; neither is a
licence on the words), what `sources/cunghjugarellu.tsv` holds (511 rows, 368 forms: two tenses of 21 tables, one
form per row with its table number), what the packages receive (words and weights only) and the three uses told
apart: checking a fact, reusing the book's texts or editorial choices, extracting a data collection. The ADECEC
pages were used only to check 53 single words.

## Rebuilding

```
python3 keyboard/data/tools/fetch_places.py    # optional: asks Wikidata again, rewrites sources/places.tsv
python3 keyboard/data/tools/make_vocab.py      # needs ~/.local/share/corsu/resources (tools/fetch_resources.py)
python3 keyboard/data/tools/simulate.py --show # top-3 checks; --old for the old list; --scan for software terms
HOME=$(mktemp -d) python3 -m unittest tests.test_keyboard_vocab
```
