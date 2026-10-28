**Français** · [English](#english)

**Windows : plus de fenêtres PowerShell qui s'ouvrent et se ferment pendant que Corsu est ouvert. Discord : le
message d'épinglage et « Aller à {serveur} » sont traduits.** Mise à jour depuis la fenêtre de Corsu (bouton
« Rechercher les mises à jour ») ou par l'installation en une ligne ; vos choix sont gardés.

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

### Nouveautés de la 0.28.3

- **Windows, fenêtres PowerShell** : tant que la fenêtre de Corsu restait ouverte, des consoles PowerShell
  apparaissaient et disparaissaient sans cesse. Corsu y lisait la liste des programmes ouverts, cherchait Minecraft
  ou lisait son raccourci. Ces commandes techniques tournent maintenant sans console, et la liste des programmes est
  lue au plus toutes les 2 secondes. Leurs sorties, codes d'erreur et journaux restent visibles dans Corsu (et dans
  le terminal si vous lancez l'installation depuis un terminal). Les demandes d'autorisation de Windows (UAC)
  s'affichent toujours. Vérifié automatiquement sur un Windows Server de GitHub : lancement par le raccourci installé,
  avec Minecraft, plusieurs rafraîchissements et des actions depuis la fenêtre, chaque processus lancé et chaque
  fenêtre affichée surveillés ; la 0.28.2 y ouvrait 8 consoles PowerShell en 76 secondes, la 0.28.3 aucune. **Pas
  encore observé sur le PC d'un utilisateur.**
- **Discord, message d'épinglage** : « … a épinglé un message dans ce salon. Voir tous les messages épinglés. »
  restait en français dans la conversation : Discord l'affiche dans le même bloc que les messages des personnes, que
  Corsu protège. Il devient « … hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati. » ; le pseudo,
  les liens et l'heure restent tels quels, et un message écrit par une personne avec les mêmes mots n'est pas touché.
  Même correction pour « a ajouté … au groupe » et « a retiré … du groupe ».
- **Discord, « Aller à {serveur} »** (bouton ou libellé qui ouvre un serveur déjà rejoint) restait en français ; il
  devient « Andà à {serveur} », le nom du serveur tel quel. « Aller sur le serveur » était déjà traduit.
- **Ce qui a été vérifié pour Discord** : pages simulées d'après la structure du client web public de Discord
  (28 octobre 2026), avec le plugin construit, dans Chromium sans affichage : affichage initial, nouveau message,
  retour après navigation. Les essais échouent avec le plugin de la 0.28.2 et passent avec celui de la 0.28.3. Pas
  dans l'application Discord elle-même. Traductions reprises de l'usage de Corsu, **non relues par un locuteur**.
- Un Discord ouvert avant la mise à jour garde l'ancien plugin jusqu'à son redémarrage.
- La mise à jour et la migration depuis la 0.28.2 publiée sont vérifiées automatiquement.

### Rappel : nouveautés de la 0.28.2

- **Fenêtre : page « Accueil »** (« Accolta » en corse), à la place de « Logiciels ». En haut, l'état général : ce qui
  est en corse, ce qui attend votre intervention, la mise à jour éventuelle. Ensuite « Logiciels gérés par Corsu »,
  où chaque ligne dit son état : en corse, partiellement en corse, en langue d'origine ou redémarrage nécessaire (une
  partie éteinte pendant que son logiciel est ouvert compte aussi dans « à vérifier »). Les interrupteurs, les
  dossiers Minecraft et les autres commandes ne changent pas. « Accolta » vient de la traduction corse de Firefox déjà
  reprise par Corsu ; le titre de la liste et la phrase d'introduction sont des propositions IA, non relues par un
  locuteur.
- **Discord, champ de saisie** : « Envoyer un message à @… » était revenu en français depuis la 0.28.0. Il redevient
  « Mandà un messaghju à @… », aussi après un brouillon effacé ; le brouillon et le curseur ne sont jamais touchés.
- **Discord, recherche dans une conversation** : « Rechercher Ron » disait « Circà Ron », lu comme chercher la
  personne ; il dit maintenant « Circà in Ron ». La recherche de personnes garde « Circà ».
- **Discord, messages système** : le message d'épinglage tel que Discord l'affiche aujourd'hui (« … a épinglé un
  message dans ce salon. Voir tous les messages épinglés. ») et le lien « Modifier le groupe » d'un groupe renommé
  restaient en français ; ils sont traduits. Un message système affiché dans l'aperçu d'une conversation est traduit,
  le message d'une personne avec les mêmes mots reste tel quel.
- **Discord, pseudonymes qui ressemblent à un libellé** : avec une personne nommée « a ajouté », le texte du message
  système à côté du nom restait en français ; seul le nom reste tel quel désormais.
