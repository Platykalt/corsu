# Changelog

## 0.19.2 (2026-10-03)

- An open Discord or Vesktop keeps the Corsu copy it started with until it closes: new windows and style reloads no
  longer fail after an update made while it is running.
- The Corsu app no longer stops with "release.json not found" after an update it started itself.
- Every installation points all launchers and shortcuts at the current copy, so earlier copies can be deleted.

## 0.19.1 (2026-10-03)

- Fixed: after installing or updating only Discord, links and downloads opened from Discord did nothing. The
  installer deleted the earlier Corsu copy that the Firefox launcher still used; every launcher and shortcut Corsu
  wrote now keeps its copy.

## 0.19.0 (2026-10-02)

- Discord: about 3,300 more texts in Corsican, found by comparing every French message of Discord with the
  dictionary. They cover the pieces of sentences around bold text and links, such as "Membre(s) correspondant à"
  when typing @, and the settings pages (privacy, age groups, subscriptions, server setup, notifications).
- Discord: sentences Discord breaks over two lines ("Ce salon n'a pas encore de / message épinglé") are translated
  as a whole, and the line break goes back at the same place in the Corsican text.
- Discord: relative times are in Corsican ("il y a 5 minutes" becomes "5 minuti fà", "dans 3 jours" becomes
  "trà 3 ghjorni", "lundi dernier" becomes "luni scorsu").

## 0.18.0 (2026-10-02)

- Updates no longer fail after Discord updates itself: the installer finds the current Discord instead of a version
  folder Discord has deleted, and forgets the files that went with it.
- Original text on hover: a small bubble now appears at once over translated text in Discord and on Google, and the
  option can be switched in Vencord's settings inside Discord without restarting.
- Vencord's own settings pages and plugin descriptions, which only exist in English, are in Corsican (about 1,000
  texts), including Backup & Restore and Patch Helper.
- More reviewed translations by Patriccollu di Santa Maria è Sichè: VLC media player, HandBrake, Tenacity, OpenTracks
  and Firefox Focus for iOS (16,600 rows from other projects, up from 13,000). Imports keep the source's "…" and skip
  lone letters.
- Without Firefox, Corsu downloads Mozilla's French Firefox and checks it against Mozilla's published SHA-512.
- "Dettagliu", plural "dettagli", everywhere.

## 0.17.0 (2026-10-01)

- The Corsu app speaks Corsican, chosen by default; French and English stay available.
- Installing shows a progress bar that fills step by step, with the current step written under it.
- Log: everything Corsu prints goes to `logs/corsu.log` in its data folder, with the full details of any error, and
  error messages say where to find it. The About page opens the folder.
- Vesktop: without Discord or Vesktop, Corsu downloads Vesktop, checks its published SHA-256 and sets it up with the
  Corsu plugin.
- Discord: labels followed by a count without spaces ("Membres—3") are translated.
- "Detagli" instead of "detaglii" everywhere, and "ditagli" aligned on it.

## 0.16.0 (2026-10-01)

- Discord: the plugin now translates labels with a name or number inside ("Send a message in {channel}",
  "{count} unread messages", "Server tag: {tag}", "In a call ({name})"), labels made of several parts
  ("Unread messages, Server name"), and dates ("ghjovi 1 ottobre 2026 à 18:04"). Names themselves are never changed.
- Discord: about 4,900 more texts, read from all of Discord's French message files instead of only the ones the app
  had cached, including tooltips such as "Search or start a conversation".
- Discord: a hidden diagnostic option lists the texts still shown in French, to find what is missing.

## 0.15.0 (2026-10-01)

- Review page in the Corsu app: go through the translations written for Corsu (Discord and Google), shortest first,
  and mark each one correct or fix it. Corrections apply on this computer at the next start of Discord or Firefox,
  and can be sent to the project as a prefilled GitHub issue.
- Updates: the Corsu app shows when a newer release exists and installs it in one click, after checking the
  archive's SHA-256 checksum.
- Learn option: hovering a translated text in Discord or on Google shows the original text.

## 0.14.0 (2026-10-01)

- Discord: about 5,600 longer sentences in Corsican too (settings explanations, warnings, dialogs). 96% of Discord's
  plain text is now covered, labels and sentences together.
- The Discord plugin is lighter (8.2 MB instead of 9.3 MB): it carries short general labels plus every text written
  for Discord, instead of every label up to 60 characters.

## 0.13.0 (2026-10-01)

- Discord: about 8,500 more interface labels in Corsican. Discord's own French text was read from the app and
  translated for Corsu with a shared glossary (canale for a channel, servore, filu, mintuvata…). 96% of Discord's
  short labels are now covered, up from about a quarter.
- New `lexicon/lexicon-fixes.tsv`, read before the imported translations, for the few that are wrong in context:
  Forum, Share your screen, Disable and Off no longer show unrelated or adjective forms.

## 0.12.0 (2026-10-01)

- Firefox: Google pages load as fast as before. The Google module now carries only Google's own labels (11 KB instead
  of the whole 11 MB lexicon) and lives inside the Firefox copy, so it is ready in every tab, including after clicking
  Images, News or Short videos.
- Firefox: about 100 more Google labels in Corsican: date and type filters, tools, map and weather labels, translation
  tool buttons, error messages, "About N results" and ratings. Buttons inside the results, such as "Show more", are
  left alone so they keep working.
- Firefox and Discord: text is translated before it is drawn, so French no longer flashes for a moment.

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
