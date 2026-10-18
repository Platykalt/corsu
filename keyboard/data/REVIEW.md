# Keyboard vocabulary: audit and review

Automated work by an AI agent (2026-10-18). **No human has reviewed these lists.** Nothing here is a speaker's
validation; "attested" only means that an external source writes the word that way.

Files:

| File | Content |
|---|---|
| `shared.tsv` | The base list: 13,197 words, both varieties' forms included (446 Corsican place names and 221 words of official commune names). |
| `cismuntincu.tsv` | 354 rows laid over `shared.tsv` for a northern preference. |
| `pumuntincu.tsv` | 357 rows laid over `shared.tsv` for a southern preference. |
| `sources/` | Hand-checked inputs: `daily.tsv` (everyday words, editorial choice), `adecec.tsv`, `cunghjugarellu.tsv`, `variant-pairs.tsv`; `places.tsv`, the Corsican place labels of Wikidata; `communes-official.tsv`, the official (INSEE) commune names. |
| `tools/make_vocab.py` | Rebuilds the three lists from the sources (needs the resources of `tools/fetch_resources.py`). |
| `tools/fetch_places.py` | Runs the three Wikidata queries that write `sources/places.tsv`. |
| `tools/fetch_communes.py` | Two requests to geo.api.gouv.fr that write `sources/communes-official.tsv`. |
| `tools/simulate.py` | Top-3 suggestion simulation and checks (also run by `tests/test_keyboard_vocab.py`). |
| `audit/removed.tsv` | Every word of the old list that was dropped, with its reason. |
| `audit/stats.json` | The numbers quoted below. |

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
- Elided forms are single entries (`nant'à`, `cum'è`, `l'annu`, `ch'è`; 1,280 in `shared.tsv`), because Keyman's
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

Range: 1 to 715,754 (*di*); median 33; 977 words at 1,000 or more.

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
446 place names and 221 words of official commune names (below): **13,197 words**, 6,546 attested. The audit reads the old list from git (commit 66e7f58,
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
*Sartene* offers *Sartène*; *lingua parlle* becomes *lingua parolle*; *paro* still offers *parò*. One warning:
*Vizzani* (Vikipedia's spelling, not in the list) becomes *Vezzani*. Adding the Vikipedia article titles of the
communes next to the Wikidata labels would fix that kind of case; it needs the titles (Wikidata sitelinks), not
fetched yet.

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
  *Zìcavu*, *Vezzani* / *Vizzani*): the labels were kept; *Vizzani* (6 times in Vikipedia) is not in the list, so
  Keyman 19 may auto-correct it: to check by hand which spelling is usual.
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
