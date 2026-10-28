# Changelog

## 0.28.3 (unreleased)

From 0.28.2 (`a8a9f69`, tag `v0.28.2`). Translator revision `2026-10-notice-1`. Structures read in Discord's public
web client (build `web.33a8a649a2fda558`, 2026-10-28) and checked in simulated pages with the built plugin
(`check_discord_regressions.py`, scenarios D1-D5), not in the real Discord app.

- **Discord, pin notice still in French** ("… a épinglé un message dans ce salon. Voir tous les messages épinglés."):
  in the message list, Discord draws every system message inside the same `<div id="message-content-…">` as a
  person's message (SystemMessage renders the notice as MessageContent's children). That wrapper is a content rule,
  so 0.28.2 never read the notice; its tests modelled the notice without the wrapper. A wrapper whose message record
  is a pin (type 6) or a group member added or removed (types 1, 2) is now read like the rest of the list: names,
  links and the time stay as they are, only the notice's own phrases change (Corsu usage, unchanged rows). A person's
  message with the same words stays as written. Renamed group or channel notices (types 4, 5) stay protected: their
  new name is a bare text.

## 0.28.2 (2026-10-27)

From 0.28.1 (`ae8890b`, tag `v0.28.1`). Translator revision `2026-10-composer-2`. Structures read in Discord's public
web client (build `web.ad0b95d8568e0f6b`, 2026-10-27) and checked in simulated pages with the built plugin
(`check_discord_built.py`), not in the real Discord app.

- **Discord, message composer**: "Envoyer un message à @Ron" (key 4c+CAx) was back in French since 0.28.0. Discord's
  composer draws this placeholder in a `<div data-slate-placeholder>` beside the editor, outside any content area;
  the search-field change of 0.28.0 (`8c25eb2`) took every Slate placeholder not inside a text field for typed
  content. It is Discord's text again: "Mandà un messaghju à @Ron", also when a draft is typed and erased (a new
  node); the draft itself and the caret are never touched.
- **Discord, message search over a conversation**: "Rechercher Ron" (LDZtFO, only used by the message search bar,
  with the conversation's or server's name) said "Circà Ron", read as searching for the person; it now says "Circà in
  Ron", as Corsu's "Circà in a pagina". Searching for people keeps "Circà", "Circà amichi". Provenance in
  `lexicon/review-discord-2026-10.tsv` (Corsu usage and an AI proposal, not read by a speaker).
- **Discord, system messages as the current client draws them**: the pin notice is "{name} a épinglé [un message]
  dans ce salon. Voir tous les [messages épinglés]." (yIDvPL, two links), not the shape 0.28.0 assumed, and a
  renamed group adds a "Modifier le groupe" link (geP3rU): these fragments stayed in French in the message list and
  are now looked up there (rows already in the lexicon). System phrases are now only looked up in message-list rows.
  Group notices ("a ajouté … au groupe.") arriving after load were already translated by 0.28.1 in the simulated
  page built from the client's structure; a Discord started before 0.28.1 was installed keeps the older plugin.
- **Discord, a nickname that reads like a notice**: with someone named "a ajouté", the notice's own fragment "a
  ajouté" beside the name elements stayed in French (the record holds that name). Only a name element, or a lone
  text equal to a recorded name, is kept now; a fragment beside the name elements is the notice's text.
- **Discord, a system message in a preview line**: Discord draws it as one plain string in the same `messageContent`
  span as people's messages. It is read only when the React record's message type is a system type (not default,
  reply or command): "Work hà aghjuntu Error à u gruppu.", while a person's message with the same words stays.
- **Tests**: `tests/e2e/check_discord_regressions.py`, written independently from the client's structures (composer
  at load, after a draft and after navigation, message search opened/closed/reopened, notices inserted after load,
  look-alike nicknames, real messages with the same words, no double translation), runs in CI: 14 of its checks
  fail on 0.28.1, all pass now. Inventory of Discord's French strings and the removal/leaving labels:
  `docs/discord-inventory-0.28.2.md` (`tools/discord_inventory.py` regenerates the table).
- **CI**: update, update with VLC and migration from the published 0.28.1.
- **Window, Home page**: the Programs page is now Home ("Accolta" / "Accueil", house icon): the summary (what is in
  Corsican, what needs you, update) first, then the list under "Programs managed by Corsu". Each row says its state
  in words (in Corsican, partly in Corsican, original language, restart needed); a part switched off while its
  program is still open reads "Restart needed" and is named in the summary. The summary counts each part as its
  row says ("4 of 8 in Corsican · 1 partly in Corsican · 1 to restart · 2 in the original language"); with nothing
  installed, the page has no summary and no lead promising one. "Accolta" is Corsu's existing usage
  (`lexicon/lexicon-mozilla.tsv`, from Mozilla's Corsican Firefox; not an independent validation); the new lead and
  heading are an AI proposal built from Corsu's own phrases, not read by a speaker. Internal page id and text key
  unchanged (`programs`).
- **Discord, review of frequent actions (first batches, AI review, not read by a speaker)**: "Exclure {user}" is
  Discord's timeout and said "Scaccià {user}", the same as the kick "Expulser {user}": now "Esclude {user} per un
  tempu" (kick: "Espulsà {user}", Corsu's convention). Verb forms fixed: "Piantà d'esclude {user}" (was "escludà"),
  "Esclude membri per un tempu" (was "Escludisce temporaneamente"), "Circà canali o roli" and "Circhendu un gruppu"
  (Italian "Cerca"), "Reinizializà" for Réinitialiser where it said "Reinizià" (restart) or "Rinizializà"; "clip"
  and "etichetta" as in Corsu's other rows. "Retirer du groupe" stays "Caccià da u gruppu" (reasons in the review
  file). About 785 of the 22,430 Discord rows examined; the batches left and the questions for INFCOR are in
  `lexicon/review-discord-progress.md`.

## 0.28.1 (2026-10-27)

From 0.28.0 (`1bb7622`, tag `v0.28.0`).

- **Discord, group conversation notices**: "X a ajouté Y au groupe." stayed in French (seen on the maintainer's
  Discord), as did "X a retiré Y du groupe." and "X a quitté le groupe.". Each name is its own element, so the text
  between them is a fragment ("a ajouté", "au groupe.") in the message list, a name area where only templates and
  dates applied: the rows existed but were never looked up there (same cause as the pin notice in 0.28.0). These
  fragments are now system labels: "X hà aghjuntu Y à u gruppu.", "X hà cacciatu Y da u gruppu.", "X hà lasciatu u
  gruppu."; "du groupe." said "di u gruppu" (of the group) and now says "da u gruppu" (from the group), as Corsu's
  "Caccià da u gruppu". Templates cover names drawn inside the sentence's own node. A name its records hold is never
  read as a system label, even one written like a fragment. Translator revision `2026-10-group-1`; provenance in
  `lexicon/review-discord-2026-10.tsv` (Corsu usage, not read by a speaker). Checked in simulated pages with the
  built plugin (`check_discord_built.py`), not in the real Discord.
