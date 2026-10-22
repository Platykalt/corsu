# Hyprland et Noctalia

[English](../en/hyprland.md)

Corsu peut mettre en corse une session [Hyprland](https://hyprland.org) avec le panneau Noctalia, et, si vous le
demandez, y installer son propre profil de bureau. **Corsu n'installe jamais de bureau** : vous installez Hyprland,
Noctalia, uwsm et xdg-desktop-portal-hyprland avec votre distribution ; Corsu les détecte. Cette partie n'existe que
sous Linux et n'a encore été essayée que sur des dossiers simulés (aucun vrai Hyprland ne l'a lancée).

## Ce qu'il faut

| Logiciel | Version | Pourquoi |
| --- | --- | --- |
| Hyprland | 0.55 ou plus récent | la configuration en Lua, que le profil utilise |
| Noctalia | 5.x | ses réglages TOML et ses catalogues JSON |
| uwsm | toute version | la langue de la session passe par `~/.config/uwsm/env-hyprland`, que seul uwsm lit |
| xdg-desktop-portal-hyprland | toute version | les portails (captures, partage d'écran) de la session Hyprland |

Corsu dit ce qu'il trouve : dans la fenêtre (page « Ajouter »), dans `corsu.py status` (rubrique `hyprland` : versions,
verdict, état des deux parties) et dans le menu texte (`app.py --text`). Sans Hyprland, les deux choix restent
affichés, grisés, avec la raison ; avec un Hyprland trop ancien, ils sont « bloqués » avec la version demandée.

## Deux choix séparés

- **Hyprland et Noctalia** (`hyprland`, la langue) : le catalogue corse de Corsu pour Noctalia et sa langue réglée
  sur le corse ; dans la session Hyprland, le corse d'abord pour les programmes, puis vos langues et l'anglais pour
  ce qui n'est pas encore traduit (`LANGUAGE=co:fr_FR:en` par exemple). Rien de visuel ne change.
- **Profil de bureau Corsu pour Hyprland** (`hyprland-profile`), **jamais coché d'avance** : des modules Lua prêts
  (touches, fenêtres, entrée), les portails de la session Hyprland et l'apparence Corsu pour Noctalia (palette
  maquis et mer). On peut prendre la langue sans le profil, ou le profil sans la langue.

## Fichiers touchés

| Fichier | Partie | Comment |
| --- | --- | --- |
| `~/.config/uwsm/env-hyprland` | langue (bloc `language`), profil (bloc `profile`) | un bloc entre `# corsu:begin …` et `# corsu:end …` ; vos lignes autour restent |
| `~/.local/share/noctalia/translations/co.json` | langue | fichier de Corsu |
| `~/.config/noctalia/settings.toml` | langue (`language`), profil (réglages d'apparence) | une valeur à la fois, l'ancienne gardée |
| `~/.config/hypr/corsu/*.lua`, `machine.lua` | profil | fichiers de Corsu ; `machine.lua` vient de la détection (clavier, échelle, carte graphique) |
| `~/.config/hypr/hyprland.lua` | profil | écrit **seulement si vous n'en avez pas** ; le vôtre est gardé |
| `~/.config/hypr/user.lua` | — | **jamais lu ni écrit** par Corsu : vos réglages vont là |
| `~/.config/xdg-desktop-portal/hyprland-portals.conf` | profil | lu seulement quand le bureau est Hyprland ; gardé s'il est à vous |
| `~/.config/noctalia/colorschemes/` | profil | la palette Corsu |

Plasma n'est pas touché : aucune variable globale, aucun fichier système, et ni `kdeglobals`, ni
`gtk-3.0/settings.ini`, ni `gtk-4.0`, ni `mimeapps.list`, ni `plasma-workspace/env/corsu.sh` (les essais le
vérifient octet par octet).

## Activer, désactiver, mettre à jour

- **Activer deux fois n'ajoute rien** : chaque fichier est suivi dans `installation.json` avec son empreinte, chaque bloc
  et chaque valeur avec la valeur d'avant.
- **Désactiver** rend seulement ce qui est encore à Corsu : un bloc modifié par vous, une valeur changée dans
  Noctalia, un fichier édité restent tels quels ; un fichier existant avant Corsu revient octet par octet ; un fichier
  que Corsu avait créé disparaît. Désactiver le profil retire le `hyprland.lua` que Corsu avait écrit : Hyprland
  reprend alors sa configuration par défaut. Déconnectez-vous de la session Hyprland puis reconnectez-vous.
- **Mises à jour et réparations** gardent vos réglages : ce que vous avez changé dans Noctalia, `user.lua`, et tout
  fichier de Corsu que vous avez modifié (il est laissé tel quel, avec un message dans la fenêtre et le journal) ;
  les fichiers inchangés reçoivent la nouvelle version.
- **Remettre l'apparence Corsu** (bouton du profil dans la fenêtre, `r` dans le menu texte, ou
  `installer.py --hyprland-reset-look`) : la palette et les réglages d'apparence du profil reviennent ; vos autres
  réglages Noctalia, la langue, Hyprland et `user.lua` ne bougent pas. Une palette que vous aviez modifiée est
  d'abord copiée dans `~/.local/share/corsu/backups/hyprland-reset/`.

## En ligne de commande

```sh
python3 src/installer.py --components hyprland                    # la langue seule
python3 src/installer.py --components hyprland hyprland-profile   # la langue et le profil
python3 src/installer.py --disable hyprland-profile               # retirer le profil, garder la langue
python3 src/installer.py --hyprland-reset-look
python3 src/corsu.py status                                       # rubrique "hyprland"
```

Une première installation sans liste (`--yes`) ne prend jamais le profil ; une mise à jour garde les parties déjà
choisies, activées ou non.
