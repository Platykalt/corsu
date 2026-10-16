**Français** · [English](#english)

| Système | Fichier | Ensuite |
| --- | --- | --- |
| Windows 10 ou 11 | `corsu-windows.zip` | décompresser, double-cliquer sur `Install for Windows.cmd` |
| macOS | `corsu-macos.tar.gz` | double-cliquer sur `Install for macOS.command` |
| Linux | `corsu-linux.tar.gz` | lancer `./"Install for Linux.sh"` |

En une ligne : `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex` dans PowerShell sous
Windows, ou `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh` dans le Terminal sous
macOS et Linux. Les [guides](https://github.com/Platykalt/corsu/tree/main/docs/fr) expliquent chaque étape.
L'application Corsu s'ouvre alors dans sa propre fenêtre.

Chaque fichier a sa somme de contrôle `.sha256`. Les archives contiennent leur propre Python. Chaque archive a été
installée, utilisée après suppression du dossier extrait, mise à jour et désinstallée sur son système avant la
publication (tests automatiques ; personne n'a regardé les écrans).

### Nouveautés de la 0.22.0

- Minecraft: Java Edition 26.3 en corse (lanceur officiel, Prism Launcher, MultiMC). Textes écrits par IA, pas encore
  relus par un locuteur ni essayés en jeu avant cette version : signalez ce qui sonne faux.
- Logiciels qui ont déjà leur traduction corse, activée par leur propre réglage : VLC, 7-Zip, Notepad++ (vérifiés
  sur de vrais logiciels), WinMerge, SumatraPDF, FileZilla, HandBrake, VeraCrypt (expérimentaux).
- La fenêtre de Corsu montre l'état réel de chaque logiciel, avec la raison et la marche à suivre.
- Firefox garde son logo comme navigateur par défaut sous Linux ; raccourci Corsu avec son icône sous Windows.
- Une installation interrompue ne perd plus le moyen de revenir en arrière.

## English

| System | File | Then |
| --- | --- | --- |
| Windows 10 or 11 | `corsu-windows.zip` | extract it and double-click `Install for Windows.cmd` |
| macOS | `corsu-macos.tar.gz` | double-click `Install for macOS.command` |
| Linux | `corsu-linux.tar.gz` | run `./"Install for Linux.sh"` |

In one line: `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex` in PowerShell on
Windows, or `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh` in Terminal on
macOS and Linux. The [guides](https://github.com/Platykalt/corsu/tree/main/docs/en) explain each step.
The Corsu app then opens in its own window.

Each file has a `.sha256` checksum. The archives carry their own Python. Every archive was installed, used after
deleting the extracted folder, updated and uninstalled on its own system before publication (automated checks; no one
looked at the screens).

### New in 0.22.0

- Minecraft: Java Edition 26.3 in Corsican (official launcher, Prism Launcher, MultiMC). AI-written texts, not yet
  reviewed by a speaker nor tried in the game before this release: please report what sounds wrong.
- Programs that already have a Corsican translation, switched on through their own setting: VLC, 7-Zip, Notepad++
  (checked with the real programs), WinMerge, SumatraPDF, FileZilla, HandBrake, VeraCrypt (experimental).
- The Corsu window shows each program's real state, with the reason and the next step.
- Firefox keeps its logo as the default browser on Linux; the Corsu shortcut has its icon on Windows.
- An interrupted installation no longer loses the way back.

[CHANGELOG.md](https://github.com/Platykalt/corsu/blob/main/CHANGELOG.md)
