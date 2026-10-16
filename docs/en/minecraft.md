# Minecraft in Corsican

[Français](../fr/minecraft.md)

Corsu adds the language **Corsu (Corsica)** to **Minecraft: Java Edition 26.3**, as a resource pack. The pack does not
touch the game's files: it is switched on and off from the Resource Packs menu.

| | |
| --- | --- |
| Edition | Java Edition only (Windows, macOS, Linux). Bedrock is not supported, see below. |
| Version | 26.3 (resource pack format 97). Other versions show an "incompatible" warning; see "Other versions". |
| File | `corsu-minecraft-java-26.3.zip`, in the [releases](https://github.com/Platykalt/corsu/releases/latest), or built with `python3 tools/minecraft.py build` |
| Sources | [minecraft/java/co_fr.json](../../minecraft/java/co_fr.json), [glossary](../../minecraft/java/glossary.tsv), [conventions](../../minecraft/java/STYLE.md), [string inventory](../../minecraft/java/inventory.tsv) |
| Status | See [minecraft/java/STATUS.md](../../minecraft/java/STATUS.md): coverage, review and in-game testing are counted separately. |

NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.

## Install with the Corsu app (automatic)

When Minecraft is installed, the Corsu app offers **Minecraft**. Close Minecraft, tick it and install: Corsu copies
the pack `corsu-minecraft-java.zip` into the `resourcepacks` folder of every game folder it finds (the official
launcher's, and Prism Launcher and MultiMC instances), turns it on and sets `lang:co_fr` in `options.txt`. On the next
start Minecraft is in Corsican. The app's switch puts back the previous language and packs without touching the game's
other settings; uninstalling Corsu also removes the pack. Command line: `python3 src/installer.py --components minecraft`.

## Install by hand

1. Download `corsu-minecraft-java-26.3.zip` and leave it zipped.
2. In Minecraft, open **Options… → Resource Packs… → Open Pack Folder** and drop the file there.
3. Back in the game, the pack shows on the left. Click its arrow to move it to the right, then **Done**.
4. Open **Options… → Language…**, choose **Corsu (Corsica)**, then **Done**.

The pack folder is also here: `%APPDATA%\.minecraft\resourcepacks` on Windows,
`~/Library/Application Support/minecraft/resourcepacks` on macOS, `~/.minecraft/resourcepacks` on Linux (or the
instance folder in Prism Launcher, MultiMC…).

## Update

Replace the old `corsu-minecraft-java-….zip` in the pack folder with the new one, and enable it again in
**Resource Packs** if its name changed. The chosen language stays Corsu.

## Uninstall

1. **Options… → Language…**: choose another language first.
2. **Resource Packs…**: remove the Corsu pack (arrow to the left), then delete the file from the folder.

If the pack is removed while Corsu is still the chosen language, Minecraft falls back to English.

## What is translated, and what is not

Everything Minecraft 26.3 takes from its language files: menus, settings, commands, blocks, items, creatures, biomes,
effects, enchantments, advancements, statistics, subtitles, death messages, Realms, the narrator. A missing string
would show in English.

Three different cases:

- **Cannot depend on the language**: the yellow splash texts on the title screen (`texts/splashes.txt`), the End Poem
  (`texts/end.txt`), the credits (`credits.json`, `postcredits.txt`). A resource pack *can* replace them, but Minecraft
  has a single version of each, read whatever the language: replacing them changes them for every language. Corsu
  therefore translates them in a **separate optional pack** (see below), never in the language pack.
- **A separate component, not covered**: the Minecraft Launcher (Microsoft), translated by Mojang on Crowdin, where
  Corsican is a target language but not shipped. It is not part of the game and Corsu does not change it.
- **Outside the base game**: text sent by a server, written in a world or a book, or added by mods and data packs.

## Optional pack: splash texts and End Poem

`corsu-minecraft-java-texts-26.3.zip` (built by `python3 tools/minecraft.py texts`) replaces the 454 splash texts and
the End Poem with their Corsican translation. **It changes them for every language**, since Minecraft reads only one
version: turn it on only if that suits you, and remove it to get English back. Corsu never installs it by itself. The
End Poem translates Julian Gough's text, which he placed under CC0; the splash texts translate Mojang's text. Choices
and doubts: [minecraft/java/texts/NOTES.md](../../minecraft/java/texts/NOTES.md).

## Other versions

A newer or older version loads the pack after a warning. Texts Mojang added since stay in English, removed ones are
ignored. `python3 tools/minecraft.py diff 26.3 <version>` lists the added, removed and changed strings, and
`python3 tools/minecraft.py inventory <version>` marks the ones whose English changed as "to review".

## Bedrock Edition

Bedrock also accepts a language added by a global pack (`texts/languages.json`, `texts/language_names.json`,
`texts/co_FR.lang`) on Windows, Android and iOS. It is not done yet: Bedrock has its own keys (about 13,000 lines)
and does not reuse the Java files. Consoles generally cannot import packs, and disabling the pack while its language is
selected crashes the game.

## Test in the game

You own Minecraft? Steps and screens to check: [minecraft/java/TESTING.md](../../minecraft/java/TESTING.md).

## Correct a translation

The translations are in `minecraft/java/co_fr.json` (one key, one text). Follow [STYLE.md](../../minecraft/java/STYLE.md)
and the [glossary](../../minecraft/java/glossary.tsv), then run `python3 tools/minecraft.py check`: it checks that no
key is missing and that every `%s`, `%1$s`, `§` code and line break is kept. Or
[open an issue](https://github.com/Platykalt/corsu/issues/new?template=translation.yml) with the key or the text you saw.
