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
verdict, état des deux parties, constats : entrée de connexion, portails, cartes graphiques, qt6ct) et dans le menu texte (`app.py --text`). Sans Hyprland, les deux choix restent
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
| `~/.config/uwsm/env-hyprland` | langue (bloc `language` : `LANGUAGE`, `NOCTALIA_ASSETS_DIR`), profil (bloc `profile` : thème Qt `qt6ct`, curseur, préfixe de menu, ordre des cartes graphiques si besoin) | deux blocs entre `# corsu:begin …` et `# corsu:end …` ; vos lignes autour restent |
| `~/.local/share/corsu/noctalia/assets/` | langue | dossier de Corsu : les ressources de Noctalia (liens) plus un `co.json` construit à chaque passage (le corse de Corsu là où le texte anglais n'a pas changé, sinon le français de Noctalia, puis l'anglais) ; gardé quand la langue est désactivée, car l'écran de verrouillage d'un Noctalia déjà lancé le relit |
| `~/.config/noctalia/00-corsu-language.toml` | langue | couche de Corsu (`lang = "co"`) ; une langue choisie dans la fenêtre Réglages de Noctalia l'emporte |
| `~/.config/noctalia/00-corsu-profile.toml`, `~/.config/noctalia/palettes/` | profil | couche d'apparence et palettes Corsu ; vos choix dans Réglages l'emportent |
| `~/.local/state/noctalia/settings.toml` | — | vos choix dans Réglages de Noctalia : jamais modifiés, sauf par « Remettre l'apparence Corsu » (voir plus bas) |
| `~/.config/hypr/corsu/*.lua`, `machine.lua` | profil | fichiers de Corsu ; `machine.lua` vient de la détection (clavier, écrans et échelle) |
| `~/.config/hypr/hyprland.lua` | profil | écrit **seulement si vous n'en avez pas**, jamais réécrit ensuite ; le vôtre est gardé (ajoutez-y `require("corsu.init")`) |
| `~/.config/hypr/user.lua` | — | **jamais lu ni écrit** par Corsu : vos réglages vont là |
| `~/.config/xdg-desktop-portal/hyprland-portals.conf` | profil | lu seulement quand le bureau est Hyprland ; gardé s'il est à vous |
| `~/.config/qt6ct/qt6ct.conf` | profil | écrit seulement s'il n'existe pas ; lu seulement dans la session Hyprland |
| `~/.local/share/applications/dev.noctalia.Noctalia.desktop` | profil | copie de l'entrée de Noctalia avec `OnlyShowIn=Hyprland` : Noctalia n'apparaît plus dans le menu de Plasma (lancé là, il ajouterait un second panneau par-dessus Plasma) ; c'est le seul effet visible dans Plasma |

Choisissez à la connexion l'entrée **« Hyprland (uwsm-managed) »** : `env-hyprland` n'est lu qu'avec elle. Sans uwsm,
la langue de la session est « bloquée » avec cette explication.

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
  `installer.py --hyprland-reset-look`) : les palettes et la couche d'apparence de Corsu reviennent, et les choix
  d'apparence enregistrés par la fenêtre Réglages de Noctalia (thème, barre…) sont retirés ; vos autres réglages
  (langue, widgets, mise en veille, Hyprland, `user.lua`) ne bougent pas. Les fichiers modifiés sont d'abord copiés
  dans `~/.local/share/corsu/backups/hyprland-reset/`.

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
