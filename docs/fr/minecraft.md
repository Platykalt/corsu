# Minecraft en corse

[English](../en/minecraft.md)

Corsu ajoute la langue **Corsu (Corsica)** à **Minecraft: Java Edition**, sous forme de pack de ressources fait pour
chaque version. Le pack ne touche pas aux fichiers du jeu : on l'active et on le retire depuis le menu Packs de
ressources.

<!-- corsu:minecraft-summary:start -->
**Minecraft Java en corse pour 87 versions** (versions stables 1.6.1 → 26.3). Traduction complète des fichiers de langue pour les versions listées ; vérifications techniques avec le code de chaque version.

| | |
| --- | --- |
| Versions | les 87 versions stables de Java Edition de 1.6.1 à 26.3 ([liste et résultat par version](../../minecraft/java/COMPATIBILITY.md)). |
| Traduction | chaque texte non vide des fichiers de langue de chaque version listée a son texte corse : de 1 353 textes (1.6.1) à 8 557 (26.3). Une seule traduction : celle de 26.3 (8 557 textes) sert partout où la clé et son anglais sont les mêmes ; 3 978 textes anciens différents ont leur propre entrée (507 repris, 1 755 clés renommées, 482 adaptés, 1 234 nouveaux). |
| Vérifications techniques | le 2026-10-18, pour chaque version : règles Python sur chaque texte (arguments, codes `§`, formats du fichier et de pack.mcmeta), puis le code du jeu de cette version (son propre fichier client, SHA-1 vérifié) a chargé le fichier de langue et affiché chaque texte : 0 problème (2 ou 3 textes par version non affichés car leur anglais lui-même ne se formate pas). Exceptions : composants de texte (chat, progrès) avant 26.1 : règle Python seulement ; section `pack` de pack.mcmeta en 1.21.1 : non lue par le code du jeu ; code de langue de la section `language` à partir de 1.20 : vérifié en Python ; l'affichage à l'écran et l'écran des packs ne sont pas vérifiés ([détail](../../minecraft/java/MULTIVERSION.md), [par version](../../minecraft/java/COMPATIBILITY.md)). Ce n'est ni une relecture par un locuteur ni une vérification visuelle de chaque écran. |
| Relecture | textes écrits par IA ; deuxième passe IA sur un échantillon de 150 entrées des 3 978 textes anciens (pas sur tous) ; relecture par un locuteur : 0. |
| En jeu | seule la 26.3 a été lancée avec le pack, sur l'instance Prism Launcher du mainteneur (2026-10-16) : le journal du jeu montre le pack chargé et des messages en corse. Aucune vérification visuelle clé par clé n'est enregistrée : c'est pourquoi [STATUS.md](../../minecraft/java/STATUS.md) compte « vu en jeu : 0 ». Les autres versions n'ont pas été lancées. |
| Disponibilité | dans les versions publiées de Corsu à partir de 0.23.0. |
| Hors champ | les fichiers de langue du jeu seulement : pas les mods, les serveurs ni le lanceur ; phrases d'accueil et poème de fin : pack facultatif séparé. Pas les snapshots, pré-versions ni release candidates, pas Bedrock, rien avant 1.6.1 (pas de packs de ressources). |

**Obtenir et activer le bon pack**

1. Fermez Minecraft.
2. Dans l'application Corsu (une version qui contient ces packs), cochez **Minecraft** et installez. Corsu lit la version jouée par chaque dossier de jeu (lanceur officiel, Prism Launcher, MultiMC, y compris sous Fabric, Forge, Quilt ou NeoForge), y copie le pack de cette version et choisit le corse.
3. Lancez le jeu : **Options… → Langue…** montre **Corsu (Corsica)**, déjà choisie.

Développeurs, depuis une copie de main : `python3 tools/mcversions.py build <version>` écrit `dist/corsu-minecraft-java-<version>.zip` ; déposez-le dans le dossier `resourcepacks` de cette version, activez-le dans **Packs de ressources…**, puis choisissez **Corsu (Corsica)** dans **Langue…**.
<!-- corsu:minecraft-summary:end -->

