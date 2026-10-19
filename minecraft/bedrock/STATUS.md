# Minecraft: Bedrock Edition in Corsican — status (PROTOTYPE, EXPERIMENTAL)

Updated 2026-10-19. **The pack has never been loaded in the game.** Nothing below says it works in Minecraft. Bedrock
is not a supported part of Corsu: it stays separate from the installers and the Java pack.

French guide and test protocol: [docs/fr/minecraft-bedrock.md](../../docs/fr/minecraft-bedrock.md). Sources and format
details: [STUDY.md](STUDY.md).

## 1. Target

Bedrock **26.50** ("Wilderness Bound"), checked on 2026-10-19: [`Mojang/bedrock-samples`](https://github.com/Mojang/bedrock-samples/releases)
has `v1.26.50.4` (2026-09-16) as its latest non-preview release; later tags are `v1.26.60.*-preview`. The game has
since had hotfixes 26.51 and 26.52 (reported by third-party sites; Mojang's changelog pages refuse automated access and
were not read) with no new bedrock-samples tag, so the texts are taken as those of 26.50.

## 2. Coverage

Source: `resource_pack/texts/en_US.lang` at `v1.26.50.4`, SHA-256
`0af440d960125ca795b0bb03623b9a6aa07c83570413cc5efd70a7491581de9c` (re-read 2026-10-19: 13,340 keys, 3 empty,
no duplicate, LF, no BOM; `fr_FR.lang` and `it_IT.lang` have the same 13,340 keys). Numbers from
`python3 tools/bedrock.py stats`, Java side = `minecraft/java/co_fr.json` (Java 26.3) as of this branch.

| Measure | Count |
| --- | ---: |
| Keys in `en_US.lang` | 13,340 |
| English text identical to some Java 26.3 English text | 5,002 |
| … only in a non-corresponding Java family (refused) | 697 |
| … matching family, but the Java translations disagree (refused) | 17 |
| … one-word interface label taken from a differently named Java key (refused) | 13 |
| … one line of a split sentence whose other lines are not reused (refused) | 3 |
| … Corsican text fails the Bedrock checks (refused) | 0 |
| **Reused in `co_FR.lang`** (each marked `## from-java:<key>`) | **4,272 / 13,340 (32.0 %)** |
| Left out (shows the game's fallback, unknown: see §4) | 9,068 |

By family (reused / keys): `item` 1,358/1,481 · `tile` 1,208/1,403 · `subtitles` 992/1,006 · `entity` 138/153 ·
`potion` 96/114 · `options` 76/1,199 · `enchantment` 52/52 · `death` 50/62 · `stat` 41/68 · `container` 29/43 ·
`key` 28/104 · `selectWorld` 27/77 · `tipped_arrow` 26/27 · `keyboard` 24/146 · `achievement` 14/76 · `gui` 12/96 ·
other families 101. Not covered at all: `howtoplay` (778), `store` (544), `commands` (919 of 927), Realms, the title
screen buttons (`menu.play`, `menu.settings`…), Education Edition screens and most Bedrock-only UI.

Refused one-word labels (2026-10-19): `createWorldScreen.cheatSettings`, `createWorldScreen.experimentalgameplay`,
`gui.confirm`, `key.cancelToast` (Java's is the name of the Cancel key, Bedrock's an action), `options.dev_chunk_map_mode_full`,
`options.dev_chunk_map_mode_limited`, `options.dev_connection_quality.no_limit`, `options.dev_serviceOverrideTypeCustom`,
`options.hudOpacity.max`, `options.renderingProfile`, `options.guiScale.maximum`, `options.guiScale.minimum` (Java's
"Massima/Minima" agree with *illuminazione*), `options.graphicsQualityPresetMode.name`. Refused split lines:
`selectWorld.gameMode.{adventure,hardcore,survival}.line2` (their `line1` differs from Java's, so the sentence would be
half English).

The reused texts are Corsu's Java texts: none of them has been reviewed by a Corsican speaker (see
`minecraft/java/STATUS.md`). A test fails when `minecraft/java/co_fr.json` changes a reused text: then run
`python3 tools/bedrock.py seed`.

## 3. Verified offline (2026-10-19, Linux)

- `python3 tools/bedrock.py check`: 0 errors. Per line: key exists in `en_US.lang`, no duplicate, same placeholder
  multiset as English (`%s`, `%1$s`, `%d`, `%1`, `%.2f`, `%%`), same `§` codes, same number of `~LINEBREAK~`/`\n`, no
  `##` inside a value, a tab before inline comments, UTF-8 without BOM, LF only, final newline. Manifest:
  `format_version` 2, `pack_scope` `"global"`, one `resources` module, distinct v4 UUIDs, `[a, b, c]` versions.
  Language code `co_FR` is not a vanilla code and follows the `ll_CC` pattern.
- `python3 tools/bedrock.py build` → `dist/corsu-minecraft-bedrock-v1.26.50.4.mcpack` (pack version 0.2.0): a zip of
  `manifest.json`, `pack_icon.png` (128×128 PNG, generated), `texts/languages.json` (`["co_FR"]`),
  `texts/language_names.json` (`[["co_FR", "Corsu (Corsica)"]]`), `texts/co_FR.lang`, `LICENSE.txt`. The `.lang`
  inside the pack has **no comments** (only `key=value` lines): the provenance stays in the repository copy.
  Reproducible on any machine: fixed member order, dates (2026-01-01), permissions (0644), creating system (Unix),
  and no compression (members STORED, icon image data in stored deflate blocks), so the bytes do not depend on the
  zlib, umask, operating system or Python version. Before this (until 85c6241) the members were deflated: CI run
  39192791783 (GitHub's Ubuntu runner) gave `a8de8a5c…9a7e` and a zlib-ng 1.3.1 machine `7a6c3838…e23a` from the
  same commit, with the same member bytes, order and metadata and only the compressed streams differing. SHA-256
  now: `91907de47ba4e26387b7e4dbda8cc8f0152d11cc6b262a2e661676f0194e7579` (260,395 bytes, 2026-10-19), identical with
  zlib-ng 1.3.1/Python 3.14 (CachyOS), zlib 1.3/Python 3.12 (Ubuntu 24.04) and zlib 1.3.1/Python 3.13 (Debian 13);
  the old deflated build gave the CI value under both stock zlib containers. Stored members are plain ZIP, but that
  the game imports them is, like everything else here, not yet seen in a game (step 1 below). No Mojang file inside.
- Unit tests `tests/test_bedrock.py` (offline, no Mojang file): reuse rules and refusals, provenance, format of the
  committed file, check errors, pack contents, comment stripping, fixed archive metadata, the same bytes with another
  umask, platform or deflate output.

No Bedrock client was run: there is none for Linux, and the official Bedrock Dedicated Server has no user interface,
so it cannot show a language. Nothing here was tested on Windows, Android or iOS.

## 4. Needs an in-game test (open questions)

1. Import: does the game accept the `.mcpack` ("Successfully imported") and list it under Global Resources?
2. Does "Corsu (Corsica)" appear in Settings > Language once the pack is active globally, and do all vanilla languages
   stay listed (our `languages.json` names only `co_FR`, as in the wiki example)?
3. **Missing keys** (9,068): English, or the raw key (`menu.play`)? Not documented by Mojang or Microsoft. Only hint: the
   Creator Tools validator documentation (marked "ai-assisted") calls `en_US` "the default fallback language for all
   packs", which is about pack texts and not proof for a whole language.
4. Is a language without `en_US.lang` in the pack accepted? (The same validator wants `en_US` in every pack's
   `languages.json`; the wiki's custom-language example does not.)
5. Does `min_engine_version [1, 26, 50]` with `pack_scope "global"` import and activate on 26.50–26.52?
6. Fonts and characters: à è ì ò ù, apostrophes (Latin letters vanilla languages already use).
7. Text length in buttons; unknown locale `co_FR` and number formats.
8. **Removal while Corsican is selected**: wiki.bedrock.dev (community, not Mojang) says Minecraft *crashes* if the pack is
   disabled before switching language. Not observed; no Mojang bug report found. The protocol always switches back to
   English first; testing the crash itself is optional and only on a device where a crash costs nothing.
9. After removal, does the game come back in the previous language, and are worlds and other packs unaffected?

## 5. Next step

Follow the protocol in [docs/fr/minecraft-bedrock.md](../../docs/fr/minecraft-bedrock.md) on Windows or Android
(26.50 or later hotfix) and write the results here with game version, platform and date. Only then change the wording
from "prototype".
