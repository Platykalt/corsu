# État des traductions

[English](../en/translation-status.md)

Ce qui est traduit, ce qui est en cours et ce qui est seulement prévu. Mis à jour le 19 octobre 2026 ; version publiée : Corsu 0.28.0.
Les systèmes pris en charge par chaque logiciel sont dans [Ce qui marche, et où](compatibilite.md).

Trois choses différentes sont suivies, et l'une n'entraîne pas l'autre :
**traduit** (un texte corse existe pour chaque chaîne), **vérifié techniquement** (les fichiers sont valides et le
logiciel les charge) et **relu par un locuteur** (le sens et la langue ont été contrôlés par une personne qui parle
corse).

Statuts : **disponible** (dans la version publiée 0.28.0), **expérimental** (disponible, peu vérifié sur ce système),
**candidat** (dans la prochaine version, pas encore publiée), **prototype** ou **prévu** (pas disponible).

## Logiciels traduits par Corsu

| Logiciel | État | Traduit | Vérifié techniquement | Relu par un locuteur |
| --- | --- | --- | --- | --- |
| Firefox (bureau) | Disponible | menus, réglages, pages d'erreur ; le reste en français | CI sur Windows, macOS et Linux | en partie (usage quotidien) |
| Discord (application) | Disponible, partiel | interface ; environ 23 000 libellés écrits pour Discord et Vencord | CI : installation et retrait | non ; relecture automatique du sens par IA de 9 942 libellés courts, 110 corrigés ([détail](../../lexicon/corrections.tsv)) |
| KDE Plasma et programmes KDE (Linux) | Disponible | à partir des traductions françaises installées | non testé par la CI | usage quotidien |
| Google Chrome (Windows, Linux) | Disponible | menus et réglages | CI | non |
| Opera GX, Edge, Brave, Vivaldi | Expérimental | même mécanisme que Chrome | non | non |
| Commandes du terminal, programmes GTK (Linux) | Expérimental | catalogues gettext construits depuis le français | non | non |
| **Minecraft: Java Edition, 87 versions (1.6.1 → 26.3)** | **Disponible** depuis 0.23.0 ; relecture par un locuteur à faire | fichiers de langue complets pour chaque version listée ([tableau](../../minecraft/java/COMPATIBILITY.md)) | le code de chaque version lit le pack et affiche chaque texte, avec les exceptions listées | **non** : écrite par IA, relue par un locuteur : 0 ; chargée en jeu : 26.3 seulement ([état](../../minecraft/java/STATUS.md)) |
| Minecraft : phrases d'accueil, poème de fin | Disponible, pack facultatif à installer soi-même (change ces textes pour toutes les langues) | voir [Minecraft en corse](minecraft.md) | — | non |
| Minecraft Bedrock Edition | Prototype, jamais essayé en jeu | 4 272 / 13 340 clés (reprises de Java, anglais identique) | formats vérifiés hors jeu ([état](../../minecraft/bedrock/STATUS.md)) | non |

## Logiciels qui ont déjà leur traduction corse : Corsu l'active

Ces logiciels ont une traduction corse faite en amont, presque toujours par Patriccollu di Santa Maria è Sichè, et
livrée avec le logiciel. Corsu ne traduit rien ici : il trouve le logiciel, vérifie que son fichier corse est présent
et change **un seul réglage** de langue, qu'il rend à la désactivation. Les logiciels eux-mêmes ne sont jamais
installés par Corsu. Détail des mécanismes et des sources : [docs/apps-research.md](../apps-research.md).

