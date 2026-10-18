# Écrire en corse sur iPhone

[English](../../en/phone/iphone.md) · [Android](android.md)

**Aucune installation de Corsu sur un ordinateur n'est nécessaire** : tout se fait sur l'iPhone.

**Télécharger le dictionnaire : [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp)**
(dernière version publiée, à ouvrir dans Keyman : voir [Installer](#installer)). Le fichier est joint aux versions de
Corsu, mais s'utilise seul.

Deux pièces, toutes deux gratuites :

- **Keyman** fournit le clavier. C'est une application de SIL, installée depuis l'App Store. Sa disposition
  EuroLatin (SIL) a toutes les lettres corses.
- **Corsu** fournit le dictionnaire : pendant que vous écrivez, il propose des mots corses dans le bandeau au-dessus
  du clavier et propose la bonne orthographe d'un mot mal tapé.

Le dictionnaire n'est ni un traducteur de phrases ni un correcteur de grammaire complet : il travaille mot par mot.

Ce guide suit Keyman pour iPhone et iPad 18.0 (version stable 18.0.254 au 16 octobre 2026). Les noms des boutons
viennent de l'aide officielle de Keyman et des fichiers de traduction de cette version ; une autre version peut les
changer. Il n'y a pas de captures d'écran.

## Dictionnaires disponibles

<!-- corsu:phone-variants:fr Fichiers réellement joints à la dernière version publiée. À la publication de la
     prochaine version, déplacer ici les lignes du tableau « Dans la prochaine version » qu'elle contient. -->
| Fichier | Nom dans Keyman | Version | Contenu | Téléchargement |
| --- | --- | --- | --- | --- |
| `corsu-keyboard.kmp` | `platykalt.co.corsu` | 1.0 (publié avec Corsu 0.25.1) | dictionnaire général, 19 805 mots tirés du lexique de Corsu ; perd la majuscule des mots et garde quelques mots parasites (mots anglais, noms de produits, fragments), défauts corrigés dans la prochaine version | [dernière version publiée](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) ([empreinte SHA-256](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp.sha256)) |

« Version » est la version du paquet du dictionnaire, que Keyman affiche (voir l'étape 5) ; elle ne suit pas les
numéros de version de Corsu.

### Dans la prochaine version (pas encore publiée)

| Fichier | Nom dans Keyman | Version | Contenu |
| --- | --- | --- | --- |
| `corsu-keyboard.kmp` | Corsu | 1.1 | le vocabulaire commun, environ 13 000 mots (mots parasites retirés), sans préférence régionale ; garde la majuscule des mots |
| `corsu-keyboard-cismuntincu.kmp` | Corsu – Cismuntincu (experimental) | 1.1 | le même vocabulaire, avec une préférence pour les formes du Cismonte ; expérimental, les formes régionales ne couvrent qu'une partie des mots (361 mots pondérés autrement) |
| `corsu-keyboard-pumuntincu.kmp` | Corsu – Pumuntincu (experimental) | 1.1 | le même vocabulaire, avec une préférence pour les formes du Pumonte ; expérimental, même limite |

Les trois sont pour la langue Corsican (`co`) et le clavier EuroLatin (SIL). Un seul suffit : voir
[Choisir un dictionnaire régional](#choisir-un-dictionnaire-régional). Pour les essayer avant leur publication :
[Essayer le dictionnaire de la prochaine version (candidate)](#essayer-le-dictionnaire-de-la-prochaine-version-candidate).

## Installer

1. **Installez Keyman** depuis l'[App Store](https://apps.apple.com/app/keyman/id933676545) (lien aussi sur
   [keyman.com/iphone](https://keyman.com/iphone/)).
2. **Ajoutez le clavier EuroLatin (SIL) pour le corse.** Dans Keyman, ouvrez **Paramètres** › **Langues installées**
   et touchez **+** en haut à droite. Cherchez `Corsican` (la recherche se fait sur le nom anglais de la langue),
   choisissez **EuroLatin (SIL)** et touchez le bouton vert **Install Keyboard**. Si l'installateur propose de choisir
   les langues, gardez **Corsican**, puis touchez **Installer** en haut à droite.
   Le dictionnaire Corsu est rattaché à la langue Corsican (code `co`) : il ne sert que lorsque EuroLatin est
   utilisé pour le corse.
3. **Téléchargez le dictionnaire** dans Safari :
   [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp). Gardez
   exactement ce nom (voir [Mettre à jour](#mettre-à-jour)).
4. **Importez-le dans Keyman.** Safari propose d'ouvrir le fichier : touchez **Ouvrir dans « Keyman »**. Si le
   fichier est déjà dans Fichiers, cherchez l'option **Ouvrir dans « Keyman »**, ou, dans Keyman, **Paramètres** ›
   **Installer depuis un fichier** (« Parcourir pour des fichiers .kmp »), puis l'option **Parcourir** en bas à
   droite. Keyman montre le paquet « Corsu » : gardez la langue Corsican, touchez **Installer** en haut à droite,
   puis **Done** (Terminé) après la page d'accueil.
5. **Vérifiez le dictionnaire.** **Paramètres** › **Langues installées** › **Corsican** : la partie
   **Dictionnaires** liste le dictionnaire, `platykalt.co.corsu` pour le paquet publié aujourd'hui (« Corsu » pour
   celui de la prochaine version). Pour voir sa version, touchez-le, puis l'icône bleue **i** à côté de son nom :
   l'écran montre la **Version du dictionnaire**, à comparer avec le tableau
   [Dictionnaires disponibles](#dictionnaires-disponibles). Revenez en arrière sans toucher **Désinstaller ce
   dictionnaire**.
6. **Réglez les suggestions** sur ce même écran, partie **Paramètres de langue** : activez **Activer les
   prédictions**, puis **Activer les corrections** (ce second bouton n'apparaît que lorsque les prédictions sont
   activées). Il n'y a pas de correction automatique dans cette version : voir
   [Correction automatique](#correction-automatique).
7. **Ajoutez Keyman aux claviers de l'iPhone.** Ouvrez **Réglages** › **Général** › **Clavier** › **Claviers** ›
   **Ajouter un clavier…**, touchez **Keyman** sous « Claviers de tiers », puis **Keyman - Keyman** et activez
   **Autoriser l'accès complet**.
   *Pourquoi l'accès complet ?* L'aide de Keyman indique qu'à cause d'un problème d'iOS 16, ce réglage doit rester
   activé pour que le clavier Keyman s'affiche normalement ; avant iOS 16, il ne servait qu'à changer certaines
   préférences. Il ne s'agit pas d'un besoin propre au dictionnaire Corsu. iOS affiche à ce moment son avertissement
   habituel sur les claviers de tiers.
   Ensuite, en écrivant, la touche globe passe d'un clavier à l'autre.
8. **Essayez.** Dans Notes ou Messages, choisissez Keyman avec la touche globe, puis tapez `bonghj` : le bandeau devrait
   proposer « bonghjornu ». Tapez `grazzie` : il devrait proposer « grazie » ; touchez-le pour corriger.

## Mettre à jour

Téléchargez le nouveau fichier et ouvrez-le dans Keyman comme à l'étape 4, **sous le même nom**
`corsu-keyboard.kmp` : Keyman tire l'identité du paquet du nom du fichier. Si un suffixe a été ajouté
(`corsu-keyboard(1).kmp`, `corsu-keyboard (1).kmp`), renommez le fichier dans Fichiers avant de l'ouvrir. Vos
réglages sont gardés. **Relancez ensuite Keyman** : jusque-là, l'ancien dictionnaire peut continuer de répondre.
Passez à un autre clavier avec la touche globe puis revenez à Keyman, ou fermez l'application Keyman. Vérifiez
ensuite la version comme à l'étape 5.

## Essayer le dictionnaire de la prochaine version (candidate)

Le dictionnaire de la prochaine version de Corsu (paquet **version 1.1**, nommé **« Corsu »** dans Keyman) n'est pas
encore publié. On peut l'essayer avant : la chaîne de construction du projet (GitHub Actions) le produit à chaque
modification. Ce n'est pas une version publiée : il peut encore changer, et rien n'a été essayé sur un iPhone (les
étapes suivent l'aide de Keyman 18.0).

1. **Connectez-vous à GitHub** dans Safari (un compte gratuit suffit) : GitHub ne donne ces fichiers qu'aux comptes
   connectés (sans connexion, le lien affiche une page « 404 »).
2. **Téléchargez l'archive** [keyboard-packages](https://github.com/Platykalt/corsu/actions/runs/39161059937/artifacts/12149352996) (commit `146d2cf` de `next-0.26`) (le téléchargement commence en ouvrant le lien). Elle
   arrive dans **Fichiers** › **Téléchargements** sous le nom `keyboard-packages.zip`. GitHub l'efface au bout de
   90 jours (le 16 janvier 2027) ; un lien plus récent sera alors donné ici.
3. **Extrayez-la** : dans l'app **Fichiers**, touchez `keyboard-packages.zip` ; iOS crée un dossier
   `keyboard-packages` à côté. Il contient `corsu-keyboard.kmp`, `corsu-keyboard-cismuntincu.kmp`,
   `corsu-keyboard-pumuntincu.kmp` et leurs empreintes `.sha256`. Pour le dictionnaire général, prenez
   **`corsu-keyboard.kmp`**, sans le renommer.
4. **Retirez d'abord le dictionnaire installé** : **Paramètres** › **Langues installées** › **Corsican** ›
   **Dictionnaires** › le dictionnaire › icône **i** › **Désinstaller ce dictionnaire**. Relancez Keyman (voir
   [Mettre à jour](#mettre-à-jour)).
5. **Installez** le `corsu-keyboard.kmp` du dossier : dans Keyman, **Paramètres** › **Installer depuis un fichier** ›
   **Parcourir**, puis choisissez-le dans le dossier `keyboard-packages`. L'écran du paquet doit montrer « Corsu » et
   la version 1.1 ; touchez **Installer**, puis **Terminé**.
6. **Relancez Keyman, puis vérifiez** comme à l'étape 5 : **Dictionnaires** liste « Corsu » (et non
   `platykalt.co.corsu`), et la **Version du dictionnaire** est 1.1. Au milieu d'une phrase, tapez `Ecc` : le bandeau
   doit proposer « Eccu » avec sa majuscule (le dictionnaire publié propose « eccu »).

**Revenir au dictionnaire publié** : désinstallez « Corsu » de la même façon (étape 4 ci-dessus), relancez Keyman,
puis installez `corsu-keyboard.kmp` téléchargé depuis le [lien publié](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp)
(étapes 3 et 4 de [Installer](#installer)). Après une nouvelle relance, **Dictionnaires** liste de nouveau
`platykalt.co.corsu`, version 1.0.

Pour une liste d'essai complète, avec les résultats attendus : [Essai en 5 minutes](essai-5-minutes.md).

## Choisir un dictionnaire régional

<!-- corsu:phone-variants:fr Les variantes régionales arrivent avec la prochaine version. -->
Avec la prochaine version, deux dictionnaires expérimentaux préféreront les formes du Cismonte ou du Pumonte. Sur
iPhone, d'après le code de Keyman 18.0 (pas essayé sur un iPhone), on choisit le dictionnaire dans **Paramètres** ›
**Langues installées** › **Corsican**, partie **Dictionnaires**, et le choix est gardé pour la langue. Relancez
ensuite Keyman comme pour une mise à jour, puis vérifiez le nom affiché (étape 5).

Avant leur publication, les deux variantes sont dans la même archive que le dictionnaire candidat : voir
[Essayer le dictionnaire de la prochaine version](#essayer-le-dictionnaire-de-la-prochaine-version-candidate).

## Majuscules et début de phrase

- **La majuscule en début de phrase vient du clavier EuroLatin, pas du dictionnaire.** Elle s'active au début d'un
  champ et après `.`, `?` ou `!` suivis d'une espace. Elle ne s'active pas après un retour à la ligne sans
  ponctuation, ni après `."` ; elle s'active à tort après `M. `. Il n'y a pas de réglage pour la couper : touchez la
  touche Maj pour l'annuler.
- **Les suggestions perdent la majuscule** avec le dictionnaire de la version publiée : `Ecc` peut devenir « eccu ».
  C'est corrigé dans les paquets de la prochaine version, qui gardent la casse tapée (« Eccu ») et mettent la
  majuscule aux suggestions en début de phrase. En attendant, finissez le mot au clavier ou remettez la majuscule.
  <!-- corsu:phone-casing À la publication : dire que c'est corrigé dans la version publiée. -->

## Correction automatique

Keyman 18.0, la version stable, **n'a pas de correction automatique** : les corrections sont proposées dans le bandeau
et ne s'appliquent que si vous les touchez. Le dictionnaire Corsu ne commande pas ce réglage. Keyman 19, encore en
version bêta, ajoute **Apply corrections automatically** ; il apparaîtra sur l'écran Corsican quand Keyman 19 sera la
version stable. Il restera facultatif. Dans nos essais du moteur de la bêta 19.0.309 (hors de l'application), un mot
présent dans le dictionnaire est toujours gardé tel qu'il est tapé, mais un mot absent peut être remplacé : un nom par
un nom proche (« Bastelicaccia » par « Bastilicaccia » quand seule la seconde graphie est dans le dictionnaire), ou un
mot en minuscules par le nom qui s'écrit pareil (« corti » par « Corti » quand « corti » y manque). La prochaine version du dictionnaire contient ces formes (« Bastelicaccia », « corti » à côté de « Corti », « Vizzani », des sigles comme « ADECEC ») ; un mot qui y manque encore, un nom de rue par exemple, peut toujours être remplacé.

## Revenir sur un mot

Déplacer le curseur ne change rien au texte. Les suggestions suivent la partie du mot **à gauche du curseur**, et une
suggestion choisie ne remplace que cette partie : la fin de l'ancien mot reste à droite du curseur. Dans
« Dopu ell|a vene », choisir « ellu » donne « Dopu ellu a vene » : ce « a » n'est pas un mot ajouté, c'est la fin de
« ella », qu'il faut effacer à la main. De même, `ca|sa` puis « casa » donne « casa sa ».

Sur iPhone, c'est vrai aussi avec le dictionnaire de la prochaine version : il demande à Keyman d'effacer la fin du
mot (ce que fait Keyman pour Android), mais Keyman pour iPhone ignore cette demande, en 18.0 comme dans la bêta 19.0
(d'après son code ; pas essayé sur un iPhone). Les gestes sûrs :

- placez le curseur **à la fin du mot** avant de choisir une suggestion : elle remplace alors le mot entier ;
- ou sélectionnez le mot, tapez ses premières lettres (elles remplacent la sélection), puis choisissez la suggestion ;
- ou effacez le mot et retapez-le.

## Si ça ne marche pas

- **Le fichier ne s'ouvre pas.** Ouvrez-le depuis Keyman : **Paramètres** › **Installer depuis un fichier**, puis
  **Parcourir**. Vérifiez que le téléchargement est terminé et que le fichier s'appelle bien `corsu-keyboard.kmp`.
- **Le corse n'apparaît pas.** Dans **Langues installées**, Corsican doit être listé avec EuroLatin (SIL). Si
  EuroLatin a été installé pour une autre langue seulement, refaites l'étape 2 en cherchant `Corsican`.
- **Pas de suggestions.** Le clavier actif doit être EuroLatin (SIL) pour Corsican ; sur l'écran Corsican,
  **Activer les prédictions** doit être activé et le dictionnaire listé. Vérifiez aussi l'accès complet (étape 7).
- **Rien n'a changé après une mise à jour.** Relancez Keyman (voir [Mettre à jour](#mettre-à-jour)). Si le fichier
  avait un suffixe `(1)`, renommez-le et ouvrez-le à nouveau dans Keyman.
- **Les majuscules disparaissent.** Voir [Majuscules et début de phrase](#majuscules-et-début-de-phrase).
- **La correction automatique ne s'applique pas.** Voir [Correction automatique](#correction-automatique).
- **Revenir au clavier habituel.** Un appui court sur la touche globe passe au clavier suivant ; un appui long ouvre
  le menu de Keyman, où **Fermer Keyman** passe au clavier suivant qui n'est pas Keyman
  ([Switching between keyboards](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/switching-between-keyboards)). Pour retirer Keyman de la
  liste : **Réglages** › **Général** › **Clavier** › **Claviers** › **Modifier**.

## D'où viennent ces informations

Les étapes suivent l'aide officielle de Keyman 18.0 et les fichiers de cette version (liste ci-dessous). Les
comportements décrits (mise à jour, majuscules, retour sur un mot) ont été observés avec le moteur de Keyman
18.0.254, commun à Android et à iOS, et avec l'application Android ; rien n'a été essayé sur un iPhone.

## Pages de l'aide Keyman utilisées

- [How To - Adding a Keyboard](https://help.keyman.com/products/iphone-and-ipad/18.0/start/searching-for-keyboards)
- [Installing Custom Keyboards/Dictionaries](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/installing-custom-keyboards-dictionaries)
- [How To - Keyboard and Dictionary Installation](https://help.keyman.com/products/iphone-and-ipad/18.0/start/installing-packages)
- [Language Settings](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/language-settings)
- [How To - Installing Keyman as a System Keyboard](https://help.keyman.com/products/iphone-and-ipad/18.0/start/installing-system-keyboard)
- [Switching between keyboards](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/switching-between-keyboards)
- [Using the Settings Screen](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/config/)
- Les libellés français viennent des fichiers de traduction de Keyman 18.0
  ([moteur](https://github.com/keymanapp/keyman/blob/stable-18.0/ios/engine/KMEI/KeymanEngine/fr.lproj/Localizable.strings),
  [application](https://github.com/keymanapp/keyman/blob/stable-18.0/ios/keyman/Keyman/Keyman/fr.lproj/Localizable.strings)).

## Applications en corse

iOS ne propose pas le corse comme langue du système ; seul Apple pourrait l'ajouter. Les applications qui ont le
corse peuvent quand même l'utiliser.

1. Ouvrez Réglages, puis Général, puis Langue et région, et touchez Ajouter une langue.
2. Choisissez Corse (Corsu). En le plaçant en deuxième position, le reste du téléphone garde votre langue actuelle.
3. Les applications qui ont le corse, Firefox et Firefox Focus par exemple, l'affichent maintenant. On peut aussi
   changer la langue d'une seule application dans Réglages, puis le nom de l'application, puis Langue.

Apple a ajouté le slovène en 2024, quelques mois après une loi slovène qui l'exigeait et une campagne publique. Aucune
demande de ce genre n'a encore été faite pour le corse.
