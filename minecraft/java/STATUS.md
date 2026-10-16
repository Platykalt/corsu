# Minecraft: Java Edition in Corsican — status

Updated 2026-10-17. Four states are kept apart; none implies the next: translation present, AI review, human
review, seen in the game.

## Every release from 1.6.1 to 26.3 (87 releases)

| State | Result |
| --- | --- |
| Translation present | 87 / 87 releases with every key translated: the 26.3 base (8,557 texts) plus `history.json` (3,978 pairs for older English: 507 reused, 1,755 renamed keys, 482 adapted, 1,234 new) |
| Technical check | 87 / 87 (`tools/mcversions.py verify all`, 2026-10-17): Python rules for placeholders, `§` codes, file and mcmeta formats; then each release's own client jar (SHA-1 checked) loads the language file, renders every text with its own formatter (0 problems, 0 unknown keys) and accepts the `language` and `pack` sections (exceptions listed in [MULTIVERSION.md](MULTIVERSION.md)) |
| AI review | every text written and reviewed by AI only; the history pairs got one second AI pass on a 150-entry sample ([history-report.md](history-report.md)) |
| Human review | 0 |
| Seen in the game | 26.3 only, on the maintainer's Prism Launcher instance (2026-10-16): the game's log shows the pack loaded and its own messages in Corsican; the maintainer's visual check is listed in [TESTING.md](TESTING.md). No other release has been started with the pack. |

Snapshots, pre-releases, release candidates and versions before 1.6.1 (no resource packs): not claimed
([other-versions.md](other-versions.md)).

## 26.3 in detail

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

## Per category (from inventory.tsv)

| category | keys | translated | AI review | speaker review | seen in game |
| --- | --- | --- | --- | --- | --- |
| Realms | 426 | 426 | 426 | 0 | 0 |
| advancements | 260 | 260 | 260 | 0 | 0 |
| armour trims | 29 | 29 | 29 | 0 | 0 |
| attributes | 83 | 83 | 83 | 0 | 0 |
| biomes | 67 | 67 | 67 | 0 | 0 |
| blocks | 1975 | 1975 | 1975 | 0 | 0 |
| commands | 821 | 821 | 821 | 0 | 0 |
| controls | 304 | 304 | 304 | 0 | 0 |
| creatures | 219 | 219 | 219 | 0 | 0 |
| death messages | 106 | 106 | 106 | 0 | 0 |
| debug screen | 63 | 63 | 63 | 0 | 0 |
| effects | 51 | 50 | 50 | 0 | 0 |
| enchantments | 54 | 54 | 54 | 0 | 0 |
| game rules | 117 | 117 | 117 | 0 | 0 |
| game tests | 86 | 86 | 86 | 0 | 0 |
| interface | 1275 | 1274 | 1274 | 0 | 0 |
| items | 829 | 829 | 829 | 0 | 0 |
| music | 92 | 92 | 92 | 0 | 0 |
| narration | 54 | 54 | 54 | 0 | 0 |
| options | 360 | 360 | 360 | 0 | 0 |
| paintings | 104 | 104 | 104 | 0 | 0 |
| statistics | 91 | 91 | 91 | 0 | 0 |
| subtitles | 1023 | 1023 | 1023 | 0 | 0 |
| telemetry | 70 | 70 | 70 | 0 | 0 |
| all | 8559 | 8557 | 8557 | 0 | 0 |

[inventory.tsv](inventory.tsv) has four separate columns per key: `translation` (present / missing, written by
`tools/minecraft.py inventory`), `ai_review`, `human_review` (a speaker read it) and `in_game` (someone saw it in the
game). A speaker's review does not check the display, and a display check does not review the language. When Mojang
changes a text's English, the inventory turns its marks into `redo`.

## Outside the language pack

Splash texts and the End Poem: an optional, separate pack (`tools/minecraft.py texts`), because Minecraft reads them
whatever the language. Credits, the launcher, server and mod texts: not covered. See
[docs/en/minecraft.md](../../docs/en/minecraft.md).
