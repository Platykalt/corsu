# Continuité du projet

Document de reprise, tenu à jour à chaque étape. Il renvoie aux documents détaillés plutôt que de les répéter.
Dernière mise à jour : 16 octobre 2026, après la passe de stabilisation (Corsu 0.22.0, publiée le 16 octobre 2026).

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

## Stabilisation du 16 octobre 2026

Correctifs, avec ce qui les prouve :

| Problème | Cause | Preuve |
| --- | --- | --- |
| Icône de Firefox en page blanche (barre des tâches, bouton « navigateur préféré ») | Firefox Corsu ne se reconnaissait pas comme navigateur par défaut ; « Définir par défaut » écrivait `userapp-Firefox-*.desktop` sans icône, vers le dossier versionné de la copie, lancé sans le lanceur de Corsu | Reproduit avec le vrai Firefox (Marionette) ; `tests/e2e/check_firefox_default.py` en CI Linux ; test unitaire avec le fichier réel |
| Échec Windows `FAIL: http://127.0.0.1:9/ ?` | Le chargement about:blank du nouvel onglet remplaçait parfois la navigation (`net::ERR_ABORTED`) ; même Chrome 155.0.8059.84 avant et après | 1 à 3 démarrages sur 40 sur un vrai Windows ; 80/80 après correction, dont 12 récupérés ; la CI finale l'a rencontré et récupéré |
| `installation.json` perdu si l'écriture est interrompue | Écriture directe | Écriture atomique + version précédente ; test unitaire |
| Pack de langue, installateur Vencord, copie d'application tronqués pris pour complets | Écriture directe, suppression avant copie | Tests unitaires |
| Logiciel annoncé « Installé » sans rien changer | Résumé fondé sur la demande | Test unitaire |
| Notepad++ : une langue choisie ensuite arrêtait l'installation | `RuntimeError` non interceptée | Test unitaire |
| Logiciel ouvert pendant la désactivation : retour perdu | Il réécrit ses réglages en quittant | Test unitaire : il reste en corse et activé, avec un message |
| Fichiers Windows : fins de ligne CRLF et BOM | BOM devant la première clé : clé dupliquée | Test unitaire |
| Fenêtre Corsu « fermée » si l'état est endommagé | Erreur 500 | Capture hors écran : bandeau d'erreur |

Vérifié avec de vrais logiciels : Firefox (Linux, Windows, macOS en CI ; Linux en local), Chrome for Testing
(Linux, Windows), 7-Zip, VLC et Notepad++ sur un vrai Windows (deux activations, retour, réactivation, choix gardé à
la désinstallation), VLC sous Linux. Seulement sur des fichiers et un registre simulés : WinMerge, SumatraPDF,
FileZilla, HandBrake, VeraCrypt, et tout macOS hors Firefox. Aucune fenêtre de ces logiciels n'a été regardée.

Ordinateur du mainteneur, réparé le 16 octobre 2026 par `repair_default_browser()` du dépôt : sauvegarde dans
`~/.local/share/corsu/backups/manual-firefox-default-2026-10-16/`, `userapp-Firefox-DQPWW3.desktop` retiré, seules
les lignes Firefox de `~/.config/mimeapps.list` changées. `xdg-mime` et `gio` donnent `firefox.desktop` (Firefox Corsu,
`Icon=firefox` du système, `Exec=~/.local/bin/firefox-corsu`) ; cache KDE reconstruit. Vérifié dans les fichiers
seulement : l'icône à l'écran n'a pas été regardée. Corsu 0.21.0 y est encore installé : son lanceur ne donne pas
`MOZ_APP_LAUNCHER`, donc cliquer sur « Définir par défaut » dans Firefox recréerait l'entrée avant la mise à jour.

## Prête pour des testeurs ?

- Cœur de Corsu (installation, activation, désactivation, désinstallation, mise à jour) : oui, CI verte sur les trois
  systèmes.
- Firefox, Chromium (pas macOS), Discord/Vesktop : oui.
- 7-Zip, VLC, Notepad++ : oui (vrai Windows ; VLC aussi sous Linux). WinMerge, SumatraPDF, FileZilla, HandBrake,
  VeraCrypt : expérimentaux (fixtures seulement).
- Minecraft Java 26.3 : expérimental, jamais essayé en jeu ni relu par un locuteur. Bedrock, extension web :
  prototypes.
- La version 0.22.0 n'est ni étiquetée ni publiée : à décider par le mainteneur.

## Itération du 16 octobre 2026 (soir)

