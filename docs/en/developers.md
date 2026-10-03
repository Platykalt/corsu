# Development

[Français](../fr/developpeurs.md)

## Layout

```
.github/            CI workflow, issue templates, release notes
docs/               docs/fr (French) and docs/en (English): guides for computers and phones, Discord, compatibility
keyboard/           the Keyman word prediction project; tools/build_keyboard.py fills its word list and builds
                    corsu-keyboard.kmp
install/            Install for Windows.cmd, Install for macOS.command, Install for Linux.sh (placed at the
                    top of each release archive), and get.sh / get.ps1 for one-line installs
lexicon/            the translations: lexicon.tsv (written for Corsu), lexicon-mozilla.tsv and
                    lexicon-upstream.tsv (reviewed translations from other projects, loaded first)
src/                the program: installer.py (setup), app.py (the Corsu window), corsu.py (Firefox, KDE,
                    Discord, shortcuts), chromium.py (Chromium browsers), engine.py (lookup and file formats),
                    release.json (version, pinned Vencord revision, installer checksums)
src/app/            the Corsu app's page (index.html) and its icon
src/discord-plugin/ the Vencord plugin that translates Discord
src/firefox/        corsu.cfg (Firefox autoconfig) and the module that completes Google's labels
tests/              unit tests; tests/e2e/ holds the end-to-end checks the CI runs on each system
tools/              packaging, coverage report, import of translations from other projects
vendor/             pinned third-party files
```

Only Python's standard library is used; the window uses pywebview when it is present. Building the Discord plugin
needs Node.js 22 or newer and pnpm.

Published archives carry their own Python (`runtime/<processor>/python`, from
[python-build-standalone](https://github.com/astral-sh/python-build-standalone), pinned with its SHA-256 in
`src/release.json`), without Tk, IDLE, pip and the tests; the Windows and macOS ones have pywebview and its bindings.
`tools/package_release.py --no-runtime` builds archives without it. Run from that Python, the installer copies it once
to `runtime/<version>` in the data folder, which the shortcuts then use.

The Corsu app (`src/app.py`) is a small web server bound to 127.0.0.1 at the fixed address `http://localhost:7744`
(the next free port when another program holds it). `src/window.py` shows it in a window of its own: pywebview when
present, WebKitGTK on Linux, otherwise the app window of Edge, Chrome or Chromium, and as a last resort a browser tab.
The same address also opens in any browser while Corsu runs. Only Corsu's page can drive it: the server refuses any
other `Host` (against DNS rebinding), requires the `X-Corsu` header, which a page from another site cannot send
without a permission the server never grants, refuses a foreign `Origin`, and on Linux checks that the connection
comes from the same account. Every action runs `installer.py` in a child process and the page shows its output. The
server stops 30 seconds after the window closes, or ten minutes after the last visit in a browser. `app.py --browser`
opens a tab instead of the window, `app.py --no-browser` only serves the address, `app.py --text` is the terminal menu.

## Lexicon

Each line of a `.tsv` file in `lexicon/` is `English|French|Corsican`. Either source may be empty. The engine
loads `lexicon-fixes.tsv`, then `lexicon-mozilla.tsv`, then `lexicon-upstream.tsv`, then `lexicon.tsv`; the first
translation found for a label wins. Reviewed translations therefore take precedence over drafts, and
`lexicon-fixes.tsv` holds the few corrections that must beat an imported translation (for example a word that means
something else in Discord).

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
   patch a stand-in Discord with the official Vencord installer and check that it is restored, this time with the
   archive's own Python, checking its copy, the shortcuts and what the window needs.

Pushing a tag `vX.Y.Z` that matches `src/release.json` publishes a GitHub release with the archives, but only when
all of the above passes.

## Making a release

1. Update `version` in `src/release.json` and add an entry to `CHANGELOG.md`.
2. Commit, then `git tag vX.Y.Z && git push origin vX.Y.Z`.

To build the archives locally instead: check out Vencord at the pinned revision into `Vencord/`, build it
(`PYTHONPATH=src python3 -c "import installer; installer.prepare_build()"`), then run
`python3 tools/package_release.py`.
