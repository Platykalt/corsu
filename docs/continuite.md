# Continuité du projet

Document de reprise, tenu à jour à chaque étape. Il renvoie aux documents détaillés plutôt que de les répéter.
Les sections datées après « État actuel » sont l'historique : ce qui y est dit ouvert a pu être corrigé depuis.

## État actuel (18 octobre 2026)

- **Version publique : 0.25.1** (tag `v0.25.1` sur `bb64655`, release
  https://github.com/Platykalt/corsu/releases/tag/v0.25.1, dernière version ; CI 39121451094). Vérifiée depuis les
  téléchargements publics dans un conteneur Debian jetable : sommes conformes, `check_migration.py --from 0.24.0`
  84 PASS, mise à jour réelle 0.24.0 → 0.25.1 par son propre `update.py` (Firefox reste désactivé). Les notes de la
  release ont un tableau « Téléchargements par usage » (texte seul modifié ; tag et fichiers inchangés).
  `v0.25.0` est un tag sans release (course sur `installation.json` sous Windows, corrigée en 0.25.1) ; il reste tel
  quel. La branche `fix-0.24.1` est dépassée : son correctif est dans la 0.25.1.
- **`main`** : code de la 0.25.1 et documentation de la version publique (README par usage, sources et droits,
  crédits, guides téléphone pour le paquet 1.0, [provenance du lexique](../lexicon/PROVENANCE.md)).
- **`next-0.26`** (en préparation, non publiée ; la publication attend l'accord du mainteneur) :
  - **Minecraft** : revue IA d'octobre 2026 (`minecraft/java/review-2026-10/` : APPLIED, REJECTED, TRACKING), deux
    tours appliqués, vérifiés sur les 87 versions avec le code de chaque jeu. Troisième tour
    (`review-2026-10/ROUND3.md`, `round3.tsv`) : comptes réconciliés (1 131 + 27 = 1 158 modifications, 1 157 textes
    distincts ; 30 lignes différées), 11 décisions sensibles relues sur leurs sources (rail : *Ragliu* gardé, ADECEC
    *La chaudronnerie* et lexique des Chemins de fer de la Corse p. 101 ; *Tonu* gardé ; raisonnements « ce mot veut
    dire autre chose » corrigés), aucun texte changé ; décisions dans `lexicon/memory/minecraft-java.jsonl` (jamais
    réutilisées pour un autre logiciel) ; consultations manuelles à faire listées. Relecture humaine : 0.
  - **Clavier Keyman** (paquets 1.1) : casse gardée, vocabulaire refait (`keyboard/data`), 446 noms de lieux
    (Wikidata, CC0), préférences Cismuntincu et Pumuntincu **expérimentales** (361 mots pondérés autrement). Vérifié
    dans le moteur de Keyman 18.0.254 (CI) et sur émulateur Android 14 ; **pas sur téléphone, pas sur iOS**.
    Suggestion choisie au milieu d'un mot : Keyman ne remplace que la partie à gauche du curseur ; les modèles 1.1
    (`keyboard/whole-word.js`) effacent la fin du mot sous Android (moteurs 18.0.254 et 19.0.309, application
    18.0.254 sur émulateur), pas sous iOS, où Keyman ignore l'effacement à droite. Ticket préparé, non envoyé :
    `docs/keyman/ticket-mid-word-suggestion.md`.
  - **Téléphone** : page « Sur téléphone » de la fenêtre, guides ; bascules de publication dans
    [release-checklist-phone.md](release-checklist-phone.md).
  - Corrigés pour les prochaines publications : une somme `.sha256` par pack Minecraft ; version des captures lue
    dans `src/release.json`.
- **Chantier en cours (18 octobre 2026)** : mise à jour (faux « à jour » vu sous 0.24), textes encore non traduits
  (« Fermer Discord », « Display Configuration ») et logo, clavier (majuscules, retour sur un mot, noms propres,
  variantes, Canopé), revue sémantique Minecraft. Résultats et preuves ajoutés ici à la fin du chantier.
- **INFCOR** : un agent a lancé 219 requêtes par script (une par mot, 3 s d'intervalle) ; arrêté. Aucune
  interrogation automatisée d'INFCOR ni d'un autre dictionnaire : consultation page par page seulement ([AGENTS.md](../AGENTS.md), test `tests/test_sources_policy.py`, incident
  décrit dans `minecraft/java/review-2026-10/ROUND3.md`).
- Tests unitaires : `HOME=$(mktemp -d) python3 -m unittest discover -s tests -t . -q` (sans `-t .`, 13 erreurs
  d'import qui ne signalent rien). CI d'une branche autre que `main` : `gh workflow run ci.yml --ref <branche>`.
- **Attend une personne** : essai du clavier sur un vrai téléphone (Android, iPhone) ; relecture par un locuteur
  (Minecraft, Discord : `lexicon/review-discord-2026-10.tsv`, VLC : 3 cas dans
  [contrib/vlc/TERMS.md](../contrib/vlc/TERMS.md)) ; essais Minecraft en jeu ; libellés Discord observés dans un vrai
  Discord ; décision de publier la 0.26.
- **Limites connues** : complément VLC absent sous Windows, macOS, Flatpak, Snap ; Audacity 4 expérimental sous
  Windows et macOS ; fre:ac et Audacity vérifiés seulement sur dossiers simulés hors Linux ; fenêtre non observée
  dans WebView2 ni WKWebView ; Keyman 18 sans correction automatique, remplacement seulement à gauche du curseur.

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
## Historique : 0.24.0 et candidate 0.25 (17 et 18 octobre 2026)

États de l'époque, remplacés par « État actuel » ci-dessus.

- **0.24.0 publiée** (17 octobre 2026) : tag `v0.24.0` sur `78697ea`, release
  https://github.com/Platykalt/corsu/releases/tag/v0.24.0 marquée dernière version (run CI 39040761519 : tests,
  archives, essais de bout en bout sur les trois systèmes, publication et installation en une ligne réussis ; un
  test unitaire instable relancé, cause corrigée sur `next-0.25`). Contenu : Audacity 3 et 4, Tenacity, fre:ac ; le
  complément VLC expérimental, désactivé par défaut, Linux seulement, avec son interrupteur dans la fiche VLC et
  `--vlc-complement on|off`.
- **Vérifié depuis les téléchargements publics** (conteneur Debian jetable) : release dernière pour l'API GitHub ;
  archives Linux, Windows, macOS et autres fichiers conformes à leurs `.sha256` et à la version 0.24.0 ; une 0.23.0
  publiée installée, Firefox désactivé, puis mise à jour par son propre `update.py` depuis GitHub : Firefox reste
  désactivé, complément VLC désactivé ; lanceur sur la nouvelle copie, fenêtre servie sans dossier de
  téléchargement ; installation en une ligne réelle (`get.sh`) en 0.24.0.
- **Vérifié avant publication** : mise à jour réelle depuis la 0.23.0 publiée (`tests/e2e/check_update.py --from
  0.21.0 0.22.0 0.23.0` sur les trois systèmes ; `tests/e2e/check_update_apps.py` avec vrais VLC et fre:ac Debian) ;
  complément VLC chargé par VLC 3.0.20 et 3.0.24 (aide) et vu dans la fenêtre Qt de 3.0.24 (menus, préférences).
- **0.25 en développement sur `next-0.25`** (non fusionnée dans `main`, non publiée) : Poedit (dialogues GTK dans
  la langue de la session, essais réels Debian 3.6.3 et Flatpak 3.10 ; macOS expérimental), PDFsam (Linux réel),
  formats régionaux de Firefox (suivent le système, cause : copie dans l'emplacement en-US et règle de
  `GetRegionalPrefsLocales`), protections Discord (page simulée dans Chrome), raccourcis du complément VLC
  (« A&ttrezzi » ; la 0.24.0 garde le double Alt+A), vérification d'utilisateur de la fenêtre
  limitée à la vraie connexion (test instable du tag 0.24.0). Notes dans [.github/RELEASE_NOTES.md](../.github/RELEASE_NOTES.md) et le CHANGELOG.
- **Candidate 0.25.0 intégrée** (18 octobre 2026) sur `next-0.25`, non taguée, non publiée, non fusionnée dans
  `main`. Réunit `fix-discord-labels` et `redesign-window`, puis trois branches de travail (`c025-discord`,
  `c025-ui`, `c025-install`). Commit et CI : voir la ligne « Validation » plus bas, mise à jour à chaque passage.
  - **Discord** : « Dans un appel » (liste des MP), « Bio » devenu « Biugrafia » (INFCOR : *biografia*, variante
    *biugrafia* ; Wikipedia corsa), « Message » nom « Messaghju », 51 + 15 libellés remis dans le sens de Discord
    (provenance de chacun dans `lexicon/review-discord-2026-10.tsv`). Textes des zones de présence gardés selon leur
    origine (jeux affichés sous un autre nom compris), diagnostic sans rien qui vienne de noms, statuts ou activités
    (révision `2026-10-origin-1`, empreinte du dictionnaire construit `126775-317a576de61ce2a3`). Pages simulées et
    module construit dans Chrome ; **pas observé dans un vrai Discord**. Le Discord personnel charge encore le module
    de la 0.23.0 (empreinte `126646-…`).
  - **Fenêtre** : refonte et rubrique Apparence (docs/window-design.md) ; clé par lancement exigée pour toute lecture
    et action (`X-Corsu-Key`, ticket à usage unique après `#t=`), qui ferme la lecture de l'état et de l'image de
    fond par un autre compte sous Windows et macOS (docs/window-security.md) ; socket d'écoute fermé à l'arrêt
    (relais `--replace` qui attendait 30 s). Observé : Chrome headless et WebKitGTK 2.54 (Xvfb, conteneur) ; **pas
    WebView2 ni WKWebView**. Captures : données fictives.
  - **Installation** : le Python de l'archive est gardé dans `DATA/runtime` même quand l'installeur tourne sur celui
    du système ; sous Linux les lanceurs passent par `DATA/bin/corsu-python` (Python du système s'il est
    complet, sinon la copie ; macOS utilise toujours la copie). Cause : `deploy_runtime` ne copiait que quand Corsu tournait déjà sur le Python de
    l'archive, et les lanceurs écrivaient `sys.executable` (`/usr/bin/python3`). Observé en conteneur : sans aucun
    Python, avec `python3-minimal` seul, Python retiré après installation ; migration réelle depuis la 0.24.0
    publiée (`tests/e2e/check_migration.py`, aussi en CI) ; Windows inchangé (le `.cmd` préférait déjà le Python
    de l'archive).
  - **Règle de traduction** des abréviations et classes de provenance : [AGENTS.md](../AGENTS.md).
  - **Validation** : code de la candidate `326a1c2`, CI run 39117128881 verte (tests unitaires 3 systèmes × Python
    3.10 et 3.13, construction de Vencord et des archives, bout en bout Linux, Windows, macOS dont la migration depuis la
    0.24.0 publiée sous Linux). Le commit suivant ne change que ce document.
  - **Reste à faire par une personne** : vérifications 9 à 11 de « Vérifier Discord à la main » après installation
    de la candidate ; relecture par un locuteur des cas incertains de `lexicon/review-discord-2026-10.tsv` ; décision
    de publication (rien n'est tagué).
- **`fix-0.24.1`** (`3e43459`, depuis `v0.24.0`) : seulement le correctif de sécurité de la fenêtre ; attend une
  décision de publication.
- Tests unitaires : `HOME=$(mktemp -d) python3 -m unittest discover -s tests -t . -q` (sans `-t .`, 13 erreurs
  d'import qui ne signalent rien).

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
- Minecraft Java : expérimental, non relu par un locuteur ; la 26.3 lancée une fois avec le pack (Prism Launcher
  du mainteneur, 16 octobre), sans contrôle visuel clé par clé. Bedrock, extension web :
  prototypes.
- (Historique : la 0.22.0 a été publiée le 16 octobre 2026, puis la 0.23.0 le 17.)

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
  Patriccollu) ; rien n'a été envoyé. (Depuis : tous contrôlés et relus par IA, voir plus bas.)

- Audit Firefox et Discord (branche `audit-firefox-discord`) : le Firefox de Corsu lancé dans un profil jetable
  et lu par Marionette (menu principal, Paramètres > Général, téléchargements, onglets, Firefox View). Corrigé :
  outils du navigateur et messages de téléchargement restés en français (31 lignes IA à relire), arguments `%S` de
  Mozilla ignorés par le moteur, « Onglets ouverts » traduit comme un bouton. Discord : surnoms de serveur
  (`userId`), destinataires de MP (`rawRecipients`, `nicks`), noms dans l'indicateur « écrit… », nœuds réutilisés
  par React (fibre `alternate`) et noms contenant « , » ou « | » sont protégés (`tests/e2e/check_discord_content.py`,
  page simulée dans Chrome, pas le vrai Discord). Reste : dates et heures du Firefox au format `en-US`
  (corrigé depuis sur `next-0.25`).

## Vérifier Discord à la main (après redémarrage)

Sans partager de message ; noter seulement l'endroit d'un défaut, pas le contenu.

1. Redémarrer Discord (Corsu activé), interface en français.
2. Quand une personne écrit : « … hè à scrive… », son nom tel quel.
3. Deux puis trois personnes : seuls « è » et « sò à scrive… » changent ; les noms, même avec une virgule, restent.
4. Serveur animé : « Parechje persone sò à scrive… ».
5. Liste des membres : « Cunnessu — N » traduit ; noms de rôles et de membres intacts.
6. Passer d'un MP à un autre, d'un serveur et d'un salon à l'autre : nouveau nom intact, libellés voisins en corse,
   l'ancien nom ne réapparaît pas.
7. Un pseudo égal à un mot de l'interface (« Online », « Home ») n'est jamais traduit.
8. Aucun message, bio ou statut traduit.
9. Liste des MP : un contact en appel montre « In una chjama » ; son pseudo, un jeu ou un statut personnalisé
   restent tels quels, même un jeu affiché sous un autre nom. Profil : titre « Biugrafia », texte de la bio intact.
10. Version chargée : Paramètres › Vencord › Plugins › Corsu, option cachée `reportMissing` (dans
    `settings.json` de Vencord) puis redémarrage : la console affiche `[CorsuMissing] {"revision":"2026-10-origin-1",
    "dictionary":"126775-317a576de61ce2a3"}` (candidate 0.25.0). Rien de tel avec le module de la 0.23.0.
11. Nouvelle fenêtre (après installation de la candidate) : Apparence › choisir une image, Appliquer ; fermer puis
    rouvrir Corsu : l'image et le thème restent ; Réinitialiser l'apparence ne change aucun interrupteur.

## Blocages et ce qui demande une personne

- Essai réel de Minecraft Java 26.3 ([TESTING.md](../minecraft/java/TESTING.md)) et de Bedrock.
- Relecture par des locuteurs : lots prêts dans [review-batches](../minecraft/java/review-batches/) ; modèles de
  demande non envoyés.
- Décisions du mainteneur : licence des textes de Corsu (CC0 recommandé, rien n'est changé). « Servore » est
  attesté en informatique (ADECEC, *Lingua corsa è Internet*, Thiers et Filippi, 1999) : ce n'est donc pas une
  raison de tout remplacer. *Servitore* reste le choix là où il est appliqué (Minecraft). Discord n'est pas
  modifié ([décision D1](../minecraft/java/decisions-2.md)).
- (Corrigé en 0.22.0 : icône de Python du raccourci Windows ; logiciels activés en partie indiqués dans la fenêtre.)
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

## VLC : complément expérimental (17/10/2026, non publié)

- Les 1 760 brouillons sont tous contrôlés (`tools/vlcpo.py check`, avec les entrées fuzzy) et relus par IA en
  deux lots thématiques : 1 580 gardés, 177 corrigés, 3 incertains (« Soften », « Shaping delay » et son aide).
  Aucun n'est validé par un locuteur ; détails dans [contrib/vlc/TERMS.md](../contrib/vlc/TERMS.md).
- Activation : `--vlc-complement on|off`, Linux, VLC 3.0.x du système, par `VLC_DATA_PATH` dans l'entrée de menu.
  Vu avec un vrai VLC 3.0.20 et 3.0.24 (conteneurs, CI). Interrupteur ajouté ensuite dans la fenêtre (fiche VLC).
- fre:ac lancé pour de vrai (paquet Debian, conteneur) : fenêtre en corse.

## Prochaines étapes (feuille de route courte)

1. **Consolider les intégrations actuelles** : mise à jour fiable et lisible, textes encore non traduits hors de la
   page Discord (menus natifs, notifications, KDE), logo et association de fenêtre, essais réels manquants
   (WebView2, WKWebView, vrai Discord).
2. **Clavier** : essai sur vrai téléphone, retour des utilisateurs sur les préférences régionales, correction
   automatique de Keyman 19 quand elle sera stable.
3. **Relecture Minecraft** par des locuteurs, en commençant par les cas différés et incertains de
   `minecraft/java/review-2026-10/TRACKING.md`.
4. **Ensuite, selon la faisabilité réelle** : Bedrock (prototype à essayer en jeu), autres logiciels et jeux
   ([feuille de route](fr/feuille-de-route.md), [roadmap-candidates.md](roadmap-candidates.md)).
5. **Contribution future au projet officiel Minecraft (Crowdin)** : objectif, pas engagé. Le moment venu, vérifier
   les conditions exactes de contribution et de licence, et les règles sur les traductions assistées par IA ; une
   licence CC0 ne règle pas la question à elle seule. Aucun envoi sans accord du mainteneur.