- **Going back from the `hyprland` development build**: 0.28.0's installer refused the parts `hyprland` and
  `hyprland-profile` that such an installation records (`invalid choice: 'hyprland'`), so the documented return to
  the published release failed (cleanly: the installation stayed as it was; seen in an isolated test). The installer
  now leaves a recorded part it does not know as it is, with a note; an unknown name nobody recorded is still an
  error. The guides now name 0.28.1 for that step.
- **CI**: update, update with VLC and migration from the published 0.28.0.

## 0.28.0 (2026-10-26)

Developed on next-0.28 from 0.27.0 (`f51b1ac`, tag `v0.27.0`).

- **Windows, Corsu's window closed at start** (0.26.0 and 0.27.0, every Windows): pywebview's WinForms backend loads
  the window icon with `System.Drawing.Icon`, which throws on a PNG; the unhandled .NET exception ended the program
  and its local server. Reported on a real Windows after the one-line install of 0.27.0. Windows now gets
  `src/app/corsu.ico` through `windows_window_icon()`; macOS (Dock icon) and Linux keep the PNG as before. The
  workaround with `--browser` in the Windows guides is kept for 0.26.0 and 0.27.0 only.
- **Discord, pinned message**: the system message "X a épinglé un message dans ce salon. Voir tous les messages
  épinglés." stayed in French, seen on the maintainer's Discord. The sentence was in the dictionary but never looked
  up in the message list; the plugin now translates these exact system sentences there (`systemLabels`), plus two
  templates where the name is drawn inside the sentence, inserting the name verbatim ("Work", "Error" stay as
  written). The link "Voir tous les messages épinglés." was added. Provenance in `lexicon/review-discord-2026-10.tsv`
  (Corsu usage, not read by a speaker); where Discord draws the name is an assumption, not inspected in the real
  client. Checked in simulated pages with the built plugin in headless Chromium (`check_discord_built.py`), not in
  the real Discord.
- **Switching a part off**: the program already open (Firefox, Discord with the Vencord plugin loaded) keeps its
  Corsican interface until it restarts, and the window used to show the switch as off without saying so. The window
  now says which program to restart, however the part was switched off (including the big "Désactiver" button),
  only while that program is really running (Discord, Vesktop and KDE by executable name, Firefox by the path of its
  translated copy), and the line goes away once it has restarted. Chromium browsers have no such signature: only the
  short hint on click. Repair and update keep the parts switched off (`installer.keep_choices`, now tested).
- **Download source**: `get.sh`, `get.ps1` and `update.py` show a visible warning when `CORSU_DOWNLOAD_BASE` points
  to a non-official source. The archive and its `.sha256` then come from the same place, so SHA-256 proves only that
  the transfer is intact, not where the file comes from; the official source stays the default (HTTPS to GitHub).
- **Firefox**: the context menu on selected text now reads "Circà « … » cù Google" instead of the French
  "Recherche Google pour « … »" (`browser.properties`, key `contextMenuSearch`, which had no lexicon row). AI
  proposal built on wording Corsu already uses beside it ("Circà cù %1"); regression test in `tests/test_engine.py`.
  End-to-end check `tests/e2e/check_firefox_context_menu.py` (run by `e2e.py firefox`): the real context menu on
  selected text, with the default engine and another one, special characters, Firefox's truncation and the access
  key.
- **Discord, search fields**: "Rechercher" stayed in French on the Friends page and over a conversation ("Rechercher
  EnzoParisi, Moz_One"), seen on the maintainer's Discord. The plugin never read text fields (`<input>`, editors),
  so their own placeholder and label were skipped; it now translates those attributes, and the placeholder Slate
  draws inside an empty editor, never what is typed nor a field inside a message. In a placeholder, the template
  "Rechercher {name}" applies whatever name Discord inserts (a group's name is composed from its members, so no
  record holds it); the name stays as written. Bare "Rechercher" now says "Circà" as Discord's own rows do, not
  Firefox's "Ricercà"; three more search labels left half French were added (provenance in
  `lexicon/review-discord-2026-10.tsv`: Corsu usage, not read by a speaker). Translator revision
  `2026-10-search-1`. Checked in simulated pages in headless Chromium (`check_discord_names.py`,
  `check_discord_built.py`), not in the real Discord.
- **CI**: update and migration from the published 0.27.0 (`check_update.py`, `check_update_apps.py`, and
  `check_migration.py --from 0.27.0` beside `--from 0.24.0`, appearance settings included). The package job fails when
  `corsu-windows.zip` lacks a valid `src/app/corsu.ico` or `pythonw.exe`; on a Windows Server runner,
  `tests/e2e/check_windows_window.py` starts Corsu's real window from the archive's own Python and checks that it
  stays up with its icon, its local server answering, and closes by itself.

## 0.27.0 (2026-10-19)

Developed on next-0.27 from 0.26.0 (`9868066`, tag `v0.26.0`). CI checks the update from the published 0.26.0.

