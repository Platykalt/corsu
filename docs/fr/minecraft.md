# Minecraft en corse

[English](../en/minecraft.md)

Corsu ajoute la langue **Corsu (Corsica)** à **Minecraft: Java Edition 26.3**, sous forme de pack de ressources. Le
pack ne touche pas aux fichiers du jeu : on l'active et on le retire depuis le menu Packs de ressources.

| | |
| --- | --- |
| Édition | Java Edition seulement (Windows, macOS, Linux). Bedrock n'est pas pris en charge, voir plus bas. |
| Version | 26.3 (format de pack de ressources 97). Les autres versions affichent un avertissement « incompatible » ; voir « Autres versions ». |
| Fichier | `corsu-minecraft-java-26.3.zip`, dans les [versions publiées](https://github.com/Platykalt/corsu/releases/latest), ou construit avec `python3 tools/minecraft.py build` |
| Sources | [minecraft/java/co_fr.json](../../minecraft/java/co_fr.json), [glossaire](../../minecraft/java/glossary.tsv), [conventions](../../minecraft/java/STYLE.md), [inventaire des chaînes](../../minecraft/java/inventory.tsv) |
| État | Voir [minecraft/java/STATUS.md](../../minecraft/java/STATUS.md) : couverture, relecture et essais en jeu sont comptés séparément. |

Ce pack n'est pas un produit officiel Minecraft ; il n'est ni approuvé par Mojang ou Microsoft, ni associé à eux.

## Installer avec l'application Corsu (automatique)

Si Minecraft est installé, l'application Corsu propose **Minecraft**. Fermez Minecraft, cochez-le et installez :
Corsu copie le pack `corsu-minecraft-java.zip` dans le dossier `resourcepacks` de chaque dossier de jeu trouvé (le
lanceur officiel, et les instances de Prism Launcher et MultiMC), l'active, et met `lang:co_fr` dans `options.txt`.
Au prochain lancement, Minecraft est en corse. L'interrupteur de l'application remet la langue et les packs d'avant
sans toucher aux autres réglages du jeu ; désinstaller Corsu retire aussi le pack. Ligne de commande :
`python3 src/installer.py --components minecraft`.

## Installer à la main

1. Téléchargez `corsu-minecraft-java-26.3.zip`, sans le décompresser.
2. Dans Minecraft, ouvrez **Options… → Packs de ressources… → Ouvrir le dossier des packs**, et déposez-y le fichier.
3. Revenez dans le jeu : le pack apparaît à gauche. Cliquez sur la flèche pour le placer à droite, puis sur **Terminé**.
4. Ouvrez **Options… → Langue…** et choisissez **Corsu (Corsica)**, puis **Terminé**.

Le dossier des packs se trouve aussi directement ici : `%APPDATA%\.minecraft\resourcepacks` sous Windows,
`~/Library/Application Support/minecraft/resourcepacks` sous macOS, `~/.minecraft/resourcepacks` sous Linux (ou le
dossier de l'instance dans Prism Launcher, MultiMC…).

## Mettre à jour

Remplacez l'ancien fichier `corsu-minecraft-java-….zip` du dossier des packs par le nouveau, puis réactivez-le dans
**Packs de ressources** si le nom a changé. La langue choisie reste Corsu.

## Désinstaller

1. **Options… → Langue…** : choisissez une autre langue d'abord.
2. **Packs de ressources…** : retirez le pack Corsu (flèche vers la gauche), puis supprimez le fichier du dossier.

Si le pack est retiré alors que Corsu est encore la langue choisie, Minecraft revient à l'anglais.

## Ce qui est traduit, et ce qui ne l'est pas

Tout ce que Minecraft 26.3 tire de ses fichiers de langue : menus, réglages, commandes, blocs, objets, créatures,
biomes, effets, enchantements, progrès, statistiques, sous-titres, messages de mort, Realms, narrateur. Si une
chaîne manquait, le jeu afficherait l'anglais à sa place.

Trois cas différents :

- **Non conditionnables par langue** : les phrases d'accueil jaunes du menu (`texts/splashes.txt`), le poème de fin
  (`texts/end.txt`), le générique (`credits.json`, `postcredits.txt`). Un pack de ressources *peut* les remplacer,
  mais Minecraft n'en a qu'une version, lue quelle que soit la langue choisie : les remplacer les change pour toutes
  les langues. Corsu les traduit donc dans un **pack facultatif séparé** (voir plus bas), jamais dans le pack de langue.
- **Composant distinct, non couvert** : le lanceur Minecraft (Microsoft), traduit par Mojang sur Crowdin, où le corse
  est une langue cible mais n'est pas publié. Il ne fait pas partie du jeu et Corsu ne le modifie pas.
- **Hors du jeu de base** : les textes envoyés par un serveur, écrits dans un monde ou un livre, ou ajoutés par des
  mods et des packs de données.

## Pack facultatif : phrases d'accueil et poème de fin

`corsu-minecraft-java-texts-26.3.zip` (construit par `python3 tools/minecraft.py texts`) remplace les 454 phrases
d'accueil et le poème de fin par leur traduction corse. **Il les change pour toutes les langues**, puisque Minecraft
n'en lit qu'une version : ne l'activez que si cela vous convient, et retirez-le pour retrouver l'anglais. Corsu ne
l'installe jamais de lui-même. Le poème de fin est traduit du texte de Julian Gough, placé par lui sous CC0 ; les
phrases d'accueil traduisent un texte de Mojang. Choix et doutes : [minecraft/java/texts/NOTES.md](../../minecraft/java/texts/NOTES.md).

## Autres versions

Une version plus récente ou plus ancienne charge le pack après un avertissement. Les textes que Mojang a ajoutés
depuis restent en anglais, ceux qu'il a retirés sont ignorés. `python3 tools/minecraft.py diff 26.3 <version>` liste
les chaînes ajoutées, supprimées et modifiées, et `python3 tools/minecraft.py inventory <version>` marque « to review »
celles dont l'anglais a changé.

## Bedrock Edition

Bedrock accepte aussi une langue ajoutée par un pack global (`texts/languages.json`, `texts/language_names.json`,
`texts/co_FR.lang`), sous Windows, Android et iOS. Ce n'est pas encore fait : Bedrock a ses propres clés (environ
13 000 lignes) et ne réutilise pas les fichiers Java. Sur consoles, importer un pack est en général impossible, et
désactiver le pack alors que la langue est choisie fait planter le jeu.

## Tester en jeu

Vous avez Minecraft ? La marche à suivre et les écrans à vérifier : [Tester Minecraft en corse](minecraft-tester.md).

## Corriger une traduction

Les traductions sont dans `minecraft/java/co_fr.json` (une clé, un texte). Suivez [STYLE.md](../../minecraft/java/STYLE.md)
et le [glossaire](../../minecraft/java/glossary.tsv), puis lancez `python3 tools/minecraft.py check` : il vérifie
qu'aucune clé ne manque et que chaque `%s`, `%1$s`, code `§` et retour à la ligne est conservé. Ou
[ouvrez un ticket](https://github.com/Platykalt/corsu/issues/new?template=translation.yml) avec la clé ou le texte vu.
