# Minecraft review of October 2026: round 5 (natural phrasing, second lot)

AI work: one agent (A), then a separate AI sub-agent that read the contexts and references itself. **Human
validation: 0.** An AI review is not a speaker's validation. Per-decision records: [round5.tsv](round5.tsv).

## Scope: what was read, and what was not

Every 26.3 text of these paths was read with its English and the official French, for its function (action, title,
description, state, error), its full sense (abbreviations written out), its construction and agreement, negations
(*ùn … micca*), parameters and formatting codes:

| Paths | Texts |
| --- | --- |
| World creation and management beyond round 4's short labels: `createWorld.*`, `selectWorld.*` (backup, conversion, experimental and deprecated warnings, incompatible versions, game-mode descriptions), `optimizeWorld.*` (there is no `editWorld.*` key; the Edit World screen is `selectWorld.edit.*`) | 170 |
| Game rules screen: `gamerule.*` | 109 |
| Server connection: `connect.*`, `disconnect.*`, `multiplayer.status.*`, `multiplayer.disconnect.*` (kick and error reasons), `multiplayer.player.*`, `multiplayer.message_not_delivered` | 95 |
| Inventory: `container.*`, `inventory.*`, recipe book (`gui.recipebook.*`, `recipe.*`), creative tabs (`itemGroup.*`), `key.inventory`, books (`book.*`) | 101 |
| Commands and their errors: `commands.give.*`, `commands.gamemode.*`, `commands.defaultgamemode.*`, `commands.teleport.*`, `commands.time.*`, `commands.weather.*`, `commands.kill.*`, `commands.help.*`, `command.*` (parse errors), `argument.*`, `gameMode.*` | 175 |
| Chat and its errors: `chat.*`, `chat_screen.*`, `commands.message.*` | 52 |

About 700 texts. Not read in this round: the rest of `commands.*` (other commands), `mco.*` (Realms) and the
abuse-report screen apart from three texts with the same verb as a change below, advancements, subtitles, death messages, item and block names,
options tooltips. "Read" means read by an AI; no text was seen in a running game.

Most texts needed nothing: errors say *Impussibule di …*, *Ci vole …* (expected …), *… inaccettevule*, *Fiascu di …*
consistently; *ùn … micca* is complete; plurals of "(s)" are written *linea(e)*, *Ricetta(e) nova(e)*; the gendered
participles (*Espulsu*, *Site esclusu*) follow the file's generic masculine; *troppu* stays invariable before a plural
noun as in Mozilla's Corsican (*troppu tentativi*).

## Applied changes

| Id | Key (screen) | Before | After | Category |
| --- | --- | --- | --- | --- |
| R5-01 | `gamerule.doFireTick` (Game Rules toggle) | Rinnovà u focu | U focu si sparghje | mistranslation: "renew the fire"; the rule lets fire spread |
| R5-02 | `gamerule.doWeatherCycle` (Game Rules toggle) | Rinnovà u tempu | U tempu cambia | mistranslation: "renew the weather / time"; ADECEC: *u tempu … cambia* |
| R5-03 | `connect.p2p.failed.unreachable` (join error, 26.2+) | U ghjucadore ùn pò micca esse ghjuntu | Impussibule di righjunghje u ghjucadore | clumsiness: *esse ghjuntu* is "have arrived" |
| R5-04 | `chat.type.advancement.goal`, `advancements.toast.goal` | … hà ghjuntu u scopu … / Scopu ghjuntu ! | … hà righjuntu u scopu … / Scopu righjuntu ! | clumsiness: transitive "reach" |
| R5-05 | `command.forkLimit`, `mco.errorMessage.6003`, `.6004`, `gui.abuseReport.send.service_unavailable` | … ghjuntu / ghjunta / Impussibule di ghjunghje u serviziu… | … righjuntu / righjunta / … righjunghje … | clumsiness (same) |
| R5-06 | `selectWorld.locked` (+ 1.16–1.21.8) | … istanza di Minecraft in corsu. | … istanza di Minecraft aperta. | preference: "Minecraft in corsu" reads "Minecraft in Corsican" |
| R5-07 | `argument.pos.mixed` (+ 1.13–26.2) | (tuttu deve impiegà ^ o nunda) | (o tutte e coordinate impieganu ^, o nisuna) | clumsiness: "everything must use ^ or nothing" |
| R5-08 | `multiplayer.disconnect.too_many_pending_chats` | … micca ricunnisciuti | … micca cunfirmati | mistranslation: *ricunnisce* is recognise (French calque) |
| R5-09 | `selectWorld.edit.export_worldgen_settings.failure`, `selectWorld.import_worldgen_settings.failure` | Fiascu à … / Sbagliu à … | Fiascu di … / Sbagliu durante … | preference: the file's own pattern |

