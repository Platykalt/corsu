# Corsu

Corsu traduit en corse les menus et les réglages de Firefox, Chrome, Opera GX et Discord. Sous Linux, il
traduit aussi le bureau KDE Plasma. Il fonctionne sous Windows, macOS et Linux, et on peut revenir au français
à tout moment.

[English version](README.md)

## Télécharger

| | |
| --- | --- |
| Windows | [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip) |
| macOS | [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz) |
| Linux | [corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz) |

Sous Windows, décompressez le fichier zip (clic droit, Extraire tout), ouvrez le dossier `corsu` et
double-cliquez sur `install.cmd`. Windows peut vous demander si vous voulez vraiment lancer un fichier
téléchargé. Si Python n'est pas installé, le script propose de l'installer.

Sous macOS et Linux, décompressez l'archive et lancez `./install.sh` depuis le dossier `corsu`.

On peut aussi tout faire en une ligne. Dans PowerShell, sous Windows :

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/get.ps1 | iex
```

Dans un terminal, sous macOS ou Linux :

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/get.sh | sh
```

## Utilisation

L'installeur affiche ce qu'il a trouvé sur l'ordinateur et vous laisse choisir :

```
Select what you want to translate:
  [x] 1. Firefox: menus, settings and error pages
  [x] 2. Chrome, Opera GX and other Chromium browsers
  [x] 3. Discord: interface through Vencord
Type numbers to toggle (e.g. "2 3"), Enter to continue, q to quit:
```

Il explique ensuite ce qu'il va modifier et attend votre accord. Fermez les logiciels avant de répondre, puis
rouvrez-les.

L'installeur ajoute un raccourci nommé Corsu Setup. Ouvrez-le plus tard pour ajouter un logiciel, revenir au
français ou retirer Corsu. Il garde une copie de chaque fichier qu'il modifie : le retirer remet l'ordinateur
dans l'état où il était.

Firefox et Discord marchent sur les trois systèmes. Chrome, Opera GX, Edge, Brave et Vivaldi marchent sous
Windows et Linux ; ils ne sont pas encore pris en charge sur macOS. [docs/components.md](docs/components.md)
détaille ce que Corsu change pour chaque logiciel.

Seul le logiciel est traduit, jamais les sites web ni les messages. Le texte qui n'a pas encore de traduction
corse reste en français.

## Les traductions

Corsu compte environ 77 000 phrases traduites. Près de 13 000 viennent d'autres logiciels libres, traduits pour
la plupart par Patriccollu di Santa Maria è Sichè : Firefox pour Android et iOS, Thunderbird, VLC, Audacity,
Notepad++, entre autres. Les autres ont été écrites pour Corsu en suivant son vocabulaire. Elles n'ont pas encore
toutes été relues par un locuteur.

Si vous voyez une traduction fausse ou maladroite, [ouvrez un ticket](https://github.com/Platykalt/corsu/issues/new?template=translation.yml)
avec le texte et l'endroit où vous l'avez vu. [CONTRIBUTING.md](CONTRIBUTING.md) explique comment corriger les
fichiers directement.

## Téléphones

Apple, Google et Samsung choisissent les langues de leurs téléphones, et le corse n'en fait pas encore partie.
Certaines applications sont pourtant déjà en corse, dont Firefox. [docs/phones.md](docs/phones.md) explique
comment s'en servir.

## Autres documents

[docs/development.md](docs/development.md) décrit le code, les tests et la publication d'une version.
[CHANGELOG.md](CHANGELOG.md) liste les changements de chaque version.

Corsu est un logiciel libre, publié sous [licence GNU GPL](LICENSE), version 3 ou ultérieure. Les traductions
reprises d'autres projets gardent leur licence, indiquée en tête de chaque fichier de [lexicon/](lexicon/).
