# Corsu

Corsican interface translations for **Firefox, Discord with Vencord, and Vesktop on Linux, Windows and macOS**,
**Chrome, Opera / Opera GX, Edge, Brave, Vivaldi and Chromium on Linux and Windows**, plus **KDE Plasma and Qt
applications on Linux**.
GPL-3.0-or-later: you can share, modify and redistribute this project, including its source.

**This is a work in progress, not a complete Corsican language pack.** Menus, dialogs, settings and error
pages are translated locally from a lexicon of draft translations. Unknown labels keep their French (or
English) text. Websites, chat messages, file names, people's names and typed text are never translated.
Application names in the Plasma launcher stay as their vendors publish them. The lexicon welcomes review
by Corsican speakers.

Reviewed human translations come first: `lexicon-mozilla.tsv` holds the Corsican work of **Patriccollu di Santa
Maria è Sichè** and the Mozilla Corsican team for Firefox on Android (MPL-2.0, from
[mozilla-l10n/android-l10n](https://github.com/mozilla-l10n/android-l10n)), and every draft row follows its
terminology (*unghjetta*, *parolla d'intesa*, *indetta*, *cronolugia*, *parametri*, *arregistrà*, *abbandunà*).
See Patriccollu's catalogue of Corsican software: [Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica).

## Download and install

Download the archive for your system from the [latest release](https://github.com/Platykalt/corsu/releases/latest)
and extract it. Each archive comes with a `.sha256` checksum.

| System | Archive | Start the installer |
| --- | --- | --- |
| Windows 10/11 (x64) | `corsu-…-windows-x86_64.zip` | Double-click `install.cmd` (it offers to install Python 3 with `winget` if needed) |
| macOS 12+ | `corsu-…-macos.tar.gz` | `./install.sh` in Terminal |
| Linux x86_64 | `corsu-…-linux-x86_64.tar.gz` | `./install.sh` |

The installer asks **“Select what you want to translate”** and lists the applications it found:

```
Select what you want to translate:
  [x] 1. Firefox — menus, settings, error pages
  [x] 2. Discord — interface labels through Vencord
  [x] 3. Chromium browsers — Chrome, Opera / Opera GX, Edge, Brave, Vivaldi
Type numbers to toggle (e.g. "2 3"), Enter to continue, q to quit:
```

It then lists every change and asks you to accept it. Afterwards a **Corsu — Setup** entry (application
menu on Linux, Start menu on Windows, `~/Applications` on macOS) reopens this selection, so you can add or
remove applications at any time. The installer copies itself into Corsu's data directory, so the downloaded
archive can be deleted.

Requirements: Python 3.10 or newer, and the applications you want translated. Firefox must be the regular
Mozilla build (Snap and Flatpak Firefox are sealed and cannot be translated this way). For the Plasma
desktop, KDE Plasma and its French translations must already be installed.

Close Firefox and Discord before installing, then reopen them. Log out and back in to activate the Plasma
language. Discord updates can remove its patch: open **Corsu — Setup** again afterwards.

## What each component changes

| Component | Systems | Effect |
| --- | --- | --- |
| `firefox` | all | A translated copy of your Firefox plus a **Firefox — Corsu** launcher. Your existing profile, bookmarks and extensions are used as they are. The copy is rebuilt automatically after Firefox updates |
| `chromium` | Linux, Windows | Translates the French interface pack (`fr.pak`) of every installed Chromium browser in place, so the browser shows Corsican wherever it would show French. Browser updates bring a fresh French pack: Corsu translates it again when you start the browser from its menu entry (Linux) or at login (Windows). System-wide browsers ask for administrator rights for that. Your profile, logins and cookies are untouched |
| `discord` | all | Patches native Discord through the official, checksum-verified Vencord installer and enables the bundled Corsu plugin |
| `vesktop` | all | Points Vesktop at the custom Vencord build and enables the Corsu plugin |
| `desktop` | Linux | User gettext and Qt catalogs (`~/.local/share/locale/co`), Plasma interface language `co:fr`, translated application menu entries |
| `qt` | Linux | Copies Corsican Qt catalogs into `/usr/share/qt6/translations` so Qt's own buttons and file choosers are translated. Requires administrator authentication and is removed again by `--uninstall` |

Firefox's translation starts from Mozilla's French language pack for your exact Firefox version, downloaded
from `archive.mozilla.org` and verified against Mozilla's published `SHA512SUMS` (a bundled copy is used
offline), then applies the Corsican lexicon on top. Firefox's security preferences and extension signature
checks remain enabled; only the translated copy's self-updater is switched off, because Corsu rebuilds it
from your updated Firefox instead.

Chromium browsers display Corsican where they would display French: on Windows Corsu selects French in the
browser's language setting; on Linux its menu entry starts the browser with `LANGUAGE=co:fr`. macOS is not
supported for Chromium browsers yet: changing a signed browser there breaks its Keychain access to saved
passwords and cookies.

Command-line options (use `py -3` instead of `python3` on Windows):

```bash
python3 installer.py --dry-run
python3 installer.py --components firefox discord
python3 installer.py --components discord --discord-path /path/to/discord
python3 installer.py --yes
python3 corsu.py status
```

`--yes` explicitly accepts the displayed plan. No settings are changed by `--dry-run` or by declining consent.
`--discord-path` takes the folder holding `resources/` on Linux, `%LOCALAPPDATA%\Discord` on Windows, or
`Discord.app` on macOS. On Linux, `~/.local/bin/firefox-corsu` launches the translated browser; explicit `-P`,
`-profile` or `-ProfileManager` arguments override profile discovery. An already running ordinary Firefox may
keep its original interface until you fully quit and reopen it.

Vencord automatic updates are disabled to protect the custom plugin; update/rebuild Corsu manually.
Vencord is a third-party Discord client modification. Read its [official documentation](https://docs.vencord.dev/installing/).
Corsu does not translate chat messages or provide a message translation service.

## Phones

No phone system can be translated by an outside project, but many apps already speak Corsican:

* **iPhone:** Settings › General › Language & Region › Add Language › Corsican. Apps that ship Corsican, such as
  Firefox for iOS, then appear in Corsican (per app: Settings › the app › Language). The Keyman app's EuroLatin
  keyboard types Corsican.
* **Android / Samsung:** Gboard has a Corsican keyboard. Firefox, Firefox Focus, Thunderbird and VLC ship Corsican.
  `adb shell settings put system system_locales co-FR,fr-FR` (then restart) makes such apps use it, with French
  for the rest.
* A Corsican system interface needs Apple, Google or Samsung — or a free Android system such as LineageOS, whose
  translations are open to volunteers on Crowdin.

## Switch Corsican off and on again

```bash
python3 installer.py --disable
python3 installer.py --enable
```

`--disable` puts every application back to the language it used before, and keeps the built catalogs and
Firefox build so that `--enable` is immediate and needs no rebuild. It restores the Plasma language
setting and the application menu entries, disables the Discord/Vesktop plugin, and makes
`firefox-corsu` start the ordinary system Firefox. Restart the applications; log out and back in for Plasma.
Files you edited yourself are never overwritten: they are reported and left alone.

## Uninstall and backups

Run `python3 installer.py --uninstall` from this source tree or an installed release directory.
Original files and hashes are tracked in Corsu's data directory — `~/.local/share/corsu` (Linux),
`%LOCALAPPDATA%\corsu` (Windows), `~/Library/Application Support/corsu` (macOS) — in `installation.json`
and its `backups/` directory.
Uninstall restores unchanged managed files and only restores app settings still holding the installed value.
Later user edits are preserved and reported for manual review. Qt catalogs installed system-wide are removed
with `pkexec`. The official Vencord installer moves the original Discord archive to `_app.asar`; Corsu also
records a backup and puts the original back in place on uninstall. Source and translated Firefox builds are retained for review.
Never remove backups before uninstalling.

## How the translation works

Python's standard library handles installation, catalog formats and Firefox resources. The only downloads
are Mozilla's French language pack and the pinned Vencord installer, both checksum-verified. There is no
machine translation at runtime and no access to documents, profiles or messages.

* `lexicon.tsv` holds reviewed `English|French|Corsican` rows. A row with an empty English field maps a
  French-only variant.
* `engine.py` translates whole labels only. It matches a label directly, or after masking placeholders
  (`%1`, `%s`, `{ $engine }`, `{ -brand-short-name }`), so one row such as `Restart %1` covers every
  argument. It keeps `&`/`_` keyboard accelerators on the translated letter, accepts either letter case,
  strips French spacing before `:`, `?` and `!`, and translates composed labels such as `Settings — General`
  part by part. A translation is rejected whenever it would change a placeholder or markup contract.
* `corsu.py` writes gettext `.mo` catalogs (contexts and plural pairs included), Qt `.qm` catalogs with
  the hash index `QTranslator` searches, `.desktop` entries, and patched Firefox `.ftl`/`.properties`
  resources, including multiline Fluent patterns and selector variants.
* `plugin/` holds the Vencord plugin, which applies the same matching rules to Discord's interface only,
  never to chat content, channel or user names.
* `coverage.py` exports a review queue from installed application resources, without reading private data.

```bash
python3 -m unittest -v
python3 coverage.py --output missing-labels.json
python3 corsu.py generate
```

For source builds, install Git, Node.js >=22 and pnpm. The first installer run can download the pinned
Vencord revision from `release.json` and build it. After changing `lexicon.tsv` or `plugin/`, rebuild so
Discord and Vesktop pick the change up — the dictionary is compiled into the plugin bundle:

```bash
python3 corsu.py generate
cd Vencord
pnpm install --frozen-lockfile
VENCORD_HASH=7f0c10c node scripts/build/build.mjs --dev --disable-updater
cd ..
python3 installer.py
```

The release script includes the upstream Vencord source at the pinned revision, the custom plugin,
license notices, compiled artifacts and the official installer. It excludes profiles, accounts, settings,
tokens, local backups, `.git`, and `node_modules`:

```bash
python3 package_release.py              # Linux, Windows and macOS archives in releases/
python3 package_release.py --platforms windows
```

## Automated checks

Every push runs [CI](.github/workflows/ci.yml) on Linux, Windows and macOS: the unit tests on Python 3.10 and
3.13, a Vencord build, the three release archives, and end-to-end runs **from each archive** in a throwaway
home directory. These install the Firefox component, start the real translated Firefox headless and read
menu, session-restore and context-menu strings (failing if any is still English or French), switch Corsu off
and on, uninstall and check nothing is left behind. On Linux and Windows they translate Chrome for Testing,
read its error page and `chrome://version` through the DevTools protocol, and check the original pack returns. They also patch a stand-in Discord with the real official
Vencord installer and check the original is restored. Pushing a `v*` tag publishes the release only when all
of this passes. Run the same checks locally with `python3 ci/e2e.py firefox`, `python3 ci/e2e.py discord` and
`CORSU_CHROMIUM=<Chrome for Testing folder> python3 ci/e2e.py chromium` (the variable hides real browsers).

See [CONTRIBUTING.md](CONTRIBUTING.md). Upstream Vencord and its installer retain their original authors
and licenses. Firefox binaries and system gettext/Qt catalogs are built or read locally and are never
redistributed.

## Remaining work

Coverage is counted, never presented as a percentage of the whole interface: the report in
`missing-labels.json` names the specific resource patterns it examined. Open work: many more lexicon rows,
review of the machine-assisted draft rows by Corsican speakers, Discord settings coverage, Plasma widgets
that ship their translations inside QML, Chromium browsers on macOS, and a Corsican spelling dictionary.
