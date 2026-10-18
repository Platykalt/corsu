# Minecraft review of October 2026: lots examined and lots remaining

This page merges `tracking-concrete.tsv` and `tracking-language.tsv` (the two proposal sets) with the independent
verification that decided what was applied. Everything here is AI work: two AI agents proposed, a third AI agent
verified the evidence. **Human validation: 0.** A speaker has not read any of it.

## Four separate states

| State | Result for this review |
| --- | --- |
| Translation present | unchanged: every non-empty text of the 87 releases has Corsican (the review only replaced texts) |
| Technical check | after the changes: `tools/minecraft.py check` 0 errors; `tools/mchistory.py check` 0 errors; `tools/mcversions.py verify all` on 2026-10-18 with each release's own client jar: 87/87 releases 0 errors, every Corsican text rendered by the release's own loader and formatter with 0 unknown keys and 0 problems (2 or 3 texts per release skipped because their English itself does not format), 26.x text components rendered by `LangCheck` with 0 problems; `tools/mcreport.py --check` up to date; unit tests 480 run, OK (2 skipped). A green check says the files load and the arguments render; it says nothing about the language. |
| AI review with sources | 102 concrete decisions and 209 language rows proposed; every change proposal re-checked against its cited source by the verifier ([APPLIED.tsv](APPLIED.tsv), [REJECTED.tsv](REJECTED.tsv)) |
| Human validation | 0 |

## Verification (2026-10-18)

How the sources were re-consulted: the ADECEC lexicon pages and the INFCOR results that the concrete agent had
already fetched and cached were read again from that cache (no new INFCOR query was sent); the Corsican Vikipedia
dump in the Corsu resources was searched locally; the reviewed software lexicons (`lexicon/lexicon-mozilla.tsv`,
`lexicon/lexicon-upstream.tsv`) were read at the cited lines. No web page was fetched in this pass.

| Set | Change proposals | Applied | Not applied: rejected | Not applied: deferred |
| --- | --- | --- | --- | --- |
| Concrete nouns (concrete.tsv) | 58 (50 changes + 8 unresolved) | 43 (42 verified, 1 adaptation) | 7 | 8 (unresolved, no change proposed) |
| Language (language.tsv) | 181 (all rows but 28 "keep") | 87 (45 verified, 19 harmonised, 23 adaptations) | 61 | 33 |
| Verifier extensions | — | 3 (clock in `/time` texts, birch biomes, old "On A Rail") | — | — |

Texts changed: 1,131 (779 in the 26.3 base, 352 older pairs in `history.json`).

Verdicts: **verified** = the cited reference exists and says what was claimed, in the game's sense; **harmonised** =
both forms are attested, one spelling was chosen for the whole product (the other is not wrong); **adapted** = a
proposed adaptation applied because the current text was demonstrably wrong (sense, language or grammar);
**rejected** = the evidence contradicts the proposal or does not support it; **deferred** = for a speaker or an
in-game length check.

Main reasons for rejecting (details per row in REJECTED.tsv): the current form is an attested variant (*Stivali*:
INFCOR "stifale, VAR stivale"; *Fiurdalisu*: INFCOR synonym of turchinellu; *trovu*, *s'annega*, *hè tornu*,
*scadutu*, *fallitu*: found in the reviewed translations or in Vikipedia); the reference cited does not exist (the
« » typography rule); a "transitive ghjunghje is wrong" claim contradicted by `lexicon-upstream.tsv:9060`; a project
decision that says the opposite (decisions-2 D2: *Baghe dolce*, and nouns in *-ioni* left open).

## Lots examined by the proposers

Concrete nouns:

| Lot | Distinct entries | Checked against a source or a decision | Read, not checked |
| --- | --- | --- | --- |
| animals and mobs | 359 | 228 | 131 |
| food and crops | 93 | 82 | 11 |
| rocks, ores, minerals | 600 | 575 | 25 |
| plants and wood | 444 | 401 | 43 |
| blocks: furniture, devices, building | 286 | 192 | 94 |
| items: tools, weapons, armour, other | 222 | 145 | 77 |
| historical-only names (older versions) | 190 | 119 | 71 |

Language (all distinct English/Corsican pairs read): 26.3 options 350, controls 297, interface 1,181, narration 54,
subtitles 950, death messages 104, advancements 258, game rules 116, statistics 91, attributes 47, effects 50,
enchantments 53, telemetry 70, debug screen 63, game tests 86, commands 804, Realms 398, UI texts in noun categories
195; `history.json` new and adapted: UI 644, Realms 150, commands 628.

## Lots remaining