- **Phone keyboard, packages 1.2** (`keyboard/`, docs/fr/telephone, docs/en/phone):
  - No space is added before punctuation already in the text: choosing "Aiacciu" in `Aiacc|.` gives "Aiacciu.", not
    "Aiacciu .". The model wrapper (`keyboard/whole-word.js`) leaves out the space for that suggestion when the word is
    followed by punctuation, a hyphen, a line break or a no-break space. At the end of a word this works on Android
    and iPhone; inside a word, on Android only.
  - The typographic apostrophe is kept: "l’is" + "l'isula" gives "l’isula".
  - 6,012 forms that sources write are now known words, so Keyman 19's automatic correction no longer replaces correct
    words ("tradizioni", "culturali", "andati", "fundata", "abitanti", "ghjocanu", "l'ADECEC", "l'abitanti"…). Rules
    5b (plurals and feminines differing by their last vowel, 2,819), 5c (forms of Wiktionary's Corsican entries,
    2,763), 5d (elided forms, 429) and 5e (forms checked in a cited source, 1: "ghjocanu", U Cunghjugarellu). Forms
    taken from Vikipedia must be written at least 5 times in Corsican prose, in at least 3 articles: titles,
    quotations, italics, bibliographies, tables and sentences in Italian, French or Latin no longer count. 324 forms
    that only the earlier count supported are held back with their passages (`keyboard/data/held-back.tsv`) and not
    shipped, for example "secoli", "prodottu", "dalla". Each added form weighs less than the words already offered
    for its prefixes, so it is recognised when typed but pushes no listed word out of the suggestions. This selection
    was made by AI and not checked by a speaker (`keyboard/data/REVIEW.md`). 13,213 words in the published 1.1
    packages, 19,341 in each 1.2 package.
  - Historical and traditional place names of Corsica from a sourced inventory (`keyboard/data/sources/historical-places.tsv`,
    `keyboard/data/historical-places.md`): micro-regions, pievi, dioceses and episcopal sees, Genoese provinces and
    historical divisions, with each spelling's usage, category and reference. 113 new words, including
    "Vallerustie" (the maintainer's report), "Mariana", "Accia" and "Sagone", and documented French or other
    spellings such as "Nebbio" and "Aléria", which weigh less than the Corsican form. Only accepted rows ship (289
    of 330; 23 uncertain and 18 deferred rows are listed, not shipped). Each name is kept as typed with automatic
    correction on, and comes below the common words offered for its first letters; a common word that is also a
    place name ("serra", "verde") keeps its entry. Compound names are known word by word: Keyman looks up only the
    last word before the caret, so "San Lurenzu di Vallerustie" is never offered as one suggestion.
  - Punctuation typed right after tapping a suggestion: Keyman 18 leaves "casa ."; one Backspace removes only the
    space. Keyman 19 removes the space itself. Written in the phone guides.
  - Final packages checked in Keyman's engines only: every check passes in 18.0.254 (also in CI); in the 19.0.309 beta
    every word case passes, but the "auto-correct on" scenario fails intermittently on an internal engine error
    (`isFullReplacement`), also reproduced with the earlier 1.1 and 1.2 packages, origin not fully isolated. The space
    before punctuation was also seen in the 18.0.254 and 19.0.309 apps on an Android 14 emulator, with earlier 1.2
    data. Not tried on a real phone or an iPhone.
- **Report a translation from the window** (« Signaler » page, `src/app/report.js`): program, version, text seen,
  place, proposal and notes. The page shows the report first, copies it, or opens a prefilled GitHub issue, only on a
  click. Nothing is sent or stored by the page; account folder paths and e-mail addresses are replaced.
- **Review sets for speakers** (`review/`, `tools/review_sets.py`): 71 short sets of Minecraft questions, each one a
  Markdown page and a self-contained HTML page that builds a reply to copy or send as a prefilled issue. Answers are
  stored as proposals tied to the English and Corsican hashes; an answer goes back to "to re-examine" when either text
  changes. Accepted answers become `validation.human` in the Minecraft memory.
- **Translation memory** (`tools/tm.py`): a candidate written for another sense is refused; an abbreviation is never
  reused from the only translation found elsewhere (`lexicon/memory/abbreviations.tsv`); each reuse records where it
  comes from; changed sources are detected. Real cases as tests: Bio, Profil, Minecraft `key.drop`.
- **Language review, round 5** (AI work, re-checked by a separate AI pass; no speaker review):
  - Minecraft Java: about 700 texts read (world management, game rules, connection, inventory, chat), 16 changed, for
    example `doFireTick` « U focu si sparghje », `doWeatherCycle` « U tempu cambia ». Verified on the 87 releases with
    each game's code.
  - Discord: a bare "Supprimer" takes the verb of its dialog; Spirlà/Dispirlà (pin), In linea / Fora di linea.
    Firefox: Minuteria for the New Tab timer. KDE: Squas for the Delete key.
- **Minecraft Bedrock, prototype** (`minecraft/bedrock/`): target Bedrock 26.50 (bedrock-samples v1.26.50.4), 4,272 of
  13,340 texts reused from Java where the English and the sense are the same; stricter reuse refusals; comment-free
  pack; install, test and removal protocol in docs/fr/minecraft-bedrock.md. Never loaded in the game. CI checks it and
  builds the test pack as a separate artifact (`minecraft-bedrock-prototype`), never attached to a release.
- CI: updates checked from the published 0.26.0 as well (`check_update.py`, `check_update_apps.py`).

## 0.26.0 (2026-10-18)

- Wording review (AI, not reviewed by a speaker): Minecraft main and pause menus, worlds, servers, options
  (review-2026-10/ROUND4.md): "Ghjucà solu" / "Ghjucà cù l'altri" on the title screen buttons, "Arregistrà è esce da u
  mondu" (was "…vultà à u titulu", a heading, not the title screen), 18 texts; Corsu window ("Rileghje", "{job} :
  operazione compia."), Firefox (create/edit profile, tab menu and "apparechju" as Mozilla's Corsican), Discord
  ("Disattivà i mumenti nutevuli"); each change with its category (mistranslation, clumsiness, preference) in
  lexicon/corrections.tsv, lexicon/review-discord-2026-10.tsv and lexicon/REVIEWS.md.
- Phone page of the window: the three dictionaries are listed as published; sections left out no longer risk showing
  "null".

- Minecraft Java: verified part of an October 2026 AI review (minecraft/java/review-2026-10: APPLIED.tsv,
  REJECTED.tsv, TRACKING.md): 1,131 texts in 26.3 and older versions. Wrong senses corrected (Squid "Calamaru" =
  inkwell > Totanu; Clay "Creta" = chalk > Arzilla; Rail "Binariu" > Ragliu; Moss "Muscu" = musk > Murzu; Smithing
  Table "ferraghju" = February > Bancu di stazzunaru; Sign "cartellu" > cartella), Italian forms replaced by attested
  Corsican ones, oak masculine (querciu) through every variant, dighjà, polite-voi agreement, left/right click,
  death messages naming the Wither effect. Pecura kept for Sheep (generic use attested). 68 proposals rejected with
  reasons, 41 deferred. Sources: ADECEC lexicons, INFCOR, Vikipedia, Mozilla/Patriccollu translations; no human
  review. All 87 versions checked against their own game code: 0 errors. `tools/minecraft.py verify` no longer
  crashes when the pack is missing. Second round on the older texts and deferred rows: 27 texts (Thunder
  "Tronu" = throne > Tonu, Ladder > Scaletta, five spellings harmonised); 28 cases still deferred with the exact
  dictionary entry to check.
- Keyman: the dictionary keeps the case typed (Eccu, ECCU; Keyman's `languageUsesCasing`), suggestions at a
  sentence start are capitalised, the package shows as "Corsu" instead of `platykalt.co.corsu`. Vocabulary rebuilt
  (keyboard/data, sources in docs/keyboard-sources.md): 5,375 entries removed (English words, product names, other
  scripts, fragments, unattested rare forms), daily vocabulary added, weights from everyday text instead of
  software labels. Two experimental regional preferences, corsu-keyboard-cismuntincu.kmp and
  corsu-keyboard-pumuntincu.kmp (361 words weighted differently, each from a cited source; partial coverage).
  446 Corsican place names from Wikidata (CC0), kept with their capital and protected from correction;
  "parlle" now offers "parolle" first (an editorial weight on parleti had no corpus support).
  Checked in Keyman for Android 18.0.254's own engine (CI) and in the real app on an Android 14 emulator; not on a
  phone, not on iOS. Keyman 18 has no automatic correction (documented). A suggestion chosen with the caret inside
  a word now replaces the whole word on Android ("Dopu ell|a vene" + ellu: "Dopu ellu vene", no longer
  "Dopu ellu a vene"): the models ask Keyman to delete the rest of the word (keyboard/whole-word.js); Keyman for
  iPhone ignores that request, so the guide there gives the safe gestures. Draft Keyman issue, not sent:
  docs/keyman/ticket-mid-word-suggestion.md.
- Update check: Corsu 0.24.0 said "up to date" on 18 October while 0.25.1 was out. Causes (docs/update-diagnosis.md):
  a window checked only when it opened, a second launch only showed that window again, and a saved answer was
  reused for 6 hours as if fresh. Now a saved answer serves 1 hour at most and never when older than the running or
  installed copy; an open window asks again every hour and on each new launch; a newer copy opens its own window;
  a failed check (network, rate limit, bad or cut answer) says "Vérification impossible", never "up to date"; the
  window shows its own version, the installed copy, the latest release and when GitHub answered. Catch-up from
  0.24.0 with the public one-line installer checked in a container (26 PASS).
- Discord: the notification-area menu ("Quitter Discord", "Ouvrir Discord"…) and Windows taskbar buttons, drawn
  by the system from strings the page sends (`setSystemTrayStrings`, `setThumbarButtons`), are translated on the
  way out; seen in a real Discord 1.0.162 in a KDE container, strings sent by hand, not logged in.
  "Fermer Discord" not found in any Discord text (docs/untranslated-inventory.md).
- KDE: desktop entries without `Name[co]` showed English ("Display Configuration") because KDE does not fall back
  to the second language; Corsu now writes `[co]` in the entries it already handles, kglobalaccel components
  included, with French when no Corsican exists.
- Corsu's window: new logo; the window is tied to its menu entry (`corsu-setup` app id and X11 class), so KDE's
  Alt+Tab shows Corsu's logo instead of a generic icon (seen on KDE Plasma 6, Wayland and X11; Windows AppUserModelID
  and macOS Dock icon set, not observed).
- Keyboard data: 221 official commune names (INSEE, Licence Ouverte) next to the Corsican names, so a legitimate
  spelling typed on purpose (Bastelicaccia) is kept; parlle offers parolle in all three models; U Cunghjugarellu
  described as it is (511 rows, 368 forms of 21 verbs, notices on the publication; docs/keyboard-sources.md).
- Minecraft: third review round (review-2026-10/ROUND3.md): counts reconciled (1,158 edits, 1,157 distinct texts),
  sensitive decisions re-read on their sources (Ragliu, Tonu, Radichju, Cartella, Pastadolce, Pecura), no text
  changed; decisions recorded in lexicon/memory/minecraft-java.jsonl, never reused for another program.
- Release files: from this release on, every published file has its own matching `.sha256` (checked in CI; the
  files already published with 0.25.1 are unchanged); `tools/count_kmp.py` counts the
  words of a built Keyman package.
- Phones: "Write Corsican on Android and iPhone" at the top of the README; guides rewritten from Keyman 18.0's help
  and source; the window's new "Sur téléphone" page with QR codes (generated locally) to the public guides.
- Project rules for agents (AGENTS.md): full meaning before abbreviations; provenance of every translation.

## 0.25.1 (2026-10-18)

0.25.0 was tagged but never published: the release run's Windows check found the fault below, so nothing was
released under that tag. 0.25.1 is 0.25.0 with this fix.

- Windows: reading or replacing `installation.json` while another Corsu process is using it (the window reads it
  every second and a half while an installer writes it; two installers started at once) failed for a moment with
  a sharing violation and stopped the run ("[Errno 13] Permission denied"). It is now tried again for up to two
  seconds. Present since the window existed; seen once in CI, in the "two installers at once" check.

## 0.25.0 (tagged 2026-10-18, not published)

- Poedit: Corsican through `LANGUAGE=co:<session languages> LC_MESSAGES=/C.UTF-8` on Linux (wxWidgets reads
  "/C.UTF-8" as no language, so LANGUAGE wins; glibc loads it as C.UTF-8 without the C exception, so GTK follows the
  next language). The former `LANG=C.UTF-8 LC_MESSAGES=C.UTF-8` put GTK's dialogs in English. Checked first with
  `LC_ALL=/C.UTF-8 locale`, falling back to the old variables with a stated trade-off. Real runs: Debian 3.6.3 and
  Flathub 3.10, fr/de/it sessions. Windows `ui_language` (simulated). macOS: per-app `AppleLanguages` array in
  `net.poedit.Poedit` (new `defaults-plist` record in `settings.py`, type-preserving revert, global domain refused);
  experimental, `defaults` round trip checked on a CI macOS runner.
- PDFsam 5.0+: Java preferences `locale=co` (new `java-prefs` kind); real run on Linux (6.0.6 deb), Windows simulated,
  macOS left alone.
- Firefox: `intl.regional_prefs.use_os_locales` true as a default of Corsu's copy (`browser/defaults/preferences`):
  the copy runs in the en-US slot and `LocaleService::GetRegionalPrefsLocales` only uses the system's regional locale
  when languages match or that pref is set. Profile choices still win. `signature()` checks argument order (plain
  `%S` as `%n$S`). 31 lexicon rows for devtools and downloads; "Onglets ouverts".
- Discord: "Dans un appel" (and the rest of the activity line) translated in the direct message list, where the
  `[class*="activity"]` and `/channels/` link rules kept it as a name; now a text there is looked up when React props
  show an activity, and the activity's own values (game, details, state, custom status, asset texts, buttons) and
  names stay as written, also inside a longer text. "Bio" (profile bio) was "Organicu", taken from Chrome's image
  styles; it is now "Biugrafia" (INFCOR lists biografia with the variant biugrafia; Wikipedia in Corsican uses
  biugrafia), the bio itself untouched. 51 Discord rows where the fallback gave another program's sense (salon > salottu, Envoyer > Incaricà,
  Événements > fre:ac's logs, Anglais > Corsu…), from an AI second-pass review (lexicon/review-discord-2026-10.tsv,
  docs/discord-review-2026-10.md). Hidden diagnostic: classifies each untranslated text (missing, unapplied, excluded
  and by which rule, template, stale), gives the plugin revision and dictionary fingerprint, and gives no name or
  status (unknown words as {?}). Simulated pages and the built bundle in Chrome; not observed in the real app.
