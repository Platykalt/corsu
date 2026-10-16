# Minecraft: Java Edition 26.3 in Corsican — status

Updated 2026-10-16. Three different things are counted, and none implies the next:

| Measure | Result | What it proves |
| --- | --- | --- |
| **Key coverage** | 8,557 / 8,557 keys with English text translated (the 2 other keys of `en_us.json` are empty in English), 0 missing, 0 extra | `tools/minecraft.py check`: every key of 26.3 `en_us.json` + `realms/lang/en_us.json` has a non-empty Corsican text |
| **Format** | 8,559 / 8,559 keys rendered by Minecraft 26.3's own code with 0 problems | `tools/minecraft.py verify`: the game's `Language.loadFromJson` reads the file and its `TranslatableContents` formatter renders each key with numbered arguments; every argument English uses comes out, none is lost, no string falls back to its raw template |
| **Linguistic review by a Corsican speaker** | 0 / 8,557 | Not done yet. The texts were written by an AI model in batches (one per category) and then harmonised by another pass of the same kind of model; that is a consistency check, **not** an independent validation. |
| **Seen in the game** | 0 / 8,557 | Not done yet: nobody has loaded the pack in a running game. The pack declares the language exactly as the game's own `pack.mcmeta` does (section `language`, read by `LanguageMetadataSection` in 26.3). |

Open questions for a speaker are in [decisions.md](decisions.md); terms and their status in [glossary.tsv](glossary.tsv)
(most game terms are proposals: no Corsican Minecraft terminology existed to reuse).

## Per category (statuses from inventory.tsv)

| category | keys | missing | to review | translated | reviewed | verified in game | empty in English |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Realms | 426 | 0 | 0 | 426 | 0 | 0 | 0 |
| advancements | 260 | 0 | 0 | 260 | 0 | 0 | 0 |
| armour trims | 29 | 0 | 0 | 29 | 0 | 0 | 0 |
| attributes | 83 | 0 | 0 | 83 | 0 | 0 | 0 |
| biomes | 67 | 0 | 0 | 67 | 0 | 0 | 0 |
| blocks | 1975 | 0 | 0 | 1975 | 0 | 0 | 0 |
| commands | 821 | 0 | 0 | 821 | 0 | 0 | 0 |
| controls | 304 | 0 | 0 | 304 | 0 | 0 | 0 |
| creatures | 219 | 0 | 0 | 219 | 0 | 0 | 0 |
| death messages | 106 | 0 | 0 | 106 | 0 | 0 | 0 |
| debug screen | 63 | 0 | 0 | 63 | 0 | 0 | 0 |
| effects | 51 | 0 | 0 | 50 | 0 | 0 | 1 |
| enchantments | 54 | 0 | 0 | 54 | 0 | 0 | 0 |
| game rules | 117 | 0 | 0 | 117 | 0 | 0 | 0 |
| game tests | 86 | 0 | 0 | 86 | 0 | 0 | 0 |
| interface | 1275 | 0 | 0 | 1274 | 0 | 0 | 1 |
| items | 829 | 0 | 0 | 829 | 0 | 0 | 0 |
| music | 92 | 0 | 0 | 92 | 0 | 0 | 0 |
| narration | 54 | 0 | 0 | 54 | 0 | 0 | 0 |
| options | 360 | 0 | 0 | 360 | 0 | 0 | 0 |
| paintings | 104 | 0 | 0 | 104 | 0 | 0 | 0 |
| statistics | 91 | 0 | 0 | 91 | 0 | 0 | 0 |
| subtitles | 1023 | 0 | 0 | 1023 | 0 | 0 | 0 |
| telemetry | 70 | 0 | 0 | 70 | 0 | 0 | 0 |
| all | 8559 | 0 | 0 | 8557 | 0 | 0 | 2 |

To record a review, change the status column of [inventory.tsv](inventory.tsv) to `reviewed` or `verified in game`
for the keys concerned. `tools/minecraft.py inventory` keeps those statuses while the English text keeps its hash,
and puts a key back to `to review` when Mojang changes its English.

## Not covered by the language file

`texts/splashes.txt` (454 splash lines), `texts/end.txt` (End Poem), `credits.json` and `postcredits.txt` are read
whatever the language; a pack replacing them would change them for every language, so they stay in English. The
Minecraft Launcher, server-sent texts, books and mod or data pack content are outside this pack.

## Next actions

1. A speaker reviews the most visible categories first: interface, options, controls, items, blocks, creatures.
2. Someone who owns Minecraft loads the pack in 26.3 and goes through: title screen, options, language list, creating
   a world, inventory and creative tabs, a death screen, subtitles on, advancements screen.
3. At each Mojang release: `python3 tools/minecraft.py fetch <new>`, `diff 26.3 <new>`, translate the added keys,
   `inventory <new>`, `check <new>`, `verify <new>`, update `VERSION`.