| | |
| --- | --- |
| Sources | [co_fr.json](../../minecraft/java/co_fr.json) (traduction de 26.3, la base), [history.json](../../minecraft/java/history.json) (textes des versions plus anciennes), [glossaire](../../minecraft/java/glossary.tsv), [conventions](../../minecraft/java/STYLE.md) |
| État | [STATUS.md](../../minecraft/java/STATUS.md) : traduction, relecture IA, relecture humaine et essais en jeu sont comptés séparément. |

Ce pack n'est pas un produit officiel Minecraft ; il n'est ni approuvé par Mojang ou Microsoft, ni associé à eux.

## Installer avec l'application Corsu (automatique)

Si Minecraft est installé, l'application Corsu propose **Minecraft**. Fermez Minecraft, cochez-le et installez :
Corsu cherche les dossiers de jeu (le lanceur officiel, et les instances de Prism Launcher et MultiMC) et la version
que chacun joue : la version de l'instance, ou celle du dernier profil utilisé dans le lanceur officiel, y compris
sous Fabric, Forge, Quilt ou NeoForge. Dans chaque dossier qui joue une version listée, il copie le pack de cette
version sous le nom `corsu-minecraft-java.zip`, l'ajoute après vos autres packs et met la langue corse dans
`options.txt` (`co_fr`, ou `co_FR` jusqu'à 1.10.2). Il laisse tels quels, en disant pourquoi, les dossiers d'une
version non listée ou inconnue, ceux où Minecraft est lancé, un `options.txt` qu'il ne peut pas relire sans risque,
et un autre fichier qui porterait déjà le nom du pack.
Au prochain lancement, Minecraft est en corse. L'interrupteur de l'application remet la langue et les packs d'avant
sans toucher aux autres réglages du jeu ; désinstaller Corsu retire aussi le pack. Ligne de commande :
`python3 src/installer.py --components minecraft`.

## Installer à la main

1. Prenez le pack de **votre** version : `corsu-minecraft-java-26.3.zip` est dans les
   [versions publiées](https://github.com/Platykalt/corsu/releases/latest) (26.3 seulement) ; pour une autre version
   listée, construisez-le depuis une copie de ce dépôt : `python3 tools/mcversions.py build <version>`, qui écrit
   `dist/corsu-minecraft-java-<version>.zip`. Ne le décompressez pas.
2. Dans Minecraft, ouvrez **Options… → Packs de ressources… → Ouvrir le dossier des packs**, et déposez-y le fichier.
3. Revenez dans le jeu : le pack apparaît à gauche. Cliquez sur la flèche pour le placer à droite, puis sur **Terminé**.
4. Ouvrez **Options… → Langue…** et choisissez **Corsu (Corsica)**, puis **Terminé**.

Le dossier des packs se trouve aussi directement ici : `%APPDATA%\.minecraft\resourcepacks` sous Windows,
`~/Library/Application Support/minecraft/resourcepacks` sous macOS, `~/.minecraft/resourcepacks` sous Linux (ou le
dossier de l'instance dans Prism Launcher, MultiMC…).

## Mettre à jour

Avec l'application Corsu : relancez l'installation, Minecraft fermé ; si une instance a changé de version, Corsu y
met le pack de la nouvelle version. À la main : remplacez l'ancien fichier `corsu-minecraft-java-….zip` du dossier des
packs par le nouveau, puis réactivez-le dans **Packs de ressources** si le nom a changé. La langue choisie reste Corsu.

## Désinstaller

1. **Options… → Langue…** : choisissez une autre langue d'abord.
2. **Packs de ressources…** : retirez le pack Corsu (flèche vers la gauche), puis supprimez le fichier du dossier.

Si le pack est retiré alors que Corsu est encore la langue choisie, Minecraft revient à l'anglais.

## Ce qui est traduit, et ce qui ne l'est pas

Tout ce que chaque version listée tire de ses fichiers de langue : menus, réglages, commandes, blocs, objets,
créatures, biomes, effets, enchantements, progrès (ou succès dans les anciennes versions), statistiques, sous-titres,
messages de mort, Realms, narrateur. Si une chaîne manquait, le jeu afficherait l'anglais à sa place.

Trois cas différents :

- **Non conditionnables par langue** : les phrases d'accueil jaunes du menu (`texts/splashes.txt`), le poème de fin
  (`texts/end.txt`), le générique (`credits.json`, `postcredits.txt`). Un pack de ressources *peut* les remplacer,
  mais Minecraft n'en a qu'une version, lue quelle que soit la langue choisie : les remplacer les change pour toutes
  les langues. Corsu les traduit donc dans un **pack facultatif séparé** (voir plus bas), jamais dans le pack de langue.
- **Composant distinct, non couvert** : le lanceur Minecraft (Microsoft), traduit par Mojang sur Crowdin, où le corse
  est une langue cible mais n'est pas publié. Il ne fait pas partie du jeu et Corsu ne le modifie pas.
- **Hors du jeu de base** : les textes envoyés par un serveur, écrits dans un monde ou un livre, ou ajoutés par des
  mods et des packs de données.

## Pack facultatif : phrases d'accueil et poème de fin (26.3)

`corsu-minecraft-java-texts-26.3.zip` (construit par `python3 tools/minecraft.py texts`) remplace les 454 phrases
d'accueil et le poème de fin de la 26.3 par leur traduction corse. **Il les change pour toutes les langues**, puisque
Minecraft n'en lit qu'une version : ne l'activez que si cela vous convient, et retirez-le pour retrouver l'anglais.
Corsu ne l'installe jamais de lui-même. Le poème de fin est traduit du texte de Julian Gough, placé par lui sous CC0 ;
les phrases d'accueil traduisent un texte de Mojang. Choix et doutes :
[minecraft/java/texts/NOTES.md](../../minecraft/java/texts/NOTES.md).

## Autres versions

Les snapshots, pré-versions et release candidates, et les versions avant 1.6.1 (sans packs de ressources), n'ont pas
de pack : l'application laisse ces dossiers tels quels ([liste](../../minecraft/java/other-versions.md)). Le pack d'une
version, chargé dans une autre, peut s'afficher « incompatible » ; les textes que Mojang a changés entre les deux restent en
anglais ou sont ignorés. Prenez toujours le pack de votre version.

## Bedrock Edition

Bedrock accepte aussi une langue ajoutée par un pack global (`texts/languages.json`, `texts/language_names.json`,
`texts/co_FR.lang`), sous Windows, Android et iOS. Ce n'est pas encore fait : Bedrock a ses propres clés (environ
13 000 lignes) et ne réutilise pas les fichiers Java. Sur consoles, importer un pack est en général impossible, et
désactiver le pack alors que la langue est choisie fait planter le jeu.

## Tester en jeu

Vous avez Minecraft ? La marche à suivre et les écrans à vérifier : [Tester Minecraft en corse](minecraft-tester.md).

## Corriger une traduction

Les textes de la 26.3 sont dans `minecraft/java/co_fr.json` (une clé, un texte) ; ceux des versions plus anciennes,
quand leur anglais diffère, dans `minecraft/java/history.json`. Une correction faite sur un texte partagé vaut pour
toutes les versions qui affichent ce même anglais. Suivez [STYLE.md](../../minecraft/java/STYLE.md) et le
[glossaire](../../minecraft/java/glossary.tsv), puis lancez `python3 tools/minecraft.py check` et
`python3 tools/mchistory.py check` : ils vérifient qu'aucune clé ne manque et que chaque `%s`, `%1$s`, code `§` et
retour à la ligne est conservé. Ou [ouvrez un ticket](https://github.com/Platykalt/corsu/issues/new?template=translation.yml)
avec la version, la clé ou le texte vu.
