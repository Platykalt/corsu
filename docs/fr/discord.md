# Discord en corse

[English](../en/discord.md)

Corsu traduit Discord grâce à Vencord, une modification libre de l'application Discord, et à un petit plugin qui
remplace le texte de l'interface. Les messages, les noms de serveurs et les noms d'utilisateurs ne sont jamais
modifiés.

## Application de bureau (Windows, macOS, Linux)

1. Lancez l'installeur de Corsu et laissez Discord coché. Si Discord est ouvert, l'installeur le modifie quand même ;
   le changement prend effet au prochain démarrage.
2. Quittez complètement Discord (depuis l'icône de la barre des tâches, pas seulement la fenêtre) et rouvrez-le.
3. Dans Discord, ouvrez Paramètres utilisateur, puis Langue, et choisissez **Français** ou **English**. Le plugin
   traduit à partir de ces deux langues. Toute autre langue, le portugais par exemple, reste telle quelle.

Pour vérifier : ouvrez les Paramètres utilisateur et descendez dans la colonne de gauche. La section de Vencord doit
y apparaître, et la page Plugins doit montrer Corsu activé. Les libellés des paramètres doivent être en corse.

Vesktop, une application Discord qui contient déjà Vencord, marche de la même façon : cochez Vesktop dans
l'installeur.

## Dépannage

- **Toujours dans une autre langue.** C'est la langue de Discord qui décide : choisissez Français ou English. Le
  plugin Corsu affiche un rappel quand Discord est réglé sur une autre langue.
- **Pas de section Vencord dans les paramètres.** Discord s'est mis à jour et a retiré la modification. Rouvrez
  Corsu Setup, ou relancez l'installeur avec seulement Discord coché.
- **Linux, Discord installé par la distribution.** Les paquets récents gardent le programme dans
  `~/.config/discord/app-<version>`. Corsu modifie le plus récent. Après une mise à jour de Discord, relancez Corsu
  Setup.
- **Discord en Flatpak.** Non pris en charge : utilisez le paquet classique ou Vesktop.
- **Vous utilisiez déjà Vencord.** Corsu le remplace par une version de Vencord qui contient le plugin Corsu. Vos
  autres plugins et réglages Vencord sont conservés.

## Version web (discord.com dans un navigateur)

Pas encore prise en charge. Le plugin Corsu est intégré à la copie de Vencord de Corsu, qui ne tourne que dans
l'application de bureau.

## Applications pour téléphone

Impossible. Les applications Discord pour téléphone ne peuvent pas être modifiées, et Discord ne propose pas le corse.