| Lot | Size | Why not done |
| --- | --- | --- |
| Concrete names read but not checked in a dictionary (invented Mojang names, coined devices such as *Fabbricadore*, *Lampatore*, *Ghjiradischi*, tropical fish, compounds) | 452 | no source expected for invented names; coined device names need a speaker |
| Banner patterns, potion and tipped-arrow names, item descriptions, music disc titles | 246 | out of the concrete scope (decisions-2 D8 for heraldry) |
| Realms legal and billing texts | — | not re-read for legal meaning (decisions-2 D15) |
| Deferred rows after round 2 (REJECTED.tsv, rows `-r2` with verdict "deferred") | 30 (28 of the 41, + H01, H02) | speaker, manual dictionary entry or in-game check; exact entry per row |
| Lengths on buttons (*Arregistrà è esce da a partita*, debug pause labels) | — | no text seen in a running game |

## Entries for a speaker or a manual dictionary check

Exact entries are in REJECTED.tsv (deferred rows) and in [concrete.md](concrete.md) "Unresolved". The ones with the
most texts behind them: *radichju* for Dandelion (applied: INFCOR, ADECEC la-cuisine and Vikipedia's text give
Taraxacum, but Vikipedia's article *Radichju* shows a radish and INFCOR's definition says "fiori turchini");
*cartella* for Sign (applied: INFCOR "écriteau, pancarte; EN placard, sign", but first sense "cartable");
*pastadolce* for Cake; *aghjurnà* or *mette à livellu* for update; *collisione* or *cullisione*; *focu*/*fucus* for
window focus; *ardesia* or *baina* for Deepslate; *diorite/andesite/calcite* or *-ita*; *cinabru*, *petrame*,
*lingottu*, *mola*, *cocciu*, *verruca*, *stillicciu*, *scala di manu* (concrete.md "Unresolved").

## Round 2 (2026-10-18): older texts and deferred rows

AI work again, by one agent; nothing here was read by a speaker. **Human validation: 0.** Rows are marked
`round=2` in [APPLIED.tsv](APPLIED.tsv) (`R2-01` to `R2-12`) and [REJECTED.tsv](REJECTED.tsv) (ids ending `-r2`).
Sources: the ADECEC lexicon pages and INFCOR results already cached in round 1 (read from the cache; no INFCOR
query, no web page fetched), the local Corsican Vikipedia dump, `lexicon/lexicon-mozilla.tsv` and
`lexicon/lexicon-upstream.tsv` by line.

| State | Result |
| --- | --- |
| Translation present | unchanged: every text of the 87 releases has Corsican (texts replaced only) |
| Technical check | `tools/minecraft.py check` 0 errors (37 warnings, the same 37 as before the round); `tools/mchistory.py check` 3,978 entries, 0 errors, 0 warnings; `tools/mcversions.py verify all` with each release's own client jar: 87/87 supported, every release 0 problems; `tools/mcreport.py --check` up to date; unit tests 509 run, OK (3 skipped) |
| AI review with sources | per lot below |
| Human validation | 0 |

| Lot | Size | Examined | Result |
| --- | --- | --- | --- |
| (a) `renamed` pairs | 1,755 (1,660 distinct English/Corsican) | all: every entry checked to equal the 26.3 text of its `from` key (1,755/1,755); the 204 whose old key belongs to another family than its source (potions vs effects, achievements vs advancements, Twitch options, old world presets…) and the 182 whose key name differs most from the source read one by one for sense in the old screen | 1 noun/verb fix (R2-03); 3 propagated from 26.3 fixes (R2-01, R2-02, R2-08) |
| (a) `reused` pairs | 507 (131 with an English that differs by more than case or punctuation) | all equal the 26.3 text of the same key (507/507); the 131 read for a change of sense ("whilst", "Pending Invitations", "Hostile Creatures", "Left Click", "There is/are"…): none changes the meaning | 3 propagated (R2-01, R2-12) |
| (b) old-only names (`new`/`adapted` in name families: tile, item, block, entity, biome, potion, effect, enchantment, itemGroup, attribute, filled_map) | 308 | all read and compared with the 26.3 names of the same thing (gender, agreement, applied round-1 names) | consistent; 4 kept or deferred with reasons (H01-H04) |
| all texts (26.3 + 3,978 history entries) | — | scan for every form replaced in round 1, for gender agreement around the renamed nouns, for Italian function words and -o endings | 5 history texts that round 1 had decided but not changed (R2-09 to R2-11); the abbreviation "min" for minutes (R2-12); no agreement error found |
| (c) deferred rows of round 1 | 41 | all re-checked against the local caches | 10 resolved by a change (R2-01, R2-02, R2-04 to R2-07), 3 kept with evidence (U01, B11, L62), 28 still deferred with the exact entry to check (L114 only for its verb) |
| glossary.tsv | 12 rows | stale proposal rows behind applied 26.3 names (Glow Squid, Hanging Sign, Concrete Powder, Dark/Pale Oak, Torchflower, three rails, Camel Husk) and Ladder, Hitbox | aligned with co_fr.json |

Texts changed in round 2: 27 (14 in the 26.3 base, 13 history pairs).

Not covered by round 2: the renamed pairs were judged through their 26.3 text, which the round-1 language and
concrete reviews read; names read but never checked in a dictionary stay as listed above; no text was seen in a
running game.
