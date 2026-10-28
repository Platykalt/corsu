# Continuité du projet

Document de reprise, tenu à jour à chaque étape. Il renvoie aux documents détaillés plutôt que de les répéter.
Les sections datées après « État actuel » sont l'historique : ce qui y est dit ouvert a pu être corrigé depuis.

## État actuel (28 octobre 2026)

- **0.28.3** : branche `fix-0.28.3`, partie de `main` `a8a9f69` (0.28.2 + continuité), publication autorisée par le
  mainteneur le 28 octobre 2026. Trois défauts signalés par des utilisateurs :
  - Windows (`5157b3b`, `0317de7`, agent « Windows ») : consoles PowerShell répétées sous la fenêtre (pythonw.exe).
    Responsables : `corsu.running_executables()` (`powershell (Get-Process).Path`, depuis `app.still_open()` environ
    toutes les 3 s et `apps.programs.running()` toutes les 20 s), `minecraft.running_folders()`
    (`Get-CimInstance Win32_Process`, toutes les 20 s quand un dossier de jeu attend), `app.shortcut_command()` (lecture
    de `Corsu.lnk`), et dans les travaux lancés par la fenêtre `windows_link`, `tasklist`, l'installeur d'une mise à
    jour, VencordInstallerCli. `corsu.hidden()` : `CREATE_NO_WINDOW` seulement quand Corsu n'a pas de console, sorties
    du parent transmises (journal du travail, terminal). Liste des processus lue au plus toutes les 2 s. UAC inchangé.
    Preuve sur runner Windows Server seulement (`tests/e2e/check_windows_consoles.py`, raccourci installé, Minecraft,
    rafraîchissements, appels de la page) : la 0.28.2 publiée ouvre 8 `powershell.exe` avec console en 76 s (CI
    40611719448) ; aucun PC d'utilisateur observé.
  - Discord (`2299915`, `e58dc15`, `1ed849a`, révision `2026-10-notice-1`) : message d'épinglage (et ajout/retrait de
    groupe) dans l'enveloppe `message-content` que la règle de contenu protégeait ; « Aller à {guildName} » (UdYYP3,
    AEfs1D, serveur déjà rejoint) sans ligne. « Aller sur un serveur », tel que signalé, n'existe dans aucun texte du
    client : paraphrase. Pages simulées d'après le client web public, pas l'application Discord.
  - CI : VLC installé depuis VideoLAN (SHA-256 vérifié) quand Chocolatey échoue (`214407c`,
    `tests/e2e/install_vlc_windows.ps1`) ; la CI de `main` 40603473995 avait échoué deux fois sur ce seul point (503 de
    Chocolatey), sans lien avec Corsu.
