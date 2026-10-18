# Minecraft review of October 2026: round 4 (full phrasings and fit to the interface, first lot)

AI work: one agent (E), then a separate AI sub-agent that read the contexts and references itself. **Human
validation: 0.** An AI review is not a speaker's validation. Per-change records: [round4.tsv](round4.tsv).

## What was checked for each label

Exact sense in the game (where the key is shown, found in the 26.3 client jar: the class that reads it); function
(action button, screen title, category, state, warning, question); the Corsican construction (noun or infinitive,
preposition, agreement); consistency with neighbouring labels; room on screen (compared with the English and the
official French, which already fits; the speaker batch notes about 30 characters for a full-width button). A change
is classed **mistranslation** (the text says something else), **clumsiness** (understandable but ungrammatical,
redundant or misleading) or **preference** (both acceptable; chosen for clarity or consistency). No global
replacement of *ghjocu*: it stays in its many nominal uses (*Modu di ghjocu*, *Ghjocu in pausa*, *Listinu di u
ghjocu*, *Esce da u ghjocu*).

## Main menu: Singleplayer and Multiplayer

Where the keys are used (26.3 jar): `menu.singleplayer` and `menu.multiplayer` only on the two big title-screen
buttons (the third is *Minecraft Realms*); Singleplayer opens the world list (title *Sceglie un mondu*),
Multiplayer opens the server list, whose title is `multiplayer.title` (English "Play Multiplayer").
`title.singleplayer` and `title.multiplayer.*` are only the suffix of the operating system's window title
(*Minecraft 26.3 - …*); `key.categories.multiplayer` is a heading in the controls list;
`menu.multiplayerOptions.network` is the label of the multiplayer-scope setting of an open world. Older versions:
the same keys with the same English since 1.6.1 (keys.tsv), so the 26.3 texts apply to all 87 releases.

| Candidate pair | Assessment |
| --- | --- |
| *Ghjocu solu* / *Parechji ghjucadori* (before) | Not mistranslations. *Ghjocu solu* is a noun phrase ("game alone", "solo play"); a reading "only the game" needs a context such as *u ghjocu solu ùn basta*, so it is not the button's natural reading, but the button names a thing rather than the action it starts. *Parechji ghjucadori* ("several players") describes people, not what the button does. Both: clumsiness for buttons. |
| ***Ghjucà solu* / *Ghjucà cù l'altri*** (maintainer's proposal, applied) | Parallel infinitive actions, like the other action buttons of the file (*Creà un mondu novu*, *Ghjucà u mondu selezziunatu*, *Ghjucà u mondu di dimustrazione*). *Ghjucà solu*: verb + predicative *solu* "alone", the construction of Vikipedia's *campò solu*, *cantà solu* (local dump); it describes how one starts playing, not "offline" (a solo world can later be opened to the LAN or online). *Ghjucà cù l'altri*: "play with the others", generic plural article as in *cù l'altri sustenitori*, *cù l'altri populi* (Vikipedia); it covers servers, LAN, Realms invitations, friends, strangers, cooperation or not, and says nothing of the Internet. A composed phrase: its words and construction are ordinary; no dictionary entry is claimed for it. 11 and 17 characters (English 12/11, French 4/11; full-width button). |
| *Ghjucà in gruppu*, *Ghjucà in cumunu* | Rejected: *in gruppu* suggests a team or an organised group, *in cumunu* a shared or cooperative activity; both narrow "multiplayer", which includes playing against others on a public server. |
| *Ghjucà à parechji* (the server-list title before) | Not used: the adverbial *à parechji* "in a group of several" was not found in the local Vikipedia (122 occurrences of *à parechji*; the contexts read are all "to several …", as in *hà cullaburatu à parechji rivisti*); it looks like French *à plusieurs*. Not shown wrong, but not supported. The noun pattern *partita à parechji ghjucadori* (game with several players), already used by `/publish`, is kept for nominal uses. |

Gender: *solu* is masculine whoever plays. A generic masculine is the usual choice for an impersonal instruction;
whether a speaker prefers another wording is an open question.

