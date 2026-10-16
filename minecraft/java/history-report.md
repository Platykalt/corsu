# Corsican for older Minecraft releases: history.json report

Status: done for every pair, October 2026. Written by an AI (agent B); **no entry has been reviewed by a Corsican
speaker** (`review: "ai"` everywhere). Contract: [MULTIVERSION.md](MULTIVERSION.md). Tool: `tools/mchistory.py`.

## What was handled

Mojang's English of the 86 releases 1.6.1 to 26.2 compared with 26.3: **3,978** unique (key, English) pairs are
not 26.3's own (key, English), and **every one has an entry** in `history.json`; with keys.tsv, no (key, hash)
of any release resolves to nothing (`python tools/mcversions.py verify all --no-engine`: 87 releases, full
coverage, 0 errors).

Second pass (after keys.tsv): the first pass used the client jars' `en_us` only (3,902 pairs). The full English
of each release written by `mcversions.py fetch` (`~/.cache/corsu/minecraft/<id>/multiversion/english.json`)
also has the Realms texts that lived outside `en_us` (com.mojang:realms jar 1.7.10-1.14.3,
`assets/realms/lang` 1.14.4-1.19.2) and `narrator.select.list.position` (1.14-1.16.5). This added 78 pairs
(76 `mco.*`, all translated, 26.3 Realms wording reused where the English is the same or trivially changed;
the old Realms library writes its line breaks as a literal `\n`, kept as is) and removed 2 entries that turned
out to be 26.3's own text (`mco.snapshotRealmsPopup.*`, the 26.3 Realms file still has the older wording). The
3 empty English texts of 1.7 (`options.aoDesc1`, `options.viewBobbingDesc1`, `options.renderCloudsDesc1`) now
have an empty Corsican entry, so the packs cover them (the checker allows an empty Corsican only for the hash of
the empty text, `da39a3ee5e6b`).

## Method

1. `mchistory.py classify` puts every pair in one class:
   - **trivial**: the key exists in 26.3 and the English differs only in case, punctuation or spacing, with the
     same placeholders (`Track output` / `Track Output`). The 26.3 Corsican is reused, with this English's final
     punctuation (colon, ellipsis, full stop) when it differs (`adapted`).
   - **renamed**: the key is not in 26.3 but the same English is, under another key (mostly the 1.13 renaming:
     `tile.stone.name` → `block.minecraft.stone`, `item.swordIron.name` → `item.minecraft.iron_sword`,
     `entity.Zombie.name`, `stat.*`, `achievement.*` → `advancements.*`, `enchantment.*`, `potion.*`). The 26.3 key
     is chosen among the keys of the same family (`tile` → block or item, `item` → item or block, `entity` →
     entity, `potion` → effect or item…, table `FAMILIES`), then by shared words in the key names. Pairs with no
     key of the same family, or with several 26.3 translations, were flagged and checked by hand (see below).
   - **absent**: the English is found nowhere in 26.3 (removed content, old options, old commands): translated.
   - **changed**: the key is in 26.3 but its English changed in sense or placeholders: the 26.3 Corsican is reused
     when it still says exactly the old English, otherwise adapted or retranslated.
   - **ambiguous**: a best translation is given and `note` starts with `ambiguous:` (list below).
   - **empty**: empty English.
2. `mchistory.py propose` wrote the renamed proposals; all 1,761 were read (key, English, 26.3 key, Corsican).
   Corrections: `Sign` (block) had been matched to the button `book.signButton` (*Firmà*) and became *Cartellu*;
   `tile.netherBrick.name` "Nether Brick" is the block (*Matoni di u Nether*, `adapted`), not the brick item; old
   potion prefixes "Clear"/"Fancy" were not taken from the keyboard key or the graphics option (feminine
   adjectives for *Pozione* instead); 1.12 logs "Oak Wood" keep the 26.3 *Legnu di quercia* (same English) with a
   note.
3. Every other pair was translated or adapted by hand following STYLE.md and glossary.tsv, looking up how 26.3
   translates the same concept in co_fr.json (*servitore*, *chjachjerata*, *prugressu* for advancement, *successu*
   for the old achievements, *tavula di punti*, *etichetta di dati*, *pezzu* for chunk…). Old `.lang` texts
   (String.format) keep the same specifiers in the same order (`%d`, `%.2f`, `%1$s`); when Corsican word order
   needed it, explicit positions were used. The translation memory of other applications was not imported.
