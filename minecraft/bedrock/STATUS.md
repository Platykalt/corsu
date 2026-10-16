# Minecraft: Bedrock Edition in Corsican — status (PROTOTYPE)

Updated 2026-10-16. **The pack has never been loaded in the game.** Nothing below says it works in Minecraft.

## 1. Coverage

Source: `resource_pack/texts/en_US.lang` of [bedrock-samples `v1.26.50.4`](https://github.com/Mojang/bedrock-samples/releases/tag/v1.26.50.4)
(game 26.50), SHA-256 `0af440d960125ca795b0bb03623b9a6aa07c83570413cc5efd70a7491581de9c`. Method in `STUDY.md` §7;
numbers from `python3 tools/bedrock.py stats`.

| Measure | Count |
| --- | ---: |
| Keys in `en_US.lang` | 13,340 (3 empty) |
| English text identical to some Java 26.3 English text | 5,002 |
| … but only in a non-corresponding Java family (left out) | 697 |
| … matching family, but the Java translations disagree (left out) | 17 |
| **Reused in `co_FR.lang`** (each marked `## from-java:<key>`) | **4,288 / 13,340 (32.1 %)** |
| Left out (expected to show the fallback, see risks) | 9,052 |

By family (reused / keys): `item` 1,358/1,481 · `tile` 1,208/1,403 · `subtitles` 990/1,006 · `entity` 138/153 ·
`potion` 96/114 · `options` 85/1,199 · `enchantment` 52/52 · `death` 50/62 · `stat` 41/68 · `selectWorld` 30/77 ·
`key` 29/104 · `container` 29/43 · `tipped_arrow` 26/27 · `keyboard` 24/146 · `achievement` 14/76 · other families
118. Not covered at all: `howtoplay` (778), `store` (544), `commands` (919 of 927), Realms, menus, Education Edition
screens and most Bedrock-only UI: these need new translation work, not reuse.

The reused texts are Corsu's Java texts: 0 of them has been reviewed by a Corsican speaker (see `minecraft/java/STATUS.md`).

## 2. Verified offline

- `python3 tools/bedrock.py check`: 0 errors. For each line: key exists in `en_US.lang`, no duplicate, same
  placeholder multiset as English (`%s`, `%1$s`, `%d`, `%1`, `%.2f`, `%%`), same `§` codes, same number of
  `~LINEBREAK~`/`\n`, no `##` inside a value, a tab (not spaces) before inline comments, UTF-8 without BOM, LF only,
  final newline. Manifest: `format_version` 2, one `resources` module, distinct v4 UUIDs, `[a, b, c]` versions.
- `dist/corsu-minecraft-bedrock-v1.26.50.4.mcpack`: a zip of `manifest.json`, `pack_icon.png` (128×128, generated),
  `texts/languages.json` (`["co_FR"]`), `texts/language_names.json` (`[["co_FR", "Corsu (Corsica)"]]`),
  `texts/co_FR.lang`, `LICENSE.txt`. Fixed dates and order: two builds give the same bytes
  (SHA-256 `f413a644a0a13e3eac2904252a1ce3dfd2855d5f39f7d020d976749eba0f14e2`). No Mojang file inside.
- Unit tests `tests/test_bedrock.py` (offline, fake data): seed reuse rules and provenance, check errors, pack contents.

## 3. Not verified

- That the game imports the `.mcpack`, lists it under Global Resources, and shows "Corsu (Corsica)" in Language.
- What a missing key shows (English or the raw key) — not documented anywhere found.
- Whether the tab before `## from-java:` is trimmed by the game (if not, 4,288 texts end with an invisible tab).
- Whether `pack_scope: "global"` and `min_engine_version [1, 26, 50]` are accepted as intended.
- Fonts: Corsican needs only Latin letters with `à è ì ò ù`, which vanilla languages already use; untested.
- Text fitting in buttons; behaviour of the unknown locale `co_FR` (number formats, sorting).
- The documented crash when the pack is disabled while Corsican is selected (wiki.bedrock.dev) is a known risk, not a test result.

## 4. Next step: manual test (Windows or Android, current stable 26.50)

1. Copy `dist/corsu-minecraft-bedrock-v1.26.50.4.mcpack` to the device and open it; expect "Successfully imported".
2. Settings > Global Resources: activate "Corsu (lingua corsa)".
3. Settings > Language: pick "Corsu (Corsica)". Check the title screen, inventory (blocks, items: Corsican),
   a creature name, subtitles on, and a Bedrock-only screen (e.g. How to Play: should be English, not raw keys).
4. Note any text with a visible trailing gap or raw `key.name`.
5. Before removing: switch Language back to English, **then** deactivate and delete the pack (crash risk otherwise).
6. Write the results here with game version and platform; only then change wording from "prototype".
