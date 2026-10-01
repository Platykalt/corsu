# Changelog

## 0.11.0 (2026-10-01)

- Discord: much more of the interface is translated: Friends, Shop, the settings menu, member list headings and other
  labels that the plugin skipped because they are not buttons. Any text that matches a lexicon entry as a whole is now
  translated, except in what people write: messages, names of people, servers, channels and roles, statuses, bios
  and embeds.
- The Corsu app has a new layout, closer to a settings window: a sidebar, grouped lists, no duplicated status labels,
  confirmation dialogs for installing and uninstalling, and the log folded under "Show details".
- Plainer names: "Corsu Setup" is now the Corsu app; parts are called Firefox, Chromium browsers (with the browsers
  found), Discord, Vesktop, Desktop, System translations and Terminal. The old "Corsu Setup" shortcut is replaced.
- The installer's plan for system translations is in French too.
- Updating deletes the copies of earlier Corsu versions, except one that Discord or Vesktop still loads.

## 0.10.0 (2026-10-01)

- Corsu Setup is now a window that opens in your browser, on Windows, macOS and Linux alike, with no extra library.
  It installs Corsu (showing what will change first), switches each part on and off, pauses the terminal, links to the
  guides and to Sapienzia, Astutu and LIV, and removes Corsu. The install scripts open it; `--text` keeps the terminal
  installer.
- Discord installed by Corsu now appears among the parts that can be switched on and off.
- Firefox: Google's AI Overview heading and warning, "Short videos" and similar labels are translated, including inside
  the results area. Links and page text are still never changed.
- Messages from Corsu itself are in French or English, following the computer.
- The repository has a security policy, a pull request template, a documentation index and screenshots.

## 0.9.2 (2026-10-01)

- Firefox: the copy always opens your usual profile, with your home page, extensions and settings, even when it is
  started as the default browser. Before, such a start could create a new, empty profile.
- Firefox: choosing Firefox Corsu as the default browser no longer creates a menu entry without an icon (the blank
  sheet in the taskbar); the choice now points at the Firefox Corsu entry.
- Firefox: the New Tab page that Firefox updates separately ("Search with Google or enter address"…) is translated.
- Copies made for older Firefox versions are removed when Firefox Corsu starts.

## 0.9.1 (2026-10-01)

- Firefox: on Google's pages, the buttons and menus that Google's own Corsican interface leaves in French or English
  ("Voir plus", "Search for Images", "Paramètres de recherche"…) are completed in Corsican. Search results are not
  changed, and no other website is touched.
- Safari added to the compatibility table: it cannot be translated, as it is part of macOS.

## 0.9.0 (2026-10-01)

- Corsican word prediction and spelling correction for the Keyman keyboard (Android, iPhone, and computers):
  `corsu-keyboard.kmp`, built from the 17,000 most used Corsican words in the lexicon and attached to each release.

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
