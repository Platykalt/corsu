# Installer Corsu sous macOS

[English](../../en/computer/macos.md)

Le plus simple est d'ouvrir le Terminal (Applications, puis Utilitaires) et d'y coller :

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

La commande télécharge la dernière version, vérifie sa somme SHA-256 et ouvre l'application
Corsu. Les logiciels trouvés sont tous cochés : décochez ce que vous ne voulez pas, cliquez sur Continuer, lisez
ce que Corsu va changer, puis cliquez sur Installer.

Vous pouvez aussi télécharger [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz), ouvrir le dossier `corsu` et
double-cliquer sur `Install for macOS.command`. La première fois, macOS refusera sans doute de l'ouvrir car le
fichier n'est pas signé : ouvrez Réglages Système, puis Confidentialité et sécurité, cliquez sur Ouvrir quand même
à côté du message, puis rouvrez le fichier.

Il n'y a rien d'autre à installer : l'archive contient son propre Python, pour les Mac Intel comme pour les Mac
Apple Silicon. Depuis le code source, il faut Python 3.10 ou plus récent, disponible sur
[python.org](https://www.python.org/downloads/macos/).

Sur macOS, Corsu traduit Firefox et Discord. Firefox en corse s'ouvre avec l'application Firefox Corsu du dossier
Applications. Chrome, Opera GX et les autres navigateurs Chromium ne sont pas pris en charge sur macOS : modifier
leurs fichiers casse leur signature et leur accès aux mots de passe enregistrés. Pour Discord, voir
[Discord](../discord.md).

## Changer d'avis

Ouvrez l'application Corsu dans le dossier Applications pour ajouter un logiciel, mettre une partie en pause ou retirer Corsu.
