# VLC 3.0.x — brouillons corses / Corsican drafts

## Français

`co.po` est le catalogue corse de VLC (branche `3.0.x`, `po/co.po`, dernier commit amont du fichier
`e66842dbd5223d41a8ad88f85ffce3637c57aa23` du 17/09/2026, lu le 17/10/2026, sha256
`40a24505…c17cddd`), traduit par Patriccollu di Santa Maria è Sichè. Les 1 760 messages qui n’y étaient pas
traduits ont reçu un **brouillon écrit par une IA, non relu**. Les 4 443 traductions de l’amont sont gardées à
l’identique, octet pour octet, ainsi que l’en-tête.

| | Messages |
|---|---:|
| Traduits en amont (inchangés) | 4 443 |
| Brouillons IA (`#, fuzzy`) | 1 760 |
| — dont réemploi exact de la mémoire (`tools/tm.py`) | 1 |
| — dont adaptés d’une suggestion de la mémoire | 61 |
| — dont nouveaux | 1 698 |
| Encore vides | 0 |

Chaque brouillon porte `# Corsu: AI draft, not reviewed (source: tm exact|suggestion|new)` et le drapeau
`#, fuzzy` : `msgfmt` et VLC l’ignorent tant qu’il n’a pas été relu. La terminologie suit les choix de Patriccollu
dans ce même fichier (esciuta, flussu, fiura, schedariu, cartulare, parolla d’intesa…).

**Relire** : ouvrir `co.po` dans Poedit ou Lokalize, corriger chaque entrée « approximative », puis retirer le
drapeau fuzzy (et le commentaire `# Corsu:`). Vérifier : `msgfmt -c --check-format -o /dev/null co.po`.

**Rien n’a été envoyé** à VLC ni à personne. Un envoi éventuel (Transifex de VLC, idéalement avec Patriccollu)
se fera seulement après relecture humaine. Ce fichier n’est pas utilisé par Corsu.

Licence : les fichiers `po` de VLC sont distribués sous la même licence que VLC (GPL-2.0-or-later, LGPL pour
libVLC) ; l’en-tête d’origine est conservé.

## English

`co.po` is VLC's Corsican catalogue (`3.0.x` branch, `po/co.po`, last upstream commit of the file
`e66842dbd5223d41a8ad88f85ffce3637c57aa23`, 2026-09-17, fetched 2026-10-17), translated by Patriccollu di Santa
Maria è Sichè. Its 1,760 untranslated messages now carry an **AI-written draft, not reviewed**. The 4,443
upstream translations and the header are kept byte-identical. Counts are in the table above.

Each draft has `# Corsu: AI draft, not reviewed (source: …)` and `#, fuzzy`, so `msgfmt` and VLC ignore it
until reviewed. **To review**: open `co.po` in Poedit or Lokalize, fix each fuzzy entry, then clear the fuzzy flag
(and the `# Corsu:` comment); check with `msgfmt -c --check-format -o /dev/null co.po`.

**Nothing has been submitted** to VLC or anyone else; submission (VLC's Transifex, ideally with Patriccollu) comes
only after human review. Corsu does not ship or use this file. Licence: same as VLC (GPL-2.0-or-later, LGPL for
libVLC); the original header is kept.
