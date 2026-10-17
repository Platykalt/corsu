# VLC 3.0.x — complément corse / Corsican complement

## Français

`co.po` est le catalogue corse de VLC (branche `3.0.x`, `po/co.po`, dernier commit amont du fichier
`e66842dbd5223d41a8ad88f85ffce3637c57aa23` du 17/09/2026, lu le 17/10/2026), traduit par Patriccollu di Santa Maria
è Sichè. Les 1 760 messages qui n’y étaient pas traduits ont reçu un brouillon écrit par une IA.

| Provenance et statut | Messages | Dans le catalogue expérimental |
|---|---:|---|
| Traduction amont (Patriccollu), inchangée octet pour octet | 4 443 | oui |
| Brouillon IA, relu par IA (2 lots thématiques + passe de cohérence, 17/10/2026) | 1 757 | oui |
| — dont gardés tels quels / corrigés | 1 579 / 178 | |
| Brouillon IA incertain après relecture IA | 3 | non |
| Validé par un locuteur | 0 | |

Les brouillons gardent le drapeau `#, fuzzy` tant qu’un locuteur ne les a pas validés, et un commentaire
`# Corsu:` qui dit leur statut. `review.json` garde pour chacun le brouillon d’origine, chaque relecture (qui, quand,
verdict, note) et le statut : `ai_draft`, `ai_reviewed`, `uncertain`, `human`. `TERMS.md` documente la
terminologie (termes attestés et sources, propositions, mots signalés, noms de genres musicaux) et les cas
incertains.

**Contrôler** : `python3 tools/vlcpo.py check` compile tout le catalogue **avec** les brouillons
(`msgfmt --use-fuzzy -c --check-format`) — une compilation normale les ignore et ne prouve rien sur eux — puis
vérifie chaque brouillon : formes plurielles, arguments (`%s`, `%1$s`, `%@`, `%1`, macros `PRI`), balises HTML,
raccourcis `&`, espaces, retours à la ligne, `:` et `...` finaux ; qu’aucun brouillon ne reprend la lettre de raccourci
d’une autre entrée du même menu de VLC (`MENUS` : barre de menus, menu contextuel, Média, Lecture, Audio, Vidéo,
Sous-titres, Outils, Vue, Aide — les doublons entre traductions amont sont seulement signalés) ; et que le catalogue privé des ajouts redonne
exactement le fichier amont (SHA-256).

**Construire le catalogue expérimental** (jamais installé par cette commande) :
`python3 tools/vlcpo.py build vlc.mo` (amont + statuts `ai_reviewed` et `human`).

**L’utiliser avec Corsu** (Linux, VLC 3.0.x du système, désactivé par défaut) : `--vlc-complement on`, puis
`--vlc-complement off` pour revenir au catalogue de VLC. Voir `src/apps/vlc_complement.py`. Essayé avec un vrai
VLC 3.0.20 et 3.0.24 (`tests/e2e/check_vlc_experimental.py`, `tests/e2e/check_vlc_complement.py`).

**Rien n’a été envoyé** à VLC ni à Patriccollu. Un envoi éventuel (Transifex de VLC, idéalement avec
Patriccollu) se fera seulement après relecture par un locuteur et avec l’accord du mainteneur de Corsu.

Licence : celle de VLC (GPL-2.0-or-later, LGPL pour libVLC) ; l’en-tête d’origine est conservé.

## English

`co.po` is VLC's Corsican catalogue (`3.0.x` branch, `po/co.po`, upstream commit
`e66842dbd5223d41a8ad88f85ffce3637c57aa23`, 2026-09-17, fetched 2026-10-17), translated by Patriccollu di Santa
Maria è Sichè. Its 1,760 untranslated messages received an AI draft. Counts by provenance and status are in the
table above: 4,443 upstream (byte-identical), 1,757 drafts reviewed by AI (1,579 kept, 178 corrected), 3 uncertain
(left out of the experimental build), 0 validated by a speaker.

Drafts keep `#, fuzzy` until a speaker validates them, plus a `# Corsu:` comment with their status; `review.json`
keeps each original draft, each review and the status. `TERMS.md` documents terminology and the open cases.

Check: `python3 tools/vlcpo.py check` (msgfmt with the fuzzy entries included, then Corsu's per-draft rules, no draft
taking an accelerator letter already used in the same VLC menu — clashes between upstream translations are only
reported —, and the upstream file must come back byte for byte). Build: `python3 tools/vlcpo.py build vlc.mo`. Use with Corsu (Linux,
system VLC 3.0.x, off by default): `--vlc-complement on|off`; see `src/apps/vlc_complement.py`.

**Nothing has been submitted** to VLC or Patriccollu; any submission comes only after a speaker's review and with
the Corsu maintainer's agreement. Licence: VLC's (GPL-2.0-or-later, LGPL for libVLC); the original header is kept.