- Ordinateur du mainteneur mis à jour en 0.22.0 avec l'archive Linux testée par la CI (commit `18c48e3`, SHA-256
  `4d626d71…5d05`) : parties `desktop`, `discord`, `firefox`, `minecraft`. Instance Prism Launcher `26.3` : pack
  copié, `lang:co_fr` (sauvegarde de `options.txt` dans `~/.local/share/corsu/backups/`). Pas encore vu en jeu.
- Défaut trouvé pendant cette mise à jour réelle, corrigé : la copie installée de Corsu n'avait pas `minecraft/java`,
  l'installation s'arrêtait. Le parcours d'archive de la CI installe désormais Minecraft dans une instance Prism.
- Défaut corrigé : `set_ini` plantait (KeyError) au second passage (VLC Flatpak).
- Fenêtre : état structuré par logiciel (`state['results']`) ; le résumé de l'installeur lit le même enregistrement.
- Windows : raccourci Corsu avec `corsu.ico` (dans `DATA`, hors des copies supprimées par les mises à jour) ;
  vérifié sur un vrai Windows de la CI par les métadonnées du raccourci, pas à l'œil.
- Archives : installées depuis un dossier avec espace et accent, dossier supprimé, mise à jour par `update.py`
  depuis les mêmes archives (`CORSU_DOWNLOAD_BASE`, somme vérifiée), désinstallées, sur les trois systèmes. Les tests
  sur la version publiée (`smoke`) ne tournent qu'avec une étiquette `v*`.
- Audacity 3/4, Tenacity, fre:ac : faits par un agent sur la branche locale `integrations-audio` (non fusionnée,
  pour la version suivante). Audacity 3, Audacity 4 et Tenacity lancés pour de vrai sous Linux (AppImages, dossier
  personnel jetable) : corse à l'écran ; Windows et macOS sur fixtures ; fre:ac jamais vu lancé. Pendant ses essais,
  fre:ac a créé deux dossiers vides dans le vrai dossier personnel (`~/.config/freac`, `~/.cache/freac`), retirés.
