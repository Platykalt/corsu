# Phone dictionary: release checklist

What to change when a Corsu release carries new Keyman dictionary packages (here: 0.26, packages version 1.1).
Nothing below is done before the release: until then, the guides and the window describe the published package
(`corsu-keyboard.kmp` version 1.0, shown as `platykalt.co.corsu`, from Corsu 0.25.1) and show the next version's
packages apart, without a release download.

## Three version numbers, kept apart

| Number | Where it is set | 0.25.1 (published) | 0.26 (candidate) |
| --- | --- | --- | --- |
| Corsu version | `src/release.json`, tag `vX.Y.Z` | 0.25.1 | 0.26.0 |
| Dictionary package version (what Keyman shows as "Dictionary version") | `keyboard/*/source/*.kps`, `kmp.json` → `info.version` | 1.0 | 1.1 (all three packages) |
| Keyman app version the guides follow | the guides' introduction | 18.0.254 (stable) | 18.0.254 (stable); 19.0 is beta |

The guides give the package version (1.1) next to the Corsu version that published it; they must not say "Corsu
1.1". If the stable Keyman changes before the release (19.0 out of beta), the automatic-correction sections of the
guides and `ph_auto` in `src/app/texts-phone.js` need rewriting first.

## 1. Release assets

- [ ] The release carries `corsu-keyboard.kmp`, `corsu-keyboard-cismuntincu.kmp`, `corsu-keyboard-pumuntincu.kmp`,
      each with its `.sha256`, under exactly these names (Keyman takes the package id from the file name).
- [ ] After publishing, for each of the three, a HEAD request on
      `https://github.com/Platykalt/corsu/releases/latest/download/<file>` (following redirects) gives 200, and the
      downloaded file's SHA-256 equals the `.sha256` asset and the CI artifact's.
- [ ] Unzip each downloaded `.kmp`: `kmp.json` → `info.version` is `1.1`, `info.name` and `lexicalModels[0].name`
      are "Corsu", "Corsu – Cismuntincu (experimental)", "Corsu – Pumuntincu (experimental)", and
      `lexicalModels[0].id` is `platykalt.co.corsu`, `platykalt.co.corsu_cismuntincu`,
      `platykalt.co.corsu_pumuntincu`, all for language `co`.

## 2. Guides (`docs/fr/telephone/`, `docs/en/phone/`)

In `android.md` and `iphone.md`, French and English (four files):

- [ ] **First `corsu:phone-variants` marker** (section « Dictionnaires disponibles » / "Available dictionaries"):
      replace the published row (1.0, `platykalt.co.corsu`, the 0.25.1 defects) by the three rows of the « Dans la
      prochaine version » / "In the next version" table, each with version 1.1 "(publié avec Corsu 0.26.0)" /
      "(published with Corsu 0.26.0)", its `releases/latest/download/<file>` link and its `.sha256` link. Then remove
      the « Dans la prochaine version » sub-section and the sentence that points to the candidate section.
- [ ] Step 5 « Vérifiez le dictionnaire » / "Check the dictionary": the published name becomes « Corsu » (not
      `platykalt.co.corsu`); drop the parenthesis about the next version.
- [ ] **Second `corsu:phone-variants` marker** (« Choisir un dictionnaire régional » / "Choosing a regional
      dictionary"): "With the next version, two experimental dictionaries will prefer…" becomes present tense, with
      links to the two published files; drop the paragraph that points to the candidate archive.
- [ ] **`corsu:phone-casing` marker** (« Majuscules et début de phrase » / "Capitals and sentence start"): the bullet
      « Les suggestions perdent la majuscule… » / "Suggestions lose the capital…" becomes: suggestions keep the case
      typed, and are capitalised at a sentence start, since Corsu 0.26.0 (package 1.1); someone who still has the 1.0
      package should update (link to « Mettre à jour » / "Updating").
- [ ] Section « Essayer le dictionnaire de la prochaine version (candidate) » / "Trying the next version's
      dictionary (candidate)": remove it, or keep it only if a newer candidate exists, with that run's artifact link
      and expiry date. Never leave an expired artifact link.
- [ ] « Revenir au dictionnaire publié »: the published name and version become « Corsu », 1.1.
- [ ] `essai-5-minutes.md`: the « Publié » column becomes the 1.1 expectations (identical to « Candidat »), or
      the two columns merge; update the expiry date or remove the candidate artifact link.
- [ ] Keep the markers (with their comment updated to describe the new state) for the next release.

## 3. README.md (owned by the lead / the README agent)

Lines to change, found by their markers:

- [ ] French part, `<!-- corsu:phone-variants:fr … -->`: the sentence « Dictionnaire publié … environ 17 000 mots
      corses courants » lists the three published files (general, Cismuntincu, Pumuntincu) with their download links
      and the general dictionary's real word count (about 13,000: 12,976 entries in
      `keyboard/platykalt.co.corsu/source/wordlist.tsv`, against 16,949 in 0.25.1); the sentence « Dans la prochaine version (pas encore publiée) :
      … » is removed or rewritten as what the published files do (keeps capitals; two experimental regional
      preferences).
