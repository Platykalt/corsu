# Texts left untranslated: where they come from (October 2026)

Inventory of texts reported in French or English in a Corsican session, and of a bounded search along the same paths
of the existing integrations (menus, closing, notification area, settings, dialogs). For each one: where it is
shown, where its text comes from, what translates it, why it was not translated, and what was done. "Observed" means
seen in the real program (in a container, throwaway home, see "How this was checked"); "simulated" means a test of
Corsu's code on an excerpt or a page made for the test.

## Reported

| Text | Shown in | Source of the text | Translated by | Why it was not | Status |
| --- | --- | --- | --- | --- | --- |
| "Display Configuration" (English) | KDE: KRunner and the launcher's search (`kcm_kscreen.desktop`), Shortcuts settings (`kglobalaccel/org.kde.kscreen.desktop`) | desktop entries `Name=` | Corsu's copies of desktop entries with `Name[co]` (`corsu.desktop_entries`) | KDE reads one language from desktop entries (KConfig with `LANGUAGE=co:fr`: `[co]`, else the untranslated English, never `[fr]`; checked with `kreadconfig6`). The lexicon only had System Settings' French "Configuration des affichages", not "Display Configuration" / "Configuration de l'affichage"; the Shortcuts folder was never read | **Fixed** (`6a7db20`): rows in the KDE section, `kglobalaccel` folder handled, French as the `[co]` fallback inside files Corsu writes. Unit tests with the real KConfig (`tests/test_desktop_entries.py`) |
| "Display Configuration" (English) | KDE System Settings: sidebar, module search, descriptions | the module's metadata compiled into the plugin (`kcm_kscreen.so`, `Name[fr]`…) | KDE (KPluginMetaData) | KPluginMetaData uses only the first language: with `LANGUAGE=co:fr` it shows English, with `LANGUAGE=fr` French (`kcmshell6 --list`, KDE Frameworks 6 of the maintainer's Plasma 6.7.5) | **Remaining**: Corsu cannot write into compiled plugins. Needs Corsican upstream or a KDE fallback along `LANGUAGE` |
| "Fermer Discord" (French) | not established | not found | | Searched without finding it: Discord's French messages (public web client, October 2026: 22 962 messages, including the tray menu), Discord's desktop app (`core.asar` 1.0.162, English only), the French gettext and Qt catalogs installed with Plasma 6.7.5 (only "Fermer %1" in `plasmawindowed`), Electron's `locales/fr.pak` in Discord (resource 12826 "Close $1" → "Fermer $1", Chromium's caption buttons; Discord's window is frameless and draws its own close button, whose `aria-label` "Fermer" the page translator already gives as "Chjode") | **Not reproduced**. The nearest French text found outside the page is the tray menu's "Quitter Discord" (next row). Needs where it was seen (menu, button, notification) |
| "Quitter Discord", "Ouvrir Discord", "Rendre muet"… (French) | Discord (desktop app, Linux and Windows): menu of the notification-area icon; on Windows, its first-close balloon | Discord's page (`setSystemTrayStrings` of its NativeUtils module), from its French messages | nothing: drawn by the desktop app (Electron, D-Bus menu on Linux), outside the page the plugin translates | the plugin only translated the page's DOM | **Fixed** (`6de0756`): the plugin patches `setSystemTrayStrings` and translates the strings on their way out (product name kept: Discord, Discord PTB). **Observed**: real Discord 1.0.162 (public download, never logged in) with the built plugin in KDE Plasma 6 on Xvfb: the patched module, called with the French strings Discord sends after login, gives the menu "Apre Discord, Circà l'aghjurnamenti…, Ringraziamenti, Esce da Discord" read over D-Bus and drawn by Plasma (screenshot). Not observed: Discord's own call after a login |

## Bounded search: same paths

| Place | Source | Status |
| --- | --- | --- |
| Discord, tray menu before login (or before the page sends its strings): "Open Discord", "Check for Updates...", "Acknowledgements", "Quit Discord" | the desktop app's own defaults (`core.asar`, main process) | **Remaining**, observed: out of reach of a page plugin (Vencord's renderer); replaced by Corsican as soon as the page sends its strings |
| Discord on Windows: tooltips of the buttons under the taskbar preview during a call ("Ne plus rendre muet", "Mettre en sourdine", "Déconnecter") | the page (`setThumbarButtons`) | **Fixed** with the same patch; simulated only (`tests/e2e/check_discord_native.py`), no Windows observed |
| Discord: its window's minimise, maximise and close buttons (Linux, Windows) | the page (`aria-label` "Minimiser", "Maximiser", "Fermer") | Covered by the dictionary (Minimizà, Massimizà, Chjode); not observed in a real Discord window |
| Discord: application menu (File, Edit, View…, "Quit Discord", "Check for Updates") | the desktop app (main process), shown in the macOS menu bar | **Remaining** (English, main process); not observed (no macOS) |
| Discord settings, menus and dialogs with Fermer/Quitter/Réduire, notifications, Paramètres, menus, Annuler/Confirmer/OK… (691 labels of Discord's French messages, initial bundles of October 2026) | the page | All translated by the plugin's dictionary but two: "Durée minimale des notifications" (**fixed**, row added), "Non classé" (game rank "Unranked": **remaining**, the Corsican for a rank needs a speaker) |
| Vesktop: tray menu ("Open", "About", "Repair Vencord", "Reset Vesktop", "Restart", "Quit") and its window menu | Vesktop's main process, English only | **Remaining**: not reachable from the page plugin |
| KDE: names of actions and entries without any Corsican (124 desktop entries with a French name, none translated, on the Plasma 6.7.5 system measured) | desktop entries | **Remaining**, English shown: a copy written only for a French fallback would hide the system's later updates of these files. In files Corsu writes anyway, untranslated texts now fall back to French (44 texts on that system) |
| KDE: messages of programs and Plasma (gettext, Qt catalogs) | catalogs | Fall back to French by design (`LANGUAGE=co:fr`) where Corsu's catalog lacks a text |

## How this was checked

- Discord's messages: the public web client (`discord.com/app` and the French and English message chunks it loads),
  downloaded once; read for the tray strings and for the bounded search. No account, no session.
- Real Discord: `tests/manual/kde-observe/discord.sh` (Discord's public Linux download, Debian sid container, KDE
  Plasma 6 on Xvfb, throwaway home, never logged in, Vencord built from this branch with the plugin). The maintainer's
  Discord was only read (strings of `core.asar` and `locales/fr.pak`), never run or changed.
- KDE: KConfig through `kreadconfig6` and `kcmshell6 --list` with `HOME` set to an empty folder; Corsu's desktop entries
  computed for the installed `/usr/share/applications` and `/usr/share/kglobalaccel` in a throwaway home.
- Regressions of the page translator (names such as "Work", "Error", "Control", templates, nodes reused after
  navigation): `tests/e2e/check_discord_names.py`, `check_discord_content.py`, `check_discord_activity.py`,
  `check_discord_built.py` in Chrome for Testing 155 (simulated pages), all passing.
