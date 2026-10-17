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

### Nouveautés de la 0.23.0

<!-- corsu:minecraft-summary:start -->
- **Minecraft Java en corse pour 87 versions** (versions stables 1.6.1 → 26.3). Traduction complète des fichiers de langue pour les versions listées ; vérifications techniques avec le code de chaque version. ([versions et vérifications](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) Cette version de Corsu contient ces packs : fermez Minecraft, puis l'application trouve la version de chaque dossier de jeu (lanceur officiel, Prism Launcher, MultiMC), y ajoute le pack de cette version et choisit le corse. Limites : textes écrits par IA ; deuxième passe IA sur un échantillon de 150 entrées des 3 978 textes anciens (pas sur tous) ; relecture par un locuteur : 0 ; seule la 26.3 a été lancée avec le pack, sur l'instance Prism Launcher du mainteneur (2026-10-16) : le journal du jeu montre le pack chargé et des messages en corse. Aucune vérification visuelle clé par clé n'est enregistrée : c'est pourquoi [STATUS.md](https://github.com/Platykalt/corsu/blob/main/minecraft/java/STATUS.md) compte « vu en jeu : 0 ». Les autres versions n'ont pas été lancées. Les vérifications automatiques ne sont ni une relecture par un locuteur ni un contrôle visuel de chaque écran. Pas les snapshots, pré-versions, Bedrock ni les versions avant 1.6.1.
<!-- corsu:minecraft-summary:end -->

- Mise à jour depuis l'application (À propos) : version installée, dernière version stable, vérification au démarrage,
  « Mettre à jour », installation automatique facultative (désactivée par défaut). Relancer l'installeur ou la commande
  en une ligne met à jour ou répare l'installation existante, avec les mêmes choix (une partie désactivée reste
  désactivée) ; une version plus ancienne est refusée ; une seule opération Corsu à la fois.
- Le téléchargement vise la version exacte annoncée, vérifie sa somme SHA-256 et sa version, s'extrait sans pouvoir
  sortir de son dossier ; la nouvelle copie est complète avant de remplacer l'ancienne, qui reste en secours.
- Discord : les pseudonymes, noms d'affichage et surnoms ne sont plus traduits (« Work », « Error » restaient
  traduits en « Travagliu », « Sbagliu ») ; seuls les textes de l'interface autour d'eux le sont.
- Minecraft : le pack corse est actif dès le premier démarrage ; les nouvelles instances en attente sont signalées.
- Corrigé depuis la 0.22.0 : copie installée sans les fichiers Minecraft, plantage d'une seconde activation VLC
  Flatpak.

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

### New in 0.23.0

<!-- corsu:minecraft-summary:start -->
- **Minecraft: Java Edition in Corsican for 87 versions** (releases 1.6.1 → 26.3). Complete translation of the language files for the listed versions; technical checks with each version's own code. ([versions and checks](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) This Corsu release contains these packs: close Minecraft, then the app finds the version of each game folder (official launcher, Prism Launcher, MultiMC), adds that version's pack and picks Corsican. Limits: texts written by AI; second AI pass on a sample of 150 entries of the 3,978 older texts (not on all of them); review by a Corsican speaker: 0; only 26.3 has been started with the pack, on the maintainer's Prism Launcher instance (2026-10-16): the game's log shows the pack loaded and messages in Corsican. No per-key visual check has been recorded, which is why [STATUS.md](https://github.com/Platykalt/corsu/blob/main/minecraft/java/STATUS.md) counts "seen in game: 0". The other versions have not been started. The automated checks are neither a speaker's review nor a visual check of every screen. No snapshots, pre-releases, Bedrock or versions before 1.6.1.
<!-- corsu:minecraft-summary:end -->

- Updating from the app (About): installed version, latest stable version, a check when it opens, "Update", optional
  automatic installation (off by default). Running the installer or the one-line command again updates or repairs the
  existing installation with the same choices (a part switched off stays off); an older version is refused; only one
  Corsu task runs at a time.
- The download targets the exact version announced, checks its SHA-256 and version, and extracts without being able to
  leave its folder; the new copy is complete before it replaces the old one, which stays as a fallback.
- Discord: user names, display names and nicknames are no longer translated ("Work" and "Error" showed as "Travagliu"
  and "Sbagliu"); only the interface text around them is.
- Minecraft: the Corsican pack is active from the first start; new instances waiting for activation are shown.
- Fixed since 0.22.0: installed copy without the Minecraft files, crash of a second VLC Flatpak activation.

[CHANGELOG.md](https://github.com/Platykalt/corsu/blob/main/CHANGELOG.md)