- Discord: texts of presence areas (activity line, and components given one activity: profile cards) are kept by
  their origin: only Discord's own activity labels and templates are translated there, so a game shown under
  another name than its record ("Control", "Mars 2") stays as written. The diagnostic decides by origin too: nothing
  from names, statuses, activities or headings above people is given, even a dictionary word ("Work", "Error").
  Plugin revision `2026-10-origin-1`. In Discord's sense: "Message" is the noun "Messaghju" (was "Mandà un MP"),
  Sync > Sincrunizà, Go > Andà, Playing > Ghjoca à, Watch > Fighjà, sec > s, "max"/"min." written out, Arcade,
  Shouting > Brionu, Banner > Bandera (profile banner label only). Each correction's provenance (external source,
  Corsu's own usage, AI proposal) is in lexicon/review-discord-2026-10.tsv. Translation rule for abbreviations in
  AGENTS.md and CONTRIBUTING.md.
- Window redesign: sidebar (top bar when narrow), Programs summary (what is in Corsican, what needs you, update),
  dense rows with problems first, states as icon and word, details on demand, sizes in rem. Appearance section: light,
  dark or system theme, five palettes, accent colour (adjusted when unreadable), plain background or personal picture
  (preview, framing, Apply/Cancel, dimming, optional blur), comfortable or compact density, reset of appearance
  only. Pictures are checked (PNG, JPEG, WebP; GIF and AVIF converted by the page; animated pictures kept still),
  reduced, copied to `DATA/appearance`; a missing or damaged one falls back to the plain background. Settings in
  `DATA/appearance/settings.json` (format 1), kept through repair, update and uninstall.
