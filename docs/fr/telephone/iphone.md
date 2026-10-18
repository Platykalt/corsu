# Écrire en corse sur iPhone

[English](../../en/phone/iphone.md) · [Android](android.md)

Deux pièces, toutes deux gratuites :

- **Keyman** fournit le clavier. C'est une application de SIL, installée depuis l'App Store. Sa disposition
  EuroLatin (SIL) a toutes les lettres corses.
- **Corsu** fournit le dictionnaire : pendant que vous écrivez, il propose des mots corses dans le bandeau au-dessus
  du clavier et propose la bonne orthographe d'un mot mal tapé.

L'application Corsu pour ordinateur n'est pas nécessaire. Le dictionnaire n'est ni un traducteur de phrases ni un
correcteur de grammaire complet : il travaille mot par mot.

Ce guide suit Keyman pour iPhone et iPad 18.0 (version stable 18.0.254 au 16 octobre 2026). Les noms des boutons
viennent de l'aide officielle de Keyman et des fichiers de traduction de cette version ; une autre version peut les
changer. Il n'y a pas de captures d'écran.

## Dictionnaires disponibles

| Fichier | Contenu | Téléchargement |
| --- | --- | --- |
| `corsu-keyboard.kmp` | dictionnaire général, environ 17 000 mots corses courants | [dernière version publiée](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) |

<!-- Liste des fichiers réellement joints à la dernière version publiée. Ajouter une ligne seulement quand la version
     publiée contient le fichier. -->
D'autres variantes sont en préparation ; elles apparaîtront dans ce tableau une fois publiées.

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
   [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp).
4. **Importez-le dans Keyman.** Safari propose d'ouvrir le fichier : touchez **Ouvrir dans « Keyman »**. Si le
   fichier est déjà dans Fichiers, cherchez l'option **Ouvrir dans « Keyman »**, ou, dans Keyman, **Paramètres** ›
   **Installer depuis un fichier** (« Parcourir pour des fichiers .kmp »), puis l'option **Parcourir** en bas à
   droite. Keyman montre le paquet « Corsu » : gardez la langue Corsican, touchez **Installer** en haut à droite,
   puis **Done** (Terminé) après la page d'accueil.
5. **Vérifiez le dictionnaire.** **Paramètres** › **Langues installées** › **Corsican** : la partie
   **Dictionnaires** doit lister Corsu (il peut s'afficher sous son identifiant, `platykalt.co.corsu`).
6. **Réglez les suggestions** sur ce même écran, partie **Paramètres de langue** : activez **Activer les
   prédictions**, puis **Activer les corrections** (ce second bouton n'apparaît que lorsque les prédictions sont
   activées). Keyman 18.0 n'a pas de réglage de correction automatique : les corrections sont proposées dans le
   bandeau et s'appliquent quand vous les touchez.
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

## Si ça ne marche pas

- **Le fichier ne s'ouvre pas.** Ouvrez-le depuis Keyman : **Paramètres** › **Installer depuis un fichier**, puis
  **Parcourir**. Vérifiez que le téléchargement est terminé et que le fichier s'appelle bien `corsu-keyboard.kmp`.
- **Le corse n'apparaît pas.** Dans **Langues installées**, Corsican doit être listé avec EuroLatin (SIL). Si
  EuroLatin a été installé pour une autre langue seulement, refaites l'étape 2 en cherchant `Corsican`.
- **Pas de suggestions.** Le clavier actif doit être EuroLatin (SIL) pour Corsican ; sur l'écran Corsican,
  **Activer les prédictions** doit être activé et le dictionnaire listé. Vérifiez aussi l'accès complet (étape 7).
- **Les majuscules disparaissent.** Avec la version publiée du dictionnaire, choisir une suggestion peut remplacer
  un mot commencé par une majuscule par sa forme en minuscules. Le problème est connu ; une correction est préparée
  mais pas encore publiée. En attendant, finissez le mot au clavier ou remettez la majuscule.
  <!-- Texte provisoire : le responsable de version l'ajuste quand la correction est publiée. -->
- **La correction automatique ne s'applique pas.** C'est le fonctionnement de Keyman 18.0 : les corrections sont
  proposées dans le bandeau, à toucher.
- **Revenir au clavier habituel.** Touchez la touche globe jusqu'à votre clavier habituel. Pour retirer Keyman de la
  liste : **Réglages** › **Général** › **Clavier** › **Claviers** › **Modifier**.

## Pages de l'aide Keyman utilisées

- [How To - Adding a Keyboard](https://help.keyman.com/products/iphone-and-ipad/18.0/start/searching-for-keyboards)
- [Installing Custom Keyboards/Dictionaries](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/installing-custom-keyboards-dictionaries)
- [How To - Keyboard and Dictionary Installation](https://help.keyman.com/products/iphone-and-ipad/18.0/start/installing-packages)
- [Language Settings](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/language-settings)
- [How To - Installing Keyman as a System Keyboard](https://help.keyman.com/products/iphone-and-ipad/18.0/start/installing-system-keyboard)
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
