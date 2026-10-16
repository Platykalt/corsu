# Minecraft Java 26.3 in Corsican: second decision pass (October 2026)

**This is not a speaker validation.** An AI model wrote this pass by looking words up in the resources listed below.
Nothing here is "validated". Each case has one of the four solidity levels of [review.md](review.md):
**attested** (found with this meaning in a resource, cited), **plausible** (the form exists or follows Corsican
morphology, meaning not confirmed), **doubtful** (a resource points elsewhere), **unresolved** (no usable evidence).
Only a Corsican speaker can take a term past these levels. The questions left open here are also in
[review-batches/07-open-questions.md](review-batches/07-open-questions.md).

Each case also says what kind of question it is:

- **sense**: the current text may say something other than the English;
- **variant**: two or more spellings or words with the same sense, and the resources disagree or are silent;
- **editorial convention**: a choice that has to be made once for consistency, even if more than one form is correct.

## Resources consulted

Nothing was looked up on the web. INFCOR, Sapienzia and the BDLC were not consulted.

- `lexicon/lexicon-mozilla.tsv`, `lexicon/lexicon-upstream.tsv`: reviewed Corsican software translations
  (Patriccollu di Santa Maria è Sichè and Mozilla's Corsican team), cited `mozilla:LINE` / `upstream:LINE`.
- Mozilla Pontoon TMX `co.all-projects.tmx` ("TMX") and Pontoon terminology.
- Patriccollu's repository `Lingua_Corsa-Infurmatica` (unzipped; few hits, as most of its files are binary).
- `tools/corsican_words.py lookup`: Vikipedia counts, Apertium, Pontoon terms, Wiktionary (kaikki dump).
- The local Vikipedia dump `cowiki-latest-pages-articles.xml` (the corpus that `corsican_words.py` counts), read
  in context ("Vikipedia KWIC") to see what a form means, not just whether it exists. Vikipedia mixes northern
  and southern spellings and many authors, so it shows how words are used, not a norm.
- Apertium's `apertium-cos.cos.dix` (its inflection paradigms).
- English, French and Italian 26.3 files, for the sense of each string.
- `lexicon/lexicon.tsv` (draft translations) is **not** evidence; it is cited only where the task concerns it.

## Summary

| # | Case | Kind | Recommendation | Solidity | Applied in `co_fr.json`? |
| --- | --- | --- | --- | --- | --- |
| D1 | Server: *servitore* / *servore* | variant | *servitore* everywhere, including Discord | attested | already (88 strings, earlier pass); Discord: recommendation only |
| D2 | Feminine plural of *-e* adjectives (*baghe dolci / dolce*) | editorial convention | *-e* after a feminine noun in *-e* (*Baghe dolce*); *-i* after masculine nouns; nouns in *-ioni* left open | plausible (majority usage, not a grammar rule) | **yes, 13 strings** |
| D3 | Enchantment: *incantesimu* / *incantu* | sense | keep *incantesimu* (game mechanic, spell), *incantà* (verb), *incantu* only for "charming" | attested (sense "spell", Vikipedia) | no change needed |
| D4 | Sneak: *accuvacciassi* | variant | keep; ask a speaker | unresolved | no |
| D5 | Seeds: *sementi / sementa* | variant | *sumente* (plural); singular avoided | attested (plural) | **yes, 8 strings** |
| D6 | Bush: *arbustu* / *machja* | sense | keep *arbustu* | plausible | no |
| D7 | Experience: *sperienza* / *esperienza* / *spirienza* | variant | keep *sperienza* | plausible | no (glossary source corrected) |
| D8 | Banner heraldry | sense + convention | keep; a speaker with heraldry knowledge must decide | unresolved | no |
| D9 | Animal sound verbs | variant / sense | keep; *bela*, *abbaghja*, *mughja* found; *cocca*, *ansa* doubtful; Celebrate harmonised on *festighjeghja* | mixed; *festighjeghja* attested | **yes, 7 strings** (Celebrate only) |
| D10 | Lukewarm: *tepidu* | variant | keep | unresolved | no |
| D11 | Potent Sulfur: *Zolfu putente* | sense | *Zolfu cuncentratu* if a speaker agrees with the FR/IT reading | doubtful (current) | no |
| D12 | Gilded Blackstone: *Petranera durata* | sense (homonym) | *Petranera indurata* | plausible (1 Vikipedia hit) | **yes, 1 string** |
| D13 | Dappled Forest: *Furesta chjazzata* | sense | *Furesta ambrata* (as FR/IT); check in game | plausible | **yes, 3 strings** |
| D14 | Villager levels | variant | keep | plausible (1, 3–5), unresolved (2) | no |
| D15 | Realms legal and billing texts | sense | need a human reading; one status label fixed | unresolved (texts); attested (fix) | **yes, 1 string** (`mco.selectServer.open`) |

**33 strings changed** (33 keys), each logged in [changes-review.tsv](changes-review.tsv) with old text, new text,
reason and solidity. `tools/minecraft.py check`: 0 errors; `verify`: 0 problems.

---

## D1. Server: *servitore* vs *servore*

- **Occurrences in `co_fr.json`:** *servitore* 79 strings, *servitori* 10; *servore* 0 (replaced by the previous
  review, see changes-review.tsv). Senses in the game: the multiplayer server list (`selectServer.*`,
  `addServer.*`, `multiplayer.*`), LAN games, Realms (`mco.*`: a Realm is a server hosted by Mojang), and the
  network sense in technical errors and telemetry. In every case it is the same thing: a machine or service that
  hosts the game.
- **Sources:** *servitore* in lexicon-mozilla (32 lines, e.g. mozilla:38 "Unexpected response from server →
  Risposta inespettata da u servitore", mozilla:56, mozilla:175 mail server), lexicon-upstream (61 lines), TMX 81
  segments (+30 *servitori*), Pontoon terminology, Patriccollu's repository (9 hits); Vikipedia 1 (+11 *servitori*).
  *servore / servori*: no attestation found in the resources consulted. They appear only in the draft
  `lexicon/lexicon.tsv`: 1,968 lines in its Discord section and 254 elsewhere (mostly the "spelling variants" header
  at the top). The same draft file has 640 lines with *servitore* outside the Discord section, so the project
  already mixes both words.
- **Discord sense:** a Discord "server" is a community space, but Discord calls it a server in every language it
  ships (FR *serveur*, IT *server*), and it is hosted on Discord's machines like a Realm. No source gives a separate
  Corsican word for it. Nothing found justifies a word for Discord that is different from the one for Firefox,
  Thunderbird and Minecraft.
- **Kind:** variant (same sense). **Recommendation:** *servitore / servitori* everywhere. For `lexicon/lexicon.tsv`
  (not edited here, as asked): replace *servore → servitore* and *servori → servitori* in the Discord section and in
  the variants header, with the usual contractions (*di u servitore*, *nant'à u servitore*). One possible worry for
  a speaker: *servitore* also means "servant" in older usage, but the Mozilla team uses it in the computing sense in
  over a hundred strings.
- **Solidity:** attested. **Applied:** yes in Minecraft (earlier pass); Discord: recommendation only.
- **Correction (2026-10-16):** *servore* is attested in the computing sense too. ADECEC's
  [Lingua corsa è Internet](https://adecec.net/parutions/lingua-corsa-%C3%A8-Internet.html) reprints the 1999
  Ghjurnata di a Lingua Corsa paper by Ghjacumu Thiers and Cristofanu Filippi (Università di Corti), which writes
  "u servore di testi literarii" and "U servore hà trè rubriche". The statement above that it has no attestation
  only described the resources consulted, so it does not justify replacing it everywhere. Both forms are valid.
  *Servitore* stays the editorial choice where it was already applied (Minecraft). Discord keeps *servore* unless
  the maintainer decides otherwise, and that decision is separate from bug fixing.

## D2. Feminine plural of adjectives in *-e*

The question: an adjective whose singular ends in *-e* for both genders (*dolce, verde, grande, pendente, sterile,
ostile, illegale, fabbricabile*): after a feminine plural noun, is it *-e* (*baghe dolce*) or *-i* (*baghe dolci*)?
Adjectives in *-u/-a* (*rossu/rossa → rossi/rosse*) are not concerned.

**Every occurrence in `co_fr.json` (feminine plural noun + adjective in *-e/-i*) before this pass:**

| Keys | Text | Ending |
| --- | --- | --- |
| `item.minecraft.sweet_berries`, `block.minecraft.sweet_berry_bush`, `death.attack.sweetBerryBush`, `death.attack.sweetBerryBush.player` | (Arbustu di) baghe dolci | -i |
| `block.minecraft.weeping_vines`, `block.minecraft.weeping_vines_plant`, `death.fell.accident.weeping_vines`, `gamerule.doVinesSpread.description` | liane pendenti | -i |
| `biome.minecraft.end_barrens` | Terre sterili di l'End | -i |
| `biome.minecraft.lush_caves` | Grotte verdi | -i |
| `gui.recipebook.toggleRecipes.craftable` | Ricette fabbricabili | -i |
| `gui.banned.reason.drugs`, `gui.abuseReport.reason.alcohol_tobacco_drugs.description` | droghe illegali | -i |
| `menu.custom_screen_info.contents` | e vostre infurmazioni persunali (noun in *-ioni*) | -i |
| `options.cutoutLeaves` | Foglie trasparente | -e |
| `options.difficulty.easy.info`, `.normal.info`, `.hard.info`, `soundCategory.hostile` | (E) criature ostile | -e |
| `gamerule.forgiveDeadPlayers.description`, `gamerule.universalAnger.description`, `gamerule.minecraft.universal_anger.description` | E criature neutrale | -e |
| `generator.single_biome_floating_islands` | Isule volante | -e |

So the file was mixed: 14 strings with *-i*, 9 with *-e*. The *-i* forms were introduced by the October 2026
consistency pass ("plural of *-e* adjectives is *-i*", decisions.md); the original translations had *-e*.
(`gamerule.*SourceConversion.description` "duie surgente" is a noun, not an adjective; Vikipedia also writes
"e surgente".)

**What the resources show:**

| Resource | Feminine noun in *-e* + adjective | Examples |
| --- | --- | --- |
| lexicon-mozilla / lexicon-upstream | about 60 with *-e*, 1 with *-i* | upstream:6741, 7023, 7145 "e forme plurale"; mozilla:900, 2990 "e ricerche recente"; upstream:6752, 7110 "e traduzzioni uguale"; upstream:8980–8989 "Preferenze generale"; mozilla:3028 "unghjette esistente"; upstream:992 "traccie individuale". Against: upstream:6051 "in parti uguali" |
| Mozilla TMX | 15 with *-e*, 0 with *-i* (pattern "e Xe Y") | "ricerche recente" 9×, "infurmazioni persunale" 4× |
| Vikipedia (many authors) | 339 with *-e*, 30 with *-i* | -e: "e guerre civile", "E stelle cadente", "e truppe imperiale", "e surgente minore", "L'ale sò trasparente"; -i: "e guerre civili", "e risorse naturali", "e forze speciali" |
| Vikipedia, noun in *-ioni* | 2 with *-e*, 13 with *-i* | "e regioni culturale" vs "e relazioni internaziunali", "e pupulazioni lucali" |
| Apertium `apertium-cos.cos.dix:803–806` | paradigm `naziunal/e__adj`: singular *-e*, plural *-i*, both genders | *dolce, verde, grande, putente* use it |
| Wiktionary (kaikki) | one plural, no gender given | *verde → verzi*, *celeste → celesti*, *nucleare → nucleari* |
| Masculine plurals (Vikipedia, "i Xi Y") | 1,801 with *-i*, 38 with *-e* | lexicons: "dati persunali", "schedarii recenti" |

**Reading:** the usage corpora (two software corpora and the multi-author Vikipedia) agree that a feminine noun in
*-e* takes an adjective in *-e*, with a minority of *-i*; with a noun in *-ioni* the evidence splits (Mozilla *-e*,
Vikipedia mostly *-i*). The dictionary-type resources (Apertium, Wiktionary) give *-i* without distinguishing the
genders. This does **not** establish a grammar rule: it shows a strong majority practice in written northern
Corsican, and the reviewed software translations that STYLE.md takes as its spelling reference follow it.

- **Kind:** editorial convention.
- **Recommendation and change made:** provisional convention "feminine noun in *-e* + adjective in *-e* → *-e*":
  13 strings changed (*Baghe dolce*, *Liane pendente*, *Terre sterile*, *Grotte verde*, *Ricette fabbricabile*,
  *droghe illegale*). Masculine plurals keep *-i* (*mondi persunalizati*, *dati persunali*). The noun-in-*-ioni*
  case (`menu.custom_screen_info.contents`, *infurmazioni persunali*) is left as it is, because the corpora disagree.
  This supersedes the line "plural of *-e* adjectives is *-i*" in decisions.md for feminine nouns; STYLE.md should
  say so the next time it is edited (not edited in this pass).
- **For a speaker:** which form do you write and say: *e baghe dolce* or *e baghe dolci*? *e criature ostile* or
  *ostili*? If *-i*, the 22 strings above can be switched by a script in one go.
- **Solidity:** plausible (majority usage, 3 corpora); no grammar source states it as a rule. **Applied:** yes, 13 strings.

## D3. Enchantment: *incantesimu* vs *incantu*

- **Occurrences:** *incantesimu/incantesimi* in 15 strings: the game mechanic (`commands.enchant.*`,
  `container.enchant.level.*`, `container.repair.cost`, `block.minecraft.enchanting_table` *Bancu d'incantesimi*,
  `item.minecraft.experience_bottle` *Buttiglia d'incantesimu*) and "spell" (`subtitles.entity.evoker.cast_spell`,
  `illusioner.cast_spell` *lancia un incantesimu*). *incantu* in 1 string: `subtitles.entity.evoker.prepare_wololo`
  "Evoker prepares charming" → *prepara un incantu*. Verb *incantà* (`container.enchant`, advancement), participle
  *incantatu* (Enchanted Book, Enchanted Golden Apple, `stat.minecraft.enchant_item`).
- **Senses found (Vikipedia KWIC):** *incantesimu* = a magic spell: "l'incantesimi trasmessi a notte di Natale"
  (the Christmas Eve charms of Corsican tradition), "l'incantesimi di Circi", "u bon esitu di l'incantesimu".
  *incantu* = charm, delight, "as if by magic": "guarisce cum'è per incantu", "a tarra di l'incantu", "d'incantu".
  *incantà* = to charm, to captivate ("capace d'incantà, d'affascinà"); *incantatu* = spellbound. No hit in the
  reviewed lexicons or the TMX (software has no such term).
- **Kind:** sense. A Minecraft enchantment is a magic property put on an item, closer to a spell than to "charm"
  (IT *incantesimo*). *incantu* fits "charming" (the wololo spell) and is used there.
- **Recommendation:** keep *incantesimu* for the mechanic, *incantà / incantatu* for the verb, *incantu* for
  "charming" only. A speaker may still prefer another word for the item property.
- **Solidity:** attested (sense "spell" of *incantesimu*, Vikipedia, 3 contexts). **Applied:** nothing to change.

## D4. Sneak: *accuvacciassi*

- **Occurrences (7):** `key.sneak` *Accuvacciassi*, `attribute.name.sneaking_speed` and
  `attribute.name.player.sneaking_speed` *Velocità accuvacciata*, `enchantment.minecraft.swift_sneak`
  *Accuvacciata rapida*, `stat.minecraft.sneak_time` *Tempu accuvacciatu*, `stat.minecraft.crouch_one_cm`
  *Distanza accuvacciata*, `advancements.adventure.avoid_vibration.description` *Accuvacciatevi*. In the game,
  Sneak = crouch (FR *S'accroupir*, IT *Accovacciati*).
- **Sources:** *accuvacc-*: no attestation found in the resources consulted. *acciucciatu* 1 Vikipedia hit
  (southern-spelling text, "asinu ... acciucciatu", "crouched/lying"); *piattassi* = "to hide oneself" (Vikipedia
  5 contexts, Apertium *piattà*): a different sense (hiding, not crouching).
- **Kind:** variant (the sense is clear; the Corsican verb is not).
- **Recommendation:** keep; ask a speaker for the everyday verb for "crouch" (*accuvacciassi*? *acciucciassi*?
  *aggrancassi*?). *Piattassi* would change the meaning.
- **Solidity:** unresolved. **Applied:** no.

## D5. Seeds: *sementi / sementa* → *sumente*

- **Occurrences (8):** item names `item.minecraft.wheat_seeds`, `beetroot_seeds`, `melon_seeds`, `pumpkin_seeds`,
  `torchflower_seeds` (*Sementi di ...*); singular *sementa* in `advancements.husbandry.plant_seed.description`,
  `advancements.husbandry.plant_any_sniffer_seed.description`, `subtitles.entity.sniffer.drop_seed`. The world seed
  (*Grana*) is a different sense, settled in review.md.
- **Sources:** *sementi, sementa, semente*: no attestation found in the resources consulted. *sumente*: Vikipedia 6,
  with the seed sense in context ("frutti è sumente", "un catalogu americanu di sumente", "hà purtatu cun ellu e
  sumente", "e prime sumente di a fede", figurative); *sumenti* (southern spelling) 10, same sense ("banchi di
  sumenti"); verb *sumenà* in the file's proverb (*Chì sumena ventu*). Singular: *sumenta* 1 hit (southern text,
  "seed/semen" sense); the northern singular was not confirmed.
- **Kind:** variant (Italian-looking *sement-* vs Corsican *sument-*, with the pretonic *e → u* the file uses
  elsewhere).
- **Change made:** *Sumente di granu / di zucca / ...*; the three singular strings were rewritten with the plural,
  like the Italian and French files (*Piantate sumente è fighjatele cresce*; *Piantate una di e sumente
  d'annusadore*; *Annusadore lascia sumente*), so no unconfirmed singular is used.
- **For a speaker:** is the singular *una sumente* or *una sumenta*? Is *sumente* the word you use for garden seeds,
  or *granu / grana*?
- **Solidity:** attested (plural, Vikipedia); singular unresolved. **Applied:** yes, 8 strings.

## D6. Bush: *arbustu* vs *machja*

- **Occurrences (8):** `block.minecraft.bush` *Arbustu*, `dead_bush` *Arbustu seccu*, `potted_dead_bush`,
  `firefly_bush` *Arbustu di lucciule*, `sweet_berry_bush` and its two death messages.
- **Sources:** *arbustu* Vikipedia 76, with the botanical sense "shrub" in context ("A ghjinestra hè un arbustu",
  "una spezia d'arbustu"). *machja*: Wiktionary "shrub, bush; macchia (shrubland)", Apertium, Vikipedia 114, but
  the contexts show mainly the maquis as a landscape ("una machja corta", "a machja corsa") and "spot, stain"
  ("una machja bianca annantu à u bavellu").
- **Kind:** sense. A Minecraft bush is one plant; *machja* most often names the maquis or a stain.
- **Recommendation:** keep *Arbustu*. A speaker may say whether *una machja* is natural for a single bush in speech.
- **Solidity:** plausible (sense of *arbustu* found; naturalness not confirmed). **Applied:** no change.

## D7. Experience: *sperienza* / *esperienza* / *spirienza*

- **Occurrences (18):** `entity.minecraft.experience_orb` *Sfera di sperienza*, `commands.experience.*` (10),
  `argument.entity.options.level.description`, `gamerule.doMobLoot.description`, `gamerule.doTileDrops.description`,
  `subtitles.entity.experience_orb.pickup` *Sperienza guadagnata*, `mco.backup.entry.worldType.experience`,
  `mco.configure.world.edit.subscreen.experience` (a Realms "experience" = a ready-made world).
- **Sources:** *sperienza* Vikipedia 29 (sense "experience": "a sperienza di u sacru", "u studiu è a sperienza");
  *esperienza* lexicon-mozilla:1877, 1930, 1934, 1941 (user/browsing experience), TMX 12; *spirienza* Apertium
  lemma, Vikipedia 11, TMX 2 (Common Voice). The glossary claimed "lexicon-upstream, practice": *sperienza* is
  **not** in lexicon-upstream; the glossary row was corrected (status *proposal*).
- **Kind:** variant (same sense; three forms, each attested somewhere).
- **Recommendation:** keep *sperienza* (most frequent in the general corpus, regular with the file's other forms).
  If the project wants to follow Mozilla's spelling everywhere, *esperienza* is the alternative.
- **Solidity:** plausible. **Applied:** no.

## D8. Banner heraldry

- **Occurrences:** 43 patterns × 16 colours (`block.minecraft.banner.<pattern>.<colour>`) plus the pattern items
  (`item.minecraft.*_banner_pattern*`), about 690 strings. The heraldic partitions are calqued on Italian heraldry:
  *Partitu* (Per Pale), *Troncatu* (Per Fess), *Trinciatu* (Per Bend), *Tagliatu* (Per Bend Sinister), *inversu*,
  *à diritta / à manca* for dexter/sinister (seen from the bearer), *in capu / in punta* for chief/base, *Palu,
  Fascia, Banda, Sbarra, Cantone, Bordu, Tondu, Rombu*. FR uses blazon (*de gueules*), IT plain colour adjectives.
- **Sources:** *troncatu, trinciatu*: no attestation found in the resources consulted; *partitu* (205) and
  *tagliatu* (27) occur in Vikipedia only in other senses ("party", "cut"); *stemma* 208 and *blasone* 141 exist
  (mostly infobox fields), with no blazon text found. Colour agreement was checked in review.md (consistent).
- **Kind:** sense (do the terms mean anything to a Corsican reader?) + editorial convention (blazon or plain
  description).
- **Recommendation:** keep for now. Ask a speaker who knows heraldry (the Moor's head arms) whether to keep the
  Italian-style terms or switch to plain descriptions (*Mità diritta rossa*, *Mità suprana rossa*). The pattern list is
  in [04-banner-heraldry.md](review-batches/04-banner-heraldry.md).
- **Solidity:** unresolved. **Applied:** no.

## D9. Animal and mob sound verbs

- **Occurrences:** about 170 subtitles (`subtitles.entity.*`), grouped by verb in
  [05-animal-sounds.md](review-batches/05-animal-sounds.md).
- **Sources (Vikipedia KWIC, Wiktionary):**
  - *abbaghja* (bark): Wiktionary "to bark", Vikipedia 20. **attested.**
  - *bela* (bleat, sheep and goat): Vikipedia "Bela la capra, la pecura è l'agnedda". **attested.**
  - *mughja* (moo / roar): Vikipedia "u ventu mughja", "u ghjucatore mughja" (roar, shout). Used for Cow, Ravager,
    Warden, parrot. **plausible** for the cow (sense "bellow" found, not "moo" specifically).
  - *cocca* (chicken clucks): the 14 Vikipedia hits are the noun *cocca* (the mushroom *Amanita caesarea*); no
    verb sense found. **doubtful.**
  - *ansa* (pants: wolf, puppy, panda): the 4 Vikipedia hits are the noun *ansa* "river bend". The previous pass
    harmonised *ansima → ansa*; the verb sense was not found. **doubtful.**
  - *annitrisce*, *ronza*, *ringhja*, *ghjappa*, *miaula*, *ronfa*, *grugna*, *gracchja*, *squitta*, *piula*,
    *gorgula*, *mugula*, *scricchjula*, *cricca*, *sbuffa*, *fischja*, *sciaccheghja*, *sciaccuttuleghja*: no
    attestation found in the resources consulted. *raglia*: 1 hit in a non-Corsican dialect quotation.
- **Kind:** variant for most (the sense is clear), sense for *cocca* and *ansa* (the found sense is another word).
- **Change made:** "celebrates" (`subtitles.entity.{evoker,piglin,pillager,ravager,villager,vindicator,witch}.celebrate`)
  had two forms in the file, *festeghja* (6) and *festighja* (1), neither found in the resources consulted. Vikipedia
  writes the verb *festighjà*, present *festighjeghja* (15 hits, sense "celebrate": "si festighjeghja a Purificazione
  di Maria"). All 7 now read *festighjeghja* (attested).
- **Inconsistencies left for a speaker:** "grunts" is *grugna* (pig, ravager, sniffer, zombified piglin) or *grunghje*
  (armadillo, camel, baby pig); "rattles" is *scricchjula* (skeletons) while the Creaking *scricchja*.
- **Recommendation:** otherwise keep; ask a speaker verb by verb (batch 05). Replacing an without attestation in the resources consulted verb by another
  without attestation in the resources consulted one would not improve anything.
- **Solidity:** attested (*abbaghja, bela, festighjeghja*), plausible (*mughja*), doubtful (*cocca, ansa*),
  unresolved (rest). **Applied:** 7 strings (Celebrate).

## D10. Lukewarm Ocean: *tepidu*

- **Occurrences (2):** `biome.minecraft.lukewarm_ocean` *Oceanu tepidu*, `deep_lukewarm_ocean` *Oceanu tepidu
  prufondu*.
- **Sources:** *tepidu, tèpidu, tiepidu, tebbiu, calducciu*: no attestation found in the resources consulted
  (lexicons, TMX, Vikipedia dump, Corsican Wiktionary dump).
- **Kind:** variant (sense clear: lukewarm, between warm and cold oceans).
- **Recommendation:** keep; ask a speaker. **Solidity:** unresolved. **Applied:** no.

## D11. Potent Sulfur

- **Occurrences (1 + 1):** `block.minecraft.potent_sulfur` *Zolfu putente*; its subtitle
  `subtitles.block.potent_sulfur.geyser_eruption` *Surgente di zolfu sbotta* (EN "Sulfur spring bursts"). New 26.3
  block that erupts like a geyser in Sulfur Caves.
- **Sources:** *putente* Vikipedia 85 + Apertium (powerful); *cuncentratu* Vikipedia 2, upstream:4373 (sense
  "focused"). FR *Soufre concentré*, IT *Zolfo concentrato*.
- **Kind:** sense. "Potent" can mean "powerful" (current) or "strong, concentrated" (FR/IT). The current text is a
  possible literal reading, not a clear mistranslation.
- **Recommendation:** *Zolfu cuncentratu* if a speaker agrees with the FR/IT reading; otherwise keep.
- **Solidity:** doubtful (current). **Applied:** no.

## D12. Gilded Blackstone: *Petranera durata* → *Petranera indurata*

- **Occurrences:** `block.minecraft.gilded_blackstone` (1). Elsewhere in the file *durata* is the noun "duration"
  (`commands.worldborder.warning.time.failed`, `telemetry.event.world_unloaded.description` twice, and other
  telemetry strings; *durata* in 72 lexicon-upstream lines, 64 of them with English "duration/length/time" and none with "gilded").
- **Sources:** *indurata* Vikipedia 1 hit, in a literary text, with the gilded sense ("a me' cresta indurata ! u me'
  fioccu inargintatu !", gilded beside silvered); *dorata/doratu* Vikipedia 1 each (an animal and a fish name,
  Italian-influenced); *duratu* in the "gilded" sense: no attestation found.
- **Kind:** sense (homonym: a player reads "Blackstone duration").
- **Change made:** *Petranera indurata*. **For a speaker:** is *induratu* the usual word for "gilded", or *doratu*?
- **Solidity:** plausible (one hit with this sense). **Applied:** yes, 1 string.

## D13. Dappled Forest: *Furesta chjazzata* → *Furesta ambrata*

- **Occurrences (3):** `biome.minecraft.dappled_forest`, `filled_map.dappled_forest_camp_map`,
  `filled_map.dappled_forest_abandoned_camp`.
- **Context:** new 26.3 biome; the same update adds poplars with yellow, orange and red leaves. FR *Forêt ambrée*,
  IT *Foresta ambrata*: both official translations name the forest by its amber colour, not by "spots".
- **Sources:** *chjazzatu/chjazzata*: no attestation found in the resources consulted (and *chjazza* "square"
  suggests a different word). *ambrata*: Vikipedia 4, colour sense ("una lebbia tinta ambrata"). *machjata/machjatu*
  ("spotted"): Vikipedia 2 ("grisgiu-brunu machjata di biancu"), the alternative if the English "dappled" is to be
  kept literally.
- **Kind:** sense. The previous text used an without attestation in the resources consulted word for a reading that both reference translations reject.
- **Change made:** *Furesta ambrata* (3 strings). Check the biome in game: if it is mottled light rather than
  amber leaves, *Furesta machjata* is the attested alternative.
- **Solidity:** plausible. **Applied:** yes, 3 strings.

## D14. Villager levels

- **Occurrences:** `merchant.level.1`–`5`: *Principiante, Apprendista, Cumpagnu, Espertu, Maestru* (EN Novice,
  Apprentice, Journeyman, Expert, Master; FR *Novice, Apprenti, Compagnon, Expert, Maître*). Shown in the trading
  screen title ("Paisanu - Principiante").
- **Sources:** *principianti* Vikipedia 3 (sense "beginners": "megliu per i principianti"); *apprendista*: no
  attestation found in the resources consulted; *cumpagnu* Wiktionary "companion", Vikipedia 41 (guild sense not
  shown); *Espertu* upstream:14447 (Expert → Espertu); *maestru* Vikipedia 115 + Apertium.
- **Kind:** variant (the sense is clear; the guild words are the question).
- **Recommendation:** keep. Ask a speaker about *Apprendista* (Italian-looking? *Garzone*?) and whether *Cumpagnu*
  reads as the trade rank.
- **Solidity:** plausible (1, 3, 4, 5), unresolved (2). **Applied:** no.

## D15. Realms legal and billing texts

- **Occurrences:** privacy and parental consent `mco.account.privacy.information`, `mco.account.privacyinfo`,
  `mco.account.privacy.info`; terms `mco.terms.title`, `mco.terms.sentence.1` + `.2` (*Accettu e* + *Cundizioni
  d'utilizazione di Minecraft Realms*, the second part is a link), `mco.terms.buttons.agree/disagree`,
  `mco.errorMessage.6002`; billing `mco.configure.world.subscription.*`, `.recurring.info`, `.recurring.daysleft`
  (*Rinnuvatu autumaticamente in*), `mco.notification.transferSubscription.message`, trial and purchase
  (`mco.selectServer.trial`, `.buy`, `.freeTrial`, `mco.pdp.trial.description`); `mco.configure.world.spawnNPCs`
  (*Apparizione di PNG*).
- **Sources:** these texts were translated from English with the usual terms (*abbunamentu*, *fatturazione*,
  *cunsensu*, *RGPD*); only spelling was corrected in the previous review. No Corsican legal reference was consulted.
- **Change made (sense):** `mco.selectServer.open` *Apre u Realm* → *Realm apertu*. This key is the status shown in
  the Realms list, beside `mco.selectServer.closed` *Realm disattivatu* and `.expired` *Realm scadutu* (FR *Realm
  ouvert*, IT *Realm aperto*); the "open" action is `mco.selectServer.openserver`, which keeps *Apre u Realm*.
- **Recommendation:** a human must read the legal and billing texts (batch 06). These are translations of
  Mojang's texts with no legal force in Corsican; the English or French terms remain the reference.
  For `spawnNPCs`, *Apparizione di paisani* (like FR/IT) would avoid the abbreviation *PNG*.
- **Note:** *Rinnuvatu* (`recurring.daysleft`) vs *Rinnovà* (`expiredRenew`, changed in the previous review after
  mozilla:272, 303): the participle *rinnovatu* was not found in the resources consulted either; left for a speaker.
- **Solidity:** unresolved (texts); attested (the status fix: *apertu* mozilla:407). **Applied:** 1 string.

## Still for a speaker

D2 (confirm *-e* or *-i*; nouns in *-ioni*), D4, D5 (singular), D6 (naturalness), D7, D8, D9, D10, D11, D12
(*induratu* vs *doratu*), D13 (in-game check), D14, D15, plus the open items of decisions.md and review.md
(Nether Wart, Copper Bulb, Zombified, Shift key, plant names). All are collected in
[review-batches/07-open-questions.md](review-batches/07-open-questions.md).
