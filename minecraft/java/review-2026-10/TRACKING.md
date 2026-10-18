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
| `history.json` renamed and reused pairs | 2,262 | pattern scan only (they copy 26.3 decisions) |
| `history.json` new/adapted noun pairs | about 250 | covered only through the concrete decisions that matched them |
| Realms legal and billing texts | — | not re-read for legal meaning (decisions-2 D15) |
| Lengths on buttons (*Arregistrà è esce da a partita*, debug pause labels) | — | no text seen in a running game |
| Deferred rows (REJECTED.tsv, verdict "deferred") | 41 | speaker or in-game check |

## Entries for a speaker or a manual dictionary check

Exact entries are in REJECTED.tsv (deferred rows) and in [concrete.md](concrete.md) "Unresolved". The ones with the
most texts behind them: *radichju* for Dandelion (applied: INFCOR, ADECEC la-cuisine and Vikipedia's text give
Taraxacum, but Vikipedia's article *Radichju* shows a radish and INFCOR's definition says "fiori turchini");
*cartella* for Sign (applied: INFCOR "écriteau, pancarte; EN placard, sign", but first sense "cartable");
*pastadolce* for Cake; *aghjurnà* or *mette à livellu* for update; *collisione* or *cullisione*; *focu*/*fucus* for
window focus; *ardesia* or *baina* for Deepslate; *diorite/andesite/calcite* or *-ita*; *cinabru*, *petrame*,
*lingottu*, *mola*, *cocciu*, *verruca*, *stillicciu*, *scala di manu* (concrete.md "Unresolved").
