# Corsu

[![CI](https://github.com/Platykalt/corsu/actions/workflows/ci.yml/badge.svg)](https://github.com/Platykalt/corsu/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Platykalt/corsu?label=version)](https://github.com/Platykalt/corsu/releases/latest)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)](LICENSE)

**[Français](#français) · [English](#english)**

Corsu met en corse les logiciels de tous les jours. Corsu puts everyday software in Corsican.

**[Écrire en corse sur Android et iPhone](#écrire-en-corse-sur-android-et-iphone)** ·
**[Write Corsican on Android and iPhone](#write-corsican-on-android-and-iphone)**

---

## Français

Corsu met en corse les menus et les réglages de Firefox et de l'application Discord sous Windows, macOS et Linux, et
ceux de Google Chrome sous Windows et Linux. Sous Linux seulement, il traduit aussi le bureau KDE Plasma, les
programmes KDE et Qt et les commandes du terminal. Opera GX et les autres navigateurs Chromium sont pris en charge à
titre expérimental. Chaque partie peut être désactivée puis réactivée à tout moment, et le détail système par système
est dans [Ce qui marche, et où](docs/fr/compatibilite.md).

<!-- corsu:minecraft-summary:start -->
**Minecraft Java en corse pour 87 versions** (versions stables 1.6.1 → 26.3). Traduction complète des fichiers de langue pour les versions listées ; vérifications techniques avec le code de chaque version. L'application Corsu trouve la version de chaque dossier de jeu, y ajoute le pack de cette version et choisit le corse. Textes écrits par IA, sans relecture par un locuteur ; vérifications automatiques, pas visuelles ; seule la 26.3 a été lancée avec le pack. Disponibilité : dans les versions publiées de Corsu à partir de 0.23.0. Détails et limites : [Minecraft en corse](docs/fr/minecraft.md), [versions et vérifications](minecraft/java/COMPATIBILITY.md).
<!-- corsu:minecraft-summary:end -->

**Logiciels déjà traduits en corse** : VLC, 7-Zip, Notepad++, WinMerge, SumatraPDF, FileZilla, HandBrake et VeraCrypt
ont une traduction corse faite par Patriccollu di Santa Maria è Sichè. Quand ils sont installés, l'application Corsu
les propose et règle leur langue sur le corse, puis la rend à la désactivation. Dans la version de développement
(pas encore publiée) : Audacity 3 et 4, Tenacity et fre:ac, avec leur propre traduction corse.

Ce qui est traduit, ce qui est en cours et ce qui est prévu : **[État des traductions](docs/fr/etat-des-traductions.md)**.

### Pourquoi Corsu

Apprendre une langue, savoir la parler et avoir des occasions de s'en servir sont trois choses différentes.
Beaucoup de Corses, surtout sur la côte et en ville, n'ont pas d'endroit où pratiquer le corse en dehors de l'école,
alors que ce sont eux qui passent le plus de temps en ligne. Et de nombreux locuteurs ne parlent pas corse parce que
la langue leur semble décalée dans le contexte où ils se trouvent.

L'irlandais montre cet écart : au recensement de 2022, 1 873 997 personnes en République d'Irlande déclaraient savoir
le parler, mais 71 968 seulement le parlaient tous les jours en dehors du système éducatif
([CSO, recensement 2022](https://www.cso.ie/en/releasesandpublications/ep/p-cpp8/censusofpopulation2022profile8-theirishlanguageandeducation/irishlanguageandthegaeltacht/)).

Corsu a deux objectifs :

1. **Rendre le corse familier au quotidien**, en le faisant rencontrer dans les interfaces qu'on utilise tous les
   jours. Cet apprentissage passif complète les cours et la conversation.
2. **Donner au corse plus d'endroits où il paraît naturel**, à commencer par les ordinateurs et les téléphones, pour
   qu'il devienne une langue normale pour s'exprimer en ligne.

Une interface traduite ne remplace pas les échanges entre locuteurs. Pour pratiquer le corse et progresser, même sans
personne à qui le parler :

- [Sapienzia](https://www.sapienzia.io) : traduction, dictionnaire, conjugaison et assistant de conversation en corse ;
- [Astutu](https://astutu.corsica) : assistant qui répond en corse ;
- [LIV](https://liv.corsica) : une intelligence artificielle qui parle corse.

La version longue : [Pourquoi Corsu](docs/fr/pourquoi-corsu.md).

### Installer sur un ordinateur

| Système | Téléchargement | Ensuite | Guide |
| --- | --- | --- | --- |
| Windows | [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip) | décompresser, double-cliquer sur `Install for Windows.cmd` | [Windows](docs/fr/ordinateur/windows.md) |
| macOS | [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz) | double-cliquer sur `Install for macOS.command` | [macOS](docs/fr/ordinateur/macos.md) |
| Linux | [corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz) | lancer `./"Install for Linux.sh"` | [Linux](docs/fr/ordinateur/linux.md) |

Ou en une ligne, dans PowerShell sous Windows : `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex`
Dans le Terminal sous macOS ou Linux : `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh`

L'application Corsu s'ouvre dans sa fenêtre avec les logiciels trouvés, tous cochés. Elle montre ce qui va
changer avant de le faire, et Corsu garde une copie de chaque fichier modifié. Rouvrez-la ensuite depuis le menu des
applications pour ajouter un logiciel, remettre une partie dans sa langue d'origine (le terminal pendant une heure,
par exemple) ou tout retirer.

<img src="docs/images/corsu-setup-fr.png" alt="L'application Corsu : Firefox, Discord et le bureau KDE Plasma en corse, chacun avec son interrupteur" width="570">

**Mettre à jour ou réparer.** Relancez la même commande (ou l'installeur de l'archive téléchargée), ou utilisez le
bouton « Mettre à jour » de l'application Corsu (rubrique À propos) : c'est le même mécanisme. Corsu trouve la version
installée : il la met à jour si celle-ci est plus récente, ou la répare si c'est la même ; une version plus ancienne est
refusée, sauf avec `--allow-downgrade`. Vos choix sont gardés : les logiciels choisis le restent, ce que vous avez
désactivé reste désactivé, et rien de nouveau n'est ajouté sans votre accord. Le téléchargement est vérifié avec sa
somme SHA-256 publiée avant toute modification. Une seule opération Corsu à la fois : si une autre est en cours, Corsu
affiche « Corsu est déjà occupé » et ne change rien.

Discord : réglez sa langue sur Français ou English, voir [Discord en corse](docs/fr/discord.md).
Google en corse : choisissez Corsu dans la langue de votre compte Google, voir [ce guide](docs/fr/compatibilite.md#google-et-les-autres-sites). Dans Firefox Corsu, les boutons que Google laisse en français ou en anglais sont complétés en corse.
Ce qui est vérifié et ce qui est seulement prévu : [Ce qui marche, et où](docs/fr/compatibilite.md).

### Écrire en corse sur Android et iPhone

Le clavier gratuit [Keyman](https://keyman.com) fournit les touches (disposition EuroLatin (SIL), langue Corsican) ;
Corsu fournit le dictionnaire, qui propose des mots corses pendant que vous écrivez et corrige leur orthographe.
L'application Corsu pour ordinateur n'est pas nécessaire. Ce n'est ni un traducteur de phrases ni un correcteur de
grammaire complet.

| Téléphone | Keyman | Guide pas à pas |
| --- | --- | --- |
| Android | [Play Store](https://play.google.com/store/apps/details?id=com.tavultesoft.kmapro) | [Android](docs/fr/telephone/android.md) |
| iPhone | [App Store](https://apps.apple.com/app/keyman/id933676545) | [iPhone](docs/fr/telephone/iphone.md) |

Dictionnaire publié (le même fichier pour Android et iPhone) :
[corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp), le dictionnaire
général (environ 17 000 mots corses courants).
<!-- corsu:phone-variants:fr Ne lister ci-dessus que les fichiers joints à la dernière version publiée ; à la
     publication, y déplacer ceux de la phrase suivante. -->
Dans la prochaine version (pas encore publiée) : un `corsu-keyboard.kmp` qui garde la majuscule des mots, et deux
dictionnaires expérimentaux qui préfèrent les formes d'une région, `corsu-keyboard-cismuntincu.kmp` et
`corsu-keyboard-pumuntincu.kmp`. Keyman 18 n'a pas de correction automatique : les corrections sont proposées dans le
bandeau, à toucher.

### Les traductions

Le lexique de Corsu compte environ 138 000 lignes de traduction, chacune un texte source et sa traduction corse.
Plus de 18 000 sont reprises d'autres logiciels libres, traduits pour la plupart par Patriccollu di Santa Maria è Sichè
(Firefox pour Android et iOS, Thunderbird pour Android, VLC, Audacity, Notepad++, Poedit, WinMerge,
Tenacity, OpenTracks, wxWidgets, fre:ac, Inno Setup…). Les autres ont été écrites pour Corsu avec le même vocabulaire,
dont plus de 23 000 pour Discord et Vencord ; ce sont des premières versions, que chacun peut relire et corriger.
Une traduction vous paraît fausse ?
[Ouvrez un ticket](https://github.com/Platykalt/corsu/issues/new?template=translation.yml) ou voyez
[CONTRIBUTING.md](CONTRIBUTING.md).

Pour aller plus loin : [toute la documentation](docs/README.md), [ce que Corsu modifie](docs/fr/ce-que-corsu-modifie.md),
[développement](docs/fr/developpeurs.md), [sécurité](SECURITY.md), [CHANGELOG.md](CHANGELOG.md).

---

## English

Corsu puts the menus and settings of Firefox and the Discord app in Corsican on Windows, macOS and Linux, and those of
Google Chrome on Windows and Linux. On Linux only, it also translates the KDE Plasma desktop, KDE and Qt programs and
terminal commands. Opera GX and the other Chromium browsers are experimental. Each part can be switched off and on
again at any time, and the details for each system are in [What works where](docs/en/compatibility.md).

<!-- corsu:minecraft-summary:start -->
**Minecraft: Java Edition in Corsican for 87 versions** (releases 1.6.1 → 26.3). Complete translation of the language files for the listed versions; technical checks with each version's own code. The Corsu app finds the version of each game folder, adds that version's pack and picks Corsican. AI-written texts, not reviewed by a speaker; automated checks, not visual ones; only 26.3 has been started with the pack. Availability: in published Corsu releases from 0.23.0. Details and limits: [Minecraft in Corsican](docs/en/minecraft.md), [versions and checks](minecraft/java/COMPATIBILITY.md).
<!-- corsu:minecraft-summary:end -->

**Programs already translated into Corsican**: VLC, 7-Zip, Notepad++, WinMerge, SumatraPDF, FileZilla, HandBrake and
VeraCrypt have a Corsican translation by Patriccollu di Santa Maria è Sichè. When they are installed, the Corsu app offers
them and sets their language to Corsican, and gives it back when switched off. In the development version (not yet
published): Audacity 3 and 4, Tenacity and fre:ac, with their own Corsican translation.

What is translated, in progress and planned: **[Translation status](docs/en/translation-status.md)**.

### Why Corsu

Learning a language, being able to speak it and having occasions to use it are three different things. Many
Corsicans, especially on the coast and in towns, have nowhere to practise Corsican outside school, while they are the
people who spend the most time online. And many speakers do not use Corsican because it feels out of place in the
situations they are in.

Irish shows the gap: in the 2022 census, 1,873,997 people in the Republic of Ireland said they could speak it, but
only 71,968 spoke it every day outside the education system ([CSO, Census 2022](https://www.cso.ie/en/releasesandpublications/ep/p-cpp8/censusofpopulation2022profile8-theirishlanguageandeducation/irishlanguageandthegaeltacht/)).

Corsu has two goals:

1. **Make Corsican familiar every day**, by meeting it in the interfaces people use daily. This passive learning adds
   to lessons and conversation.
2. **Give Corsican more places where it feels natural**, starting with computers and phones, so that it becomes a
   normal language to express yourself online.

A translated interface does not replace talking with other speakers. To practise Corsican and improve, even with
nobody around to speak it with:

- [Sapienzia](https://www.sapienzia.io): translation, dictionary, conjugation and a conversation assistant in Corsican;
- [Astutu](https://astutu.corsica): an assistant that answers in Corsican;
- [LIV](https://liv.corsica): an artificial intelligence that speaks Corsican.

The long version: [Why Corsu](docs/en/why-corsu.md).

### Install on a computer

| System | Download | Then | Guide |
| --- | --- | --- | --- |
| Windows | [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip) | extract it, double-click `Install for Windows.cmd` | [Windows](docs/en/computer/windows.md) |
| macOS | [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz) | double-click `Install for macOS.command` | [macOS](docs/en/computer/macos.md) |
| Linux | [corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz) | run `./"Install for Linux.sh"` | [Linux](docs/en/computer/linux.md) |

Or in one line, in PowerShell on Windows: `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex`
In Terminal on macOS or Linux: `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh`

The Corsu app opens in its own window with the programs found, all ticked. It shows what will change before
doing it, and Corsu keeps a copy of every file it changes. Open it again from the applications menu to add a program,
put a part back in its original language (the terminal for an hour, for example) or remove everything.

<img src="docs/images/corsu-setup-en.png" alt="The Corsu app: Firefox, Discord and the KDE Plasma desktop in Corsican, each with its own switch" width="570">

**Updating or repairing.** Run the same command again (or the downloaded archive's installer), or use the Corsu app's
"Update" button (in About): it is the same mechanism. Corsu finds the installed version and updates it if this one is
newer, or repairs it if it is the same; an older version is refused unless you add `--allow-downgrade`. Your choices
are kept: the programs you chose stay chosen, parts you switched off stay off, and nothing new is added unless you
select it. The download is checked against its published SHA-256 before anything changes. Only one Corsu task runs at
a time; if another is running, Corsu says "Corsu is already busy" and changes nothing.

Discord: set its language to Français or English, see [Discord in Corsican](docs/en/discord.md).
Google in Corsican: choose Corsu as your Google account language, see [this guide](docs/en/compatibility.md#google-and-other-websites). In Firefox Corsu, the buttons Google leaves in French or English are completed in Corsican.
What is verified and what is only expected: [What works where](docs/en/compatibility.md).

### Write Corsican on Android and iPhone

The free [Keyman](https://keyman.com) keyboard gives the keys (EuroLatin (SIL) layout, Corsican language); Corsu gives
the dictionary, which suggests Corsican words as you type and corrects their spelling. The Corsu desktop app is not
needed. It is neither a sentence translator nor a full grammar checker.

| Phone | Keyman | Step-by-step guide |
| --- | --- | --- |
| Android | [Play Store](https://play.google.com/store/apps/details?id=com.tavultesoft.kmapro) | [Android](docs/en/phone/android.md) |
| iPhone | [App Store](https://apps.apple.com/app/keyman/id933676545) | [iPhone](docs/en/phone/iphone.md) |

Published dictionary (the same file for Android and iPhone):
[corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp), the general
dictionary (about 17,000 common Corsican words).
<!-- corsu:phone-variants:en List above only the files attached to the latest published release; at release time,
     move there those of the next sentence. -->
In the next version (not published yet): a `corsu-keyboard.kmp` that keeps the capital letters of words, and two
experimental dictionaries preferring one region's forms, `corsu-keyboard-cismuntincu.kmp` and
`corsu-keyboard-pumuntincu.kmp`. Keyman 18 has no automatic correction: corrections are offered in the banner, to
tap.

### Translations

Corsu's lexicon has about 138,000 translation lines, each a source text and its Corsican translation. More than
18,000 are taken from other free software, most of them translated by Patriccollu di Santa Maria è Sichè (Firefox for
Android and iOS, Thunderbird for Android, VLC, Audacity, Notepad++, Poedit, WinMerge, Tenacity,
OpenTracks, wxWidgets, fre:ac, Inno Setup…). The rest were written for Corsu with the same vocabulary, more than
23,000 of them for Discord and Vencord; they are first versions that anyone can review and correct.
Does a translation look wrong?
[Open an issue](https://github.com/Platykalt/corsu/issues/new?template=translation.yml) or see
[CONTRIBUTING.md](CONTRIBUTING.md).

More: [all the documentation](docs/README.md), [what Corsu changes](docs/en/what-corsu-changes.md),
[development](docs/en/developers.md), [security](SECURITY.md), [CHANGELOG.md](CHANGELOG.md).

---

Corsu est un logiciel libre sous [licence GNU GPL](LICENSE), version 3 ou ultérieure · Corsu is free software under the
[GNU GPL](LICENSE), version 3 or later. Les traductions reprises d'autres projets gardent leur licence, indiquée dans
[lexicon/](lexicon/) · Translations taken from other projects keep their own license, given in [lexicon/](lexicon/).
