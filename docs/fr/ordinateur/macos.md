# Installer Corsu sous macOS

[English](../../en/computer/macos.md)

Le plus simple est d'ouvrir le Terminal (Applications, puis Utilitaires) et d'y coller :

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

La commande télécharge la dernière version, vérifie sa somme SHA-256 et lance l'installeur. Appuyez sur Entrée pour
tout installer, ou tapez d'abord un numéro pour décocher un élément. Tapez `o` pour confirmer.

Vous pouvez aussi télécharger [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz), ouvrir le dossier `corsu` et
double-cliquer sur `Install for macOS.command`. La première fois, macOS refusera sans doute de l'ouvrir car le
fichier n'est pas signé : ouvrez Réglages Système, puis Confidentialité et sécurité, cliquez sur Ouvrir quand même
à côté du message, puis rouvrez le fichier.

Corsu a besoin de Python 3.10 ou plus récent. Si macOS propose d'installer les outils de développement en ligne de
commande, acceptez : ils contiennent Python. Python est aussi disponible sur [python.org](https://www.python.org/downloads/macos/).

Sur macOS, Corsu traduit Firefox et Discord. Firefox en corse s'ouvre avec l'application Firefox Corsu du dossier
Applications. Chrome, Opera GX et les autres navigateurs Chromium ne sont pas pris en charge sur macOS : modifier
leurs fichiers casse leur signature et leur accès aux mots de passe enregistrés. Pour Discord, voir
[Discord](../discord.md).

## Changer d'avis

Ouvrez Corsu Setup dans le dossier Applications pour ajouter un logiciel, mettre une partie en pause ou retirer Corsu.