4. Old command syntax lines (`/give <player> <item> [amount]`, 173 pairs) are translated by fixed
   rules: argument names inside `<>`/`[]` are translated (*ghjucadore*, *ogettu*, *quantità*), keywords and
   alternatives (`give|take`, `clear`, `everything`, `x y z`) are kept, `OR` becomes `O`. 36 of them contain only
   keywords and stay identical to the English (noted `same as English`).
5. `mchistory.py apply` records rows as `review: "ai"`; it refuses to overwrite an entry reviewed by a speaker.

## Counts

Per class and file format (a pair present in both formats counts as JSON):

| Format | trivial | renamed | absent | changed | ambiguous | empty | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JSON (1.13 to 26.2) | 319 | 82 | 252 | 377 | 4 | 0 | 1,034 |
| `.lang` (1.6.1 to 1.12.2) | 27 | 1,678 | 1,030 | 204 | 2 | 3 | 2,944 |
| total | 346 | 1,760 | 1,282 | 581 | 6 | 3 | 3,978 |

Per family (class):

| Family | trivial | renamed | absent | changed | ambiguous | empty | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blocks | 0 | 367 | 121 | 6 | 0 | 0 | 494 |
| items, potions, effects, enchantments | 6 | 1,094 | 101 | 17 | 2 | 0 | 1,220 |
| entities | 1 | 83 | 9 | 1 | 2 | 0 | 96 |
| biomes, world generation | 0 | 27 | 107 | 7 | 0 | 0 | 141 |
| interface (gui, options, keys, menus, Twitch) | 129 | 22 | 234 | 179 | 2 | 3 | 569 |
| Realms (mco) | 99 | 6 | 53 | 105 | 0 | 0 | 263 |
| statistics, achievements | 1 | 75 | 90 | 3 | 0 | 0 | 169 |
| advancements | 41 | 1 | 1 | 17 | 0 | 0 | 60 |
| commands, arguments, game rules | 59 | 25 | 545 | 173 | 0 | 0 | 802 |
| subtitles, death messages | 10 | 59 | 20 | 73 | 0 | 0 | 162 |
| other (`$o` of 1.7.2, `narrator.select.list.position`) | 0 | 1 | 1 | 0 | 0 | 0 | 2 |

Per family (kind recorded in history.json):

| Family | reused | renamed | adapted | new |
| --- | --- | --- | --- | --- |
| blocks | 1 | 366 | 13 | 114 |
| items, potions, effects, enchantments | 5 | 1,092 | 55 | 68 |
| entities | 1 | 83 | 5 | 7 |
| biomes, world generation | 2 | 27 | 6 | 106 |
| interface (3 empty entries counted as new) | 155 | 22 | 154 | 238 |
| Realms (mco) | 110 | 4 | 94 | 55 |
| statistics, achievements | 1 | 75 | 6 | 87 |
| advancements | 43 | 1 | 16 | 0 |
| commands, arguments, game rules | 140 | 25 | 93 | 544 |
| subtitles, death messages | 49 | 59 | 40 | 14 |
| other | 0 | 1 | 0 | 1 |
| **total (3,978)** | **507** | **1,755** | **482** | **1,234** |

## Per target version

`python3 tools/mchistory.py measure` (full English of each release + history.json + co_fr.json, resolution order
of MULTIVERSION.md). "Reused" counts history entries of kind `reused` or `renamed` (26.3 Corsican, other key or
same meaning); "26.3 as is" counts keys whose English is 26.3's.

| Version | Format | Keys | 26.3 as is | Reused | Adapted | New | Missing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 26.2 | json | 8,123 | 8,067 | 36 | 20 | 0 | 0 |
| 26.1.2 | json | 7,886 | 7,791 | 73 | 22 | 0 | 0 |
| 1.21.11 | json | 7,767 | 7,676 | 71 | 20 | 0 | 0 |
| 1.21.1 | json | 6,881 | 6,580 | 161 | 57 | 83 | 0 |
| 1.20.1 | json | 6,217 | 5,845 | 217 | 72 | 83 | 0 |
| 1.16.5 | json | 5,046 | 4,542 | 269 | 77 | 158 | 0 |
| 1.12.2 | lang | 3,531 | 994 | 1,797 | 142 | 598 | 0 |
| 1.8.9 | lang | 2,761 | 456 | 1,369 | 179 | 757 | 0 |