- [ ] English part, `<!-- corsu:phone-variants:en … -->`: same change ("Published dictionary …", "In the next
      version (not published yet): …").

## 4. The window's « Sur téléphone » page

- [ ] `src/app/phone.js`: move the two entries of `COMING` into `VARIANTS` (after the general one) and leave
      `COMING = []`. The heading « Dans la prochaine version » disappears by itself when `COMING` is empty.
- [ ] Decide whether the variants get their own download links in the window: today only `VARIANTS[0]` is a
      download (`RELEASE + VARIANTS[0].file`); the variants are only listed. If they get links, they must use
      `RELEASE + file`, never an artifact.
- [ ] `src/app/texts-phone.js` (co, fr, en): `ph_coming_text` is no longer shown (keep or delete the key in all three
      languages together); `ph_variant_general_detail` gives no word count on purpose, keep it that way or give the
      published one; check `ph_a5` (the dictionary shows as « Corsu »).
- [ ] `tests/test_phone.py`, `ReleasedFilesTests.test_only_the_released_dictionary_is_offered`: expect the three
      files in `VARIANTS` and an empty `COMING`; allow the variants' `releases/latest/download/` links in the guides
      and README. `RenderTests.test_steps_and_texts` checks "In the next version": update it.
- [ ] The QR codes point to the guides on `main` and do not change.

## 5. Release notes and continuity (owned by the lead)

- [ ] `.github/RELEASE_NOTES.md`: the "Downloads" table names the three dictionary files, version 1.1, and that
      they are used on their own (no Corsu installation on a computer).
- [ ] `CHANGELOG.md`, `docs/continuite.md`: the published package version (1.1) and what was really tested
      (engine in CI, Android 14 emulator; a physical phone or an iPhone only if someone did run
      `docs/fr/telephone/essai-5-minutes.md` on one).

## 6. After publishing

- [ ] Download `corsu-keyboard.kmp` from `releases/latest/download/` on a phone or an emulator, install it over the
      1.0 package, restart Keyman, and check that Keyman shows « Corsu », version 1.1.
- [ ] Run `HOME=$(mktemp -d) python3 -m unittest discover -s tests -t .` on `main`.

## Downloads table for the 0.26 release notes (`.github/RELEASE_NOTES.md`)

Replace the table at the top of the French part with this one (the English part gets the same rows, headings
"Downloads" | "For" | "File" | "Then", guides under `docs/en/phone/`):

| Pour | Fichier | Ensuite |
| --- | --- | --- |
| Windows 10 ou 11 | `corsu-windows.zip` | décompresser, double-cliquer sur `Install for Windows.cmd` |
| macOS | `corsu-macos.tar.gz` | double-cliquer sur `Install for macOS.command` |
| Linux | `corsu-linux.tar.gz` | lancer `./"Install for Linux.sh"` |
| Téléphone Android ou iPhone (clavier Keyman) | `corsu-keyboard.kmp` | dictionnaire corse pour Keyman, **utilisable seul** : aucune installation sur ordinateur. Paquet 1.1, nom dans Keyman : « Corsu ». Guides : [Android](https://github.com/Platykalt/corsu/blob/main/docs/fr/telephone/android.md), [iPhone](https://github.com/Platykalt/corsu/blob/main/docs/fr/telephone/iphone.md) |
| Téléphone, variante régionale (expérimentale) | `corsu-keyboard-cismuntincu.kmp` ou `corsu-keyboard-pumuntincu.kmp` | même vocabulaire, préférence pour les formes du Cismonte ou du Pumonte (361 mots pondérés autrement, couverture partielle) ; paquet 1.1. Sous Android, un seul dictionnaire actif par langue : désinstaller l'autre puis relancer Keyman |
| Minecraft Java 26.3, sans l'application | `corsu-minecraft-java-26.3.zip` | pack de ressources : Options › Packs de ressources, l'activer, puis Options › Langue › Corsu ; pack facultatif des textes d'accueil et de fin : `corsu-minecraft-java-texts-26.3.zip`. Les autres versions (1.6.1 → 26.2) : par l'application Corsu ([versions et vérifications](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) |

Chaque fichier a sa somme de contrôle `.sha256`. Keep the existing tag scheme: no separate keyboard release (it would
change `releases/latest` and the app's update check).
