# Essai du dictionnaire Keyman en 5 minutes

Pour la personne qui publie Corsu : après une version, vérifier sur un vrai téléphone que `corsu-keyboard.kmp`
s'installe et fonctionne. Un essai sur Android ou sur iPhone ; noter la plateforme, la version d'Android ou d'iOS et
la version de Keyman (menu › Paramètres, ou « À propos »). Le résultat ne vaut que pour ce téléphone et cette version.

## Avant de commencer

- Keyman est installé, avec EuroLatin (SIL) pour **Corsican** (étapes 1 et 2 du guide
  [Android](android.md) ou [iPhone](iphone.md)).
- Si une version précédente du dictionnaire est installée, la retirer d'abord (Langues installées › Corsican ›
  le dictionnaire › désinstaller), pour essayer le fichier publié et pas l'ancien.
- Une application où écrire : Notes, Messages ou un champ de texte du navigateur.

## Déroulé

| # | Action | Résultat attendu | OK ? |
| --- | --- | --- | --- |
| 1 | Sur le téléphone, ouvrir https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp | Le fichier se télécharge ; sa taille est proche de celle affichée sur la page de la version | |
| 2 | L'importer dans Keyman (Android : Paramètres › Installer un clavier ou un dictionnaire › Installer depuis un fichier local ; iPhone : Ouvrir dans « Keyman ») | L'écran du paquet montre « Corsu », la version du paquet et la langue Corsican ; Installer aboutit sans erreur | |
| 3 | Langues installées › Corsican | Le dictionnaire est listé (Corsu ou `platykalt.co.corsu`) ; suggestions réglées sur *Predictions with corrections* (Android) ou prédictions et corrections activées (iPhone) | |
| 4 | Dans l'application d'essai, choisir Keyman, EuroLatin (SIL) en corse ; taper `bonghj` | Le bandeau propose « bonghjornu » | |
| 5 | Toucher « bonghjornu » | Le mot est écrit en entier, suivi d'une espace | |
| 6 | Taper `grazzie` (faute voulue) | Le bandeau propose « grazie » | |
| 7 | Taper une espace sans toucher le bandeau | Keyman 18.0 laisse « grazzie » tel quel (pas de correction automatique dans cette version) ; noter si une version plus récente de Keyman le corrige seule | |
| 8 | **Casse** : taper `Ecc` (majuscule à la main) | Le bandeau propose « Eccu » avec sa majuscule. Avec la version 0.24.0 du dictionnaire, il peut proposer « eccu » en minuscules : problème connu, correction préparée | |
| 9 | Toucher la suggestion | « Eccu » garde sa majuscule (même remarque pour 0.24.0) | |
| 10 | **Début de phrase** : après « bonghjornu. » et une espace, taper `ecc` (laisser le clavier mettre la majuscule s'il le fait) | La première lettre est en majuscule et la suggestion choisie la garde : « Eccu » | |
| 11 | **Retour sur un mot** : placer le curseur à la fin de « grazzie » (taper dessus), puis effacer la dernière lettre | Le bandeau repropose des mots pour ce mot (« grazie ») ; en toucher un remplace bien le mot entier, pas seulement la fin | |
| 12 | Revenir au clavier habituel (Android : icône de clavier ; iPhone : touche globe), puis de nouveau à Keyman | Les deux claviers alternent ; Keyman retrouve les suggestions corses | |

Compter un peu moins d'une minute pour 1 à 3 si Keyman est déjà prêt, et le reste en trois ou quatre minutes.

## Noter le résultat

Plateforme et version du système, version de Keyman, version de Corsu (le nom de la version publiée), puis le
numéro des lignes qui échouent avec ce qui s'est affiché. Pas de capture d'écran avec des messages personnels.