- Window (security, all systems): a key made at each launch is required on every call, reads included
  (`X-Corsu-Key`, obtained once from a one-time ticket in the window's address). Until now, on Windows and macOS,
  another account of the computer could read Corsu's state and the background picture, and trigger actions, by
  sending the `X-Corsu` header itself. See docs/window-security.md.
- Launchers: the archive's Python is kept in Corsu's data folder even when the installer runs on the system's
  Python. On Linux, launchers fall back to it when the system's Python is missing, too old or incomplete
  (`DATA/bin/corsu-python`); on macOS they always use it, also after a repair run with another Python. Until 0.24.0 the menu entry and Firefox launcher pointed at `/usr/bin/python3` and broke
  if it was removed; installing with only `python3-minimal` failed.
- Discord: protected names checked in every lookup (templates, counts, dates), labels around a name still translated,
  "…" and "..." equivalent; English typing words in the lexicon. Simulated page in Chrome only.
- Window (security, Linux): an action is accepted only from the client end of that very connection: both addresses
  and ports, ESTABLISHED, exactly one owner equal to the window's user; an unidentified caller is refused. Until
  0.24.0 the owner was looked up by port alone: another local account could make its connection read as the
  window's user (bind 127.0.0.2:<window port>, connect to the window) and trigger installs, updates or uninstalls
  while the window was open; and a closed connection in TIME_WAIT on the same port (uid 0) refused the user's own
  actions at random (0.23 % of requests on a quiet machine, 75 % under heavy connection churn). See
  docs/window-security.md.
- VLC: `vlc --version` is read with `LC_ALL=C` (German VLC prints "VLC-Version 3.0.24"): the complement was refused
  as "unknown version" in 63 session languages, with no message.
- Firefox: switching it off and uninstalling take the copies' `[Install…]` sections back out of `profiles.ini` and
  `installs.ini` (`unlink_profile` only ran when pruning old copies).
- Poedit: plain `C` fallback where C.UTF-8 does not load; on macOS a "System default" chosen since is kept.
- VLC complement: "A&ttrezzi", "Sempre s&opra"; `tools/vlcpo.py check` reports accelerator clashes per VLC menu
  (error for drafts, note for upstream).

## 0.24.0 (2026-10-17)

- Audacity 3 and 4, Tenacity and fre:ac: Corsu switches on their own Corsican translation through their language
  setting, version by version and platform by platform (Audacity 4 on Windows and macOS experimental; fre:ac Flatpak
  and macOS, AppImages and Audacity 4 Flatpak left alone with the reason). Audacity 3, Audacity 4 and Tenacity were
  started for real on Linux (official AppImages, throwaway home) and showed Corsican; the rest is checked on
  simulated folders. The window says what to do when one is left alone (reinstall with translations, start it once,
  close it).
- fre:ac started for real on Linux (Debian's package, in a container): Corsican window, setting kept when fre:ac
  rewrites its settings, switched off, kept off through an update, uninstalled. Its coverage now counts the English
  template's empty entries (it showed no total).
- VLC: an experimental Corsican complement, off unless asked for (`--vlc-complement on|off`, Linux system package of
  VLC 3.0.x): VLC's own catalogue plus AI translations of the 1,760 messages it leaves in English, each reviewed by
  AI (1,757 kept in the build, 3 uncertain left out), none by a speaker. VLC reads it from Corsu's folder through
  `VLC_DATA_PATH` set in its menu entry; no system file is touched. Real VLC 3.0.20 and 3.0.24 showed the new texts
  in their help and Qt windows (CI: `tests/e2e/check_vlc_experimental.py`, `check_vlc_complement.py`).
- The window: VLC's row has its own "Experimental complement" switch (off by default, disabled with the reason
  where unavailable, separate from VLC's own switch); it writes the same preference as `--vlc-complement`, saved
  only once the installer holds its lock. VLC 3.0.24's own window was looked at with the complement (container).
- Updates are checked from the published 0.23.0 too, and from 0.23.0 with real VLC and fre:ac packages
  (`tests/e2e/check_update_apps.py`).
- `tools/vlcpo.py`: checks every VLC draft (msgfmt with the fuzzy entries, arguments, plurals, tags, accelerators,
  punctuation; the upstream file must come back byte for byte), records reviews in `contrib/vlc/review.json`, builds
  the experimental catalogue.

## 0.23.0 (2026-10-17)

- Minecraft: Java Edition in Corsican for 87 versions, releases 1.6.1 to 26.3: one pack per version, built from the
  26.3 translation and `history.json` (3,978 older texts: reused, renamed keys, adapted, new). Each version's own
  game code loaded the pack and rendered every text, with the exceptions listed in
  `minecraft/java/COMPATIBILITY.md`; texts written by AI, not reviewed by a speaker; only 26.3 loaded in a game.
  Corsu detects each game folder's version (Prism Launcher, MultiMC, official launcher, Fabric, Quilt, Forge,
  NeoForge) and installs the matching pack. `tools/mcreport.py` regenerates the pages and counters from the data,
  and each check is tied to a fingerprint of the files it checked.
- The Minecraft pack is selected from the first start (it was also listed as incompatible, which made the game skip
  it once).
- Updates: an Update section in the app (installed and latest stable version, check at start, update button,
  optional automatic installation of stable releases, off by default, restart into the new copy). Re-running the
  installer, the one-line command or the button runs the same code: newer → update, same → repair, older → refused
  (`--allow-downgrade`), keeping the chosen parts and those switched off. Downloads name the exact tag, check the
  SHA-256 and the archive's own version, and extract safely on every supported Python. A lock lets one Corsu task run
  at a time. The new copy is complete before launchers move to it; a failed update leaves them on the previous copy.
- Discord: people's names (user names, display names, server nicknames, server, channel and role names) are no
  longer looked up in the dictionary: "Work" and "Error" stayed "Travagliu" and "Sbagliu". The plugin recognises them
  from the data React keeps on Discord's nodes; checked in a real browser page in CI.
- Tests no longer touch the real installation: two installer tests rewrote the Corsu menu entry when run on a
  developer's computer.
- Installed copy of Corsu now carries the Minecraft data; a second VLC Flatpak activation no longer stops with
  KeyError.

## 0.22.0 (2026-10-16)

- The Corsu window shows each program's real state: in Corsican, partly (some installations switched, others not,
  each with its reason and the next step), blocked, failed, or to restart. Translation coverage is shown separately
  (VLC: 4,443 / 6,203), and so is how each switch was checked. The installation summary reads the same record.
