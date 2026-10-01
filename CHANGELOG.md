# Changelog

## 0.8.1 (2026-10-01)

- Linux: Corsu patches every version of Discord found in `~/.config/discord`, including the one the launcher still
  starts before Discord switches to the newest.
- How to get Google, and its AI, in Corsican through the Google account language.

## 0.8.0 (2026-10-01)

- Corsu window (Corsu Setup): switch Firefox, the Chromium browsers, Discord, Vesktop, the desktop and the
  terminal on or off one by one; put the terminal back in French for an hour.
- Firefox and the Chromium browsers ask websites for Corsican first, then French. Google answers in Corsican.
- Discord: Corsu patches the newest version of Discord installed in `~/.config/discord`, and the plugin reminds
  you to set Discord to French or English.
- GTK programs and terminal commands now use the Corsican translations (system translations option).
- The installer speaks French on French systems. Enter installs everything; `a` ticks all, `n` ticks none.
- README in French with an English version. Documentation in French and English, with guides for computers and
  phones, Discord, a table of what works where, and why Corsu exists.
- About 32,000 more phrases for the desktop and the terminal: file types, keyboard layouts, units, Kate,
  GnuPG, and the commands of coreutils, bash, git, pacman, sudo and util-linux.

## 0.7.0 (2026-10-01)

- About 18,700 new phrases for the applications people use on Linux: Krita, Kleopatra, Lutris, Transmission,
  Meld, Haruna, Solaar, pavucontrol and the rest of the KDE programs, plus GTK and GLib dialogs, PipeWire and
  NetworkManager.
- The README, the guides and the installer messages were rewritten in plainer language.
- The installer says in plain words what it will change before asking.
- CI now also tries the one-line installers against each published release.
- Simpler layout: the installers (`Install for Windows.cmd`, `Install for macOS.command`, `Install for Linux.sh`)
  sit at the top of each download, a guide per system is in `docs/`, the code is in `src/`.
- On macOS the installer can be opened by double-clicking.

## 0.6.0 (2026-10-01)

- Corsican punctuation now follows the reviewed translations: a space before `:`, `?`, `!` and `;`.
- Reviewed Corsican translations from Firefox for iOS, Mozilla VPN, Thunderbird for Android, VLC for Android,
  Audacity, Poedit, WinMerge and Notepad++ (about 13,000 rows, most by Patriccollu di Santa Maria è Sichè),
  imported by `tools/import_translations.py` and loaded before the drafts.
- About 14,000 new draft rows for the KDE Plasma desktop, Dolphin, Konsole, KWin and System Settings.
- One-line installers: `get.sh` (Linux, macOS) and `get.ps1` (Windows).
- Release archives now have fixed names (`corsu-windows.zip`, `corsu-macos.tar.gz`, `corsu-linux.tar.gz`), so the
  download links in the README always point to the latest version.
- Files reorganised into `src/`, `lexicon/`, `tests/`, `tools/` and `docs/`. Shortcuts are now named
  "Firefox Corsu" and "Corsu Setup".
- The installer stops cleanly when it gets no answer instead of failing.

## 0.5.0 (2026-10-01)

- Chrome, Chromium, Opera, Opera GX, Edge, Brave and Vivaldi on Windows and Linux.
- Mozilla's Corsican translations of Firefox for Android loaded first, and draft rows aligned with their
  vocabulary.
- About 16,600 new rows for Chrome, Opera and Opera GX.
- Chrome for Testing checks in CI on Windows and Linux.

## 0.4.0 (2026-10-01)

- Windows and macOS support for Firefox, Discord and Vesktop.
- "Select what you want to translate" menu and a Corsu Setup shortcut.
- Firefox uses Mozilla's French language pack for the exact installed version, `.properties` files included.
- About 14,000 new rows for Firefox pages and Qt dialogs.
- End-to-end checks on Linux, Windows and macOS before every release.
