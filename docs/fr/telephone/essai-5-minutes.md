# Essai du dictionnaire Keyman en 5 minutes

Pour la personne qui publie Corsu : vérifier sur un vrai téléphone que le dictionnaire Corsu publié s'installe et
fonctionne. Un essai sur Android ou sur iPhone ; noter la plateforme, la version d'Android ou d'iOS et la version de
Keyman (menu › Paramètres, ou « À propos »). Le résultat ne vaut que pour ce téléphone et cette version.

Les résultats attendus ont été observés avec le moteur de Keyman 18.0.254 et l'application Keyman 18.0.254 sur un
émulateur Android 14, pas encore sur un téléphone réel ni sur un iPhone.

## Quel fichier essayer

<!-- Fichier publié avec Corsu 0.26.0 (paquet 1.1) ; pas de candidat plus récent. Si un
     candidat revient, lui donner sa propre colonne avec le lien de son exécution et sa date d'expiration. -->
| | Dictionnaire publié |
| --- | --- |
| Où le prendre | [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) ([empreinte SHA-256](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp.sha256)) |
| Fichier | `corsu-keyboard.kmp` |
| Nom dans Keyman | Corsu |
| Version du dictionnaire | 1.1 (publié avec Corsu 0.26.0) |
| Pas à pas | « Installer » dans le guide [Android](android.md#installer) ou [iPhone](iphone.md#installer) |

Le fichier doit garder exactement le nom `corsu-keyboard.kmp` (sinon le renommer : Keyman tire l'identité du paquet
du nom du fichier).

## Avant de commencer

- Keyman est installé, avec EuroLatin (SIL) pour **Corsican** (étapes 1 et 2 du guide
  [Android](android.md) ou [iPhone](iphone.md)).
- Si un dictionnaire Corsu est déjà installé, le retirer d'abord (Langues installées › Corsican › le dictionnaire ›
  désinstaller), puis relancer Keyman, pour essayer le fichier publié et pas l'ancien.
- Une application où écrire : Notes, Messages ou un champ de texte du navigateur.

## Déroulé

| # | Action | Attendu (paquet 1.1) | OK ? |
| --- | --- | --- | --- |
| 1 | Télécharger le fichier (tableau ci-dessus) | `corsu-keyboard.kmp`, sous ce nom exact | |
| 2 | L'importer dans Keyman (Android : Paramètres › Installer un clavier ou un dictionnaire › Installer depuis un fichier local ; iPhone : Ouvrir dans « Keyman », ou Paramètres › Installer depuis un fichier › Parcourir) | L'écran du paquet montre « Corsu », la version 1.1 et la langue Corsican ; Installer aboutit sans erreur | |
| 3 | Relancer Keyman, puis Langues installées › Corsican ; ouvrir le dictionnaire (Android : Dictionnaire › le dictionnaire coché ; iPhone : le dictionnaire › icône i) | Nom « Corsu » (et non `platykalt.co.corsu`, le paquet 1.0), **Version du dictionnaire** 1.1 ; suggestions sur *Predictions with corrections* (Android) ou prédictions et corrections activées (iPhone) | |
| 4 | Dans l'application d'essai, choisir Keyman, EuroLatin (SIL) en corse ; taper `bonghj` | Le bandeau propose « bonghjornu » | |
| 5 | Toucher « bonghjornu » | Le mot est écrit en entier, suivi d'une espace | |
| 6 | Taper `grazzie` (faute voulue) | Le bandeau propose « grazie » | |
| 7 | Taper une espace sans toucher le bandeau | « grazzie » reste tel quel : Keyman 18.0 n'a pas de correction automatique (limite connue de Keyman, pas du dictionnaire) | |
| 8 | **Casse** : au milieu d'une phrase, taper `Ecc` (Maj à la main) | Le bandeau propose « Eccu » avec sa majuscule | |
| 9 | Toucher la suggestion | « Eccu » garde sa majuscule | |
| 10 | **Début de phrase** : après « bonghjornu. » et une espace, taper `ecc` sans toucher Maj | Le clavier EuroLatin met de lui-même la majuscule (« Ecc ») et les suggestions sont en majuscule : « Eccu » | |
| 11 | Toujours en début de phrase : retour à la ligne sans ponctuation, puis `ecc` | Pas de majuscule automatique : comportement du clavier EuroLatin, limite connue (de même après `."`) | |
| 12 | **Retour sur un mot** : écrire « Dopu ella vene », placer le curseur entre `ell` et `a`, choisir « ellu » dans le bandeau. Puis placer le curseur à la fin d'un mot et choisir une suggestion | Android : « Dopu ellu vene », le mot entier est remplacé. iPhone : « Dopu ellu a vene », le « a » est la fin de « ella » restée à droite du curseur (limite de Keyman pour iPhone). À la fin d'un mot : la suggestion remplace le mot entier, sur les deux | |
| 13 | Revenir au clavier habituel (Android : icône de clavier, ou appui court sur la touche globe ; iPhone : touche globe), puis de nouveau à Keyman | Les deux claviers alternent ; Keyman retrouve les suggestions corses | |

Compter un peu moins d'une minute pour 1 à 3 si Keyman est déjà prêt, et le reste en trois ou quatre minutes.

**Échec ou limite ?** Les lignes 7, 11 et 12 sur iPhone décrivent des limites connues de Keyman ou du clavier
EuroLatin : un résultat conforme est « OK ». Un échec, c'est un résultat différent de la colonne « Attendu ». Si rien
ne change après une mise à jour, relancer Keyman (changer de clavier puis revenir, ou forcer l'arrêt de
l'application) avant de conclure ; si Keyman montre encore `platykalt.co.corsu` ou la version 1.0, c'est l'ancien
paquet qui répond.

## Variantes régionales

Publiées avec Corsu 0.26.0, version 1.1 :
[corsu-keyboard-cismuntincu.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-cismuntincu.kmp)
et
[corsu-keyboard-pumuntincu.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-pumuntincu.kmp).
En installer une **après** `corsu-keyboard.kmp`. Sur Android, attendu : les deux apparaissent dans la liste, mais
l'ancien reste actif. Le désinstaller (Corsican › Dictionnaire › le dictionnaire › Désinstaller le dictionnaire),
relancer Keyman : la variante devient active, avec son nom « Corsu – Cismuntincu (experimental) » ou « Corsu –
Pumuntincu (experimental) ».

## Noter le résultat

Plateforme et version du système, version de Keyman, fichier essayé (et version de Corsu qui l'a publié) et version
du dictionnaire affichée par Keyman, puis le numéro des lignes qui
échouent avec ce qui s'est affiché. Pas de capture d'écran avec des messages personnels.