- **0.28.2 publiée** (27 octobre 2026, 23 h 34 UTC) : tag annoté `v0.28.2` sur `a3a00c8` (= `main` à la publication),
  release https://github.com/Platykalt/corsu/releases/tag/v0.28.2, dernière version, 16 fichiers, sommes SHA-256
  vérifiées après téléchargement. CI de la candidate 40590847509 verte (`a3a00c8`) ; CI du tag 40597336799 verte,
  publication et installation en une ligne (Ubuntu, Windows) comprises. Archives publiées inspectées : version 0.28.2,
  plugin Discord `2026-10-composer-2` avec les corrections, « Accolta » dans la fenêtre, aucune trace de `strix_runs/`.
  Essai isolé après publication : la 0.28.1 publiée voit la 0.28.2 sur GitHub (`status: available`), se met à jour
  par son propre `update.py` ; partie désactivée, apparence et préférence `auto_update` gardées.
  `a3a00c8` corrige aussi l'essai Firefox de la CI : Firefox 159 exige `MOZ_REMOTE_ALLOW_SYSTEM_ACCESS=1` pour le
  contexte chrome de Marionette (CI 40584496466 rouge sur Ubuntu pour cette seule raison).
  - Discord (`2f7c755`, `fa1f3ac`, révision du traducteur `2026-10-composer-2`) : champ « Envoyer un message à @… »
    (texte de remplacement Slate hors champ de saisie), « Rechercher {name} » = « Circà in {name} », message
    d'épinglage actuel et lien « Modifier le groupe » cherchés dans la liste des messages, message système dans
    l'aperçu seulement si le type React du message est un type système, pseudo qui ressemble à un fragment. Essais
    `tests/e2e/check_discord_regressions.py` écrits indépendamment (14 échouent sur la 0.28.1). Pages simulées avec le
    plugin construit, pas le vrai Discord ; provenance usage Corsu ou proposition IA, aucune relecture par un locuteur.
    Plugin embarqué vérifié dans les trois archives de la CI (révision et textes présents dans
    `Vencord/dist/renderer.js`).
  - Relecture linguistique Discord (IA) : environ 785 lignes sur 22 430 examinées, suite dans
    `lexicon/review-discord-progress.md` ; elle continue séparément et n'a pas retardé la 0.28.2.
  - Fenêtre (`8848557`) : la page « Logiciels » devient « Accueil » (« Accolta », usage Corsu repris de Firefox) :
    résumé en haut, liste « Logiciels gérés par Corsu », état en mots sur chaque ligne (en corse, partiellement,
    langue d'origine, redémarrage nécessaire), focus gardé au rafraîchissement. Identifiant interne `programs` gardé.
- **0.28.1 publiée** (27 octobre 2026) : tag `v0.28.1` sur `ae8890b`, release
  https://github.com/Platykalt/corsu/releases/tag/v0.28.1 (messages de groupe Discord, parties inconnues laissées
  telles quelles par l'installateur).
- **`hyprland`** : branche de développement, jamais fusionnée dans `main` ; elle reprend chaque version publiée et,
  en plus, l'intégration Hyprland + Noctalia et les dates en corse dans la session Hyprland (`a9ed3a0`).
  L'installation personnelle du mainteneur vient de cette branche (composants `hyprland` et `hyprland-profile`) : la
  mise à jour automatique ne lui propose pas les versions publiées ; elle se met à jour depuis une construction de
  cette branche. Depuis le 28 octobre 2026 : 0.28.2 de `hyprland` `5e08012` (archives de la CI 40597179092), qui se
  présente comme 0.28.2 mais n'est pas l'archive publiée.
  `check_migration.py` relit l'état de la fenêtre avant de demander le redémarrage (course vue dans la CI 40591065196 :
  `/api/state` calcule `restart` avant de lire le travail terminé).

## Historique : publication 0.28.1 (27 octobre 2026)

- Branche `fix-0.28.1`, partie de `v0.28.0`. Discord : messages de groupe « a ajouté … au groupe »,
  « a retiré … du groupe », « a quitté le groupe » (`4d52662`, révision du traducteur `2026-10-group-1`). Installateur :
  partie notée inconnue laissée telle quelle (`c082c55`, `e0b0fb5`). Notes `ba24b04`, CI de la candidate 40434114016.

## Historique : publication 0.28.0 (26 octobre 2026)

- **0.27.0 reste la dernière version publiée** (tag `v0.27.0` sur `f51b1ac`). `main` = `751c461` (documentation :
  Hyprland en développement, contournement `--browser` pour la fenêtre Windows de la 0.27.0).
