# Installing Corsu on macOS

[En français plus bas](#en-français)

The simplest way is to open Terminal (in Applications, then Utilities) and paste this line:

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

It downloads the latest release, checks its SHA-256 checksum and starts the installer. Every program found is selected; type a number to leave one out, then press Enter and type `y` to confirm.

You can also download [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz),
open the `corsu` folder and double-click `Install for macOS.command`. macOS will probably refuse to open it the
first time, because the file is not signed by a registered developer. Go to System Settings, then Privacy &
Security, click Open Anyway next to the message about the file, and open it again.

Corsu needs Python 3.10 or newer. If macOS offers to install the command line developer tools, accept: they
include Python. You can also get it from [python.org](https://www.python.org/downloads/macos/).

On macOS Corsu translates Firefox and Discord. Firefox in Corsican opens from the Firefox Corsu app in your
Applications folder. Chrome and Opera GX are not supported on macOS yet.

## Changing your mind later

Open Corsu Setup from your Applications folder to add a program, go back to French, or remove Corsu.

## En français

Le plus simple est d'ouvrir le Terminal (dans Applications, puis Utilitaires) et d'y coller cette ligne :

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

Elle télécharge la dernière version, vérifie sa somme SHA-256 et lance l'installeur. Tous les logiciels trouvés sont sélectionnés ; tapez un numéro pour en retirer un, puis appuyez sur Entrée et tapez `y` pour confirmer.

Vous pouvez aussi télécharger [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz),
ouvrir le dossier `corsu` et double-cliquer sur `Install for macOS.command`. La première fois, macOS refusera
sans doute de l'ouvrir, car le fichier n'est pas signé. Allez dans Réglages Système, puis Confidentialité et
sécurité, cliquez sur Ouvrir quand même à côté du message concernant le fichier, puis ouvrez-le de nouveau.

Corsu a besoin de Python 3.10 ou plus récent. Si macOS propose d'installer les outils de développement en ligne de
commande, acceptez : ils contiennent Python.

Sur macOS, Corsu traduit Firefox et Discord. Firefox en corse s'ouvre avec l'application Firefox Corsu de votre
dossier Applications. Pour revenir au français ou tout retirer, ouvrez Corsu Setup dans le même dossier.
