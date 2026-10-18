# Minecraft Java: concrete vocabulary review (October 2026)

> **Verified 2026-10-18.** A separate AI verification checked every change proposal below against its source and applied part of them: see [APPLIED.tsv](APPLIED.tsv), [REJECTED.tsv](REJECTED.tsv) and [TRACKING.md](TRACKING.md). The text below is the proposal as written; "nothing was changed" was true when it was written.

**Proposals only.** Nothing in `co_fr.json`, `history.json`, `glossary.tsv`, `keys.tsv`, `inventory.tsv`, `texts/` or
`lexicon/` was changed. An AI model wrote this review by looking words up in the sources listed below. It is
**not** a speaker's validation; a second AI pass would not be one either. Every proposal waits for the maintainer
and, ideally, a Corsican speaker.

Files:

- [concrete.tsv](concrete.tsv): one row per decision (102 rows). Columns `id`, `lot`, `key(s)` (every affected name
  key; history pairs as `key@hash`), `english`, `current_co`, `proposed_co` (all distinct current forms and their
  proposed forms, in the same order), `sense_in_game`, `reference`, `justification`, `status`, `propagation`
  (counts, and the non-name texts that use the term, for the language agent).
- [tracking-concrete.tsv](tracking-concrete.tsv): lots, distinct entries, what was examined, what remains.
- This page: method, sources, the two required analyses (Pecura, Diorite), the change table, the unresolved list,
  and the texts handed to the language agent.

## Scope

Nouns of concrete things: animals and mobs as creatures, plants, wood types, rocks, ores, minerals, materials, food,
items, tools, blocks and their variants (Polished, Slab, Stairs, Wall, Smooth, Chiseled, Cracked, Mossy, coloured
families), in 26.3 first, then the names that exist only in older versions (`history.json`). Sentences, UI, actions,
subtitles, advancements and death messages belong to the language agent: when they contain one of the nouns
below, they are listed in the last section with the term to use, and the language agent applies the grammar.

Out of scope here: banner patterns (heraldry, decisions-2 D8), potion and tipped-arrow effect names, item
descriptions, music disc titles, Mojang proper names (Creeper, Nether, Redstone…).

## Method

1. **Data.** The 26.3 English (`~/.cache/corsu/minecraft/26.3/en_us.json`), French and Italian files, `co_fr.json`,
   and `history.json` joined to the English of every cached release (all 3,978 history pairs resolved, 0 missing).
   Name keys = `block.*`, `item.*`, `entity.*` (26.3: 2,308 keys, 2,198 distinct English names) plus the old
   `tile.*`, `item.*`, `entity.*` keys of the history (1,558 pairs; 190 distinct names that no longer exist in 26.3).
2. **Reading.** Every 26.3 name was read once (key, English, Corsican, French). The 16-colour families (wool,
   carpet, concrete, concrete powder, terracotta, glazed terracotta, stained glass and panes, candles, candle cakes,
   beds, banners, shulker boxes, dyes, harnesses, bundles, cushions, wool and concrete slabs/stairs) and the wood
   families were checked by script for gender/number agreement: all 21 colour families agree with their head noun.
3. **Words to check.** Each Corsican word used in a name was counted in the local Vikipedia dump; words with no or
   very few hits, and words that look Italian or French, were looked up first. Absence from a source was never taken
   as proof of an error; a word was changed only when a source gives another form **with the game's sense**, or when
   the current word has another sense in the sources (calamaru = inkwell, muscu = musk, ferraghju = February,
   creta = chalk, binariu = binary).
4. **Deduplication and propagation.** One decision per English sense; the decision is written as substitution rules
   on the Corsican text, applied (in a scratch copy only) to every text of 26.3 and every history pair, so all keys and
   versions that show the same word get the same proposal. Agreement was handled in the rules where a gender changes
   (querciu, cartella, chjudenda, pastadolce) and checked by reading the 974 resulting texts.
5. **Abbreviations.** None of the concrete names uses an abbreviation; "TNT" and "NPC/PNG" are left to their owners.

## Sources and how each was used

| Source | How it was consulted | Use |
| --- | --- | --- |
| ADECEC thematic lexicons, https://adecec.net/data/new_lessichi/html/ | 10 pages fetched once each (filage-et-tissage, chaudronnerie, la-maison, la-cuisine, la-géographie, a-frutta, oiseaux, le-temps-qu'il-fait, ghjochi-è-ghjoculi, a-caccia-in-corsica) and searched locally by French headword | priority reference; quoted entry by entry in concrete.tsv |
| INFCOR (ADECEC), https://www.adecec.net/infcor/ | 219 single-word lookups through the site's own search endpoint (`infcor/try/swift.php`, one French or Corsican headword per request, chosen by hand for a decision, 3 s apart, results cached so no word was asked twice) | headwords, variants, synonyms, French/Italian/English glosses and definitions; quoted as `INFCOR "entry"` |
| Collectivité de Corse, https://www.isula.corsica/linguacorsa/attachment/2058611/ | the PDF downloaded once and read (it is *A matina*, Ghjuvan Micheli Weber, CRDP de Corse 2013) | Cuntrastu 16 "In muntagna", p. 108: the generic sense of *pecura* |
| Local Vikipedia dump (`cowiki-latest`, already in the Corsu resources) | counts and contexts (KWIC) | usage and sense of a form; never counted as a dictionary |
| Wiktionary (kaikki dump), Apertium, `lexicon/lexicon-mozilla.tsv`, `lexicon-upstream.tsv` | local search | *ferraghju* = February (kaikki); the software lexicons contain none of the concrete nouns |
| Web search | 3 searches | Musée de la Corse / *petra uchjata*: no museum page found (see Diorite) |

INFCOR and ADECEC were used for single entries only; no page was crawled. The INFCOR lookups were issued in small
batches by a script that requests one headword at a time with a pause; the maintainer may judge whether 219 such
lookups stay within "individual pages only".

## Required analysis 1: Pecura / Muntone

**Both references verified.**

