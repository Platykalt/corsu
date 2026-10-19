# Phone dictionary: release checklist

What to change when a Corsu release carries new Keyman dictionary packages (here: 0.27.0, packages version 1.2).
The published release is still 0.26.0 (packages 1.1, 13,213 words each); nothing in this list publishes anything.
On `next-0.27`, the guides, `essai-5-minutes.md` and `.github/RELEASE_NOTES.md` already describe 0.27.0 ("from Corsu
0.27.0") and say what 0.26.0 carried; they reach `main` only with the release.

## Three version numbers, kept apart

| Number | Where it is set | 0.26.0 (published) | 0.27.0 (candidate) |
| --- | --- | --- | --- |
| Corsu version | `src/release.json`, tag `vX.Y.Z` | 0.26.0 | 0.27.0 |
| Dictionary package version (what Keyman shows as "Dictionary version") | `keyboard/*/source/*.model.kps` (`<Version>`), `kmp.json` → `info.version` | 1.1 | 1.2 (all three packages) |
| Words per package (`tools/count_kmp.py`, entries of the built `.model.js`) | built from `keyboard/data` | 13,213 (13,201 ignoring case) | 19,341 (19,308 ignoring case), to recount after any keyboard change |
| Keyman app version the guides follow | the guides' introduction | 18.0.254 (stable) | 18.0.254 (stable); 19.0 is beta |

The guides give the package version next to the Corsu version that carries it; they must not say "Corsu 1.2". If
the stable Keyman changes before the release (19.0 out of beta), the automatic-correction sections of the guides and
`ph_auto` in `src/app/texts-phone.js` need rewriting first.

## Where the keyboard figures live

Count from the packages, never from a source list:

```sh
python3 tools/build_keyboard.py --package
python3 -I tools/count_kmp.py keyboard/build/corsu-keyboard.kmp keyboard/build/corsu-keyboard-cismuntincu.kmp \
    keyboard/build/corsu-keyboard-pumuntincu.kmp
```

Then, if the count or the package version changes, update every place below (search for the old figure in both
spellings, `19 341` and `19,341`):

| File | What it holds |
| --- | --- |
| `docs/fr/telephone/android.md`, `docs/fr/telephone/iphone.md` | first `corsu:phone-variants:fr` comment (version, count, published state); table « Dictionnaires disponibles » (version column ×3, « 19 341 mots » in the general row); sentence under it (0.26.0: 1.1, 13 213 mots); « Mettre à jour » (version to check); second `corsu:phone-variants:fr` comment; « Revenir au dictionnaire général » (version); « Correction automatique » (« environ 6 000 formes ») |
| `docs/en/phone/android.md`, `docs/en/phone/iphone.md` | the same places in English (`corsu:phone-variants:en`, "19,341 words", "about 6,000 more forms") |
| `docs/fr/telephone/essai-5-minutes.md` | the comment above « Quel fichier essayer », « Version du dictionnaire », the « Attendu (paquet 1.2) » heading, rows 2, 3 and 13, « Variantes régionales » |
| `.github/RELEASE_NOTES.md` | both "Downloads" tables (« Paquet 1.2 », « paquet 1.2 » / "Package 1.2", "package 1.2"); the `corsu:keyboard-figures` comment and the « Clavier sur téléphone » / "Phone keyboard" bullet of « Nouveautés de la 0.27.0 » / "New in 0.27.0" (19 341 / 19,341, 6 012 / 6,012, version 1.2) |
| `keyboard/*/source/*.model.kps` | `<Version>` (1.2) |
| `keyboard/data/REVIEW.md`, `keyboard/data/audit/stats.json` | counts recorded with the keyboard data (owned by the keyboard work) |
| `README.md`, `CHANGELOG.md`, `docs/continuite.md` | owned by the lead: README `corsu:phone-variants` sentences (still 1.1 / 13,213: the published state), CHANGELOG 0.27.0 entry (13,213 in the published 1.1 packages, 19,341 in 1.2), continuity notes |

The regional variants' "361 words weighted differently" is the count of regional source rows; it did not change
between 1.1 and 1.2.

## 1. Release assets

- [ ] The release carries `corsu-keyboard.kmp`, `corsu-keyboard-cismuntincu.kmp`, `corsu-keyboard-pumuntincu.kmp`,
      each with its `.sha256`, under exactly these names (Keyman takes the package id from the file name).
- [ ] After publishing, for each of the three, a HEAD request on
      `https://github.com/Platykalt/corsu/releases/latest/download/<file>` (following redirects) gives 200, and the
      downloaded file's SHA-256 equals the `.sha256` asset and the CI artifact's.
- [ ] Unzip each downloaded `.kmp`: `kmp.json` → `info.version` is `1.2`, `info.name` and `lexicalModels[0].name`
      are "Corsu", "Corsu – Cismuntincu (experimental)", "Corsu – Pumuntincu (experimental)", and
      `lexicalModels[0].id` is `platykalt.co.corsu`, `platykalt.co.corsu_cismuntincu`,
      `platykalt.co.corsu_pumuntincu`, all for language `co`.
- [ ] `python3 -I tools/count_kmp.py` on the three downloaded files gives the count written in the guides and the
      release notes (19,341 at the time of writing).

## 2. Guides (`docs/fr/telephone/`, `docs/en/phone/`)

Same files and names as 0.26.0, so no row moves and no link changes; only versions and counts.

- [x] Table « Dictionnaires disponibles » / "Available dictionaries": version 1.2 « (à partir de Corsu 0.27.0) » /
      "(from Corsu 0.27.0)", 19,341 words; a sentence says that 0.26.0 carried 1.1 (13,213 words).
- [x] « Mettre à jour » / "Updating" and « Revenir au dictionnaire général »: version 1.2, with 1.1 for 0.26.0.
- [x] Sections that said « prochaine version de Corsu, pas encore publiée » / "next version of Corsu, not published
      yet" for the 1.2 behaviour (punctuation, apostrophe, added forms) now say "from Corsu 0.27.0".
- [x] `essai-5-minutes.md`: expectations for 1.2, and a row for punctuation already written after the word.
- [ ] Before tagging: recount (section above) if the keyboard changed after these edits.
- [ ] Keep the `corsu:phone-variants` and `corsu:phone-casing` markers, with their comments describing the state.

## 3. README.md (owned by the lead)

- [ ] French and English `corsu:phone-variants` sentences: package 1.2 from Corsu 0.27.0 and the word count counted
      in the release candidate's packages (`tools/count_kmp.py`), instead of 1.1 / 13,213.

## 4. The window's « Sur téléphone » page

- [ ] `src/app/phone.js`: nothing to move (`VARIANTS` already lists the three files, `COMING` is empty); downloads
      stay `RELEASE + file`, never an artifact.
- [ ] `src/app/texts-phone.js` (co, fr, en): carries no package version or word count; keep it that way.
- [ ] `tests/test_phone.py` needs no change for 0.27.0 (same three released files, empty `COMING`).

## 5. Release notes and continuity

- [x] `.github/RELEASE_NOTES.md`: « Nouveautés de la 0.27.0 » / "New in 0.27.0" written from the CHANGELOG entry,
      the 0.26.0 sections become « Rappel » / "Earlier", the "Downloads" tables say package 1.2.
- [ ] `CHANGELOG.md`, `docs/continuite.md` (lead): the published package version (1.2) and what was really tested
      (engines in CI, Android 14 emulator; a physical phone or an iPhone only if someone did run
      `docs/fr/telephone/essai-5-minutes.md` on one).

## 6. After publishing

- [ ] Download `corsu-keyboard.kmp` from `releases/latest/download/` on a phone or an emulator, install it over the
      1.1 package, restart Keyman, and check that Keyman shows « Corsu », version 1.2.
- [ ] Run `HOME=$(mktemp -d) python3 -m unittest discover -s tests -t .` on `main`.

Keep the existing tag scheme: no separate keyboard release (it would change `releases/latest` and the app's update
check).
