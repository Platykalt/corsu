# Ce que Corsu modifie

[English](../en/what-corsu-changes.md)

Corsu ne touche qu'aux logiciels que vous choisissez. Chaque fichier qu'il écrit est noté dans `installation.json`,
et l'original est copié dans un dossier `backups` à côté. Les deux se trouvent dans le dossier de données de Corsu :
`%LOCALAPPDATA%\corsu` sous Windows, `~/Library/Application Support/corsu` sous macOS et `~/.local/share/corsu` sous
Linux.

La désinstallation remet chaque fichier d'origine. Si vous avez modifié vous-même l'un de ces fichiers après
l'installation, Corsu laisse votre version et indique où se trouve la copie d'origine.

## Firefox

Corsu fait une copie de votre Firefox dans son dossier de données et traduit cette copie. Votre Firefox n'est pas
modifié. La copie ouvre votre profil habituel : vos marque-pages, mots de passe et extensions sont là.

La traduction part du pack de langue français de Mozilla pour votre version exacte de Firefox. Corsu le télécharge
sur archive.mozilla.org et le vérifie avec les sommes de contrôle publiées par Mozilla. Hors ligne, il utilise la
copie fournie avec la version de Corsu. Les traductions corses sont ensuite appliquées par-dessus le texte français.

La copie indique aussi aux sites web que vous préférez le corse, puis le français. Les sites qui proposent le corse,
dont Google, l'affichent alors. L'interface corse de Google est incomplète et laisse certains boutons et menus en
français ou en anglais ; sur les pages de Google, la copie complète ces libellés avec le lexique de Corsu. Les
résultats de recherche et le reste du texte des pages ne sont jamais modifiés, et aucun autre site n'est touché.

Quand Firefox se met à jour, la copie est reconstruite à la prochaine ouverture. Le système de mise à jour propre à
la copie est donc coupé. Les réglages de sécurité de Firefox et la vérification des extensions ne changent pas.

Sous Windows, on l'ouvre avec le raccourci Firefox Corsu du menu Démarrer, et sous macOS avec l'application Firefox
Corsu de `~/Applications`. Sous Linux, l'entrée Firefox habituelle du menu l'ouvre, et `~/.local/bin/firefox-corsu`
fait de même depuis un terminal.

Les versions Snap et Flatpak de Firefox ne peuvent pas être copiées : Corsu a besoin de la version classique de
Mozilla ou de votre distribution.

## Navigateurs Chromium

Cela concerne Google Chrome, Chromium, Opera, Opera GX, Microsoft Edge, Brave et Vivaldi, sous Windows et Linux.

Ces navigateurs gardent le texte français de leur interface dans un fichier, `fr.pak`. Corsu réécrit ce fichier avec
les traductions corses, et le navigateur affiche alors le corse partout où il aurait affiché le français. Votre
profil, vos mots de passe et vos cookies ne sont pas touchés. Le navigateur est aussi réglé pour indiquer aux sites
que vous préférez le corse, puis le français.

Sous Windows, Corsu règle la langue du navigateur sur le français pour qu'il lise ce fichier. Un navigateur installé
pour tous les utilisateurs se trouve dans `Program Files` : Windows demande alors l'autorisation avant que Corsu ne
le modifie.

Sous Linux, l'entrée du navigateur dans le menu passe par Corsu, qui le lance avec `LANGUAGE=co:fr`. Si le navigateur
a été installé par votre distribution, votre mot de passe est demandé.

Une mise à jour du navigateur apporte un nouveau fichier français. Corsu le traduit de nouveau à la prochaine
ouverture de session sous Windows, ou à l'ouverture du navigateur depuis son entrée de menu sous Linux.

Sous macOS, modifier les fichiers d'un navigateur casse sa signature, et il perd alors l'accès aux mots de passe et
cookies rangés dans le Trousseau. Corsu ne prend donc pas ces navigateurs en charge sur macOS.

## Discord

Corsu utilise Vencord, une modification libre de l'application Discord, avec un petit plugin qui traduit
l'interface. Les messages, les noms de serveurs et les noms d'utilisateurs ne sont jamais traduits.

L'application Discord est modifiée avec l'installeur officiel de Vencord, après que Corsu a vérifié sa somme de
contrôle avec celle notée dans `src/release.json`. Vesktop, une application Discord qui contient déjà Vencord, n'a
besoin que d'un réglage. Les mises à jour automatiques de Vencord sont coupées, car elles effaceraient le plugin.

Réglez la langue de Discord sur le français ou l'anglais : le plugin traduit à partir de ces deux langues.
[discord.md](discord.md) donne les détails et le dépannage.

## KDE Plasma

Sous Linux, Corsu construit des fichiers de traduction corses pour le bureau et les programmes KDE à partir des
fichiers français installés, et les place dans `~/.local/share/locale/co`. Il règle ensuite la langue de Plasma sur
`co:fr` : ce qui n'a pas encore de traduction corse s'affiche en français. Les noms des programmes dans le menu ne
changent pas. Déconnectez-vous et reconnectez-vous pour voir le changement.

Les programmes hors KDE (programmes GTK, commandes du terminal) ainsi que les boutons et boîtes de dialogue propres à
Qt ne lisent leurs traductions que dans des dossiers du système. Les traductions système, en option, copient les
fichiers corses dans `/usr/share/locale/co` et `/usr/share/qt6/translations` après avoir demandé votre mot de passe.
Un fichier qui appartient à un paquet installé n'est jamais écrasé, et la désinstallation retire ce que Corsu a
copié.

Les nouveaux terminaux suivent un petit interrupteur lu par bash, zsh et fish : le terminal peut repasser en français
seul, pour une heure ou jusqu'à ce que vous le réactiviez.

## Revenir au français

Chaque partie peut être désactivée séparément : Firefox, les navigateurs Chromium, Discord, Vesktop, le bureau, le
terminal. Désactiver une partie lui rend sa langue d'avant mais garde les fichiers traduits : la réactiver est
immédiat.
