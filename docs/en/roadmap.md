# Roadmap

[Français](../fr/feuille-de-route.md)

Everything below is **planned or under consideration**, not available. What works today is in
[What works where](compatibility.md). Status as of 19 October 2026 (published release: 0.26.0). The French page has the full tables, including
the inventory of software already in Corsican elsewhere; this is a summary.

## Already in Corsican elsewhere

Most of it is the work of Patriccollu di Santa Maria è Sichè, whose list is the reference:
[Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica). Mozilla ships Firefox for
Android and iOS, Focus and Mozilla VPN in Corsican, but **not Firefox or Thunderbird for desktop**, which is why Corsu
builds its own Firefox translation. Mozilla does not accept a new desktop locale with a single active translator
([details](https://discourse.mozilla.org/t/about-requesting-a-new-locale-for-firefox/86515)).
Thunderbird for Android (92.8 %), Tenacity (98.4 %) and OpenTracks (76.1 %) are on Hosted Weblate; Notepad++, WinMerge, Poedit, HandBrake, Audacity, VeraCrypt, SumatraPDF, PDFsam and FileZilla carry
Corsican in their own releases. No Corsican was found for LibreOffice, GIMP, Inkscape, KeePassXC, F-Droid, OsmAnd or
Luanti.

## Done in 0.26.0

- Phone keyboard: a Corsu dictionary for Keyman that keeps the capitals you type, and experimental regional
  preferences (Cismuntincu, Pumuntincu).
- Minecraft Java: a further AI review of the texts (October 2026). Still no review by a speaker.

## Next, in order

**Ready now**
- Minecraft Java: done; Corsu makes Corsican the game's language (component `minecraft`; 26.3 since 0.22.0, 87
  versions since 0.23.0).
- Minecraft Java: review by a speaker, key by key, with statuses in `minecraft/java/inventory.tsv` (8,559 strings).
- Minecraft Java: a screen-by-screen in-game test of 26.3 (menus, inventory, death screen, subtitles). So far 26.3
  has only been started once with the pack, on the maintainer's instance (game log checked, no screens recorded).
- Minecraft Java: follow new versions with `tools/minecraft.py diff` (26.2 → 26.3 added 436 strings and changed 56).
- Discord: finish the semantic review of short labels (about 9,900 labels of 1 to 5 words).
- Lexicon: report the imported translations whose French did not match their English back to the original projects.

**Needs a study or a partner**
- Minecraft Bedrock: a global pack (`texts/co_FR.lang`, `languages.json`, `language_names.json`) on Windows, Android,
  iOS; about 13,000 lines with keys of its own; consoles are closed.
- Official Minecraft and its launcher (Crowdin, `co` already listed, not shipped): Mojang decides what ships; its
  contributor terms were not found; decide the texts' licence first (`minecraft/java/LICENSING.md`).
- Official Firefox desktop: Mozilla first wants several active Corsican translators on its smaller projects; an
  attempt in 2010 was closed ([bug 599312](https://bugzilla.mozilla.org/show_bug.cgi?id=599312)).
- Stardew Valley (custom languages since 1.5.5, via Content Patcher), RimWorld and Factorio (language mods): one game
  at a time, volume to be measured on each game's files.
- Free games upstream: Luanti, Mindustry, Wesnoth, SuperTuxKart, OpenTTD.

**Steam**: no official Corsican and no supported mechanism for the client or the website. Steamworks
[only supports its own languages](https://partner.steamgames.com/doc/store/localization/languages) and its translation
server (now valve.crowdin.com) does not offer Corsican; no public way to request a language was found. Unofficial
client mods can replace text on one's own computer, but Valve does not support them and updates undo them; Corsu does
not offer that. Games on Steam are case by case; the Workshop only where the game allows language mods.

**Tools for contributors**: Crowdin's free open-source plan asks for a project older than three months with an active
community, which Corsu (started 30 September 2026) does not meet yet; Weblate Libre is the other option. For now:
the translation issue form and the statuses in `minecraft/java/inventory.tsv`.

**Speculative**: a licence or export for INFCOR from ADECEC; a Corsican Hunspell spellchecker built from attested
forms; a shared translation memory with context and provenance.
