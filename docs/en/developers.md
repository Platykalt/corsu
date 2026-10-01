# Development

[Français](../fr/developpeurs.md)

## Layout

```
.github/            CI workflow, issue templates, release notes
docs/               docs/fr (French) and docs/en (English): guides for computers and phones, Discord, compatibility
install/            Install for Windows.cmd, Install for macOS.command, Install for Linux.sh (placed at the
                    top of each release archive), and get.sh / get.ps1 for one-line installs
lexicon/            the translations: lexicon.tsv (written for Corsu), lexicon-mozilla.tsv and
                    lexicon-upstream.tsv (reviewed translations from other projects, loaded first)
src/                the program: installer.py (setup), app.py (the Corsu window), corsu.py (Firefox, KDE,
                    Discord, shortcuts), chromium.py (Chromium browsers), engine.py (lookup and file formats),
                    release.json (version, pinned Vencord revision, installer checksums)
src/discord-plugin/ the Vencord plugin that translates Discord
tests/              unit tests; tests/e2e/ holds the end-to-end checks the CI runs on each system
tools/              packaging, coverage report, import of translations from other projects
vendor/             pinned third-party files
```

Only Python's standard library is used. Building the Discord plugin needs Node.js 22 or newer and pnpm.

## Lexicon

Each line of a `.tsv` file in `lexicon/` is `English|French|Corsican`. Either source may be empty. The engine
loads `lexicon-mozilla.tsv`, then `lexicon-upstream.tsv`, then `lexicon.tsv`; the first translation found for a
label wins, so reviewed translations take precedence over drafts.

Placeholders are matched by position: one row `Restart %1|Redémarrer %1|Rilancià %1` also covers
`Redémarrer { -brand-short-name }` in Firefox and `Redémarrer $1` in Chrome. The engine refuses a translation
that would drop or add a placeholder or a markup tag.

`tools/import_translations.py` downloads the Corsican translations of Firefox for Android and iOS, Mozilla VPN,
Thunderbird for Android, VLC for Android, Audacity, Poedit, WinMerge and Notepad++, and rewrites the two
reviewed files. `tools/coverage.py --output missing-labels.json` lists the labels still untranslated on this
computer.

## Tests

```sh
python3 -m unittest discover -s tests -t .
python3 tests/e2e/e2e.py firefox     # installs in a throwaway home, starts Firefox and reads its menus
python3 tests/e2e/e2e.py discord     # patches a stand-in Discord with the official Vencord installer
CORSU_CHROMIUM=/path/to/chrome-for-testing python3 tests/e2e/e2e.py chromium
```

`CORSU_CHROMIUM` replaces every installed Chromium browser with the given folder, so the test never touches a
real browser. `CORSU_FIREFOX` does the same for Firefox.

## Continuous integration

[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) runs on every push:

1. unit tests on Linux, Windows and macOS with Python 3.10 and 3.13;
2. a Vencord build and the three release archives;
3. on each system, from that system's archive: install, start the translated Firefox and Chrome for Testing,
   read their interface text, switch off, switch on, uninstall, and check that nothing is left behind; then
   patch a stand-in Discord with the official Vencord installer and check that it is restored.

Pushing a tag `vX.Y.Z` that matches `src/release.json` publishes a GitHub release with the archives, but only when
all of the above passes.

## Making a release

1. Update `version` in `src/release.json` and add an entry to `CHANGELOG.md`.
2. Commit, then `git tag vX.Y.Z && git push origin vX.Y.Z`.

To build the archives locally instead: check out Vencord at the pinned revision into `Vencord/`, build it
(`PYTHONPATH=src python3 -c "import installer; installer.prepare_build()"`), then run
`python3 tools/package_release.py`.