Kept on purpose: `title.singleplayer` *Ghjocu solu* and `title.multiplayer.*` *Parechji ghjucadori (…)* (a window
title names a state; a noun phrase fits), `key.categories.multiplayer` (a category), `options.worldOptions.multiplayer.title`
(a section heading).

## Pause menu

- `menu.returnToGame` *Ritornu à u ghjocu* (Back to Game): **kept**. Nominal like every other "Back …" button of
  the file (*Ritornu*, *Ritornu à a lista di mondi*, *Ritornu à u listinu principale*); the English is nominal too.
  *Vultà à u ghjocu* would be equally correct (preference), but changing only this one would break the series.
- `menu.returnToMenu` *Arregistrà è vultà à u titulu* → ***Arregistrà è esce da u mondu*** (mistranslation): *u
  titulu* is a heading or a title, not the title screen, which the file calls *listinu principale*; the full form
  *… vultà à u listinu principale* (41 characters) is too long for the button (English 22, French 32). The button
  saves and leaves the current world (in multiplayer it is replaced by *Discunnette*); *esce da u mondu* says that,
  and differs from *Esce da u ghjocu* (quit the program). 28 characters. Closes deferred L58-r2.

## Other screens examined (no change needed)

Title screen and pause menu (`menu.*`), generic buttons (`gui.*`: back, done, cancel, yes/no, to-list buttons),
world selection, creation and editing (`selectWorld.*`, `createWorld.*`), server list and connection
(`selectServer.*`, `addServer.*`, `manageServer.*`, `connect.*`, `disconnect.*`, `multiplayer.*`), LAN and world
options (`lanServer.*`, `menu.multiplayerOptions.*`, `options.worldOptions.*`), death screen (`deathScreen.*`) and the
short labels of the options screens (`options.*`, tooltips excluded). Verbs are consistent: create *Creà*, edit
*Mudificà*, delete *Squassà*, save *Arregistrà*, back *Ritornu*, join *Raghjunghje*, quit *Esce*. Categories stay
nominal, states descriptive, questions interrogative. *Grafia* for Font is the reviewed translations' term
(lexicon-upstream "Font|Police|Grafia").

## Applied changes

| Key (screen) | Before | After | Category |
| --- | --- | --- | --- |
| `menu.singleplayer` (title screen button) | Ghjocu solu | Ghjucà solu | clumsiness (noun on an action button) |
| `menu.multiplayer` (title screen button) | Parechji ghjucadori | Ghjucà cù l'altri | clumsiness (describes players, not the action) |
| `multiplayer.title` (server list title) | Ghjucà à parechji | Ghjucà cù l'altri | preference (same words as its button; *à parechji* unsupported) |
| `menu.returnToMenu` (pause menu) | Arregistrà è vultà à u titulu | Arregistrà è esce da u mondu | mistranslation (*titulu* ≠ title screen) |
| `gui.banned.name.title` (ban screen title) | Nome micca permessu in parechji ghjucadori | Nome micca permessu in e partite à parechji ghjucadori | clumsiness (grammar: "in several players") |
| `dataPack.locator_bar.description` (data pack list) | … in parechji ghjucadori | … in e partite à parechji ghjucadori | clumsiness (same grammar slip) |
| `disconnect.loginFailedInfo.insufficientPrivileges`, `title.multiplayer.disabled` (+2 older) | U modu parechji ghjucadori / U ghjocu à parechji hè disattivatu | U ghjocu cù l'altri hè disattivatu | clumsiness (calque *modu parechji ghjucadori*) and consistency: the same English had two wordings; it is the tooltip of the Multiplayer button |
| `menu.multiplayerOptions.publish.started.online` (chat, 26.2+) | … apertu à u ghjocu in linea à parechji | … apertu à l'altri ghjucadori in linea | preference (unsupported *à parechji*; a first rewording *in linea cù l'altri* could parse as "in line with", caught by the sub-agent) |
| `menu.multiplayerOptions.publish.stopped` (chat, 26.2+) | … ùn hè più apertu à parechji ghjucadori | … ùn hè più apertu à l'altri ghjucadori | clumsiness ("open to several players"); pairs with the line above |
| `gui.banned.name.description` (ban screen) | Pudete ghjucà solu, ma … | Pudete sempre ghjucà solu, ma … | clumsiness (could read "you can only play") |
| `commands.kick.singleplayer.failed` | … in una partita in ghjocu solu fora di linea | … in una partita à un solu ghjucadore fora di linea | clumsiness (*partita in ghjocu solu*) |
| `mco.brokenworld.message.line2` | … per ghjucà ci in ghjocu solu | … per ghjucà ci solu | clumsiness (redundant) |
| older only: `options.multiplayer.title` (1.6–1.12 "Multiplayer Settings..."), `multiplayer.info1` (1.6–1.7) | ghjocu à parechji; U modu parechji ghjucadori di Minecraft | ghjocu cù l'altri; U ghjocu cù l'altri in Minecraft | consistency, clumsiness |