| Logiciel | Traduction amont | Activation par Corsu | Couverture (mesurée) | Tests automatiques | Essai réel | Revue humaine |
| --- | --- | --- | --- | --- | --- | --- |
| VLC | Patriccollu, `po/co.po` de VLC | Linux : entrée de menu lancée avec `LANGUAGE=co:…` (paquet du système), override du Flatpak ; Windows : réglage `Lang` de VLC ; macOS : préférence `language` | 3.0.24 : 4 443 / 6 203 textes (71,6 %) ; paquet Ubuntu 3.0.20 : 3 144 messages corses pour 6 254 français | unitaires (Linux, Windows, Flatpak simulés) ; CI : vrai VLC d'Ubuntu, aide affichée en corse, puis retour | CI Linux seulement (aide en ligne de commande, pas la fenêtre) | celle de Patriccollu en amont |
| VLC, complément expérimental (désactivé par défaut, `--vlc-complement on`) | amont + 1 757 brouillons IA relus par IA (`contrib/vlc`) | Linux, paquet du système 3.0.x : l'entrée de menu ajoute `VLC_DATA_PATH` vers le dossier de Corsu ; aucun fichier système touché | 6 200 / 6 203 textes de 3.0.24 (3 incertains exclus) | unitaires ; CI : vrai VLC (Ubuntu 3.0.20), 741 nouveaux textes affichés en corse, puis désactivé ; aussi 3.0.24 de Debian dans un conteneur | fenêtres Qt vues dans un conteneur (3.0.24) | IA seulement, pas un locuteur |
| 7-Zip (Windows) | Patriccollu, `Lang/co.txt` | réglage `Lang` de 7-Zip | non mesurée | unitaires ; CI : vrai 7-Zip et registre Windows | non | amont |
| Notepad++ (Windows) | Patriccollu, `corsican.xml` | copie en `nativeLang.xml`, comme le menu de Notepad++ (mode portable compris) | non mesurée | unitaires ; CI : vrai Notepad++ | non | amont |
| WinMerge (Windows) | Patriccollu, `Corsican.po` | réglage `LanguageId` = 1155 (portable laissé tel quel) | non mesurée | unitaires | non | amont |
| SumatraPDF (Windows) | Patriccollu, intégrée au programme | `UiLanguage = co` dans ses réglages | non mesurée | unitaires | non | amont |
| FileZilla (Windows, Linux) | Patriccollu, `filezilla.mo` | `Language Code` dans `filezilla.xml` | 99,7 % (catalogue amont) | unitaires | non | amont |
| HandBrake (Windows, Linux) | Patriccollu, intégrée / `ghb.mo` | `UiLanguage` dans ses réglages (portable laissé tel quel) | non mesurée | unitaires | non | amont |
| VeraCrypt (Windows, Linux) | Patriccollu, `Language.co.xml` | `Language` dans `Configuration.xml` | non mesurée | unitaires | non | amont |
| Audacity 3 (Linux, Flatpak, Windows, macOS) | amont, `audacity.mo` | `[Locale] Language=co` dans `audacity.cfg` | mesurée par rapport au français quand les deux catalogues sont là | unitaires (simulés) | Linux : AppImage officielle 3.7.7, menus vus en corse | amont |
| Audacity 4 (Linux ; Windows, macOS expérimentaux) | amont, `audacity_co.qm` | `language=co` dans `[General]` d'`Audacity4.ini` (macOS : préférence) | 4 050 / 4 050 (source 4.0.1) | unitaires (simulés) | Linux : AppImage officielle 4.0.1, fenêtre vue en corse | amont |
| Tenacity 1.3 (Linux, Flatpak, Windows, macOS) | amont, `tenacity.mo` | `[Locale] Language=co` dans `tenacity.cfg` | 3 851 / 4 106 (93,8 %) | unitaires (simulés) | Linux : AppImage officielle 1.3.5, menus vus en corse | amont |
| fre:ac 1.1 (Windows, Linux) | amont, `freac_co.xml` | `Language` = `freac_co.xml` dans `freac.xml` | 1 104 / 1 104 (zip 1.1.7) ; paquet Debian 1.1.7+git20260412 : 1 111 / 1 117 | unitaires (simulés) ; vrai paquet Debian dans un conteneur (Linux) | Linux : fenêtre vue en corse (conteneur) | amont |
| Poedit (Linux, Flatpak, Windows ; macOS expérimental) | Patriccollu, `co.po` de Poedit | Linux : entrée de menu lancée avec `LANGUAGE=co:…` et `LC_MESSAGES=/C.UTF-8` ; Windows : `ui_language` = `co` dans le registre ; macOS : préférence `AppleLanguages` de Poedit | 1 089 messages (Windows 3.10, autant que le français) | unitaires (Windows, macOS simulés ; aller-retour `defaults` sur un Mac de CI) | Linux : paquet Debian 3.6.3 et Flatpak 3.10, fenêtre et dialogues GTK vus en corse (conteneur) | amont |
| PDFsam Basic 5.0+ (Linux, Windows ; pas macOS) | Patriccollu, `Messages_co.properties` | préférence Java `locale` = `co` | non mesurée | unitaires (Windows simulé) | Linux : paquet .deb 6.0.6 (conteneur) | amont |

Règles communes : un logiciel qui réécrit ses réglages en quittant doit être fermé (sinon il est laissé tel quel, et
Corsu le dit) ; un fichier de réglages absent (logiciel jamais lancé) ou illisible n'est pas créé ni réécrit ; une
valeur que vous changez ensuite vous appartient et n'est pas remise à la désactivation. Audacity, Tenacity et fre:ac sont
disponibles depuis 0.24.0, Poedit et PDFsam depuis 0.25.1. Applications de téléphone : Corsu ne peut pas les régler depuis l'ordinateur ;
sur Android 13 et plus, choisissez la langue de chaque application dans les réglages du téléphone.

## Traductions reprises d'autres projets

Le lexique de Corsu reprend aussi ces traductions comme **vocabulaire** (avec leur contexte, leur version et leur
licence, dans `lexicon/memory/`), pour traduire de manière cohérente les logiciels qui n'en ont pas. Reprendre du
vocabulaire n'active rien dans le logiciel d'origine : c'est la section précédente qui le fait. Chaque section garde sa licence ([lexicon-upstream.tsv](../../lexicon/lexicon-upstream.tsv),
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
