# Essai du dictionnaire Keyman en 5 minutes

Pour la personne qui publie Corsu : vérifier sur un vrai téléphone qu'un dictionnaire Corsu s'installe et
fonctionne, **avant** une version (le dictionnaire candidat) ou **après** (le fichier publié). Un essai sur Android
ou sur iPhone ; noter la plateforme, la version d'Android ou d'iOS et la version de Keyman (menu › Paramètres, ou
« À propos »). Le résultat ne vaut que pour ce téléphone et cette version.

Les résultats attendus ont été observés avec le moteur de Keyman 18.0.254 et l'application Keyman 18.0.254 sur un
émulateur Android 14, pas encore sur un téléphone réel ni sur un iPhone.

## Quel fichier essayer

| | Candidat (prochaine version) | Publié (dernière version) |
| --- | --- | --- |
| Où le prendre | archive [keyboard-packages](https://github.com/Platykalt/corsu/actions/runs/39161059937/artifacts/12149352996) (commit `146d2cf` de `next-0.26`) produite par GitHub Actions (compte GitHub connecté ; `.zip` à extraire ; effacée le 16 janvier 2027) | [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) |
| Fichier | `corsu-keyboard.kmp` du dossier extrait | `corsu-keyboard.kmp` |
| Nom dans Keyman | Corsu | `platykalt.co.corsu` |
| Version du dictionnaire | 1.1 | 1.0 (Corsu 0.25.1) |
| Pas à pas | « Essayer le dictionnaire de la prochaine version » dans le guide [Android](android.md#essayer-le-dictionnaire-de-la-prochaine-version-candidate) ou [iPhone](iphone.md#essayer-le-dictionnaire-de-la-prochaine-version-candidate) | « Installer » dans le guide [Android](android.md#installer) ou [iPhone](iphone.md#installer) |

Le fichier doit garder exactement le nom `corsu-keyboard.kmp` (sinon le renommer : Keyman tire l'identité du paquet
du nom du fichier).

## Avant de commencer

- Keyman est installé, avec EuroLatin (SIL) pour **Corsican** (étapes 1 et 2 du guide
  [Android](android.md) ou [iPhone](iphone.md)).
- Si un dictionnaire Corsu est déjà installé, le retirer d'abord (Langues installées › Corsican › le dictionnaire ›
  désinstaller), puis relancer Keyman, pour essayer le fichier choisi et pas l'ancien.
- Une application où écrire : Notes, Messages ou un champ de texte du navigateur.

## Déroulé

| # | Action | Attendu avec le candidat (1.1) | Attendu avec le publié (1.0) | OK ? |
| --- | --- | --- | --- | --- |
| 1 | Télécharger le fichier choisi (tableau ci-dessus) ; pour le candidat, extraire l'archive | `corsu-keyboard.kmp`, sous ce nom exact | idem | |
| 2 | L'importer dans Keyman (Android : Paramètres › Installer un clavier ou un dictionnaire › Installer depuis un fichier local ; iPhone : Ouvrir dans « Keyman », ou Paramètres › Installer depuis un fichier › Parcourir) | L'écran du paquet montre « Corsu », la version 1.1 et la langue Corsican ; Installer aboutit sans erreur | « Corsu », version 1.0, Corsican ; Installer aboutit | |
| 3 | Relancer Keyman, puis Langues installées › Corsican ; ouvrir le dictionnaire (Android : Dictionnaire › le dictionnaire coché ; iPhone : le dictionnaire › icône i) | Nom « Corsu », **Version du dictionnaire** 1.1 ; suggestions sur *Predictions with corrections* (Android) ou prédictions et corrections activées (iPhone) | Nom `platykalt.co.corsu`, version 1.0 ; mêmes réglages | |
| 4 | Dans l'application d'essai, choisir Keyman, EuroLatin (SIL) en corse ; taper `bonghj` | Le bandeau propose « bonghjornu » | idem | |
| 5 | Toucher « bonghjornu » | Le mot est écrit en entier, suivi d'une espace | idem | |
| 6 | Taper `grazzie` (faute voulue) | Le bandeau propose « grazie » | idem | |
| 7 | Taper une espace sans toucher le bandeau | « grazzie » reste tel quel : Keyman 18.0 n'a pas de correction automatique (limite connue de Keyman, pas du dictionnaire) | idem | |
| 8 | **Casse** : au milieu d'une phrase, taper `Ecc` (Maj à la main) | Le bandeau propose « Eccu » avec sa majuscule | « eccu » : défaut connu du paquet 1.0 | |
| 9 | Toucher la suggestion | « Eccu » garde sa majuscule | la majuscule est perdue (défaut connu) | |
| 10 | **Début de phrase** : après « bonghjornu. » et une espace, taper `ecc` sans toucher Maj | Le clavier EuroLatin met de lui-même la majuscule (« Ecc ») et les suggestions sont en majuscule : « Eccu » | majuscule du clavier, mais suggestions en minuscules (même défaut) | |
| 11 | Toujours en début de phrase : retour à la ligne sans ponctuation, puis `ecc` | Pas de majuscule automatique : comportement du clavier EuroLatin, limite connue (de même après `."`) | idem | |
| 12 | **Retour sur un mot** : écrire « Dopu ella vene », placer le curseur entre `ell` et `a`, choisir « ellu » dans le bandeau. Puis placer le curseur à la fin d'un mot et choisir une suggestion | Android : « Dopu ellu vene », le mot entier est remplacé (candidat produit à partir de cette modification ; l'archive du 18 octobre 2026 ne l'a pas). iPhone : « Dopu ellu a vene », le « a » est la fin de « ella » restée à droite du curseur (limite de Keyman pour iPhone). À la fin d'un mot : la suggestion remplace le mot entier | « Dopu ellu a vene » sur les deux : le « a » est la fin de « ella », restée à droite du curseur (limite connue de Keyman). À la fin d'un mot : le mot entier est remplacé | |
| 13 | Revenir au clavier habituel (Android : icône de clavier, ou appui court sur la touche globe ; iPhone : touche globe), puis de nouveau à Keyman | Les deux claviers alternent ; Keyman retrouve les suggestions corses | idem | |

Compter un peu moins d'une minute pour 1 à 3 si Keyman est déjà prêt, et le reste en trois ou quatre minutes.

**Échec ou limite ?** Les lignes 7, 11 et la première partie de 12 (sauf le candidat sur Android) décrivent des
limites connues de Keyman ou du clavier EuroLatin, et les lignes 8 à 10 de la colonne « publié » un défaut connu du paquet 1.0 : un résultat conforme
est « OK ». Un échec, c'est un résultat différent de la colonne « Attendu » du fichier essayé. Si rien ne change
après une mise à jour, relancer Keyman (changer de clavier puis revenir, ou forcer l'arrêt de l'application) avant de
conclure.

## Variantes régionales

Elles sont dans l'archive du candidat (et seront jointes à la version qui les publie) :
`corsu-keyboard-cismuntincu.kmp` et `corsu-keyboard-pumuntincu.kmp`, version 1.1. En installer une **après**
`corsu-keyboard.kmp`. Sur Android, attendu : les deux apparaissent dans la liste, mais l'ancien reste actif. Le
désinstaller (Corsican › Dictionnaire › le dictionnaire › Désinstaller le dictionnaire), relancer Keyman : la
variante devient active, avec son nom « Corsu – Cismuntincu (experimental) » ou « Corsu – Pumuntincu
(experimental) ».

## Noter le résultat

Plateforme et version du système, version de Keyman, fichier essayé (candidat avec le numéro de l'exécution GitHub
Actions, ou version publiée de Corsu) et version du dictionnaire affichée par Keyman, puis le numéro des lignes qui
échouent avec ce qui s'est affiché. Pas de capture d'écran avec des messages personnels.
