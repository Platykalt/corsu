# Discord linguistic review, October 2026 (AI second pass)

Proposals only: nothing in `lexicon/lexicon.tsv`, `lexicon/lexicon-fixes.tsv` or the code was changed. Every
proposal is listed in [lexicon/review-discord-2026-10.tsv](../lexicon/review-discord-2026-10.tsv) (79 rows) and was
written by an AI (Claude) as a second pass. None of it has been validated by a Corsican speaker. The `evidence_type`
column says what backs each one:

- **ATTESTED**: the same wording exists in a reviewed translation (`lexicon-mozilla.tsv`, `lexicon-upstream.tsv`);
- **EDITORIAL CONVENTION**: a choice the project already made (`lexicon-fixes.tsv`, Discord rows of `lexicon.tsv`,
  `lexicon/variants.md`), with the file and line;
- **AI PROPOSAL**: no attestation was found in the local resources. That does not mean the word does not exist.

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
- No online dictionary was queried. The absence of a word from these files is not taken as proof that it does not
  exist.
