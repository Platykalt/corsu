# Discord linguistic review, October 2026 (AI passes)

Every row of [lexicon/review-discord-2026-10.tsv](../lexicon/review-discord-2026-10.tsv) (92 rows) was written by an
AI (Claude). None of it has been validated by a Corsican speaker. Proposals and applied corrections are kept apart by
the `status` column: `applied af45709` (first pass, 17 October), `applied c67715b` (second pass, 18 October, below),
or `not applied` with the reason. The `provenance_class` column says what backs each row:

- **external source**: a source outside Corsu was consulted and is cited in `external_source` (INFCOR, Corsican
  Wikipedia, Mozilla's Corsican translations on Pontoon or as imported in `lexicon-mozilla.tsv` and
  `lexicon-upstream.tsv`);
- **corsu-usage (not independent validation)**: the same wording is already used elsewhere in Corsu, cited by file and
  line. This shows consistency with the project, not that the wording is right;
- **ai-proposal**: nothing outside the AI's own reading backs it.

The older `evidence_type` column (ATTESTED, EDITORIAL CONVENTION, AI PROPOSAL) is kept as it was written in the first
pass.

## Method

1. **Discord's own strings.** The public web client (`https://discord.com/app`, no account and no login; `/app` and
   `/assets/` are allowed by robots.txt) loads its messages per locale. The 44 `en-US`/`fr` message chunk pairs
   referenced by the entry script were downloaded and turned into an en↔fr catalogue: 26,518 English and
   26,349 French messages, keyed by Discord's message id. Plural and select messages were rendered with their
   `other` branch, and arguments as `{name}`. The entry script names 51 `en-US` loaders; the 7 that are not in it
   live in lazy chunks and were not parsed. To check where a label is used, the code chunks were downloaded too, and
   message ids were searched in them. Everything is kept outside the repository, in the session scratchpad.
   Nothing from a Discord account or session was read.
2. **Resolution as the plugin sees it.** Every catalogue string, French and English, was looked up in the same
   order as `engine.application_words('Discord', 'Vencord')`: `lexicon-fixes.tsv`, then the Discord and Vencord
   sections, then the reviewed translation memory, then the fallback (`lexicon-mozilla.tsv`,
   `lexicon-upstream.tsv`, then all of `lexicon.tsv`, first row wins). The lookup also tried placeholder templates,
   trailing punctuation and the first-letter case swap, the way `translate.ts` does. Each hit records its file, line
   and section.
3. **Reading.** The cross-context imports were all read by hand (see the counts below). So were the French strings
   that answer several English ones, and the visible paths in the list further down. Conventions were checked
   against the Discord section's own counts (for example *canale* 751 rows vs *salottu* 0, *avvenimentu* 146 vs
   *evenimentu* 5, *boost* 402 vs *rinforz-* 1).

## Scope, in numbers

French side of the catalogue, by where each string's translation comes from:

| Source | Strings (by id) | Distinct French texts |
|---|---|---|
| Discord section | 18,964 | 16,872 |
| `lexicon-fixes.tsv` | 91 | 32 |
| Vencord section | 1 | 1 |
| **Fallback (other programs)** | **3,073** | **1,622** |
| Not translated (French shown) | 4,218 | 3,905 |

**Cross-context imports (task 1).** 1,478 distinct French labels of at most 3 words come from another program's row.
All of them were read and sorted into three groups:

- 568 where the source row's English equals Discord's English (same sense, low risk);
- 717 where the source row has French only (`|French|Corsican`, sense unknown: this is how *Bio* > *Organicu* got in);
- 193 where the source row's English differs from Discord's (possible sense shift).

Of these, **46 are flagged as risky** in the TSV: 26 wrong senses, 19 inconsistent or ambiguous imports, and a few
agreement or case defects. The rest read correctly in Discord, for example country names, colours, *Ghjoca à*,
*Amichi* and *Bluccà*.

**Same French, different English (task 1).** 291 French labels of at most 3 words answer two or more English
strings. Most differ only by case or wording. About 24 cover truly different senses, and in about 10 of them the
single translation is wrong for one sense: *Connexion* (Log In / Connection), *Quitter* (Exit / Leave), *Ignorer*
(Dismiss / Ignore), *Envoyer* (Send / Submit / Upload), *Pêche* (Fishing / Peach), *Intégration* (Embed /
Integration), *Plateforme* (Platform / Platformer), *Code de vérification* (Code / Verification Role), *Message
marqué* (Bookmarked / Mark Complete), *Date* (Date / Oldest). A flat French key cannot split these. Only a row
written for the dominant Discord sense helps.

