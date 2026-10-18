# Roadmap candidates: what exists in Corsican, how it would plug in, how big it is

Research note, 16 October 2026. Nothing here is started. Numbers were measured on that date with the methods given;
"to verify" means not tested on a real install. Companion to [en/roadmap.md](en/roadmap.md).

## Method

- **Existing Corsican**: Hosted Weblate API (`/api/components/<project>/<component>/statistics/`,
  `/api/languages/co/`), repository file listings (`gh api …/contents`), Transifex public project pages
  (explore.transifex.com), translations.telegram.org pages.
- **Volume**: source strings counted in each project's template or English file at HEAD on 16 Oct 2026
  (Weblate `total`/`total_words`; `msgfmt --statistics`; `<source>` count in `.ts`; `key = value` lines in `.strings`;
  non-comment lines of Luanti `locale/template.txt`).
- **Reuse**: exact match (after removing `&` accelerators) of each English source string against the English column of
  `lexicon/lexicon.tsv`, `lexicon-upstream.tsv` and `lexicon-mozilla.tsv` (rows with a Corsican value). For the
  Minecraft-like Luanti games: case-insensitive match against the English text of the 4,272 keys in
  `minecraft/bedrock/co_FR.lang` (Bedrock `en_US.lang` 26.50). Exact match underestimates reuse (no fuzzy, no
  terminology), and a match is a draft, not a reviewed translation.

## Summary table

