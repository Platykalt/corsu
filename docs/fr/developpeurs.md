# Développement

[English](../en/developers.md)

## Organisation

```
.github/            CI, modèles de tickets, notes de version
docs/               docs/fr (français) et docs/en (anglais) : guides ordinateur et téléphone, Discord, compatibilité
keyboard/           le projet de prédiction de mots pour Keyman ; tools/build_keyboard.py remplit sa liste de mots
                    et construit corsu-keyboard.kmp
install/            Install for Windows.cmd, Install for macOS.command, Install for Linux.sh (placés en tête de
                    chaque archive), et get.sh / get.ps1 pour installer en une ligne
lexicon/            les traductions : lexicon.tsv (écrit pour Corsu), lexicon-mozilla.tsv et lexicon-upstream.tsv
                    (traductions relues reprises d'autres projets, chargées en premier)
src/                le programme : installer.py (installation), app.py (la fenêtre Corsu), corsu.py (Firefox, KDE,
                    Discord, raccourcis), chromium.py (navigateurs Chromium), engine.py (recherche et formats de
                    fichiers), release.json (version, révision de Vencord, sommes de contrôle des installeurs)
src/app/            la page Corsu Setup (index.html) et son icône
src/discord-plugin/ le plugin Vencord qui traduit Discord
src/firefox/        corsu.cfg (configuration automatique de Firefox) et le module qui complète les libellés de Google
tests/              tests unitaires ; tests/e2e/ contient les vérifications de bout en bout lancées par la CI
tools/              publication, rapport de couverture, import des traductions d'autres projets
vendor/             fichiers tiers figés
```

Seule la bibliothèque standard de Python est utilisée. Construire le plugin Discord demande Node.js 22 ou plus et pnpm.

Corsu Setup (`src/app.py`) est un petit serveur web lié à 127.0.0.1, sur un port au hasard. La page reçoit une clé
aléatoire dans la partie de l'adresse après `#` et l'envoie à chaque requête ; une requête sans elle, ou avec un autre
`Host`, est refusée, si bien que les autres pages ouvertes dans le navigateur ne peuvent pas le piloter. Chaque action
lance `installer.py` dans un processus à part et la page affiche ce qu'il écrit. Le serveur s'arrête dix minutes
après la dernière ouverture de la page. `app.py --text` donne le menu dans le terminal.

## Lexique

Chaque ligne d'un fichier `.tsv` de `lexicon/` s'écrit `anglais|français|corse`. L'une des deux sources peut être
vide. Le moteur charge `lexicon-mozilla.tsv`, puis `lexicon-upstream.tsv`, puis `lexicon.tsv` ; la première
traduction trouvée l'emporte, donc les traductions relues passent avant les autres.

Les variables sont reconnues par leur position : une seule ligne `Restart %1|Redémarrer %1|Rilancià %1` couvre aussi
`Redémarrer { -brand-short-name }` dans Firefox et `Redémarrer $1` dans Chrome. Le moteur refuse une traduction qui
perdrait ou ajouterait une variable ou une balise.

`tools/import_translations.py` télécharge les traductions corses de Firefox pour Android et iOS, Mozilla VPN,
Thunderbird pour Android, VLC pour Android, Audacity, Poedit, WinMerge et Notepad++, et réécrit les deux fichiers
relus. `tools/coverage.py --output missing-labels.json` liste ce qui reste à traduire sur l'ordinateur.

## Tests

```sh
python3 -m unittest discover -s tests -t .
python3 tests/e2e/e2e.py firefox     # installe dans un dossier personnel jetable, lance Firefox et lit ses menus
python3 tests/e2e/e2e.py discord     # modifie un faux Discord avec l'installeur officiel de Vencord
CORSU_CHROMIUM=/chemin/vers/chrome-for-testing python3 tests/e2e/e2e.py chromium
```

`CORSU_CHROMIUM` remplace tous les navigateurs Chromium installés par le dossier indiqué : le test ne touche jamais
un vrai navigateur. `CORSU_FIREFOX` fait de même pour Firefox.

## Intégration continue

[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) tourne à chaque envoi :

1. tests unitaires sous Linux, Windows et macOS avec Python 3.10 et 3.13 ;
2. construction de Vencord et des trois archives ;
3. sur chaque système, depuis son archive : installation, lancement de Firefox traduit et de Chrome for Testing,
   lecture de leur texte, désactivation, réactivation, désinstallation et vérification que rien ne reste ; puis
   modification d'un faux Discord avec l'installeur officiel de Vencord et vérification de sa restauration.

Envoyer une étiquette `vX.Y.Z` qui correspond à `src/release.json` publie une version sur GitHub avec les archives,
seulement si tout ce qui précède passe.

## Publier une version

1. Mettre à jour `version` dans `src/release.json` et ajouter une entrée au `CHANGELOG.md`.
2. Committer, puis `git tag vX.Y.Z && git push origin vX.Y.Z`.
