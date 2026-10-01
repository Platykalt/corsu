# Corsu

Corsu met en corse l'interface des logiciels de tous les jours : Firefox, Chrome et Opera GX, Discord, et le
bureau KDE Plasma. Il fonctionne sous Windows, macOS et Linux, et on peut le désactiver ou le désinstaller à tout
moment.

**Télécharger :**
[Windows](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip) ·
[macOS](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz) ·
[Linux](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz)

[Read in English](README.md)

## Installer sous Windows

1. Téléchargez [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip).
2. Faites un clic droit sur le fichier, choisissez *Extraire tout*, puis ouvrez le dossier `corsu`.
3. Double-cliquez sur `install.cmd`. Windows peut vous demander de confirmer l'ouverture d'un fichier téléchargé.
4. Choisissez ce que vous voulez traduire et acceptez la liste des changements.

Corsu a besoin de Python 3.10 ou plus récent. S'il manque, `install.cmd` propose de l'installer avec `winget`.

Vous pouvez aussi installer depuis PowerShell, en une ligne :

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/get.ps1 | iex
```

## Installer sous macOS ou Linux

Ouvrez un terminal et lancez :

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/get.sh | sh
```

La commande télécharge la dernière version, vérifie sa somme de contrôle SHA-256 et lance l'installeur. Vous
pouvez aussi télécharger l'archive de votre système, l'extraire et lancer `./install.sh` dans le dossier `corsu`.

## Ce que fait l'installeur

Il cherche les logiciels présents sur l'ordinateur et demande lesquels traduire :

```
Select what you want to translate:
  [x] 1. Firefox: menus, settings and error pages
  [x] 2. Chrome, Opera GX and other Chromium browsers
  [x] 3. Discord: interface through Vencord
Type numbers to toggle (e.g. "2 3"), Enter to continue, q to quit:
```

Avant de toucher à quoi que ce soit, il affiche ce qu'il va faire et attend votre accord. Il ajoute ensuite un
raccourci **Corsu Setup** (menu Démarrer, menu des applications, ou `~/Applications` sur macOS). Ouvrez-le plus
tard pour ajouter des logiciels, revenir au français ou tout désinstaller. L'archive téléchargée peut être
supprimée.

Fermez Firefox, Chrome et Discord avant l'installation, puis rouvrez-les. Sous Linux, déconnectez-vous et
reconnectez-vous pour le bureau Plasma.

## Ce qui est traduit

| Logiciel | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Firefox | oui | oui | oui |
| Chrome, Opera, Opera GX, Edge, Brave, Vivaldi | oui | pas encore | oui |
| Discord (avec Vencord) et Vesktop | oui | oui | oui |
| Bureau KDE Plasma et applications Qt | | | oui |

Seule l'interface est traduite : menus, boutons, paramètres, pages d'erreur. Les sites web, les messages et ce que
vous tapez ne changent pas. Corsu fonctionne hors ligne et ne lit jamais vos messages, profils ou documents. Un
libellé qui n'a pas encore de traduction corse reste en français.

[docs/components.md](docs/components.md) détaille ce que chaque partie modifie sur l'ordinateur.

## Les traductions

Le lexique de Corsu compte environ 50 000 entrées. Plus de 12 000 sont des traductions relues, faites pour la
plupart par Patriccollu di Santa Maria è Sichè pour Firefox, Thunderbird, VLC, Audacity, Notepad++ et d'autres
logiciels libres ([lexicon/](lexicon/)). Le reste est un brouillon qui suit le même vocabulaire et doit encore
être relu par des locuteurs.

Si vous voyez une erreur, ouvrez un ticket ou corrigez la ligne vous-même : voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Téléphones

Apple, Google et Samsung ne laissent pas un projet extérieur traduire leur système, mais plusieurs applications
parlent déjà corse. [docs/phones.md](docs/phones.md) explique comment les utiliser sur iPhone ou Android.

## Désactiver ou désinstaller

Ouvrez **Corsu Setup**, ou lancez l'une de ces commandes depuis le dossier `corsu` (`py -3` au lieu de `python3`
sous Windows) :

```sh
python3 src/installer.py --disable     # retour au français, tout reste prêt pour réactiver
python3 src/installer.py --enable
python3 src/installer.py --uninstall   # remet les fichiers et réglages d'origine
```

Corsu garde une copie de chaque fichier qu'il modifie. Les fichiers que vous modifiez ensuite vous-même ne sont
pas touchés.

## Pour aller plus loin

- [docs/components.md](docs/components.md) : ce que modifie chaque composant, et où
- [docs/phones.md](docs/phones.md) : le corse sur iPhone et Android
- [docs/development.md](docs/development.md) : organisation du projet, tests, publication d'une version
- [CHANGELOG.md](CHANGELOG.md)

Corsu est un logiciel libre sous [GNU GPL v3](LICENSE) ou ultérieure. Les traductions reprises d'autres projets
gardent leur licence d'origine, indiquée dans chaque fichier de [lexicon/](lexicon/).
