**Français** · [English](#english)

### Téléchargements par usage

| Pour | Fichier | Ensuite |
| --- | --- | --- |
| Windows 10 ou 11 | `corsu-windows.zip` | décompresser, double-cliquer sur `Install for Windows.cmd` |
| macOS | `corsu-macos.tar.gz` | double-cliquer sur `Install for macOS.command` |
| Linux | `corsu-linux.tar.gz` | lancer `./"Install for Linux.sh"` |
| Téléphone Android ou iPhone (clavier Keyman) | `corsu-keyboard.kmp` | dictionnaire corse pour Keyman, **utilisable seul** : aucune installation sur ordinateur. Paquet 1.2, nom dans Keyman : « Corsu ». Guides : [Android](https://github.com/Platykalt/corsu/blob/main/docs/fr/telephone/android.md), [iPhone](https://github.com/Platykalt/corsu/blob/main/docs/fr/telephone/iphone.md) |
| Téléphone, variante régionale (expérimentale) | `corsu-keyboard-cismuntincu.kmp` ou `corsu-keyboard-pumuntincu.kmp` | même vocabulaire, préférence pour les formes du Cismonte ou du Pumonte (361 mots pondérés autrement, couverture partielle) ; paquet 1.2. Sous Android, un seul dictionnaire actif par langue : désinstaller l'autre puis relancer Keyman |
| Minecraft Java 26.3, sans l'application | `corsu-minecraft-java-26.3.zip` | pack de ressources : Options › Packs de ressources, l'activer, puis Options › Langue › Corsu ; pack facultatif des textes d'accueil et de fin : `corsu-minecraft-java-texts-26.3.zip`. Les autres versions (1.6.1 → 26.2) : par l'application Corsu ([versions et vérifications](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) |

En une ligne : `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex` dans PowerShell sous
Windows, ou `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh` dans le Terminal sous
macOS et Linux. Les [guides](https://github.com/Platykalt/corsu/tree/main/docs/fr) expliquent chaque étape.
L'application Corsu s'ouvre alors dans sa propre fenêtre.

Chaque fichier a sa somme de contrôle `.sha256`. Les archives contiennent leur propre Python. Chaque archive a été
installée, utilisée après suppression du dossier extrait, mise à jour et désinstallée sur son système avant la
publication (tests automatiques ; personne n'a regardé les écrans).

### Nouveautés de la 0.27.0

<!-- corsu:keyboard-figures Paquets 1.2, 19 341 mots par paquet (tools/count_kmp.py sur les .kmp construits) ; 1.1 :
     13 213. À recompter si le clavier change avant la publication (docs/release-checklist-phone.md). -->
- **Clavier sur téléphone** (paquets 1.2, 19 341 mots par paquet, contre 13 213 dans les paquets 1.1) : plus d'espace
  ajoutée devant une ponctuation déjà écrite (`Aiacc|.` puis « Aiacciu » donne « Aiacciu. », et non « Aiacciu . ») ;
  à la fin d'un mot sous Android et sur iPhone, au milieu d'un mot sous Android seulement. L'apostrophe typographique
  est gardée (« l’is » donne « l’isula »). 6 012 formes écrites par les sources (pluriels, féminins, formes du
  Wiktionnaire, formes élidées) sont maintenant connues, pour que la correction automatique de Keyman 19 ne remplace
  plus des mots justes (« tradizioni », « abitanti », « l'ADECEC ») ; sélection faite par IA, **non vérifiée par un
  locuteur** ; les formes de Vikipedia ne sont comptées que dans la prose corse (titres, citations et passages en
  italien, français ou latin écartés). Noms de lieux historiques ajoutés d'après un inventaire sourcé : pievi,
  micro-régions, anciens diocèses, provinces et divisions historiques ; couverture limitée aux listes de référence
  retenues, pas exhaustive (113 mots, dont « Vallerustie », « Mariana »,
  « Accia ») ; les noms composés sont reconnus mot par mot. Paquets finaux vérifiés dans les moteurs de Keyman (navigateur sans affichage, pas dans l'application) : tous les
  contrôles passent avec Keyman 18.0.254, la version stable ; avec la bêta 19.0.309, tous les cas de mots passent, mais
  le scénario « correction automatique activée » échoue par intermittence sur une erreur interne du moteur
  (`isFullReplacement`), reproduite aussi avec les paquets 1.1 et 1.2 précédents, d'origine non complètement isolée.
  Espace avant la ponctuation vu aussi dans les deux applications sur émulateur Android 14, avec des données 1.2
  antérieures ;
  **pas sur un vrai téléphone, pas sur iPhone**. Mettre à jour : télécharger de nouveau le fichier sous le même nom, puis relancer Keyman (guides
  ci-dessus) ; Keyman affiche alors la version 1.2.
- **Signaler une traduction depuis la fenêtre** (page « Signaler ») : logiciel, version, texte vu, endroit,
  proposition et remarques. La page montre le signalement, le copie ou ouvre un ticket GitHub prérempli, seulement
  sur un clic. Rien n'est envoyé ni gardé par la page ; les chemins de dossiers personnels et les adresses e-mail
  sont remplacés.
- **Relecture par des locuteurs** : 71 courtes séries de questions sur les textes de Minecraft
  ([review/](https://github.com/Platykalt/corsu/tree/main/review)), chacune en page Markdown et en page HTML autonome
  qui prépare une réponse à copier ou à envoyer en ticket prérempli. Une réponse redevient « à réexaminer » quand le
  texte anglais ou corse change.
- **Relecture de la langue, 5e passe** (travail IA, revérifié par une autre passe IA ; **aucune relecture par un
  locuteur**) : Minecraft Java, environ 700 textes lus et 16 changés (par exemple `doFireTick` « U focu si
  sparghje »), vérifiés sur les 87 versions avec le code de chaque jeu ; Discord : un « Supprimer » seul prend le
  verbe de sa fenêtre, Spirlà/Dispirlà (épingler), In linea / Fora di linea ; Firefox : Minuteria pour le minuteur
  du Nouvel onglet ; KDE : Squas pour la touche Suppr.
- **Mémoire de traduction** : une traduction écrite pour un autre sens n'est plus reprise, une abréviation n'est
  jamais reprise de la seule traduction trouvée ailleurs, et chaque reprise dit d'où elle vient.
- La mise à jour depuis la 0.26.0 publiée est vérifiée automatiquement.
- **Minecraft Bedrock** : un prototype existe dans le dépôt, mais il n'est **pas joint** à cette version (jamais
  chargé dans le jeu).

### Rappel : nouveautés de la 0.26.0

- **Mise à jour** : la 0.24.0 a pu dire « à jour » alors que la 0.25.1 était publiée : une fenêtre restée ouverte ne
  vérifiait qu'à son ouverture, une relance réaffichait cette fenêtre, et une réponse de GitHub servait 6 heures comme
  si elle était récente ([diagnostic](https://github.com/Platykalt/corsu/blob/main/docs/update-diagnosis.md)). Désormais
  la réponse sert une heure au plus, une fenêtre ouverte vérifie toutes les heures et à chaque relance, une erreur
  (réseau, limite de GitHub, réponse incomplète) affiche « Vérification impossible », jamais « à jour », et la fenêtre
  montre sa version, la copie installée, la dernière version publiée et l'heure de la réponse. Si votre Corsu reste
  sur une ancienne version, le bouton « Rechercher » ou l'installation en une ligne ci-dessus la rattrape, en gardant
  vos réglages.
- **Clavier sur téléphone** (paquets 1.1) : la majuscule tapée est gardée et les suggestions de début de phrase en
  prennent une ; vocabulaire refait à partir de sources citées (13 213 mots) ; noms de lieux corses et noms
  officiels des communes ; deux préférences régionales expérimentales. Sous Android, une suggestion choisie au milieu
  d'un mot remplace le mot entier ; sur iPhone, Keyman ne remplace que le début (gestes conseillés dans le guide).
  Vérifié dans le moteur de Keyman 18.0.254 et dans l'application sur émulateur Android 14 ; **pas sur un vrai
  téléphone, pas sur iPhone**. Keyman 18 n'a pas de correction automatique.
- **Minecraft** : revue IA des textes (sens corrigés, sources citées), boutons du menu principal « Ghjucà solu » et
  « Ghjucà cù l'altri », « Arregistrà è esce da u mondu » dans le menu de pause ; les 87 versions vérifiées avec le
  code de chaque jeu. **Aucun texte relu par un locuteur** ; rien n'a été regardé à l'écran dans le jeu.
- **Discord** : le menu de la zone de notification (« Quitter Discord »…) est traduit ; plusieurs libellés revus.
- **KDE** : les raccourcis sans nom corse (« Display Configuration ») ne s'affichent plus en anglais.
- **Fenêtre de Corsu** : nouveau logo, reconnu dans Alt+Tab et la barre des tâches sous KDE (Windows et macOS : non
  observés).
- **Firefox** : libellés du menu des onglets et des profils revus.
- Chaque fichier publié a maintenant sa propre somme `.sha256`.

### Rappel : nouveautés de la 0.25.1

La 0.25.0 a été étiquetée mais jamais publiée : la vérification Windows a trouvé le défaut ci-dessous. La 0.25.1
est la 0.25.0 avec cette correction.

- **Windows** : quand la fenêtre de Corsu lisait son fichier d'état au moment où un installeur le remplaçait (ou
  quand deux installeurs démarraient ensemble), l'opération pouvait s'arrêter sur « Permission denied ». Corsu
  réessaie maintenant pendant deux secondes au plus.

- **Poedit** : Corsu active sa traduction corse. Linux : essais réels du paquet Debian (3.6.3) et du Flatpak (3.10)
  avec des sessions française, allemande et italienne : Poedit en corse, fenêtres de fichiers et boutons standard
  dans la langue habituelle, formats régionaux inchangés. Compromis : cette séparation repose sur la façon dont la
  bibliothèque C de Linux (glibc) lit les noms de langue ; si Corsu ne peut pas la vérifier, Poedit passe quand même
  en corse mais les fenêtres de fichiers restent en anglais (formats de la session gardés), et l'application le
  dit. Windows : réglage de langue de
  Poedit, vérifié sur fichiers simulés seulement. macOS, **expérimental** : liste de langues propre à Poedit (jamais
  la langue du système), remise telle quelle à la désactivation, et un choix « Par défaut du système » fait ensuite
  est respecté ; écriture des préférences vérifiée sur une machine macOS de la CI, Poedit lui-même jamais lancé sur
  un Mac.
- **PDFsam** (5.0 et plus) : Corsu règle sa langue sur le corse. Essai réel sous Linux (paquet officiel 6.0.6) ;
  PDFsam doit être fermé pendant l'activation. Windows : vérifié sur fichiers simulés seulement. macOS : laissé tel
  quel, avec la marche à suivre.
- **Firefox** : les heures, dates et nombres suivent de nouveau les réglages régionaux de l'ordinateur (on voyait
  « 11:32 AM » sur un système français) : ceux de la catégorie des dates du système (`LC_TIME`), y compris pour les
  nombres ; un choix fait dans les paramètres de Firefox reste prioritaire. `profiles.ini` et `installs.ini`
  reviennent à l'identique quand Firefox est désactivé ou Corsu désinstallé (une section de Corsu y restait). Outils du
  navigateur et messages de téléchargement traduits (31 textes IA, à relire) ; « Onglets ouverts » n'est plus traduit
  comme un verbe ; le contrôle des textes vérifie l'ordre des valeurs insérées.
- **Nouvelle fenêtre** : navigation latérale, résumé en tête (ce qui est en corse, ce qui demande votre
  intervention, mise à jour), liste compacte avec les problèmes en premier, détails techniques sur demande. Rubrique
  **Apparence** : thème clair, sombre ou du système, cinq palettes, couleur d'accent (ajustée si elle est peu
  lisible), fond uni ou image personnelle (aperçu, cadrage, Appliquer/Annuler, assombrissement, flou facultatif),
  affichage confortable ou compact, réinitialisation de l'apparence seule. L'image est vérifiée, réduite et copiée
  dans les données de Corsu ; rien n'est envoyé ailleurs. Vue dans Chrome et WebKitGTK (Linux) ; pas encore
  observée dans WebView2 (Windows) ni sur macOS.
- **Discord** : « Dans un appel » traduit dans la liste des MP ; « Bio » du profil devient « Biugrafia » (c'était
  « Organicu », pris aux styles d'images de Chrome) ; « Message » redevient le nom « Messaghju » ; 51 libellés pris
  à d'autres logiciels remis dans le sens de Discord, et d'autres abréviations écrites en entier (relecture IA, pas
  par un locuteur). Les activités, jeux (même affichés sous un autre nom), statuts et noms restent tels quels ; noms
  de personnes, surnoms, conversations privées et noms contenant une virgule protégés partout ; indicateur « est en
  train d'écrire » traduit. Vérifié sur des pages simulées et sur le module construit dans Chrome, pas encore dans
  un vrai Discord.
- **Sécurité de la fenêtre (Linux)** : sur un ordinateur partagé, un autre compte pouvait déclencher les actions de
  la fenêtre de Corsu (installer, mettre à jour, désinstaller) pendant qu'elle était ouverte. La fenêtre vérifie
  maintenant la connexion exacte et refuse un appelant non identifié. Corrige aussi des refus aléatoires des
  actions de l'utilisateur lui-même. Sur tous les systèmes, une clé créée à chaque lancement est maintenant exigée
  pour toute lecture et toute action : sous Windows et macOS, un autre compte pouvait lire l'état de Corsu et l'image
  de fond (voir `docs/window-security.md`).
- **Lanceurs Linux** : le Python de l'archive est gardé, et les raccourcis s'en servent si le Python du système
  disparaît ou est incomplet (en 0.24.0, ils cessaient de fonctionner) ; l'installation avec seulement
  `python3-minimal` ne plante plus.
- **Complément VLC** : Outils devient « A&ttrezzi » (Alt+T), il prenait Alt+A comme Audio ; « Sempre s&opra » ne
  double plus Alt+S. Corrections de brouillons IA, la traduction amont de VLC est inchangée. Les 3 traductions
  incertaines restent exclues. Le complément était refusé sans le dire dans les sessions où VLC traduit sa ligne de
  version (allemand, italien, corse…) : corrigé.
- **Mise à jour depuis la 0.24.0** vérifiée sous Linux (conteneur Debian, session française) : composants désactivés
  gardés, complément VLC gardé et réellement chargé par VLC, réglages régionaux et fichiers personnels inchangés,
  Poedit et PDFsam détectés puis activés, désactivation et désinstallation rendant les originaux à l'identique.

### Rappel : nouveautés de la 0.24.0

- **Audacity 3 et 4, Tenacity, fre:ac** : Corsu active leur propre traduction corse (celle de Patriccollu) par leur
  réglage de langue. Audacity 3, Audacity 4 et Tenacity lancés pour de vrai sous Linux (AppImages officielles) ;
  fre:ac lancé pour de vrai sous Linux (paquet Debian) : fenêtre en corse, réglage conservé à la fermeture, désactivé,
  gardé désactivé pendant une mise à jour, désinstallé. Windows et macOS : vérifiés sur des dossiers simulés
  seulement ; Audacity 4 y est expérimental. Quand un logiciel est laissé tel quel, l'application dit quoi faire.
- **VLC, complément corse expérimental (Linux, désactivé par défaut)** : la traduction de VLC laisse 1 760 textes de
  VLC 3.0.x en anglais. Corsu propose pour eux des traductions écrites par IA puis relues par IA (1 757 ; 3 cas
  incertains exclus), **non relues par un locuteur**. Elles ne sont utilisées que si vous le demandez : interrupteur
  « Complément expérimental » dans la fiche VLC de l'application, ou `--vlc-complement on` (`off` revient au
  catalogue de VLC, toujours en corse). Rien n'est modifié dans les fichiers du système : VLC lit le complément
  depuis le dossier de Corsu par sa variable `VLC_DATA_PATH`, donnée par l'entrée de menu. Seulement pour le VLC 3.0.x
  installé par les paquets de Linux ; pas sous Windows, macOS, ni en Flatpak ou Snap (l'application dit pourquoi).
  Vérifications : chargement constaté dans l'aide en ligne de commande de VLC 3.0.20 (Ubuntu 24.04, 741 nouveaux
  textes en corse) et 3.0.24 (Debian 13, 685) ; affichage regardé dans la fenêtre de VLC 3.0.24 seulement (barre de
  menus, menus Attrezzi et Affissà, préférences Video et Entrata / Cudechi), pas dans toute l'interface.
- Les traductions amont de VLC restent intactes, octet pour octet ; chaque brouillon et chaque relecture est suivi
  dans `contrib/vlc/review.json`. Rien n'a été envoyé à VLC.

### Rappel : nouveautés de la 0.23.0

<!-- corsu:minecraft-summary:start -->
- **Minecraft Java en corse pour 87 versions** (versions stables 1.6.1 → 26.3). Traduction complète des fichiers de langue pour les versions listées ; vérifications techniques avec le code de chaque version. ([versions et vérifications](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) Cette version de Corsu contient ces packs : fermez Minecraft, puis l'application trouve la version de chaque dossier de jeu (lanceur officiel, Prism Launcher, MultiMC), y ajoute le pack de cette version et choisit le corse. Limites : textes écrits par IA ; deuxième passe IA sur un échantillon de 150 entrées des 3 978 textes anciens (pas sur tous) ; relecture par un locuteur : 0 ; seule la 26.3 a été lancée avec le pack, sur l'instance Prism Launcher du mainteneur (2026-10-16) : le journal du jeu montre le pack chargé et des messages en corse. Aucune vérification visuelle clé par clé n'est enregistrée : c'est pourquoi [STATUS.md](https://github.com/Platykalt/corsu/blob/main/minecraft/java/STATUS.md) compte « vu en jeu : 0 ». Les autres versions n'ont pas été lancées. Les vérifications automatiques ne sont ni une relecture par un locuteur ni un contrôle visuel de chaque écran. Pas les snapshots, pré-versions, Bedrock ni les versions avant 1.6.1.
<!-- corsu:minecraft-summary:end -->

- Mise à jour depuis l'application (À propos) : version installée, dernière version stable, vérification au démarrage,
  « Mettre à jour », installation automatique facultative (désactivée par défaut). Relancer l'installeur ou la commande
  en une ligne met à jour ou répare l'installation existante, avec les mêmes choix (une partie désactivée reste
  désactivée) ; une version plus ancienne est refusée ; une seule opération Corsu à la fois.
- Le téléchargement vise la version exacte annoncée, vérifie sa somme SHA-256 et sa version, s'extrait sans pouvoir
  sortir de son dossier ; la nouvelle copie est complète avant de remplacer l'ancienne, qui reste en secours.
- Discord : les pseudonymes, noms d'affichage et surnoms ne sont plus traduits (« Work », « Error » restaient
  traduits en « Travagliu », « Sbagliu ») ; seuls les textes de l'interface autour d'eux le sont.
- Minecraft : le pack corse est actif dès le premier démarrage ; les nouvelles instances en attente sont signalées.
- Corrigé depuis la 0.22.0 : copie installée sans les fichiers Minecraft, plantage d'une seconde activation VLC
  Flatpak.

## English

### Downloads by use

| For | File | Then |
| --- | --- | --- |
| Windows 10 or 11 | `corsu-windows.zip` | extract it and double-click `Install for Windows.cmd` |
| macOS | `corsu-macos.tar.gz` | double-click `Install for macOS.command` |
| Linux | `corsu-linux.tar.gz` | run `./"Install for Linux.sh"` |
| Android phone or iPhone (Keyman keyboard) | `corsu-keyboard.kmp` | Corsican dictionary for Keyman, **usable on its own**: nothing to install on a computer. Package 1.2, shown in Keyman as "Corsu". Guides: [Android](https://github.com/Platykalt/corsu/blob/main/docs/en/phone/android.md), [iPhone](https://github.com/Platykalt/corsu/blob/main/docs/en/phone/iphone.md) |
| Phone, regional variant (experimental) | `corsu-keyboard-cismuntincu.kmp` or `corsu-keyboard-pumuntincu.kmp` | same vocabulary, preferring the forms of Cismonte or Pumonte (361 words weighted differently, partial coverage); package 1.2. On Android only one dictionary is active per language: uninstall the other, then restart Keyman |
| Minecraft Java 26.3, without the app | `corsu-minecraft-java-26.3.zip` | resource pack: Options › Resource Packs, turn it on, then Options › Language › Corsu; optional pack of the splash and end texts: `corsu-minecraft-java-texts-26.3.zip`. Other versions (1.6.1 → 26.2): through the Corsu app ([versions and checks](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) |

In one line: `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex` in PowerShell on
Windows, or `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh` in Terminal on
macOS and Linux. The [guides](https://github.com/Platykalt/corsu/tree/main/docs/en) explain each step.
The Corsu app then opens in its own window.

Each file has a `.sha256` checksum. The archives carry their own Python. Every archive was installed, used after
deleting the extracted folder, updated and uninstalled on its own system before publication (automated checks; no one
looked at the screens).

### New in 0.27.0

<!-- corsu:keyboard-figures Packages 1.2, 19,341 words per package (tools/count_kmp.py on the built .kmp files); 1.1:
     13,213. Count again if the keyboard changes before publication (docs/release-checklist-phone.md). -->
- **Phone keyboard** (packages 1.2, 19,341 words per package, against 13,213 in the 1.1 packages): no space is added
  before punctuation already in the text (`Aiacc|.` then "Aiacciu" gives "Aiacciu.", not "Aiacciu ."); at the end of
  a word on Android and iPhone, inside a word on Android only. The typographic apostrophe is kept ("l’is" gives
  "l’isula"). 6,012 forms that the sources write (plurals, feminines, Wiktionary forms, elided forms) are now known
  words, so Keyman 19's automatic correction no longer replaces correct words ("tradizioni", "abitanti",
  "l'ADECEC"); the selection was made by AI and **not checked by a speaker**, and forms from Vikipedia are
  counted in Corsican prose only (titles, quotations and Italian, French or Latin passages left out). Historical place
  names added from a sourced inventory: pievi, micro-regions, former dioceses, provinces and historical divisions; coverage limited to the reference lists used,
  not exhaustive (113
  words, including "Vallerustie", "Mariana", "Accia"); compound names are known word by word. The final packages were checked in Keyman's engines (headless browser, not the app): every check passes with
  Keyman 18.0.254, the stable version; with the 19.0.309 beta every word case passes, but the "auto-correct on"
  scenario fails intermittently on an internal engine error (`isFullReplacement`), also reproduced with the earlier 1.1
  and 1.2 packages, whose origin is not fully isolated. The space before punctuation was also seen in both apps on an
  Android 14 emulator, with earlier 1.2 data; **not on a real phone, not on iPhone**. To update: download the file again under the same name, then restart Keyman
  (guides above); Keyman then shows version 1.2.
- **Report a translation from the window** ("Signaler" page): program, version, text seen, place, proposal and notes.
  The page shows the report, copies it, or opens a prefilled GitHub issue, only on a click. Nothing is sent or stored
  by the page; personal folder paths and e-mail addresses are replaced.
- **Review by speakers**: 71 short sets of questions on the Minecraft texts
  ([review/](https://github.com/Platykalt/corsu/tree/main/review)), each one a Markdown page and a self-contained HTML
  page that builds a reply to copy or send as a prefilled issue. An answer goes back to "to re-examine" when the
  English or the Corsican text changes.
- **Language review, round 5** (AI work, re-checked by a separate AI pass; **no speaker review**): Minecraft Java,
  about 700 texts read and 16 changed (for example `doFireTick` "U focu si sparghje"), checked on the 87 releases
  with each game's code; Discord: a bare "Supprimer" takes the verb of its dialog, Spirlà/Dispirlà (pin), In linea /
  Fora di linea; Firefox: Minuteria for the New Tab timer; KDE: Squas for the Delete key.
- **Translation memory**: a translation written for another sense is no longer reused, an abbreviation is never reused
  from the only translation found elsewhere, and each reuse records where it comes from.
- The update from the published 0.26.0 is checked automatically.
- **Minecraft Bedrock**: a prototype exists in the repository but is **not attached** to this release (never loaded
  in the game).

### Earlier: new in 0.26.0

- **Updates**: 0.24.0 could say "up to date" while 0.25.1 was out: a window left open checked only when it opened, a
  new launch showed that window again, and a GitHub answer was reused for 6 hours as if fresh
  ([diagnosis](https://github.com/Platykalt/corsu/blob/main/docs/update-diagnosis.md)). Now an answer serves one hour
  at most, an open window checks every hour and at each launch, a failure (network, GitHub limit, incomplete answer)
  shows "check impossible", never "up to date", and the window shows its version, the installed copy, the latest
  release and when GitHub answered. If your Corsu is stuck on an old version, the "Rechercher" button or the
  one-line install above catches up and keeps your settings.
- **Phone keyboard** (packages 1.1): the case typed is kept and suggestions at a sentence start get a capital;
  vocabulary rebuilt from cited sources (13,213 words); Corsican place names and the communes' official names; two
  experimental regional preferences. On Android a suggestion chosen inside a word replaces the whole word; on iPhone
  Keyman replaces only its beginning (safe gestures in the guide). Checked in Keyman 18.0.254's engine and in the app
  on an Android 14 emulator; **not on a real phone, not on iPhone**. Keyman 18 has no automatic correction.
- **Minecraft**: AI review of the texts (senses corrected, sources cited), main menu buttons "Ghjucà solu" and
  "Ghjucà cù l'altri", "Arregistrà è esce da u mondu" in the pause menu; all 87 versions checked with each game's own
  code. **No text reviewed by a speaker**; nothing was looked at on screen in the game.
- **Discord**: the notification-area menu ("Quitter Discord"…) is translated; several labels reviewed.
- **KDE**: shortcuts without a Corsican name ("Display Configuration") no longer show in English.
- **Corsu's window**: new logo, recognised in Alt+Tab and the taskbar on KDE (Windows and macOS: not observed).
- **Firefox**: tab menu and profile labels reviewed.
- Every published file now has its own `.sha256`.

### Earlier: new in 0.25.1

0.25.0 was tagged but never published: the Windows check found the fault below. 0.25.1 is 0.25.0 with this fix.

- **Windows**: when Corsu's window read its state file while an installer was replacing it (or when two installers
  started together), the operation could stop on "Permission denied". Corsu now tries again for up to two seconds.

- **Poedit**: Corsu switches on its Corsican translation. Linux: Debian package (3.6.3) and Flatpak (3.10) run for
  real with French, German and Italian sessions: Poedit in Corsican, file dialogs and standard buttons in the usual
  language, regional formats unchanged. Trade-off: this relies on how Linux's C library (glibc) reads language names;
  when Corsu cannot check it, Poedit still turns Corsican but file dialogs stay in English (the session's formats
  are kept), and the app says so.
  Windows: Poedit's language setting, checked on simulated files only. macOS, **experimental**: Poedit's own language
  list (never the system language), given back as it was when switched off, and a later "System default" choice
  is respected; writing the preference checked on a CI macOS machine, Poedit itself never started on a Mac.
- **PDFsam** (5.0 and later): Corsu sets its language to Corsican. Run for real on Linux (official 6.0.6 package);
  PDFsam must be closed while it is switched. Windows: checked on simulated files only. macOS: left alone, with what
  to do.
- **Firefox**: times, dates and numbers follow the computer's regional settings again ("11:32 AM" showed on a French
  system): those of the system's date category (`LC_TIME`), numbers included; a choice made in Firefox's settings
  still wins. `profiles.ini` and `installs.ini` come back unchanged when Firefox is switched off or Corsu
  uninstalled (a Corsu section stayed there). Browser tools and download messages translated (31 AI
  texts, to be reviewed); "Onglets ouverts" no longer translated as a verb; the text check verifies the order of
  inserted values.
- **New window**: side navigation, a summary at the top (what is in Corsican, what needs you, update), a compact list
  with problems first, technical details on demand. **Appearance** section: light, dark or system theme, five
  palettes, accent colour (adjusted when hard to read), plain background or personal picture (preview, framing,
  Apply/Cancel, dimming, optional blur), comfortable or compact density, reset of the appearance only. The picture is
  checked, reduced and copied to Corsu's data; nothing is sent anywhere. Seen in Chrome and WebKitGTK (Linux); not
  yet observed in WebView2 (Windows) or on macOS.
- **Discord**: "Dans un appel" translated in the direct message list; the profile's "Bio" becomes "Biugrafia" (it
  was "Organicu", taken from Chrome's image styles); "Message" is the noun "Messaghju" again; 51 labels taken from
  other programs put back in Discord's sense, and other abbreviations written out (AI review, not a speaker's).
  Activities, games (even shown under another name), statuses and names stay as written; people's names, nicknames,
  private conversations and names containing a comma are protected everywhere; the "is typing" indicator is
  translated. Checked on simulated pages and on the built plugin in Chrome, not yet in a real Discord.
- **Window security (Linux)**: on a shared computer, another account could trigger the Corsu window's actions
  (install, update, uninstall) while it was open. The window now checks the exact connection and refuses a caller
  it cannot identify. This also fixes random refusals of the user's own actions. On every system, a key made at each
  launch is now required for every read and action: on Windows and macOS another account could read Corsu's state
  and the background picture (see `docs/window-security.md`).
- **Linux launchers**: the archive's Python is kept, and shortcuts use it when the system's Python goes away or is
  incomplete (in 0.24.0 they stopped working); installing with only `python3-minimal` no longer fails.
- **VLC complement**: Tools becomes "A&ttrezzi" (Alt+T), it took Alt+A like Audio; "Sempre s&opra" no longer doubles
  Alt+S. Fixes to AI drafts, VLC's upstream translation is unchanged. The 3 uncertain translations stay left out.
  The complement was silently refused in sessions where VLC translates its version line (German, Italian,
  Corsican…): fixed.
- **Update from 0.24.0** checked on Linux (Debian container, French session): parts switched off stay off, the VLC
  complement stays on and is really loaded by VLC, regional settings and personal files unchanged, Poedit and PDFsam
  detected then switched on, switching off and uninstalling give the originals back unchanged.

### Earlier: new in 0.24.0

- **Audacity 3 and 4, Tenacity, fre:ac**: Corsu switches on their own Corsican translation (Patriccollu's) through
  their language setting. Audacity 3, Audacity 4 and Tenacity started for real on Linux (official AppImages); fre:ac
  started for real on Linux (Debian package): window in Corsican, setting kept when it quits, switched off, kept off
  through an update, uninstalled. Windows and macOS: checked on simulated folders only; Audacity 4 is experimental
  there. When a program is left alone, the app says what to do.
- **VLC, experimental Corsican complement (Linux, off by default)**: VLC's translation leaves 1,760 texts of VLC 3.0.x
  in English. Corsu offers AI translations for them, reviewed by AI (1,757; 3 uncertain ones left out), **not reviewed
  by a Corsican speaker**. They are used only when you ask: the "Experimental complement" switch in VLC's row of the
  app, or `--vlc-complement on` (`off` goes back to VLC's own catalogue, still Corsican). No system file changes: VLC
  reads the complement from Corsu's folder through its `VLC_DATA_PATH` variable, set by the menu entry. Only for VLC
  3.0.x installed from Linux packages; not on Windows, macOS, Flatpak or Snap (the app says why). Checks: loading seen
  in the command-line help of VLC 3.0.20 (Ubuntu 24.04, 741 new texts in Corsican) and 3.0.24 (Debian 13, 685);
  display looked at in VLC 3.0.24's window only (menu bar, Tools and View menus, Video and Input / Codecs
  preferences), not the whole interface.
- VLC's upstream translations stay byte for byte; every draft and every review is tracked in
  `contrib/vlc/review.json`. Nothing was sent to VLC.

### Earlier: new in 0.23.0

<!-- corsu:minecraft-summary:start -->
- **Minecraft: Java Edition in Corsican for 87 versions** (releases 1.6.1 → 26.3). Complete translation of the language files for the listed versions; technical checks with each version's own code. ([versions and checks](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) This Corsu release contains these packs: close Minecraft, then the app finds the version of each game folder (official launcher, Prism Launcher, MultiMC), adds that version's pack and picks Corsican. Limits: texts written by AI; second AI pass on a sample of 150 entries of the 3,978 older texts (not on all of them); review by a Corsican speaker: 0; only 26.3 has been started with the pack, on the maintainer's Prism Launcher instance (2026-10-16): the game's log shows the pack loaded and messages in Corsican. No per-key visual check has been recorded, which is why [STATUS.md](https://github.com/Platykalt/corsu/blob/main/minecraft/java/STATUS.md) counts "seen in game: 0". The other versions have not been started. The automated checks are neither a speaker's review nor a visual check of every screen. No snapshots, pre-releases, Bedrock or versions before 1.6.1.
<!-- corsu:minecraft-summary:end -->

- Updating from the app (About): installed version, latest stable version, a check when it opens, "Update", optional
  automatic installation (off by default). Running the installer or the one-line command again updates or repairs the
  existing installation with the same choices (a part switched off stays off); an older version is refused; only one
  Corsu task runs at a time.
- The download targets the exact version announced, checks its SHA-256 and version, and extracts without being able to
  leave its folder; the new copy is complete before it replaces the old one, which stays as a fallback.
- Discord: user names, display names and nicknames are no longer translated ("Work" and "Error" showed as "Travagliu"
  and "Sbagliu"); only the interface text around them is.
- Minecraft: the Corsican pack is active from the first start; new instances waiting for activation are shown.
- Fixed since 0.22.0: installed copy without the Minecraft files, crash of a second VLC Flatpak activation.

[CHANGELOG.md](https://github.com/Platykalt/corsu/blob/main/CHANGELOG.md)
