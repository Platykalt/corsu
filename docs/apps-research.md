# Programs translated into Corsican: how Corsu can switch them on

Research note, consulted **2026-10-16**. Source inventory: Patriccollu di Santa Maria è Sichè's
[Lingua_Corsa-Infurmatica README](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica#readme) (branch `ceppu`,
last README commit 2026-03-15 `2ff6e25`; byte-identical to the local copy in
`~/.local/share/corsu/resources/patriccollu/Lingua_Corsa-Infurmatica.zip`) and its `Prughjetti/*/Traduzzione.md`
notes. Machine-readable summary: [`src/apps/catalog.json`](../src/apps/catalog.json).

Method: release packages were downloaded and listed (`7z l`), catalogs were run through `msgfmt --statistics`, and
the code that reads each language setting was read at the tag of the current release. "(?)" marks anything not
checked against source code or a real package.

## 1. Ground rules for an installer that runs as the user

- **Only per-user settings.** Corsu runs without admin rights, so it can't write into `Program Files`, `/usr` or
  `/Applications`. Every mechanism below is a per-user registry value, a config file in the profile, a `defaults`
  domain or an environment override. Adding a missing catalog to an install folder (MozBackup, WinCDEmu, older
  VeraCrypt) is a manual, admin-only step and is out of scope.
- **Don't ship the catalogs.** Every program in the priority list already contains its Corsican catalog. Corsu
  should check that the catalog is there (detection paths below) and only flip the setting. If a catalog ever has to
  be supplied (a backport), fetch it from a pinned upstream commit URL and check its SHA-256. Don't bundle it:
  licences differ (GPL, AGPL, MIT, proprietary), and a bundled copy goes stale with every upstream release.
- **Close the program first** when it rewrites its configuration on exit (marked `must_close`). Otherwise the
  program saves its in-memory value over Corsu's edit.
- **Libraries and installer frameworks don't translate apps.** wxWidgets (`co.po` → `wxstd.mo`), Lazarus LCL
  (`lclstrconsts.co.po`), Inno Setup (`Files/Languages/Corsican.isl`) and NSIS (`Corsican.nlf/.nsh`) only translate
  stock dialogs, or the setup wizard itself. That only happens when the application or setup ships and loads the
  `co` file. Example: Arch's `wxwidgets-common` installs `/usr/share/locale/co/LC_MESSAGES/wxstd-3.2.mo`, but a wx
  app still shows its own strings in another language unless it has its own `co` catalog.
- **Linux environment.** gettext programs without their own setting (VLC, GTK apps) follow
  `LANGUAGE=co:fr` (not Poedit: wxWidgets reads `LANG` first, §3.9). gettext ignores `LANGUAGE` when the locale
  is `C`/`POSIX`, so `LANG` must be a real locale.
  Per-app options are a copied `.desktop` file in `~/.local/share/applications` with `Exec=env LANGUAGE=co:fr …`,
  or for Flatpak `flatpak override --user --env=LANGUAGE=co:fr <app-id>`, which writes
  `~/.local/share/flatpak/overrides/<app-id>`.
- **Flatpak locale subsets.** Translations go into a separate `.Locale` extension. That extension only holds the
  languages configured with `flatpak config` (`languages`, `extra-languages`), so Corsican catalogs may be absent
  even when upstream ships them. Fix: `flatpak config --user --set extra-languages co`, then `flatpak update`
  ([flatpak-config](https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-config)). Corsu's
  `src/apps/vlc.py` already reports this case.
- **macOS.** Cocoa apps that ship `co.lproj` follow the per-app `AppleLanguages` default
  (`defaults write <bundle-id> AppleLanguages -array co fr en`). For sandboxed apps the domain lives in
  `~/Library/Containers/<bundle-id>/Data/Library/Preferences/` (?). Apps with their own gettext layer (VLC) ignore
  `AppleLanguages` and use their own key.

## 2. Classification of every project in the inventory

Status columns follow the README's three parts: ✨ translated and usable, ⏳ awaiting distribution, 🎯 being translated.

| Project | Status | Kind | Platforms | Notes |
| --- | --- | --- | --- | --- |
| 7-Zip | ✨ | desktop app | Windows (Linux/macOS builds are console only) | §3.5 |
| Audacity | ✨ | desktop app | Win/mac/Linux | §3.2 |
| CCleaner | ✨ | desktop app (proprietary) | Windows | Corsican not maintained since April 2023 (Gen Digital); still present in v6.14 |
| CDex | ✨ | desktop app | Windows | not researched |
| Colors, Hasher, RandPass, ReNamer, Resizer, Shutter (den4b) | ✨ | desktop apps (freeware) | Windows | not researched |
| FileZilla | ✨ | desktop app | Win/mac/Linux | §3.8 |
| libfilezilla | ✨ | library | – | used by FileZilla |
| Firefox for Android, Focus for Android | ✨ | mobile app | Android | §4 |
| Firefox for iOS, Focus for iOS | ✨ | mobile app | iOS | §4 |
| fre:ac | ✨ | desktop app | Win/mac/Linux | §3.11 |
| GeneWeb | ✨ | web application (local server) | Win/mac/Linux | language per URL (`lang=co`); nothing to configure |
| HandBrake | ✨ | desktop app | Win/mac/Linux | §3.10 |
| Inno Setup | ✨ | installer framework | Windows | official `Corsican.isl` |
| K-9 Mail → Thunderbird for Android | ✨ | mobile app | Android | §4 |
| Lazarus / LCL | ✨ | library | – | `lcl/languages/lclstrconsts.co.po` |
| Lufi, PrivateBin, Worldle, PDFCreator Online | ✨ | website / web service | browser | follow browser language or site URL; Worldle dropped Corsican (Nov 2022) |
| Mozilla VPN | ✨ | desktop + mobile client (paid) | all | not researched |
| Mp3tag | ✨ | desktop app (proprietary) | Windows (Mac version paid) | §3.14 |
| NoNonsense Notes, OpenTracks, OSM Dashboard | ✨ | mobile app | Android | §4 |
| Notepad++ | ✨ | desktop app | Windows | §3.4 |
| NSIS | ✨ | installer framework | Windows | official `Corsican.nlf/.nsh` |
| OmegaT | ✨ | desktop app (Java) + website | Win/mac/Linux | mechanism not researched |
| Paint.NET | ✨ | desktop app (proprietary) | Windows | §3.15 |
| PDFCreator (+ HotFolder, Images2PDF) | ✨ | desktop app | Windows | not researched |
| PDFsam Basic | ✨ | desktop app (Java) | Win/mac/Linux | §3.13 |
| Poedit (+ WinSparkle) | ✨ | desktop app (+ updater library) | Win/mac/Linux | §3.9 |
| SumatraPDF | ✨ | desktop app | Windows | §3.6 |
| Tenacity | ✨ | desktop app | Win/mac/Linux | §3.3 |
| VeraCrypt | ✨ | desktop app | Win/mac/Linux | §3.12 |
| Video DownloadHelper | ✨ | browser extension + companion app | browsers | follows the browser UI language; v9's new UI ignores `co` |
| VirtualMIDISynth | ✨ | desktop driver/app | Windows | `lang\1155.lang` (1155 = Corsican LCID) since 2.11.1 |
| VLC for Android, VLC for iOS | ✨ | mobile app | Android / iOS | §4 |
| WinMerge (+ website) | ✨ | desktop app | Windows | §3.7 |
| wxWidgets | ✨ | library | – | see §1 |
| FreeOTP | ⏳ | mobile app | Android/iOS | no in-app language choice; waits for Android to support `co` |
| MozBackup | ⏳ | desktop app (abandoned) | Windows | one `Default.lng` at a time, replaced in the install folder (admin) |
| WinCDEmu | ⏳ | desktop app | Windows | 4.1 doesn't ship it; manual `langfiles\vmnt_corsican.lng` (admin) |
| Common Voice | 🎯 | website | browser | |
| Unicode CLDR | 🎯 | locale data library | – | benefits ICU/CLDR users generally; no per-app switch |
| VLC media player | 🎯 (README) | desktop app | Win/mac/Linux | §3.1; shipped and selectable today despite the 🎯 |

