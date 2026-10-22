# Hyprland et Noctalia

[English](../en/hyprland.md)

Corsu peut mettre en corse une session [Hyprland](https://hyprland.org) avec le panneau Noctalia, et, si vous le
demandez, y installer son propre profil de bureau. **Corsu n'installe jamais de bureau** : vous installez Hyprland,
Noctalia, uwsm et xdg-desktop-portal-hyprland avec votre distribution ; Corsu les détecte. Cette partie n'existe que
sous Linux. Statut : expérimental (voir [État réel](#état-réel)).

## État réel

Vérifié le 22 octobre 2026 sur CachyOS (Hyprland 0.56.2, Noctalia 5.3.0, uwsm 0.27.1, portail Hyprland 1.4.1),
portable Intel + NVIDIA RTX 5070 dont l'écran interne est relié à la NVIDIA :

- **Vrai Hyprland, session imbriquée** (Hyprland lancé dans un KWin virtuel sans écran, bus D-Bus privé, bus système
  masqué) : configuration chargée sans erreur, 66 raccourcis enregistrés, clavier `fr`, Noctalia démarré par
  l'autolancement, en corse (accueil, barre, menu de session, aide des touches `/tasti`). Captures ci-dessous.
- **Configuration validée** par `Hyprland --verify-config` et `noctalia config validate`.
- **Pas encore vérifié dans une vraie connexion** (écran réel, GPU réel) : portails (sélecteur de fichiers KDE,
  capture, partage d'écran), agent polkit, verrouillage et déverrouillage, KWallet à l'ouverture, réseau, Bluetooth,
  batterie, luminosité, veille et capot, touches AZERTY au clavier. Le partage d'écran demande un vrai essai dans
  Firefox, Discord ou OBS : lancer le programme ne suffit pas.
- Traduction de Noctalia : 3 126 textes ; 382 reprennent une traduction corse publiée, 267 l'usage existant de
  Corsu, 2 375 sont des propositions IA ; aucun texte relu par un locuteur
  ([PROVENANCE](../../src/hyprland/translations/PROVENANCE.md)).

| Accueil de Noctalia (choix « langue » seul) | Barre | Menu de session |
| --- | --- | --- |
| ![Accueil de Noctalia en corse](../images/hyprland/noctalia-welcome-co.png) | ![Barre de Noctalia](../images/hyprland/noctalia-bar-co.png) | ![Menu de session en corse](../images/hyprland/noctalia-session-co.png) |

Captures d'une session imbriquée 1280 × 720 sans réseau ni Bluetooth (bus système masqué) : sur un vrai écran, la
barre montre aussi réseau, Bluetooth, zone de notification et luminosité. Avec le profil, l'accueil ne s'ouvre pas
(`setup_wizard_enabled = false`) : il enregistrerait ses propres couleurs par-dessus celles de Corsu.

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

## Ce qui est coché d'avance, et pourquoi

- **La langue** n'est cochée d'avance que si Corsu trouve un Hyprland compatible **et** Noctalia 5 : comme pour les
  autres logiciels, Corsu traduit ce qui est déjà installé, et n'installe aucun bureau. Sinon elle reste proposée,
  décochée, ou grisée avec la raison.
- **Le profil** n'est jamais coché d'avance : c'est un choix de bureau, pas une traduction.
- **Le profil cache Noctalia du menu de Plasma** (une copie de son entrée avec `OnlyShowIn=Hyprland`) : lancé depuis
  Plasma, Noctalia ajouterait un second panneau par-dessus celui de Plasma. C'est le seul changement visible dans
  Plasma, dit aussi dans la description du profil ; il disparaît quand le profil est désactivé.

## Fichiers touchés

| Fichier | Partie | Comment |
| --- | --- | --- |
| `~/.config/uwsm/env-hyprland` | langue (bloc `language` : `LANGUAGE`, `NOCTALIA_ASSETS_DIR`), profil (bloc `profile` : thème Qt `qt6ct`, curseur, préfixe de menu, ordre des cartes graphiques si besoin) | deux blocs entre `# corsu:begin …` et `# corsu:end …` ; vos lignes autour restent |
| `~/.local/share/corsu/noctalia/assets/` | langue | dossier de Corsu : les ressources de Noctalia (liens) plus un `co.json` construit à chaque passage (le corse de Corsu là où le texte anglais n'a pas changé, sinon le français de Noctalia, puis l'anglais) ; gardé quand la langue est désactivée, car l'écran de verrouillage d'un Noctalia déjà lancé le relit |
| `~/.config/noctalia/00-corsu-language.toml` | langue | couche de Corsu (`lang = "co"`) ; une langue choisie dans la fenêtre Réglages de Noctalia l'emporte |
| `~/.config/noctalia/00-corsu-profile.toml`, `~/.config/noctalia/palettes/` | profil | couche d'apparence et palettes Corsu ; vos choix dans Réglages l'emportent |
| `~/.local/state/noctalia/settings.toml` | — | vos choix dans Réglages de Noctalia : jamais modifiés par Corsu |
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
  `installer.py --hyprland-reset-look`) : les palettes et la couche d'apparence de Corsu (`00-corsu-profile.toml`)
  reviennent, même modifiées (votre version est d'abord copiée dans `~/.local/share/corsu/backups/hyprland-reset/`).
  Ce que vous avez choisi dans la fenêtre Réglages de Noctalia n'est jamais modifié et l'emporte toujours : le bouton
  « Reset Page » de chaque page de Noctalia y revient à l'apparence Corsu. La langue, Hyprland et `user.lua` ne
  bougent pas.

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