- Windows: the Corsu shortcut shows Corsu's icon instead of Python's (`corsu.ico`, kept outside the release folders
  that updates delete).
- `CORSU_DOWNLOAD_BASE` points the one-line scripts and the updater at another folder of the same archives (for tests);
  the checksum is still checked. CI now installs from the built archives outside the checkout, deletes the extracted
  folder, updates and uninstalls, on all three systems.
- Firefox keeps its logo as the default browser on Linux. Firefox Corsu did not recognise its own menu entry as the
  default, and "Make default" wrote an entry without an icon that pointed at the copy's versioned folder. That entry
  also started the copy without Corsu's launcher, so the taskbar's browser button showed a blank page. The launcher now
  gives Firefox its command (`MOZ_APP_LAUNCHER`), and installing, switching off and uninstalling repair an existing
  entry. On macOS, Firefox Corsu.app shows Firefox's icon.
- An interrupted run no longer loses the way back. `installation.json` is replaced atomically and keeps its previous
  version. A language pack, Vencord installer or application copy cut short is never taken as complete.
- Programs with their own Corsican translation: the summary names only the programs actually switched. A program that
  is open stays in Corsican when switched off, until it is closed. A language chosen in Notepad++ afterwards is kept
  (it used to stop the installation). Settings files keep their Windows line endings and byte order mark.
- The Corsu window says when its record is damaged instead of reading as closed.
- Chromium check on Windows: the new tab's own about:blank load sometimes replaced the page being checked
  (`net::ERR_ABORTED`). The check now detects this and reports browser, URL, page state, HTML and a screenshot when
  it fails.
- Minecraft: Java Edition 26.3 in Corsican, as a resource pack adding the language "Corsu (Corsica)": all 8,557
  texts of the game's language files (menus, options, blocks, items, creatures, biomes, advancements, subtitles,
  commands, Realms…). `tools/minecraft.py` fetches Mojang's texts, checks every key and argument, renders every
  string with the game's own code (`verify`), lists what changes between versions (`diff`, `inventory`) and builds
  `corsu-minecraft-java-26.3.zip`. The texts still need a review by a speaker and a test in the game: see
  `minecraft/java/STATUS.md`. Glossary, conventions and open questions in `minecraft/java/`.