## 3. Desktop applications

Common columns: *shipped* (where the catalog sits in the package), *mechanism* (exact per-user setting), *close*
(must the program be closed?), *sources*.

### 3.1 VLC media player

**Shipped.**

| Platform | Version checked | Catalog in package |
| --- | --- | --- |
| Windows | 3.0.24 (`vlc-3.0.24-win64.7z`) | `vlc-3.0.24/locale/co/LC_MESSAGES/vlc.mo` (4443 messages; sha256 `2fb128f8…8bda`). The installer also has `languages/CorsicanExtra.nsh` (Corsican NSIS setup). |
| macOS | 3.0.24 (`vlc-3.0.24-arm64.dmg`) | `VLC.app/Contents/MacOS/share/locale/co/LC_MESSAGES/vlc.mo`, plus `Contents/Resources/co.lproj/InfoPlist.strings` |
| Debian 13 | `vlc-l10n 3.0.24-0+deb13u1` | `/usr/share/locale/co/LC_MESSAGES/vlc.mo` ([filelist](https://packages.debian.org/trixie/all/vlc-l10n/filelist)); `vlc-l10n` must be installed |
| Arch | `vlc 3.0.24-1` | `/usr/share/locale/co/LC_MESSAGES/vlc.mo` ([files](https://archlinux.org/packages/extra/x86_64/vlc/files/)) |
| Flathub `org.videolan.VLC` | manifest on KDE 5.15-25.08 | locale split into `.Locale` (see §1) |
| Snap | – | not checked (?) |

**Mechanism.**

- **Windows.** `HKCU\Software\VideoLAN\VLC`, `Lang` (REG_SZ) = `co`. `winvlc.c` reads it before `libvlc_new`
  and runs `putenv("LANG=co")`
  ([winvlc.c L238-L255](https://github.com/videolan/vlc/blob/3.0.x/bin/winvlc.c#L238-L255)). The Qt preferences
  write the same value
  ([simple_preferences.cpp L1275-L1286](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/qt/components/simple_preferences.cpp#L1275-L1286)).
  `{ "co", "Corsu" }` has been in the Qt language list since **3.0.9**: absent in 3.0.8, present in 3.0.9
  ([L85](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/qt/components/simple_preferences.cpp#L85)).
  `auto` or no value means the system language; `--language` on the command line overrides it. It isn't `vlcrc`.
- **macOS.** `defaults write org.videolan.vlc language co`. `darwinvlc.m` calls
  `CFPreferencesCopyAppValue(CFSTR("language"))` and exports `LANG`
  ([L252-L266](https://github.com/videolan/vlc/blob/3.0.x/bin/darwinvlc.m#L252-L266)). The Simple Preferences
  popup writes the same key
  ([VLCSimplePrefsController.m L924-L926](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/macosx/VLCSimplePrefsController.m#L924-L926);
  `co` in its list at L70). `AppleLanguages` doesn't affect VLC's gettext UI.
- **Linux.** There's no option: the language box is hidden when not `_WIN32`
  ([L740-L742](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/qt/components/simple_preferences.cpp#L740-L742)),
  and `vlcrc` has no UI-language key. Use `LANGUAGE=co:fr` through a `.desktop` override, or a Flatpak env override.
  This is what `src/apps/vlc.py` already does.
- **Close?** No. The value is read at start-up and VLC only writes it when the user saves preferences.

**Corsican catalog (`po/co.po`).** Statistics from `msgfmt --statistics`:

| Tree | POT-Creation-Date | PO-Revision-Date | Last-Translator | translated / fuzzy / untranslated | % |
| --- | --- | --- | --- | --- | --- |
| tag 3.0.0 | – | – | – | 2590 / 34 / 3592 | 41.7 |
| tag 3.0.16 (2021-06-18) | – | – | – | 2589 / 5 / 3633 | 41.6 |
| tag 3.0.18 | – | 2018-12-19 | Patriccollu | 2589 / 26 / 3657 | 41.3 |
| tag 3.0.21 | 2024-06-05 | 2017-12-10 | Patriccollu (…2016-2023) | 3147 / 11 / 3127 | 50.1 |
| tag 3.0.23 | 2025-12-08 | 2017-12-10 | Patriccollu | 3782 / 4 / 2509 | 60.1 |
| **tag 3.0.24 = branch 3.0.x (2026-10-16)** | 2026-06-28 16:08+0200 | 2017-12-10 22:48+0000 | Patriccollu di Santa Maria è Sichè, 2026 | **4443 / 0 / 1760** | **71.6** |
| branch master (VLC 4) | 2017-12-06 02:55+0100 | 2017-09-20 03:43+0000 | Patriccollu | 2348 / 331 / 3541 | 37.7 |

- **What VLC 3.0.21 and later ship.** The release builds come from the `3.0.x` branch. Its latest Corsican commit
  is `e66842dbd5223d41a8ad88f85ffce3637c57aa23` "po: update Corsican translation" (author Patriccollu,
  2026-09-16; committed by F. Kühne 2026-09-17; +1190/−878 lines). It was cherry-picked from `b092c52f`. On
  code.videolan.org, `b092c52f` exists but isn't contained in any branch (the refs API returns `[]`). `master` still
  has the 2017 file.
- **Tags.** The `3.0.24` tag (2026-09-17 13:01) contains the update. The Windows `vlc.mo` holds exactly 4443
  messages, which confirms it. 3.0.24 is the build in `download.videolan.org/pub/videolan/vlc/last/`.
- **Three different dates.**
  - **First publication:** a Windows release in November 2017 (Patriccollu: 2339/6030 strings, 38%). The first
    traces go back to Ghjuvan Pasquinu Castellani in 2006.
  - **File revision date:** the `PO-Revision-Date: 2017-12-10` header is stale. Transifex never refreshed it, while
    the content changed in 2023, 2025 and 2026. Rely on the `Translators:` comment ("2016-2023,2026"), the git log
    and the statistics instead.
  - **Consultation date:** 2026-10-16.
- **Patriccollu's text, reconciled.** `Prughjetti/VLC/Traduzzione.md` says: «Di nuvembre di u 2017 era
  distribuita a mo prima versione per Windows chì cuntinia 2339 catene tradutte nant’à 6030, sia 38%» and «In u
  2021, a versione di VLC 3.0 cuntene 6268 catene è a versione in lingua corsa hè tradutta à 43%». That matches
  3.0.16 (≈41.6% by msgfmt; his figure comes from Transifex). The README, which lists VLC under 🎯, says:
  «VLC media player distribuisce dighjà cù a versione attuale una parte - più o menu __una metà__ - di a
  traduzzione in lingua corsa. Ma ùn si pò ancu sceglie a lingua corsa in e preferenze di VLC. Per impiegalla, hè
  faciule : basta à sceglie *Auto* in e preferenze di l’interfaccia di VLC è à definisce a lingua *Corse*, cù una
  tastera *Français*, in e preferenze di lingua di Windows.» "About half" matches 3.0.21 (50.1%). Since 3.0.24 it's
  71.6%. "Can't be chosen in the preferences" is outdated: `Corsu` has been in the Windows and macOS lists since
  3.0.9.
- **Licence.** The header says "distributed under the same license as the VLC package" (GPL-2.0-or-later). Corsu
  doesn't need to redistribute it, because every current package has it.

### 3.2 Audacity

- **Shipped.**
  - Windows 4.0.1: `locale/audacity_co.qm` in `audacity-win-4.0.1-x86_64.7z`.
  - Source 4.0.1: `share/locale/audacity_co.ts`. 4050/4050 current messages translated (100%). `languages.json`
    has `"co": {"name": "Corsu", "fallbackLanguages": ["fr"]}`.
  - Linux 3.x: Arch `audacity 3.7.9` and Debian 13 `audacity-data 3.7.3` have
    `/usr/share/locale/co/LC_MESSAGES/audacity.mo`. 3.7.9 `co.po` is 4521/4521 (100%).
  - Flathub still builds `Audacity-3.7.8`.
  - macOS 4.0.1 dmg: not inspected (?).
- **Mechanism, 3.x** (Linux distros, Flathub, older Windows/mac installs). In `audacity.cfg`, set `[Locale]`
  `Language=co`. `AudacityApp.cpp` reads `/Locale/Language`
  ([L208](https://github.com/audacity/audacity/blob/Audacity-3.7.9/src/AudacityApp.cpp#L208)). Locations:
  - Linux: `~/.config/audacity/audacity.cfg` ([FileNames.cpp L247-L259](https://github.com/audacity/audacity/blob/Audacity-3.7.9/libraries/lib-files/FileNames.cpp#L247-L259); legacy `~/.audacity-data`)
  - Flatpak: `~/.var/app/org.audacityteam.Audacity/config/audacity/`
  - Windows: `%APPDATA%\audacity\`
  - macOS: `~/Library/Application Support/audacity/`
- **Mechanism, 4.x** (current Windows/mac release, Linux AppImage). Audacity 4 runs on MuseScore's `muse`
  framework. The setting is `Settings::Key("languages","language")`
  ([languagesconfiguration.cpp L36](https://github.com/musescore/muse_framework/blob/3ba3cd6886433b41759d2d7adef8aef9bbbd546b/framework/languages/internal/languagesconfiguration.cpp#L36)).
  It's stored through `QSettings` in IniFormat (native format on macOS)
  ([settings.cpp L49-L61](https://github.com/musescore/muse_framework/blob/3ba3cd6886433b41759d2d7adef8aef9bbbd546b/framework/global/settings.cpp#L49-L61)),
  organisation `Audacity`, application `Audacity4`
  ([main.cpp L95-L114](https://github.com/audacity/audacity/blob/Audacity-4.0.1/src/app/main.cpp#L95-L114)).
  With Qt defaults this gives `language=co` in:
  - Windows: `%APPDATA%\Audacity\Audacity4.ini`
  - Linux: `~/.config/Audacity/Audacity4.ini`
  - macOS: domain `org.audacityteam.Audacity4`

  These exact file locations come from Qt defaults and haven't been checked on a real install (?).
- **Close?** Yes. wxFileConfig (3.x) flushes the whole file on exit, and 4.x probably also writes on exit (?).
- **Licence:** GPL (see the project's LICENSE.txt) (?).

### 3.3 Tenacity

- **Shipped.** Tenacity 1.3.5 (Codeberg, 2026-07-06) has `co` in `locale/LINGUAS`. Its `co.po` is 3851 translated,
  205 fuzzy, 50 untranslated (93.8%). The release ships source, AppImage and macOS dmgs; the Windows exe from
  1.4-alpha1 wasn't inspected (?).
- **Mechanism.** Same code as Audacity 3: in `tenacity.cfg`, set `[Locale]` `Language=co`
  ([TenacityApp.cpp L150](https://codeberg.org/tenacityteam/tenacity/src/tag/v1.3.5/src/TenacityApp.cpp#L150)).
  - Linux: `$XDG_CONFIG_HOME/tenacity/tenacity.cfg`, default `~/.config/tenacity/`
    ([FileNames.cpp L257-L262](https://codeberg.org/tenacityteam/tenacity/src/tag/v1.3.5/libraries/lib-files/FileNames.cpp#L257-L262))
  - Windows: `%APPDATA%\Tenacity\` (?)
  - macOS: `~/Library/Application Support/tenacity/` (?)
- **Close?** Yes.

### 3.4 Notepad++ (Windows)

- **Shipped.** 8.9.8.1 (2026-09-24) has `localization/corsican.xml` in the portable zip (sha256 `fcee12ed…f483`).
  The installer's "Localization" component installs the same folder.
- **Mechanism.** Copy `<install>\localization\corsican.xml` to `nativeLang.xml` in the user directory. This is
  exactly what the Preferences switch does: `LocalizationSwitcher::switchToLang` → `CopyFileW(langPath, _nativeLangPath)`
  ([Parameters.cpp L887-L893](https://github.com/notepad-plus-plus/notepad-plus-plus/blob/v8.9.8.1/PowerEditor/src/Parameters.cpp#L887-L893)).
  The user directory is:
  - normally `%APPDATA%\Notepad++\`
  - the program folder if `doLocalConf.xml` exists there and the folder isn't the Program Files directory (portable
    mode)
  - the cloud folder or `-settingsDir=`, if set
    ([L1300-L1345](https://github.com/notepad-plus-plus/notepad-plus-plus/blob/v8.9.8.1/PowerEditor/src/Parameters.cpp#L1300-L1345))

  If there's no user `nativeLang.xml`, `<install>\nativeLang.xml` is tried
  ([L1236-L1248](https://github.com/notepad-plus-plus/notepad-plus-plus/blob/v8.9.8.1/PowerEditor/src/Parameters.cpp#L1236-L1248)).
  The portable marker is `doLocalConf.xml`, not `doNotUseAppData.xml`. `config.xml` isn't involved. To undo,
  delete the user `nativeLang.xml`.
- **Close?** No. The file is read at start-up and never rewritten on exit; the change shows on the next launch.
- **Licence:** GPL-3.0-or-later.

### 3.5 7-Zip (Windows)

- **Shipped.** `Lang/co.txt` in `7z2604-x64.exe` (26.04, 2026-10-06). Its header says "24.04 : 2024-04-06 :
  Patriccollu … (Latest Update)", created 9.20 in 2010. The Linux tarball is console-only, with no `Lang`.
- **Mechanism.** `HKCU\Software\7-Zip`, `Lang` (REG_SZ) = `co`
  ([RegistryUtils.cpp L14-L20, L58-L59](https://github.com/ip7z/7zip/blob/26.04/CPP/7zip/UI/FileManager/RegistryUtils.cpp#L14-L20)).
  `ReloadLang()` appends `.txt` when the value has no dot and resolves it in `<exe dir>\Lang\`. `-` means English.
  With no value, the language comes from `GetUserDefaultLangID`, whose table includes `co`
  ([LangUtils.cpp L178, L308](https://github.com/ip7z/7zip/blob/26.04/CPP/7zip/UI/FileManager/LangUtils.cpp#L308)).
  The value is a plain name, not a full path.
- **Close?** No for 7zFM. The Explorer context-menu extension loads the language once per process, so the menu
  changes after Explorer restarts or the user signs out.
- **Licence:** GNU LGPL (7-Zip licence).

### 3.6 SumatraPDF (Windows)

- **Shipped.** Translations are compiled into the exe. 3.6.1 (2026-04-06) has `co` in `gLangCodes`, shown as
  "Corsican (Corsu)" ([TranslationLangs.cpp](https://github.com/sumatrapdfreader/sumatrapdf/blob/3.6.1rel/src/TranslationLangs.cpp)).
- **Mechanism.** The line `UiLanguage = co` in `SumatraPDF-settings.txt`
  ([Settings.h L494-L495](https://github.com/sumatrapdfreader/sumatrapdf/blob/3.6.1rel/src/Settings.h#L494-L495)).
  Sumatra uses its own text format: a top-level key, not an INI section. The file is in
  `%LOCALAPPDATA%\SumatraPDF\` for installed copies, or next to the exe in portable mode when writable
  ([AppTools.cpp L124-L146](https://github.com/sumatrapdfreader/sumatrapdf/blob/3.6.1rel/src/AppTools.cpp#L124-L146)).
- **Close?** Yes. Settings are saved on exit (`SaveSettings`).
- **Licence:** GPL-3.0. Strings live on AppTranslator.

### 3.7 WinMerge (Windows)

- **Shipped.** 2.16.58.2 (latest stable; 2.16.59 is a pre-release) has `Languages/Corsican.po`,
  `Languages/ShellExtension/Corsican.po`, `Merge7z/Lang/co.txt` and `Docs/ReadMe-Corsican.txt`. `Corsican.po` has
  PO-Revision-Date 2026-06-21.
- **Mechanism.** Option `Locale/LanguageId`
  ([OptionsDef.h L11](https://github.com/WinMerge/winmerge/blob/v2.16.58.2/Src/OptionsDef.h#L10-L11)), which
  defaults to `GetUserDefaultLangID()`
  ([OptionsInit.cpp L41-L42](https://github.com/WinMerge/winmerge/blob/v2.16.58.2/Src/OptionsInit.cpp#L41-L42)).
  - Registry: `HKCU\Software\Thingamahoochie\WinMerge\Locale`, `LanguageId` (REG_DWORD) = **1155** (`0x0483` =
    `MAKELANGID(LANG_CORSICAN, SUBLANG_DEFAULT)`; `Corsican.po` declares `LANG_CORSICAN, SUBLANG_DEFAULT`).
  - Portable: if `winmerge.ini` sits next to `WinMergeU.exe`, or `/inifile` is used, write
    `[WinMerge] Locale/LanguageId=1155` there instead
    ([Merge.cpp L143-L157](https://github.com/WinMerge/winmerge/blob/v2.16.58.2/Src/Merge.cpp#L143-L157),
    [IniOptionsMgr.cpp L14](https://github.com/WinMerge/winmerge/blob/v2.16.58.2/Src/Common/IniOptionsMgr.cpp#L14)).
- **Close?** Safer, yes. Options are written one by one, so an overwrite on exit is unlikely (?).
- **Licence:** GPL-2.0-or-later.

### 3.8 FileZilla Client

- **Shipped.**
  - Linux: Arch `filezilla 3.71.1` and Debian 13 `filezilla-common` have `/usr/share/locale/co/LC_MESSAGES/filezilla.mo`.
  - Windows: the trunk NSIS script has a "Language files" section that includes the generated
    `installlangfiles.nsh` (all compiled locales) into `<install>\locales\<lang>\filezilla.mo`
    ([install.nsi.in](https://svn.filezilla-project.org/svn/FileZilla3/trunk/data/install.nsi.in)). The binary
    wasn't inspected, because the download site is gated, and the component can be deselected.
  - macOS: not checked (?).
  - The `co.po` (PO-Revision-Date 2026-04-15) is 1896/1901 (99.7%).
- **Mechanism.** In `filezilla.xml`, set `<Settings><Setting name="Language Code">co</Setting>`
  ([Options.cpp](https://svn.filezilla-project.org/svn/FileZilla3/trunk/src/interface/Options.cpp) L44). It's read
  before the UI starts by `CInitializer` ([locale_initializer.cpp](https://svn.filezilla-project.org/svn/FileZilla3/trunk/src/interface/locale_initializer.cpp) L355-L357).
  - Windows: `%APPDATA%\FileZilla\`
  - Linux: `~/.config/filezilla/`
  - Flatpak: `~/.var/app/org.filezillaproject.Filezilla/config/filezilla/`
  - macOS: same as Linux (?)
  - `fzdefaults.xml` "Config Location" can redirect it.
- **Close?** Yes. The settings file is written back by the running client.
- **Licence:** GPL-2.0-or-later.

### 3.9 Poedit

Implemented in [`src/apps/poedit.py`](../src/apps/poedit.py) (checked 2026-10-17).

- **Shipped.**
  - Source v3.10-oss (2026-10-14) has `locales/co.po`, 736/737 (99.9%); Corsican since at least 3.4.2.
  - Windows 3.10 (`Poedit-3.10-setup.exe`, installed silently with Wine in a container): `Program Files\Poedit\Translations\co\poedit.mo`.
  - macOS 3.10 (`Poedit-3.10.zip`): `Poedit.app/Contents/Resources/co.lproj/poedit.mo`; bundle id `net.poedit.Poedit`, not sandboxed.
  - Debian 13 `poedit` + `poedit-common` 3.6.3: `/usr/bin/poeditor`, `/usr/share/locale/co/LC_MESSAGES/poedit.mo`.
  - Flathub `net.poedit.Poedit`: `co` in its `.Locale` extension (needs `extra-languages co`).
- **Mechanism.**
  - **Windows** is the only platform with an in-app choice (`NEED_CHOOSELANG_UI` is `__WXMSW__` only,
    [uilang.h L34-L38](https://github.com/vslavik/poedit/blob/v3.10-oss/src/uilang.h#L34-L38)). Poedit's wxConfig has
    no file there ([edapp.cpp L405-L411](https://github.com/vslavik/poedit/blob/v3.10-oss/src/edapp.cpp#L405-L411)), so
    it is wxRegConfig: `HKCU\Software\Vaclav Slavik\Poedit`, REG_SZ `ui_language` = `co` (or `default`)
    ([uilang.cpp L196-L222](https://github.com/vslavik/poedit/blob/v3.10-oss/src/uilang.cpp#L196-L222),
    [edapp.cpp L344-L345](https://github.com/vslavik/poedit/blob/v3.10-oss/src/edapp.cpp#L344-L345)). Read at start,
    written only by that dialog; can be set before the first start. Not run on Windows (Poedit.exe needs Windows' own
    `icu.dll`, missing under Wine).
  - **Linux:** no setting (`NEED_CHOOSELANG_UI` is 0, so no `ui_language` key is read, 3.6.3 and 3.10), and
    `LANGUAGE` alone is not enough. Two readers of the same variables:
    - Poedit's own strings: `PoeditApp::SetupLanguage` ([edapp.cpp L543-L590](https://github.com/vslavik/poedit/blob/v3.6.3-oss/src/edapp.cpp#L543-L590))
      asks `wxUILocale::GetPreferredUILanguages`, which puts the language of `LC_ALL`, else `LC_MESSAGES`, else
      `LANG` before `LANGUAGE`'s list, a `C`/`POSIX` value (the part before `.`/`@`) counting as none
      ([uilocale.cpp L56-L99, L886-L956](https://github.com/wxWidgets/wxWidgets/blob/v3.2.8/src/unix/uilocale.cpp#L886-L956);
      identical in 3.2.12, Flathub's build); ICU's `uloc_acceptLanguage` then picks the first language with a catalogue.
    - GTK's dialogs (file chooser, its buttons): glibc gettext, after `wxLocale::Init(wxLANGUAGE_DEFAULT)` did
      `setlocale(LC_ALL, "")` ([intl.cpp L486](https://github.com/wxWidgets/wxWidgets/blob/v3.2.8/src/common/intl.cpp#L486)).
      glibc ignores `LANGUAGE` when `LC_MESSAGES` is `C` or `C.<codeset>`
      ([dcigettext.c, release/2.41, L1527-L1543](https://sourceware.org/git/?p=glibc.git;a=blob;f=intl/dcigettext.c;hb=refs/heads/release/2.41/master#l1527)).

    So the first way (0.25 before this fix: `LANG=C.UTF-8 LC_MESSAGES=C.UTF-8`, formats given back) had Poedit in
    Corsican but GTK's dialogs in English (reproduced: Debian 3.6.3 and Flathub 3.10). A `co_FR` locale name does not
    exist in glibc: `setlocale` fails as a whole and the C++ locale breaks.

    **Now:** `LANGUAGE=co:<languages> LC_MESSAGES=/C.UTF-8`, `LANG` and the formats untouched (when the session sets
    `LC_ALL`, it is emptied and its value given to `LANG` and the categories the session sets). wxWidgets sees `/C`:
    not `C`, no known language, so `LANGUAGE`'s list comes first → Corsican. glibc accepts a name starting with `/`
    (`valid_locale_name`, [findlocale.c L95](https://sourceware.org/git/?p=glibc.git;a=blob;f=locale/findlocale.c;hb=refs/heads/release/2.41/master#l95))
    and finds it under its locale folder (`/usr/lib/locale//C.UTF-8`, the C.UTF-8 folder glibc ≥ 2.35 ships): only
    `LC_MESSAGES` comes from it, and since its name is not `C`, gettext follows `LANGUAGE` → GTK, which has no
    Corsican, uses the person's language.

    Run for real on 2026-10-17, in containers under Xvfb:
    - Debian 13 `poedit` 3.6.3 (wxWidgets 3.2.8, glibc 2.41, GTK 3.24.49).
    - Flathub `net.poedit.Poedit` 3.10 (wxWidgets 3.2.12, GNOME 51 runtime, glibc 2.44).
    - Sessions `fr_FR`, `de_DE`, `it_IT`, plus `LC_ALL=it_IT` over `LANG=en_US`.

    Observed: Poedit's trace says `using UI language 'co'`, its window is in Corsican, File → Open's GTK chooser and
    its buttons are in French/German/Italian, the file-list dates and "50 %" use the session's format, a `.po` in an
    accented folder opens, and there is no locale error. Corsu's own code wrote the entry or override; switching off,
    on and uninstalling gave the files back.

    **Trade-offs:**
    - This depends on how glibc resolves locale names, not on a documented interface. Before writing the menu entry,
      Corsu checks it with `LC_ALL=/C.UTF-8 locale` (no "Cannot set").
    - Where the check fails (musl, a glibc without the C.UTF-8 folder), Corsu falls back to the first way. The
      installation's label then says the file dialogs will be in English.
    - The Flatpak is not checked by Corsu: its runtime's glibc is the one seen.
    - `LC_MESSAGES` data (yes/no regexes) is C's: Poedit does not use it.
    - Programs Poedit starts (msgfmt…) inherit the same variables, and their messages follow `LANGUAGE` too.
  - **macOS:** no setting of Poedit's own; `wxUILocale::GetPreferredUILanguages` is `[NSLocale preferredLanguages]`
    ([osx/core/uilocale.mm L314-L325](https://github.com/wxWidgets/wxWidgets/blob/v3.2.8/src/osx/core/uilocale.mm#L314-L325)),
    which reads `AppleLanguages` from the app's own domain before the global one, the same array System Settings →
    Language & Region → Applications writes.

    Corsu writes `AppleLanguages` = `co` + the person's global list (read only; `co*` taken out) in
    `net.poedit.Poedit` (bundle id from Poedit.xcodeproj; the app has no entitlements, so it is not sandboxed).
    AppKit's own panels have no Corsican, so they should take the next language.

    The new typed-preference helper (`settings.set_defaults_value`) works as follows:
    - It reads with `defaults export <domain> -` and plistlib, and writes `defaults write <domain> <key> '<array>…</array>'`
      (XML fragment, any plist type).
    - It records the original as an XML fragment, or as absent, and gives back exactly that type and value. A value
      changed since stays.
    - It refuses `NSGlobalDomain`/`-g`/`.GlobalPreferences`.

    **Experimental:** Poedit itself was not run on a Mac. The unit tests use a simulated `defaults`.
    `tests/test_apps_settings.py` `RealMacTests` runs only on GitHub Actions macOS runners, on throwaway domains. On
    the macOS 26 arm64 runner (2026-10-17, workflow_dispatch run 39034793266):
    - The helper's real `defaults` round trip passed: an absent key and an array `AppleLanguages`, and string, int,
      bool and dict values on another key, all came back with the same type.
    - A tool with its own bundle id got `NSLocale.preferredLanguages` = `co,fr-FR` from the per-app list (`en-US`
      without it).
    - A *string* written to `AppleLanguages` reads back as absent there: Foundation only takes an array.

    The Poedit window and whether AppKit panels fall back to the second language are still unverified (?).
- **Close?** No: neither the registry value nor the menu entry is rewritten by Poedit; a restart is enough.
- **Licence:** MIT.

### 3.10 HandBrake

- **Shipped.**
  - Windows 1.11.2: the single-file `HandBrake.exe` embeds the satellite resources, and the "Corsican (Corsu)"
    entry is present.
  - macOS 1.11.2: `HandBrake.app/Contents/Resources/co.lproj/*.strings`.
  - Linux: `co` in `gtk/po/LINGUAS`; Debian 13 and Arch install `/usr/share/locale/co/LC_MESSAGES/ghb.mo`.
- **Mechanism.**
  - **Windows.** `%APPDATA%\HandBrake\settings.json` (nightly builds: `…\HandBrake\Nightly\`; portable: `storage.dir` from
    `portable.ini`). Set the JSON key `"UiLanguage": "co"`
    ([UserSettingConstants.cs L70](https://github.com/HandBrake/HandBrake/blob/1.11.2/win/CS/HandBrakeWPF/UserSettingConstants.cs#L70),
    [App.xaml.cs L150-L160](https://github.com/HandBrake/HandBrake/blob/1.11.2/win/CS/HandBrakeWPF/App.xaml.cs#L150-L160),
    [InterfaceLanguageUtilities.cs L31](https://github.com/HandBrake/HandBrake/blob/1.11.2/win/CS/HandBrakeWPF/Utilities/InterfaceLanguageUtilities.cs#L31),
    [DirectoryUtilities.cs](https://github.com/HandBrake/HandBrake/blob/1.11.2/win/CS/HandBrake.App.Core/Utilities/DirectoryUtilities.cs#L29-L98)).
  - **Linux (GTK).** `~/.config/ghb/preferences.json` (Flatpak: `~/.var/app/fr.handbrake.ghb/config/ghb/`). Set
    `{"Preferences": {"UiLanguage": "co"}}`. `application.c` reads it before building the UI and sets
    `LANGUAGE=co` ([L763-L770](https://github.com/HandBrake/HandBrake/blob/1.11.2/gtk/src/application.c#L763-L770),
    [hb-backend.c L420-L428](https://github.com/HandBrake/HandBrake/blob/1.11.2/gtk/src/hb-backend.c#L420-L428),
    [presets.c L1131-L1141](https://github.com/HandBrake/HandBrake/blob/1.11.2/gtk/src/presets.c#L1131-L1141)).
    A plain `LANGUAGE` environment variable also works.
  - **macOS.** No in-app option, so use per-app `AppleLanguages (co, fr, en)`. The app is sandboxed
    ([entitlements](https://github.com/HandBrake/HandBrake/blob/1.11.2/macosx/HandBrake.entitlements)), so write the
    container domain `~/Library/Containers/fr.handbrake.HandBrake/Data/Library/Preferences/fr.handbrake.HandBrake` (?).
- **Close?** Yes. The whole settings or preferences file is rewritten on save.
- **Licence:** GPL-2.0.

### 3.11 fre:ac

- **Shipped.** The Windows 1.1.7 zip has `lang/freac_co.xml`, `tips_co.xml` and `eupdate_co.xml`. The AppImage,
  macOS and distro packages weren't inspected (?).
- **Mechanism.** In `freac.xml`, set
  `<ConfigFile><configuration name="default"><section name="Settings"><value name="Language">freac_co.xml</value>`.
  - The value is the **file name**, not `co`
    ([config.cpp L24, L60](https://github.com/enzo1982/freac/blob/v1.1.7/src/config.cpp#L60-L61);
    smooth `magic = file.GetFileName()` [translator.cpp](https://github.com/enzo1982/smooth/blob/master/classes/i18n/translator.cpp#L410-L420);
    XML names in [smooth config.cpp](https://github.com/enzo1982/smooth/blob/master/classes/misc/config.cpp#L15-L22)).
  - The file is next to the exe when it exists there outside Program Files (portable). Otherwise it's
    `%APPDATA%\freac\freac.xml` on Windows or `~/.config/freac/freac.xml` on Linux
    ([BoCA config.cpp L285-L350](https://github.com/enzo1982/BoCA/blob/master/runtime/common/config.cpp#L285-L350)).
  - With no value, the language comes from the Windows user language (`LANG_CORSICAN` → `co`).
- **Close?** Yes.
- **Licence:** GPL-2.0-or-later.

### 3.12 VeraCrypt

- **Shipped.** 1.26.29 (2026-06-12). `Translations/Language.co.xml` has `prog-version="1.26.29"`, and its header
  history runs to May 2026.
  - Windows: the file is referenced by `Setup.rc`, `Portable.rc` and the MSI `.wxs`, and installed to
    `<install>\Languages\`.
  - macOS: `Main.make` copies `Translations/*` into `VeraCrypt.app/Contents/Resources/languages`.
  - Linux: `INSTALL_LANGUAGES ?= 1` installs to `/usr/share/veracrypt/languages/`; the AppImage uses
    `$APPDIR/usr/share/…`
    ([Resources.cpp L51-L100](https://github.com/veracrypt/VeraCrypt/blob/VeraCrypt_1.26.29/src/Main/Resources.cpp#L51-L100)).
- **Mechanism.** In `Configuration.xml`, set `<config key="Language">co</config>`.
  - Windows: `%APPDATA%\VeraCrypt\`, or next to the exe in portable mode
    ([Mount.c L1449 read, L1573 write](https://github.com/veracrypt/VeraCrypt/blob/VeraCrypt_1.26.29/src/Mount/Mount.c#L1449)).
  - Linux: `~/.config/VeraCrypt/` ([Application.cpp](https://github.com/veracrypt/VeraCrypt/blob/VeraCrypt_1.26.29/src/Main/Application.cpp#L40-L70)).
  - macOS: wx user data dir (?).
  - On Linux and macOS, `system` means "derive from `LANG`".
- **Close?** Yes, including the tray instance. `SaveSettings` writes `Language` back.
- **Licence:** Apache-2.0 / TrueCrypt 3.0 (project). The translation file has no separate notice (?).

### 3.13 PDFsam Basic

**Switched by Corsu (`src/apps/pdfsam.py`, component `pdfsam`) on Linux and Windows.** Checked on Linux with the real
program; Windows and macOS with simulated files only.

- **Shipped.** 6.0.6 (2026-10-02): `pdfsam-i18n-6.0.6.jar` contains `org/pdfsam/i18n/Messages_co.properties`
  (466/466 entries, like French). It's the same jar in the .deb, the Linux tar.gz, the Windows zip/MSI
  (`app/mods/`) and the macOS zip. Corsican has been there since **3.0.0**: `Locale("co")` and `po/co.po` came in
  commit 6d075b1b (2015-08-03), first tag v3.0.0.M2. `co` is in the supported set
  ([I18nContext.java L47-L54](https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-i18n/src/main/java/org/pdfsam/i18n/I18nContext.java#L47-L54)).
- **Mechanism.** Java Preferences node `/org/pdfsam/user/conf`
  ([ApplicationContext.java L56](https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-core/src/main/java/org/pdfsam/core/context/ApplicationContext.java#L56)),
  key `locale`: the enum name lower-cased
  ([StringPersistentProperty.java L40, L64-L66](https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-core/src/main/java/org/pdfsam/core/context/StringPersistentProperty.java#L40)).
  4.x used `LOCALE`; the lower-case key came with 5.0.0, so Corsu leaves versions before 5 alone. The value is a
  language tag, `co`
  ([ComboItem.java L70-L72](https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-model/src/main/java/org/pdfsam/model/ui/ComboItem.java#L70-L72)).
  PDFsam reads it once, at start
  ([PdfsamApp.java L106-L107](https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-gui/src/main/java/org/pdfsam/gui/PdfsamApp.java#L106-L107)).
  It also writes it back at every start, with the language it shows: the settings page sets its language list, and
  the list's listener saves the value
  ([PreferenceAppearencePane.java L55-L57](https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-gui/src/main/java/org/pdfsam/gui/components/content/preference/PreferenceAppearencePane.java#L55-L57),
  [PreferenceComboBox.java L46-L49](https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-gui/src/main/java/org/pdfsam/gui/components/content/preference/PreferenceComboBox.java#L46-L49)).
  The first start wrote `locale="en"`. Before that first start there's nothing to change, so Corsu leaves PDFsam
  alone and asks the person to start it once (an `action`, not an error).
  - Linux: `~/.java/.userPrefs/org/pdfsam/user/conf/prefs.xml`, `<entry key="locale" value="co"/>`
    ([FileSystemPreferences](https://github.com/openjdk/jdk/blob/master/src/java.prefs/unix/classes/java/util/prefs/FileSystemPreferences.java)).
    These node names need no escaping.
  - Windows: `HKCU\Software\JavaSoft\Prefs\org\pdfsam\user\conf`, `locale` (REG_SZ) = `co`. Java escapes capital
    letters as `/X` in names and values
    ([WindowsPreferences](https://github.com/openjdk/jdk/blob/master/src/java.prefs/windows/classes/java/util/prefs/WindowsPreferences.java)
    `toWindowsName`, `toWindowsValueString`). `locale` and `co` have none; 4.x's `LOCALE` was `/L/O/C/A/L/E`.
  - macOS: **not switched.** Nodes three or more levels deep live in the CFPreferences domain of their first three
    names: `org.pdfsam.user`, `~/Library/Preferences/org.pdfsam.user.plist`. The whole `/org/pdfsam/user/` tree is
    one nested dictionary there
    ([MacOSXPreferences.cfFileForNode](https://github.com/openjdk/jdk/blob/master/src/java.prefs/macosx/classes/java/util/prefs/MacOSXPreferences.java),
    [MacOSXPreferencesFile.m copyTreeForPath](https://github.com/openjdk/jdk/blob/master/src/java.prefs/macosx/native/libprefs/MacOSXPreferencesFile.m)),
    and `defaults` can't change one key inside it. Corsu shows the step instead (Settings > Language).
  - The JVM property `org.pdfsam.default.locale` is only a default: the MSI may write it into `app\pdfsam.cfg`, and
    the preference wins over it.
- **Close?** Linux: **yes**, also to switch off. A running PDFsam keeps the node in memory and writes it back when
  it quits, without reading a change another program made in the meantime: Java only reloads when another JVM
  touches `.userRootModFile`. In the real run, `co` written while PDFsam was open came back as `en` after it quit.
  Corsu recognizes the process by the Java command line, which names `org.pdfsam.basic`. Windows: no. The registry
  is read and written live, so PDFsam only needs a restart (`restart_required`).
- **Installations.** Every installation on an account shares the one preference, portable zips included.
  - Detected: `/opt/pdfsam-basic` (official .deb, AUR `pdfsam-bin`), `/usr/share/java/pdfsam` (AUR `pdfsam`), a
    tar.gz reached through `pdfsam`/`pdfsam-basic` in `PATH`, `%ProgramFiles%\PDFsam Basic\pdfsam.exe` (MSI,
    `pdfsam.wxs`), and `/Applications/PDFsam Basic.app`.
  - Not on Flathub (`org.pdfsam.basic`: 404, 2026-10-17) or the Snap Store, so there's no sandboxed variant to target.
- **After Corsu.**
  - If the person picks another language in PDFsam, it's kept: a later Corsu run leaves it alone, and switching off
    or uninstalling doesn't touch it.
  - Switching off brings back the earlier value. With no earlier value, the key is removed.
- **Real run** (Debian 13 container, official `pdfsam-basic_6.0.6-1_amd64.deb`, Xvfb, isolated account). Never
  started gives "start once". Switched on twice: one line of `prefs.xml` changed. PDFsam showed Corsican ("Accolta",
  "Attrezzi per frazziunà"), and `co` was still there after it quit. While open, Corsu waited. Switched off: the file
  was byte-identical to before. A later `fr` survived Corsu runs and uninstallation.
- **Licence:** AGPL-3.0.

### 3.14 Mp3tag (Windows; Mac paid)

- **Shipped.** Not verified. Patriccollu reports `Corsican.lng` in `<install>\lang` since 2.75 (2016), and a
  Corsican NSIS installer.
- **Mechanism.** Unknown. The documentation only says "Options > Language … used after a restart"
  ([docs](https://docs.mp3tag.de/customization/options/language/)). The only registry value found in forums is the
  *installer* language, `HKCU\Software\Moebius\Install\Mp3tag\Installer Language`. Treat Mp3tag as a guided user
  step.
- **Licence:** proprietary. Don't redistribute.

### 3.15 Paint.NET (Windows)

- **Shipped.** Corsican (`co`) was added in 4.3.3 (Nov 2021, [release notes](https://blog.getpaint.net/2021/11)).
  The current 5.x package wasn't inspected.
- **Mechanism (?).** `HKCU\Software\paint.net`, value `UI/Language`. This comes only from forum posts (example value
  `en-US`; HKCU overrides HKLM,
  [forum](https://forums.getpaint.net/topic/116028-automatic-language-selection-on-terminal-server-windows-server-2016/)).
  The expected value is `co`; check it on a real install. Store edition: unknown.
- **Licence:** proprietary freeware. Don't redistribute.

## 4. Mobile apps

Firefox and Focus for Android and iOS, Thunderbird for Android (ex K-9 Mail), VLC for Android and iOS, OpenTracks,
OSM Dashboard, NoNonsense Notes and FreeOTP run on the phone. **A desktop installer can't configure them.** Corsu
can only show instructions:

- **In-app choice.** VLC for Android, OpenTracks (≥ 4.16.1), OSM Dashboard (≥ 6.1.0), Thunderbird for Android and
  Firefox for Android have their own language setting that lists Corsican, according to Patriccollu's notes.
- **Android 13+ per-app language.** Settings → System → Languages → App languages → *app* → Corsu. This only works
  for apps that declare `co` in their locale config, and when the system offers Corsican. FreeOTP has no in-app
  choice and is blocked until Android supports `co` (README).
- **iOS.** Add Corsu under Settings → General → Language & Region (Patriccollu's tip for Firefox iOS), or use the
  per-app language on the app's Settings page.

## 5. Redistribution summary

| Catalog | Licence | Advice |
| --- | --- | --- |
| VLC `co.po` | GPL-2.0-or-later | in all current packages; if ever needed, pin `code.videolan.org/videolan/vlc/-/raw/<tag>/po/co.po` + SHA-256 |
| Audacity / Tenacity | GPL | shipped |
| Notepad++ `corsican.xml` | GPL-3.0-or-later | shipped; Corsu copies the installed file, it doesn't bring its own |
| 7-Zip `co.txt` | LGPL | shipped |
| SumatraPDF | GPL-3.0 | compiled in |
| WinMerge `Corsican.po` | GPL-2.0-or-later | shipped |
| FileZilla `co.po` | GPL-2.0-or-later | shipped |
| Poedit `co.po` | MIT | shipped |
| HandBrake | GPL-2.0 | shipped |
| fre:ac | GPL-2.0-or-later | shipped |
| VeraCrypt `Language.co.xml` | VeraCrypt licence (?) | shipped since 1.26.7; for older versions the file needs admin rights to install, so it's out of scope |
| PDFsam `Messages_co.properties` | AGPL-3.0 | inside the jar |
| Mp3tag, Paint.NET, CCleaner | proprietary | never redistribute |
| MozBackup, WinCDEmu (Patriccollu's repo) | his repository (licence not stated (?)) | install-folder copies need admin, so out of scope |

## 6. Best candidates for automatic activation

All eight have a verified catalog in the current release, a verified per-user setting and a simple value.

1. **7-Zip (Windows).** `HKCU\Software\7-Zip\Lang = "co"`. One registry string, no close needed. `Lang\co.txt`
   is in 26.04.
2. **Notepad++ (Windows).** Copy `<install>\localization\corsican.xml` to `%APPDATA%\Notepad++\nativeLang.xml`
   (respect `doLocalConf.xml`). This mirrors the program's own code, and the file is never rewritten on exit.
3. **WinMerge (Windows).** `HKCU\Software\Thingamahoochie\WinMerge\Locale\LanguageId = 1155` (DWORD), or
   `winmerge.ini` in portable mode.
4. **VLC.** Windows `HKCU\Software\VideoLAN\VLC\Lang = "co"`; macOS `defaults write org.videolan.vlc language co`;
   Linux `LANGUAGE` override (already implemented). 71.6% coverage in 3.0.24, so mention the partial coverage.
5. **SumatraPDF (Windows).** `UiLanguage = co` in `SumatraPDF-settings.txt`. Close it first.
6. **FileZilla (all platforms).** `<Setting name="Language Code">co</Setting>` in `filezilla.xml`. 99.7%
   coverage. Close it first.
7. **HandBrake (Windows and Linux).** `"UiLanguage": "co"` in `settings.json` (Windows) or in
   `preferences.json` → `Preferences` (GTK). Close it first.
8. **VeraCrypt (all platforms).** `<config key="Language">co</config>` in `Configuration.xml`. Close it first,
   including the tray instance.

Next in line:

- **Audacity:** 3.x is fully verified; the 4.x file location still needs checking on a real install.
- **fre:ac:** value `freac_co.xml`.
- **PDFsam:** Java Preferences.
- **Poedit:** done (§3.9).
- **Tenacity.**
- **Paint.NET and Mp3tag:** mechanism unverified.

## 7. Open points (?)

- Audacity 4 `Audacity4.ini` / plist location and key on a real install; whether the macOS 4.0.1 dmg contains
  `audacity_co.qm`.
- FileZilla Windows/macOS binaries (installer contents not downloaded); FileZilla macOS config path.
- Poedit on a real Windows and Mac (registry value and per-app language list not run).
- HandBrake macOS sandbox container domain for `AppleLanguages`.
- Paint.NET `UI/Language` value format for `co`; Mp3tag storage.
- VLC Snap: catalog presence and a workable per-user override.
- Tenacity Windows/macOS config paths.
