# Discord inventory for the linguistic review (0.28.2)

`docs/discord-inventory-0.28.2.tsv` lists every French string of Discord's public web client (fetched 2026-10-27,
`web.ad0b95d8568e0f6b.js`, 25,604 French catalogue strings) that the Corsu plugin translates: **21,748 rows** whose
French text, or its placeholder template, is a key of the dictionary the 0.28.1 plugin is built with
(`Vencord/src/userplugins/corsu/dictionary.json`). It is data for a reviewer; nothing in `lexicon/` was changed, and
nothing in it is a speaker's validation. A string looked up only by the translator's fallbacks (other letter case,
final punctuation, a count, pieces around separators) is not listed.

The TSV itself (5 MB) is not in the repository, so it does not ship in every archive: regenerate it (the client
files are untrusted data, only read as text):

```
python3 -I tools/discord_inventory.py CLIENT_DIR Vencord/src/userplugins/corsu/dictionary.json docs/discord-inventory-0.28.2.tsv
```

`CLIENT_DIR` holds `web.<hash>.js` and every lazy chunk under `CLIENT_DIR/all/`, named as the chunk map in
`web.<hash>.js` names them (`<id>.<hash>.js` or `<hash>.js`, from `https://discord.com/assets/`). The fetching was done
apart, in a separate folder; the tool itself makes no network request.

## Columns

