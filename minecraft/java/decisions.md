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
| Wall X | X di Y murale, X murale di Y | **X murale di Y**: Cartellu murale di quercia, Torcia murale di redstone, Capu murale di Piglin, Cranu murale di scheletru, Ventaglia murale di curallu tubu; hanging signs: Cartellu appesu murale di Y | rule given; *Cartellu appesu* is treated as the head noun |
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
| Sweet Berries, Weeping Vines, End Barrens | Baghe dolce, Liane pendente / pienghjulente, Terre sterile | **Baghe dolci**, **Liane pendenti**, **Terre sterili** | plural of *-e* adjectives is *-i* |
| Powder Snow | Neve polverosa, Neve in polvera | **Neve polverosa** (Secchja di neve polverosa) | block name |
| Turtle Shell, Ink Sac, Lodestone Compass, Shelf Mushroom, Wolf Armor, Tripwire, Fishing Bobber | Carapace, Sacca, Bussula di calamita, Fungu à mensula, Armatura di lupu, Filu di scattu, Galleghjante | name keys: **Scorza di tartaruga, Bursa d'inchjostru, Bussula calamitata, Fungu à scaffale, Armatura per lupu, Filu d'inciampu, Galleghjante di pesca** | subtitles and advancements follow the item name |
| Screenshot | fiura di screnu, cattura di screnu | **cattura di screnu** | lexicon-upstream: Catture di screnu |
| Edit box | campu di scrittura, campu di testu | **campu di testu** | 13 uses; lexicon-mozilla "campu di testu" |
| Banned | scacciatu, esclusu | **esclusu / esclusione** | the commands already used esclusione for the noun |
| Typography | `word:`, `word :`, `...` | space before `: ; ! ?`, `…` for `...` | reviewed lexicon; never inside placeholders, times (`%s:%s`, `1:%s`), ids, key labels, `???`, or pure format strings (`%s: %s`) |
| Elision | di un, una entità, stu ogettu | **d'un, d'una, d'ogni, un'entità, st'ogettu** | lexicon: d'un 56 vs di un 4 |

## Open questions for a Corsican speaker

