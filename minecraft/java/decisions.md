# Consistency pass: decisions and open questions

Eleven batches were merged into `co_fr.json`; this pass made one name per thing, applied the typography rule and
fixed clear grammar slips. Every choice is provisional and listed in [glossary.tsv](glossary.tsv) (status `proposal`
unless the reviewed lexicon has it).

## Harmonisation decisions

| Term | Variants seen | Choice | Reason |
| --- | --- | --- | --- |
| Dripleaf | Foglia stillante, Fogliastizza, Foglia à goccia | **Foglia à goccia** (chjuca / grande) | already the Big Dripleaf name; *goccia* attested, *stillante* not |
| Copper Bulb | Lampa, Lampada, Lampadina | **Lampadina di ramu** | *lampadina* is a bulb and attested; *Lampada* is already Redstone Lamp |
| Stem | Gambu, Fustu | **Fustu** everywhere (Fustu di zucca, Fustu cremisi, Fustu di fungu) | *fustu* well attested (93 + Apertium), *gambu* 1 |
| Froglight | Granochjalume, Lume di granochja | **Granochjalume** (pl. granochjalumi) | the block name; same pattern as Fungulume, Vaccafungu |
| Bush | Machja, Arbustu | **Arbustu**; Dead Bush = Arbustu seccu; Firefly Bush = Arbustu di lucciule | *machja* is the maquis as a whole; IT uses Arbusto / Arbusto secco |
| Ominous | minacciosu, funestu, di malu presagiu | **funestu** (Buttiglia funesta, Chjave di prova funesta, Stendardu funestu, Generatore d'ogetti funestu) | majority in subtitles; same sense as FR *funeste*; one adjective for the whole Ominous family |
| Command | cumandu (m), cumanda (f) | **cumanda / cumande** (f) | reviewed lexicon: Command → Cumanda, Commands → Cumande; Command Block → **Bloccu di cumanda** |
| Sculk Shrieker | Urladore, Urlatore, sculk urlatore | **Urladore di sculk** | block name; Catalyst = Catalizatore di sculk, Sensor = Sensore di sculk (block names) |
| Wall X | X di Y murale, X murale di Y | **X murale di Y**: Cartella murale di querciu, Torchja murale di redstone, Capu murale di Piglin, Cranu murale di scheletru, Ventaglia murale di curallu tubu; hanging signs: Cartella appesa murale di Y | rule given; *Cartella appesa* is treated as the head noun (names changed by the 2026-10 review, see below) |
| Colour plurals | aranci/arance, invariable forms | regular inflection: **aranciu/arancia, pl. aranci/arance**; grisgiu chjaru → grisgi chjari; celeste → celesti; marrone → marroni; verde → verdi; *verde limone* and *magenta* invariable | grammatical and already used consistently (Denti aranci, Foglie di piobbu arance) |
| Zombified Piglin | zombificatu, zumbificatu | **Piglin zumbificatu** | the name key; regular Corsican *o → u* before the stress |
| Speed | Velocità, Vitezza | kept: **Velocità** effect/potion, **vitezza** in settings | as decided |
| Brightness | Luminosità, Lucidezza | **Lucidezza** | both reviewed lexicons (Mozilla, upstream) |
| Creature names | Shulker/shulker, Piglin/piglin, Slime/slime, Axolotl/axolotl | **capitalised** (Scatula di Shulker, Capu di Piglin, Bloccu di Slime) | STYLE: invented creature names keep their capital, as Creeper, Ghast, Blaze already did |
| Amethyst Bud | Germogliu, Gemma | **Gemma d'ametista** chjuca / mezana / grande | *germogliu* is already Bamboo Shoot and Nether Sprouts |
| Bars | Sbarre, Barre | **Sbarre** (ferru, ramu) | Iron Bars already Sbarre |
| Nylium | Niliu, Nylium | **Niliu** | adapted like Miceliu |
| Eyeblossom closed | chjusu, chjosu | **chjosu** | the reviewed lexicon writes chjosu/chjosa |
| Tube Coral | Curallu à tubu, Curallu tubu | **Curallu tubu** | same pattern as cervellu, bolla, focu, cornu |
| Cornflower / Azure Bluet | Fiordalisu; Houstonia | **Fiurdalisu**; **Houstonia celeste** (also potted) | match the plant name |
| Sweet Berries, Weeping Vines, End Barrens | Baghe dolce, Liane pendente / pienghjulente, Terre sterile | ~~Baghe dolci, Liane pendenti, Terre sterili~~ → now **Baghe dolce**, **Liane pendente**, **Terre sterile** | superseded by [decisions-2.md](decisions-2.md) D2: after a feminine plural noun, *-e* adjectives keep *-e* in the reviewed translations and Vikipedia (a provisional convention, not a grammar rule) |
| Powder Snow | Neve polverosa, Neve in polvera | **Neve polverosa** (Secchja di neve polverosa) | block name |
| Turtle Shell, Ink Sac, Lodestone Compass, Shelf Mushroom, Wolf Armor, Tripwire, Fishing Bobber | Carapace, Sacca, Bussula di calamita, Fungu à mensula, Armatura di lupu, Filu di scattu, Galleghjante | name keys: **Scorza di tartaruga, Bursa d'inchjostru, Bussula calamitata, Fungu à scaffale, Armatura per lupu, Filu d'inciampu, Galleghjante di pesca** | subtitles and advancements follow the item name |
| Screenshot | fiura di screnu, cattura di screnu | **cattura di screnu** | lexicon-upstream: Catture di screnu |
| Edit box | campu di scrittura, campu di testu | **campu di testu** | 13 uses; lexicon-mozilla "campu di testu" |
| Banned | scacciatu, esclusu | **esclusu / esclusione** | the commands already used esclusione for the noun |
| Typography | `word:`, `word :`, `...` | space before `: ; ! ?`, `…` for `...` | reviewed lexicon; never inside placeholders, times (`%s:%s`, `1:%s`), ids, key labels, `???`, or pure format strings (`%s: %s`) |
| Elision | di un, una entità, stu ogettu | **d'un, d'una, d'ogni, un'entità, st'ogettu** | lexicon: d'un 56 vs di un 4 |

## October 2026 review, verified

Two AI review sets (concrete names, language and context) were checked entry by entry by a separate AI verification
before anything was applied; nothing of it is a speaker's validation. Applied changes with their references:
[review-2026-10/APPLIED.tsv](review-2026-10/APPLIED.tsv); proposals not applied and why:
[review-2026-10/REJECTED.tsv](review-2026-10/REJECTED.tsv); summary: [review-2026-10/TRACKING.md](review-2026-10/TRACKING.md).
The harmonisations it made (one spelling for the product; the other form is attested and not wrong): *dighjà* (not
*digià*), *seranu/serete* (not *saranu/sarete*), *perfurmenze* (not *prestazioni*), *evenimenti* (not
*avvenimenti*), polite *voi* with a singular adjective (*Site sicuru*, *Site esclusu*).

## Open questions for a Corsican speaker

An AI terminology review (October 2026, **not** a speaker validation) gave each question a proposal and a solidity
level (attested / plausible / doubtful / unresolved), with the evidence, in [review.md](review.md). One question was
answered with an attested form and applied (Q30); Q20 and Q22 were only harmonised. The same review replaced
*servore* by *servitore*, *chjachjarata* by *chjachjerata* and the world *sementa* by *grana* (attested forms), see
[changes-review.tsv](changes-review.tsv).

1. `block.minecraft.small_dripleaf`, `big_dripleaf`: is *Foglia à goccia* natural, or is there a local plant word? — *Review 2026-10:* keep; plausible.
2. `block.minecraft.copper_bulb`: *Lampadina di ramu* vs *Lampa di ramu*; is *lampa* (attested 33×) the better everyday word, and should Redstone Lamp then become *Lampa di redstone*? — *Review 2026-10:* keep; unresolved.
3. `item.minecraft.ominous_bottle`, `block.minecraft.ominous_banner`: *funestu* vs *minacciosu* vs *di malu presagiu* for Ominous. — *Review 2026-10:* keep *funestu*; plausible.
4. `block.minecraft.bush`, `dead_bush`: *Arbustu / Arbustu seccu* vs *Machja*. — *Review 2026-10:* keep *Arbustu* (*machja* also attested as "bush", Wiktionary); unresolved.
5. `block.minecraft.crimson_stem`, `mushroom_stem`: *Fustu* for a mushroom stem, or *gambu*? — *Review 2026-10:* keep *Fustu*; plausible.
6. `block.minecraft.sculk_shrieker`: *Urladore* (coined from *urlà*); agent nouns mix *-adore* and *-atore* across the file (Urladore, Catalizatore, Fabbricadore, Osservatore) — pick a rule? — *Review 2026-10:* no single suffix rule (both attested); *urladore* unresolved.
7. `entity.minecraft.zombified_piglin`: *zumbificatu* vs *zombificatu*. — *Review 2026-10:* keep; unresolved.
8. `block.minecraft.orange_poplar_leaves`: plural *arance* of the colour *arancia* reads like "oranges" (the fruit); keep, or use an invariable form? — *Review 2026-10:* keep; unresolved.
9. `block.minecraft.nether_wart`: *Verruca di u Nether* without attestation in the resources consulted. — *Review 2026-10:* ask about *porru*; current doubtful. *Round 2 (2026-10-18):* *verruche* is used in the wart sense in the local Vikipedia (article *Lophius piscatorius*); kept, still for a speaker.
10. `block.minecraft.sea_pickle`: *Cucumaru di mare* is a guess (the real creature is a pyrosome). — *Review 2026-10:* keep; plausible.
11. `block.minecraft.allium`, `cornflower` (*Fiurdalisu* vs *Fiordalisu*), `azure_bluet` (*Houstonia*), `lily_pad` (*ninfea*): common Corsican plant names? — *Review 2026-10:* keep; *Agliu salvaticu* plausible, others unresolved. — *Verification 2026-10-18:* *Fiurdalisu* kept (INFCOR lists it as a synonym of *turchinellu*); Lily Pad changed to *Nenufaru* (INFCOR, EN "lily pad").
12. `block.minecraft.potent_sulfur`: meaning of "Potent" (new 26.3 block) unclear; *Zolfu putente*. — *Review 2026-10:* *Zolfu cuncentratu* if FR/IT reading confirmed; current doubtful.
13. `block.minecraft.banner.*`: heraldic terms *Trinciatu, Tagliatu, Troncatu, Partitu* calqued on Italian heraldry; dexter/sinister as *à diritta / à manca*. — *Review 2026-10:* keep; unresolved.
14. `block.minecraft.frosted_ice` (*brinatu*), `gilded_blackstone` (*durata* may read as "duration"), `chipped_anvil` (*intaccata*): without attestation in the resources consulted adjectives. — *Review 2026-10:* *Petranera indurata* proposed (*durata* clashes with "duration"); doubtful.
15. `biome.minecraft.deep_lukewarm_ocean`: *tepidu* without attestation in the resources consulted (tèpidu? calducciu?). — *Review 2026-10:* keep; unresolved.
16. `biome.minecraft.dappled_forest`: *chjazzata*; `lush_caves`: *verdi* may be too plain; `jagged_peaks`: *dentati*. — *Review 2026-10:* check the biome in game (FR/IT read "amber"); unresolved.
17. `entity.minecraft.parched` (*Scheletru arsu*), `camel_husk` (*Camellu seccu*, spelling verified 2026-10), `entity.minecraft.cushion` (*Cuscinu*): new 26.x mobs, meaning guessed from FR/IT. — *Review 2026-10:* keep; *arsu* doubtful.
18. `advancements.husbandry.feed_snifflet.description`: Snifflet coined *annusadurellu*. — *Review 2026-10:* keep; unresolved.
19. `subtitles.entity.ghastling.ambient`: Ghastling coined *Ghastinu*. — *Review 2026-10:* keep; plausible.
20. `subtitles.entity.horse.ambient` / `zombie_horse.angry`: *annitrisce* vs *nitrisce* (neigh). — *Review 2026-10:* harmonised on *annitrisce*; unresolved.
21. `subtitles.entity.chicken.ambient`: *cocca* for cluck (chjoccia? cucculeghja?). — *Review 2026-10:* keep; unresolved.
22. `subtitles.entity.wolf.growl`, `baby_wolf.ambient`: *ringhja, ghjappa, ansima* sound Italian; Corsican verbs? — *Review 2026-10:* *abbaghja* attested; *ansima → ansa* harmonised; rest unresolved.
23. `subtitles.entity.bee.ambient`, `parrot.imitate.breeze`: *ronza* (buzz, whir) without attestation in the resources consulted. — *Review 2026-10:* keep; unresolved.
24. `subtitles.entity.axolotl.splash`, `slime.squish`: coined *sciaccuttuleghja*, *sciaccheghja*. — *Review 2026-10:* keep; unresolved.
25. `subtitles.entity.parrot.imitate.creaking`: distinction *cricca* (creaks) / *scricchjula* (rattles) is coined. — *Review 2026-10:* keep; unresolved.
26. `subtitles.entity.drowned.ambient` (*gorgula*), `panda.worried_ambient` (*mugula*), `rabbit.ambient` (*squitta*), `strider.idle` (*piula*), `parrot.imitate.endermite` (*zampetta*): without attestation in the resources consulted sound verbs. — *Review 2026-10:* keep; unresolved.
27. `subtitles.item.trident.thunder`: *tonu* for thunder. — *Review 2026-10:* keep; plausible. *Round 2:* attested (ADECEC la-géographie "tonnerre : tonu", le-temps-qu'il-fait "Tonnerre : tonu"); *tronu* (throne in Vikipedia) replaced by *tonu* in the lightning subtitle and `/weather`. *Round 3:* confirmed on the attestation of *tonu*; that *tronu* means throne in the texts consulted does not show it cannot be a regional word for thunder (to check by hand: INFCOR "tonnerre", "tronu"), see [review-2026-10/ROUND3.md](review-2026-10/ROUND3.md).
28. `advancements.adventure.blowback.title`: proverb *Chì sumena ventu ricoglie timpesta* — wording and spelling. — *Review 2026-10:* keep; plausible. *Round 2:* ADECEC la-géographie "récolter : ricoglie, ra-"; `plant_seed.title` harmonised on *ricoglie*.
29. `advancements.adventure.two_birds_one_arrow.title`: *Dui pichjoni cù una freccia*, adapted from Italian; is there a Corsican idiom? — *Review 2026-10:* keep; plausible.
30. `advancements.adventure.minecraft_trials_edition.description`: imperative *Mettite pede* (mittite?). — *Review 2026-10:* **changed to *Mittite*** (mozilla:1892); attested.
31. `advancements.husbandry.root.title`: Husbandry as *Agricultura*; *Allevu* possible. — *Review 2026-10:* keep; plausible.
32. `item.minecraft.debug_stick`: *Bastone di spannatura* may be opaque. — *Review 2026-10:* keep; *spannatura* attested (mozilla:881, 1506).
33. `enchantment.minecraft.riptide` (*Risacca*), `channeling` (*Canalizazione*, -zione or -zzione?), `depth_strider` (*Passu di l'abissi*). — *Review 2026-10:* keep; *Canalizazione* plausible (attested -izazione pattern), others unresolved.
34. `item.modifiers.any` / `item.modifiers.saddle`: *equipatu*, *insellatu* without attestation in the resources consulted. — *Review 2026-10:* keep; unresolved.
35. `item.minecraft.sheaf_pottery_sherd` (*mannella* vs *gregna*), `snort_pottery_sherd` (*sbuffu*), `mourner_pottery_sherd` (*luttu*). — *Review 2026-10:* keep; plausible / unresolved.
36. `key.keyboard.backspace` (*Ritornu in daretu*), `key.keyboard.left.shift` (*Maiuscule manca*: gender of the side keys), `key.keyboard.scroll.lock` (*Bloccu sfilà*). — *Review 2026-10:* Backspace and Scroll attested (upstream:12682, :3883); Shift unresolved.
37. `options.viewBobbing` (*Oscillazione di a vista*), `options.vignette` (*Vignettatura*), `options.prioritizeChunkUpdates` (*Custruttore di pezzi*): coined setting names. — *Review 2026-10:* keep; plausible.
38. `merchant.level.1`–`3`: *Principiante, Apprendista, Cumpagnu* for Novice, Apprentice, Journeyman. — *Review 2026-10:* keep; levels 3–5 plausible, 1–2 unresolved.
39. `mco.configure.world.spawnNPCs`: *PNG* (persunaghju micca ghjucadore) may be unclear; and `mco.account.privacy.information`, `mco.configure.world.subscription.recurring.info`: legal and billing texts need a careful read. — *Review 2026-10:* needs a human reading; unresolved.
40. `multiplayer.player.list.hp`: *%s PS* (punti di salute) as the abbreviation for HP. — *Review 2026-10:* keep; plausible.