- Fixed a family of wrong translations coming from imported projects whose French was shorter than their English:
  "Profil" showed as "Forzà un Prufilu" (VLC's "Force Profile"), "Actuellement" as "Ripruduzzione in Corsu", "Police :"
  as "Ozzioni di grafia"… The French side of such rows is no longer used; 92 labels changed.
- Discord: 110 short labels corrected after a sense review of about 9,900 (wrong sense, verb vs noun on buttons,
  calques such as "telecaricà" for upload, agreement). Each change, and the 64 less certain suggestions not applied,
  are listed in `lexicon/corrections.tsv`.
- README and compatibility pages say exactly which program is translated on which system (Chrome not on macOS, KDE
  Plasma and the terminal only on Linux, Opera GX experimental), and give the real size of the lexicon.
- `tools/fetch_resources.py` downloads the reusable Corsican resources (Mozilla terminology and memory, Wiktionary,
  Vikipedia, Apertium, CLDR, Tatoeba) with date and checksum; `tools/corsican_words.py` looks words up in them.
  `resources/README.md` lists them, and the dictionaries that can only be consulted by hand.
- New roadmap: `docs/fr/feuille-de-route.md`, `docs/en/roadmap.md`.
- Minecraft: the Corsu app can make Corsican the game's language: it copies the pack into every Minecraft game
  folder it finds (official launcher, Prism Launcher, MultiMC) and sets `lang:co_fr` and the pack in `options.txt`;
  switching off or uninstalling puts back only those settings. Optional separate pack for the splash texts and the
  End Poem (they change for every language). `verify` also reads the built zip's `pack.mcmeta` with the game's codecs.
  A third AI review pass changed 242 Minecraft texts with evidence (`minecraft/java/review.md`); still no speaker
  review and no in-game test (`minecraft/java/STATUS.md`, `TESTING.md`). Licensing notes: `minecraft/java/LICENSING.md`.
- Discord and Google: their own rows now win over the same label taken from other programs (55 Discord labels).
- Variants resolved by meaning in 337 rows: storage = allucamentu (almacenamentu was found in none of the Corsican resources consulted and looks like Spanish almacenamiento), shortcut =
  accurtatoghju, poll = sundaghju, survey = inchiesta (`lexicon/variants.md`).
- More of Patriccollu's translations imported: wxWidgets, fre:ac and Inno Setup (about 2,800 rows).
- Minecraft installer, safer: only game folders playing 26.3 are changed (Prism Launcher / MultiMC instance version,
  or the official launcher's last used profile, including Fabric-style versions); unknown versions, a running game,
  an `options.txt` that is not UTF-8 or has a malformed pack list, and a different file with the pack's name are left
  alone and listed; other packs keep their order, Corsu's pack is never added twice, CRLF files stay CRLF, settings
  are recorded before writing; switching off removes only what Corsu added, keeps a language or pack the player had
  or chose since, and waits while the game runs.
- `inventory.tsv` has separate columns for translation, AI review, speaker review and in-game check.
- Review batches for speakers (`minecraft/java/review-batches/`), a second decision pass (`decisions-2.md`: server =
  servitore, seeds = sumente, Dappled Forest = Furesta ambrata, -e adjectives after feminine plurals keep -e…), notes
  for testers (`minecraft/java/TESTERS.md`), licence options with sources (`LICENSING-OPTIONS.md`, no change made),
  `CREDITS.md`.
- Bedrock prototype (not tried in the game): `tools/bedrock.py`, `minecraft/bedrock/`; 4,288 of 13,340 keys reused
  from Java where the English is identical.
- HandBrake's translations are no longer imported: GPL-2.0-only cannot be combined with Corsu's GPL-3.0-or-later.
- Translation status page (`docs/fr/etat-des-traductions.md`, `docs/en/translation-status.md`); claims about
  Firefox desktop, Steam and the dictionaries rewritten with sources.

## 0.21.0 (2026-10-03)

- Nothing else to install: the Windows, macOS and Linux archives carry their own Python (python-build-standalone,
  checked against its published SHA-256), with what Corsu's window needs on Windows (WebView2) and macOS (WebKit).
  The installer copies it once into Corsu's data folder and the shortcuts use that copy. On Linux, the distribution's
  Python stays the first choice, since its GTK bindings give Corsu its window.
- Linux shortcuts call the Python that installed Corsu instead of whatever `python3` is first on the path.
- Archives: about 41 MB on Linux (was 10), Python trimmed of Tk, IDLE, pip, headers and tests.

## 0.20.1 (2026-10-03)

Includes 0.20.0, which was not published.


- The Corsu app opens in a window of its own, with Corsu's name and icon, instead of a browser tab: WebKitGTK on
  Linux, pywebview when installed, otherwise the app window of Edge, Chrome or Chromium, and a browser tab only when
  none of these exists.
- While Corsu is open, it can also be shown in any browser at the fixed address http://localhost:7744 (the next free
  port when another program holds it). Only Corsu's own page can drive it: other sites, other host names and, on
  Linux, other accounts on the computer are refused.
- `--browser` opens a tab instead of the window.
- Windows: Corsu no longer takes a port another program already uses.
- Fixed from 0.19.2, which was not published: launchers are found again when the data folder is reached through a
  link or a short Windows name.

## 0.19.2 (2026-10-03)

- An open Discord or Vesktop keeps the Corsu copy it started with until it closes: new windows and style reloads no
  longer fail after an update made while it is running.
- The Corsu app no longer stops with "release.json not found" after an update it started itself.
- Every installation points all launchers and shortcuts at the current copy, so earlier copies can be deleted.

## 0.19.1 (2026-10-03)

- Fixed: after installing or updating only Discord, links and downloads opened from Discord did nothing. The
  installer deleted the earlier Corsu copy that the Firefox launcher still used; every launcher and shortcut Corsu
  wrote now keeps its copy.

## 0.19.0 (2026-10-02)

- Discord: about 3,300 more texts in Corsican, found by comparing every French message of Discord with the
  dictionary. They cover the pieces of sentences around bold text and links, such as "Membre(s) correspondant à"
  when typing @, and the settings pages (privacy, age groups, subscriptions, server setup, notifications).
- Discord: sentences Discord breaks over two lines ("Ce salon n'a pas encore de / message épinglé") are translated
  as a whole, and the line break goes back at the same place in the Corsican text.
- Discord: relative times are in Corsican ("il y a 5 minutes" becomes "5 minuti fà", "dans 3 jours" becomes
  "trà 3 ghjorni", "lundi dernier" becomes "luni scorsu").

## 0.18.0 (2026-10-02)

- Updates no longer fail after Discord updates itself: the installer finds the current Discord instead of a version
  folder Discord has deleted, and forgets the files that went with it.
- Original text on hover: a small bubble now appears at once over translated text in Discord and on Google, and the
  option can be switched in Vencord's settings inside Discord without restarting.
- Vencord's own settings pages and plugin descriptions, which only exist in English, are in Corsican (about 1,000
  texts), including Backup & Restore and Patch Helper.
- More reviewed translations by Patriccollu di Santa Maria è Sichè: VLC media player, HandBrake, Tenacity, OpenTracks
  and Firefox Focus for iOS (16,600 rows from other projects, up from 13,000). Imports keep the source's "…" and skip
  lone letters.
- Without Firefox, Corsu downloads Mozilla's French Firefox and checks it against Mozilla's published SHA-512.
- "Dettagliu", plural "dettagli", everywhere.

## 0.17.0 (2026-10-01)

- The Corsu app speaks Corsican, chosen by default; French and English stay available.
- Installing shows a progress bar that fills step by step, with the current step written under it.
- Log: everything Corsu prints goes to `logs/corsu.log` in its data folder, with the full details of any error, and
  error messages say where to find it. The About page opens the folder.
- Vesktop: without Discord or Vesktop, Corsu downloads Vesktop, checks its published SHA-256 and sets it up with the
  Corsu plugin.
- Discord: labels followed by a count without spaces ("Membres—3") are translated.
- "Detagli" instead of "detaglii" everywhere, and "ditagli" aligned on it.

## 0.16.0 (2026-10-01)

- Discord: the plugin now translates labels with a name or number inside ("Send a message in {channel}",
  "{count} unread messages", "Server tag: {tag}", "In a call ({name})"), labels made of several parts
  ("Unread messages, Server name"), and dates ("ghjovi 1 ottobre 2026 à 18:04"). Names themselves are never changed.
- Discord: about 4,900 more texts, read from all of Discord's French message files instead of only the ones the app
  had cached, including tooltips such as "Search or start a conversation".
- Discord: a hidden diagnostic option lists the texts still shown in French, to find what is missing.

## 0.15.0 (2026-10-01)

- Review page in the Corsu app: go through the translations written for Corsu (Discord and Google), shortest first,
  and mark each one correct or fix it. Corrections apply on this computer at the next start of Discord or Firefox,
  and can be sent to the project as a prefilled GitHub issue.
- Updates: the Corsu app shows when a newer release exists and installs it in one click, after checking the
  archive's SHA-256 checksum.
- Learn option: hovering a translated text in Discord or on Google shows the original text.

## 0.14.0 (2026-10-01)

- Discord: about 5,600 longer sentences in Corsican too (settings explanations, warnings, dialogs). 96% of Discord's
  plain text is now covered, labels and sentences together.
- The Discord plugin is lighter (8.2 MB instead of 9.3 MB): it carries short general labels plus every text written
  for Discord, instead of every label up to 60 characters.

## 0.13.0 (2026-10-01)

- Discord: about 8,500 more interface labels in Corsican. Discord's own French text was read from the app and
  translated for Corsu with a shared glossary (canale for a channel, servore, filu, mintuvata…). 96% of Discord's
  short labels are now covered, up from about a quarter.
- New `lexicon/lexicon-fixes.tsv`, read before the imported translations, for the few that are wrong in context:
  Forum, Share your screen, Disable and Off no longer show unrelated or adjective forms.

## 0.12.0 (2026-10-01)

- Firefox: Google pages load as fast as before. The Google module now carries only Google's own labels (11 KB instead
  of the whole 11 MB lexicon) and lives inside the Firefox copy, so it is ready in every tab, including after clicking
  Images, News or Short videos.
