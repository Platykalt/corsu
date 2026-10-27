# Discord linguistic review: progress

AI review (Claude), started 2026-10-27 on branch `fix-discord-0.28.2`. Not a human validation: every decision is a row
of `lexicon/review-discord-2026-10.tsv` (applied ones also in `lexicon/corrections.tsv`). Rules: AGENTS.md (full meaning
before abbreviations, provenance, no scripted dictionary queries: INFCOR and BDLC questions go to the list below).

Inventory: the `# Discord:` sections of `lexicon/lexicon.tsv` hold 22,430 rows. Batches are chosen by the first verb
of the French text (frequent actions first). "Examined" means each row read with its French and English; a row
not listed in the review file was found acceptable as it is.

## Done

| Batch | Rows examined | Applied | Proposals |
|---|---|---|---|
| Remove/kick/ban/timeout/leave (Retirer du groupe, Exclure, Expulser, Bannir, Quitter le groupe) | about 25 | 4 | 1 (ban forms) |
| Rechercher / Chercher / Recherche (with "Rechercher {name}" of fix-discord-0.28.2) | 89 | 3 + 1 | 2 |
| Envoyer | 66 | 0 | 1 (signalement) |
| Retirer | 45 | 0 | 2 |
| Quitter | 19 | 0 | 0 |
| Bloquer | 16 | 0 | 0 |
| Signaler | 37 | 0 | 0 |
| Épingler | 8 | 0 | 1 (post) |
| Enregistrer | 13 | 0 | 0 |
| Inviter | 33 | 0 | 0 |
| Supprimer | 98 | 2 | 2 |
| Rejoindre | 54 | 0 | 0 |
| Réinitialiser | 34 | 4 | 1 (cugnome) |
| Modifier | 95 | 0 | 2 (banner, wishlist) |
| Ajouter | 154 | 0 | 3 |

About 785 rows examined of 22,430 (3.5 %); the rest is not reviewed.

## Remaining batches (in this order)

1. Other frequent verbs: Afficher/Masquer, Activer/Désactiver, Créer, Ouvrir/Fermer, Copier, Gérer, Accepter/Refuser,
   Annuler, Confirmer, Partager, Télécharger, Mettre en sourdine / Rendre muet, Sélectionner, Changer, Choisir.
2. Discord rows whose Corsican was imported from Mozilla, VLC or Chromium rows (same French text): check that the sense
   is the same in Discord (as "Bio", "Salon", "Envoyer" were).
3. Templates with values (`{user}`, `{name}`, `{count}`): agreement and prepositions around the value.
4. Harmonisation passes for the proposals (banner, post, wishlist, favourites, phone, authentication, reminder,
   library, commands, report) once a word is chosen for each.
5. Everything else, by section of the Discord settings.

## Open questions for INFCOR (to look up by hand, one entry at a time)

1. *expulser*: is the usual Corsican form "espulsà" (Corsu's convention) or "spulsà" (ADECEC football lexicon)?
2. *bannir*: "sbandisce", "bandisce" or "sbandì" for banning someone from a server; and is "à" before the person
   ("Bandisce à {username}") usual in a short button?
3. *pseudo / pseudonyme* (a nickname chosen by the user): does "cugnome" mean nickname, or family name? Alternatives:
   "soprannome", "pseudonimu".
4. *exclure temporairement* (timeout): is "esclude per un tempu" natural, or is there a set expression?
5. *bannière* (profile banner): "bandera", "banderola" or "banderone"?
6. *quête* (Discord Quests): "cerca" or another word?