- **Ce qui a été vérifié** : essais automatiques écrits à partir de la structure du client web public de Discord
  (27 octobre 2026), sur des pages simulées avec le plugin construit, dans Chromium sans affichage ; pas dans
  l'application Discord elle-même. Les traductions reprennent l'usage de Corsu ou sont des propositions IA ; **aucune
  n'a été relue par un locuteur**. La relecture linguistique de Discord continue séparément : environ 785 textes sur
  22 430 examinés (3,5 %), par IA ; le reste n'est pas relu.
- Un Discord ouvert avant la mise à jour garde l'ancien plugin jusqu'à son redémarrage.
- La mise à jour et la migration depuis la 0.28.1 publiée sont vérifiées automatiquement.

### Rappel : nouveautés de la 0.28.1

- **Discord, conversations de groupe** : « X a ajouté Y au groupe. », « X a retiré Y du groupe. » et « X a quitté le
  groupe. » restaient en français. Ils deviennent « X hà aghjuntu Y à u gruppu. », « X hà cacciatu Y da u gruppu. »
  et « X hà lasciatu u gruppu. » ; les noms restent tels quels. « du groupe. » disait « di u gruppu » et dit
  maintenant « da u gruppu », comme « Caccià da u gruppu » déjà employé par Corsu. Traductions reprises de l'usage de
  Corsu, non relues par un locuteur. Vérifié sur des pages simulées avec le plugin construit, pas dans le vrai
  Discord.
- **Retour depuis la version de développement Hyprland** : l'installateur de la 0.28.0 refusait les parties
  `hyprland` et `hyprland-profile` notées par cette version (`invalid choice: 'hyprland'`), sans rien abîmer.
  L'installateur laisse maintenant telle quelle une partie notée qu'il ne connaît pas.
- La mise à jour et la migration depuis la 0.28.0 publiée sont vérifiées automatiquement.

### Rappel : nouveautés de la 0.28.0

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

### Minecraft Java