16 texts: 14 in 26.3 (every release whose English is the same uses them) and 2 older pairs in `history.json`
(`selectWorld.locked` 1.16–1.21.8 without the final period, `argument.pos.mixed` 1.13–26.2 with "&"; same sense,
checked in each release's English). `glossary.tsv`: the *rinnovi* row now says it names the category, not the two
rule labels.

### On *ghjunghje* and *righjunghje*

*Ghjunghje* (arrive) takes *esse*: *hè ghjuntu* 25 times in the local dump of the Corsican Wikipedia, all "arrived".
"Reach (something)" is *righjunghje*: 45 occurrences, 14 *hà righjuntu* with an object (*hà righjuntu u scopu*, *hà
righjuntu 170.000 megawatt*, *righjunghje u rifughju*); no transitive *hà ghjuntu* was found among the uses read.
So *hà ghjuntu u scopu* and *ùn pò micca esse ghjuntu* (the player "cannot have arrived") were changed. A form not
found proves nothing by itself: whether *ghjunghje* can take an object in some areas stays a question for a speaker.
The Discord rows with the same construction were changed too (lexicon/review-discord-2026-10.tsv).

### Weather and fire rules

ADECEC's lexicon *Le temps qu'il fait* (cached page) lists what the weather does: *U tempu veraneghja, cambia, muta,
varieghja, si guasta…*: *U tempu cambia* is the plain one. The fire rule uses the file's own verb for fire spreading
(*u focu si pò sparghje*, the neighbouring radius rule) and the sentence form of its neighbours (*E liane si
sparghjenu*, *A lava si cambia in surgente*). The rule also lets fire burn out; the label names the main effect, as
the French does (*Propagation du feu*).

## Kept or open (not changed)

- Q5-01 `/weather` results *U tempu hè avà sirenu / piuvosu*: ADECEC gives *serenu* (*tempu serenu*) and, for
  rainy, *piuvascu, piuviscosu, acquazzosu*, or *u tempu hè à l'acqua*; *sirenu* is on that page only as a mountain
  breeze, *piuvosu* not at all. A form missing from one page proves nothing: question for a speaker.
- Q5-02 *naufragi* (Shipwrecks, the structures): a shipwreck event or the wrecks themselves (*relitti*)?
- Q5-03 `%s PS` for health points in the player list: the abbreviation is not explained anywhere; the space is narrow.
- Q5-04 *telepurtassi* once against *teleport-* 13 times: spelling before harmonising.
- Q5-05 *Manghjà è bevande* (Food & Drinks tab): nominal infinitive next to a noun.
- K5-01 *Rinnovi di u mondu* (category heading) and K5-02 nominal command results (*Eliminazione di %s*, which avoids
  a gendered participle) kept on purpose.
- Not reopened: *Tonu* (thunder) and the round-4 decisions.

## Separate AI review

A separate AI sub-agent read the diff, the English and French, the neighbouring texts, the local Wikipedia dump, the
cached ADECEC page, Mozilla's Corsican (Pontoon TMX, lexicon-mozilla.tsv) and the reviewed upstream lexicon; no
dictionary was queried. It agreed with R5-01 to R5-09, with these reservations, kept in round5.tsv:

- R5-01: the rule also lets fire burn out; the French names only the spreading too.
- R5-02: a slight time/weather ambiguity of *tempu* remains (*Cicculu di u tempu*, the French's "cycle", possible).
- R5-03 to R5-05: the direction is right (no *hà ghjuntu* with an object in the dump; *Scopu ghjuntu* a marginal
  calque), but the claim is not absolute: one reviewed upstream row says *U numeru massimu di filtri … hè statu
  ghjuntu*, and Mozilla's Corsican says a limit is *toccu* (*Limitu di %1$d Go toccu*). *righjuntu* kept; *toccu* noted
  as an alternative for limits. It found one more Minecraft text with the same verb (`gui.abuseReport.send.service_unavailable`,
  added to R5-05) and 16 more Discord rows (changed, lexicon/review-discord-2026-10.tsv).
- R5-09: a consistency gain; Mozilla has once *Fiascu à l'arregistramentu*, so the old form was not wrong.

## Checks

Python checks and checks with the game's code are kept apart; no game window was opened: see TRACKING.md, round 5.
