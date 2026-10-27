# Discord plugin: verification of the cases reported after 0.28.1

Independent verification, 2026-10-27, of the cases the maintainer reported on Discord desktop 1.0.166 with the French
interface (Corsu 0.28.1, commit ae8890b). Nothing here was observed in the real Discord app: the structures come from
the code of Discord's public web client fetched that day (`web.ad0b95d8568e0f6b.js` and its lazy chunks, class names
from the client's CSS module maps). The cases are replayed on simulated pages, in headless Chrome 152 (Linux), by
`tests/e2e/check_discord_regressions.py` against the plugin as built (Vencord's `dist/renderer.js` with the real
dictionary, built by `installer.prepare_build()` at Vencord 7f0c10c). A simulated page does not validate the desktop
app (Electron); see "Limits" at the end.

Run: `python3 tests/e2e/check_discord_regressions.py CHROME [VENCORD_DIR]` (exit code 1 while a case fails).

## A. DM composer: "Envoyer un message à @X"

- **Key and element.** The current client has no "Envoyez un message…" string: the French catalogue says
  `4c+CAx` "Envoyer un message à {channel}" (English "Message {channel}"), used for a DM with `{channel}` = "@Ron";
  a group DM uses `8lzR/R` "Envoyer un message dans {channel}" with the name Discord composes from the members; the
  editor's label is `fqOxbV` "Écrire un message, {channel}" (lazy chunk `00d172fbbd884146.js`). Discord's own
  SlateTextArea (in `web.ad0b95d8568e0f6b.js`, the class with `showPlaceholder`) draws the placeholder as a
  `<div class="placeholder__1b31f slateTextArea_ec4baf" aria-hidden="true" data-slate-placeholder="true">` placed
  **next to** the editor (`div.markup__75297.editor__1b31f`, `contenteditable`, `role="textbox"`), not inside it, and
  only while the editor is empty: typing removes the div, erasing the draft inserts a new one.
- **Why it stays French in 0.28.1.** `inContent()` in `src/discord-plugin/translate.ts` treats a node under
  `[data-slate-placeholder]` as Discord's text only when that placeholder sits inside a text field; when no content
  area is found above it, it returns "content" (`return !editor || …`). Slate's own placeholder (the search bar, B) is
  inside the field and is translated; the composer's is outside, so it is skipped at load, after a draft is erased
  and after navigation. The editor's aria-label is translated (Scrive un messaghju, @Ron).
- **Expected.** "Mandà un messaghju à @Ron"; group: "Mandà un messaghju in Work, Error". Provenance: Corsu usage
  (lexicon.tsv:112560 `|Envoyer un message à {channel}|Mandà un messaghju à {channel}`, lexicon.tsv:112058 for
  "dans"), not a speaker validation.
- **Baseline 0.28.1:** FAIL at load, after erasing a draft, after navigation (node reused) and in a group; the draft
  ("Envoyer un message", a dictionary phrase) and the caret are left alone (PASS).

## B. Message search over a DM or group: "Circà Ron"

- **Key and element.** The search bar (lazy chunk `c5b5c25ec8ff16aa.js`) uses `LDZtFO` "Rechercher {name}" (English
  "Search {name}") where `{name}` is the server's name or the conversation's (a DM: the person; a group: its name or
  its members); the all-DMs search uses `m7OrlR` "Chercher dans les MP" (Circà in i MP). The text is Slate's
  placeholder span inside the combobox and the combobox's aria-label. `7N3xxX` "Rechercher {guildName}" and `Zfl1NA`
  "Rechercher {title}" are in the catalogue but not used by the client code. Searching for a person or a friend uses
  other keys: `60M8Ae`/`K5e6bn`/`CmSHYx`/`lLDtTK`/`Kd5RaI` "Rechercher des amis" (Circà amichi), `JaOYyf` "Rechercher
  des amis ou des membres de serveur", `InYY4f` "Rechercher des MP avec {userName}".
