# Minecraft in Corsican

[Français](../fr/minecraft.md)

Corsu adds the language **Corsu (Corsica)** to **Minecraft: Java Edition**, as a resource pack made for each version.
The pack does not touch the game's files: it is switched on and off from the Resource Packs menu.

<!-- corsu:minecraft-summary:start -->
**Minecraft: Java Edition in Corsican for 87 versions** (releases 1.6.1 → 26.3). Complete translation of the language files for the listed versions; technical checks with each version's own code.

| | |
| --- | --- |
| Versions | the 87 Java Edition releases from 1.6.1 to 26.3 ([list and result per version](../../minecraft/java/COMPATIBILITY.md)). |
| Translation | every non-empty text of each listed version's language files has its Corsican text: from 1,353 texts (1.6.1) to 8,557 (26.3). One translation: 26.3's (8,557 texts) serves wherever the key and its English are the same; 3,978 differing older texts have their own entry (507 reused, 1,755 renamed keys, 482 adapted, 1,234 new). |
| Technical checks | on 2026-10-17, for each version: Python rules on every text (arguments, `§` codes, language file and pack.mcmeta formats), then that version's own game code (its client jar, SHA-1 checked) loaded the language file and rendered every text: 0 problems (2 or 3 texts per version not rendered because their English itself does not format). Exceptions: text components (chat, advancements) before 26.1: Python rule only; the `pack` section of pack.mcmeta in 1.21.1: not read by the game's code; the code in the `language` section from 1.20: checked in Python; drawing on screen and the resource pack screen are not checked ([details](../../minecraft/java/MULTIVERSION.md), [per version](../../minecraft/java/COMPATIBILITY.md)). This is neither a speaker's review nor a visual check of every screen. |
| Review | texts written by AI; second AI pass on a sample of 150 entries of the 3,978 older texts (not on all of them); review by a Corsican speaker: 0. |
| In the game | only 26.3 has been started with the pack, on the maintainer's Prism Launcher instance (2026-10-16): the game's log shows the pack loaded and messages in Corsican. No per-key visual check has been recorded, which is why [STATUS.md](../../minecraft/java/STATUS.md) counts "seen in game: 0". The other versions have not been started. |
| Availability | on the main branch (development) today; in a published Corsu release only once a release containing these packs is published (the last published one, 0.22.0, has only the 26.3 pack). |
| Out of scope | the game's language files only: not mods, servers or the launcher; splash texts and the End Poem: a separate optional pack. No snapshots, pre-releases or release candidates, no Bedrock, nothing before 1.6.1 (no resource packs). |

**Getting and switching on the right pack**

1. Close Minecraft.
2. In the Corsu app (a release that contains these packs), tick **Minecraft** and install. Corsu reads the version each game folder plays (official launcher, Prism Launcher, MultiMC, also under Fabric, Forge, Quilt or NeoForge), copies that version's pack there and picks Corsican.
3. Start the game: **Options… → Language…** shows **Corsu (Corsica)**, already chosen.

Developers, from a copy of main: `python3 tools/mcversions.py build <version>` writes `dist/corsu-minecraft-java-<version>.zip`; drop it in that version's `resourcepacks` folder, switch it on in **Resource Packs…**, then pick **Corsu (Corsica)** in **Language…**.
<!-- corsu:minecraft-summary:end -->

| | |
| --- | --- |
| Sources | [co_fr.json](../../minecraft/java/co_fr.json) (the 26.3 translation, the base), [history.json](../../minecraft/java/history.json) (texts of older versions), [glossary](../../minecraft/java/glossary.tsv), [conventions](../../minecraft/java/STYLE.md) |
| Status | [STATUS.md](../../minecraft/java/STATUS.md): translation, AI review, human review and in-game testing are counted separately. |

NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.

## Install with the Corsu app (automatic)

