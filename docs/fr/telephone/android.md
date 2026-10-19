# Écrire en corse sur Android

[English](../../en/phone/android.md) · [iPhone](iphone.md)

**Aucune installation de Corsu sur un ordinateur n'est nécessaire** : tout se fait sur le téléphone.

**Télécharger le dictionnaire : [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp)**
(dernière version publiée, à ouvrir dans Keyman : voir [Installer](#installer)). Le fichier est joint aux versions de
Corsu, mais s'utilise seul.

Deux pièces, toutes deux gratuites :

- **Keyman** fournit le clavier. C'est une application de SIL, installée depuis le Play Store. Sa disposition
  EuroLatin (SIL) a toutes les lettres corses.
- **Corsu** fournit le dictionnaire : pendant que vous écrivez, il propose des mots corses dans le bandeau au-dessus
  du clavier et propose la bonne orthographe d'un mot mal tapé.

Le dictionnaire n'est ni un traducteur de phrases ni un correcteur de grammaire complet : il travaille mot par mot.

Ce guide suit Keyman pour Android 18.0 (version stable 18.0.254 au 16 octobre 2026). Les noms des boutons viennent de
l'aide officielle de Keyman et des fichiers de traduction de cette version ; une autre version peut les changer. Il
n'y a pas de captures d'écran.

## Dictionnaires disponibles

<!-- corsu:phone-variants:fr Fichiers joints à Corsu 0.27.0 (les trois paquets 1.2, 19 341 mots chacun, comptés
     avec tools/count_kmp.py dans les paquets construits). Ce guide décrit la 0.27.0 ; tant qu'elle n'est pas
     publiée, « dernière version publiée » donne encore les paquets 1.1 de Corsu 0.26.0 (13 213 mots). À la
     publication d'une version suivante, ne lister ici que les fichiers qu'elle contient. -->
| Fichier | Nom dans Keyman | Version | Contenu | Téléchargement |
| --- | --- | --- | --- | --- |
| `corsu-keyboard.kmp` | Corsu | 1.2 (à partir de Corsu 0.27.0) | dictionnaire général : le vocabulaire commun, 19 341 mots (mots parasites retirés), sans préférence régionale ; garde la majuscule des mots | [dernière version publiée](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) ([empreinte SHA-256](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp.sha256)) |
| `corsu-keyboard-cismuntincu.kmp` | Corsu – Cismuntincu (experimental) | 1.2 (à partir de Corsu 0.27.0) | le même vocabulaire, avec une préférence pour les formes du Cismonte ; expérimental, les formes régionales ne couvrent qu'une partie des mots (361 mots pondérés autrement) | [dernière version publiée](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-cismuntincu.kmp) ([empreinte SHA-256](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-cismuntincu.kmp.sha256)) |
| `corsu-keyboard-pumuntincu.kmp` | Corsu – Pumuntincu (experimental) | 1.2 (à partir de Corsu 0.27.0) | le même vocabulaire, avec une préférence pour les formes du Pumonte ; expérimental, même limite | [dernière version publiée](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-pumuntincu.kmp) ([empreinte SHA-256](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-pumuntincu.kmp.sha256)) |

« Version » est la version du paquet du dictionnaire, que Keyman affiche (voir l'étape 5) ; elle ne suit pas les
numéros de version de Corsu. Corsu 0.26.0 contenait les paquets 1.1 (13 213 mots).

Les trois sont pour la langue Corsican (`co`) et le clavier EuroLatin (SIL). Un seul suffit : voir
[Choisir un dictionnaire régional](#choisir-un-dictionnaire-régional).

## Installer

1. **Installez Keyman** depuis le [Play Store](https://play.google.com/store/apps/details?id=com.tavultesoft.kmapro)
   (ou depuis [keyman.com/android](https://keyman.com/android/)).
2. **Ajoutez le clavier EuroLatin (SIL) pour le corse.** Dans Keyman, ouvrez le menu, puis **Paramètres** ›
   **Langues installées**, et touchez **+** en bas à droite. Cherchez `Corsican` (la recherche se fait sur le nom
   anglais de la langue ; `l:id:co` marche aussi), choisissez **EuroLatin (SIL)** et touchez le bouton vert
   d'installation. Si l'installateur demande les langues, gardez **Corsican**. Keyman cherche ensuite un dictionnaire
   corse sur son propre site et peut répondre « Aucun dictionnaire à télécharger » : c'est normal, celui de Corsu
   s'installe à l'étape suivante.
   Le dictionnaire Corsu est rattaché à la langue Corsican (code `co`) : il ne sert que lorsque EuroLatin est
   utilisé pour le corse.
3. **Téléchargez le dictionnaire** sur le téléphone :
   [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp). Le fichier
   arrive en général dans le dossier Téléchargements (Download). Gardez exactement ce nom : si le navigateur l'a
   renommé `corsu-keyboard(1).kmp` ou `corsu-keyboard (1).kmp`, renommez-le (voir [Mettre à jour](#mettre-à-jour)).
4. **Importez-le dans Keyman.** Menu › **Paramètres** › **Installer un clavier ou un dictionnaire** › **Installer
   depuis un fichier local**, puis choisissez `corsu-keyboard.kmp` dans Téléchargements. Si Android demande
   l'accès aux fichiers, autorisez-le (Keyman le demande une seule fois). Keyman montre le paquet « Corsu » et sa
   version : touchez **Installer**, puis **OK** après la page d'accueil.
5. **Vérifiez le dictionnaire.** **Paramètres** › **Langues installées** › **Corsican** : en bas de l'écran,
   **Dictionnaire** indique le dictionnaire actif : « Corsu » pour le dictionnaire général. Pour voir sa version,
   touchez **Dictionnaire**, puis le dictionnaire coché : l'écran « Dictionnaire : … » montre la **Version du
   dictionnaire** (Keyman y affiche la version du paquet), à comparer avec le tableau [Dictionnaires
   disponibles](#dictionnaires-disponibles). Revenez en arrière sans toucher **Désinstaller le dictionnaire**.
6. **Réglez les suggestions** sur ce même écran. Keyman 18.0 propose trois choix, affichés en anglais même quand
   Keyman est en français : *Disable suggestions* (aucune), *Predictions only* (mots proposés, sans correction) et
   *Predictions with corrections* (mots proposés et fautes corrigées). Choisissez **Predictions with corrections**.
   Il n'y a pas de correction automatique dans cette version : voir
   [Correction automatique](#correction-automatique).
7. **Faites de Keyman le clavier du téléphone.** Menu › **Paramètres** › **Activer Keyman comme clavier système**
   (on le trouve aussi dans **Commencer**). L'écran des claviers d'Android s'ouvre : activez **Keyman**, puis
   répondez **OK** aux deux messages de confirmation. Android y rappelle qu'un clavier peut lire ce qu'on tape ; c'est
   l'avertissement de tout clavier ajouté. Ensuite, quand un clavier est affiché, l'icône de clavier en bas à droite
   de l'écran permet de choisir Keyman.
8. **Essayez.** Dans une application de notes ou de messages, choisissez Keyman, puis tapez `bonghj` : le bandeau devrait
   proposer « bonghjornu ». Tapez `grazzie` : il devrait proposer « grazie » ; touchez-le pour corriger.

## Mettre à jour

Téléchargez le nouveau fichier et installez-le comme à l'étape 4, **sous le même nom** `corsu-keyboard.kmp`. Keyman tire
l'identité du paquet du nom du fichier : si le navigateur a ajouté un suffixe (`corsu-keyboard(1).kmp`,
`corsu-keyboard (1).kmp`), renommez le fichier avant de l'installer, ou supprimez d'abord l'ancien téléchargement. Vos
réglages sont gardés. **Relancez ensuite Keyman** : jusque-là, l'ancien dictionnaire continue de répondre. Pour
relancer, passez à un autre clavier puis revenez à Keyman, ou forcez l'arrêt de l'application Keyman dans les réglages
d'Android. Vérifiez ensuite la version comme à l'étape 5 : 1.2 pour les paquets de Corsu 0.27.0 (1.1 pour ceux de Corsu
0.26.0). Un dictionnaire installé avant Corsu 0.26.0 s'appelle `platykalt.co.corsu` dans Keyman, version 1.0 : mettez-le
à jour.

Pour une liste d'essai complète, avec les résultats attendus : [Essai en 5 minutes](essai-5-minutes.md).

## Choisir un dictionnaire régional

<!-- corsu:phone-variants:fr Les deux variantes régionales sont publiées depuis Corsu 0.26.0 (paquets 1.1 ; 1.2 à
     partir de Corsu 0.27.0). -->
Deux dictionnaires expérimentaux préfèrent les formes du Cismonte ou du Pumonte :
[corsu-keyboard-cismuntincu.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-cismuntincu.kmp)
et
[corsu-keyboard-pumuntincu.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-pumuntincu.kmp)
(même vocabulaire, couverture partielle : voir [Dictionnaires disponibles](#dictionnaires-disponibles)). Gardez leur
nom de fichier exact. Sur Android, **un seul dictionnaire est actif par langue : le premier installé**. Installer un
deuxième paquet Corsu l'ajoute à la liste, mais l'ancien reste actif. Pour changer :

1. **Paramètres** › **Langues installées** › **Corsican** › **Dictionnaire** › le dictionnaire actif ›
   **Désinstaller le dictionnaire** ;
2. installez le paquet voulu (étape 4) s'il ne l'est pas déjà ;
3. relancez Keyman (voir [Mettre à jour](#mettre-à-jour)), puis vérifiez le nom affiché (étape 5).

Pour revenir au dictionnaire général, faites de même avec `corsu-keyboard.kmp` : **Dictionnaire** indique alors
« Corsu », version 1.2 (1.1 avec Corsu 0.26.0).

## Majuscules et début de phrase

- **La majuscule en début de phrase vient du clavier EuroLatin, pas du dictionnaire.** Elle s'active au début d'un
  champ et après `.`, `?` ou `!` suivis d'une espace. Elle ne s'active pas après un retour à la ligne sans
  ponctuation, ni après `."`, `…`, `:`, `;` ou `«` ; elle s'active à tort après `M. `. Il n'y a pas de réglage pour la
  couper : touchez la touche Maj pour l'annuler.
- **Les suggestions gardent la casse tapée** depuis Corsu 0.26.0 (paquets 1.1) : au milieu d'une phrase, `Ecc`
  propose « Eccu », et en début de phrase les suggestions ont la majuscule. Avec l'ancien paquet 1.0 (nommé
  `platykalt.co.corsu` dans Keyman), `Ecc` pouvait devenir « eccu » : si vous l'avez encore,
  [mettez-le à jour](#mettre-à-jour), puis relancez Keyman.
  <!-- corsu:phone-casing Corrigé depuis Corsu 0.26.0 (paquet 1.1) ; le paquet 1.0 perdait la majuscule. -->

## Correction automatique

Keyman 18.0, la version stable, **n'a pas de correction automatique** : les corrections sont proposées dans le bandeau
et ne s'appliquent que si vous les touchez. Le dictionnaire Corsu ne commande pas ce réglage. Keyman 19, encore en
version bêta, ajoute le choix *Predictions with auto-corrections* ; il apparaîtra sur l'écran Corsican quand Keyman 19
sera la version stable. Il restera facultatif. Dans nos essais du moteur de la bêta 19.0.309 (hors de l'application),
un mot présent dans le dictionnaire est toujours gardé tel qu'il est tapé, mais un mot absent peut être remplacé : un
nom par un nom proche (« Bastelicaccia » par « Bastilicaccia » quand seule la seconde graphie est dans le
dictionnaire), ou un mot en minuscules par le nom qui s'écrit pareil (« corti » par « Corti » quand « corti » y
manque). Le dictionnaire 1.1 (Corsu 0.26.0) contient ces formes (« Bastelicaccia », « corti » à côté de « Corti », «
Vizzani », des sigles comme « ADECEC ») ; un mot qui y manque encore, un nom de rue par exemple, peut toujours être
remplacé.

Le dictionnaire 1.2 (à partir de Corsu 0.27.0) connaît en plus environ 6 000 formes trouvées dans ses sources : pluriels
et féminins (« tradizioni », « fundata », « partuti », que le moteur 19.0.309 remplaçait par « tradizione »,
« fundatu », « partiti »), formes verbales du Wiktionnaire (« manghjatu ») et formes élidées (« l'abitanti »,
« L'ADECEC », devenues « abitanti » et « ADECEC »). Les formes qui lui manquent (formes verbales comme « vedemu »,
élisions plus rares) peuvent encore être remplacées.

## Revenir sur un mot

Déplacer le curseur ne change rien au texte. Les suggestions suivent la partie du mot **à gauche du curseur**.

- **Curseur à la fin du mot** : la suggestion choisie remplace le mot entier. C'est le geste sûr, quel que soit le
  dictionnaire.
- **Curseur au milieu du mot**, avec les dictionnaires 1.1 et 1.2 (Corsu 0.26.0 et 0.27.0) : la suggestion remplace le
  mot entier. Dans « Dopu ell|a vene », choisir « ellu » donne « Dopu ellu vene ». Le dictionnaire demande à Keyman
  d'effacer la fin du mot, ce que Keyman pour Android fait. Observé dans le moteur de Keyman 18.0.254 et 19.0.309 (bêta)
  et dans l'application Keyman 18.0.254 sur un émulateur Android 14, pas sur un téléphone. Une limite de Keyman reste :
  l'annulation que Keyman propose juste après (effacer, puis toucher le mot entre guillemets) ne rend pas la fin de
  l'ancien mot.
- **Ponctuation déjà écrite après le mot** : avec le dictionnaire 1.2 (à partir de Corsu 0.27.0), le mot choisi reste
  collé à elle, curseur à la fin du mot ou au milieu : `Aiacc|.` ou `Aiacc|iu.` puis « Aiacciu » donne « Aiacciu. », et
  `Sar|i-Solenzara` puis « Sari » garde le trait d'union. Avec le dictionnaire 1.1, Keyman ajoutait une espace devant le
  signe (« Aiacciu . »). Observé dans le moteur de Keyman 18.0.254 et 19.0.309, pas sur un téléphone.
- **Curseur au milieu du mot**, avec l'ancien dictionnaire 1.0 (`platykalt.co.corsu`, avant Corsu 0.26.0) : la
  suggestion ne remplace que la partie à gauche du curseur, et la fin de l'ancien mot reste à sa droite :
  « Dopu ellu a vene », où ce « a » est la fin de « ella », à effacer à la main ; de même, `ca|sa` puis « casa »
  donne « casa sa ». [Mettez-le à jour](#mettre-à-jour).
- **Après avoir ajouté ou effacé une lettre au milieu du mot**, c'est le même cas : les suggestions suivent la partie
  à gauche du curseur, et la règle ci-dessus s'applique.
- **Ponctuation tapée après une suggestion touchée** : Keyman ajoute une espace après le mot touché, et Keyman 18 la
  garde si l'on tape ensuite `.` ou `,` (« casa . »). Touchez une fois la touche d'effacement (elle n'enlève que
  l'espace), puis tapez le signe : « casa. ». Keyman 19 (bêta) enlève lui-même cette espace. C'est la façon dont
  Keyman traite les touches ; le dictionnaire n'y peut rien.
- **Formes régionales** : quand le bandeau propose les deux formes (zitellu, ziteddu), touchez celle que vous voulez ;
  pour changer un mot déjà écrit, placez le curseur à sa fin (ou au milieu) et touchez l'autre forme : le mot entier
  est remplacé.
- **Apostrophes** : les mots élidés sont proposés en entier (`l'is` donne « l'isula », `ch'el` donne « ch'ella »). Si
  le texte emploie l'apostrophe typographique `’`, le dictionnaire 1.2 la garde dans le mot qu'il écrit
  (« l’isula »).
- **Mot sélectionné** : tapez les premières lettres du mot voulu (elles remplacent la sélection), puis choisissez la
  suggestion. Toucher une suggestion sans rien taper remplace la sélection par une suggestion de début de phrase, avec
  majuscule (« Eccu a Di di Petru. ») : comportement du moteur de Keyman, observé dans son moteur seulement.

## Si ça ne marche pas

- **Le fichier ne s'ouvre pas.** Passez par Keyman (étape 4) plutôt que par le fichier lui-même. Vérifiez que le
  téléchargement est terminé et que le fichier s'appelle bien `corsu-keyboard.kmp` ; sinon téléchargez-le à nouveau.
  Si l'accès aux fichiers a été refusé, voir
  [Grant Storage Permission](https://help.keyman.com/products/android/18.0/troubleshooting/grant-storage-permission).
- **Le corse n'apparaît pas.** Dans **Langues installées**, Corsican doit être listé avec EuroLatin (SIL). Si
  EuroLatin a été installé pour une autre langue seulement, refaites l'étape 2 en cherchant `Corsican`.
- **Pas de suggestions.** Le clavier actif doit être EuroLatin (SIL) pour Corsican (pas pour le français) ; sur
  l'écran Corsican, le choix ne doit pas être *Disable suggestions* et un dictionnaire Corsu doit être indiqué.
- **Rien n'a changé après une mise à jour, ou après un changement de dictionnaire.** Relancez Keyman (voir
  [Mettre à jour](#mettre-à-jour)). Si le fichier avait un suffixe `(1)`, renommez-le et installez-le à nouveau.
- **Les majuscules disparaissent.** Voir [Majuscules et début de phrase](#majuscules-et-début-de-phrase).
- **La correction automatique ne s'applique pas.** Voir [Correction automatique](#correction-automatique).
- **Revenir au clavier habituel.** Touchez l'icône de clavier en bas à droite de l'écran et choisissez votre clavier
  habituel. Sur le clavier Keyman, la touche globe le fait aussi : avec un seul clavier Keyman installé, un appui
  court revient au clavier système précédent ; un appui long ouvre la liste des langues, avec en bas les **Autres
  méthodes de saisie** ([Switching Between Keyboards](https://help.keyman.com/products/android/18.0/basic/switching-between-keyboards)).
  Pour retirer le dictionnaire :
  [Removing Dictionaries](https://help.keyman.com/products/android/18.0/basic/uninstalling-dictionaries).

## D'où viennent ces informations

Les étapes suivent l'aide officielle de Keyman 18.0 et les fichiers de cette version (liste ci-dessous). Les
comportements décrits (dictionnaire actif, mise à jour, majuscules, retour sur un mot) ont été observés avec le
moteur de Keyman 18.0.254 et l'application Keyman 18.0.254 sur un émulateur Android 14, pas sur un téléphone réel.

## Pages de l'aide Keyman utilisées

- [Installing Custom Keyboards/Dictionaries](https://help.keyman.com/products/android/18.0/basic/installing-custom-packages)
- [How To - Download and Install a Keyman Keyboard](https://help.keyman.com/products/android/18.0/start/installing-keyboards)
- [Adding Dictionaries](https://help.keyman.com/products/android/18.0/basic/installing-dictionaries)
- [Using the Settings Screen](https://help.keyman.com/products/android/18.0/basic/config/)
- [Enabling Keyman as a System-Wide Keyboard](https://help.keyman.com/products/android/18.0/start/enabling-system-keyboard)
- [Install Keyboard or Dictionary](https://help.keyman.com/products/android/18.0/basic/config/install-keyboard-or-dictionary)
- [Removing Dictionaries](https://help.keyman.com/products/android/18.0/basic/uninstalling-dictionaries)
- [Switching Between Keyboards](https://help.keyman.com/products/android/18.0/basic/switching-between-keyboards)
- [Using the Banner on the Keyboard](https://help.keyman.com/products/android/18.0/basic/using-the-banner)
- La **Version du dictionnaire** affichée est celle du paquet : voir le code de Keyman 18.0
  ([écran du dictionnaire](https://github.com/keymanapp/keyman/blob/stable-18.0/android/KMEA/app/src/main/java/com/keyman/engine/ModelInfoActivity.java),
  [lecture du paquet](https://github.com/keymanapp/keyman/blob/stable-18.0/android/KMEA/app/src/main/java/com/keyman/engine/packages/LexicalModelPackageProcessor.java)).
- Les libellés français et les trois choix de suggestions viennent des fichiers de Keyman 18.0
  ([traductions](https://github.com/keymanapp/keyman/tree/stable-18.0/android/KMEA/app/src/main/res),
  [écran de langue](https://github.com/keymanapp/keyman/blob/stable-18.0/android/KMEA/app/src/main/res/layout/language_settings_list_layout.xml),
  où la correction automatique est désactivée pour la 18.0).

## Autres claviers

Gboard, le clavier de Google, a aussi une disposition corse avec suggestions de mots : dans les réglages de Gboard,
ouvrez Langues, touchez Ajouter un clavier et choisissez Corse. Le dictionnaire Corsu ne s'y installe pas ; il ne
fonctionne que dans Keyman.

## Applications en corse

Firefox, Firefox Focus, Thunderbird, K-9 Mail, VLC et OpenTracks sont disponibles en corse. VLC a son propre réglage
de langue. Les autres suivent la liste des langues du téléphone, qui ne propose pas le corse. On peut l'ajouter depuis
un ordinateur avec [ADB](https://developer.android.com/tools/adb), après avoir activé le débogage USB du téléphone :

```sh
adb shell settings put system system_locales co-FR,fr-FR
```

Redémarrez le téléphone. Les applications qui ont le corse l'utilisent, et le reste reste en français. Rechoisir sa
langue dans les réglages du téléphone annule le changement.

Sous Android 13 ou plus récent, on peut aussi ne changer qu'une seule application :

```sh
adb shell cmd locale set-app-locales org.mozilla.firefox --locales co-FR
```

## Le système lui-même

Android et One UI (Samsung) ne proposent pas le corse, et seuls Google ou Samsung pourraient l'ajouter. LineageOS,
une version libre d'Android qui fonctionne sur certains téléphones Samsung, est traduit par des bénévoles sur
[Crowdin](https://crowdin.com/project/lineageos). Le sarde, le frioulan et le gallois y sont déjà ; le corse pourrait
y être ajouté de la même façon. Google a ajouté le galicien et le basque à Android après une demande du gouvernement
galicien.
