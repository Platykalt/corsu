# État des traductions

[English](../en/translation-status.md)

Ce qui est traduit, ce qui est en cours et ce qui est seulement prévu. Mis à jour le 16 octobre 2026 (Corsu 0.22.0).
Les systèmes pris en charge par chaque logiciel sont dans [Ce qui marche, et où](compatibilite.md).

Trois choses différentes sont suivies, et l'une n'entraîne pas l'autre :
**traduit** (un texte corse existe pour chaque chaîne), **vérifié techniquement** (les fichiers sont valides et le
logiciel les charge) et **relu par un locuteur** (le sens et la langue ont été contrôlés par une personne qui parle
corse).

## Logiciels traduits par Corsu

| Logiciel | État | Traduit | Vérifié techniquement | Relu par un locuteur |
| --- | --- | --- | --- | --- |
| Firefox (bureau) | Disponible | menus, réglages, pages d'erreur ; le reste en français | CI sur Windows, macOS et Linux | en partie (usage quotidien) |
| Discord (application) | Disponible, partiel | interface ; environ 23 000 libellés écrits pour Discord et Vencord | CI : installation et retrait | non ; relecture automatique du sens par IA de 9 942 libellés courts, 110 corrigés ([détail](../../lexicon/corrections.tsv)) |
| KDE Plasma et programmes KDE (Linux) | Disponible | à partir des traductions françaises installées | non testé par la CI | usage quotidien |
| Google Chrome (Windows, Linux) | Disponible | menus et réglages | CI | non |
| Opera GX, Edge, Brave, Vivaldi | Expérimental | même mécanisme que Chrome | non | non |
| Commandes du terminal, programmes GTK (Linux) | Expérimental | catalogues gettext construits depuis le français | non | non |
| **Minecraft: Java Edition 26.3** | **En cours de relecture** | 8 557 / 8 557 textes | le code de Minecraft 26.3 lit le pack et affiche les 8 559 clés sans erreur | **non** : traduction écrite par IA, ni relue par un locuteur ni essayée en jeu ([état](../../minecraft/java/STATUS.md)) |
| Minecraft : phrases d'accueil, poème de fin | Pack facultatif, toutes langues | voir [Minecraft en corse](minecraft.md) | — | non |
| Minecraft Bedrock Edition | Prototype, jamais essayé en jeu | 4 288 / 13 340 clés (reprises de Java, anglais identique) | formats vérifiés hors jeu ([état](../../minecraft/bedrock/STATUS.md)) | non |

## Traductions reprises d'autres projets

Le lexique de Corsu reprend les traductions corses publiées par d'autres logiciels libres, presque toutes de
Patriccollu di Santa Maria è Sichè. Elles servent de vocabulaire de référence et traduisent les mêmes libellés
ailleurs. Chaque section garde sa licence ([lexicon-upstream.tsv](../../lexicon/lexicon-upstream.tsv),
[lexicon-mozilla.tsv](../../lexicon/lexicon-mozilla.tsv), `tools/import_translations.py`).

| Projet | Lignes reprises | Licence |
| --- | --- | --- |
| Audacity | 4 075 | GPL-2.0-or-later |
| Firefox pour Android, Focus | 2 178 | MPL-2.0 |
| VLC (bureau) | 1 733 | GPL-2.0-or-later |
| WinMerge | 1 730 | GPL-2.0-or-later |
| wxWidgets (boîtes de dialogue de nombreux programmes) | 1 724 | licence wxWindows |
| VLC pour Android | 1 191 | GPL-2.0-or-later |
| Firefox pour iOS | 1 000 | MPL-2.0 |
| Notepad++ | 898 | GPL-3.0-or-later |
| Thunderbird pour Android | 830 | Apache-2.0 |
| fre:ac | 784 | GPL-2.0-or-later |
| Tenacity | 672 | GPL-2.0-or-later |
| Poedit | 658 | MIT |
| OpenTracks | 467 | Apache-2.0 |
| Mozilla VPN | 418 | MPL-2.0 |
| Inno Setup (assistants d'installation) | 253 | licence Inno Setup |
| Firefox Focus pour iOS | 140 | MPL-2.0 |

wxWidgets, fre:ac et Inno Setup sont nouveaux dans 0.22.0. D'autres traductions de Patriccollu existent déjà
dans les logiciels eux-mêmes et n'ont pas besoin de Corsu : il suffit de choisir le corse dans leurs réglages
(VeraCrypt, SumatraPDF, PDFsam, FileZilla, Notepad++, WinMerge, Poedit, HandBrake…). Sa liste complète :
[Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica).

## En préparation

Voir la [feuille de route](feuille-de-route.md).
