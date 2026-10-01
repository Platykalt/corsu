# Corsu

Corsu met en corse les menus et les réglages de Firefox, Chrome, Opera GX et Discord, ainsi que le bureau KDE Plasma
et les commandes du terminal sous Linux. Il fonctionne sous Windows, macOS et Linux, et chaque partie peut être
désactivée puis réactivée à tout moment.

[English](README.en.md) · [Pourquoi Corsu](docs/fr/pourquoi-corsu.md) · [Ce qui marche, et où](docs/fr/compatibilite.md)

## Installer sur un ordinateur

| Système | Téléchargement | Ensuite | Guide |
| --- | --- | --- | --- |
| Windows | [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip) | décompresser, double-cliquer sur `Install for Windows.cmd` | [Windows](docs/fr/ordinateur/windows.md) |
| macOS | [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz) | double-cliquer sur `Install for macOS.command` | [macOS](docs/fr/ordinateur/macos.md) |
| Linux | [corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz) | lancer `./"Install for Linux.sh"` | [Linux](docs/fr/ordinateur/linux.md) |

Ou en une ligne. Dans PowerShell, sous Windows :

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
```

Dans le Terminal, sous macOS ou Linux :

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

L'installeur affiche ce qu'il a trouvé, tout est coché d'avance : Entrée installe tout. Il dit ce qu'il va changer
avant de le faire, et garde une copie de chaque fichier modifié. Le raccourci Corsu Setup permet ensuite d'ajouter
un logiciel, de mettre une partie en pause ou de tout retirer.

Pour Discord, réglez sa langue sur Français ou English : voir [Discord en corse](docs/fr/discord.md).

## Sur un téléphone

Les menus d'Android et d'iOS ne peuvent pas être traduits par un projet extérieur, mais Firefox, Thunderbird, VLC et
d'autres applications existent déjà en corse, et Gboard a un clavier corse. Voir [Android](docs/fr/telephone/android.md)
et [iPhone](docs/fr/telephone/iphone.md).

## Les traductions

Corsu compte environ 77 000 phrases traduites. Plus de 13 000 viennent d'autres logiciels libres, traduits pour la
plupart par Patriccollu di Santa Maria è Sichè : Firefox pour Android et iOS, Thunderbird, VLC, Audacity, Notepad++,
entre autres. Les autres ont été écrites pour Corsu en suivant le même vocabulaire.

Une traduction vous paraît fausse ou maladroite ? [Ouvrez un ticket](https://github.com/Platykalt/corsu/issues/new?template=translation.yml)
avec le texte et l'endroit où vous l'avez vu, ou corrigez la ligne vous-même : voir [CONTRIBUTING.md](CONTRIBUTING.md).

Pour pratiquer le corse avec quelqu'un, ou progresser seul : [Sapienzia](https://www.sapienzia.io),
[Astutu](https://astutu.corsica), [LIV](https://liv.corsica).

## Pour aller plus loin

- [Pourquoi Corsu](docs/fr/pourquoi-corsu.md)
- [Ce que Corsu modifie](docs/fr/ce-que-corsu-modifie.md)
- [Ce qui marche, et où](docs/fr/compatibilite.md)
- [Développement](docs/fr/developpeurs.md) et [CHANGELOG.md](CHANGELOG.md)

Corsu est un logiciel libre, publié sous [licence GNU GPL](LICENSE), version 3 ou ultérieure. Les traductions reprises
d'autres projets gardent leur licence, indiquée en tête de chaque fichier de [lexicon/](lexicon/).