1. `block.minecraft.small_dripleaf`, `big_dripleaf`: is *Foglia à goccia* natural, or is there a local plant word?
2. `block.minecraft.copper_bulb`: *Lampadina di ramu* vs *Lampa di ramu*; is *lampa* (attested 33×) the better everyday word, and should Redstone Lamp then become *Lampa di redstone*?
3. `item.minecraft.ominous_bottle`, `block.minecraft.ominous_banner`: *funestu* vs *minacciosu* vs *di malu presagiu* for Ominous.
4. `block.minecraft.bush`, `dead_bush`: *Arbustu / Arbustu seccu* vs *Machja*.
5. `block.minecraft.crimson_stem`, `mushroom_stem`: *Fustu* for a mushroom stem, or *gambu*?
6. `block.minecraft.sculk_shrieker`: *Urladore* (coined from *urlà*); agent nouns mix *-adore* and *-atore* across the file (Urladore, Catalizatore, Fabbricadore, Osservatore) — pick a rule?
7. `entity.minecraft.zombified_piglin`: *zumbificatu* vs *zombificatu*.
8. `block.minecraft.orange_poplar_leaves`: plural *arance* of the colour *arancia* reads like "oranges" (the fruit); keep, or use an invariable form?
9. `block.minecraft.nether_wart`: *Verruca di u Nether* unattested.
10. `block.minecraft.sea_pickle`: *Cucumaru di mare* is a guess (the real creature is a pyrosome).
11. `block.minecraft.allium`, `cornflower` (*Fiurdalisu* vs *Fiordalisu*), `azure_bluet` (*Houstonia*), `lily_pad` (*ninfea*): common Corsican plant names?
12. `block.minecraft.potent_sulfur`: meaning of "Potent" (new 26.3 block) unclear; *Zolfu putente*.
13. `block.minecraft.banner.*`: heraldic terms *Trinciatu, Tagliatu, Troncatu, Partitu* calqued on Italian heraldry; dexter/sinister as *à diritta / à manca*.
14. `block.minecraft.frosted_ice` (*brinatu*), `gilded_blackstone` (*durata* may read as "duration"), `chipped_anvil` (*intaccata*): unattested adjectives.
15. `biome.minecraft.deep_lukewarm_ocean`: *tepidu* unattested (tèpidu? calducciu?).
16. `biome.minecraft.dappled_forest`: *chjazzata*; `lush_caves`: *verdi* may be too plain; `jagged_peaks`: *dentati*.
17. `entity.minecraft.parched` (*Scheletru arsu*), `camel_husk` (*Cammellu seccu*), `entity.minecraft.cushion` (*Cuscinu*): new 26.x mobs, meaning guessed from FR/IT.
18. `advancements.husbandry.feed_snifflet.description`: Snifflet coined *annusadurellu*.
19. `subtitles.entity.ghastling.ambient`: Ghastling coined *Ghastinu*.
20. `subtitles.entity.horse.ambient` / `zombie_horse.angry`: *annitrisce* vs *nitrisce* (neigh).
21. `subtitles.entity.chicken.ambient`: *cocca* for cluck (chjoccia? cucculeghja?).
22. `subtitles.entity.wolf.growl`, `baby_wolf.ambient`: *ringhja, ghjappa, ansima* sound Italian; Corsican verbs?
23. `subtitles.entity.bee.ambient`, `parrot.imitate.breeze`: *ronza* (buzz, whir) unattested.
24. `subtitles.entity.axolotl.splash`, `slime.squish`: coined *sciaccuttuleghja*, *sciaccheghja*.
25. `subtitles.entity.parrot.imitate.creaking`: distinction *cricca* (creaks) / *scricchjula* (rattles) is coined.
26. `subtitles.entity.drowned.ambient` (*gorgula*), `panda.worried_ambient` (*mugula*), `rabbit.ambient` (*squitta*), `strider.idle` (*piula*), `parrot.imitate.endermite` (*zampetta*): unattested sound verbs.
27. `subtitles.item.trident.thunder`: *tonu* for thunder.
28. `advancements.adventure.blowback.title`: proverb *Chì sumena ventu ricoglie timpesta* — wording and spelling.
29. `advancements.adventure.two_birds_one_arrow.title`: *Dui pichjoni cù una freccia*, adapted from Italian; is there a Corsican idiom?
30. `advancements.adventure.minecraft_trials_edition.description`: imperative *Mettite pede* (mittite?).
31. `advancements.husbandry.root.title`: Husbandry as *Agricultura*; *Allevu* possible.
32. `item.minecraft.debug_stick`: *Bastone di spannatura* may be opaque.
33. `enchantment.minecraft.riptide` (*Risacca*), `channeling` (*Canalizazione*, -zione or -zzione?), `depth_strider` (*Passu di l'abissi*).
34. `item.modifiers.any` / `item.modifiers.saddle`: *equipatu*, *insellatu* unattested.
35. `item.minecraft.sheaf_pottery_sherd` (*mannella* vs *gregna*), `snort_pottery_sherd` (*sbuffu*), `mourner_pottery_sherd` (*luttu*).
36. `key.keyboard.backspace` (*Ritornu in daretu*), `key.keyboard.left.shift` (*Maiuscule manca*: gender of the side keys), `key.keyboard.scroll.lock` (*Bloccu sfilà*).
37. `options.viewBobbing` (*Oscillazione di a vista*), `options.vignette` (*Vignettatura*), `options.prioritizeChunkUpdates` (*Custruttore di pezzi*): coined setting names.
38. `merchant.level.1`–`3`: *Principiante, Apprendista, Cumpagnu* for Novice, Apprentice, Journeyman.
39. `mco.configure.world.spawnNPCs`: *PNG* (persunaghju micca ghjucadore) may be unclear; and `mco.account.privacy.information`, `mco.configure.world.subscription.recurring.info`: legal and billing texts need a careful read.
40. `multiplayer.player.list.hp`: *%s PS* (punti di salute) as the abbreviation for HP.
