# Minecraft Java in Corsican: language and context review (October 2026)

> **Verified 2026-10-18.** A separate AI verification checked every change proposal below against its source and applied part of them: see [APPLIED.tsv](APPLIED.tsv), [REJECTED.tsv](REJECTED.tsv) and [TRACKING.md](TRACKING.md). The text below is the proposal as written; "nothing was changed" was true when it was written.

**This is an AI review, not a speaker validation.** Nothing here has been applied to `co_fr.json` or `history.json`:
[language.tsv](language.tsv) holds proposals only. Coverage is in [tracking-language.tsv](tracking-language.tsv).
Concrete nouns (animals, plants, blocks, items, materials) belong to the parallel review (`concrete.tsv`); where a
sentence depends on such a noun, the noun was kept and the row says so.

## Method

1. Every distinct (English, Corsican) pair of 26.3 in the sentence/UI categories of `inventory.tsv` was read with
   its key (options, controls, interface, narration, subtitles, death messages, advancements, game rules, statistics,
   attributes, effects, enchantments, telemetry, debug screen, game tests, commands, Realms), plus the UI sentences
   that `inventory.tsv` files under nouns (bed messages, tooltips, item modifiers, smithing templates). Identical
   pairs under several keys were read once.
2. The older English texts of `history.json` marked `new` or `adapted` (1,422 pairs: old options, achievements,
   Twitch streaming, old commands and Realms) were read the same way, with their English recovered from the cached
   language files by hash. Entries marked `renamed` or `reused` copy a 26.3 translation and were only scanned for the
   faulty forms found in 26.3.
3. Each suspicion was checked against the whole file (is the form isolated or the majority?) and against the
   reviewed Corsican software translations in `lexicon/lexicon-mozilla.tsv` and `lexicon/lexicon-upstream.tsv`
   (Patriccollu di Santa Maria è Sichè and fellow translators), cited by line. The French and Italian 26.3 files were
   used to understand context only.
4. Placeholders and line breaks of every proposal were checked against the English with Minecraft's argument rule;
   no proposal adds, loses or renumbers an argument.

Statuses: **attested** = the proposed form is found with this sense in the reviewed lexicons (line cited);
**proposed-adaptation** = grammar, consistency or sense fix without a dictionary entry; **uncertain** = a choice a
speaker must make; **keep** = verified and kept (important everyday labels, and evidence for harmonisations).

Sources: the two reviewed lexicons above; `decisions.md`, `decisions-2.md`, `review.md`, `review-batches/` (not
redone; their open questions are not re-asked here). No ADECEC, INFCOR or other online dictionary entry was
consulted (one web search for *tonu/tronu* returned nothing usable); see the manual list below.

## Result in numbers

209 rows: 120 proposed adaptations, 45 attested corrections, 16 uncertain, 28 keep. Three rows are patterns
covering many keys (*digià*: 65 26.3 keys + 19 older; *aghjurnà*: 5 + 12; *Site sicuri*: 11 older).

## Systematic issues found

| Issue | Where | Proposal |
| --- | --- | --- |
| *digià* vs *dighjà* | 65 keys say *digià* (commands), 7 *dighjà* | *dighjà*, the only form in the reviewed lexicons (mozilla:384) |
| Polite *voi* agreement | *Site sicuri / esclusi / pronti / invitati / cunnessi* beside *Site sicuru, Vi site cunnettu, Site statu* | singular agreement, as 6 of 8 reviewed hits (upstream:1424) |
| Left/right click | *cliccu mancu* (7), *cliccu drittu* (2) beside *cliccu à manca*, *cliccu dirittu* | the attested *cliccu à manca*, *cliccu dirittu* (upstream:6005–6007) |
| *ghjunghje* used transitively | *hà ghjuntu u scopu*, *Scopu ghjuntu*, *ùn pò esse ghjuntu*, *Limita … ghjunta* | *righjunghje* (reach), already used in the file |
| Italian forms in isolated keys | *riempiutu, fallita/fallitu/fallisce, prestazioni, registrazione, esplosioni, rifiuta, schiude, schiaccia, s'annega, escludere, compiuta* | the Corsican forms the rest of the file uses (*empiutu, fiascata, perfurmenze, arregistramentu, splusioni, ricusa, si sciappa, sciaccheghja, s'anniga, esclude, compia*) |
| False friends | *inghjusta* (= unjust) for invalid; *focu* (fire) for window focus; *debule* for low disk space; *Piazza* (square) for location; *scadutu* (expired) for outdated software; *Ritornu* (return) for the movement key Back | *inaccettevule*, a description of the window state, *pocu spaziu*, *Lucalizazione*, *obsuletu*, *In daretu* |
| Agreement with a placeholder | *%s hè chjosu à chjave* breaks with feminine containers (*Cascia*) | gender-free wording |
| Mode values as verbs | structure and test block modes mix nouns (*Cantone, Fiascu*) and infinitives (*Caricà, Accettà*) | nouns |
| One term per thing | world spawn *nascita / apparizione / rinascita*; update *aghjurnà / mette à livellu*; *cuntenitore / cuntenidore*; *collisione / cullisione*; *detti / dettagliu / detaglii*; *suciali / suciale*; *saranu / seranu*; *passageri / passaghjeri*; *equipagiu / equipaghju* | per row; most follow the majority or attested form |
| Gender of option values | telemetry values *Tuttu / Minima / Nisuna*; network value *DISATTIVATU* (all capitals, masculine) quoted elsewhere as « Disattivata » | agree with the noun they qualify |

