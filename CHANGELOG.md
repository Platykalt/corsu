# Changelog

## 0.7.0 (2026-10-01)

- About 18,700 new phrases for the applications people use on Linux: Krita, Kleopatra, Lutris, Transmission,
  Meld, Haruna, Solaar, pavucontrol and the rest of the KDE programs, plus GTK and GLib dialogs, PipeWire and
  NetworkManager.
- The README, the guides and the installer messages were rewritten in plainer language.
- The installer says in plain words what it will change before asking.
- CI now also tries the one-line installers against each published release.
- Simpler layout: `Install for Windows.cmd`, `Install for macOS.command` and `Install for Linux.sh` at the top,
  a guide per system in `docs/`, the one-line installers in `tools/`, the code in `src/`.
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