- **Proposal: "Circà in Ron"** (`Rechercher {name}` → `Circà in {name}` in the Discord section only). "Circà Ron"
  reads as "look for Ron" (find the person), while Discord means "search in this conversation". **AI proposal**,
  built on Corsu usage (lexicon.tsv:399 `Rechercher dans la page|Circà in a pagina`, :2905 `Rechercher dans
  %1|Circà in %1`, :97096 `Rechercher dans ce MP|Circà in stu MP`, :110893 `Chercher dans {channelName}|Circà in
  {channelName}`); repeating our own lexicon is not an independent validation and no speaker has read it. Note: the
  row lexicon.tsv:118505 `Search {name}|Rechercher {name}|Circà {name}` also yields the shared template
  "Rechercher \x001\x00"; only `LDZtFO` uses that shape in the current client, always with a place (server or
  conversation), so "in" fits every use found.
- **Baseline 0.28.1:** wording FAIL (tagged `proposal`); the mechanics PASS: the bar opened after load, a typed query
  left alone, the placeholder after clearing, closing and reopening, navigation with the node reused or remounted,
  names Ron/Error/Work kept.

## C. Group DM notices ("X a ajouté Y au groupe.") and pins

- **Keys.** `7/Xl0S` and `MMN2Jq` still exist with the same text: `{username} a ajouté {otherUsername} au groupe.`
  (`7/Xl0S` with `$link` names, used only by `SystemMessageUtils.stringify` for notification text; `MMN2Jq` with
  username hooks, used by the message list and by the message preview line). Also `QtZ0RD`/`L2FyVq` (a retiré … du
  groupe.), `Qn5+Lf`/`5v2xa8` (a quitté le groupe.).
- **Real row structure** (lazy chunk `fe6d9251f9aa4e0a.js`): `li#chat-messages-…` > system layout (module 888675:
  `div.container__235ca` > `div.content__235ca` > `div`) whose children are the hook elements and **bare text
  nodes** (" a ajouté ", " au groupe."), then the timestamp; a name is an Anchor >
  `span.container__703b9` > `span.nameContainer__703b9` > `span.name__703b9.username__703b9` inside a user popout
  holding the user record.
- **Baseline 0.28.1, message list:** inserted after the translator started, the add, remove and leave notices are
  translated and the names kept (C1, C2: PASS), also when React reuses the text nodes. **So the report is not
  reproduced by the message list row in this simulation.** What does fail, with evidence:
  1. **Pins as the current client draws them** (C3 FAIL): `yIDvPL` is " a épinglé " + link "un message" + " dans ce
     salon. Voir tous les " + link "messages épinglés" + "."; `R7vZGZ` is " a épinglé un message dans ce salon. Voir
     tous les " + link "messages épinglés" + ".". 0.28.1's `systemLabels` only know the older split ("… dans ce
     salon." + "Voir tous les messages épinglés."), so every piece stays French although the dictionary already has
     "a épinglé" (lexicon.tsv:118000), "un message" (:114717), "dans ce salon. Voir tous les" (:118002), "a épinglé un
     message dans ce salon. Voir tous les" (:117998) and "Messages épinglés" (:575).
  2. **A nickname equal to a fragment** (C2 FAIL): when the author's records hold the name "a ajouté", the fragment
     " a ajouté " of the same notice is no longer looked up (the guard compares it to every name around).
  3. **The message preview line** (C5 FAIL; lazy chunk `4bb013d8238b3d6b.js`, MessagePreviewManager, rows of the
     friends/DM widget): the notice is ONE plain string "Work a ajouté Error au groupe." inside
     `span.messageContent__7c4a2`, which `[class*="messageContent"]` marks as what people write. The same span also
     holds a real message's content (then rendered by a component given `{message}`), which must stay as written
     (C5: PASS).
  4. Not testable here: desktop notifications built from `SystemMessageUtils.stringify` (`7/Xl0S`, module 861464)
     are drawn by the operating system, outside the page, like the tray menu (see `translateTrayStrings`).
  To tell which one the maintainer saw: where the French notice appeared (message list, a preview line, a desktop
  notification) and whether a member's nickname reads like a fragment.
