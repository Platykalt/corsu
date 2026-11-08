# Démarrage de Discord : alertes et mode de secours

[English](../en/discord-start.md)

La traduction de Discord passe par Vencord. Quand Discord change sa façon de se charger, Vencord peut cesser de
fonctionner et Discord rester bloqué sur « Starting » (c'est arrivé avec Corsu 0.28.3 et Discord 1.0.168). Corsu
observe donc les démarrages de Discord et propose de quoi s'en sortir. Cette page dit ce qui est observé, ce que font
les boutons, et comment tout remettre à la main.

## Ce qui déclenche une alerte

Corsu lit le journal de Discord (`logs/renderer_js.log` dans le dossier de Discord), jamais Discord lui-même, et
classe le dernier démarrage :

| Ce que Corsu a vu | Ce qu'il en dit |
|---|---|
| Une erreur qui mentionne Vencord avant l'affichage de Discord | *probablement* une incompatibilité avec la traduction |
| Une autre erreur avant l'affichage | un problème au démarrage, cause non déterminée |
| Rien de décisif après quelques minutes, Discord toujours ouvert | démarrage lent, cause inconnue |
| Échec de connexion ou de mise à jour de Discord | réseau ou serveurs de Discord ; la traduction n'est probablement pas en cause |
| La fenêtre ouverte hors de l'écran (Linux Hyprland seulement) | fenêtre hors écran |
| Discord fermé avant son affichage, sans erreur notée | pas d'alerte : une fermeture volontaire et un plantage sans trace donnent le même journal, Corsu ne peut pas les distinguer |

Corsu ne dit jamais qu'une cause est certaine : un journal montre ce qui s'est passé, pas toujours pourquoi.

## Quels démarrages sont surveillés

- **Linux** : quand Discord est ouvert depuis son entrée du menu ou démarré avec la session, Corsu le lance puis le
  surveille quelques minutes ; une notification apparaît en cas de problème (sauf si « Ne pas déranger » est actif :
  c'est le système qui décide).
- **Windows et macOS** : Discord réécrit ses propres raccourcis à chaque mise à jour, Corsu ne les remplace donc pas.
  Le problème est constaté après coup, à l'ouverture de la fenêtre Corsu.
- **Non couverts** : Discord relancé par son propre outil de mise à jour (le démarrage suivant est surveillé),
  Discord lancé depuis un terminal ou un autre lanceur.

Pour arrêter la surveillance sous Linux (Discord retrouve alors son entrée de menu d'origine) :
`installer.py --discord-watch off` ; `--discord-watch on` la remet. Le choix est gardé lors des mises à jour.

Sans service de notification, rien ne s'affiche : l'incident reste noté et la fenêtre Corsu le montre (ligne
Discord de l'accueil). Une seule notification par incident.

## La page « Discord » de la fenêtre Corsu

Elle s'ouvre depuis le bouton de la notification ou depuis la ligne Discord de l'accueil.

- **Rechercher une mise à jour** : la même vérification que la page « À propos ». La page dit ce qui est vrai :
  mise à jour disponible, Corsu à jour, vérification impossible, mise à jour installée mais Discord encore ouvert avec
  l'ancienne version, ou copie de développement. Une mise à jour n'est jamais présentée comme la solution : ses notes
  de version disent ce qu'elle corrige.
- **Démarrer sans la traduction** : met Discord en *mode de secours*. Corsu remet l'archive d'origine de Discord
  (gardée lors de l'installation et vérifiée) ; Discord démarre alors en français ou en anglais. Discord doit être
  fermé : Corsu ne ferme jamais Discord à votre place. Tant que le mode de secours est actif, les mises à jour et
  réparations de Corsu ne remettent pas la traduction d'elles-mêmes.
- **Remettre la traduction** (en mode de secours) : réinstalle la traduction puis démarre Discord sous surveillance.
  - La réactivation n'est annoncée réussie que si ce démarrage montre le plugin Corsu en train de démarrer. Une
    fermeture, un démarrage sans signal décisif ou un Discord affiché sans le plugin restent « non confirmés » : le
    mode de secours reste actif (Corsu ne touche pas à Discord) jusqu'à un démarrage qui le prouve (bouton
    **Réessayer**, ou le prochain démarrage surveillé), ou jusqu'à **Démarrer sans la traduction**.
  - Si le démarrage échoue, Corsu remet l'archive d'origine. Si Discord est resté ouvert et bloqué, rien n'est
    remplacé sous lui : la page demande de le quitter complètement, puis **Terminer la restauration** remet
    l'archive d'origine. Entre-temps, aucune mise à jour ni réparation ne remet la traduction.
- **Réessayer** : relance Discord sous surveillance (seulement si Discord est fermé).
- **Voir le diagnostic** : l'état observé, les versions de Discord, de Corsu et de Vencord, et les lignes du journal
  qui ont décidé (les données personnelles en sont retirées).
- **Plus tard** : l'incident reste noté mais ne demande plus votre attention.

## Limites

- La surveillance lit un journal : si Discord change ses messages, un démarrage peut être classé « lent » au lieu
  d'« erreur ».
- Sans connexion à un compte, le démarrage réussi correspond à la page de connexion de Discord, où le plugin Corsu
  ne démarre pas encore : une réactivation y reste « non confirmée ».
- **Windows et macOS** : pas d'alerte au moment du démarrage. Il faut ouvrir la fenêtre Corsu pour constater un
  problème : sur ces systèmes, la fonction est partielle.
- Sans service de notification (ou avec « Ne pas déranger »), aucune aide immédiate : il faut ouvrir la fenêtre Corsu.
- Les notifications sont en français ou en anglais, pas encore en corse. Sous Windows, elles s'affichent sous le nom
  « Windows PowerShell » et n'ont pas de bouton.
- Le mode de secours ne s'applique qu'à l'installation de Discord que Corsu a lui-même modifiée, avec une copie
  d'origine vérifiée. Sinon, le bouton explique pourquoi et la procédure manuelle ci-dessous reste possible.

## Procédure manuelle

Si la fenêtre Corsu ne s'ouvre pas ou si le bouton refuse, vous pouvez remettre Discord d'origine vous-même.
L'installeur officiel de Vencord a mis l'archive d'origine de Discord à côté de la sienne, sous le nom `_app.asar`.

1. Quittez complètement Discord (y compris depuis l'icône de la zone de notification).
2. Copiez `_app.asar` par-dessus `app.asar`, dans le dossier `resources` de Discord. Gardez `_app.asar`.
   - **Linux** : dans le dossier de l'application Discord, par exemple `~/.config/discord/app-1.0.168/resources/` (Discord
     de la distribution récent ; prenez le numéro le plus élevé) ou `/opt/discord/resources/` :
     `cp ~/.config/discord/app-1.0.168/resources/_app.asar ~/.config/discord/app-1.0.168/resources/app.asar`
   - **Windows** : `%LOCALAPPDATA%\Discord\app-<version la plus élevée>\resources\`. Dans PowerShell :
     `Copy-Item "$env:LOCALAPPDATA\Discord\app-1.0.9999\resources\_app.asar" "$env:LOCALAPPDATA\Discord\app-1.0.9999\resources\app.asar"`
     (remplacez `1.0.9999` par votre version).
   - **macOS** : `/Applications/Discord.app/Contents/Resources/` :
     `cp /Applications/Discord.app/Contents/Resources/_app.asar /Applications/Discord.app/Contents/Resources/app.asar`
3. Rouvrez Discord : il démarre sans la traduction.

Pour remettre la traduction ensuite, rouvrez la fenêtre Corsu (ou relancez l'installeur avec Discord coché) quand une
version compatible est disponible. Si `_app.asar` est absent ou très petit (quelques centaines d'octets), ce n'est
pas l'archive d'origine : réinstallez Discord.
