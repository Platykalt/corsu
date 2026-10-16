# Translation status

[Français](../fr/etat-des-traductions.md)

What is translated, what is in progress and what is only planned. Updated 16 October 2026 (Corsu 0.22.0). Which
systems each program works on is in [What works where](compatibility.md).

Three different things are tracked, and none implies the next: **translated** (a Corsican text exists for every
string), **technically checked** (the files are valid and the program loads them) and **reviewed by a speaker** (a
person who speaks Corsican checked the sense and the language).

## Programs Corsu translates

| Program | State | Translated | Technically checked | Reviewed by a speaker |
| --- | --- | --- | --- | --- |
| Firefox (desktop) | Available | menus, settings, error pages; the rest in French | CI on Windows, macOS and Linux | partly (daily use) |
| Discord (app) | Available, partial | interface; about 23,000 labels written for Discord and Vencord | CI: install and restore | no; an AI sense review of 9,942 short labels corrected 110 ([details](../../lexicon/corrections.tsv)) |
| KDE Plasma and KDE programs (Linux) | Available | from the installed French translations | not in CI | daily use |
| Google Chrome (Windows, Linux) | Available | menus and settings | CI | no |
| Opera GX, Edge, Brave, Vivaldi | Experimental | same mechanism as Chrome | no | no |
| Terminal commands, GTK programs (Linux) | Experimental | gettext catalogs built from French | no | no |
| **Minecraft: Java Edition 26.3** | **Under review** | 8,557 / 8,557 texts | Minecraft 26.3's own code reads the pack and renders all 8,559 keys without error | **no**: written by AI, neither reviewed by a speaker nor tried in the game ([status](../../minecraft/java/STATUS.md)) |
| Minecraft splash texts, End Poem | Optional pack, every language | see [Minecraft in Corsican](minecraft.md) | — | no |
| Minecraft Bedrock Edition | Prototype, never tried in the game | 4,288 / 13,340 keys (reused from Java, identical English) | formats checked offline ([status](../../minecraft/bedrock/STATUS.md)) | no |

## Programs that already have a Corsican translation: Corsu switches it on

These programs ship a Corsican translation made upstream, almost always by Patriccollu di Santa Maria è Sichè. Corsu
translates nothing here: it finds the program, checks its Corsican file is there, and changes **one** language setting,
which it gives back when switched off. Corsu never installs the programs. Mechanisms and sources:
[docs/apps-research.md](../apps-research.md).

| Program | Upstream translation | How Corsu switches it | Coverage (measured) | Automatic tests | Real check | Human review |
| --- | --- | --- | --- | --- | --- | --- |
| VLC | Patriccollu, VLC's `po/co.po` | Linux: menu entry started with `LANGUAGE=co:…` (system package), Flatpak override; Windows: VLC's `Lang` setting; macOS: `language` preference | 3.0.24: 4,443 / 6,203 texts (71.6%); Ubuntu's 3.0.20 package: 3,144 Corsican messages for 6,254 French | unit (simulated Linux, Windows, Flatpak); CI: Ubuntu's real VLC shows its help in Corsican, then back | CI Linux only (command-line help, not the window) | upstream (Patriccollu) |
| 7-Zip (Windows) | Patriccollu, `Lang/co.txt` | 7-Zip's `Lang` setting | not measured | unit; CI: real 7-Zip and Windows registry | no | upstream |
| Notepad++ (Windows) | Patriccollu, `corsican.xml` | copied to `nativeLang.xml`, as Notepad++'s own menu does (portable mode too) | not measured | unit; CI: real Notepad++ | no | upstream |
| WinMerge (Windows) | Patriccollu, `Corsican.po` | `LanguageId` = 1155 (portable left alone) | not measured | unit | no | upstream |
| SumatraPDF (Windows) | Patriccollu, built in | `UiLanguage = co` in its settings | not measured | unit | no | upstream |
| FileZilla (Windows, Linux) | Patriccollu, `filezilla.mo` | `Language Code` in `filezilla.xml` | 99.7% (upstream catalogue) | unit | no | upstream |
| HandBrake (Windows, Linux) | Patriccollu, built in / `ghb.mo` | `UiLanguage` in its settings (portable left alone) | not measured | unit | no | upstream |
| VeraCrypt (Windows, Linux) | Patriccollu, `Language.co.xml` | `Language` in `Configuration.xml` | not measured | unit | no | upstream |

A program that rewrites its settings when it quits must be closed (otherwise it is left alone, and Corsu says so); a
missing settings file (program never started) or an unreadable one is neither created nor rewritten; a value you
change afterwards is yours and is not reset when Corsu is switched off. Next: Audacity, Tenacity, fre:ac, PDFsam,
Poedit. Phone apps cannot be set from the computer; on Android 13+, pick each app's language in the phone settings.

## Translations taken from other projects

Corsu's lexicon reuses the Corsican translations published by other free software, almost all by Patriccollu di
Santa Maria è Sichè: Audacity (4,075 lines), Firefox for Android and Focus (2,178), VLC (1,733), WinMerge (1,730),
wxWidgets (1,724), VLC for Android (1,191), Firefox for iOS (1,000), Notepad++ (898), Thunderbird for Android (830),
fre:ac (784), Tenacity (672), Poedit (658), OpenTracks (467), Mozilla VPN (418), Inno Setup (253),
Focus for iOS (140). Each keeps its licence ([lexicon-upstream.tsv](../../lexicon/lexicon-upstream.tsv),
[lexicon-mozilla.tsv](../../lexicon/lexicon-mozilla.tsv)). wxWidgets, fre:ac and Inno Setup are new in 0.22.0.

Several of his translations already ship inside the programs, which need no Corsu: choose Corsican in their
settings (VeraCrypt, SumatraPDF, PDFsam, FileZilla, Notepad++, WinMerge, Poedit, HandBrake…). His full list:
[Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica).

## Coming next

See the [roadmap](roadmap.md).