| Candidate | Corsican today | Source volume | Exact reuse | Mechanism | Main blocker |
| --- | --- | ---: | ---: | --- | --- |
| Telegram | Unofficial pack `corsican`, iOS only, ~empty (3/147 in "Log In"; last activity Dec 2021) | Desktop 8,715 · Android 11,565 · iOS 12,358 · macOS 9,059 · Web A 4,398 (+ Web K, Unigram 5,897, Android X 4,799) | 12.6 % (Desktop, 1,094/8,664) | `t.me/setlanguage/<pack>` link, all platforms, synced by server | Platform pack owned by someone else; tdesktop settings encrypted, so no silent apply |
| Luanti engine | None (`co` absent from Weblate and `po/`) | 1,575 strings / 11,160 words (+ Android 9, ContentDB 1,231) | 7.2 % | `language = co` in `minetest.conf`; `.mo` shipped by the engine | Engine `.mo` lives in install dir (read-only for distro/Flatpak) → needs upstream |
| Minetest Game | None (0 `*.co.tr`) | 583 strings (28 templates) | 2.7 % | `<mod>/locale/<mod>.co.tr` | Small audience |
| Mineclonia | None | 4,884 unique strings (163 `.pot`) | **39.3 %** from Corsu Minecraft texts | `.po` per mod | Engine UI stays English without the engine part |
| VoxeLibre | None | 4,249 unique strings (158 templates) | 26.1 % from Corsu Minecraft texts | `.tr` per mod | same |
| SuperTuxKart | None (Transifex, 76 languages, no Corsican) | 1,256 strings / 6.61k words | 14.9 % | Options → UI → Language; `config.xml` | `co` must be requested on Transifex; `.po` read from install `data/po/` |
| KeePassXC | None (Transifex, 59 languages, no Corsican) | 2,501 messages (55 plural) / 11,572 words; Transifex: 23.14k words | 14.6 % | `keepassxc.ini` `[GUI] Language=co` | `.qm` only loaded from install data dir (root/admin; breaks macOS signature) |
| Godot editor | None (`co` absent: Weblate 85 langs, repo 39 `.po`) | Editor 6,422 / 36,662 words; properties 4,306 / 10,000 words; class ref 24,064 / 659,593 words | 6.6 % | `interface/editor/editor_language` in `editor_settings-4.x.tres` | Translations compiled into the binary; only languages ≥ 20 % editor UI are included |
| Minecraft Bedrock | Corsu prototype, never loaded in game | 13,340 keys | 4,272 (32.0 %) already reused | Global resource pack + Language setting | Untested; 9,052 keys need new work |
| VLC | Upstream `co`, by Patriccollu: 3.0.x 4,443/6,203 (71.6 %); master 2,348 + 331 fuzzy / 6,220 (37.7 %); last revision 2017 | 6,220 (master) | 32.7 % (lexicon already imports Patriccollu's work) | Already selectable ("Corsu" in Qt prefs language list) | Upstream Transifex (`vlc-trans`); 1,760 (3.0) / 3,872 (master) strings left |
| Web extensions | `docs/webext.md` not present when this note was written | — | — | — | Read that file when it exists |

## Candidates in detail

### Telegram
- **Exists**: a custom pack named **Corsican / Corsu** at
  [translations.telegram.org/corsican](https://translations.telegram.org/corsican/), link
  [t.me/setlanguage/corsican](https://t.me/setlanguage/corsican). It only covers iOS (`/corsican/android/`,
  `/tdesktop/` etc. redirect away); the "Log In" section has 144 of 147 phrases without a value; the most recent
  translation shown dates from 26 Dec 2021. `/co/`, `/corsu/` are not taken. No official Corsican.
- **Mechanism**: custom packs are created on the platform per app (Android, iOS, tdesktop, macOS, Web K/A…); anyone
  opens the `t.me/setlanguage/<name>` (or `tg://setlanguage?lang=<name>`) link on any device and the app downloads the
  pack and keeps it updated. Telegram Desktop can also load a local `.strings` file (Settings → hold **Shift+Alt** and
  click "Change language"; [desktop.telegram.org/translations](https://desktop.telegram.org/translations)).
- **Automatic apply on desktop**: not cleanly. tdesktop stores settings (including the language pack key) AES-encrypted
  (`storage/localstorage.cpp`: `SettingsKey = CreateLegacyLocalKey(QByteArray(), salt)`, `writeEncrypted`). The key is
  derivable without a passcode, but editing `tdata` from outside is undocumented and could corrupt a session. Feasible
  instead: Corsu opens the `tg://setlanguage?lang=…` link (`xdg-open` / `start` / `open`), the user confirms once.
- **Benefit**: daily messaging on phone and desktop under one pack name. A pack holds a separate string set per app
  (Telegram Desktop, Android, iOS, macOS, Web), each with its own keys, so each one is translated on its own; only the
  install link is shared. Telegram is less used in Corsica than WhatsApp (no data
  found; to verify with users).
- **Maintenance**: Telegram adds strings with every release; the pack falls back to English for missing keys.
- **Blockers**: contact the `corsican` pack owner or create a new pack (e.g. `corsu`) covering all apps; translations
  live on Telegram's server (licence/terms of the platform, not Corsu's repo).

### Luanti (ex-Minetest)
- **Exists**: no `co` in [Hosted Weblate minetest/minetest](https://hosted.weblate.org/projects/minetest/minetest/)
  (79 languages; Catalan 16.6 %, Occitan 16.7 %), none in [luanti-org/luanti `po/`](https://github.com/luanti-org/luanti/tree/master/po),
  [minetest_game](https://github.com/luanti-org/minetest_game), [Mineclonia](https://codeberg.org/mineclonia/mineclonia),
  [VoxeLibre](https://git.minetest.land/VoxeLibre/VoxeLibre).
- **Three layers**: engine (menus, settings: Weblate, `.po` → `.mo`), game (Minetest Game, Mineclonia, VoxeLibre:
  per-mod `locale/` with `.tr` or `.po`, in each game's repo), and third-party mods (same format, each its own repo).
- **Mechanism**: `language = co` in `minetest.conf` (plain text, user-writable). Games installed from ContentDB sit
  in the user's data dir, so Corsu could drop `*.co.tr`/`co.po` there, but a game update erases them; upstreaming is
  the durable route. Whether mod translations work with `language = co` while the engine has no `co.mo`, and whether
  the settings dropdown then shows it: to verify.
- **Reuse**: Mineclonia reuses 39.3 % (1,918 strings) from Corsu's Minecraft texts, the best ratio measured here.
- **Blockers**: engine needs `co` added on Weblate (request to maintainers); Minecraft-derived texts carry
  Corsu's licensing question (`minecraft/java/LICENSING.md`) before contributing them to GPL/CC projects.

### SuperTuxKart
- **Exists**: [Transifex](https://explore.transifex.com/supertuxkart/supertuxkart/) lists 76 languages, no Corsican
  (Sardinian, Breton, Occitan present); no `co.po` in [`data/po`](https://github.com/supertuxkart/stk-code/tree/master/data/po).
- **Mechanism**: Options → User Interface → Language; stored in the user `config.xml`. STK reads `.po` files at
  runtime from its install `data/po/` (needs the file in the release, or write access to the install: to verify).
- **Volume**: 1,256 strings / 6.61k words, small. [Process](https://supertuxkart.net/Translating_STK): join the team,
  request the language.

### KeePassXC
- **Exists**: [Transifex](https://explore.transifex.com/keepassxc/keepassxc/) 59 languages, no Corsican; no
  `keepassxc_co.ts` in [`share/translations`](https://github.com/keepassxreboot/keepassxc/tree/develop/share/translations).
- **Mechanism**: `[GUI] Language=co` in `keepassxc.ini`. The language list and `.qm` files come only from the install
  data dir (`src/core/Translator.cpp`, `Resources.cpp`), so a local add needs root on Linux, admin on Windows, and
  modifying the app bundle on macOS (breaks signing). Upstream is the realistic route.
- **Benefit**: security tool used daily by some; small Corsican audience; texts are technical (crypto, databases).

### Godot editor
- **Exists**: no `co` in [Hosted Weblate godot-engine](https://hosted.weblate.org/projects/godot-engine/) (editor 85
  languages; Catalan and Italian 100 %).
- **Mechanism**: `interface/editor/editor_language` in `editor_settings-4.x.tres` (text). Translations are compiled
  into the binary, and `editor/SCsub` only includes languages with ≥ 20 % editor UI (≥ 10 % class reference), so
  nothing can be added locally: ~1,285 editor strings translated upstream before it ships.
- **Benefit**: developers and students only; high volume, low reuse (6.6 %). Not a priority.

### Minecraft Bedrock
- Prototype in `minecraft/bedrock/` (see its `STATUS.md`): 4,272 / 13,340 keys reused from Java, 0 errors offline,
  **never loaded in the game**. Remaining 9,052 keys include `howtoplay` 778, `store` 544, `commands` 919, `options`
  1,114. Next step is the manual test on Windows/Android, not more translation.

### VLC (completion)
- Mechanism and sources: [apps-research.md](apps-research.md). Figures below were measured directly.
- Upstream already ships Corsican and lists it in the interface (`{ "co", "Corsu" }` in Qt
  `simple_preferences.cpp`). [3.0.x `po/co.po`](https://github.com/videolan/vlc/blob/3.0.x/po/co.po): 4,443 / 6,203
  (71.6 %); [master `po/co.po`](https://github.com/videolan/vlc/blob/master/po/co.po): 2,348 + 331 fuzzy / 6,220. Last
  translator revision Dec 2017 (Patriccollu). The missing strings can be prepared now in Corsu's translation memory
  (`tools/tm.py`); sending them upstream through VLC's Transifex team, ideally with Patriccollu, is a later step and
  does not block that work. Measured reuse on 3.0.x with the context-aware memory: 10 exact compatible reuses, 70
  suggestions to review, 1,750 still to translate, so most of it is new translation, whatever the lexicon's size.
- Benefit: no install work for Corsu at all; every finished string reaches all VLC users who pick Corsican.

### Web extensions
- Assessment and prototype: [webext.md](webext.md).

## Recommendation: three projects, one at a time

Do not open more than one of these at once; each finishes with a measured state before the next starts.

1. **Minecraft Bedrock: test, then decide** (first). Work is already done and only an in-game test on one device is
   missing; it reaches the largest young audience of any candidate. If the test passes, translate in order of
   visibility (`options`, `selectWorld`, menus) rather than `howtoplay`/`store`. If it fails, stop and record why.
2. **Telegram pack covering Desktop + Android + iOS** (second). Highest daily use; one pack name and link for every
   app, which updates itself, but each app's string set is translated separately, and Corsu's install step is just opening a link. Start by contacting the `corsican` pack owner
   (avoid two competing packs); begin with Desktop's 8,715 strings, of which 1,094 match a lexicon entry by text alone (a preliminary estimate,
   before the context check that `tools/tm.py` applies), and the
   most visible sections (chat list, settings, login). No encrypted-file hacks.
3. **Luanti engine upstream, then Mineclonia** (third). Engine is small (1,575 strings) and goes through Weblate, so
   it ships to everyone; Mineclonia has the best reuse measured (39 % from Corsu's Minecraft texts), which also gives
   the Minecraft work a free, open home. Settle the Minecraft-text licensing before contributing reused strings.

Not now: Godot (volume, compiled-in, low reuse), KeePassXC and SuperTuxKart (fine small upstream contributions for a
second translator, but neither has a local install path for Corsu), VLC completion (best handled with Patriccollu,
who maintains it upstream).