18 texts: 14 in 26.3 (every release that has the key with the same English uses them), 4 older pairs in
`history.json`; the speaker batch `review-batches/01-interface-options.*` and `glossary.tsv` now show the new texts
with their questions. Parameters, line breaks and proper names unchanged (checked by the tools below).

## Separate AI review

A sub-agent read the diff, the English and French, the neighbouring labels, the local Vikipedia, the reviewed
software lexicons and the cached ADECEC games page itself (no INFCOR or other online query). It agreed with every
change and with keeping `menu.returnToGame`; its points, and what was done:

- *Ghjocu solu* leans to "a single game" or "I play alone" (*ghjocu* is also "I play"; *in un colpu solu* in this
  file = "one single blow"): clumsy, not a mistranslation. *Ghjucà solu* paired with *Ghjucà cù l'altri* reads
  "alone". Generic masculine *solu* is normal; *da per sè* exists but was not adopted.
- *Ghjucà cù l'altri* covers LAN, servers, strangers and PvP; *ghjucà incù X* can mean "play on X's team"
  (Vikipedia "hà ghjucatu incù a Juventus"), unlikely with the generic *l'altri*. Slightly homely register,
  acceptable. *Ghjucà à X* names the game played ("si pò ghjucà à a morra"; ADECEC *Ghjochi è ghjoculi* "Ghjucà à
  buschette"), another reason to avoid *Ghjucà à parechji*.
- Applied from its review: `publish.started.online` reworded (the *in linea cù* parse), `publish.stopped` aligned,
  `gui.banned.name.description` disambiguated with *sempre*.
- Not applied, listed below: the remaining *Parechji ghjucadori* labels and the coined *portata multighjucadore*;
  the detached clitic *ghjucà ci* (already in the file, spelling to check).

## Open questions (for a speaker)

- *Ghjucà solu* / *Ghjucà cù l'altri*: natural on the buttons? the generic masculine *solu*?
- `menu.multiplayerOptions.network` *Parechji ghjucadori* with the values *Disattivata / In linea / LAN*: the
  feminine value agrees with *portata* (the tooltips say *portata multighjucadore*), not with the label; a label
  such as *Ghjocu cù l'altri* would need *Disattivatu* and the two tooltips that quote the value. Not changed.
- Window titles *Ghjocu solu* / *Parechji ghjucadori (LAN)*: keep nominal, or *Ghjocu cù l'altri (LAN)*?
- *à parechji* as an adverb ("à plusieurs"): Corsican or a calque? (still used in *partita à parechji ghjucadori*,
  a different, nominal construction).
- Terminology families: labels *ghjocu cù l'altri*, descriptions *partita(e) à parechji ghjucadori*; still
  *Parechji ghjucadori* in `key.categories.multiplayer`, `key.category.minecraft.multiplayer`,
  `options.worldOptions.multiplayer.title`, window titles; *portata multighjucadore* in two world-option tooltips;
  *mondi di ghjocu solu* in two Realms upload texts. Not wrong; to settle with a speaker before a wider harmonisation.
- *ghjucà ci* (detached clitic) vs *ghjucacci*: spelling.
- `deathScreen.title` *Avete persu a vita !* for "You Died!": correct; *Site mortu !* would be shorter but gendered.

## Checks

Python checks and checks with the game's code are kept apart; no game window was opened and nothing was seen in a
running game: see TRACKING.md, round 4.