- ADECEC *Filage et tissage* (https://adecec.net/data/new_lessichi/html/filage-et-tissage.html): "brebis : pecura",
  "mouton : muntone"; the same page gives "laine : lana" and "ciseaux (à tondre) ou forces : furbice".
- *A matina* (isula.corsica attachment 2058611), Cuntrastu 16 "In muntagna", Vucabulariu: "A pecura : La brebis en
  particulier. Génériquement, « pecura » désigne les moutons du troupeau : una banda di pecure/i (un troupeau de
  moutons). Le berger de moutons est u pecuraghju / picuraghju, le petit l'agnellu / agneddu, le bélier est
  l'arghjetu, le mouton u muntone/i." The dialogue of the same unit translates "più furzacute chè e pecure" as
  "plus forts que les moutons".
- INFCOR *pecura*: FR "brebis, mouton, ovin"; definition "Femina di u muntone dumesticu … allevata pè u so latte, a
  so lana è ancu a so carne. – Estens. L'inseme di a sterpa pecurina"; synonyms *ovinu, muntone*. INFCOR *muntone*:
  FR "mouton; mouton mâle châtré; bélier", synonym "pecura (Sudu)".

**Sense in Minecraft.** Sheep is the species: one mob for both sexes, lambs ("baby sheep"), sheared for wool, eaten as
mutton. That is the generic sense the three sources give to *pecura*.

**Decision.** *Pecura* is **kept** (A01): it is correct and attested in its generic use; it is not an error.
*Muntone* would also be correct (generic *mouton*), but switching brings nothing. Separately:

- mob `entity.minecraft.sheep` and history `entity.Sheep.name`: *Pecura*, keep;
- spawn egg `item.minecraft.sheep_spawn_egg`: *Ovu generatore di pecura*, keep (A03);
- meat `item.minecraft.mutton` / `cooked_mutton` (and history `item.muttonRaw.name`, `item.muttonCooked.name`):
  *Castratu crudu / cottu*, keep (A02): INFCOR *castratu* gives "Porcu o muntone castratu: carne di castratu".
  Alternative for a speaker: *Carne pecurina cruda / cotta* (ADECEC la-cuisine "Haricot de mouton : tianu di pomi è
  carne pecurina");
- subtitles `subtitles.entity.sheep.*`: term *pecura* (f.) for the language agent; current agreement is right;
- wool: *lana* (all 16 colours + slabs + stairs) and shears *forbice* keep (M05). *Forbice* is an INFCOR variant of
  *furbici* (EN shears); the ADECEC spinning lexicon writes *furbice*; a speaker may prefer it.

## Required analysis 2: Diorite and the words left identical to French

**Diorite.** The current *Diorite* is the French form. Checked:

- *diurita* (the proposal to check): one Vikipedia hit, "scalinati in diurita nera", in a southern-spelling text;
- *diorita*: used by INFCOR in the definition of *petra uchjata*: "petra ochjata, petra uchjata, petra occhiata —
  FR diorite orbiculaire — GEOLUGIA. Varietà di diorita sfruttata in Corsica". Not an INFCOR headword;
- *petra uchjata* is the **orbicular diorite**, a particular Corsican variety (Santa Lucia di Tallà; INFCOR above,
  Vikipedia article "Petra uchjata"). It must not replace the generic term: Minecraft's Diorite is ordinary diorite.
  The Musée de la Corse attribution given in the task could not be confirmed: no museum page with that name was
  found by web search (the Google Arts & Culture orbicular diorite is a Smithsonian specimen).

Proposal R01: **Diorita** (Diorita lisciata, Lastra / Scala / Muru di diorita), status *attested-borrowing*: a learned
borrowing found in a Corsican dictionary's own definition, with the northern spelling; *diurita* is the attested
southern variant. Feminine like *diorite*, so no agreement changes.

**Other words identical to French or Italian, classified.**

| Word now | Class | Proposal |
| --- | --- | --- |
| Diorite, Andesite, Calcite | French form; Corsican texts write *diorita*, *andesita/andesiti*, *calcita* | attested-borrowing (R01–R03) |
| Granitu, Basaltu, Quarzu, Zolfu, Ossidiana, Ametista, Smeraldu, Magma, Lava | Corsican forms, in INFCOR or ADECEC | keep (R08) |
| Tufu | in Vikipedia for the rock; ADECEC géographie writes *tofu*; INFCOR *tufu* = "dive" | keep, flagged (R09) |
| Terracotta | identical to Italian, but an INFCOR headword | keep (M08) |
| Lapislazuli | INFCOR *lapislazzuli* | attested spelling (R10) |
| Arenaria | Italian rock name; in Corsican texts the plant genus | *Petra rinaghja* (R05, INFCOR EN sandstone) |
| Ardesia (Deepslate) | Italian; Corsican slate is *baina* | *Baina prufonda*, proposed adaptation (R04) |
| Creta (Clay) | Corsican *creta* = chalk | *Arzilla* (R07, INFCOR EN clay) |
| Betonu | not found; ADECEC béton = *cimentu* | *Cimentu* (M02) |
| Cinabru, Prismarina, Netherite, Purpur, Podzol, Miceliu | invented or technical names | cinabru unresolved (R11); others kept as names |
| Acacia, Azalea, Bambù, Cactus, Panda, Lama | international names; *bambù* is an INFCOR headword | keep |

A Corsican-looking ending was not taken as validation: *ghjàira, betonu, steccatu, bodula, tintura, pisciacane,
ancùdina, capirossulu, custuletta, cuiaghju* all look Corsican and none was found in any source.

## Proposed changes

Counts: **102 decisions** (each a distinct English sense, propagated to all its keys and versions):
43 attested, 4 attested-borrowing, 3 proposed-adaptation, 8 unresolved (no change proposed), 44 keep (checked and
confirmed). The 50 change decisions touch **974 texts**: 582 name keys of 26.3 and 271 history pairs (concrete
names), plus 102 texts of 26.3 and 19 history pairs owned by the language agent (subtitles, advancements, stats,
death messages, options).

Gender changes that need agreement: oak *quercia* (f) → *querciu* (m); sign *cartellu* (m) → *cartella* (f); fence
*steccatu* (m) → *chjudenda* (f); cake *torta* (f) → *pastadolce* (m). Each is handled in the rules
(Querciu scuru, Cartella appesa murale distorta, Chjudenda distorta, "un pastadolce"). Other changes keep the gender.

| id | English | current → proposed (main form) | status | name keys (26.3 + history) | other texts for the language agent |
| --- | --- | --- | --- | --- | --- |
| A04 | Squid / Glow Squid | Calamaru → Totanu | attested | 4 + 1 | 8 |
| A05 | Bee | Ape → Apa | attested | 2 + 0 | 9 |
| A06 | Camel / Camel Husk | Cammellu → Camellu | attested | 4 + 0 | 18 |
| A07 | Tadpole | Capirossulu → Cudutu | attested | 3 + 0 | 7 |
| F01 | Melon / Melon Slice / Melon Seeds / Melon Stem / Glistering Melon | Pateca → Patecca | attested | 6 + 4 | 0 |
| F02 | Porkchop (Raw / Cooked) | Custuletta di porcu cotta → Custelletta di porcu cotta | attested | 2 + 2 | 0 |
| F03 | Cocoa / Cocoa Beans | Cacau → Caccaò | attested | 2 + 2 | 0 |
| F04 | Cake / Cake with Candle (+16 coloured candle cakes) | Torta → Pastadolce | attested | 18 + 2 | 4 |
| F05 | Sweet Berries / Glow Berries / Sweet Berry Bush | Baghe dolce → Baghi dolci | proposed-adaptation | 3 + 0 | 5 |
| P01 | Oak (all oak, dark oak, pale oak, petrified oak variants) | quercia → querciu (m): Quercia scura → Querciu scuru, Lastra di quercia petrificata → Lastra di querciu petrificatu | attested | 76 + 21 | 1 |
| P02 | Birch (all birch variants) | betula → biolu | attested | 25 + 10 | 0 |
| P03 | Spruce (all spruce variants) | abete → abetu | attested | 25 + 10 | 0 |
| P04 | Cherry (all cherry variants, Cherry Grove biome) | cirasgiu → chjarasgiu | attested | 28 + 0 | 0 |
| P06 | Moss / Moss Block / Moss Carpet / Pale Moss / Mossy X | Petra muscosa → Petra murzosa | attested | 14 + 4 | 0 |
| P07 | Dandelion / Golden Dandelion / Dandelion Yellow (old) | Pisciacane → Radichju | attested | 4 + 3 | 2 |
| P08 | Poppy | Pàparu → Pappaveru | attested | 2 + 1 | 0 |
| P09 | Cornflower | Fiurdalisu → Turchinellu | attested | 2 + 0 | 0 |
| P10 | Rose Bush | Rusaghju → Rosulaghju | attested | 1 + 1 | 0 |
| P11 | Peony | Peonia → Pigonia | attested | 1 + 1 | 0 |
| P12 | Lilac | Lilà → Lillà | attested | 1 + 1 | 0 |
| P13 | Lily Pad | Foglia di ninfea → Nenufaru | attested | 1 + 1 | 0 |
| R01 | Diorite (Diorite, Polished Diorite, slabs, stairs, walls) | Diorite → Diorita | attested-borrowing | 7 + 2 | 0 |
| R02 | Andesite (and variants) | Andesite → Andesita | attested-borrowing | 7 + 2 | 0 |
| R03 | Calcite | Calcite → Calcita | attested-borrowing | 1 + 0 | 0 |
| R04 | Deepslate (all deepslate blocks, ores, tiles, bricks) | Ardesia prufonda → Baina prufonda | proposed-adaptation | 30 + 0 | 0 |
| R05 | Sandstone / Red Sandstone (cut, chiseled, smooth, slabs, stairs, walls) | Arenaria → Petra rinaghja | attested | 20 + 12 | 0 |
| R06 | Gravel / Suspicious Gravel | Ghjàira → Gravetta | attested | 3 + 3 | 2 |
| R07 | Clay / Clay Ball / Hardened & Stained Clay (old Terracotta) / Clayfish | Creta → Arzilla | attested | 3 + 38 | 0 |
| R10 | Lapis Lazuli (item, block, ores) | Lapislazuli → Lapislazzuli | attested-borrowing | 6 + 5 | 1 |
| R11 | Cinnabar (26.x) | cinabru (unchanged) | unresolved | 13 + 0 | 0 |
| R12 | Cobblestone (and variants) | petrame (unchanged) | unresolved | 13 + 6 | 1 |
| M01 | Brick / Bricks (all brick blocks, Nether/Mud/Stone/Resin/Tuff/... bricks) | Matone → Mattone | attested | 72 + 23 | 0 |
| M02 | Concrete / Concrete Powder (16 colours each, slabs, stairs) | betonu → cimentu (Betonu neru → Cimentu neru) | attested | 64 + 32 | 0 |
| M03 | Carpet (16 colours, Moss Carpet, Pale Moss Carpet; old "Carpet") | Tappetu → Tappettu | attested | 18 + 18 | 1 |
| M04 | Dye (16 colours) | Tintura nera → Tinta nera | attested | 16 + 9 | 1 |
| M07 | Glass Pane / Stained Glass Pane | Pannellu di vetru → Vetru di finestra | attested | 17 + 18 | 0 |
| M11 | Ingot (iron, gold, copper, netherite) | lingotti, lingottu (unchanged) | unresolved | 8 + 4 | 5 |
| B01 | Trapdoor (all wood, copper, iron trapdoors) | Bodula → Caterazza | attested | 22 + 3 | 9 |
| B02 | Fence (all wood fences, Nether Brick Fence; old "Fence") | Steccatu (m) → Chjudenda (f): Steccatu distortu → Chjudenda distorta | attested | 14 + 8 | 0 |
| B04 | Sign / Hanging Sign / Wall Sign / Wall Hanging Sign (all woods) | Cartellu (m) → Cartella (f): Cartellu appesu → Cartella appesa | attested | 53 + 4 | 9 |
| B05 | Anvil / Chipped / Damaged (old: Slightly, Very Damaged) | Ancùdina → Incudine | attested | 3 + 4 | 7 |
| B06 | Smithing Table; Toolsmith (villager); old "Tool Smith" | Bancu di ferraghju → Bancu di stazzunaru | proposed-adaptation | 2 + 2 | 5 |
| B07 | Hopper / Minecart with Hopper | Tramoghja → Trimoghja | attested | 4 + 4 | 2 |
| B08 | Lectern | Leghju → Pulpitru | attested | 2 + 0 | 1 |
| B09 | Sponge / Wet Sponge | Sponga → Spunga | attested | 2 + 3 | 2 |
| B11 | Grindstone | mola (unchanged) | unresolved | 1 + 0 | 2 |
| B13 | Pottery Sherd (all 23) | cocciu (unchanged) | unresolved | 47 + 0 | 2 |
| I01 | Minecart (and all Minecart with X; old container names) | Carrettu → Vagunettu | attested | 13 + 13 | 14 |
| I02 | Bamboo Raft / with Chest | Zatta di bambù → Zattera di bambù | attested | 4 + 0 | 0 |
| I03 | Boots (all materials) | Stivali d'oru → Stifali d'oru | attested | 7 + 5 | 0 |
| I04 | Lead / Leash Knot | Ligaccia → Catinetta | attested | 2 + 1 | 11 |
| I05 | Clock (item) | Orologhju → Orillogiu | attested | 1 + 1 | 0 |
| U01 | Nether Wart | verruca (unchanged) | unresolved | 2 + 2 | 0 |
| U03 | Dripstone / Pointed Dripstone | stillicciu (unchanged) | unresolved | 3 + 0 | 0 |
| U05 | Ladder | scala di manu (unchanged) | unresolved | 1 + 1 | 1 |
| B14 | Torch (wall, redstone, soul, copper torches; Torchflower) | Torcia → Torchja | attested | 12 + 2 | 1 |
| B15 | Rail / Powered / Detector / Activator Rail | Binariu → Ragliu | attested | 4 + 4 | 0 |
| A16 | Leatherworker (villager) | Cuiaghju → Cunciadore | attested | 1 + 1 | 1 |

Notes on the weaker proposals (a speaker should look at these first):

- **P07 Dandelion → Radichju**: ADECEC la-cuisine and INFCOR give *radichju* = pissenlit (EN dandelion, Taraxacum),
  but the Corsican Vikipedia article *Radichju* is the radish. Other INFCOR names: *strigliulu*, *erbiglia*, *lumera*.
- **R02 Andesita, R03 Calcita**: two Vikipedia hits each at most; no dictionary entry.
- **F05 Baghi**: the plural *baghi* is used in Vikipedia, the singular *bacu/bagu* (m) in ADECEC a-frutta is first of
  all the arbutus berry.
- **R04 Baina prufonda**: built name for an invented block; *baina* is well attested for slate.
- **B06 Bancu di stazzunaru**: the current *ferraghju* is certainly February; *stazzunaru* (INFCOR forgeron) is sure,
  the compound is built. *Ferrale* (INFCOR EN smith, blacksmith) is the alternative.
- **B02 Chjudenda**: ADECEC gives it for clôture/fencing; INFCOR also has *serrenda*, *palancatu* (palisade),
  *cataru* (field gate, barrier).
- **I05 Orillogiu**: INFCOR headword; the same word in `commands.time.*` (game timeline clocks) is the language
  agent's choice.
- **B04 Cartella**: INFCOR glosses it EN "placard, sign" but also "schoolbag, file card".

## Unresolved: entries to consult by hand

| id | Game entry | Current | Exact entries to look up | What is known |
| --- | --- | --- | --- | --- |
| R11 | Cinnabar, Chiseled/Polished Cinnabar, Cinnabar Bricks… (26.x) | Cinabru | INFCOR / a geology text: "cinabre", "cinabru", "cinnabaru" | INFCOR has no "cinabre"; Vikipedia 0 |
| R12 | Cobblestone and all variants (19 keys) | Petrame | INFCOR: "petrame", "pétraille", "pierraille"; ADECEC la-maison "moellon" | INFCOR has *carcacoda* (moellon, EN rubble stone), *roccaglia* (rocaille) |
| M11 | Iron/Gold/Copper/Netherite Ingot; "Ingots & Crystals" | Lingottu | INFCOR "lingot" (no entry); a metalwork glossary | ADECEC chaudronnerie "lingot : asta, astone" |
| B11 | Grindstone | Mola | INFCOR "meule", "meule à aiguiser", "affûtoir" | INFCOR *mola* = lineage only; *pisana* (pierre/meule à aiguiser), *arrutinu* (remouleur; meule à aiguiser) |
| B13 | Pottery Sherd (23 kinds) | Cocciu di vasu | INFCOR "tesson", "débris de poterie", "cocciu" | INFCOR *cocciu* = a fish only; no "tesson" entry |
| U01 | Nether Wart | Verruca di u Nether | INFCOR "verrue", "porru" (decisions.md Q9) | not consulted again here |
| U03 | Dripstone Block, Pointed Dripstone | Stillicciu | INFCOR "stalagmite", "concrétion" | INFCOR *stalattita* (stalactite), *candeleru* |
| U05 | Ladder | Scala di manu | INFCOR "échelle à main", "scaletta" | ADECEC la-maison "Echelle: scala, scaletta"; *scala* alone = Stairs |

Also for a speaker, among the kept words: A02 *castratu* vs *carne pecurina*; A08 *ghjallina* vs *pullastru* for the
meat; A09 *merluzzu* vs *laverdone* (INFCOR EN cod); A14 *strega* vs *moca* (INFCOR sorcière); B12 *faru* vs
*stantella* (INFCOR EN beacon); M05 *forbice* vs *furbice*; M09 *muru* vs *murellu* (ADECEC "muret") for the game's
low walls; P21 *arbustu* vs *arburellu* (ADECEC "arbuste"); R09 *tufu* vs *tofu*; F06 *barbabietula* vs
*bieterava*; F08 *zucca* vs *zuccu* (ADECEC "citrouille"); professions not checked: Butcher *macellaghju* (INFCOR
gives *acciaccadore*, *ammazzadore*), Fletcher, Librarian, Cartographer, Nitwit.

## Possible clashes created or removed

- Removed: *binariu* (rail) also meant "binary" (`key.keyboard.keypad.binary`, `snbt.parser.expected_binary_numeral`);
  *calamaru* (squid) is the inkwell; *muscu* (moss) is musk; *ferraghju* is February; *creta* is chalk.
- Created: *tinta* (dye, noun) next to the participle *tinta* ("Arzilla tinta" = stained clay, old versions) — same
  word family, different function, judged acceptable. *Botte* was avoided for Boots because INFCOR *botte* is also
  the barrel; *stifali* (INFCOR synonym) is proposed instead.
- None of the proposed words is used elsewhere in `co_fr.json` today (checked for all 27 new words).

## Kept after checking

| id | English | Corsican kept | main reference |
| --- | --- | --- | --- |
| A01 | Sheep | pecura | ADECEC filage-et-tissage.html "brebis : pecura", "mouton : muntone"; https://www.isula.corsica/linguacorsa/attachment/2058611/ (A matina, G. M. Weber, CRDP Corsica 2013, Cuntrastu 16 "In muntagna", Vucabulariu p. 108) "A pecura : … |
| A02 | Raw Mutton / Cooked Mutton | castratu | INFCOR "castratu" (DEF "Porcu o muntone castratu: carne di castratu"); INFCOR "picurinu/pecurinu" (FR "odeur ou viande de mouton"); ADECEC la-cuisine.html "Haricot de mouton : tianu di pomi è carne pecurina" |
| A03 | Sheep Spawn Egg; sheep subtitles | pecura | see A01 |
| A08 | Chicken (mob) / Raw, Cooked Chicken | ghjallina | INFCOR "gallina / ghjallina" (FR poule; EN hen); ADECEC la-cuisine.html "poule : gallina, ghj-", "poulet : pullastru" |
| A09 | Cod / Raw Cod / Cooked Cod | merluzzu | INFCOR "baccalà" (DEF "Merluzzu salitu è seccatu"; FR morue); INFCOR "merluzzu" (FR merlu, merluche, colin; EN hake); INFCOR "laverdone" (FR cabillaud, églefin; EN cod) |
| A10 | Bat | topu pinnutu | INFCOR "topu pinnutu" (FR chauve-souris); local Vikipedia dump cowiki-latest (corsican_words.py resources), topu pinnutu 37 |
| A11 | Donkey | sumere | INFCOR "prisoghju" (FR âne; SIN sumere, asinu); local Vikipedia dump cowiki-latest (corsican_words.py resources), sumere 66 |
| A12 | Rabbit; Raw/Cooked Rabbit | cunigliulu | INFCOR "cunigliu / cunigliulu" (FR lapin); ADECEC la-cuisine.html "lapin : cunigliu, -ulu" |
| A13 | Cat / Wolf / Fox / Pig / Cow / Horse / Mule / Goat / Frog / Turtle / Dolphin / Spider / Skeleton / Polar Bear / Salmon / Parrot | capra, cavallu, delfinu, ghjattu, granochja, lupu, mulu, orsu, pappagallu, porcu, ragnu, salmone, scheletru, tartaruga, vacca, volpe | INFCOR entries ghjattu (EN cat), lupu (loup), volpe (renard), porcu (porc), vacca (vache, EN cow), cavallu (cheval), mulu (mulet), capra (EN goat), ranochja/granochja (grenouille), tartaruga (EN turtle), delfinu (dauphin), aragnu/… |
| A14 | Witch | strega | INFCOR "moca" (FR sorcière), "strigà/stregà" (FR ensorceler); local Vikipedia dump cowiki-latest (corsican_words.py resources), strega 54 |
| A15 | Raw Beef / Steak | bistecca, manzu | INFCOR "manzu / mansu" (FR bouvillon); ADECEC la-cuisine.html "bifteck : bistecca", "bœuf : boie" |
| F06 | Beetroot / Beetroots / Beetroot Seeds / Soup | barbabietula, barbabietule | INFCOR "barbabietula" (FR betterave); ADECEC la-cuisine.html "betterave : bieterava, -avana" |
| F07 | Seeds (Wheat, Beetroot, Melon, Pumpkin, Torchflower) | sumente | INFCOR "sumenta / sementa / sumente" (FR semence, n.f.) |
| F08 | Pumpkin / Carved Pumpkin / Pumpkin Pie | zucca | ADECEC la-cuisine.html "courge : zucca", "citrouille : zuccu"; ADECEC a-frutta.html "zucca : courge" |
| F09 | Bread / Cookie / Apple / Carrot / Potato / Wheat / Sugar / Honey / Egg / Milk / Rotten Flesh / Bowl / Stew | biscottu, carne fracica, carotta, granu, latte, mela, mele, ovu, pane, patata, scudella, stufatu, zuccheru | ADECEC la-cuisine.html "pain : pane", "biscuit : biscottu", "pomme : mela", "carotte : carotta", "patate : patata", "blé : granu", "miel : mele", "œuf : ovu", "lait : latte", "gâté : guastu, merciu, fracicu", "écuelle : scudella",… |
| F10 | Hay Bale / Straw Bed | fenu, paglia | INFCOR "fenu" (FR foin; EN hay), "paglia" (FR paille; EN straw) |
| P05 | Poplar / Acacia / Mangrove / Jungle / Bamboo | acacia, bambù, giungla, mangrovia, piobbu | INFCOR "piopu / piobu / piobbu" (FR peuplier), "bambù" (EN bamboo) |
| P14 | Fern / Large Fern | filetta | INFCOR "filetta / filettu" (FR fougère; EN fern) |
| P15 | Sunflower / Oxeye Daisy / Lily of the Valley / Tulips | girasole, margarita, mughettu, tulipanu | INFCOR "girasole" (FR tournesol), "margarita" (FR marguerite), "mughettu" (FR muguet), "tulipanu" (FR tulipe) |
| P16 | Kelp / Dried Kelp / Seagrass | alga | INFCOR "alga / aliga" (FR algue; EN alga) |
| P17 | Sapling (all) | pianticella | INFCOR "pianticella" (FR petite ou jeune plante) |
| P18 | Stripped Log / Wood / Stem / Hyphae | scurzate, scurzatu | INFCOR "scurzatu" (FR écorcé; DEF "Chì ùn hà più scurza") |
| P19 | Glow Lichen | lichene | INFCOR "lichenu / lichene" (FR lichen); ADECEC filage-et-tissage.html "lichen : licchenu" |
| P20 | Vines / Cave Vines / Weeping / Twisting Vines | liane | INFCOR "liana" (FR liane; EN creeper) |
| P21 | Bush / Dead Bush / Firefly Bush / Sweet Berry Bush | arbustu | ADECEC la-g%C3%A9ographie.html "arbuste : arburellu"; local Vikipedia dump cowiki-latest (corsican_words.py resources), arbustu 76 (decisions-2 D6) |
| P22 | Sugar Cane | canna da zuccheru | local Vikipedia dump cowiki-latest (corsican_words.py resources), "canna da zuccheru" 5 hits |
| R08 | Granite / Basalt / Quartz / Sulfur / Obsidian / Amethyst / Emerald / Diamond / Coal / Iron / Gold / Copper / Sand / Stone / Dirt / Mud / Snow / Ice / Lava / Magma / Coral / Ore | ametista, basaltu, carbone, curallu, diamante, fangu, ferru, ghjacciu, granitu, lava, magma, minerale, neve, oru, ossidiana, petra, quarzu, ramu, rena, smeraldu, terra, zolfu | INFCOR granitu (EN granite), basaltu (EN basalt), quarzu (quartz), zolfu (soufre), ossidiana (obsidienne), amatista/ametista (EN amethyst), smeraldu (émeraude); ADECEC la-g%C3%A9ographie.html "charbon : carbone", "fer : ferru", "o… |
| R09 | Tuff (and variants) | tufu | local Vikipedia dump cowiki-latest (corsican_words.py resources), tufu 10 (rock sense, Etruscan building); ADECEC la-g%C3%A9ographie.html "Tuf : tofu"; INFCOR "tuffu / tufu" (FR plongeon) |
| M05 | Wool (16 colours, slabs, stairs) / Shears | forbice, lana | INFCOR "lana" (FR laine); ADECEC filage-et-tissage.html "laine : lana", "ciseaux (à tondre) ou forces : furbice"; INFCOR "furbici / forbici / furbice / forbice" (FR ciseaux, cisailles; EN shears) |
| M06 | Glass / Stained Glass / Tinted Glass | vetru | ADECEC la-cuisine.html "verre : vetru"; ADECEC la-maison.html "Vitre: vetru - pane" |
| M08 | Terracotta / Glazed Terracotta | terracotta | INFCOR "terracotta" (FR terre cuite); "smaltu" (FR émail) |
| M09 | Planks / Log / Wood / Slab / Stairs / Wall / Door / Ladder | lastra, legnu, muru, porta, scala, tavule, troncu | ADECEC la-maison.html "Planche: tavula - board, plank", "Dalle: teghja, lastra", "Escalier: scala", "Echelle: scala, scaletta", "Muret, muretin: murellu, muretta"; ADECEC la-g%C3%A9ographie.html "bois : legnu"; INFCOR "ceppu" (EN … |
| M10 | Leather / Leather armour | coghju | INFCOR "curazza" (DEF "a curazza di coghju o di ramu") |
| M12 | Nugget | pepita | INFCOR "pepita / pipita" (FR pépite; EN nugget) |
| B03 | Fence Gate | cancellu | INFCOR "cancellu" (DEF "Porta fatta d'aste di legnu o di ferru dispaziate è adunite da traverse") |
| B10 | Cauldron / Brewing Stand / Barrel / Chest / Beehive / Honeycomb / Scaffolding / Lodestone / Lever / Lantern / Candle / Bell / Furnace | barile, bugnu, calamita, campana, candela, cascia, favu, fornu, lambiccu, lanterna, leva, paghjolu, ponte | INFCOR "paghjola / paghjolu" (FR chaudron; EN cauldron), "lambiccu" (FR alambic), "barile" (EN barrel), "cofanu" (SIN cascia), "bugna / bugnu" (FR ruche), "favu" (FR rayon de miel), "ponte" (FR échafaudage), "calamita" (aimant; ox… |
| B12 | Beacon | faru | INFCOR "stantella" (FR balise; EN beacon); local Vikipedia dump cowiki-latest (corsican_words.py resources), faru 6 (lighthouse) |
| I06 | Helmet / Chestplate / Leggings / Pickaxe / Shovel / Hoe / Axe / Sword / Shield / Bow / Crossbow / Arrow / Saddle / Compass / Brush / Spyglass / Bucket / Bottle / Stick / Feather / String / Bone / Book / Paper / Map / Name Tag / Flint / Flint and Steel / Scute | accetta, acciarinu, arcu, balestra, bastone, bussula, buttiglia, cannuchjale, carta, curazza, elmu, etichetta, filu, freccia, gambali, libru, ossu, pala, petra fucaghja, piccone, pinnellu, piuma, scaglia, scudu, secchja, sella, spada, zappa | INFCOR elmu (FR casque), curazza (EN armour-plating), gambale (FR jambière; "prutezzione metallica pè copre a gamba"), piccone (FR pic-pioche), pala (EN shovel), zappa (FR pioche, houe), bussula (EN compass), pinnellu (EN brush), … |
| I07 | Smithing Template | mudellu di forgia | ADECEC chaudronnerie.html "forge (atelier) : stazzona - (fourneau) : forge" |
| U02 | Allium | agliu salvaticu | INFCOR "agliu" (FR ail) |
| U04 | Armadillo / Ocelot / Llama / Panda / Axolotl | armadillu, axolotl, lama, ocelot, panda | none (international animal names) |
| U06 | Cactus / Mushroom / Azalea / Bamboo / Mycelium / Podzol | azalea, cactus, fungu, miceliu, podzol | ADECEC la-cuisine.html "champignon : fungu" |
| A17 | Armorer / Weaponsmith / Mason / Shepherd / Fisherman / Cleric | armaghjolu, muratore, pastore, piscadore, prete | INFCOR "armaghjolu" (FR armurier; EN armourer), "muratore" (FR maçon; EN mason), "pastore" (FR berger; EN shepherd), "piscadore" (FR pêcheur; EN fisherman) |
| B16 | Bed (16 colours) / Banner (16 colours) / Chain / Roots / Item Frame | catena, curnice, lettu, radiche, stendardu | INFCOR "sciloffu" (FR lit; SIN lettu), "stendardu" (FR étendard: "Bandera di regimentu ... di cunfraternità"), "radica / radice" (FR racine; EN root); ADECEC la-maison.html "Chaîne: catena" |

## For the language agent: terms and the texts that use them

Terms (gender for agreement): *totanu* (m, squid), *apa* (f, one bee; plural *ape* unchanged), *camellu* (m),
*cudutu* (m, tadpole), *pastadolce* (m, cake), *baghi* (m pl, berries), *querciu* (m), *murzu* (m) / *murzosu*,
*radichju* (m), *gravetta* (f), *arzilla* (f), *mattone/i* (m), *cimentu* (m), *tappettu* (m), *tinta* (f, dye),
*caterazza* (f, trapdoor), *chjudenda* (f, fence), *cartella* (f, sign), *incudine* (f, anvil), *stazzunaru* (m),
*trimoghja* (f, hopper), *pulpitru* (m, lectern), *spunga* (f), *vagunettu* (m, minecart), *catinetta* (f, lead),
*orillogiu* (m, clock), *torchja* (f), *ragliu* (m, rail), *cunciadore* (m, leatherworker), *lapislazzuli*. Also: the
singular of seeds *sumenta* is attested (INFCOR "sumenta / sementa / sumente"), which answers decisions-2 D5.

These 121 texts outside the names use one of the changed nouns. The proposed text below only swaps the noun (and
its article and adjective where the gender changes); the grammar, the verb and the final wording are yours.

| key | current | proposed | decision |
| --- | --- | --- | --- |
| `achievement.onARail.desc@ee6e91ec2be5` | Viaghjate in carrettu almenu 1 km da u vostru puntu di partenza | Viaghjate in vagunettu almenu 1 km da u vostru puntu di partenza | I01 |
| `advancements.adventure.heart_transplanter.description` | Piazzate un core di scricchjone cù l'allineamentu currettu trà dui tronchi di quercia pallida | Piazzate un core di scricchjone cù l'allineamentu currettu trà dui tronchi di querciu pallidu | P01 |
| `advancements.adventure.trim_with_any_armor_pattern.description` | Fabbricate un'armatura rifinita nant'à un bancu di ferraghju | Fabbricate un'armatura rifinita nant'à un bancu di stazzunaru | B06 |
| `advancements.adventure.trim_with_any_armor_pattern.description@a1cf89c53770` | Fabbricate un'armatura rifinita nant'à un bancu di ferraghju | Fabbricate un'armatura rifinita nant'à un bancu di stazzunaru | B06 |
| `advancements.husbandry.allay_deliver_cake_to_note_block.description` | Fate chì un Allay lasci una torta vicinu à un bloccu musicale | Fate chì un Allay lasci un pastadolce vicinu à un bloccu musicale | F04 |
| `advancements.husbandry.leash_all_frog_variants.description` | Tinite ogni varietà di granochja à a ligaccia | Tinite ogni varietà di granochja à a catinetta | I04 |
| `advancements.husbandry.make_a_sign_glow.description` | Fate brillà u testu di qualunque tipu di cartellu | Fate brillà u testu di qualunque tipu di cartella | B04 |
| `advancements.husbandry.make_a_sign_glow.description@00e3d13c49d0` | Fate brillà u testu d'un cartellu | Fate brillà u testu d'una cartella | B04 |
| `advancements.husbandry.make_a_sign_glow.description@619fa27f50e5` | Fate brillà u testu d'un cartellu | Fate brillà u testu d'una cartella | B04 |
| `advancements.husbandry.tadpole_in_a_bucket.description` | Chjappate un capirossulu cù una secchja | Chjappate un cudutu cù una secchja | A07 |
| `dataPack.minecart_improvements.description` | Muvimentu migliuratu per i carretti | Muvimentu migliuratu per i vagunetti | I01 |
| `dataPack.minecart_improvements.name` | Migliuramenti di i carretti | Migliuramenti di i vagunetti | I01 |
| `death.attack.anvil` | Un'ancùdina chì cascava hà sciacciatu à %1$s | Un'incudine chì cascava hà sciacciatu à %1$s | B05 |
| `death.attack.anvil.player` | Un'ancùdina chì cascava hà sciacciatu à %1$s mentre luttava contr'à %2$s | Un'incudine chì cascava hà sciacciatu à %1$s mentre luttava contr'à %2$s | B05 |
| `death.attack.anvil.player@9c67b0ff72f9` | Un'ancùdina chì cascava hà sciacciatu à %1$s mentre luttava contr'à %2$s | Un'incudine chì cascava hà sciacciatu à %1$s mentre luttava contr'à %2$s | B05 |
| `death.attack.sweetBerryBush` | Un arbustu di baghe dolce hà tombu à %1$s à punture | Un arbustu di baghi dolci hà tombu à %1$s à punture | F05 |
| `death.attack.sweetBerryBush.player` | Un arbustu di baghe dolce hà tombu à %1$s à punture mentre scappava da %2$s | Un arbustu di baghi dolci hà tombu à %1$s à punture mentre scappava da %2$s | F05 |
| `death.attack.sweetBerryBush.player@52afa74f007f` | Un arbustu di baghe dolce hà tombu à %1$s à punture mentre scappava da %2$s | Un arbustu di baghi dolci hà tombu à %1$s à punture mentre scappava da %2$s | F05 |
| `gamerule.doEntityDrops.description` | Decide ciò chì lascianu i carretti (cumpresu u so inventariu), e curnice, e barche, ecc. | Decide ciò chì lascianu i vagunetti (cumpresu u so inventariu), e curnice, e barche, ecc. | I01 |
| `gamerule.doEntityDrops.description@31def2c11127` | Decide ciò chì lascianu i carretti (cumpresu u so inventariu), e curnice, e barche, ecc. | Decide ciò chì lascianu i vagunetti (cumpresu u so inventariu), e curnice, e barche, ecc. | I01 |
| `gamerule.minecartMaxSpeed` | Velocità massima di i carretti | Velocità massima di i vagunetti | I01 |
| `gamerule.minecartMaxSpeed.description` | Velocità massima predefinita d'un carrettu chì si move in terra. | Velocità massima predefinita d'un vagunettu chì si move in terra. | I01 |
| `hanging_sign.edit` | Mudificà u messaghju di u cartellu appesu | Mudificà u messaghju di a cartella appesa | B04 |
| `options.rotateWithMinecart` | Girà cù i carretti | Girà cù i vagunetti | I01 |
| `options.rotateWithMinecart.tooltip` | S'è a vista di u ghjucadore deve girà cù un carrettu chì gira. Dispunibule solu in i mondi induve u parametru esperimentale « Migliuramenti di i carretti » hè attivatu. | S'è a vista di u ghjucadore deve girà cù un vagunettu chì gira. Dispunibule solu in i mondi induve u parametru esperimentale « Migliuramenti di i vagunetti » hè attivatu. | I01 |
| `sign.click_actions_disabled` | L'azzioni di cliccu sò disattivate per stu cartellu | L'azzioni di cliccu sò disattivate per sta cartella | B04 |
| `sign.edit` | Mudificà u messaghju di u cartellu | Mudificà u messaghju di a cartella | B04 |
| `sign.edit@8bd8fc0ef5e0` | Mudificà u messaghju di u cartellu | Mudificà u messaghju di a cartella | B04 |
| `stat.cakeSlicesEaten@7f6e73d406ba` | Fette di torta manghjate | Fette di pastadolce manghjate | F04 |
| `stat.hopperInspected@bbce03b463f8` | Tramoghje frugate | Trimoghje frugate | B07 |
| `stat.minecartOneCm@1cd84e2710a4` | Distanza in carrettu | Distanza in vagunettu | I01 |
| `stat.minecraft.eat_cake_slice` | Fette di torta manghjate | Fette di pastadolce manghjate | F04 |
| `stat.minecraft.inspect_hopper` | Tramoghje frugate | Trimoghje frugate | B07 |
| `stat.minecraft.interact_with_anvil` | Interazzioni cù l'ancùdina | Interazzioni cù l'incudine | B05 |
| `stat.minecraft.interact_with_lectern` | Interazzioni cù u leghju | Interazzioni cù u pulpitru | B08 |
| `stat.minecraft.interact_with_smithing_table` | Interazzioni cù u bancu di ferraghju | Interazzioni cù u bancu di stazzunaru | B06 |
| `stat.minecraft.minecart_one_cm` | Distanza in carrettu | Distanza in vagunettu | I01 |
| `subtitles.block.anvil.destroy` | Ancùdina distrutta | Incudine distrutta | B05 |
| `subtitles.block.anvil.land` | Ancùdina casca | Incudine casca | B05 |
| `subtitles.block.anvil.use` | Ancùdina aduprata | Incudine aduprata | B05 |
| `subtitles.block.beehive.enter` | Ape entre in u bugnu | Apa entre in u bugnu | A05 |
| `subtitles.block.beehive.exit` | Ape esce da u bugnu | Apa esce da u bugnu | A05 |
| `subtitles.block.cake.add_candle` | Torta s'ammacca | Pastadolce s'ammacca | F04 |
| `subtitles.block.copper_trapdoor.close` | Bodula si chjode | Caterazza si chjode | B01 |
| `subtitles.block.copper_trapdoor.open` | Bodula s'apre | Caterazza s'apre | B01 |
| `subtitles.block.frogspawn.hatch` | Capirossulu nasce | Cudutu nasce | A07 |
| `subtitles.block.hanging_sign.waxed_interact_fail` | Cartellu si dondula | Cartella si dondula | B04 |
| `subtitles.block.iron_trapdoor.close` | Bodula si chjode | Caterazza si chjode | B01 |
| `subtitles.block.iron_trapdoor.close@9547f49f46f8` | Bodula s'apre | Caterazza s'apre | B01 |
| `subtitles.block.iron_trapdoor.open` | Bodula s'apre | Caterazza s'apre | B01 |
| `subtitles.block.iron_trapdoor.open@62a5572485d8` | Bodula si chjode | Caterazza si chjode | B01 |
| `subtitles.block.redstone_torch.burnout` | Torcia sfrigulighja | Torchja sfrigulighja | B14 |
| `subtitles.block.sign.waxed_interact_fail` | Cartellu si dondula | Cartella si dondula | B04 |
| `subtitles.block.smithing_table.use` | Bancu di ferraghju adupratu | Bancu di stazzunaru adupratu | B06 |
| `subtitles.block.sponge.absorb` | Sponga assorbe | Spunga assorbe | B09 |
| `subtitles.block.sweet_berry_bush.pick_berries` | Baghe scoppianu | Baghi scoppianu | F05 |
| `subtitles.block.trapdoor.close` | Bodula si chjode | Caterazza si chjode | B01 |
| `subtitles.block.trapdoor.open` | Bodula s'apre | Caterazza s'apre | B01 |
| `subtitles.block.trapdoor.toggle` | Bodula scricchja | Caterazza scricchja | B01 |
| `subtitles.block.wet_sponge.dries` | Sponga sicca | Spunga sicca | B09 |
| `subtitles.entity.bee.ambient` | Ape ronza | Apa ronza | A05 |
| `subtitles.entity.bee.death` | Ape more | Apa more | A05 |
| `subtitles.entity.bee.hurt` | Ape hè ferita | Apa hè ferita | A05 |
| `subtitles.entity.bee.loop` | Ape ronza | Apa ronza | A05 |
| `subtitles.entity.bee.loop_aggressive` | Ape ronza arrabbiata | Apa ronza arrabbiata | A05 |
| `subtitles.entity.bee.pollinate` | Ape ronza cuntenta | Apa ronza cuntenta | A05 |
| `subtitles.entity.bee.sting` | Ape punghje | Apa punghje | A05 |
| `subtitles.entity.camel.ambient` | Cammellu grunghje | Camellu grunghje | A06 |
| `subtitles.entity.camel.dash` | Cammellu si lancia | Camellu si lancia | A06 |
| `subtitles.entity.camel.dash_ready` | Cammellu si ripiglia | Camellu si ripiglia | A06 |
| `subtitles.entity.camel.death` | Cammellu more | Camellu more | A06 |
| `subtitles.entity.camel.eat` | Cammellu manghja | Camellu manghja | A06 |
| `subtitles.entity.camel.hurt` | Cammellu hè feritu | Camellu hè feritu | A06 |
| `subtitles.entity.camel.sit` | Cammellu si posa | Camellu si posa | A06 |
| `subtitles.entity.camel.stand` | Cammellu s'arrizza | Camellu s'arrizza | A06 |
| `subtitles.entity.camel.step` | Cammellu cammina | Camellu cammina | A06 |
| `subtitles.entity.camel.step_sand` | Cammellu cammina in a rena | Camellu cammina in a rena | A06 |
| `subtitles.entity.camel_husk.ambient` | Cammellu seccu grunghje | Camellu seccu grunghje | A06 |
| `subtitles.entity.camel_husk.dash` | Cammellu seccu si lancia | Camellu seccu si lancia | A06 |
| `subtitles.entity.camel_husk.dash_ready` | Cammellu seccu si ripiglia | Camellu seccu si ripiglia | A06 |
| `subtitles.entity.camel_husk.death` | Cammellu seccu more | Camellu seccu more | A06 |
| `subtitles.entity.camel_husk.eat` | Cammellu seccu manghja | Camellu seccu manghja | A06 |
| `subtitles.entity.camel_husk.hurt` | Cammellu seccu hè feritu | Camellu seccu hè feritu | A06 |
| `subtitles.entity.camel_husk.sit` | Cammellu seccu si posa | Camellu seccu si posa | A06 |
| `subtitles.entity.camel_husk.stand` | Cammellu seccu s'arrizza | Camellu seccu s'arrizza | A06 |
| `subtitles.entity.glow_squid.ambient` | Calamaru luminosu nata | Totanu luminosu nata | A04 |
| `subtitles.entity.glow_squid.death` | Calamaru luminosu more | Totanu luminosu more | A04 |
| `subtitles.entity.glow_squid.hurt` | Calamaru luminosu hè feritu | Totanu luminosu hè feritu | A04 |
| `subtitles.entity.glow_squid.squirt` | Calamaru luminosu sputa inchjostru | Totanu luminosu sputa inchjostru | A04 |
| `subtitles.entity.leash_knot.break` | Nodu di ligaccia rottu | Nodu di catinetta rottu | I04 |
| `subtitles.entity.leash_knot.break@74b6615a1b03` | Nodu di ligaccia si rompe | Nodu di catinetta si rompe | I04 |
| `subtitles.entity.leash_knot.break@e08f52796daf` | Nodu di ligaccia si rompe | Nodu di catinetta si rompe | I04 |
| `subtitles.entity.leash_knot.place` | Nodu di ligaccia attaccatu | Nodu di catinetta attaccatu | I04 |
| `subtitles.entity.leash_knot.place@2b888cf1f619` | Nodu di ligaccia attaccatu | Nodu di catinetta attaccatu | I04 |
| `subtitles.entity.leashknot.break@74b6615a1b03` | Nodu di ligaccia rottu | Nodu di catinetta rottu | I04 |
| `subtitles.entity.leashknot.place@2b888cf1f619` | Nodu di ligaccia attaccatu | Nodu di catinetta attaccatu | I04 |
| `subtitles.entity.minecart.inside` | Carrettu tintinna | Vagunettu tintinna | I01 |
| `subtitles.entity.minecart.inside_underwater` | Carrettu tintinna sott'acqua | Vagunettu tintinna sott'acqua | I01 |
| `subtitles.entity.minecart.riding` | Carrettu rotula | Vagunettu rotula | I01 |
| `subtitles.entity.squid.ambient` | Calamaru nata | Totanu nata | A04 |
| `subtitles.entity.squid.death` | Calamaru more | Totanu more | A04 |
| `subtitles.entity.squid.hurt` | Calamaru hè feritu | Totanu hè feritu | A04 |
| `subtitles.entity.squid.squirt` | Calamaru sprizza inchjostru | Totanu sprizza inchjostru | A04 |
| `subtitles.entity.tadpole.death` | Capirossulu more | Cudutu more | A07 |
| `subtitles.entity.tadpole.flop` | Capirossulu si sbatte | Cudutu si sbatte | A07 |
| `subtitles.entity.tadpole.grow_up` | Capirossulu cresce | Cudutu cresce | A07 |
| `subtitles.entity.tadpole.hurt` | Capirossulu hè feritu | Cudutu hè feritu | A07 |
| `subtitles.entity.villager.work_leatherworker` | Cuiaghju travaglia | Cunciadore travaglia | A16 |
| `subtitles.entity.villager.work_toolsmith` | Ferraghju d'attrezzi travaglia | Stazzunaru d'attrezzi travaglia | B06 |
| `subtitles.item.berries.pick@12a894e23ec4` | Baghe scoppianu | Baghi scoppianu | F05 |
| `subtitles.item.brush.brushing.gravel` | Pinnellatura di ghjàira | Pinnellatura di gravetta | R06 |
| `subtitles.item.brush.brushing.gravel.complete` | Ghjàira pinnellata | Gravetta pinnellata | R06 |
| `subtitles.item.bucket.fill_tadpole` | Capirossulu pigliatu | Cudutu pigliatu | A07 |
| `subtitles.item.dye.use` | Tintura tinghje | Tinta tinghje | M04 |
| `subtitles.item.golden_dandelion.unuse` | Pisciacane d'oru rimette l'invechjamentu | Radichju d'oru rimette l'invechjamentu | P07 |
| `subtitles.item.golden_dandelion.use` | Pisciacane d'oru ferma l'invechjamentu | Radichju d'oru ferma l'invechjamentu | P07 |
| `subtitles.item.lead.break` | Ligaccia si strappa | Catinetta si strappa | I04 |
| `subtitles.item.lead.tied` | Ligaccia attaccata | Catinetta attaccata | I04 |
| `subtitles.item.lead.untied` | Ligaccia staccata | Catinetta staccata | I04 |
| `subtitles.item.llama_carpet.unequip` | Tappetu staccatu | Tappettu staccatu | M03 |
| `trim_material.minecraft.lapis` | Materiale : lapislazuli | Materiale : lapislazzuli | R10 |

## Tracking and limits

[tracking-concrete.tsv](tracking-concrete.tsv) lists the lots. Every 26.3 name was read (2,004 distinct entries in the six
concrete lots; an English name used by keys of two lots counts in each) and every history-only name (190): 1,742 of
these 2,194 entries contain a word covered by a decision row (checked against a source or confirmed). The rest were read but not checked in a dictionary: invented Mojang names (Sculk, Allay…),
coined device names (Fabbricadore, Lampatore, Ghjiradischi, Affumicatore, Tagliapetra, Cumpustatore, Paragunatore…),
tropical fish types, and compounds of checked words. Those are the next lots.

Not done: no catalogue was edited; `tools/minecraft.py check` was not run on the proposals because they are not
applied (the only placeholders touched are in `container.enchant.lapis.*`, `%d/%s lapislazzuli`, kept intact); no
version was started in the game; no speaker was consulted.
