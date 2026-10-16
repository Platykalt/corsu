# Roadmap

[Français](../fr/feuille-de-route.md)

Everything below is **planned or under consideration**, not available. What works today is in
[What works where](compatibility.md). Status as of 16 October 2026. The French page has the full tables, including
the inventory of software already in Corsican elsewhere; this is a summary.

## Already in Corsican elsewhere

Most of it is the work of Patriccollu di Santa Maria è Sichè, whose list is the reference:
[Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica). Mozilla ships Firefox for
Android and iOS, Focus and Mozilla VPN in Corsican, but **not Firefox or Thunderbird for desktop**, which is why Corsu
builds its own Firefox translation. Thunderbird for Android (92.8 %), Tenacity (98.4 %) and OpenTracks (76.1 %) are on
Hosted Weblate; Notepad++, WinMerge, Poedit, HandBrake, Audacity, VeraCrypt, SumatraPDF, PDFsam and FileZilla carry
Corsican in their own releases. No Corsican was found for LibreOffice, GIMP, Inkscape, KeePassXC, F-Droid, OsmAnd or
Luanti.

## Next, in order

**Ready now**
- Minecraft Java: review by a speaker, key by key, with statuses in `minecraft/java/inventory.tsv` (8,559 strings).
- Minecraft Java: one in-game test of 26.3 (menus, inventory, death screen, subtitles) by someone who owns the game.
- Minecraft Java: follow new versions with `tools/minecraft.py diff` (26.2 → 26.3 added 436 strings and changed 56).
- Discord: finish the semantic review of short labels (about 9,900 labels of 1 to 5 words).
- Lexicon: report the imported translations whose French did not match their English back to the original projects.

**Needs a study or a partner**
- Minecraft Bedrock: a global pack (`texts/co_FR.lang`, `languages.json`, `language_names.json`) on Windows, Android,
  iOS; about 13,000 lines with keys of its own; consoles are closed.
- Official Minecraft (Crowdin, `co` already listed): rights go to Mojang; ask the project owner first.
- Official Firefox desktop: ask Mozilla to open the `firefox` project for `co` on Pontoon.
- Stardew Valley (custom languages since 1.5.5, via Content Patcher), RimWorld and Factorio (language mods): one game
  at a time, volume to be measured on each game's files.
- Free games upstream: Luanti, Mindustry, Wesnoth, SuperTuxKart, OpenTTD.

**Steam**: the Steam client and website cannot get Corsican (Valve only takes its 31 interface languages and Corsican
is not even in the list a game can declare). Games on Steam are case by case; the Workshop only where the game allows
language mods; a Corsu installer for game packs would also have to be built game by game.

**Speculative**: a licence or export for INFCOR from ADECEC; a Corsican Hunspell spellchecker built from attested
forms; a shared translation memory with context and provenance.