- **Expected** (Corsu usage, lexicon.tsv:116373, 118005–118007, 117998–118002, 114717, 575; not read by a speaker):
  " hà aghjuntu ", " à u gruppu.", " hà cacciatu ", " da u gruppu.", " hà lasciatu u gruppu.", " hà spirlatu ",
  "un messaghju", " in stu canale. Vede tutti i ", "messaghji spirlati"; preview line "Work hà aghjuntu Error à u
  gruppu."; a real message with the same words stays French (C4, C5: PASS).

## Baseline result lines (0.28.1, Vencord 7f0c10c, headless Chrome 152)

48 PASS, 14 FAIL (exit code 1). The failing lines:

```
FAIL: A1 DM composer placeholder at load = 'Envoyer un message à @Ron' (expected 'Mandà un messaghju à @Ron')
FAIL: A2 placeholder translated again after the draft is erased = 'Envoyer un message à @Ron' (expected 'Mandà un messaghju à @Ron')
FAIL: A3 DM composer placeholder after navigation (node reused) = 'Envoyer un message à @Error' (expected 'Mandà un messaghju à @Error')
FAIL: A3 group DM composer placeholder inserted after load = 'Envoyer un message dans Work, Error' (expected 'Mandà un messaghju in Work, Error')
FAIL: B1 DM search placeholder wording = 'Circà Ron' (expected 'Circà in Ron') [proposal]
FAIL: B1 DM search aria-label wording = 'Circà Ron' (expected 'Circà in Ron') [proposal]
FAIL: C2 fragment translated next to a nickname 'a ajouté' = ' a ajouté ' (expected ' hà aghjuntu ')
FAIL: C3 pin (yIDvPL): verb = ' a épinglé ' (expected ' hà spirlatu ')
FAIL: C3 pin (yIDvPL): link 'un message' = 'un message' (expected 'un messaghju')
FAIL: C3 pin (yIDvPL): middle = ' dans ce salon. Voir tous les ' (expected ' in stu canale. Vede tutti i ')
FAIL: C3 pin (yIDvPL): link 'messages épinglés' = 'messages épinglés' (expected 'messaghji spirlati')
FAIL: C3 pin (R7vZGZ): sentence = ' a épinglé un message dans ce salon. Voir tous les ' (expected ' hà spirlatu un messaghju in stu canale. Vede tutti i ')
FAIL: C3 pin (R7vZGZ): link = 'messages épinglés' (expected 'messaghji spirlati')
FAIL: C5 group notice in a message preview line = 'Work a ajouté Error au groupe.' (expected 'Work hà aghjuntu Error à u gruppu.')
```

Passing on 0.28.1: the composer's aria-label, the draft and caret, the search mechanics, the group add/remove/leave
notices inserted after load (names Work, Error, Ron and "a ajouté" kept), real messages with the same words, and no
double translation (every checked value unchanged after the page writes it back twice and a second translator runs).

## Other French texts found in DMs, groups, friends, composers and notices

From the client code (not seen on screen); cause classes: **missing entry**, **wrong context**, **over-protection**,
**dynamic element ignored**, **stale reuse after navigation**.