- **Candidate 0.28.0** : `next-0.28` = `c471a0d` (`next-0.28` fusionnée avec `main`), plus la documentation de
  publication sur la branche `docs-028` (CHANGELOG « 0.28.0 (2026-10-26) », notes de version, README et pages d'état
  qui nomment la 0.28.0). Non publiée : la publication attend l'accord du mainteneur.
  - Fenêtre Windows : `b4d99ef`, `fa4473f` (icône `corsu.ico` par `windows_window_icon()` sous Windows seulement ;
    macOS et Linux inchangés), `d00b266` (CI : vraie fenêtre ouverte avec le Python de l'archive sur un runner Windows
    Server, `tests/e2e/check_windows_window.py`).
  - Firefox : `fc5e88d`, `ee3faa4` (`contextMenuSearch`, voir l'historique ci-dessous).
  - Discord : `8c25eb2` (champs de recherche), `319b281`, `e290746`, `a23d8c0` (message d'épinglage ; provenance
    usage Corsu, non relu par un locuteur). Vérifié sur pages simulées avec le plugin construit dans Chromium sans
    affichage, pas dans le vrai Discord ; l'emplacement du pseudo dans le message d'épinglage reste une hypothèse.
  - Désactiver : `b416445`, `df89ab8` (consigne de redémarrage seulement tant que le logiciel tourne).
  - Source de téléchargement : `ebed6f3` (avertissement quand `CORSU_DOWNLOAD_BASE` n'est pas la source officielle).
  - CI de la candidate : **40360790474 verte** sur `8b235f0` (26 octobre 2026) : tests unitaires (3 systèmes,
    Python 3.10 et 3.13), archives, bout en bout sur les trois systèmes. Plugin Discord construit : révision
    `2026-10-pins-1`, recherche et épinglage traduits, pseudos gardés ; fenêtre native de Corsu ouverte sous Windows
    avec le Python de l'archive, icônes posées (capture `windows-native-window`) ; mise à jour depuis la 0.27.0
    publiée sous les trois systèmes, migration 0.27.0 → 0.28.0 sous Linux (Firefox éteint reste éteint, apparence
    gardée). Archives inspectées : version 0.28.0, `corsu.ico`, aucune trace de `strix_runs/` ni de secret, sommes
    SHA-256 conformes. Ensuite seulement de la documentation (`c471a0d`, fusion de `main` ; release) : 640 tests
    unitaires verts en local ; la CI du tag reconstruit et revérifie tout avant de publier.
- **`fix-0.27.1`** (`f59fb6d`, 0.27.0 avec la correction de la fenêtre Windows) : jamais publiée, remplacée par la
  0.28.0, qui contient la même correction.
- **`hyprland`** (`b5ec13f`) : branche de développement, non fusionnée dans `next-0.28` ni dans `main` ; la 0.28.0 ne
  contient pas l'intégration Hyprland + Noctalia.

## Historique : candidate 0.28 (22 octobre 2026)

- **0.27.0 publiée** (19 octobre 2026, 12 h 06 UTC) : tag annoté `v0.27.0` sur `f51b1ac`, release
  https://github.com/Platykalt/corsu/releases/tag/v0.27.0, dernière version (16 fichiers ; CI du tag 39243504586
  verte, installation en une ligne comprise). `main` = `ef6c9b6` (documentation seulement : README, pages d'état et
  captures de la 0.27.0 ; CI 39250281799 verte). Installation personnelle du mainteneur : 0.27.0.
- **`next-0.28`** (depuis `ef6c9b6` ; non publiée, la publication attend l'accord du mainteneur). CI seulement par
  `gh workflow run ci.yml --ref next-0.28`. `src/release.json` dit 0.28.0 : la CI vérifie la mise à jour et la
  migration depuis la 0.27.0 publiée.
  - `fc5e88d` : menu contextuel du texte sélectionné dans Firefox (`contextMenuSearch`, « Recherche %1$S pour
    « %2$S » » → « Circà « %2 » cù %1 », proposition IA bâtie sur « Circà cù %1 » déjà présent) ; CI 39633324591
    verte.
  - `ee3faa4` : essai de bout en bout `tests/e2e/check_firefox_context_menu.py` (vrai menu dans Firefox, moteur par
    défaut et autre moteur, troncature, touche d'accès).
  - `35ced37`, `ae5bcdb` : version 0.28.0 ; la CI met à jour depuis la 0.27.0 publiée (`check_update.py` sur les trois
    systèmes, `check_update_apps.py` et `check_migration.py --from 0.27.0` sous Linux) ; `check_migration.py`
    enregistre désormais des réglages d'apparence avec la copie publiée avant la mise à jour et vérifie qu'ils restent ;
    provenance de `contextMenuSearch` dans `lexicon/corrections.tsv`.
  - **CI 39818931689 (`ae5bcdb`, 22 octobre 2026)** : tests unitaires et archives verts ; bout en bout vert sous
    Ubuntu et Windows. Sous Ubuntu : menu contextuel en corse dans un vrai Firefox ; mise à jour 0.27.0 → 0.28.0
    (`@result … "from": "0.27.0", "to": "0.28.0"`) ; migration 0.27.0 → 0.28.0 : Firefox reste désactivé, VLC et son
    complément restent actifs, réglages d'apparence choisis en 0.27.0 inchangés, fichiers personnels intacts, lanceurs
    sur la nouvelle copie. Sous Windows : menu contextuel et mise à jour depuis la 0.27.0 verts. **Échec macOS** :
    traduction juste (« Circà « Corsica » cù Google »), mais l'essai exigeait une touche d'accès soulignée, que les
    menus de macOS n'affichent pas ; l'essai attend désormais un libellé sans soulignement sous macOS. Les étapes
    suivantes de macOS (dont la mise à jour depuis la 0.27.0) n'ont pas tourné dans cette CI.
  - **CI 39825997542 (`33e1c5c`, 22 octobre 2026) : verte** sur les trois systèmes (tests unitaires, archives, bout en
    bout). Menu contextuel en corse dans un vrai Firefox sous Linux, Windows et macOS ; mise à jour 0.27.0 → 0.28.0
    réussie sous les trois systèmes ; migration 0.27.0 → 0.28.0 (réglages gardés) sous Linux. Candidate prête, non
    publiée ; la publication attend l'accord du mainteneur.
  - Limites : migration complète vérifiée sous Linux seulement ; même Python embarqué en 0.27.0 et 0.28.0 (le
    remplacement du Python n'est pas exercé) ; aucun essai ne lit le nouveau libellé dans une installation mise à jour
    (la copie de Firefox est reconstruite au lancement, son nom dépend de l'empreinte du lexique).
  - **Chantier suivant, textes Firefox restés français** (audit complet des `.properties` non commencé), par
    priorité : 1. « Temps de connexion dépassé » (page d'erreur, très visible) ; 2. `unsignedAddonsDisabled`
    (installation de modules) ; 3. `geolocationLastAccessIndicatorText` (barre d'adresse, autorisations) ;
    4. `crashedplugins` (rare).
- **Branche `hyprland`** (depuis `next-0.28` `2931910`, 22 octobre 2026 ; ni fusion, ni tag, ni release) :
  composant facultatif Hyprland 0.56 + Noctalia 5.3, deux choix (`hyprland` langue, `hyprland-profile` profil,
  jamais coché d'avance). Contrat : [src/hyprland/README.md](../src/hyprland/README.md) ; système, GPU, portails :
  [hyprland-system.md](hyprland-system.md) ; usage et état réel : [fr/hyprland.md](fr/hyprland.md). Préréglage
  `cachyos-hypr-noctalia` écarté (conflit avec `cachyos-kde-settings`, qui porte la configuration Wayland de SDDM ;
  `/etc/profile.d` global ; GPL-1.0-only). Vérifié : vrai Hyprland en session imbriquée (KWin virtuel, bus privés),
  Noctalia en corse ; non vérifié avant une vraie connexion : portails, partage d'écran, polkit, verrouillage,
  KWallet, veille. Catalogue Noctalia : 2 375 textes sur 3 126 proposés par IA, aucune relecture humaine.
  Installation personnelle du mainteneur : 0.28.0 de cette branche avec les deux choix (retour testé vers 0.27.0).
- **PHP** (avis du 21 octobre 2026, CVE-2026-109618 et CVE-2026-109619) : Corsu ne dépend pas de PHP (aucun fichier,
  appel, paquet, étape de CI ni image de conteneur qui l'utilise ; les adresses `.php` citées sont des sites
  distants). Aucune mise à jour PHP du projet n'est nécessaire.

## Historique : candidate 0.27 (19 octobre 2026)

- **0.26.0 publiée** (18 octobre 2026, 22 h 29 UTC) : tag `v0.26.0` sur `9868066`, release
  https://github.com/Platykalt/corsu/releases/tag/v0.26.0, dernière version (CI du tag 39169945473 : tests,
  archives, bout en bout sur les trois systèmes, publication, installation en une ligne Linux et Windows ; CI de la
  candidate 39167633006). Vérifié depuis `releases/latest/download` : 8 fichiers conformes à leurs 8 `.sha256`,
  archives en 0.26.0, trois dictionnaires 1.1 (13 213 mots chacun, identifiants attendus). `main` = `9868066`.
- **`next-0.27`** (en développement depuis `8d3cba8`, sur la 0.26.0 ; non publiée, la publication attend l'accord du
  mainteneur). `src/release.json` dit 0.27.0 pour que la CI vérifie la mise à jour depuis la 0.26.0 publiée. Détail
  dans le CHANGELOG ; quatre chantiers intégrés (agents A à D) :
  - **Clavier 1.2** (branche `c027-kb`) : plus d'espace avant une ponctuation déjà écrite (modèle ; Android et iOS en
    fin de mot, Android seul au milieu d'un mot), apostrophe ’ gardée ; +6 012 formes écrites par les sources
    (Vikipédia, comptées seulement dans la prose corse, Wiktionnaire, élisions ; 324 formes mises en attente dans
    `keyboard/data/held-back.tsv` ; sélection IA non relue) pour que la correction automatique de Keyman 19 ne
    remplace plus des mots justes ; 19 341 mots par paquet. Paquets finaux vérifiés dans les moteurs seulement : tout passe avec 18.0.254 (aussi en CI) ; avec la bêta
    19.0.309, tous les cas de mots passent, mais le scénario « correction automatique activée » échoue par intermittence
    (erreur interne `isFullReplacement`, aussi avec les paquets 1.1 et 1.2 précédents, origine non isolée). Espace avant
    la ponctuation vu dans les applications 18.0.254 et 19.0.309 sur émulateur Android 14 avec des données 1.2
    antérieures ; ni téléphone réel ni iPhone. Commit fonctionnel validé : `b9ff20f` (CI 39233111017). Ponctuation tapée
    juste après une suggestion : Keyman 18 laisse « casa . » (un retour arrière enlève l'espace), Keyman 19 l'enlève.
  - **Noms de lieux historiques** (branches `c027c-inv`, `c027c-kb`) : inventaire sourcé
    (`keyboard/data/sources/historical-places.tsv`, 330 lignes : pievi, micro-régions, diocèses et sièges, provinces,
    divisions historiques) ; 113 mots ajoutés aux trois paquets, dont « Vallerustie » ; graphies françaises reconnues
    sous la forme corse ; noms composés reconnus mot par mot seulement. Manques et cas incertains :
    `keyboard/data/historical-places.md`.
  - **Signaler une traduction** : page « Signaler » de la fenêtre ; rien n'est envoyé sans clic, chemins et adresses
    masqués. **Séries de relecture** (`review/`, 71 séries Minecraft) : réponses gardées comme propositions, liées
    aux empreintes des textes. **Mémoire de traduction** : sens, abréviations, provenance, sources changées.
  - **Langue, cinquième tour** (IA, revérifié par une autre passe IA ; relecture humaine : 0) : 16 textes Minecraft
    (`minecraft/java/review-2026-10/ROUND5.md`), verbe de dialogue pour « Supprimer » dans Discord, Spirlà/Dispirlà,
    In linea / Fora di linea, Minuteria, Squas.
  - **Bedrock** : prototype pour Bedrock 26.50, 4 272 textes sur 13 340 repris de Java, jamais chargé en jeu ; la CI
    le vérifie et construit le pack d'essai comme artefact séparé (`minecraft-bedrock-prototype`), jamais joint à une
    release. Protocole : [minecraft-bedrock.md](fr/minecraft-bedrock.md).
- Tests unitaires : `HOME=$(mktemp -d) python3 -m unittest discover -s tests -t . -q` (sans `-t .`, 13 erreurs
  d'import qui ne signalent rien). CI d'une branche autre que `main` : `gh workflow run ci.yml --ref <branche>`.
- **INFCOR** et autres dictionnaires en ligne : consultation page par page seulement, jamais par script
  ([AGENTS.md](../AGENTS.md), test `tests/test_sources_policy.py`).
- **Attend une personne** : essai des paquets clavier 1.2 sur un vrai téléphone Android et sur iPhone ; relecture par
  un locuteur (séries `review/`, Minecraft, Discord : `lexicon/review-discord-2026-10.tsv`, formes ajoutées au clavier :
  `keyboard/data/REVIEW.md`) ; essais Minecraft en jeu, Java et Bedrock (neuf questions dans minecraft-bedrock.md) ;
  libellés Discord observés dans un vrai Discord ; envoi éventuel du ticket Keyman
  (`docs/keyman/ticket-mid-word-suggestion.md`, brouillon) ; décision de publier la 0.27.
- **Limites connues** : complément VLC absent sous Windows, macOS, Flatpak, Snap ; Audacity 4 expérimental sous
  Windows et macOS ; fenêtre non observée dans WebView2 ni WKWebView ; Keyman 18 sans correction automatique ;
  suggestion choisie au milieu d'un mot : seulement la partie à gauche du curseur remplacée sous iOS (limite de
  l'application Keyman) ; « calvi » devient « Calvi » (aucune source pour l'adjectif) ; formes verbales absentes des
  sources (« vedemu ») encore remplaçables par la correction de Keyman 19.

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
| Minecraft : Corsu lit la version de chaque dossier de jeu (instance) et n'y ajoute que le pack de cette version parmi les 87 prises en charge, puis choisit le corse ; une version non prise en charge n'est pas modifiée ; rien n'est réécrit qui ne puisse être relu | `tests/test_minecraft_instances.py`, `tests/test_lexicon_minecraft.py` |
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

## Historique : préparation de la 0.26 (18 octobre 2026)

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
    réutilisées pour un autre logiciel) ; consultations manuelles à faire listées. Quatrième tour (`ROUND4.md`, `round4.tsv`) : formulations et
    adéquation à l'interface, premier lot (menus principal et pause, mondes, serveurs, options) ; 18 textes changés
    (« Ghjucà solu » / « Ghjucà cù l'altri », « Arregistrà è esce da u mondu » au lieu de « … vultà à u titulu ») ;
    aucun essai visuel en jeu. Relecture humaine : 0.
  - **Clavier Keyman** (paquets 1.1) : casse gardée, vocabulaire refait (`keyboard/data`), 446 noms de lieux
    (Wikidata, CC0), préférences Cismuntincu et Pumuntincu **expérimentales** (361 mots pondérés autrement). Vérifié
    dans le moteur de Keyman 18.0.254 (CI) et sur émulateur Android 14 ; **pas sur téléphone, pas sur iOS**.
    Suggestion choisie au milieu d'un mot : Keyman ne remplace que la partie à gauche du curseur ; les modèles 1.1
    (`keyboard/whole-word.js`) effacent la fin du mot sous Android (moteurs 18.0.254 et 19.0.309, application
    18.0.254 sur émulateur), pas sous iOS, où Keyman ignore l'effacement à droite. Ticket préparé, non envoyé :
    `docs/keyman/ticket-mid-word-suggestion.md`.
  - **Téléphone** : page « Sur téléphone » de la fenêtre, guides ; bascules de publication dans
    [release-checklist-phone.md](release-checklist-phone.md).
  - Corrigés pour les prochaines publications (les fichiers déjà publiés de la 0.25.1 restent tels quels, sans somme
    propre pour le pack de textes) : une somme `.sha256` par fichier publié, vérifiée en CI ; version des captures lue
    dans `src/release.json`.
- **Chantier du 18 octobre 2026 (soir), intégré dans `next-0.26`** (agents A à E ; détail dans le CHANGELOG) :
  - **Faux « à jour »** : cause établie par le journal et reproduite avec le code de la 0.24.0
    ([update-diagnosis.md](update-diagnosis.md)) : fenêtre ouverte à 10 h 50 qui ne vérifiait qu'à l'ouverture,
    relance qui réaffichait cette fenêtre, réponse gardée 6 h. Corrigé ; rattrapage par l'installeur public vérifié
    en conteneur. Windows et macOS non lancés.
  - **Textes** : menu de la zone de notification de Discord traduit (vrai Discord 1.0.162 en conteneur KDE, chaînes
    envoyées à la main, sans connexion) ; « Display Configuration » (KDE) corrigé ; « Fermer Discord » introuvable
    dans les textes de Discord ; le menu « Quitter Discord » est traité ; un autre emplacement ne sera recherché
    qu'après une capture qui le montre. Inventaire : [untranslated-inventory.md](untranslated-inventory.md).
  - **Logo** : nouveau dessin ; fenêtre associée à `corsu-setup.desktop`, logo vu dans Alt+Tab, barre des tâches et
    titre sous KDE Plasma 6 (Wayland, X11, conteneur). Non observé : Windows, macOS, GNOME.
  - **Clavier** : fin du mot effacée sous Android quand on choisit une suggestion au milieu (iPhone : non, limite de
    Keyman) ; noms officiels de communes ; cas dépendant des données dans `tests/e2e/keyboard_data_cases.tsv`.
    Correction automatique (moteurs 18.0.254 et 19.0.309 bêta) : Vizzani, corti, ADECEC gardés (données
    ajoutées) ; reste calvi → Calvi (adjectif non attesté dans les sources consultées). Paquets 1.1 : 13 213 mots chacun (`tools/count_kmp.py`).
  - **Canopé** : `sources/cunghjugarellu.tsv` contient 511 lignes (368 formes de 21 verbes, avec numéro de tableau) ;
    les paquets n'ont que mots et poids. Correction ciblée proposée, non appliquée : règles propres pour les verbes
    réguliers, formes irrégulières seules listées (aucun effet sur les paquets).
  - **Minecraft** : troisième tour, comptes réconciliés, décisions sensibles relues sur leurs sources, aucun texte
    changé ; mémoire contextuelle `lexicon/memory/minecraft-java.jsonl`.
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
  dans WebView2 ni WKWebView ; Keyman 18 sans correction automatique ; suggestion choisie au milieu d'un mot : mot entier remplacé sous Android
  avec les paquets 1.1, seulement la partie à gauche du curseur sous iOS (limite de l'application Keyman).

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