- Version 0.22.0 publiée le 16 octobre 2026 (étiquette `v0.22.0` sur `d94e4f0`, avec l'accord du mainteneur) :
  tous les tests de la CI, puis installation en une ligne depuis la version publiée sous Linux et Windows (pas de
  test de ce type sous macOS). Suite : fusionner `integrations-audio`, PDFsam, Poedit.

## Minecraft Java, toutes les versions (17 octobre 2026)

- Corsu construit et installe un pack pour chaque version publiée de 1.6.1 à 26.3 (87 versions), choisi d'après la
  version de chaque instance (Prism Launcher, MultiMC, lanceur officiel, Fabric/Quilt/Forge/NeoForge). Contrat et
  formats : [MULTIVERSION.md](../minecraft/java/MULTIVERSION.md) ; état : [STATUS.md](../minecraft/java/STATUS.md).
- Couverture des traductions : 87/87 versions complètes (base 26.3 + `history.json`, 3 978 paires : 507 reprises,
  1 755 clés renommées, 482 adaptées, 1 234 nouvelles), toutes écrites par IA.
- Vérification technique : 87/87 par `tools/mcversions.py verify all` (règles Python, puis le jar de chaque version
  charge le fichier de langue et rend chaque texte : 0 problème). La CI refait les 87 contrôles Python et 9 versions
  avec leur propre code.
- Essais en jeu : 26.3 seulement (instance Prism du mainteneur ; journal du jeu). Relecture humaine : 0.
- Défaut corrigé : le pack listé aussi dans `incompatibleResourcePacks` n'était pas sélectionné au démarrage.
- Ordinateur du mainteneur mis à jour avec l'archive CI de `9ad7f09` : `options.txt` de l'instance inchangé.
- Hors périmètre : snapshots, préversions, versions avant 1.6.1 ([other-versions.md](../minecraft/java/other-versions.md)).

## Version 0.23.0 (17 octobre 2026)

- Une seule installation gérée par utilisateur : archive, commande en une ligne et bouton « Mettre à jour » passent
  par `src/installer.py` (contrat : [update-architecture.md](update-architecture.md)). Plus récente → mise à jour ;
  même version → réparation ; plus ancienne → refusée (`--allow-downgrade`). Parties désactivées gardées désactivées,
  originaux jamais réenregistrés, verrou `DATA/lock`, téléchargement de l'étiquette exacte (SHA-256 + version de
  l'archive), extraction sûre, copie complète avant bascule, retour des lanceurs en cas d'échec.
- Fenêtre : rubrique Mise à jour (versions, vérification au démarrage, mise à jour, installation automatique
  facultative désactivée par défaut, redémarrage vers la nouvelle copie), instances Minecraft en attente.
- CI : mise à jour depuis les 0.21.0 et 0.22.0 publiées sur les trois systèmes (`tests/e2e/check_update.py`),
  réparation, refus d'une version plus ancienne, archive tronquée, interruption, deux installeurs simultanés,
  désinstallation.
- Discord : les noms des personnes (pseudonymes, noms d'affichage, surnoms, noms de serveurs, salons, rôles) ne sont
  plus traduits ; reconnus par leur origine (props React), vérifié dans une vraie page Chrome en CI
  (`tests/e2e/check_discord_names.py`). Pas encore observé dans le Discord du mainteneur.
- Minecraft : pages générées par `tools/mcreport.py` (87 versions, limites, empreinte de chaque vérification).
- Incident : deux tests de l'installeur réécrivaient la vraie entrée de menu Corsu du mainteneur quand ils tournaient
  sur sa machine (corrigé : tests isolés ; l'entrée est réparée par la mise à jour 0.23.0).

## Nuit du 17 octobre 2026 (version de développement, rien de publié)

- Audacity 3 et 4, Tenacity et fre:ac intégrés à la liste des logiciels (branche `integrations-audio` fusionnée),
  avec la marche à suivre quand Corsu les laisse tels quels. Audacity 3, Audacity 4 et Tenacity lancés pour de vrai
  sous Linux (AppImages officielles, dossier jetable) : corse à l'écran ; le reste sur dossiers simulés.
- VLC 3.0.x : brouillons IA des 1 760 messages manquants dans `contrib/vlc/co.po` (marqués `#, fuzzy`, non relus ;
  1 réemploi exact, 61 adaptés d'une suggestion de la mémoire, 1 698 nouveaux ; amont `e66842d`), validés par
  `msgfmt -c --check-format`. À relire par un locuteur avant tout envoi en amont (Transifex de VLC, idéalement avec
  Patriccollu) ; rien n'a été envoyé ni mis en service. Mots à vérifier d'abord : [contrib/vlc/README.md](../contrib/vlc/README.md).

## Blocages et ce qui demande une personne

- Essai réel de Minecraft Java 26.3 ([TESTING.md](../minecraft/java/TESTING.md)) et de Bedrock.
- Relecture par des locuteurs : lots prêts dans [review-batches](../minecraft/java/review-batches/) ; modèles de
  demande non envoyés.
- Décisions du mainteneur : licence des textes de Corsu (CC0 recommandé, rien n'est changé). « Servore » est
  attesté en informatique (ADECEC, *Lingua corsa è Internet*, Thiers et Filippi, 1999) : ce n'est donc pas une
  raison de tout remplacer. *Servitore* reste le choix là où il est appliqué (Minecraft). Discord n'est pas
  modifié ([décision D1](../minecraft/java/decisions-2.md)).
- Restent visibles : le raccourci Windows « Corsu » montre l'icône de Python ; la fenêtre n'indique pas encore les
  logiciels activés en partie.
- macOS : la CI tourne sur un vrai Mac de GitHub (macos-latest). Firefox y est installé, lancé et lu par les
  vérifications automatiques, et l'archive y est installée puis mise à jour. Personne n'a regardé l'écran d'un Mac.
  Les autres logiciels n'y sont testés que sur fixtures ; FileZilla et VeraCrypt n'y sont pas activés (chemins de
  réglages non confirmés).

## Mesures de réutilisation

- VLC 3.0.x (`po/co.po`, 6 203 textes) : 4 443 traduits en amont, 1 760 manquants. `tools/tm.py match` sur la mémoire
  actuelle : 10 réutilisations exactes compatibles, 70 suggestions à relire, 0 conflit, 1 750 restent à traduire.
  Compléter VLC est donc surtout un travail de traduction nouveau, quelle que soit la taille du lexique. Il peut se
  préparer dès maintenant dans la mémoire de Corsu ; l'envoi en amont (Transifex de VLC, idéalement avec Patriccollu)
  est une étape ultérieure, pas un préalable. Les chiffres « textuels » (correspondance par le texte seul) sont des
  estimations préliminaires ; seuls les réemplois compatibles avec le contexte comptent comme acquis.
- Transmission (essai de l'outil, catalogue sans corse) : 597 textes uniques, 39 réutilisations exactes, 36
  suggestions, 30 conflits refusés.

## Prochaines étapes

1. Audacity / Tenacity, fre:ac, PDFsam, Poedit : même mécanisme, sources dans [apps-research.md](apps-research.md).
2. Bedrock : un essai en jeu, puis traduire les écrans les plus visibles.
3. Telegram : un même nom de pack et un même lien pour toutes les applications, mais chaque application (Desktop,
   Android, iOS, macOS, Web) a ses propres textes à traduire ([roadmap-candidates.md](roadmap-candidates.md)).
