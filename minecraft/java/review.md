# Minecraft Java 26.3 in Corsican: terminology review (October 2026)

**This is not a speaker validation.** It was written by an AI model that looked words up in the resources listed
below. Nothing here is "validated": every entry carries one of four solidity levels, and only a Corsican speaker can
move a term beyond them.

| Level | Meaning |
| --- | --- |
| **attested** | found *with this meaning* in a resource, cited (file:line, TMX project, Wiktionary gloss) |
| **plausible** | the word exists (e.g. Vikipedia/Apertium hits) or follows Corsican morphology, but the meaning was not confirmed |
| **doubtful** | a resource points elsewhere, or the form looks Italian/French rather than Corsican |
| **unresolved** | no usable evidence either way; a speaker must decide |

Resources used (no web lookups, INFCOR not queried):

- `lexicon/lexicon-mozilla.tsv`, `lexicon/lexicon-upstream.tsv`: reviewed Corsican software translations (mostly
  Patriccollu di Santa Maria è Sichè), cited as `mozilla:LINE` / `upstream:LINE`. `lexicon/lexicon.tsv` is a draft
  file and was **not** used as evidence.
- Mozilla Pontoon TMX (`co.all-projects.tmx`, cited "TMX") and terminology TBX (`co.v2.tbx`, cited "TBX").
- `tools/corsican_words.py lookup`: Vikipedia hit counts ("vik N"), Apertium dictionary, Pontoon terms, Wiktionary
  glosses (kaikki dump, cited "Wiktionary"). A Vikipedia count shows that a form exists, not what it means.
- English, French and Italian files of 26.3 for the meaning of each string.

"Strings" = number of keys of `co_fr.json` that contain the term after this review.

## What changed in `co_fr.json`