**Visible paths reviewed (task 2):**

| Surface | Strings checked |
|---|---|
| Friends list, profiles, status, activities (fixed list) | 51 found in the catalogue (64 searched) |
| Calls and voice, DMs and group DMs, message context menu, server and channel menus and settings, notifications (fixed list) | 105 found (136 searched) |
| Activity, stream, mute and notification labels (pattern search) | about 150 |
| Untranslated short labels on these paths (pattern search) | 55 |

All placeholder rows of the Discord section were also checked: 0 rows have a placeholder set in the Corsican that
differs from the source.

## Proposals

By category: 26 bug-wrong-sense, 19 ambiguous-import, 8 placeholder, 6 agreement, 6 syntax, 5 plural,
3 noun-vs-infinitive-vs-imperative, 6 ok-keep. By evidence: 45 editorial convention, 10 attested, 24 AI proposal.
By confidence: 29 high, 31 medium, 19 low.

The main ones:

- **Bio.** Discord ids `ZzAR2Y` and `YWo+Zd`, en-US "Bio" and fr "Bio". `ZzAR2Y` is the section title of the bio editor
  in Settings > Profiles (main and per-server profile) and the hidden heading of the bio block in profile popouts.
  `YWo+Zd` labels the per-server bio field, whose placeholder is "Présente-toi à ce serveur". It means biography or
  About-me text. The Discord section has no `Bio` row, so the fallback picks `|Bio|Organicu`
  (`lexicon.tsv:23840`, Chrome's list of AI image styles, where it means organic). Proposal: a Discord row
  `Bio|Bio|Bio`, following the 18+ Discord rows that write *bio* (`Add a bio` > *Aghjunghje una bio*, `Edit bio` >
  *Mudificà a bio*, `Server Bio` > *Bio di u servore*). The alternative is *Biografia* (3 rows use it). *Organicu*
  is the only occurrence of the word in the repository and is correct in its Chrome context: keep it.
- **Salon = canale, not salottu.** The first section of `lexicon.tsv` (lines 520–535) still gives *salottu* for the
  French keys of *Créer un salon*, *Paramètres du salon*, *Modifier le salon*, *Supprimer le salon*, *Salons
  textuels* and *Salons vocaux*. The English keys and the fixes already use *canale*.
- **Wrong senses on frequent buttons:** *Envoyer* > *Incaricà* (upload; Mozilla's own `Send|Envoyer|Mandà` comes
  later in the file and loses), *Ignorer* > *Ricusà*, *Réinitialiser* > *Viutà* (to empty), *Valider* > *Definisce*,
  *Événements* > *Ghjurnali di messaghji*, *Couper* > *&Taglià* (accelerator leak), *Modifier le profil* >
  *Mudificazione di prufilu* (noun on a button), *Rendre muet* > *Mutu attivu*.
- **VLC language-list rows:** *Anglais* > *Corsu*, *Français* and *Espagnol* > the English word *Corsican*
  (`lexicon-upstream.tsv:9457–9495`). In VLC these rows name the translator's own language.
- **Generic template `{a} de {b}` > `{a} nant'à {b}`** (wxWidgets "%i of %u"). The plugin's `fromTemplate` tries it
  on any untranslated "X de Y" label, so "from" and "by" read as "out of". Discord-specific rows are needed.

## Uncertain cases (for a speaker)

1. *Bio* or *Biografia* for the label. The project uses both, mostly *bio*.
2. *Bannière*: the Discord section has six forms (*banderola* 29, *bandera* 19, *banderone* 15, *banera* 5,
   *banderuola* 4, *banniera* 1). One term should be chosen. The proposal takes the most used one.
3. *Pseudonyme* (Display Name): *Nome affissatu* (first section) or *Pseudonimu* (current). The Discord section
   writes *cugnome* for both pseudo and pseudonyme, which merges Display Name and Nickname.
4. *Cugnome* for Nickname is kept: in Corsican it is understood as a sobriquet. A speaker should confirm it.
5. *Quitter*: *Lascià* (leave a server, call or group) or *Esce* (quit the app). One flat key serves both.
6. *Sort* (English Trick): *Scherzu* follows the English, *Malìa* the French. *Cri* (English Shouting): *Urlu* or
   *Bramu*.
7. *tastera* or *tastiera*. `variants.md` leaves this open. The proposal follows the Discord row `102347`
   (*tastera*).
8. Plurals: *seconde* and *settimane* are attested in Mozilla's Corsican and are kept. *minute* (`lexicon.tsv:8241`)
   is not attested, while *minuti* is, so the proposal changes it. The plugin's date code uses *secondi* and *simana*,
   which differ from the attested forms. That is code, outside this review.
9. English-mode Discord: `lexicon-fixes.tsv` maps the English key *More* to *Dettagli* and *Show less* to *Menu
   dettagli*. In Discord's English UI, "More" is a menu button. This review covers the French UI first.
10. Lower-case values imported from drafts (*membru*, *rolu*, *privatu*, *codice*, *banera*…) show as lower-case
    labels when the match is exact. Only the visible ones are listed in the TSV.

## Sources

- Discord web client, en-US and fr message chunks, fetched anonymously on 2026-10-17. Kept outside the repository.
- `lexicon/lexicon-mozilla.tsv` and `lexicon/lexicon-upstream.tsv` (attested translations), `lexicon/lexicon.tsv`
  (Discord section, as the project's convention), `lexicon/lexicon-fixes.tsv`, `lexicon/variants.md`,
  `lexicon/REVIEWS.md`.
- First pass: no online dictionary was queried. Second pass: INFCOR, Corsican Wikipedia and Mozilla Pontoon, as
  described above. The absence of a word from a source is not taken as proof that it does not exist.

## Second pass (0.25 candidate, 18 October 2026)

### Method

Each correction starts from where Discord shows the string: its message ids in the en-US/fr catalogue, then the code
chunks that use these ids (the same anonymous download as the first pass), to tell a button from a title, a noun from
a verb, an abbreviation's full expression and its function. A French string used for several senses is not replaced
globally: the safest form is kept and the case is listed as uncertain. Spellings were checked outside Corsu:

- **INFCOR** (ADECEC's Corsican dictionary, https://infcor.adecec.net, queried through its public search on
  2026-10-18): headwords, variants, French, Italian and English equivalents;
- **Corsican Wikipedia** (co.wikipedia.org, public search API, 2026-10-18): counts and use of competing spellings;
- **Mozilla Pontoon**, Corsican translations of all Mozilla projects (TMX export, 2026-10-17).

The BDLC (Banca di dati di a lingua corsa, Università di Corsica) answers but was not queried through its forms.

**Abbreviation rule** (new project rule): when a label holds an abbreviation, its full expression and its function in
the interface are identified first, then it is translated in context; full words are preferred when natural and when
they fit; usual technical acronyms, identifiers and proper nouns stay (AFK, GIF, FPS, PC, MP, Nitro). In the Discord
catalogue: *sec* (seconds, was *seccu* "dry"), *max* / *max.* / *min.* written out (*massimu*, *massima*, *minimu*),
*Sync* (a button: *Sincrunizà*), *Infos*/*Info* (kept *Infurmazione*, as Mozilla writes it), *Micro* (already the full
*Micrufonu*), *Mod* (*Muderatore*, right), *Auto* (*Autumaticu*, right), *Pro* for the level Expert (proposal only).
*min* for minutes stays the unit in "{count} min", "il y a {count} min"; the dictionary has no bare *Min* or *Max*,
so there is no minimum/minutes collision. A lighter scan of labels other programs bring into Discord found the
English keys *Playing* (a player's *Lettura*), *Watch* (*Surveglianza*), *Go* (Mozilla's *Apre*), *Arcade*
(*Arcata*, an arch) and *Cri* (*Cree*).

### Corrections applied (commit c67715b)

| Source (en / fr) | Old | New | Provenance | Justification |
|---|---|---|---|---|
| Bio / Bio (ZzAR2Y, YWo+Zd) | Bio | Biugrafia | external source | User's decision to write out "Biographie". INFCOR: headword *biografia*, variants *biugrafia*, *biograffia*, *biugraffia*. Corsican Wikipedia: *biugrafia* 1222 pages, *biografia* 42; *Biugrafia* is its section title over a person's life, the same function. Pontoon: neither. |
| Server Bio / Bio du serveur, and "de {guildName}" | Bio di u servore | Biugrafia di u servore | external source | Same titles. Sentences keep *bio*. |
| Message / Message (BAB0yK) | Mandà un MP | Messaghju | corsu-usage (lexicon.tsv:566), Mozilla (upstream:2014) | A noun: screen-reader role of every message, icon of text channels. The button is "Envoyer un message". |
| sec / s (DLBuoP) | seccu | s | external source (SI, Mozilla keeps units) | Seconds, not "dry". |
| Sync / Synchroniser (BkuOO6) | Sincrunizazione | Sincrunizà | external source (Mozilla "Sync now" > "Sincrunizà avà") | A button. |
| Playing / Joue à (BMTj28) | Lettura | Ghjoca à | corsu-usage | Activity card header. |
| Watch / Regarder | Surveglianza | Fighjà | corsu-usage | Watch a stream or activity. |
| Go / Aller (rK4Gqv) | Apre | Andà | external source (lexicon-upstream.tsv:13443) | A "go" button, not "open". |
| Max : {statisticName} | Mass. : {statisticName} | Massimu : {statisticName} | external source (INFCOR, Mozilla "massima") | Abbreviation written out, as "Minimu di" beside it. |
| Longueur max du message atteinte | Lunghezza max… | Lunghezza massima… | external source | Abbreviation written out. |
| Nombre max. d'utilisateurs affichés | Numeru max. … | Numeru massimu … | external source | Abbreviation written out. |
| Durée max d'inactivité (brhYaR) | Durata max … | Durata massima … | external source | AFK timeout label. |
| min. requis (A+mTPq) | min. richiestu | minimu richiestu | ai-proposal | Minimum required, under a percentage. |
| Arcade (Sbxowr) | Arcata | Arcade | external source shows the old one wrong (INFCOR: arcata = arch); new: ai-proposal | Game genre. |
| fashion / mode (4J2PYL) | modu | moda | external source (INFCOR moda vs modu) | Topic suggestion "fashion". |
| Shouting / Cri (3gqpuo) | Cree | Brionu | external source (INFCOR brionu: EN shout, outcry) | Clip signal. |
| Banner / Bannière (BSVog8, JaecVH) | (French shown) | Bandera | external source (INFCOR bannière > bandera; banderola = small pennant) | Profile banner label only. |
| Close Window / Fermer la fenêtre | Chjode una Finestra | Chjode a finestra | corsu-usage (lexicon.tsv:392) | A close button. |
| No command found / Aucune commande trouvée | Nisuna cumanda trova | Nisuna cumanda trovata | corsu-usage | Agreement. |

### Uncertain cases of this pass (left as they are)

1. *Quitter*: Leave (a server, an activity, a voice channel: F3qExp, Hi1/aQ, wH/wDO) and Exit (confirm buttons of
   "discard changes?" dialogs: 7WGI4H, h0bti/, TzJA4g) share one key. *Abbandunà* (Mozilla) reads for both and stays.
2. *Mars*: the catalogue string is a gradient preset (planet), but the month shows bare in date-of-birth selects.
   *Marzu* stays.
3. *Message* in English Discord is also the button (verb); the key is shared, the noun wins.
4. *Bannière*: only the label was set (*Bandera*); the 76 Discord rows with six forms in sentences are not harmonised.
5. *Biugrafia* in titles, *bio* in sentences (*Aghjunghje una bio*), and three Discord rows that write *biografia*:
   both spellings are attested (INFCOR); harmonising is left to a speaker.
6. *Micrufonu* (51 Discord rows) is not in INFCOR (*microfunu*, *microfonu*, *micro*).
7. *Pro* (level Expert), *Entreprise* (context not downloaded), *Active*, *Petit*, *Privée* (gender of an implied
   noun): proposals only.
8. *Pseudonyme* stays *Pseudonimu* (INFCOR *pseudonimu*), *Pseudo* stays *Cugnome*: Discord's French keeps display
   name and nickname apart, and so does Corsu.
