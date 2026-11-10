# Discord en corse

[English](../en/discord.md)

Corsu traduit Discord grâce à Vencord, une modification libre de l'application Discord, et à un petit plugin qui
remplace le texte de l'interface. Les messages, les noms de serveurs et les noms d'utilisateurs ne sont jamais
modifiés.

## Application de bureau (Windows, macOS, Linux)

1. Installez Corsu (ou rouvrez l'application Corsu) et laissez Discord coché. Si Discord est ouvert, Corsu le modifie quand même ;
   le changement prend effet au prochain démarrage.
2. Quittez complètement Discord (depuis l'icône de la barre des tâches, pas seulement la fenêtre) et rouvrez-le.
3. Dans Discord, ouvrez Paramètres utilisateur, puis Langue, et choisissez **Français** ou **English**. Le plugin
   traduit à partir de ces deux langues. Toute autre langue, le portugais par exemple, reste telle quelle.

Pour vérifier : ouvrez les Paramètres utilisateur et descendez dans la colonne de gauche. La section de Vencord doit
y apparaître, et la page Plugins doit montrer Corsu activé. Les libellés des paramètres doivent être en corse.

Vesktop, une application Discord qui contient déjà Vencord, marche de la même façon : cochez Vesktop dans
l'installeur.

## Dépannage

- **Discord bloqué sur « Starting » ou qui ne démarre plus.** Voir [Démarrage de Discord : alertes et mode de secours](discord-demarrage.md)
  (bouton « Démarrer sans la traduction », procédure manuelle).
- **Toujours dans une autre langue.** C'est la langue de Discord qui décide : choisissez Français ou English. Le
  plugin Corsu affiche un rappel quand Discord est réglé sur une autre langue.
- **Pas de section Vencord dans les paramètres.** Discord s'est mis à jour et a retiré la modification. Rouvrez
  l'application Corsu, ou relancez l'installeur avec seulement Discord coché.
- **Linux, Discord installé par la distribution.** Les paquets récents gardent le programme dans
  `~/.config/discord/app-<version>`. Corsu modifie le plus récent. Après une mise à jour de Discord, rouvrez
  l'application Corsu.
- **Discord en Flatpak.** Non pris en charge : utilisez le paquet classique ou Vesktop.
- **Vous utilisiez déjà Vencord.** Corsu le remplace par une version de Vencord qui contient le plugin Corsu. Vos
  autres plugins et réglages Vencord sont conservés.

## Si Discord ne démarre plus et que Corsu ne peut pas aider

L'aide de Corsu quand Discord reste bloqué (alerte, bouton « Démarrer sans la traduction ») est dans la fenêtre de
Corsu. Elle ne sert à rien si cette fenêtre ne s'ouvre pas, ou si c'est Corsu lui-même qui est cassé. Ce qui est
couvert, précisément :

- **Linux** : un démarrage depuis l'entrée du menu de Discord ou à l'ouverture de session est surveillé sur le moment
  (notification s'il reste bloqué). Les autres démarrages (terminal, autre lanceur, Discord qui se relance après sa
  mise à jour) ne sont vus qu'après coup, par la fenêtre de Corsu.
- **Windows et macOS** : aucun démarrage n'est surveillé sur le moment et aucune notification n'est envoyée au
  démarrage de Discord. La fenêtre de Corsu, tant qu'elle est ouverte, lit le journal de Discord toutes les
  30 secondes et montre le problème du dernier démarrage. Sans ouvrir la fenêtre de Corsu, rien ne vous prévient.
- Les notifications de Corsu respectent le mode « Ne pas déranger » du système (Assistant de concentration, Concentration) :
  aucune n'est forcée.

Ces façons de revenir en arrière **n'ont pas besoin** de la fenêtre de Corsu. Quittez d'abord complètement Discord
(aussi depuis son icône de la zone de notification).

1. **Remettre l'archive d'origine de Discord** (Discord démarre alors sans la traduction, rien d'autre ne change). Dans
   le dossier `resources` de Discord, l'installeur officiel de Vencord a gardé l'original sous le nom `_app.asar` :
   copiez-le par-dessus `app.asar` et gardez `_app.asar`.
   - Windows (PowerShell ; la première commande prend le dossier `app-<version>` le plus récent) :
     ```powershell
     $resources = (Get-ChildItem "$env:LOCALAPPDATA\Discord\app-*" | Sort-Object { [version]($_.Name -replace '^app-') } | Select-Object -Last 1).FullName + "\resources"
     Copy-Item "$resources\_app.asar" "$resources\app.asar"
     ```
     Discord PTB et Canary : `DiscordPTB` et `DiscordCanary` au lieu de `Discord`.
   - Linux : `cp ~/.config/discord/app-<version>/resources/_app.asar ~/.config/discord/app-<version>/resources/app.asar`
     (chaque dossier `app-<version>` qui a un `_app.asar`), ou `/opt/discord/resources/`.
   - macOS : `cp /Applications/Discord.app/Contents/Resources/_app.asar /Applications/Discord.app/Contents/Resources/app.asar`
   - Pas de `_app.asar`, ou un tout petit (quelques centaines d'octets) ? Corsu a gardé sa propre copie de l'original :
     dans `installation.json`, dans le dossier de données de Corsu (`%LOCALAPPDATA%\corsu` sous Windows,
     `~/.local/share/corsu` sous Linux, `~/Library/Application Support/corsu` sous macOS), l'entrée de cet `app.asar`
     la nomme sous `"backup"` (un fichier du dossier `backups` voisin). Copiez ce fichier par-dessus `app.asar`.
2. **Ou réinstaller Discord** avec l'installeur de Discord, sur discord.com (sous Windows, désinstallez d'abord Discord
   dans Paramètres, Applications). Un Discord neuf n'a pas Vencord. Votre compte, vos serveurs et vos messages sont
   sur les serveurs de Discord ; Discord garde ses réglages locaux.
3. **Ou retirer la modification de Corsu depuis un terminal**, sans la fenêtre, avec l'installeur d'une archive de
   Corsu (`installer.py --uninstall` retire tout ce que Corsu a modifié, Discord compris). Attention :
   `installer.py --disable discord` désactive seulement le plugin Corsu ; Vencord se charge toujours, ce qui ne
   sert à rien quand c'est Vencord qui bloque Discord.

Ensuite, une mise à jour ou une réparation de Corsu avec Discord coché remet la traduction (un Discord remis à la main
compte comme inchangé) : décochez Discord tant qu'aucune version de Corsu ne dit corriger le problème, ou, dès que la
fenêtre de Corsu s'ouvre, utilisez son mode de secours, que les mises à jour de Corsu respectent. Détails :
[Démarrage de Discord : alertes et mode de secours](discord-demarrage.md).

## Version web (discord.com dans un navigateur)

Pas encore prise en charge. Le plugin Corsu est intégré à la copie de Vencord de Corsu, qui ne tourne que dans
l'application de bureau.

## Applications pour téléphone

Impossible. Les applications Discord pour téléphone ne peuvent pas être modifiées, et Discord ne propose pas le corse.
