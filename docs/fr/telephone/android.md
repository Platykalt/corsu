# Écrire en corse sur Android

[English](../../en/phone/android.md) · [iPhone](iphone.md)

Deux pièces, toutes deux gratuites :

- **Keyman** fournit le clavier. C'est une application de SIL, installée depuis le Play Store. Sa disposition
  EuroLatin (SIL) a toutes les lettres corses.
- **Corsu** fournit le dictionnaire : pendant que vous écrivez, il propose des mots corses dans le bandeau au-dessus
  du clavier et propose la bonne orthographe d'un mot mal tapé.

L'application Corsu pour ordinateur n'est pas nécessaire. Le dictionnaire n'est ni un traducteur de phrases ni un
correcteur de grammaire complet : il travaille mot par mot.

Ce guide suit Keyman pour Android 18.0 (version stable 18.0.254 au 16 octobre 2026). Les noms des boutons viennent de
l'aide officielle de Keyman et des fichiers de traduction de cette version ; une autre version peut les changer. Il
n'y a pas de captures d'écran.

## Dictionnaires disponibles

| Fichier | Contenu | Téléchargement |
| --- | --- | --- |
| `corsu-keyboard.kmp` | dictionnaire général, environ 17 000 mots corses courants | [dernière version publiée](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) |

<!-- Liste des fichiers réellement joints à la dernière version publiée. Ajouter une ligne seulement quand la version
     publiée contient le fichier. -->
D'autres variantes sont en préparation ; elles apparaîtront dans ce tableau une fois publiées.

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
   arrive en général dans le dossier Téléchargements (Download).
4. **Importez-le dans Keyman.** Menu › **Paramètres** › **Installer un clavier ou un dictionnaire** › **Installer
   depuis un fichier local**, puis choisissez `corsu-keyboard.kmp` dans Téléchargements. Si Android demande
   l'accès aux fichiers, autorisez-le (Keyman le demande une seule fois). Keyman montre le paquet « Corsu » et sa
   version : touchez **Installer**, puis **OK** après la page d'accueil.
5. **Choisissez le dictionnaire.** **Paramètres** › **Langues installées** › **Corsican** : en bas de l'écran,
   **Dictionnaire** doit indiquer Corsu (il peut s'afficher sous son identifiant, `platykalt.co.corsu`). Sinon,
   touchez-le et choisissez-le (le dictionnaire installé a une coche).
6. **Réglez les suggestions** sur ce même écran. Keyman 18.0 propose trois choix, affichés en anglais même quand
   Keyman est en français : *Disable suggestions* (aucune), *Predictions only* (mots proposés, sans correction) et
   *Predictions with corrections* (mots proposés et fautes corrigées). Choisissez **Predictions with corrections**.
   Keyman 18.0 pour Android n'a pas de correction automatique : la correction s'affiche dans le bandeau et
   s'applique quand vous la touchez.
7. **Faites de Keyman le clavier du téléphone.** Menu › **Paramètres** › **Activer Keyman comme clavier système**
   (on le trouve aussi dans **Commencer**). L'écran des claviers d'Android s'ouvre : activez **Keyman**, puis
   répondez **OK** aux deux messages de confirmation. Android y rappelle qu'un clavier peut lire ce qu'on tape ; c'est
   l'avertissement de tout clavier ajouté. Ensuite, quand un clavier est affiché, l'icône de clavier en bas à droite
   de l'écran permet de choisir Keyman.
8. **Essayez.** Dans une application de notes ou de messages, choisissez Keyman, puis tapez `bonghj` : le bandeau devrait
   proposer « bonghjornu ». Tapez `grazzie` : il devrait proposer « grazie » ; touchez-le pour corriger.

## Si ça ne marche pas

- **Le fichier ne s'ouvre pas.** Passez par Keyman (étape 4) plutôt que par le fichier lui-même. Vérifiez que le
  téléchargement est terminé et que le fichier s'appelle bien `corsu-keyboard.kmp` ; sinon téléchargez-le à nouveau.
  Si l'accès aux fichiers a été refusé, voir
  [Grant Storage Permission](https://help.keyman.com/products/android/18.0/troubleshooting/grant-storage-permission).
- **Le corse n'apparaît pas.** Dans **Langues installées**, Corsican doit être listé avec EuroLatin (SIL). Si
  EuroLatin a été installé pour une autre langue seulement, refaites l'étape 2 en cherchant `Corsican`.
- **Pas de suggestions.** Le clavier actif doit être EuroLatin (SIL) pour Corsican (pas pour le français) ; sur
  l'écran Corsican, le choix ne doit pas être *Disable suggestions* et le dictionnaire doit être Corsu.
- **Les majuscules disparaissent.** Avec la version publiée du dictionnaire, choisir une suggestion peut remplacer
  un mot commencé par une majuscule par sa forme en minuscules. Le problème est connu ; une
  correction est préparée mais pas encore publiée. En attendant, finissez le mot au clavier ou remettez la majuscule.
  <!-- Texte provisoire : le responsable de version l'ajuste quand la correction est publiée. -->
- **La correction automatique ne s'applique pas.** C'est le fonctionnement de Keyman 18.0 pour Android : les
  corrections sont proposées dans le bandeau, à toucher.
- **Revenir au clavier habituel.** Touchez l'icône de clavier en bas à droite de l'écran (ou, sur le clavier Keyman,
  la touche globe) et choisissez votre clavier habituel. Pour retirer le dictionnaire :
  [Removing Dictionaries](https://help.keyman.com/products/android/18.0/basic/uninstalling-dictionaries).

## Pages de l'aide Keyman utilisées

- [Installing Custom Keyboards/Dictionaries](https://help.keyman.com/products/android/18.0/basic/installing-custom-packages)
- [How To - Download and Install a Keyman Keyboard](https://help.keyman.com/products/android/18.0/start/installing-keyboards)
- [Adding Dictionaries](https://help.keyman.com/products/android/18.0/basic/installing-dictionaries)
- [Using the Settings Screen](https://help.keyman.com/products/android/18.0/basic/config/)
- [Enabling Keyman as a System-Wide Keyboard](https://help.keyman.com/products/android/18.0/start/enabling-system-keyboard)
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
