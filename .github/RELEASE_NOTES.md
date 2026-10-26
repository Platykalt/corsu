**Français** · [English](#english)

**Windows : avec Corsu 0.26.0 ou 0.27.0, la fenêtre de Corsu se fermait au démarrage. La 0.28.0 corrige ce
défaut.** Téléchargez `corsu-windows.zip` ci-dessous (aucun compte GitHub nécessaire) ou relancez l'installation en
une ligne ; vos choix sont gardés.

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

### Nouveautés de la 0.28.0

- **Windows** : la fenêtre de Corsu ne se ferme plus au démarrage (défaut des 0.26.0 et 0.27.0). Windows reçoit
  maintenant une icône au format `.ico`. Vérifié automatiquement sur un Windows Server : la vraie fenêtre, ouverte
  avec le Python de l'archive, reste affichée. macOS et Linux : inchangés.
- **Firefox** : clic droit sur un texte sélectionné, la recherche s'affiche en corse (« Circà « … » cù Google »).
  Proposition IA, bâtie sur une formulation que Corsu emploie déjà.
- **Discord** : les champs de recherche (« Rechercher … ») et le message d'épinglage (« X a épinglé un message dans
  ce salon. Voir tous les messages épinglés. ») sont traduits ; les noms restent tels quels. Traductions reprises de
  l'usage de Corsu, non relues par un locuteur. Vérifié sur des pages simulées avec le plugin construit, dans
  Chromium sans affichage ; pas dans le vrai Discord.
- **Désactiver** : quand vous éteignez une partie (interrupteur ou gros bouton « Désactiver ») alors que le logiciel
  concerné est ouvert (Firefox, Discord, KDE), la fenêtre dit de le redémarrer ; l'indication disparaît
  après le redémarrage. Réparation et mise à jour gardent les parties éteintes.
- **Source de téléchargement** : l'installation en une ligne et la mise à jour affichent un avertissement quand une
  source non officielle est utilisée (`CORSU_DOWNLOAD_BASE`, prévue pour le développement). La somme SHA-256 prouve
  que le transfert est intact, pas d'où vient le fichier.
- La mise à jour et la migration depuis la 0.27.0 publiée sont vérifiées automatiquement.

### Rappel : nouveautés de la 0.27.0

<!-- corsu:keyboard-figures Paquets 1.2, 19 341 mots par paquet (tools/count_kmp.py sur les .kmp construits) ; 1.1 :
     13 213. À recompter si le clavier change avant la publication (docs/release-checklist-phone.md). -->
