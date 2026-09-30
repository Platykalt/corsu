# Corsu

Corsican interface translations for **Linux, KDE Plasma, Firefox, Discord with Vencord, and Vesktop**.
GPL-3.0-or-later: you can share, modify and redistribute this project, including its source.

**This is a work in progress, not a complete Corsican language pack.** Common controls, menu labels and
dialog buttons are translated locally from a reviewed lexicon. Unknown labels keep their original French
or English text. Websites, chat messages, file names, people's names and typed text are never translated.
Application names in the Plasma launcher stay as their vendors publish them. The lexicon holds draft
translations and welcomes review by Corsican speakers.
Windows, macOS, Flatpak/Snap Firefox and non-KDE desktop environments are not supported by this installer.

## Install

Extract the Linux x86_64 release archive. Install Python 3, Firefox and native Discord or Vesktop using
your distribution's software manager. For desktop translation, KDE Plasma and French gettext catalogs
must already be installed. The installer detects supported integrations; it does not install a new desktop.

From the extracted directory:

```bash
./install.sh
```

The installer lists the changes and asks you to accept them. It copies its code and bundled builds into
`~/.local/share/corsu/releases/`, so the downloaded archive can be removed after installation.
The Linux release bundles Vencord's source and a custom build; Node.js is unnecessary for installing it.
The official Vencord installer is checksum checked before execution and may access GitHub for update checks.
System-owned Discord installations may request administrator authentication through `pkexec`.
Close Discord/Firefox before installing, then reopen them afterward. Log out and back in to activate
the Plasma interface language. Updates to Discord can remove its patch: rerun the installer after reviewing
the installation status. Firefox's launcher rebuilds its translated copy after system Firefox updates.
Firefox's security preferences and extension signature checks remain enabled.

## What each component changes

| Component | Effect |
| --- | --- |
| `desktop` | User gettext catalogs (`~/.local/share/locale/co`), Qt catalogs for KDE framework dialogs, Plasma interface language `co:fr`, translated application menu entries |
| `firefox` | A translated local copy of system Firefox plus a user launcher, keeping your existing profile |
| `discord` | Patches native Discord through the official Vencord installer and enables the bundled Corsu plugin |
| `vesktop` | Points Vesktop at the custom Vencord build and enables the Corsu plugin |
| `qt` | Copies Corsican Qt catalogs into `/usr/share/qt6/translations` so Qt's own buttons and file choosers are translated. Requires administrator authentication and is removed again by `--uninstall` |

Optional commands:

```bash
python3 installer.py --dry-run
python3 installer.py --components firefox desktop
python3 installer.py --components discord --discord-path /path/to/discord
python3 installer.py --yes
python3 corsu.py status
```

`--yes` explicitly accepts the displayed plan. No settings are changed by `--dry-run` or by declining consent.
Use `~/.local/bin/firefox-corsu` to launch the translated browser. Explicit `-P`, `-profile` or
`-ProfileManager` arguments override profile discovery. Ambiguous profiles open Firefox's profile chooser.
An already running ordinary Firefox may keep its original interface until you fully quit and reopen it.

Vencord automatic updates are disabled to protect the custom plugin; update/rebuild Corsu manually.
Vencord is a third-party Discord client modification. Read its [official documentation](https://docs.vencord.dev/installing/).
Corsu does not translate chat messages or provide a message translation service.

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
Original files and hashes are tracked in `~/.local/share/corsu/installation.json` and its `backups/` directory.
Uninstall restores unchanged managed files and only restores app settings still holding the installed value.
Later user edits are preserved and reported for manual review. Qt catalogs installed system-wide are removed
with `pkexec`. The original Discord archive is retained by the official installer as `resources/_app.asar`;
Corsu also records a backup. Source and translated Firefox builds are retained for review.
Never remove backups before uninstalling.

## How the translation works

Python's standard library handles installation, catalog formats and Firefox resources — no network access,
no machine translation and no access to documents, profiles or messages.

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
python3 package_release.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Upstream Vencord and its installer retain their original authors
and licenses. Firefox binaries and system gettext/Qt catalogs are built or read locally and are never
redistributed.

## Remaining work

Coverage is counted, never presented as a percentage of the whole interface: the report in
`missing-labels.json` names the specific resource patterns it examined. Open work: many more lexicon rows,
sentence-level translations, Firefox strings that only exist in a language pack for a newer Firefox release
(the interface then falls back to English), Discord settings coverage, and Plasma widgets that ship their
translations inside QML.
