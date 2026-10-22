# Where the Corsican of `co.json` comes from

Catalogue: Noctalia 5.3.0 `assets/translations/en.json` (3,126 strings, MIT licence; French context from `fr.json`,
which has 2,144 of them). State on 22 October 2026. **No string has been read by a Corsican speaker yet.**

## Coverage

3,126 of 3,126 keys have a value (100 %); 102 of them are deliberately identical to the English (see below). Every
value keeps the English placeholders (`{count}`, `{name}`…), markup (`<source>`, `<name>`), line breaks and `%s`
(checked by `tests/test_noctalia_translation.py`).

## How the strings were made

1. Every English string was matched exactly against Corsu's lexicon files (English, and French of the same key), with
   file and line kept as a candidate. No dictionary, INFCOR or BDLC page was consulted, by script or by hand, and no
   online service was used.
2. Eight AI agents (Claude Opus 5.5) each translated one part of the catalogue from the English, with the French as
   context, a shared glossary (below) and the candidates; they were told to reuse a candidate only when its sense fits
   the place the key shows it (key path: label, description, button, state…). A ninth pass (same model) unified the
   terms that diverged between parts (toast, drawer, popup, pill, greeter, legacy, identifier, Move), Italian-looking
   forms (*giò* → *ghjò*) and the space before `;` `:` `?` `!` (CONTRIBUTING rule 5).
