# Installing Corsu on Linux

[En français plus bas](#en-français)

The quickest way is one line in a terminal:

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/tools/get.sh | sh
```

It downloads the latest release, checks its SHA-256 checksum and starts the installer.

To do it by hand, download [corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz),
extract it, and run the installer from the `corsu` folder:

```sh
tar xzf corsu-linux.tar.gz
cd corsu
./"Install for Linux.sh"
```

Every program found is selected; type a number to leave one out, then press Enter and type `y` to confirm. Some steps ask for your password:
translating a browser installed by your distribution, and the optional Qt dialogs.

Corsu needs Python 3.10 or newer, which every current distribution ships. Firefox has to be the regular package
or Mozilla's own build; the Snap and Flatpak versions cannot be translated. For the desktop, KDE Plasma and its
French translations must be installed.

Close the programs before confirming and open them again afterwards. Log out and back in to see the Plasma desktop
in Corsican.

## Changing your mind later

Open Corsu Setup from the application menu to add a program, go back to French, or remove Corsu.

## En français

Le plus simple est une ligne dans un terminal :

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/tools/get.sh | sh
```

Elle télécharge la dernière version, vérifie sa somme SHA-256 et lance l'installeur.

À la main : téléchargez [corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz),
décompressez-le et lancez `./"Install for Linux.sh"` depuis le dossier `corsu`.

Tous les logiciels trouvés sont sélectionnés ; tapez un numéro pour en retirer un, puis appuyez sur Entrée et tapez `y` pour confirmer. Certaines étapes demandent
votre mot de passe : traduire un navigateur installé par la distribution, et les boîtes de dialogue Qt.

Firefox doit être la version classique de votre distribution ou celle de Mozilla, pas la version Snap ou Flatpak.
Pour le bureau, KDE Plasma et ses traductions françaises doivent être installés. Déconnectez-vous puis
reconnectez-vous pour voir Plasma en corse. Pour revenir au français ou tout retirer, ouvrez Corsu Setup dans le
menu des applications.
