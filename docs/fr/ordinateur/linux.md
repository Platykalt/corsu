# Installer Corsu sous Linux

[English](../../en/computer/linux.md)

Le plus simple est une ligne dans un terminal :

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

Elle télécharge la dernière version, vérifie sa somme SHA-256 et lance l'installeur. À la main : téléchargez
[corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz), décompressez-le et lancez `./"Install for Linux.sh"` depuis le dossier
`corsu`.

L'application Corsu s'ouvre dans sa fenêtre. Les logiciels trouvés sont tous cochés : décochez ce que vous
ne voulez pas, cliquez sur Continuer, lisez ce que Corsu va changer, puis cliquez sur Installer. Sans interface
graphique, ou avec `--text`, l'installation se fait dans le terminal : Entrée installe tout ce qui est coché, un
numéro coche ou décoche un élément. Certaines étapes demandent votre mot de passe : traduire un
navigateur installé par la distribution, et les traductions système utilisées par les programmes GTK et les commandes
du terminal.

Corsu a besoin de Python 3.10 ou plus récent, présent dans les distributions actuelles.

## Différences entre distributions

- Arch, CachyOS, Manjaro, Fedora, openSUSE, Debian : le paquet Firefox de la distribution fonctionne.
- Ubuntu installe Firefox en Snap, qui ne peut pas être traduit. Installez plutôt le Firefox de Mozilla, depuis
  [le dépôt APT de Mozilla](https://support.mozilla.org/kb/install-firefox-linux) ou l'archive de mozilla.org.
- Les versions Flatpak de Firefox, Chrome ou Discord sont scellées et ne peuvent pas être traduites.
- La traduction du bureau demande KDE Plasma et ses traductions françaises. Sur GNOME et les autres bureaux, Corsu
  traduit les navigateurs et Discord, et les traductions système couvrent quand même les programmes GTK et les
  commandes du terminal.

Fermez les logiciels avant de confirmer, puis rouvrez-les. Déconnectez-vous et reconnectez-vous pour voir Plasma en
corse. Pour Discord, voir [Discord](../discord.md).

## Changer d'avis

Ouvrez l'application Corsu dans le menu des applications pour ajouter un logiciel, mettre le terminal en pause une heure,
désactiver une partie ou retirer Corsu. Depuis un terminal : `python3 src/installer.py --disable terminal --hours 1`,
`--enable terminal`, `--uninstall`.