- Firefox: about 100 more Google labels in Corsican: date and type filters, tools, map and weather labels, translation
  tool buttons, error messages, "About N results" and ratings. Buttons inside the results, such as "Show more", are
  left alone so they keep working.
- Firefox and Discord: text is translated before it is drawn, so French no longer flashes for a moment.

## 0.11.0 (2026-10-01)

- Discord: much more of the interface is translated: Friends, Shop, the settings menu, member list headings and other
  labels that the plugin skipped because they are not buttons. Any text that matches a lexicon entry as a whole is now
  translated, except in what people write: messages, names of people, servers, channels and roles, statuses, bios
  and embeds.
- The Corsu app has a new layout, closer to a settings window: a sidebar, grouped lists, no duplicated status labels,
  confirmation dialogs for installing and uninstalling, and the log folded under "Show details".
- Plainer names: "Corsu Setup" is now the Corsu app; parts are called Firefox, Chromium browsers (with the browsers
  found), Discord, Vesktop, Desktop, System translations and Terminal. The old "Corsu Setup" shortcut is replaced.
- The installer's plan for system translations is in French too.
- Updating deletes the copies of earlier Corsu versions, except one that Discord or Vesktop still loads.

## 0.10.0 (2026-10-01)

- Corsu Setup is now a window that opens in your browser, on Windows, macOS and Linux alike, with no extra library.
  It installs Corsu (showing what will change first), switches each part on and off, pauses the terminal, links to the
  guides and to Sapienzia, Astutu and LIV, and removes Corsu. The install scripts open it; `--text` keeps the terminal
  installer.
- Discord installed by Corsu now appears among the parts that can be switched on and off.
- Firefox: Google's AI Overview heading and warning, "Short videos" and similar labels are translated, including inside
  the results area. Links and page text are still never changed.
- Messages from Corsu itself are in French or English, following the computer.
- The repository has a security policy, a pull request template, a documentation index and screenshots.

## 0.9.2 (2026-10-01)

- Firefox: the copy always opens your usual profile, with your home page, extensions and settings, even when it is
  started as the default browser. Before, such a start could create a new, empty profile.
- Firefox: choosing Firefox Corsu as the default browser no longer creates a menu entry without an icon (the blank
  sheet in the taskbar); the choice now points at the Firefox Corsu entry.
- Firefox: the New Tab page that Firefox updates separately ("Search with Google or enter address"…) is translated.
- Copies made for older Firefox versions are removed when Firefox Corsu starts.

## 0.9.1 (2026-10-01)

- Firefox: on Google's pages, the buttons and menus that Google's own Corsican interface leaves in French or English
  ("Voir plus", "Search for Images", "Paramètres de recherche"…) are completed in Corsican. Search results are not
  changed, and no other website is touched.
- Safari added to the compatibility table: it cannot be translated, as it is part of macOS.

## 0.9.0 (2026-10-01)

- Corsican word prediction and spelling correction for the Keyman keyboard (Android, iPhone, and computers):
  `corsu-keyboard.kmp`, built from the 17,000 most used Corsican words in the lexicon and attached to each release.

## 0.8.1 (2026-10-01)

- Linux: Corsu patches every version of Discord found in `~/.config/discord`, including the one the launcher still
  starts before Discord switches to the newest.
- How to get Google, and its AI, in Corsican through the Google account language.

## 0.8.0 (2026-10-01)

- Corsu window (Corsu Setup): switch Firefox, the Chromium browsers, Discord, Vesktop, the desktop and the
  terminal on or off one by one; put the terminal back in French for an hour.
- Firefox and the Chromium browsers ask websites for Corsican first, then French. Google answers in Corsican.
- Discord: Corsu patches the newest version of Discord installed in `~/.config/discord`, and the plugin reminds
  you to set Discord to French or English.
- GTK programs and terminal commands now use the Corsican translations (system translations option).
- The installer speaks French on French systems. Enter installs everything; `a` ticks all, `n` ticks none.
- README in French with an English version. Documentation in French and English, with guides for computers and
  phones, Discord, a table of what works where, and why Corsu exists.
- About 32,000 more phrases for the desktop and the terminal: file types, keyboard layouts, units, Kate,
  GnuPG, and the commands of coreutils, bash, git, pacman, sudo and util-linux.

## 0.7.0 (2026-10-01)

- About 18,700 new phrases for the applications people use on Linux: Krita, Kleopatra, Lutris, Transmission,
  Meld, Haruna, Solaar, pavucontrol and the rest of the KDE programs, plus GTK and GLib dialogs, PipeWire and
  NetworkManager.
- The README, the guides and the installer messages were rewritten in plainer language.
- The installer says in plain words what it will change before asking.
- CI now also tries the one-line installers against each published release.
- Simpler layout: the installers (`Install for Windows.cmd`, `Install for macOS.command`, `Install for Linux.sh`)
  sit at the top of each download, a guide per system is in `docs/`, the code is in `src/`.
- On macOS the installer can be opened by double-clicking.

## 0.6.0 (2026-10-01)

- Corsican punctuation now follows the reviewed translations: a space before `:`, `?`, `!` and `;`.
- Reviewed Corsican translations from Firefox for iOS, Mozilla VPN, Thunderbird for Android, VLC for Android,
  Audacity, Poedit, WinMerge and Notepad++ (about 13,000 rows, most by Patriccollu di Santa Maria è Sichè),
  imported by `tools/import_translations.py` and loaded before the drafts.
- About 14,000 new draft rows for the KDE Plasma desktop, Dolphin, Konsole, KWin and System Settings.
- One-line installers: `get.sh` (Linux, macOS) and `get.ps1` (Windows).
- Release archives now have fixed names (`corsu-windows.zip`, `corsu-macos.tar.gz`, `corsu-linux.tar.gz`), so the
  download links in the README always point to the latest version.
- Files reorganised into `src/`, `lexicon/`, `tests/`, `tools/` and `docs/`. Shortcuts are now named
  "Firefox Corsu" and "Corsu Setup".
- The installer stops cleanly when it gets no answer instead of failing.

## 0.5.0 (2026-10-01)

- Chrome, Chromium, Opera, Opera GX, Edge, Brave and Vivaldi on Windows and Linux.
- Mozilla's Corsican translations of Firefox for Android loaded first, and draft rows aligned with their
  vocabulary.
- About 16,600 new rows for Chrome, Opera and Opera GX.
- Chrome for Testing checks in CI on Windows and Linux.

## 0.4.0 (2026-10-01)

- Windows and macOS support for Firefox, Discord and Vesktop.
- "Select what you want to translate" menu and a Corsu Setup shortcut.
- Firefox uses Mozilla's French language pack for the exact installed version, `.properties` files included.
- About 14,000 new rows for Firefox pages and Qt dialogs.
- End-to-end checks on Linux, Windows and macOS before every release.
