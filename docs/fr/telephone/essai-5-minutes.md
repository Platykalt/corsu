# Essai du dictionnaire Keyman en 5 minutes

Pour la personne qui publie Corsu : après une version, vérifier sur un vrai téléphone que `corsu-keyboard.kmp`
s'installe et fonctionne. Un essai sur Android ou sur iPhone ; noter la plateforme, la version d'Android ou d'iOS et
la version de Keyman (menu › Paramètres, ou « À propos »). Le résultat ne vaut que pour ce téléphone et cette version.

Les résultats attendus sont ceux des paquets de la prochaine version (dictionnaire version 1.1, nommé « Corsu » dans
Keyman). Ils ont été observés avec le moteur de Keyman 18.0.254 et l'application Keyman 18.0.254 sur un émulateur
Android 14, pas encore sur un téléphone réel ni sur un iPhone. Avec le paquet de la v0.25.1 et des versions
antérieures, les lignes marquées « 0.25.1 » diffèrent.

## Avant de commencer

- Keyman est installé, avec EuroLatin (SIL) pour **Corsican** (étapes 1 et 2 du guide
  [Android](android.md) ou [iPhone](iphone.md)).
- Si une version précédente du dictionnaire est installée, la retirer d'abord (Langues installées › Corsican ›
  le dictionnaire › désinstaller), puis relancer Keyman, pour essayer le fichier publié et pas l'ancien.
- Une application où écrire : Notes, Messages ou un champ de texte du navigateur.

## Déroulé

| # | Action | Résultat attendu | OK ? |
| --- | --- | --- | --- |
| 1 | Sur le téléphone, ouvrir https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp | Le fichier se télécharge sous le nom exact `corsu-keyboard.kmp` (sinon le renommer : Keyman tire l'identité du paquet du nom du fichier) | |
| 2 | L'importer dans Keyman (Android : Paramètres › Installer un clavier ou un dictionnaire › Installer depuis un fichier local ; iPhone : Ouvrir dans « Keyman ») | L'écran du paquet montre « Corsu », la version 1.1 et la langue Corsican ; Installer aboutit sans erreur | |
| 3 | Langues installées › Corsican | Le dictionnaire s'appelle « Corsu » (0.25.1 : `platykalt.co.corsu`) ; suggestions sur *Predictions with corrections* (Android) ou prédictions et corrections activées (iPhone) | |
| 4 | Dans l'application d'essai, choisir Keyman, EuroLatin (SIL) en corse ; taper `bonghj` | Le bandeau propose « bonghjornu » | |
| 5 | Toucher « bonghjornu » | Le mot est écrit en entier, suivi d'une espace | |
| 6 | Taper `grazzie` (faute voulue) | Le bandeau propose « grazie » | |
| 7 | Taper une espace sans toucher le bandeau | « grazzie » reste tel quel : Keyman 18.0 n'a pas de correction automatique (limite connue de Keyman, pas du dictionnaire) | |
| 8 | **Casse** : au milieu d'une phrase, taper `Ecc` (Maj à la main) | Le bandeau propose « Eccu » avec sa majuscule (0.25.1 : « eccu », défaut connu, corrigé dans les nouveaux paquets) | |
| 9 | Toucher la suggestion | « Eccu » garde sa majuscule (0.25.1 : la perd) | |
| 10 | **Début de phrase** : après « bonghjornu. » et une espace, taper `ecc` sans toucher Maj | Le clavier EuroLatin met de lui-même la majuscule (« Ecc ») et les suggestions sont en majuscule : « Eccu » | |
| 11 | Toujours en début de phrase : retour à la ligne sans ponctuation, puis `ecc` | Pas de majuscule automatique : comportement du clavier EuroLatin, limite connue (de même après `."`) | |
| 12 | **Retour sur un mot** : écrire « ella », placer le curseur entre `ell` et `a`, choisir « ellu » dans le bandeau | Résultat « ellu a » : la suggestion ne remplace que la partie à gauche du curseur (limite connue de Keyman). Puis placer le curseur à la fin d'un mot : la suggestion remplace le mot entier | |
| 13 | Revenir au clavier habituel (Android : icône de clavier ; iPhone : touche globe), puis de nouveau à Keyman | Les deux claviers alternent ; Keyman retrouve les suggestions corses | |

Compter un peu moins d'une minute pour 1 à 3 si Keyman est déjà prêt, et le reste en trois ou quatre minutes.

**Échec ou limite ?** Les lignes 7, 11 et la première partie de 12 décrivent des limites connues de Keyman ou du
clavier EuroLatin : un résultat conforme est « OK ». Un échec, c'est un résultat différent de la colonne « Résultat
attendu ». Si rien ne change après une mise à jour, relancer Keyman (changer de clavier puis revenir, ou forcer
l'arrêt de l'application) avant de conclure.

## Variantes régionales (si la version les publie)

Si la version contient `corsu-keyboard-cismuntincu.kmp` ou `corsu-keyboard-pumuntincu.kmp` : en installer une
**après** `corsu-keyboard.kmp`. Sur Android, attendu : les deux apparaissent dans la liste, mais l'ancien reste
actif. Le désinstaller (Corsican › Dictionnaire › le dictionnaire › Désinstaller le dictionnaire), relancer Keyman :
la variante devient active, avec son nom « Corsu – Cismuntincu (experimental) » ou « Corsu – Pumuntincu
(experimental) ».

## Noter le résultat

Plateforme et version du système, version de Keyman, version de Corsu (le nom de la version publiée), puis le
numéro des lignes qui échouent avec ce qui s'est affiché. Pas de capture d'écran avec des messages personnels.