**Button convention.** STYLE.md says buttons take the infinitive. The file follows it, with one consistent exception
taken from the reviewed lexicons: *Back / Go Back* = *Ritornu* (mozilla:31, 1052), and *Done* = *Fattu*
(upstream:29). These are kept. Instructions and tutorial toasts use the *voi* imperative, as STYLE.md says.

**Abbreviations.** *FPS, GUI* (as *interfaccia*), *LAN, UUID, NBT, JFR* are kept as usual acronyms; *FOV* is already
written out (*Campu visivu*). Proposed expansions: *Altezza mass./min.* → *massima/minima*, *numeru mass*, *portata
mass* in old usage lines. Key labels (*tast. num.*, *Bloccu num*, *Sist.*) keep their keyboard abbreviations, which
follow the French and Italian keycaps and the attested *Bloccu num* (upstream:11444).

## Main decisions (see language.tsv for each key)

- Difficulty descriptions: present tense throughout (*appariscenu*), not future + present.
- *Sprint Window* tooltip rewritten (the infinitive chain was ambiguous).
- *Save and Quit to Title* → *Arregistrà è esce da a partita* (*vultà à u titulu* read as "the title" of a book).
- *Open to LAN* harmonised on *Apre à a reta lucale*.
- Game rules *Update weather / Update fire*: *Fà cambià u tempu*, *Evoluzione di u focu* (*Rinnovà* = renew).
- Death by the Wither effect names the effect, not the boss.
- *Vaccafungu munta* → *muntu* (masculine; *munta* reads as "climbs").
- Donkey and mule *angry* sounds get *annitrisce*, distinct from their ambient *raglia*.
- Realms: *Lucalizazione*, spawn protection on *puntu d'apparizione*, *Avertimentu !* for warnings.

## For a speaker or a manual dictionary check (exact entries)

1. *cullisione* or *collisione* (hitboxes, team collision rule) — ADECEC / INFCOR: *collision*.
2. *tonu* or *tronu* for thunder (`subtitles.entity.lightning_bolt.thunder`, `subtitles.item.trident.thunder`, `commands.weather.set.thunder`) — INFCOR: *tonnerre*.
3. *grugnà* or *grunghje* for grunt/oink (pig, ravager, sniffer vs baby pig, camel, armadillo) — INFCOR: *grogner*.
4. *ricoglie* or *raccoglie* in the proverb titles (`advancements.husbandry.plant_seed.title`, `advancements.adventure.blowback.title`).
5. *raghjunevule* or *ragiunevule* (`options.graphics.preset.tooltip`, `/locate` messages) — INFCOR: *raisonnable*.
6. *aghjurnà* vs *mette à livellu* for update/upgrade: one term for the whole file (Realms uses the first).
7. *Nimu pò* or *Nimu ùn pò* (`menu.multiplayerOptions.network.off.tooltip`).
8. Wind Charged effect: *Caricatu di ventu* vs keeping *Carica di ventu* (same as the item).
9. *stalattite* or *stalattita* (subtitle vs death messages) — concrete-nouns review.
10. Bee: singular *Ape* or *Apa*; every bee subtitle follows the entity name — concrete-nouns review.
11. Debug pause wording (`key.debug.focusPause`, `debug.pause_focus.*`): length must be checked in game.
12. *Rindite … pane per fucaccia* (Italian idiom) for "a taste of their own medicine".
13. Also for the concrete review: `filled_map.village_snowy` (*di e neve*), `block.minecraft.scaffolding` *Ponte* (also "bridge").

## What remains

Older `renamed`/`reused` entries were not read one by one (they reuse 26.3 translations; pattern scan only); older
noun entries are left to the concrete review; Realms legal texts were not re-read for legal meaning; no text was
seen in the game, so lengths on buttons (notably *Arregistrà è esce da a partita*, the debug pause labels) are
unchecked.