`python tools/mcversions.py verify all --no-engine`: all 87 releases (1.6.1 to 26.3) report every key
translated (0 left in English) and 0 errors.

## Quality

- **Checker** (`python3 tools/mchistory.py check`, with the English): placeholders by position and conversion
  (`%s`, `%d`, `%.2f`, `%1$s`…), `%%` count, `§` codes, line breaks, leading/trailing spaces as in the English,
  no empty text (except the empty English), kind/from/review rules, JSON without duplicate keys, no untranslated English unless the key is in
  same-as-english.txt or the note says `same as English` (names, codes, keyword-only command syntax). Result:
  **3,978 entries, 0 errors, 5 warnings** (false positives of the leftover-English hint: `/gamemode` in a
  command list, *visità* contains "visit", names inside the old Realms privacy text, a literal `\n` glued to a word). Without the English (CI), it checks against
  `history-placeholders.tsv` (key, hash, signature only).
- **Tests**: `tests/test_minecraft_history.py` (schema, 12-hex hashes, placeholders against the TSV for every
  entry, the TSV holds no English, every pair has an entry, offline checker, signature rules,
  hashing). `python -m unittest discover -s tests -t .`: all pass.
- **Second pass (AI review, not human)**: a random sample of 150 entries (seed 263: 69 renamed, 45 new, 21 reused,
  15 adapted) was re-read against the English: 149 kept, 1 corrected (*Prumove à muderatore*). Outside the
  sample, a search for words the glossary avoids found one more (*multighjucadore* → *Parametri di u ghjocu à
  parechji…*), corrected.

## Ambiguous cases (6, best translation given)

| Key | Corsican | Why |
| --- | --- | --- |
| `entity.PigZombie.name`, `entity.minecraft.zombie_pigman` | *Omu-porcu zombi* | no 26.3 name (became Zombified Piglin, *Piglin zumbificatu*); literal pig-man zombie |
| `item.minecraft.zombie_pigman_spawn_egg` | *Ovu generatore d'omu-porcu zombi* | same name |
| `options.snooper`, `options.snooper.view` | *Permette u Snooper*, *Parametri di u Snooper…* | Mojang's data collection named "Snooper", kept as a name |
| `potion.prefix.grenade` | *Lampabile* | 1.8 and older put it before the potion name (*Lampabile Pozione di cura*); 26.3 says *Pozione da lampà* |

Other judgment calls, with a note in the entry: the 1.8 potion prefixes (*Banale*, *Limpida*…) are feminine
adjectives placed **before** *Pozione* by the game's code; `Redstone` (item, 1.6-1.13) stays *Redstone*;
`options.languageWarning` of 1.6 ("100% accurate", a bare `%` read by String.format as `% a`) keeps the sequence
"100% a" (*100% affidabile*); the 1.9-1.15 trapdoor subtitles whose English swaps "opens"/"closes" are translated
as written.

## Possible errors in the 26.3 base (for the lead; co_fr.json not edited)

- *dighjà* appears 7 times in co_fr.json and *digià* 65 times (e.g. `selectWorld.futureworld.error.text`): one
  spelling should be chosen.
- `datapackFailure.safeMode` "Safe Mode" → *Modu senza fiascu* ("mode without failure"); a safe mode is rather
  *modu sicuru* / *modu prutettu*. Reused as is in the 4 history pairs that contain it.

## What remains

- Human review by a Corsican speaker of all 3,978 entries (none done); priority: the 1,234 `new` and 482
  `adapted` entries, the ambiguous list, old achievements (free titles).
- Seen in the game: no old version has been launched with these texts (packs are built by `mcversions.py`, not
  part of this work); in particular the 1.8 potion names and the old command syntax lines.
- Snapshots and releases before 1.6.1 are out of scope (MULTIVERSION.md).