<!-- corsu:minecraft-summary:start -->
- **Minecraft Java en corse pour 87 versions** (versions stables 1.6.1 → 26.3). Traduction complète des fichiers de langue pour les versions listées ; vérifications techniques avec le code de chaque version. ([versions et vérifications](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) Cette version de Corsu contient ces packs : fermez Minecraft, puis l'application trouve la version de chaque dossier de jeu (lanceur officiel, Prism Launcher, MultiMC), y ajoute le pack de cette version et choisit le corse. Limites : textes écrits par IA ; deuxième passe IA sur un échantillon de 150 entrées des 3 978 textes anciens (pas sur tous) ; relecture par un locuteur : 0 ; seule la 26.3 a été lancée avec le pack, sur l'instance Prism Launcher du mainteneur (2026-10-16) : le journal du jeu montre le pack chargé et des messages en corse. Aucune vérification visuelle clé par clé n'est enregistrée : c'est pourquoi [STATUS.md](https://github.com/Platykalt/corsu/blob/main/minecraft/java/STATUS.md) compte « vu en jeu : 0 ». Les autres versions n'ont pas été lancées. Les vérifications automatiques ne sont ni une relecture par un locuteur ni un contrôle visuel de chaque écran. Pas les snapshots, pré-versions, Bedrock ni les versions avant 1.6.1.
<!-- corsu:minecraft-summary:end -->

## English

**Windows: no more PowerShell windows opening and closing while Corsu is open. Discord: the pin notice and "Aller à
{server}" are translated.** Update from Corsu's window ("Rechercher les mises à jour" button) or with the one-line
install; your choices are kept.

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

### New in 0.28.3

- **Windows, PowerShell windows**: while Corsu's window was open, PowerShell consoles kept appearing and
  disappearing. Corsu used them to read the list of running programs, look for Minecraft or read its shortcut. These
  technical commands now run without a console, and the program list is read at most every 2 seconds. Their output,
  error codes and logs still reach Corsu (and the terminal when you install from one). Windows' own permission
  prompts (UAC) still show. Checked automatically on a GitHub Windows Server: started from the installed shortcut,
  with Minecraft, several refreshes and actions from the window, every process started and every window shown
  watched; 0.28.2 opened 8 PowerShell consoles in 76 seconds there, 0.28.3 none. **Not yet observed on a user's PC.**
- **Discord, pin notice**: "… a épinglé un message dans ce salon. Voir tous les messages épinglés." stayed in French
  in the conversation: Discord draws it in the same block as people's messages, which Corsu protects. It now reads
  "… hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati."; the nickname, the links and the time
  stay as they are, and a person's message with the same words is not touched. Same fix for "a ajouté … au groupe"
  and "a retiré … du groupe".
- **Discord, "Aller à {server}"** (button or label that opens a server you already joined) stayed in French; it now
  reads "Andà à {server}", the server name as written. "Aller sur le serveur" was already translated.
- **What was checked for Discord**: simulated pages built from the structure of Discord's public web client
  (28 October 2026), with the built plugin, in headless Chromium: first display, new message, return after
  navigation. The checks fail with 0.28.2's plugin and pass with 0.28.3's. Not in the Discord app itself.
  Translations taken from Corsu's own usage, **not read by a speaker**.
- A Discord opened before the update keeps the older plugin until it is restarted.
- The update and the migration from the published 0.28.2 are checked automatically.

### Earlier: new in 0.28.2

- **Window: "Home" page** ("Accolta" in Corsican) in place of "Programs". At the top, the overall state: what is in
  Corsican, what needs you, a possible update. Then "Programs managed by Corsu", where each row says its state: in
  Corsican, partly in Corsican, original language or restart needed (a part switched off while its program is open
  also counts as needing attention). Switches, Minecraft folders and the other commands are unchanged. "Accolta"
  comes from Firefox's Corsican translation already used by Corsu; the list heading and the introduction are AI
  proposals, not read by a speaker.
- **Discord, message field**: "Envoyer un message à @…" was back in French since 0.28.0. It is "Mandà un messaghju à
  @…" again, also after an erased draft; the draft and the caret are never touched.
- **Discord, search in a conversation**: "Rechercher Ron" said "Circà Ron", read as searching for the person; it now
  says "Circà in Ron". Searching for people keeps "Circà".
- **Discord, system messages**: the pin notice as Discord draws it today ("… a épinglé un message dans ce salon. Voir
  tous les messages épinglés.") and the "Modifier le groupe" link of a renamed group stayed in French; they are
  translated. A system message shown in a conversation's preview line is translated, while a person's message with
  the same words stays as written.
- **Discord, nicknames that read like a label**: with someone named "a ajouté", the system message's text beside the
  name stayed in French; only the name stays as written now.
- **What was checked**: automated checks written from the structure of Discord's public web client (27 October 2026),
  in simulated pages with the built plugin, in headless Chromium; not in the Discord app itself. The translations
  come from Corsu's own usage or are AI proposals; **none was read by a speaker**. The Discord language review goes on
  separately: about 785 of 22,430 texts examined (3.5 %), by AI; the rest is not reviewed.
- A Discord opened before the update keeps the older plugin until it is restarted.
- The update and the migration from the published 0.28.1 are checked automatically.

### Earlier: new in 0.28.1

- **Discord, group conversations**: "X a ajouté Y au groupe.", "X a retiré Y du groupe." and "X a quitté le groupe."
  stayed in French. They now read "X hà aghjuntu Y à u gruppu.", "X hà cacciatu Y da u gruppu." and "X hà lasciatu u
  gruppu."; names stay as written. "du groupe." said "di u gruppu" (of the group) and now says "da u gruppu" (from
  the group), as Corsu's "Caccià da u gruppu". Translations taken from Corsu's own usage, not read by a speaker.
  Checked in simulated pages with the built plugin, not in the real Discord.
- **Going back from the Hyprland development build**: 0.28.0's installer refused the parts `hyprland` and
  `hyprland-profile` that build records (`invalid choice: 'hyprland'`), without damaging anything. The installer now
  leaves a recorded part it does not know as it is.
- The update and the migration from the published 0.28.0 are checked automatically.

### Earlier: new in 0.28.0

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

### Minecraft Java

<!-- corsu:minecraft-summary:start -->
- **Minecraft: Java Edition in Corsican for 87 versions** (releases 1.6.1 → 26.3). Complete translation of the language files for the listed versions; technical checks with each version's own code. ([versions and checks](https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md)) This Corsu release contains these packs: close Minecraft, then the app finds the version of each game folder (official launcher, Prism Launcher, MultiMC), adds that version's pack and picks Corsican. Limits: texts written by AI; second AI pass on a sample of 150 entries of the 3,978 older texts (not on all of them); review by a Corsican speaker: 0; only 26.3 has been started with the pack, on the maintainer's Prism Launcher instance (2026-10-16): the game's log shows the pack loaded and messages in Corsican. No per-key visual check has been recorded, which is why [STATUS.md](https://github.com/Platykalt/corsu/blob/main/minecraft/java/STATUS.md) counts "seen in game: 0". The other versions have not been started. The automated checks are neither a speaker's review nor a visual check of every screen. No snapshots, pre-releases, Bedrock or versions before 1.6.1.
<!-- corsu:minecraft-summary:end -->
