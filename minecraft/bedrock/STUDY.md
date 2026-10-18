# Minecraft: Bedrock Edition in Corsican — technical study

Written 2026-10-16, sources re-checked 2026-10-19. Nothing here has been tried in a running game: there is no Bedrock install and no account on
this machine. "Verified" below means "read in a primary source" or "checked offline on the files", never "seen in game".

## 1. Version pinned

| | |
| --- | --- |
| Stable game version | Bedrock **26.50** ("Wilderness Bound"), engine version `1.26.50` |
| Pinned source | [`Mojang/bedrock-samples` tag `v1.26.50.4`](https://github.com/Mojang/bedrock-samples/releases/tag/v1.26.50.4), published 2026-09-16, marked as a release (not a preview); its `version.json` lists `1.26.50.4` dated 15-09-2026 as `latest` |
| Next in preview | `v1.26.60.29-preview` (2026-10-02), [releases list](https://github.com/Mojang/bedrock-samples/releases) |
| Hotfixes since | 26.51 and 26.52 (1.26.52.3, 2026-09-25), reported by third-party sites citing Mojang's changelog; no bedrock-samples tag for them (checked 2026-10-19 with the GitHub API), so the 26.50 texts stay the reference |
| Release notes | linked from the tag: [Minecraft Bedrock Edition 26.50 Changelog](https://feedback.minecraft.net/hc/en-us/articles/48826825649933-Minecraft-Bedrock-Edition-26-50-Changelog-Wilderness-Bound) (the page refused automated access; not read) |

The vanilla `resource_pack/manifest.json` of that tag uses `"min_engine_version": [1, 26, 50]`.

## 2. Source texts: bedrock-samples and its licence

- `resource_pack/texts/` at `v1.26.50.4` holds `en_US.lang` (816,616 bytes), 28 other `xx_XX.lang`, `languages.json`
  and `language_names.json` (29 languages, no Corsican).
- Licence: [`LICENSE.md`](https://github.com/Mojang/bedrock-samples/blob/main/LICENSE.md) reads in full
  "(c) Mojang AB. All rights reserved. By downloading the files in this repository, you agree to the
  [Minecraft End User License Agreement](https://www.minecraft.net/en-us/eula) and that these files are subject to its
  terms." GitHub reports it as `NOASSERTION` (no open licence).
- Consequence: downloading `en_US.lang` for local checks is allowed under the EULA (the repository exists for
  creators, [README](https://github.com/Mojang/bedrock-samples)); redistributing it is not. Corsu therefore treats it
  like the Java `en_us.json`: `tools/bedrock.py fetch` puts it in `~/.cache/corsu/bedrock/<tag>/`, with a
  `fetched.json` recording URL and SHA-256; it is never committed and never put in the pack.

## 3. The .lang format

Observed in `en_US.lang` at the pinned tag and described by [wiki.bedrock.dev, Intro to Text & Localization](https://wiki.bedrock.dev/text/text-intro):

- UTF-8, one `key=value` per line, split at the first `=`. `en_US.lang` has LF endings and no BOM; `fr_FR.lang` starts
  with a BOM, so the game accepts one. 13,340 lines, 13,340 keys, no duplicates, no comments at this tag.
- Microsoft Learn, [Preparing Raw Text for Localization](https://learn.microsoft.com/minecraft/creator/documents/preparingrawtextforlocalization)
  (written for files Microsoft localises): "`<tab>#` is the required terminator for our parser to recognize the
  string"; the value "ends with a tab character followed by a hashtag character"; the file "must be saved in UTF-8
  encoding. Processing will fail if the file is encoded in ANSI, UTF-8 BOM, UCS-2…". Mojang's own `fr_FR.lang` has a
  BOM, so the BOM rule is the localisation pipeline's, not necessarily the game's. Corsu's repository lines end with
  `<tab>## from-java:<key>`, which satisfies both this and the wiki; the copy in the `.mcpack` has no comments at all.
- In `en_US.lang` a lone `#` inside a value is text (`playscreen.realmsPreProdNotAuthorized` contains ` #ask-Realms…`).
- Comments: `##` at the start of a line, or inline after the value. The wiki warns that spaces before an inline `##`
  are kept in the text and says to use a tab; Microsoft's localisation requirements quoted there ask for
  `<tab>#` before comments, CR+LF, no duplicate keys. (CR+LF is for files Microsoft localises; Mojang's own
  `en_US.lang` uses LF.)
- Line breaks inside a value: `~LINEBREAK~` (5 values) or `\n` (none in `en_US.lang`).
- Placeholders: `%s` (798), `%1$s`, `%2$s`… , `%d`, `%1$d`… , `%.2f`, bare numbered `%1`, `%2` (29 values), and `%%`.
- Formatting codes `§x`: 104 values. Values may also contain input glyph tokens such as `:_input_key.inventory:`.
- Some values end with spaces (e.g. `commands.inputpermission.mount=Mount `): kept as they are.

## 4. Adding a language

From [wiki.bedrock.dev](https://wiki.bedrock.dev/text/text-intro), section "Custom Languages":

- "With a global resource pack, custom languages may be introduced through the `languages.json` and
  `language_names.json` files. Once the pack is applied globally the language can be changed in the Language tab."
- `texts/languages.json` lists **only the pack's own languages**: the wiki's example is `["xx_XX", "yy_YY"]`, and for
  ordinary packs "an array with each of the languages you plan to change". Vanilla languages are not repeated.
- `texts/language_names.json`: `[["xx_XX", "New Language (Custom Language #1)"]]`.
- The language file is `texts/xx_XX.lang`.
- Warning quoted from the wiki (community documentation, [source](https://github.com/Bedrock-OSS/bedrock-wiki/blob/main/docs/text/text-intro.md),
  file last changed 2026-09-27): "make sure to switch away from the language before you disable the resource pack that
  it is a part of, otherwise Minecraft will crash." **Crash risk is documented by the community only**: no
  Mojang bug report or Microsoft page found (search 2026-10-19). Uninstall instructions must say to switch the language
  back first; whether the crash still happens in 26.50 is an in-game question.

Pack header, from Microsoft Learn [manifest.json reference](https://learn.microsoft.com/minecraft/creator/reference/content/addonsreference/packmanifest):
`format_version` 2 for resource packs (3 is in preview); `header` with `name`, `description`, `uuid`, `version`
`[a, b, c]`, `min_engine_version` (required for resource packs); one module of type `"resources"` with its own
distinct `uuid`. A re-imported pack replaces the old one only if `version` is higher. `pack_scope` may be `"world"`,
`"global"` or `"any"`; Corsu's manifest sets `"global"` because a language only works from a global pack.

Corsu's choice: code **`co_FR`**, name **"Corsu (Corsica)"**, following the vanilla
`ll_CC` pattern (`co` = ISO 639-1 Corsican, `FR` = France); no vanilla language uses it. Unknown, needs a test: whether the game uses the code for font or
locale choices (number formats, etc.) and how it behaves with an unknown locale.

**Fallback: not documented.** No Mojang or game-behaviour source read says what the game shows for a key missing from
a custom language (English, or the raw key). The only related sentence is in Microsoft's Creator Tools validator
reference ([Language Files rules](https://learn.microsoft.com/minecraft/creator/reference/content/mctoolsvalreference/langfiles),
marked "ai-assisted"): "English is required as the default fallback language for all packs" — a rule of a validation
tool for pack texts, not a statement about a whole custom language. Every vanilla language at the pinned tag has all
13,340 keys, so Mojang's files show no partial language either. The prototype assumes English. If the game shows raw keys, 9,052 keys would show as keys;
filling them with English would mean shipping Mojang's text, which Corsu avoids. This is the first thing to test.

## 5. Platforms and installation

From Microsoft Learn [Getting started with add-ons](https://learn.microsoft.com/minecraft/creator/documents/gettingstarted):

| Platform | How a `.mcpack` arrives | Global resource packs |
| --- | --- | --- |
| Windows 10/11 | open (double-click) the `.mcpack`; a `.zip` may be renamed to `.mcpack` | Settings > Global Resources (per [minecraft.wiki Resource pack](https://minecraft.wiki/w/Resource_pack)) |
| Android | open the file from a file manager / download | same |
| iOS / iPadOS | tap the file, "Open in Minecraft" | same |
| Consoles (Xbox, PlayStation, Switch) | no sideloading; the documented route is a world with add-ons uploaded to a Realm | a world pack cannot add a language (wiki: global packs only) — **not feasible** outside the Marketplace |

Importing copies the pack to `com.mojang/resource_packs` ([minecraft.wiki](https://minecraft.wiki/w/Resource_pack)).
On Windows the game moved from UWP to GDK at 1.21.120: `com.mojang` is now
`%appdata%\Minecraft Bedrock\users\shared\games\com.mojang` (Preview: `Minecraft Bedrock Preview`); the old UWP path was
`%localappdata%\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang`
([Microsoft Learn, GDK migration](https://learn.microsoft.com/minecraft/creator/documents/gdkpcprojectfolder)).
Packs can also be placed by hand in `development_resource_packs`.

`minecraftpe/global_resource_packs.json` (a list of `{"pack_id", "version"}` activating global packs) is known from
community practice only; no primary source was found by searching. An installer must not edit it until a test confirms
its location and format on each platform; the in-game Global Resources screen is the supported way.

## 6. Distribution constraints

- [Minecraft EULA](https://www.minecraft.net/en-us/eula) and [Usage Guidelines](https://www.minecraft.net/en-us/usage-guidelines):
  free distribution of fan-made packs, no Mojang files, notice "NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR
  ASSOCIATED WITH MOJANG OR MICROSOFT." The open question about translations as derivatives is the same as for Java
  (`minecraft/java/LICENSING.md`).
- Marketplace: selling or listing requires being an approved partner ([Partner Program](https://www.minecraft.net/en-us/partner));
  not an option for Corsu. Consoles therefore stay out of reach.
- Official route for a real Corsican Bedrock: Mojang's translation project; out of scope here.

## 7. Counting method

`python3 tools/bedrock.py stats` (results in `STATUS.md`):

1. Denominator: keys of `en_US.lang` at the pinned tag (13,340; 3 have an empty value).
2. Category: first part of the key (`item`, `tile`, `options`, …).
3. Java reuse candidate: the Bedrock English value is **byte-identical** to a value of Java 26.3 `en_us.json`
   (+ `realms/lang/en_us.json`).
4. Reused: candidate **and** the Java key's family corresponds to the Bedrock key's family (table `FAMILIES` in
   `tools/bedrock.py`: `tile`→`block`/`item`, `item`→`item`/`block`/`color`/`jukebox_song`/…, `entity`→`entity`,
   `subtitles`→`subtitles`, `death`→`death`, `achievement`→`advancements`, `options`→`options`, …) **and** all
   matching Java keys have the same Corsican text **and** the Corsican text passes the Bedrock checks (same
   placeholders, `§` codes, line breaks). Everything else is left out; nothing is machine-translated.
5. Two more refusals (added 2026-10-19 after reading every reused interface line): in interface families (`options`,
   `gui`, `key`, `keyboard`, `menu`, `chat`, `commands`, `selectWorld`, `createWorld`, `createWorldScreen`), a one-word
   text is refused when the Java key does not contain the last part of the Bedrock key (gender and sense depend on the
   screen: `options.ao.max` "Massima" is not reused for `options.guiScale.maximum`); a key ending in `.lineN` is reused
   only if every non-empty line of the same sentence is.
6. Provenance: when several Java keys qualify, the one with the same last part is named.