- **Clavier sur téléphone** (paquets 1.2, 19 341 mots par paquet, contre 13 213 dans les paquets 1.1) : plus d'espace
  ajoutée devant une ponctuation déjà écrite (`Aiacc|.` puis « Aiacciu » donne « Aiacciu. », et non « Aiacciu . ») ; à
  la fin d'un mot sous Android et sur iPhone, au milieu d'un mot sous Android seulement. L'apostrophe typographique
  est gardée (« l’is » donne « l’isula »). 6 012 formes écrites par les sources (pluriels, féminins, formes du
  Wiktionnaire, formes élidées) sont maintenant connues, pour que la correction automatique de Keyman 19 ne remplace
  plus des mots justes (« tradizioni », « abitanti », « l'ADECEC ») ; sélection faite par IA, **non vérifiée par un
  locuteur** ; les formes de Vikipedia ne sont comptées que dans la prose corse (titres, citations et passages en
  italien, français ou latin écartés). Noms de lieux historiques ajoutés d'après un inventaire sourcé : pievi,
  micro-régions, anciens diocèses, provinces et divisions historiques ; couverture limitée aux listes de référence
  retenues, pas exhaustive (113 mots, dont « Vallerustie », « Mariana », « Accia ») ; les noms composés sont reconnus
  mot par mot. Paquets finaux vérifiés dans les moteurs de Keyman (navigateur sans affichage, pas dans l'application)
  : tous les contrôles passent avec Keyman 18.0.254, la version stable ; avec la bêta 19.0.309, tous les cas de mots
  passent, mais le scénario « correction automatique activée » échoue par intermittence sur une erreur interne du
  moteur (`isFullReplacement`), reproduite aussi avec les paquets 1.1 et 1.2 précédents, d'origine non complètement
  isolée. Espace avant la ponctuation vu aussi dans les deux applications sur émulateur Android 14, avec des données
  1.2 antérieures ; **pas sur un vrai téléphone, pas sur iPhone**. Mettre à jour : télécharger de nouveau le fichier
  sous le même nom, puis relancer Keyman (guides ci-dessus) ; Keyman affiche alors la version 1.2.
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
  prennent une ; vocabulaire refait à partir de sources citées (13 213 mots) ; noms de lieux corses et noms officiels
  des communes ; deux préférences régionales expérimentales. Sous Android, une suggestion choisie au milieu d'un mot
  remplace le mot entier ; sur iPhone, Keyman ne remplace que le début (gestes conseillés dans le guide). Vérifié dans
  le moteur de Keyman 18.0.254 et dans l'application sur émulateur Android 14 ; **pas sur un vrai téléphone, pas sur
  iPhone**. Keyman 18 n'a pas de correction automatique.
- **Minecraft** : revue IA des textes (sens corrigés, sources citées), boutons du menu principal « Ghjucà solu » et
  « Ghjucà cù l'altri », « Arregistrà è esce da u mondu » dans le menu de pause ; les 87 versions vérifiées avec le
  code de chaque jeu. **Aucun texte relu par un locuteur** ; rien n'a été regardé à l'écran dans le jeu.
- **Discord** : le menu de la zone de notification (« Quitter Discord »…) est traduit ; plusieurs libellés revus.
- **KDE** : les raccourcis sans nom corse (« Display Configuration ») ne s'affichent plus en anglais.
- **Fenêtre de Corsu** : nouveau logo, reconnu dans Alt+Tab et la barre des tâches sous KDE (Windows et macOS : non
  observés).
- **Firefox** : libellés du menu des onglets et des profils revus.
- Chaque fichier publié a maintenant sa propre somme `.sha256`.

### Minecraft Java

<!-- corsu:minecraft-summary:start -->
- **Minecraft Java en corse pour 87 versions** (versions stables 1.6.1 → 26.3). Traduction complète des fichiers de langue pour les versions listées ; vérifications techniques avec le code de chaque version. ([versions et vérifications](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) Cette version de Corsu contient ces packs : fermez Minecraft, puis l'application trouve la version de chaque dossier de jeu (lanceur officiel, Prism Launcher, MultiMC), y ajoute le pack de cette version et choisit le corse. Limites : textes écrits par IA ; deuxième passe IA sur un échantillon de 150 entrées des 3 978 textes anciens (pas sur tous) ; relecture par un locuteur : 0 ; seule la 26.3 a été lancée avec le pack, sur l'instance Prism Launcher du mainteneur (2026-10-16) : le journal du jeu montre le pack chargé et des messages en corse. Aucune vérification visuelle clé par clé n'est enregistrée : c'est pourquoi [STATUS.md](https://github.com/Platykalt/corsu/blob/main/minecraft/java/STATUS.md) compte « vu en jeu : 0 ». Les autres versions n'ont pas été lancées. Les vérifications automatiques ne sont ni une relecture par un locuteur ni un contrôle visuel de chaque écran. Pas les snapshots, pré-versions, Bedrock ni les versions avant 1.6.1.
<!-- corsu:minecraft-summary:end -->

## English

**Windows: with Corsu 0.26.0 or 0.27.0, Corsu's window closed at start. 0.28.0 fixes this.** Download
`corsu-windows.zip` below (no GitHub account needed) or run the one-line install again; your choices are kept.

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

### New in 0.28.0

- **Windows**: Corsu's window no longer closes at start (a fault of 0.26.0 and 0.27.0). Windows now gets an icon in
  `.ico` format. Checked automatically on a Windows Server: the real window, started with the archive's Python, stays
  up. macOS and Linux: unchanged.
- **Firefox**: right-click on selected text, the search shows in Corsican ("Circà « … » cù Google"). AI proposal,
  built on wording Corsu already uses.
- **Discord**: the search fields ("Rechercher …") and the pin message ("X a épinglé un message dans ce salon. Voir
  tous les messages épinglés.") are translated; names stay as written. Translations taken from Corsu's own usage, not
  read by a speaker. Checked in simulated pages with the built plugin, in headless Chromium; not in the real Discord.
- **Switching off**: when you switch a part off (its switch or the big "Désactiver" button) while its program is
  open (Firefox, Discord, KDE), the window says to restart it; the line goes away after the restart. Repair
  and update keep the parts switched off.
- **Download source**: the one-line install and the update show a warning when a non-official source is used
  (`CORSU_DOWNLOAD_BASE`, meant for development). The SHA-256 checksum proves the transfer is intact, not where the
  file comes from.
- The update and the migration from the published 0.27.0 are checked automatically.

### Earlier: new in 0.27.0

<!-- corsu:keyboard-figures Packages 1.2, 19,341 words per package (tools/count_kmp.py on the built .kmp files); 1.1:
     13,213. Count again if the keyboard changes before publication (docs/release-checklist-phone.md). -->
- **Phone keyboard** (packages 1.2, 19,341 words per package, against 13,213 in the 1.1 packages): no space is added
  before punctuation already in the text (`Aiacc|.` then "Aiacciu" gives "Aiacciu.", not "Aiacciu ."); at the end of a
  word on Android and iPhone, inside a word on Android only. The typographic apostrophe is kept ("l’is" gives
  "l’isula"). 6,012 forms that the sources write (plurals, feminines, Wiktionary forms, elided forms) are now known
  words, so Keyman 19's automatic correction no longer replaces correct words ("tradizioni", "abitanti", "l'ADECEC");
  the selection was made by AI and **not checked by a speaker**, and forms from Vikipedia are counted in Corsican
  prose only (titles, quotations and Italian, French or Latin passages left out). Historical place names added from a
  sourced inventory: pievi, micro-regions, former dioceses, provinces and historical divisions; coverage limited to
  the reference lists used, not exhaustive (113 words, including "Vallerustie", "Mariana", "Accia"); compound names
  are known word by word. The final packages were checked in Keyman's engines (headless browser, not the app): every
  check passes with Keyman 18.0.254, the stable version; with the 19.0.309 beta every word case passes, but the
  "auto-correct on" scenario fails intermittently on an internal engine error (`isFullReplacement`), also reproduced
  with the earlier 1.1 and 1.2 packages, whose origin is not fully isolated. The space before punctuation was also
  seen in both apps on an Android 14 emulator, with earlier 1.2 data; **not on a real phone, not on iPhone**. To
  update: download the file again under the same name, then restart Keyman (guides above); Keyman then shows version
  1.2.
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

### Minecraft Java

<!-- corsu:minecraft-summary:start -->
- **Minecraft: Java Edition in Corsican for 87 versions** (releases 1.6.1 → 26.3). Complete translation of the language files for the listed versions; technical checks with each version's own code. ([versions and checks](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) This Corsu release contains these packs: close Minecraft, then the app finds the version of each game folder (official launcher, Prism Launcher, MultiMC), adds that version's pack and picks Corsican. Limits: texts written by AI; second AI pass on a sample of 150 entries of the 3,978 older texts (not on all of them); review by a Corsican speaker: 0; only 26.3 has been started with the pack, on the maintainer's Prism Launcher instance (2026-10-16): the game's log shows the pack loaded and messages in Corsican. No per-key visual check has been recorded, which is why [STATUS.md](https://github.com/Platykalt/corsu/blob/main/minecraft/java/STATUS.md) counts "seen in game: 0". The other versions have not been started. The automated checks are neither a speaker's review nor a visual check of every screen. No snapshots, pre-releases, Bedrock or versions before 1.6.1.
<!-- corsu:minecraft-summary:end -->