| Column | Meaning |
|---|---|
| batch | review batch (below); rows are sorted by batch, cross-app rows first, then French |
| priority | the action verb of the batch, empty for the rest |
| key | Discord's catalogue key (e.g. `LDZtFO`), the same in every language |
| english | Discord's English (en-US catalogue) for that key |
| french | Discord's French, with `{name}` where Discord inserts a value; rich text flattened (link text kept) |
| corsican | what the plugin shows today |
| match | `direct` (the French is a dictionary key) or `template` (its placeholder shape is) |
| function | how the client code uses the key, from the property it fills: placeholder, accessibility label, title, label (option, field or menu item), menu item, description / instruction, tooltip, notification (toast), button or text, text; `formatted text` when the call is not a property; `not found in the client code` for keys no fetched chunk uses (dead strings, or code not in the web client) |
| component | the chunk(s) using the key (file name without hash suffix, `web` = main bundle), with the nearest `navId`, `displayName` or `analyticsName` when one is close |
| lexicon_row | `file:line` of the row the Corsican comes from: the first source `engine.application_words('Discord', 'Vencord')` reads it from (lexicon-fixes.tsv, then lexicon.tsv's Discord and Vencord sections, then the translation memory, then every other row); a person's own corrections are left out |
| lexicon_section | the heading of that row's part of the file |
| cross_app | `cross-app` when the Corsican comes from another program's rows (Mozilla, Chrome, KDE, VLC, Audacity…) or a shared section |
| cross_app_reason | why the sense may differ: the section, that row's English when it is not Discord's, a short label whose sense depends on where it is shown |

**Cross-app rows: 2,636.** In the priority batches: 01: 14, 02: 18, 03: 61, 04: 11, 05: 60, 06: 12, 07: 0, 08: 6,
09: 12, 10: 6, 11: 2, 12: 25, 13: 8, 14: 1, 15: 1 (237); the other 2,399 fill batches 16 to 21.

## Batches (how to resume)

Work batch by batch; within a batch, the cross-app rows come first. A batch is a French stem found anywhere in the
string (so "Effacer l'historique de recherche" is in 01).

| Batch | Stem | Rows |
|---|---|---|
| 01 | rechercher, chercher, recherche | 242 |
| 02 | envoyer | 586 |
| 03 | ajouter | 596 |
| 04 | retirer | 132 |
| 05 | supprimer | 357 |
| 06 | quitter | 84 |
| 07 | rejoindre | 411 |
| 08 | inviter | 297 |
| 09 | bloquer | 121 |
| 10 | signaler | 108 |
| 11 | épingler | 73 |
| 12 | modifier | 288 |
| 13 | enregistrer | 98 |
| 14 | réinitialiser | 49 |
| 15 | exclure, expulser, bannir, débannir, révoquer (stems: also catches "exclusif") | 267 |
| 16–61 | the rest, 400 rows each (16–21: cross-app rows), 39 in 61 | 18,039 |

To resume: note the last batch done; regenerating with the same client and dictionary gives the same batches. After
lexicon changes the Corsican and the provenance columns change, the batches do not (they depend on the French only).

## Removing people and leaving: never confuse them

What each action does in Discord, and what the plugin shows today (0.28.1). Provenance in `lexicon_row` of the TSV.

| Action | What it does | Keys (French → English) | Corsican today |
|---|---|---|---|
| Remove from group | takes a member out of a group DM (the owner) | `n5zMI+` Retirer du groupe → Remove From Group | Caccià da u gruppu (lexicon.tsv:1443, **Firefox section**: cross-app) |
| Leave group | you leave a group DM | `26C4oi` Quitter le groupe → Leave Group | Lascià u gruppu (lexicon.tsv:15049, **Chrome section**: cross-app) |
| Kick | removes a member from a server; they can come back with an invite | `3glT6Z`, `fQUQIJ` Expulser → Kick; `pBNv6i` Expulser des membres → Kick Members; `03N0UL` Expulser l'utilisateur → Kick user; `9l/iTS` Expulser {user} → Kick {user}; `1Ie87p` Expulser {user} du serveur → Kick {user} from Server; `yOiJHB` Expulser '{user}' | Espulsà (lexicon-fixes.tsv:28); Espulsà membri; Espulsà l'utilizatore; **Scaccià {user}**; Espulsà {user} da u servore; Espulsà '{user}' |
| Ban | removes a member and stops them from coming back | `5MBJ5M` Bannir → Ban; `oTBA7N`, `2a50fF` Bannir des membres → Ban Members; `HWuskv`, `I+Cbum` Bannir l'utilisateur → Ban User; `WnpUBi`, `WDR8Xd` Bannir {user}/{username}; `jeKpok` Bannir {username} ?; `i62APf` Bannir {user} du serveur; `TuAZuW` Bannir '{user}' | **Sbandisce** (lexicon-fixes.tsv:27); Sbandisce membri; Sbandisce l'utilizatore; **Bandì** {user}; **Bandisce à** {username} ?; Bandisce à {user} da u servore; Bandì '{user}' |
| Timeout | the member stays but cannot write, speak or react for a while | `Nd4BcM`, `MlPTIi`, `kTlLrz`, `xpsADY` Exclure temporairement → Timeout; `KkPcep`, `6WPxY2` Exclure temporairement l'utilisateur; `Xz2njA` … un membre; `+RL6pz`, `iqwXvc` … des membres; `FN7NIS` Exclure '{user}' temporairement; **`OhsOy0` Exclure {user} → Timeout {user}**; `LXTQr5` Exclure l'utilisateur jusqu'à : {newValue} → Set timeout for user until {newValue} | Esclude per un tempu; Esclude tempuraneamente l'utilizatore; Esclude un membru per un tempu; Escludisce temporaneamente membri; Escludà '{user}' tempurariamente; **Scaccià {user}**; `LXTQr5` not in the dictionary |

For the reviewer (observations, not corrections):
- **Collision:** `OhsOy0` "Exclure {user}" (Timeout) and `9l/iTS` "Expulser {user}" (Kick) both show **"Scaccià
  {user}"**, in the same user context menu (`241469c6f326c780`, `f94331171f9cc6ed` ThreadUserContextMenu). A timeout
  would read as a kick. Discord's French "Exclure" alone means the timeout here (English "Timeout {user}").
- Kick is "Espulsà" in five rows and "Scaccià" in one; ban is "Sbandisce", "Bandì" and "Bandisce à"; timeout mixes
  "Esclude / Escludisce / Escludà" with "per un tempu / tempuraneamente / temporaneamente / tempurariamente"; buttons
  mix an infinitive (Espulsà, Caccià) and a third person (Sbandisce, Esclude).
- "Retirer du groupe" and "Quitter le groupe" come from Firefox and Chrome rows; the wording matches Discord's sense
  here, but the provenance is another program.

## Still French in DMs, groups, friends, composers and notices

See `docs/discord-review-0.28.2.md` ("Other French texts…"), each with its cause class (missing entry, wrong context,
over-protection, dynamic element ignored, stale reuse after navigation).