| Where | French (key) | Likely cause |
|---|---|---|
| Composer of a DM / group / thread / forum | "Envoyer un message à {channel}" (4c+CAx), "… dans {channel}" (8lzR/R, Y6qWLc), "Envoyer un message" (YzpScd), "Salon en lecture seule." (RRvRp/) | over-protection (placeholder div outside the editor, case A) |
| Message list, group DM | "a changé l'icône du groupe." (OEdU6X/4wLp25), "a changé le nom du groupe : … Modifier le groupe" (geP3rU/rk0be9), "a supprimé le nom de groupe personnalisé." (AI1ZZr) | over-protection: name area where only `systemLabels` fragments are looked up (the fragments are in the dictionary) |
| Message list, calls | "a commencé un appel." (LuB5RD), "a commencé un appel qui a duré {d}." (7TeC1P), "Tu as manqué un appel de {u}." (43phHx), "… qui a duré {d}." (AcqBmO) | same; " qui a duré " and " a commencé un appel qui a duré " also missing entries |
| Message list, pins | " a épinglé ", "un message", " dans ce salon. Voir tous les ", "messages épinglés", "." (yIDvPL, R7vZGZ, lD5tup, 7mvRNF) | dynamic element ignored: the current split is unknown to `systemLabels` (case C3) |
| Message list, friends | "a accepté ta demande d'ami." (H/9Tlj), "Tu as accepté la demande d'ami envoyée par {u}." (S6PRsh), with note (IquUXd, ZOZy2q) | over-protection (name area), fragments in the dictionary |
| Message list, threads | "a commencé un fil : {t}. Voir tous les fils." (cZ9Uf2), "a ajouté {t} au fil." (tusv2h), "a retiré {t} du fil." (32QI5/) | over-protection (name area) |
| Message list, servers | boosts (SbSWvY, yfC9ds, PO9uJD, cUfTTE), "a ajouté {app} au serveur." (/qIck6), raid alert (W0UBI3), applications (21R6Ch, Bz/QC2, Kpkesg) | over-protection; several fragments are missing entries (" a boosté ce serveur ", " au serveur.", " a signalé un raid sur ") |
| Any notice where a member's nickname equals a fragment | e.g. a nickname "a ajouté" | wrong context: the name guard also blocks the fragment (C2) |
| Message preview lines (friends/DM widget rows) | every system notice as one string (MMN2Jq, L2FyVq, 5v2xa8, OEdU6X, oItgEw, vfkjqx…), typing "{a} est en train d'écrire..." (lJ9sZX, rB0CUa, StKThj) | over-protection: `span.messageContent__7c4a2` is read as what people write (C5) |
| Desktop notifications | system notices via SystemMessageUtils.stringify (7/Xl0S…) | outside the page (drawn by the OS), not reachable by the page translator; unverified |
| Friends list (chunk fac1b27ad9e698a9) | "Tes demandes" (JHcSBI), "Masquer les notes" (QX4H2E), "Voir la note" (xZupEi), "Personnaliser la liste d'amis" (wvbB3Z), "Regrouper les ami(e)s dans le salon vocal" (/b1eZT) and its description, sort descriptions (IzzWNM, lE79Lm) | missing entry |
| Search settings popover (not French, wording) | "Recherche dans tous tes MP" (ji3jTF) → "Ricerca in tutti i to MP", "Tu recherches dans tous les MP" (8lklch) → "Cerchi in tutti i MP", beside "Circà" everywhere else in search | translated, but three verbs for one action: for the reviewer (inventory batch 01) |
| Overlay / invitations | "Déverrouiller pour répondre {keybind}" (Odi54y), "Déverrouiller pour rejoindre {keybind}" (aB5xLy) | missing entry |

No stale-reuse failure was found in these simulations: reused text nodes and attributes (composer aria-label, search
placeholder, group notices) were translated again; the composer's placeholder failed for the reason above, not
because of reuse.

## Limits

- Simulated pages in headless Chrome, with React's records imitated (fibers and props on the nodes), not the real
  Discord desktop app (Electron 1.0.166) nor a real account; class names and keys are those of the web client of
  2026-10-27, which can differ from the desktop build the maintainer runs.
- C is not reproduced in the message list itself; the candidate causes above are backed by the client code and by
  the failing cases, not by an observation of the maintainer's screen.
- The Corsican expected values repeat Corsu's own rows (Corsu usage) or an AI proposal ("Circà in {name}"); none was
  validated by a Corsican speaker, and no online dictionary was queried.