3. The class of each value was then measured by comparing it with the candidates: equal to a row of
   `lexicon-upstream.tsv` or `lexicon-mozilla.tsv` (translations published by Corsican translators of other free
   software) → "published"; equal to a row of `lexicon.tsv` or `lexicon-fixes.tsv` → "Corsu usage" (not an independent
   attestation: Corsu's lexicon was itself written with AI help, see `lexicon/PROVENANCE.md`); otherwise "AI
   proposal". "Published" says that the same wording exists in that program for the same English (or French) text;
   the choice to reuse it here is still an AI judgement.

| Section | Strings | Published | Corsu usage | AI proposal | Same as English |
| --- | ---: | ---: | ---: | ---: | ---: |
| `auth` | 19 | 1 | 1 | 17 | 0 |
| `bar` | 125 | 20 | 27 | 66 | 12 |
| `clipboard` | 22 | 1 | 1 | 20 | 0 |
| `common` | 8 | 5 | 1 | 2 | 0 |
| `control-center` | 236 | 35 | 30 | 159 | 12 |
| `desktop-widgets` | 154 | 48 | 18 | 83 | 5 |
| `dock` | 3 | 1 | 1 | 1 | 0 |
| `internal-apps` | 1 | 1 | 0 | 0 | 0 |
| `launcher` | 71 | 13 | 23 | 29 | 6 |
| `location` | 8 | 3 | 0 | 5 | 0 |
| `lockscreen` | 8 | 0 | 2 | 6 | 0 |
| `notifications` | 74 | 5 | 2 | 64 | 3 |
| `osd` | 26 | 1 | 5 | 20 | 0 |
| `plugins` | 7 | 0 | 0 | 7 | 0 |
| `power` | 17 | 1 | 6 | 10 | 0 |
| `session` | 9 | 3 | 3 | 3 | 0 |
| `settings.actions` | 2 | 0 | 1 | 1 | 0 |
| `settings.badges` | 7 | 1 | 4 | 2 | 0 |
| `settings.calendar-accounts` | 37 | 4 | 1 | 28 | 4 |
| `settings.controls` | 7 | 2 | 0 | 5 | 0 |
| `settings.dialogs` | 1 | 1 | 0 | 0 | 0 |
| `settings.entities` | 118 | 24 | 12 | 82 | 0 |
| `settings.errors` | 23 | 0 | 0 | 23 | 0 |
| `settings.export-config` | 8 | 1 | 0 | 7 | 0 |
| `settings.idle` | 21 | 5 | 1 | 12 | 3 |
| `settings.navigation` | 104 | 36 | 26 | 34 | 8 |
| `settings.notifications` | 23 | 1 | 2 | 19 | 1 |
| `settings.options` | 120 | 37 | 19 | 56 | 8 |
| `settings.palette-inspector` | 13 | 1 | 1 | 10 | 1 |
| `settings.plugins` | 87 | 7 | 4 | 72 | 4 |
| `settings.schema` | 910 | 54 | 31 | 811 | 14 |
| `settings.session-actions` | 20 | 6 | 3 | 11 | 0 |
| `settings.storage-recovery` | 7 | 0 | 0 | 7 | 0 |
| `settings.templates` | 14 | 1 | 1 | 12 | 0 |
| `settings.widgets` | 666 | 41 | 22 | 594 | 9 |
| `settings.window` | 27 | 3 | 0 | 24 | 0 |
| `setup-wizard` | 11 | 3 | 1 | 7 | 0 |
| `system` | 4 | 1 | 0 | 3 | 0 |
| `theme` | 10 | 1 | 0 | 4 | 5 |
| `time` | 24 | 0 | 1 | 18 | 5 |
| `tray` | 3 | 2 | 0 | 1 | 0 |
| `ui` | 23 | 11 | 2 | 8 | 2 |
| `wallpaper` | 19 | 0 | 2 | 17 | 0 |
| `weather` | 24 | 1 | 12 | 11 | 0 |
| `window-switcher` | 5 | 0 | 1 | 4 | 0 |
| **total** | **3126** | **382** | **267** | **2375** | **102** |

Reused rows by origin:

| Strings | Class | File | Section of the file |
| ---: | --- | --- | --- |
| 101 | Corsu usage | `lexicon.tsv` | Current Firefox, Discord and Plasma spelling variants |
| 82 | published translation | `lexicon-upstream.tsv` | VLC for Android (GPL-2.0-or-later) |
| 81 | published translation | `lexicon-upstream.tsv` | Audacity (GPL-2.0-or-later) |
| 57 | published translation | `lexicon-upstream.tsv` | Thunderbird for Android (Apache-2.0) |
| 51 | published translation | `lexicon-upstream.tsv` | VLC media player (GPL-2.0-or-later) |
| 43 | Corsu usage | `lexicon.tsv` | KDE Plasma desktop, Dolphin, Konsole, KWin, System Settings: drafts aligned wi |
| 33 | published translation | `lexicon-mozilla.tsv` | Firefox for Android, Focus and Android Components (MPL-2.0) |
| 27 | Corsu usage | `lexicon.tsv` | Qt and KDE framework dialogs, Firefox chrome, common status labels (0.3.0) |
| 24 | Corsu usage | `lexicon.tsv` | Chrome, Chromium and Opera interface — draft translations aligned with Mozilla |
| 20 | published translation | `lexicon-upstream.tsv` | WinMerge (GPL-2.0-or-later) |
| 20 | published translation | `lexicon-upstream.tsv` | OpenTracks (Apache-2.0) |
| 20 | Corsu usage | `lexicon.tsv` | wording Corsu already uses beside it ("Circà cù %1", "Circà cù %S in una fines |
| 17 | Corsu usage | `lexicon.tsv` | Discord: labels of the Discord app, translated for Corsu from Discord's French |
| 16 | Corsu usage | `lexicon.tsv` | Installed applications (Krita, Kleopatra, Lutris, Transmission, Meld...) and G |
| 11 | published translation | `lexicon-mozilla.tsv` | Firefox for iOS (MPL-2.0) |
| 10 | published translation | `lexicon-upstream.tsv` | wxWidgets (wxWindows-exception-3.1) |
| 8 | Corsu usage | `lexicon.tsv` | Firefox interface, error pages and Qt dialogs — draft translations, review wel |
| 6 | published translation | `lexicon-upstream.tsv` | Notepad++ (GPL-3.0-or-later) |
| 6 | published translation | `lexicon-upstream.tsv` | fre:ac (GPL-2.0-or-later) |
| 5 | published translation | `lexicon-upstream.tsv` | Poedit (MIT) |
| 5 | Corsu usage | `lexicon.tsv` | File types, keyboard layouts, units, Kate, GnuPG, terminal commands (coreutils |
| 3 | Corsu usage | `lexicon.tsv` | Google: labels of Google's own pages, always sent to Firefox's Google module w |
| 1 | Corsu usage | `lexicon.tsv` | Opera GX interface — draft translations aligned with Mozilla co terminology, r |
| 1 | Corsu usage | `lexicon.tsv` | Discord: rows not applied are in lexicon/review-discord-2026-10.tsv. |
| 1 | Corsu usage | `lexicon.tsv` | Vencord: settings pages and plugin descriptions of Vencord, which only exist i |

## Terms chosen (to review first)

Source letters: P = Corsu's Plasma rows (`lexicon.tsv`, first sections), M = Mozilla's Corsican, U = upstream
translators (Audacity, VLC…), A = AI choice made for this catalogue.

| English | Corsican | Why | Src |
| --- | --- | --- | --- |
| Settings | Parametri | same as Plasma, Firefox, all upstream rows | P M U |
| Launcher | lanciadore | Corsu's "Lanciadore d'appiecazioni" | P |
| Control Center | Centru di cuntrollu | no earlier row | A |
| Widget | elementu graficu | Corsu's Plasma "Elementi grafichi"; Mozilla keeps *widget* | P |
| Wallpaper | fondu di screnu | Corsu's Plasma row; Mozilla says *sfondulu di screnu* | P |
| Workspace | spaziu di travagliu | Corsu's Plasma row | P |
| Clipboard | preme’papei | Mozilla's spelling (with ’) | M |
| Brightness | luminosità | Corsu's Plasma row; Mozilla and VLC say *lucidezza*: a speaker should choose one for all of Corsu | P |
| Microphone | micrufonu | Corsu's Plasma row; Mozilla says *microfonu* | P |
| Plugin | estensione | upstream programs (Audacity, Poedit); Corsu's Discord rows say *moduli* | U |
| Template | mudellu | upstream | U |
| Log out / Shut down / Reboot / Suspend | Chjode a sessione / Spenghje / Rilancià / Mette in veghja | Corsu's Plasma rows | P |
| Lock screen | screnu di bluccatura | Corsu's row | P |
| Do Not Disturb | Ùn disturbà micca | Corsu's row | P |
| Weather | meteo | *tempu* (Corsu's earlier row) collides with time; gender of *meteo* varies between strings (u/a) and needs a decision | A |
| Night light | lume di notte | no earlier row | A |
| Power profile | prufilu energeticu | no earlier row | A |
| System tray | zona di nutificazione | from the French *zone de notification* | A |
| Taskbar | barra di l'appiecazioni | describes what Noctalia's taskbar shows | A |
| Palette | tavuletta di culori | no earlier row | A |
| Toast (short-lived notification) | nutificazione passaghjera | no earlier row | A |
| Popup | finestretta | no earlier row | A |
| Drawer | cassettu | no earlier row | A |
| Pill / Capsule (bar shapes) | pillula / capsula | *Pillula* exists in the lexicon (medicine sense) | A |
| Greeter (login screen) | screnu d'accolta | "Noctalia Greeter" kept as a name | A |
| Tooltip | bolla d'aiutu | no earlier row | A |
| Timeout | ritardu | no earlier row | A |
| Dock | dock | kept as the component's name, as French does | A |
| Caffeine | Caffeina | feature name; descriptions say *impedisce a veghja* | A |
| Bluetooth pairing | accuppià / accuppiamentu | no earlier row | A |
| Keyboard focus | fucalizazione / fucalizà | lexicon's *cuncentrazione* is the mental sense | A |

## Abbreviations written out

CPU Freq → frequency (*Frequenza CPU*); CPU/GPU Temp → temperature; Temperature Max/Min → maximum/minimum; Label Min
Width, Min/Max Length → minimum/maximum; "{count} hr ago", "{count} min ago" → hours, minutes (*{count} ore fà*,
*{count} minuti fà*); "Starts in {minutes} min" → minutes; Mic → microphone; DND → Do Not Disturb; Net Rx/Tx, Network
RX/TX → reception/emission of the network; Stat → statistic; App → application; UI/GUI → (graphical) interface;
MRU → most recently used; Regex → regular expression; hex → hexadecimal; Config → configuration; ID → identifier
(*identificatore*); e.g. → *per esempiu*; ms → milliseconds in descriptions. Kept: CPU, GPU, RAM, VRAM, OSD, DPMS,
UPower, IP, WAN, VPN, SSID, EAP/PEAP/MSCHAPv2, SIM, PIN, UV, DDC/CI, TTY, TOML, CalDAV, ICS, URL, kB/s, MB/s, px, %.
Compact units on narrow widgets stay as symbols: `{count}h`, `{count}m`, `<1m`, `{seconds} s`.

## Values identical to the English (102)

Proper names and products (Noctalia, Noctalia Greeter, Niri, Umbriel, Google, iCloud, CalDAV, Flatpak, AppImage, Nix,
Snap, Git, Polkit), technical acronyms and units (CPU, GPU, RAM, Swap, IP, VPN, OSD, Wi-Fi, Bluetooth, kB/s, MB/s, ID,
DDC/CI), key names (Alt, Ctrl, Shift, Super, Ctrl+V, Caps, Num, Scroll and their one-letter forms), Material colour
scheme names (M3 Tonal Spot…), example paths and commands in input hints (`~/Pictures/Wallpapers`, `notify-send …`,
`swappy -f -`), placeholder-only strings (`{first} {second}`), symbols (↑ ↓) and words already used as such in Corsican
(Media, Internet, Script, Shell, Dock, Emoji).

## Other texts shown in the Hyprland session (not in Noctalia's catalogue)

| Source | Mechanism | Corsican? |
| --- | --- | --- |
| Hyprland's own dialogs and notices (application not responding, permission request, safe mode, config errors), drawn by hyprland-guiutils | translations compiled into the Hyprland binary (hyprutils i18n): about forty locales, from `as_IN` to `zh_TW`, French included; language from the locale or `general.locale` | no, and none can be added without a new Hyprland build; Corsu's profile sets `general.locale = "fr_FR"` (`config/corsu/language.lua`) |
| xdg-desktop-portal-hyprland share picker (`hyprland-share-picker`, Qt Widgets) | calls `QCoreApplication::translate` but the 1.4.1 package ships no `.qm` file | English only |
| qt6ct (if installed for the session's Qt theme) | Qt `.qm` catalogues in the qt6ct package | not checked: qt6ct is not installed here |
| Polkit prompts | the dialog is Noctalia's (`auth.polkit.*`, translated); the action message comes from each program's polkit policy (`<message xml:lang>`) | only where that program ships Corsican |
| PAM messages on the lock screen | Linux-PAM gettext domain, following the session's `LANGUAGE` | French exists (`/usr/share/locale/fr/LC_MESSAGES/Linux-PAM.mo`), Corsican does not |
| Notification bodies, window titles, Wi-Fi names, media titles | runtime content of other programs | left as they are, by design |
