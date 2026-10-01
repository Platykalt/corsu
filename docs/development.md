# Development

## Layout

```
src/              Python code: installer.py (setup), corsu.py (Firefox, KDE, Discord, launchers),
                  chromium.py (Chromium browsers), engine.py (lexicon lookup and file formats)
lexicon/          the translations: lexicon.tsv (drafts), lexicon-mozilla.tsv and lexicon-upstream.tsv
                  (reviewed translations from other projects, loaded first)
discord-plugin/   the Vencord plugin that translates Discord's interface
tests/            unit tests (python -m unittest discover -s tests -t .)
ci/               end-to-end checks used by the CI, also runnable locally
tools/            packaging, coverage report, import of upstream translations
docs/             documentation
vendor/           pinned third-party files (Vencord installer source)
install.sh, install.cmd   start the installer from an extracted release
get.sh, get.ps1           one-line download-and-install scripts
release.json      version, pinned Vencord revision and installer checksums
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
python3 ci/e2e.py firefox     # installs in a throwaway home, starts Firefox and reads its menus
python3 ci/e2e.py discord     # patches a stand-in Discord with the official Vencord installer
CORSU_CHROMIUM=/path/to/chrome-for-testing python3 ci/e2e.py chromium
```

`CORSU_CHROMIUM` replaces every installed Chromium browser with the given folder, so the test never touches a
real browser. `CORSU_FIREFOX` does the same for Firefox.

## Continuous integration

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every push:

1. unit tests on Linux, Windows and macOS with Python 3.10 and 3.13;
2. a Vencord build and the three release archives;
3. on each system, from that system's archive: install, start the translated Firefox and Chrome for Testing,
   read their interface text, switch off, switch on, uninstall, and check that nothing is left behind; then
   patch a stand-in Discord with the official Vencord installer and check that it is restored.

Pushing a tag `vX.Y.Z` that matches `release.json` publishes a GitHub release with the archives, but only when
all of the above passes.

## Making a release

1. Update `version` in `release.json` and add an entry to `CHANGELOG.md`.
2. Commit, then `git tag vX.Y.Z && git push origin vX.Y.Z`.

To build the archives locally instead: check out Vencord at the pinned revision into `Vencord/`, build it
(`PYTHONPATH=src python3 -c "import installer; installer.prepare_build()"`), then run
`python3 tools/package_release.py`.
