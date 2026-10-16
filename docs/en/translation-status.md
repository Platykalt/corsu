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
| Minecraft Bedrock Edition | Planned | — | — | — |

## Translations taken from other projects

Corsu's lexicon reuses the Corsican translations published by other free software, almost all by Patriccollu di
Santa Maria è Sichè: Audacity (4,075 lines), Firefox for Android and Focus (2,178), VLC (1,733), WinMerge (1,730),
wxWidgets (1,724), VLC for Android (1,191), Firefox for iOS (1,000), Notepad++ (898), Thunderbird for Android (830),
fre:ac (784), HandBrake (677), Tenacity (672), Poedit (658), OpenTracks (467), Mozilla VPN (418), Inno Setup (253),
Focus for iOS (140). Each keeps its licence ([lexicon-upstream.tsv](../../lexicon/lexicon-upstream.tsv),
[lexicon-mozilla.tsv](../../lexicon/lexicon-mozilla.tsv)). wxWidgets, fre:ac and Inno Setup are new in 0.22.0.

Several of his translations already ship inside the programs, which need no Corsu: choose Corsican in their
settings (VeraCrypt, SumatraPDF, PDFsam, FileZilla, Notepad++, WinMerge, Poedit, HandBrake…). His full list:
[Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica).

## Coming next

See the [roadmap](roadmap.md).