When Minecraft is installed, the Corsu app offers **Minecraft**. Close Minecraft, tick it and install: Corsu looks for
game folders (the official launcher's, and Prism Launcher and MultiMC instances) and the version each one plays: the
instance's version, or the official launcher's last used profile, also under Fabric, Forge, Quilt or NeoForge. In each
folder playing a listed version, it copies that version's pack as `corsu-minecraft-java.zip`, adds it after your other
packs and sets the Corsican language in `options.txt` (`co_fr`, or `co_FR` up to 1.10.2). It leaves alone, saying
why, folders of a version that is not listed or unknown, folders where Minecraft is running, an `options.txt` it
cannot read back safely, and another file that already has the pack's name. On the next start Minecraft is in
Corsican. The app's switch puts back the previous language and packs without touching the game's other settings;
uninstalling Corsu also removes the pack. Command line: `python3 src/installer.py --components minecraft`.

## Install by hand

1. Take the pack of **your** version: `corsu-minecraft-java-26.3.zip` is in the
   [releases](https://github.com/Platykalt/corsu/releases/latest) (26.3 only); for another listed version, build it
   from a copy of this repository: `python3 tools/mcversions.py build <version>`, which writes
   `dist/corsu-minecraft-java-<version>.zip`. Leave it zipped.
2. In Minecraft, open **Options… → Resource Packs… → Open Pack Folder** and drop the file there.
3. Back in the game, the pack shows on the left. Click its arrow to move it to the right, then **Done**.
4. Open **Options… → Language…**, choose **Corsu (Corsica)**, then **Done**.

The pack folder is also here: `%APPDATA%\.minecraft\resourcepacks` on Windows,
`~/Library/Application Support/minecraft/resourcepacks` on macOS, `~/.minecraft/resourcepacks` on Linux (or the
instance folder in Prism Launcher, MultiMC…).

## Update

With the Corsu app: run the installation again with Minecraft closed; if an instance changed version, Corsu puts the
new version's pack there. By hand: replace the old `corsu-minecraft-java-….zip` in the pack folder with the new one,
and enable it again in **Resource Packs** if its name changed. The chosen language stays Corsu.

## Uninstall

1. **Options… → Language…**: choose another language first.
2. **Resource Packs…**: remove the Corsu pack (arrow to the left), then delete the file from the folder.

If the pack is removed while Corsu is still the chosen language, Minecraft falls back to English.

## What is translated, and what is not

Everything each listed version takes from its language files: menus, settings, commands, blocks, items, creatures,
biomes, effects, enchantments, advancements (or achievements in old versions), statistics, subtitles, death messages,
Realms, the narrator. A missing string would show in English.

Three different cases:

- **Cannot depend on the language**: the yellow splash texts on the title screen (`texts/splashes.txt`), the End Poem
  (`texts/end.txt`), the credits (`credits.json`, `postcredits.txt`). A resource pack *can* replace them, but Minecraft
  has a single version of each, read whatever the language: replacing them changes them for every language. Corsu
  therefore translates them in a **separate optional pack** (see below), never in the language pack.
- **A separate component, not covered**: the Minecraft Launcher (Microsoft), translated by Mojang on Crowdin, where
  Corsican is a target language but not shipped. It is not part of the game and Corsu does not change it.
- **Outside the base game**: text sent by a server, written in a world or a book, or added by mods and data packs.

## Optional pack: splash texts and End Poem (26.3)

`corsu-minecraft-java-texts-26.3.zip` (built by `python3 tools/minecraft.py texts`) replaces 26.3's 454 splash texts
and the End Poem with their Corsican translation. **It changes them for every language**, since Minecraft reads only
one version: turn it on only if that suits you, and remove it to get English back. Corsu never installs it by itself.
The End Poem translates Julian Gough's text, which he placed under CC0; the splash texts translate Mojang's text.
Choices and doubts: [minecraft/java/texts/NOTES.md](../../minecraft/java/texts/NOTES.md).

## Other versions

Snapshots, pre-releases and release candidates, and versions before 1.6.1 (no resource packs), have no pack: the app
leaves those folders alone ([list](../../minecraft/java/other-versions.md)). One version's pack loaded in another may
show as "incompatible"; texts Mojang changed between the two stay in English or are ignored. Always take your own
version's pack.

## Bedrock Edition

Bedrock also accepts a language added by a global pack (`texts/languages.json`, `texts/language_names.json`,
`texts/co_FR.lang`) on Windows, Android and iOS. It is not done yet: Bedrock has its own keys (about 13,000 lines)
and does not reuse the Java files. Consoles generally cannot import packs, and disabling the pack while its language is
selected crashes the game.

## Test in the game

You own Minecraft? Steps and screens to check: [minecraft/java/TESTING.md](../../minecraft/java/TESTING.md).

## Correct a translation

The 26.3 texts are in `minecraft/java/co_fr.json` (one key, one text); those of older versions, where their English
differs, in `minecraft/java/history.json`. A correction to a shared text applies to every version showing that same
English. Follow [STYLE.md](../../minecraft/java/STYLE.md) and the [glossary](../../minecraft/java/glossary.tsv), then
run `python3 tools/minecraft.py check` and `python3 tools/mchistory.py check`: they check that no key is missing and
that every `%s`, `%1$s`, `§` code and line break is kept. Or
[open an issue](https://github.com/Platykalt/corsu/issues/new?template=translation.yml) with the version, the key or the
text you saw.
