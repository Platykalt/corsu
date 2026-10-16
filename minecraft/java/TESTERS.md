# Minecraft Java 26.3 in Corsican — experimental build for testers

Corsu 0.22.0, not published as a release. This build is **ready to be offered to testers**. It is **not ready to be
announced as stable**: nobody has seen it in the game yet, and no Corsican speaker has reviewed it.

## What it is

- `corsu-minecraft-java-26.3.zip`: resource pack adding the language "Corsu (Corsica)" to Minecraft: Java Edition
  26.3. The Corsu app installs it and selects it in compatible game folders.
- `corsu-minecraft-java-texts-26.3.zip`: optional pack with the splash texts and the End Poem in Corsican. It changes
  them **for every language**; install it by hand only if you want that.

Both are built by the CI of each commit (artifact "releases") and by `python3 tools/minecraft.py build` and
`python3 tools/minecraft.py texts`.

## How the texts were made

All 8,557 texts were **written by an AI model** and then **revised by further AI passes** (harmonisation of terms,
then a review against the reviewed Corsican translations of Mozilla and Patriccollu di Santa Maria è Sichè). AI review
finds mistakes; it does not validate a translation. No Corsican speaker has reviewed them yet
([inventory.tsv](inventory.tsv), column `human_review`).

## What has been checked, automatically

- Every key of Minecraft 26.3 has a Corsican text, with the same arguments, formatting codes and line breaks
  (`tools/minecraft.py check`).
- Minecraft 26.3's own code reads the pack's metadata and language file and renders every text with its arguments
  (`tools/minecraft.py verify`); this is not a game session.
- The zip is rebuilt identically from the sources, and the Corsu installer builds the same bytes.
- The installer's handling of game folders is covered by unit tests on simulated folders: only folders playing 26.3
  (Prism Launcher / MultiMC instance version, or the official launcher's last used profile) are changed; unknown
  versions, a running game, an unreadable `options.txt` or a different file with the pack's name are left alone; other
  packs keep their order; switching off removes only what Corsu added.

## Not checked yet

- **No real game session**: the pack has not been loaded in a running Minecraft, and the installer has not run on a
  real Minecraft installation. Fitting text into buttons is unknown.
- **No speaker review.**

## Known issues and open questions

- Some terms are proposals waiting for a speaker: banner heraldry, animal sounds in subtitles, enchantment names,
  Realms legal texts ([review-batches/](review-batches/), [decisions.md](decisions.md)).
- Corsican is often longer than English: some buttons may overflow.
- Another game version than 26.3 is left alone by the installer; installed by hand, the pack shows as incompatible and
  newer texts stay in English.
- The official launcher's folder is changed only when its last used profile plays 26.3; a folder without profiles is
  left alone (version unknown).
- The splash texts / End Poem pack applies to every language.

## How to test and report

The short path (20 minutes) and the full list of screens: [TESTING.md](TESTING.md), in French
[docs/fr/minecraft-tester.md](../../docs/fr/minecraft-tester.md). Report with the
[translation issue form](https://github.com/Platykalt/corsu/issues/new?template=translation.yml): text seen, screen,
key if you found it, suggestion. A display report fills the `in_game` column only; a language review fills
`human_review` only.
