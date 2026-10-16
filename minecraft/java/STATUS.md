# Minecraft: Java Edition 26.3 in Corsican — status

Updated 2026-10-16. Three measures are kept apart; none implies the next.

## 1. Completeness

| Scope | Result |
| --- | --- |
| Version | `26.3`, release id of Mojang's [version manifest](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json); client jar SHA-1 `e877b6a07acd633fb3bb475002175cec036e7b87` |
| Source keys | 8,559 keys of `assets/minecraft/lang/en_us.json` inside that client jar (the asset `realms/lang/en_us.json` has 5 keys, all already among them) |
| Corsican texts | 8,557 / 8,557 keys with English text (2 keys are empty in English), 0 missing, 0 extra |

## 2. Technical validity, as tested

`python3 tools/minecraft.py check` (Python, no game code): every key present, no empty text, the same arguments as
English by Minecraft's rule `%(?:(\d+)\$)?([A-Za-z%]|$)`, same `§` codes and line breaks. Result: 0 errors.

`python3 tools/minecraft.py verify` runs classes from the official 26.3 client jar in a plain Java program
(`tools/minecraft/LangCheck.java`). Result: 0 problems. It shows that:

- `Language.loadFromJson`, the game's own reader, accepts `co_fr.json` and the file inside the built zip;
- `LanguageMetadataSection.CODEC` accepts the pack's `language` section (`co_fr`: Corsu, Corsica) and the pack's
  format range `[97.0, 97.*]` accepts the game's format 97.1;
- every key, rendered by the game's formatter (`Component.translatable(...).getString()`) with numbered arguments,
  shows every argument English shows and never falls back to its raw template.

It does **not** open a game window, load the pack through the resource pack screen, draw text with the game's font,
or show whether a text fits its button. That is the in-game test below.

The zip (`dist/corsu-minecraft-java-26.3.zip`): 4 files (`pack.mcmeta`, `pack.png`,
`assets/minecraft/lang/co_fr.json`, `LICENSE.txt`), UTF-8 without BOM, fixed dates; building twice gives the same
bytes, and the Corsu installer builds the same bytes from the committed files (unit tests). No official 26.3 language
uses the code `co_fr`.

## 3. Language review and in-game test

| | Done |
| --- | --- |
| Review by a Corsican speaker | **0 / 8,557** |
| Seen in a running game | **0 / 8,557** |

The texts were written by an AI model, harmonised by a second AI pass, then reviewed by a third AI pass that changed
242 texts with evidence from the reviewed Corsican translations ([changes-review.tsv](changes-review.tsv),
[review.md](review.md)). These passes find mistakes; they are not a validation. Open questions for a speaker:
[decisions.md](decisions.md). Test procedure: [TESTING.md](TESTING.md).

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

To record a review, set the status column of [inventory.tsv](inventory.tsv) to `reviewed` or `verified in game`.
`tools/minecraft.py inventory` keeps those statuses while the English text keeps its hash, and puts a key back to
`to review` when Mojang changes its English.

## Outside the language pack

Splash texts and the End Poem: an optional, separate pack (`tools/minecraft.py texts`), because Minecraft reads them
whatever the language. Credits, the launcher, server and mod texts: not covered. See
[docs/en/minecraft.md](../../docs/en/minecraft.md).
