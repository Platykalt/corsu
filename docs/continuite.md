# Continuité du projet

Document de reprise, tenu à jour à chaque étape. Il renvoie aux documents détaillés plutôt que de les répéter.
Dernière mise à jour : 16 octobre 2026 (Corsu 0.22.0, non publiée).

## Objectifs retenus

1. Quand Corsu est installé, les logiciels présents sur l'ordinateur qui ont une traduction corse s'ouvrent en corse,
   avec une couverture annoncée honnêtement ([état des traductions](fr/etat-des-traductions.md)).
2. Minecraft: Java Edition en corse, fiable et sans risque pour les réglages des joueurs
   ([STATUS](../minecraft/java/STATUS.md)).
3. Une base de traduction contextuelle (application, clé, contexte, provenance, licence, statut de relecture) qui
   accélère chaque nouvelle intégration sans propager les contresens ([lexicon/memory](../lexicon/memory/README.md)).

## Décisions et leurs preuves

| Décision | Preuve |
| --- | --- |
| Activer d'abord la traduction livrée avec le logiciel, par son propre réglage de langue ; ne jamais restaurer un fichier de configuration entier | [apps-research.md](apps-research.md) ; tests `tests/test_apps.py` |
| VLC sous Linux : entrée de menu avec `LANGUAGE=co:…` (VLC n'a pas de réglage de langue sous Linux) | CI : vrai VLC d'Ubuntu, aide affichée en corse (`tests/e2e/check_vlc.py`) |
| Minecraft : seuls les dossiers de jeu en 26.3 sont modifiés ; rien n'est réécrit qui ne puisse être relu | `tests/test_lexicon_minecraft.py` |
| Une traduction propre à un logiciel n'est pas réutilisée ailleurs quand les applications divergent (`engine.lookup` refuse) | `tests/test_memory.py` |
| HandBrake n'est plus importé dans le lexique (GPL-2.0-only) mais son corse est activé dans HandBrake lui-même | [LICENSING-OPTIONS.md](../minecraft/java/LICENSING-OPTIONS.md) |
| Traductions écrites par IA : jamais présentées comme validées | [REVIEWS.md](../lexicon/REVIEWS.md), colonnes séparées de `minecraft/java/inventory.tsv` |

## Terminé et vérifié (au niveau indiqué)

- Activation automatique : VLC (Linux, Windows, macOS ; essai réel en CI sous Linux), 7-Zip, Notepad++, WinMerge,
  SumatraPDF (Windows), FileZilla, HandBrake, VeraCrypt (Windows, Linux) : tests unitaires ; 7-Zip, VLC et Notepad++
  aussi sur un vrai Windows en CI.
- Minecraft Java 26.3 : pack complet, vérifié par le code du jeu, installation prudente ; pack facultatif des phrases
  d'accueil et du poème de fin.
- Mémoire de traduction contextuelle et `tools/tm.py` (extraction, réutilisation exacte compatible, suggestions,
  conflits, mises à jour).
- Prototype d'extension web pour GitHub ([webext.md](webext.md)) et prototype Bedrock ([STATUS](../minecraft/bedrock/STATUS.md)) :
  jamais essayés dans un navigateur ou un jeu réel.

## Blocages et ce qui demande une personne

- Essai réel de Minecraft Java 26.3 ([TESTING.md](../minecraft/java/TESTING.md)) et de Bedrock.
- Relecture par des locuteurs : lots prêts dans [review-batches](../minecraft/java/review-batches/) ; modèles de
  demande non envoyés.
- Décisions du mainteneur : licence des textes de Corsu (CC0 recommandé, rien n'est changé) ; « servitore » dans
  Discord.
- macOS : aucun logiciel n'a été essayé sur un vrai Mac ; FileZilla et VeraCrypt sous macOS ne sont pas activés
  (chemins de réglages non confirmés).

## Mesures de réutilisation

- VLC 3.0.x (`po/co.po`, 6 203 textes) : 4 443 traduits en amont, 1 760 manquants. `tools/tm.py match` sur la mémoire
  actuelle : 10 réutilisations exactes compatibles, 70 suggestions à relire, 0 conflit, 1 750 restent à traduire.
  Compléter VLC est donc surtout un travail de traduction nouveau, à faire en amont avec Patriccollu plutôt que dans
  Corsu.
- Transmission (essai de l'outil, catalogue sans corse) : 597 textes uniques, 39 réutilisations exactes, 36
  suggestions, 30 conflits refusés.

## Prochaines étapes

1. Audacity / Tenacity, fre:ac, PDFsam, Poedit : même mécanisme, sources dans [apps-research.md](apps-research.md).
2. Bedrock : un essai en jeu, puis traduire les écrans les plus visibles.
3. Telegram : un seul pack pour bureau et téléphone, après contact avec le propriétaire du pack « corsican »
   existant ([roadmap-candidates.md](roadmap-candidates.md)).