242 edits on 230 keys, every one logged in [changes-review.tsv](changes-review.tsv) with old text, new text, reason
and solidity. Key order, formatting and placeholders are unchanged (`tools/minecraft.py check`: 0 errors;
`verify`: 8,559 keys rendered by the game's code, 0 problems).

| Type | Edits | Examples |
| --- | --- | --- |
| Term spelling replaced by the attested one | 173 | *servore → servitore* (88), *chjachjarata → chjachjerata* (70), world *sementa → grana* (8), *cunsula → cunsola* (2), Title Screen harmonised on *listinu principale* (5) |
| Italian forms → Corsican forms attested in the reviewed lexicons | 57 | *esplorazione → esplurazione*, *Mettite → Mittite*, *Prutegite → Prutigite*, *perderete → pirderete*, *Tenite → Tinite*, *al più → à u più*, *colonna → culonna*, *restrizzioni → ristrizzioni*, *rinnuvà → rinnovà*, *ridottu → riduttu*, *riduzione → riduzzione*, *ripresentazioni/rapprisentazione → riprisentazione* |
| Typography (spaces inside « ») | 10 | *«Mondu caricatu» → « Mondu caricatu »* |
| Internal consistency of subtitles | 2 | *Cavallu zombi nitrisce → annitrisce*; *Lupachjolu ansima → ansa* |

No change was made where the evidence was only a Vikipedia count or where both forms are attested.

Scans that found nothing to fix: Italian articles and contractions (*il, lo, gli, della, nella, del*), *non*,
*è* used for *hè*, *ùn* without *micca* (8 hits, all with another negative word: *nè, nisunu, più, alcunu*),
missing elision (*di un, una + vowel, stu + vowel, u/a/i/e + vowel*), colour agreement in the 21 coloured block
families and the 40 banner patterns × 16 colours (all consistent with the noun's gender).

## Part 1: the 40 open questions of decisions.md

### Q1. Dripleaf
- **Keys:** `block.minecraft.small_dripleaf`, `big_dripleaf` (+ subtitles); EN *Small/Big Dripleaf*; FR *foliogoutte*, IT *Piantaforma*.
- **Context:** a cave plant whose leaf tilts when stood on.
- **Current:** *Foglia à goccia chjuca / grande*. **Alternatives:** a local plant name if one exists.
- **Evidence:** *foglia* Wiktionary "leaf", vik 35; *goccia* vik 6. No plant name found.
- **Proposal:** keep. **Solidity:** plausible. **Strings:** 5.

### Q2. Copper Bulb vs Redstone Lamp
- **Keys:** `block.minecraft.copper_bulb` (+ oxidised/waxed variants), `block.minecraft.redstone_lamp`.
- **Current:** *Lampadina di ramu*; *Lampada di redstone*. **Alternatives:** *Lampa*.
- **Evidence:** *lampadina* vik 2, *lampada* vik 2, *lampa* vik 33 — but *lampa* is also the 3rd person of *lampà*
  "to throw", which the file uses (*Lampatore* = Dropper), so the 33 hits do not show a noun "lamp". No lexicon hit.
- **Proposal:** keep (distinct names for two blocks). **Solidity:** unresolved. **Strings:** 11 + 1.

### Q3. Ominous
- **Keys:** `item.minecraft.ominous_bottle`, `block.minecraft.ominous_banner`, ominous trial key/spawner.
- **Current:** *funestu/funesta*. **Alternatives:** *minacciosu*, *di malu presagiu*.
- **Evidence:** *funestu* vik 3, *minacciosu* vik 1, *presagiu* not found (note: Bad Omen is *malu presagiu*, unattested).
  FR *funeste*, IT *infausto*.
- **Proposal:** keep *funestu*. **Solidity:** plausible. **Strings:** 12.

### Q4. Bush
- **Keys:** `block.minecraft.bush`, `dead_bush`, `firefly_bush`.
- **Current:** *Arbustu*, *Arbustu seccu*. **Alternative:** *Machja*.
- **Evidence:** *machja* Wiktionary "shrub, bush, brake; macchia (shrubland)", vik 114, Apertium; *arbustu* vik 76
  (meaning not checked). So *machja* is attested in the "bush" sense but also names the maquis as a whole.
- **Proposal:** keep *Arbustu* (a single block, not a landscape); a speaker should say whether *machja* is natural for
  one bush. **Solidity:** unresolved (both defensible). **Strings:** 8.

### Q5. Stem
- **Keys:** `block.minecraft.crimson_stem`, `warped_stem`, `mushroom_stem`, melon/pumpkin stems.
- **Current:** *Fustu*. **Alternative:** *gambu*; Wiktionary also lists *anca* "stem".
- **Evidence:** *fustu* vik 93 + Apertium; *gambu* vik 1.
- **Proposal:** keep *Fustu*. **Solidity:** plausible. **Strings:** 10.

### Q6. Sculk Shrieker, and agent nouns -adore / -atore
- **Keys:** `block.minecraft.sculk_shrieker` (+ subtitles); also Crafter, Observer, Catalyst.
- **Current:** *Urladore di sculk*; *Fabbricadore*, *Osservatore*, *Catalizatore*.
- **Evidence:** *urladore* not found, *urlà* vik 1. Both suffixes are attested in the reviewed lexicons:
  *-adore* (*separadore* mozilla:2241, *ingannadore* mozilla:1225, *ghjucadore*) and *-atore* (*utilizatore*,
  *navigatore*, *espluratore* upstream:8113). *Osservatore* vik 5 + Apertium.
- **Proposal:** no single rule: keep established words (*osservatore*, *catalizatore*), *-adore* for new coinages
  from *-à* verbs. **Solidity:** plausible (suffix), unresolved (*urladore*). **Strings:** 3 (Urladore).

### Q7. Zombified Piglin
- **Keys:** `entity.minecraft.zombified_piglin` (+ spawn egg, subtitles).
- **Current:** *Piglin zumbificatu*. **Alternative:** *zombificatu*.
- **Evidence:** neither form found; *zombi* vik 1 (the file writes *Cavallu zombi*, *Zombi*).
- **Proposal:** keep, but note that *zombificatu* would keep the stem visible as in *zombi*. **Solidity:** unresolved. **Strings:** 8.

### Q8. Orange (plural *arance*)
- **Keys:** `block.minecraft.orange_poplar_leaves` (the only *arance*); the colour family uses *aranciu/arancia*.
- **Current:** *Foglie di piobbu arance*. **Alternative:** invariable *aranciu*, or *di culore aranciu*.
- **Evidence:** *arance* not found, *arancia* vik 1, *aranciu* vik 29. Wiktionary gives -i plurals for -e adjectives only.
- **Proposal:** keep regular inflection for now. **Solidity:** unresolved. **Strings:** 1 (*arance*), 21 (*arancia*).

### Q9. Nether Wart
- **Keys:** `block.minecraft.nether_wart`, `item.minecraft.nether_wart`, wart block.
- **Current:** *Verruca di u Nether*. **Alternative:** *porru* (Corsican/southern word for wart, also "leek").
- **Evidence:** *verruca* not found; *porri* vik 24 (sense not checked).
- **Proposal:** ask a speaker about *porru*. **Solidity:** doubtful (current form looks Italian). **Strings:** 4.

### Q10. Sea Pickle
- **Key:** `block.minecraft.sea_pickle`. **Current:** *Cucumaru di mare*. FR *Cornichon de mer*, IT *Cetriolo di mare*.
- **Evidence:** *cucumaru* vik 10.
- **Proposal:** keep (same image as FR/IT). **Solidity:** plausible. **Strings:** 1.

### Q11. Allium, Cornflower, Azure Bluet, Lily Pad
- **Keys:** `block.minecraft.allium`, `cornflower`, `azure_bluet`, `lily_pad` (+ potted).
- **Current:** *Agliu salvaticu*, *Fiurdalisu*, *Houstonia celeste*, *Foglia di ninfea*.
- **Evidence:** *agliu* vik 6; *fiurdalisu*, *fiordalisu*, *ninfea* not found.
- **Proposal:** keep; ask for local plant names. **Solidity:** plausible (*agliu salvaticu*), unresolved (others). **Strings:** 7.

### Q12. Potent Sulfur
- **Key:** `block.minecraft.potent_sulfur`. **Current:** *Zolfu putente*. FR *Soufre concentré*, IT *Zolfo concentrato*.
- **Evidence:** *putente* vik 85 + Apertium ("powerful"); *cuncentratu* vik 2, upstream:4373 (in the sense "focused").
  FR and IT both read "concentrated".
- **Proposal:** *Zolfu cuncentratu* if a speaker confirms the FR/IT reading. **Solidity:** doubtful (current). **Strings:** 1.

### Q13. Banner heraldry
- **Keys:** `block.minecraft.banner.*` (diagonal, half, per bend, per pale…).
- **Current:** *Trinciatu, Tagliatu, Troncatu, Partitu*, dexter/sinister *à diritta / à manca*.
- **Evidence:** none of the heraldic terms found (*troncatu* 0, *trinciatu* 0). They follow Italian heraldry
  (IT *Trinciato, Tagliato, Troncato, Partito*). Agreement is consistent across all 16 colours.
- **Proposal:** keep; needs a speaker familiar with Corsican heraldry (the Moor's head flag). **Solidity:** unresolved. **Strings:** 152.

### Q14. Frosted Ice, Gilded Blackstone, Chipped Anvil
- **Keys:** `block.minecraft.frosted_ice`, `gilded_blackstone`, `chipped_anvil`.
- **Current:** *Ghjacciu brinatu*, *Petranera durata*, *Ancùdina intaccata*.
- **Evidence:** *brinatu* not found; *durata* vik 96 — most of it is the noun "duration", and this file also uses
  *durata* for "duration" (telemetry, `commands.title.times`), so the clash is real; *indurata* vik 1 (from *indurà*
  "to gild"), *dorata* vik 1; *intaccata* vik 1; *ancùdina* not found.
- **Proposal:** *Petranera indurata* to avoid the clash, if a speaker confirms *indurà*. **Solidity:** doubtful
  (*durata*), unresolved (others). **Strings:** 3.

### Q15. Lukewarm
- **Keys:** `biome.minecraft.lukewarm_ocean`, `deep_lukewarm_ocean`. **Current:** *tepidu*.
- **Evidence:** *tepidu*, *tèpidu*, *tiepidu*, *calducciu* all not found.
- **Proposal:** keep. **Solidity:** unresolved. **Strings:** 2.

### Q16. Dappled Forest, Lush Caves, Jagged Peaks
- **Keys:** `biome.minecraft.dappled_forest`, `lush_caves`, `jagged_peaks`.
- **Current:** *Furesta chjazzata*, *Grotte verdi*, *Pinzi dentati*.
- **Evidence:** *chjazzata* not found; FR *Forêt ambrée*, IT *Foresta ambrata* both read the new biome as
  amber-coloured, not spotted; *dentati* vik 8.
- **Proposal:** check the biome in game before choosing between "spotted" and "amber". **Solidity:** unresolved. **Strings:** 5.

### Q17. New mobs (Parched, Camel Husk, Cushion)
- **Keys:** `entity.minecraft.parched`, `camel_husk`, `cushion` (+ spawn eggs, subtitles; Cushion is also a coloured block family).
- **Current:** *Scheletru arsu*, *Cammellu seccu*, *Cuscinu*. FR *Desséché / Dromadaire momifié / Coussin*, IT *Ossecco / Mummifario / Cuscino*.
- **Evidence:** *arsu* not found; *seccu* vik 36; *cuscinu* vik 22.
- **Proposal:** keep; *Scheletru seccu* would match FR "desséché" better than "burnt" *arsu*. **Solidity:** plausible
  (*Cuscinu*, *Cammellu seccu*), doubtful (*arsu*). **Strings:** 36.

### Q18. Snifflet
- **Key:** `advancements.husbandry.feed_snifflet.description` (+ entity). **Current:** *annusadurellu*.
- **Evidence:** not found; *annusadore* (Sniffer, 22 strings) also unattested; *-ellu* diminutive is productive.
- **Proposal:** keep. **Solidity:** unresolved. **Strings:** 1.

### Q19. Ghastling
- **Key:** `subtitles.entity.ghastling.*`, `entity.minecraft.happy_ghast` family. **Current:** *Ghastinu*.
- **Evidence:** coinage; *-inu* is a productive diminutive (*lupachjolu* uses *-olu*).
- **Proposal:** keep. **Solidity:** plausible (pattern). **Strings:** 4.

### Q20. Neigh
- **Keys:** `subtitles.entity.horse.*`, `baby_horse.*`, `zombie_horse.angry`.
- **Current:** *annitrisce* (5), *nitrisce* (1, now harmonised). **Evidence:** neither found.
- **Change made:** `zombie_horse.angry` → *annitrisce* (consistency only).
- **Proposal:** one verb everywhere; which one is for a speaker. **Solidity:** unresolved. **Strings:** 5.

### Q21. Cluck
- **Key:** `subtitles.entity.chicken.ambient`. **Current:** *Ghjallina cocca*. **Alternatives:** *chjoccia*, *cucculeghja*.
- **Evidence:** *cocca* vik 9 (sense not checked); others not found.
- **Proposal:** keep. **Solidity:** unresolved. **Strings:** 1.

### Q22. Wolf sounds
- **Keys:** `subtitles.entity.wolf.growl`, `baby_wolf.ambient`, `*.pant`.
- **Current:** *ringhja* (growl, 12 strings with hoglin/zoglin/dragon), *ghjappa* (yip), *ansa* (pant).
- **Evidence:** *abbaghjà* Wiktionary "to bark" (used for `wolf.bark`, attested); *ringhjà*, *ghjappà*, *ansà* not found.
- **Change made:** `baby_wolf.pant` *ansima → ansa* (the 3 other "pants" strings use *ansa*; *ansima* is Italian).
- **Proposal:** keep. **Solidity:** attested (*abbaghja*), unresolved (others). **Strings:** 12.

### Q23. Buzz / whir
- **Keys:** `subtitles.entity.bee.*`, `block.beacon.ambient`, `parrot.imitate.breeze`. **Current:** *ronza*.
- **Evidence:** *ronza*, *ronzà* not found. **Proposal:** keep. **Solidity:** unresolved. **Strings:** 8.

### Q24. Splash / squish
- **Keys:** `subtitles.entity.axolotl.splash`, `slime.squish` (+ magma cube). **Current:** *sciaccuttuleghja*, *sciaccheghja*.
- **Evidence:** not found. **Proposal:** keep. **Solidity:** unresolved. **Strings:** 8.

### Q25. Creak / rattle
- **Keys:** `subtitles.entity.parrot.imitate.creaking`, creaking and skeleton subtitles. **Current:** *cricca* / *scricchjula*.
- **Evidence:** neither found. **Proposal:** keep the distinction. **Solidity:** unresolved. **Strings:** 10.

### Q26. Other sound verbs
- **Keys:** `subtitles.entity.drowned.ambient` (*gorgula*), `panda.worried_ambient` (*mugula*), `rabbit.ambient`
  (*squitta*), `strider.idle` (*piula*), `parrot.imitate.endermite` (*zampetta*).
- **Evidence:** none found. **Proposal:** keep. **Solidity:** unresolved. **Strings:** 7.

### Q27. Thunder
- **Key:** `subtitles.item.trident.thunder`. **Current:** *Tonu di u tridente scoppia*.
- **Evidence:** *tonu* vik 41 + Apertium (meaning not shown; *tonu* is also "tone"). **Proposal:** keep. **Solidity:** plausible. **Strings:** 1.

### Q28. Blowback proverb
- **Key:** `advancements.adventure.blowback.title`. **Current:** *Chì sumena ventu ricoglie timpesta*.
- **Evidence:** *sumena* vik 4, *timpesta* vik 51 + Apertium. Proverb wording not found.
- **Proposal:** keep; length is fine for a toast. **Solidity:** plausible. **Strings:** 1.

### Q29. Two Birds, One Arrow
- **Key:** `advancements.adventure.two_birds_one_arrow.title`. **Current:** *Dui pichjoni cù una freccia* (from IT).
- **Evidence:** *pichjone* vik 4. No Corsican idiom found. **Proposal:** keep. **Solidity:** plausible. **Strings:** 1.

### Q30. *Mettite pede*
- **Keys:** `advancements.adventure.minecraft_trials_edition.description`, `gui.friends.error.upgrade_needed`, `pack.folderInfo`.
- **Evidence:** mozilla:1892 "Update your Firefox browser" → "**Mittite** à livellu…" (also :1894, :1903); *mettite*
  in no reviewed resource.
- **Change made:** *Mettite → Mittite* in the 3 strings. **Solidity:** attested. **Strings:** 3.

### Q31. Husbandry
- **Key:** `advancements.husbandry.root.title`. **Current:** *Agricultura*. **Alternative:** *Allevu*.
- **Evidence:** *agricultura* vik 36, *allevu* vik 5; FR *Agriculture*, IT *Vita dei campi*. The tab covers breeding
  and farming. **Proposal:** keep. **Solidity:** plausible. **Strings:** 1.

### Q32. Debug Stick
- **Key:** `item.minecraft.debug_stick` (and every "debug" string).
- **Evidence:** "debug" → *spannatura* in mozilla:881 (Remote debugging), mozilla:1506–1507 (Debug menu → Listinu
  di spannatura); TBX debug → *spannà*. *Bastone* vik 21.
- **Proposal:** keep *Bastone di spannatura*; it reads as opaque only because the concept is technical. **Solidity:**
  attested (*spannatura*), plausible (compound). **Strings:** 18.

### Q33. Riptide, Channeling, Depth Strider
- **Keys:** `enchantment.minecraft.riptide`, `channeling`, `depth_strider`.
- **Current:** *Risacca*, *Canalizazione*, *Passu di l'abissi*.
- **Evidence:** *risacca*, *canalizazione* not found; the reviewed lexicons write *-izazione* with one *z* after
  *-iz-* (*sincrunizazione* 56 lines, *lucalizazione* 21, *persunalizazione* 4), so *canalizazione* follows the
  attested pattern; *abissi* vik 1.
- **Proposal:** keep. **Solidity:** plausible (*Canalizazione*), unresolved (others). **Strings:** 3.

### Q34. *equipatu*, *insellatu*
- **Keys:** `item.modifiers.any` (When equipped:), `item.modifiers.saddle` (When saddled:) and similar.
- **Evidence:** neither found; FR *À l'usage*, IT *Sul corpo*.
- **Proposal:** keep. **Solidity:** unresolved. **Strings:** 3.

### Q35. Pottery sherds
- **Keys:** `item.minecraft.sheaf_pottery_sherd`, `snort_…`, `mourner_…` (+ shard aliases).
- **Current:** *mannella*, *sbuffu*, *luttu*. **Evidence:** *mannella* vik 3, *luttu* vik 2, *gregna*, *sbuffu* not found.
- **Proposal:** keep. **Solidity:** plausible (*mannella*, *luttu*), unresolved (*sbuffu*). **Strings:** 6.

### Q36. Keyboard keys
- **Keys:** `key.keyboard.backspace`, `left.shift` / `right.shift`, `scroll.lock`.
- **Evidence:** Backspace → *tastu di ritornu in daretu* in upstream:12682 (attested); Scroll → *Sfilà* in
  upstream:3883, mozilla:1043 (attested); *maiuscule* "capital letters" mozilla:1176, upstream:6811 (attested as a
  word, not as a key name).
- **Proposal:** keep *Ritornu in daretu*, *Bloccu sfilà*; for *Maiuscule manca/diritta* the plural noun with a
  singular adjective is odd — a speaker should choose (*Maiuscula manca*? *Tastu maiuscule*?). **Solidity:**
  attested (Backspace, Scroll), unresolved (Shift). **Strings:** 6.

### Q37. Coined setting names
- **Keys:** `options.viewBobbing`, `options.vignette`, `options.prioritizeChunkUpdates`.
- **Current:** *Oscillazione di a vista*, *Affissà a vignettatura*, *Custruttore di pezzi*.
- **Evidence:** *oscillazione* vik 1; *vignettatura* not found; *pezzu* for chunk is attested (see Chunk below).
- **Proposal:** keep. **Solidity:** plausible. **Strings:** 3.

### Q38. Villager levels
- **Keys:** `merchant.level.1`–`5`. **Current:** *Principiante, Apprendista, Cumpagnu, Espertu, Maestru*.
- **Evidence:** *cumpagnu* Wiktionary "companion" (the guild sense of FR *compagnon* is not shown); *maestru* vik 117
  + Apertium; *espertu* vik 6; *principiante*, *apprendista* not found.
- **Proposal:** keep. **Solidity:** plausible (3–5), unresolved (1–2). **Strings:** 5.

### Q39. Realms NPCs and legal texts
- **Keys:** `mco.configure.world.spawnNPCs` (*Apparizione di PNG*), `mco.account.privacy.information`,
  `mco.account.privacyinfo`, `mco.configure.world.subscription.recurring.info`.
- **Evidence:** no Corsican abbreviation for NPC found; FR/IT avoid it (*Villageois*, *Villici*). In the legal texts this
  review only fixed spelling (*rispettendu → rispittendu*, *cunnettite → cunnittite*).
- **Proposal:** a human must read the legal and billing texts; for the toggle, *Apparizione di paisani* (as FR/IT)
  would avoid the abbreviation. **Solidity:** unresolved. **Strings:** 4.

### Q40. HP abbreviation
- **Key:** `multiplayer.player.list.hp` (*%s PS*). IT also uses *PS*; "health" → *salute* (mozilla:203).
- **Proposal:** keep. **Solidity:** plausible. **Strings:** 1.

## Part 2: the 30 most visible terms

Counts are keys containing the English term / the Corsican form after review.

| # | English (main keys) | Where seen | Current | Alternatives | Evidence | Proposal | Solidity | Strings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Survival (`selectWorld.gameMode.survival`, `gameMode.survival`, `itemGroup.inventory`) | Create World, F3, inventory tab | *Sopravivenza* | — | vik 3; **not** in lexicon-upstream as the glossary claimed (source corrected) | keep | plausible | 8 |
| 2 | Creative (`selectWorld.gameMode.creative`, `gameMode.creative`) | Create World | *Creativu* | — | *creativu* not found; *creatività* upstream:1427 | keep | plausible | 9 |
| 3 | Hardcore (`selectWorld.gameMode.hardcore`, `deathScreen.title.hardcore`) | Create World, death screen | *Estremu* | *Hardcore* | *Estremu* = "Extreme" upstream:3211; IT MC *Estrema* | keep | plausible | 12 |
| 4 | Singleplayer (`menu.singleplayer`, `title.singleplayer`) | title screen | *Ghjocu solu* | *Un ghjucadore* | *solu* vik 1010, *ghjocu* vik 125 + Apertium | keep | plausible | 7 |
| 5 | Multiplayer (`menu.multiplayer`, LAN screens) | title screen | *Parechji ghjucadori* | *Multighjucadore* (used in 2 tooltips: "portata multighjucadore") | *parechji* vik 1720, *ghjucadore* vik 149 + Apertium | keep; check button width | plausible | 18 |
| 6 | Seed (`selectWorld.enterSeed`, `seedInfo`, `commands.seed.success`, `mco.reset.world.seed`) | More World Options, /seed | ~~*Sementa*~~ → **Grana** | *sumente* | upstream:3807 (Audacity) "Random Seed:" → "**Grana** di numeru aleatoriu"; *sementa* in no resource | **changed** (8 strings, world/RNG seed only) | attested | 8 |
| 7 | Respawn (`deathScreen.respawn`) | death screen | *Rinasce* | *Riapparisce* | *rinasce* vik 8 + Apertium; *rinascita* vik 42 | keep | plausible | 19 |
| 8 | Item (`container.creative`, `inventory.binSlot`, tooltips, commands) | creative inventory, /give errors | *Ogettu* | *Elementu* (UI list item, wrong sense), *Oggettu* | *ogettu* vik 136 + Apertium; Mozilla's *elementu* (mozilla:68) is a list entry, not a thing | keep | plausible | 85 |
| 9 | Slot (`gui.togglable_slot`, `commands.item.*`) | crafter, /item errors | *Casella* | *Slot* | TMX mozilla-vpn-client "checkbox" → *casella* (close sense); vik 24 | keep | plausible | 39 |
| 10 | Hotbar (`inventory.hotbarInfo`, `itemGroup.hotbar`, `key.saveToolbarActivator`) | creative tab, HUD | *Barra rapida* | *barra d'attrezzi* (toolbar) | *barra d'attrezzi* = toolbar mozilla:868; *barra* + *rapida* plausible | keep | plausible | 16 |
| 11 | Inventory (`container.inventory`, `key.inventory`) | inventory screen | *Inventariu* | — | vik 17 | keep | plausible | 11 |
| 12 | Advancement (`gui.advancements`, `advancements.toast.*`) | advancements screen, toast | *Prugressu* | *Avanzamentu* | progress → *prugressione* mozilla:1913, *prugressi* TMX common-voice | keep | plausible | 38 |
| 13 | Crafting (`container.crafting`, `itemGroup.crafting`, recipe book) | inventory, crafting table | *Fabbricazione* | *Artisanat*-type calque avoided | *fabbricazione* vik 2, *fabbricà* vik 12 | keep | plausible | 22 |
| 14 | Enchantment (`container.enchant`, `enchantment.*`) | enchanting table, tooltips | *Incantesimu*, verb *incantà* | *Incantu* | *incantesimu* vik 1, *incantu* vik 11 | keep (a speaker may prefer *incantu*) | unresolved | 26 |
| 15 | Chunk (`options.chunks`, `menu.savingChunks`, F3) | Video settings, F3 | *Pezzu* | *Chunk* (IT MC) | upstream:3816, 3830, 3832 (Audacity) chunk(s) → *pezzu/pezzi* | keep | attested | 56 |
| 16 | Sneak (`key.sneak`) | Controls | *Accuvacciassi* | *Piattassi* | not found; *piattassi* vik 7 ("hide oneself") | keep | unresolved | 7 |
| 17 | Sprint (`key.sprint`, `options.sprintWindow`) | Controls | *Corre* | — | vik 25 + Apertium | keep | plausible | 7 |
| 18 | Spawn (`gamerule.doMobSpawning`, `menu.preparingSpawn`, spawner) | game rules, loading | *apparisce / apparizione*; Spawner *Generatore* | — | *apparisce* vik 46 + Apertium | keep | plausible | 146 |
| 19 | Mob (`gamerule.category.mobs`, `soundCategory.hostile`) | game rules, Music & Sounds | *Criatura* | *Mostru* (hostile only) | vik 27 | keep | plausible | 27 |
| 20 | Villager (`entity.minecraft.villager`, professions) | world, trading | *Paisanu* | *Abitante* | *paisanu* vik 12 + Apertium, *paisani* vik 39 | keep | plausible | 28 |
| 21 | Spawn Egg (`itemGroup.spawnEggs`, `item.minecraft.*_spawn_egg`) | creative tab | *Ovu generatore* | — | *ovu* vik 46 | keep | plausible | 91 |
| 22 | Resource Pack (`options.resourcepack`, `resourcePack.title`) | Options | *Pacchettu di risorse* | *Pack* | Package → *pacchettu* upstream:2421; Resources → *Risorse* upstream:8585 | keep | plausible | 20 |
| 23 | Data Pack (`selectWorld.dataPacks`) | Create World | *Pacchettu di dati* | — | *dati* Pontoon term; *pacchettu* as above | keep | plausible | 12 |
| 24 | Spectator (`selectWorld.gameMode.spectator`, `key.categories.spectator`) | game mode, death screen | *Spettatore* | — | vik 6 | keep | plausible | 9 |
| 25 | Render Distance (`options.renderDistance`) | Video settings slider | *Distanza di visualizazione* | *Distanza d'affissera* | *visualizazione* vik 9 + Apertium; Display → *Affissera* upstream:417 | keep; **long on a half-width slider ("Distanza di visualizazione : 12 pezzi")**: check in game | plausible | 3 |
| 26 | Done (`gui.done`) | every screen | *Fattu* | *Compiu* (mozilla:761) | Done → *Fattu* upstream:29 | keep | attested | 5 |
| 27 | Back (`gui.back`, `gui.to*`) | every screen | *Ritornu* | *Pagina precedente* (web only) | Back → *Ritornu* mozilla:1034 | keep | attested | 11 |
| 28 | Cancel (`gui.cancel`) | dialogs | *Abbandunà* | — | mozilla:257; 117 TMX segments | keep | attested | 16 |
| 29 | Quit (`menu.quit`, `deathScreen.quit.confirm`) | title screen | *Esce da u ghjocu* | *Esce di u ghjocu* | Quit → *Esce* upstream:7069; "Quit %1$s" → "Esce **di** %1$s" mozilla:711 | keep (*da* is also Corsican); a speaker may align on *di* | attested (*Esce*) | 11 |
| 30 | Options (`menu.options`, `options.title`) | title screen | *Ozzioni* | — | upstream:4181 | keep | attested | 42 |

### Other visible terms changed or questioned

- **Server → *servitore*** (88 strings: server list, LAN, Realms, telemetry). *Servore* was taken from the unreviewed
  Discord drafts; the reviewed Mozilla translations always write *servitore* (mozilla:38, :56; 112 lexicon lines,
  101 TMX segments, Pontoon). **attested**.
- **Chat → *chjachjerata*** (70 strings). upstream:256–257 and TMX (sumo) write *chjachjerata*; *chjachjarata* is in
  no resource. **attested**.
- **Title Screen → *listinu principale*** (5 strings harmonised: `gui.toTitle`, `narrator.screen.title`,
  `datapackFailure.title`, `options.realmsNotifications.tooltip`, telemetry). mozilla:2866 Main Menu → *Listinu
  principale*. `menu.returnToMenu` (*Arregistrà è vultà à u titulu*) was left short on purpose: the full form would
  be 41 characters on a pause-menu button. **attested**.
- **Console → *cunsola*** (upstream:9050), **Explore → *esplurà*** (mozilla:978, upstream:8113). **attested**.
- **Experience → *sperienza*** (18 strings): Mozilla writes *esperienza* (mozilla:1877, user experience), Common Voice
  *spirienza*; *sperienza* vik 29. Mixed evidence: **unresolved**, not changed.
- **At least → *almenu*** (8 strings): Mozilla writes *omancu* (mozilla:1207, :3388; 14 lines), but *almenu* has vik 125
  + Apertium. Both attested: not changed.
- **Seeds (items) → *Sementi di …*** (5 strings + 3 plant-sense strings with *sementa*): *sementi/sementa* are in no
  resource; Vikipedia has *sumente* (6) / *sumenti* (10). Plant sense not checked: **doubtful**, not changed.
- **On / Off** (`options.on/off` = *Sì / Nò*): reviewed lexicons use *Attivu / Inattivu* (3×) but also Off → *Nò*.
  Not changed.
- **Feminine plural of -e adjectives**: the consistency pass chose *-i* (*Baghe dolci, Liane pendenti, Terre
  sterili*), but Patriccollu's translations write *-e* for feminine plurals (25 cases, none against: *e forme
  plurale*, *e ricerche recente*, *e traccie individuale*, *l'unghjette esistente*), while Wiktionary lists only
  *-i* plurals (*verde → verzi*, *celeste → celesti*). The file now mixes both (*Foglie trasparente*, *Criature
  ostile* vs *Baghe dolci*). **unresolved**: a speaker should fix one rule, then a script can apply it.

## Still unresolved (short list)

Heraldry (152 strings); feminine plural of -e adjectives; Enchantment *incantesimu/incantu*; Sneak *accuvacciassi*;
Experience *sperienza/esperienza*; plant seeds *sementi/sumente*; Bush *arbustu/machja*; Shift key name; Nether Wart;
Potent Sulfur (*putente* vs *cuncentratu*); Gilded (*durata* clashes with "duration"); Dappled Forest (spotted vs
amber); Parched (*arsu*); Zombified (*zumbificatu/zombificatu*); Copper Bulb / Redstone Lamp; all sound verbs
(Q20–Q26); Lukewarm; plant names (Q11); villager levels 1–2; *equipatu/insellatu*; Realms legal texts and *PNG*.
