# Tester le corse dans Minecraft Java

[English](../../minecraft/java/TESTING.md)

Seule la 26.3 a été lancée avec le pack, une fois, par le mainteneur : le journal du jeu montre le pack chargé, mais
personne n'a encore noté écran par écran ce qui s'affiche, et aucune autre version n'a été lancée
([état](../../minecraft/java/STATUS.md)). Si vous avez Minecraft: Java Edition, une heure passée sur les écrans
ci-dessous est l'aide la plus utile qui soit. Pas besoin de
parler corse pour repérer un texte qui déborde d'un bouton ou un reste d'anglais ; si vous le parlez, regardez aussi
les mots.

## Parcours court (20 minutes)

Notez pour chaque étape « ok » ou ce qui ne va pas, avec une capture (F2).

1. **Installation** : fermez Minecraft, ouvrez l'application Corsu, cochez Minecraft, installez. Le journal liste
   chaque dossier de jeu : « Minecraft en corse » ou « laissé tel quel » avec la raison (version, jeu lancé…).
   Vérifiez que la raison est juste.
2. **Langue** : lancez Minecraft 26.3. Le jeu doit déjà être en corse. Dans **Ozzioni… → Lingua…**, « Corsu
   (Corsica) » doit apparaître et être sélectionnée ; les autres langues sont toujours là.
3. **Menu principal et options** : chaque bouton de l'écran titre, puis Ozzioni et ses sous-écrans (vidéo, sons,
   commandes, accessibilité). Survolez quelques options pour lire leur infobulle.
4. **Inventaire et textes avec paramètres** : créez un monde créatif, survolez des objets (livre enchanté, potion,
   œuf, laine de couleur) ; tapez `/give @s diamond 5` puis `/give @s blabla` pour voir un message de réussite et un
   message d'erreur ; mourez une fois (chute) pour lire le message de mort avec votre nom.
5. **Caractères et place** : les lettres à, è, ì, ò, ù et les apostrophes s'affichent ; aucun texte ne déborde d'un
   bouton ni n'est coupé ; tout est lisible à la taille d'interface habituelle.
6. **Désactivation** : fermez Minecraft, mettez l'interrupteur Minecraft de l'application Corsu sur « arrêt »,
   relancez : la langue d'avant revient, vos autres packs sont toujours actifs et dans le même ordre, vos réglages
   (champ de vision, touches…) n'ont pas changé. Réactivez : le corse revient.
7. **Autre version** : Corsu fait un pack pour chaque version stable de 1.6.1 à 26.3. Créez une instance Prism
   Launcher d'une version plus ancienne (par exemple 1.21.1, 1.16.5, 1.12.2 ou 1.8.9), lancez-la une fois, fermez-la,
   lancez Corsu, relancez-la : les menus sont en corse (de 1.6 à 1.10 aussi, la langue s'appelle « Corsu (Corsica) »).
   Ces textes anciens sont les moins essayés : regardez l'écran titre, les options et l'infobulle d'un objet, et notez
   tout reste d'anglais ou texte coupé. Une instance que Corsu a « laissée telle quelle » doit être inchangée.

## 1. Installer

1. Choisissez une version stable de **Minecraft: Java Edition** entre 1.6.1 et 26.3 (dans le lanceur :
   Configurations → Nouvelle → version). Prenez le pack de cette version : le pack d'une autre version peut être
   refusé ou laisser des textes en anglais.
2. Le plus simple : l'application Corsu fait les étapes 3 et 4 avec le bon pack (Minecraft fermé). À la main :
   `corsu-minecraft-java-26.3.zip` est dans la [dernière version](https://github.com/Platykalt/corsu/releases/latest)
   (26.3 seulement) ; pour une autre version, construisez-le depuis une copie du dépôt :
   `python3 tools/mcversions.py build <version>`. Ne le décompressez pas.
3. Dans le jeu : **Options… → Packs de ressources… → Ouvrir le dossier des packs**, déposez-y le zip, revenez, passez
   le pack dans la colonne de droite avec sa flèche, puis **Terminé**.
4. **Options… → Langue…**, choisissez **Corsu (Corsica)**, puis **Terminé**.

Pour essayer vos propres corrections en direct : décompressez le pack dans un dossier de `resourcepacks/`, modifiez
`assets/minecraft/lang/co_fr.json`, puis appuyez sur **F3 + T** dans le jeu pour recharger les ressources.

## 2. Écrans à vérifier

Faites une capture (F2) de tout ce qui cloche ; elles sont dans `.minecraft/screenshots`.

1. **Écran titre** : chaque bouton, l'infobulle du bouton de langue, la ligne de copyright.
2. **Options** et chaque sous-écran : Personnalisation du skin, Musique et sons, Paramètres vidéo (curseurs
   *Distance d'affichage*, *Distance de simulation*, *Taille de l'interface*…), Commandes → Souris et Touches
   (faites défiler toute la liste), Chat, Accessibilité, En ligne, Télémétrie, Crédits. Survolez chaque option pour
   lire son infobulle.
3. **Liste des langues** : Corsu (Corsica) apparaît, bien rangé ; rien d'autre n'a changé.
4. **Créer un nouveau monde** : onglets Jeu, Monde et Plus ; faites défiler *Mode de jeu* (Survie, Hardcore, Créatif)
   et *Difficulté* et lisez les descriptions ; le champ *Graine* et son indication ; *Règles du jeu* (toutes les
   catégories) ; *Packs de données* et *Expériences*.
5. **Inventaire et onglets du mode créatif** : ouvrez chaque onglet, survolez beaucoup d'objets (outils, livres
   enchantés, potions et flèches à effet, œufs d'apparition, laine et béton de couleur, bannières, garnitures
   d'armure, tessons de poterie, disques). Essayez une fois F3 + H (infobulles avancées).
6. **Fabrication** : établi et livre de recettes (recherche, bouton de filtre), fourneau, enclume (renommer), table
   d'enchantement, meule, table de forgeron, tailleur de pierre, métier à tisser, alambic, écran de commerce d'un
   villageois (noms des niveaux).
7. **Écran de débogage F3**, et F3 + Q (liste des raccourcis).
8. **Écran de mort** : mourez une fois (et dans un monde Hardcore si possible), lisez le message de mort dans le chat.
9. **Chat et commandes** : tapez `/` et parcourez les suggestions ; essayez des commandes qui échouent exprès, par
   exemple `/give @s rien`, `/give @s stone 99999`, `/tp personne`, `/gamerule`, `/seed`, `/time set day`,
   `/effect give @s minecraft:speed`, `/locate structure village_plains`.
10. **Progrès** (touche L) : chaque onglet, titres et descriptions ; obtenez un progrès pour voir sa notification.
11. **Sous-titres** : Musique et sons → *Sous-titres* activés, puis promenez-vous près d'animaux, ouvrez portes et
    coffres, approchez l'eau, la lave et une grotte.
12. **Realms** : le bouton *Minecraft Realms* de l'écran titre (l'accueil et l'écran d'achat s'affichent sans
    abonnement), et **Multijoueur** : liste des serveurs, Ajouter un serveur, Connexion directe, et *Ouvrir au
    réseau local* dans le menu pause.

## 3. Ce qu'il faut regarder

- **Débordement** : le corse est souvent plus long que l'anglais. Un texte qui dépasse d'un bouton, d'un curseur ou
  d'une infobulle, coupé par « … », ou qui en chevauche un autre. Notez l'écran, la taille de fenêtre et la taille
  de l'interface.
- **Anglais restant**, ou une clé brute comme `item.minecraft.foo`, ou un `%s` / `%1$s` visible.
- **Mauvais sens** : un mot qui traduit l'anglais au pied de la lettre mais veut dire autre chose dans le jeu (une
  créature dont le nom ressemble à un objet, un réglage qui dit le contraire de ce qu'il fait…).
- **Grammaire** : genre et nombre (*a lana rossa*, *i blocchi rossi*), élision (*l'ogettu*, *d'un*), négation
  (*ùn … micca*).
- **Incohérence** : une même chose avec deux noms selon l'écran.
- Les mots qu'un locuteur n'emploierait jamais. Les termes incertains sont listés dans
  [review.md](../../minecraft/java/review.md) et [decisions.md](../../minecraft/java/decisions.md) : votre avis sur
  ceux-là est particulièrement précieux.

## 4. Trouver la clé d'un texte

Chaque texte a une clé dans [co_fr.json](../../minecraft/java/co_fr.json) (une ligne par clé, par exemple
`"gui.done": "Fattu"`) :

- Sur GitHub, ouvrez [co_fr.json](https://github.com/Platykalt/corsu/blob/main/minecraft/java/co_fr.json) (ou sa
  version **Raw**) et cherchez le texte corse exact avec Ctrl+F dans le navigateur. S'il contient un nom ou un nombre,
  cherchez seulement la partie fixe (le reste est un `%s`).
- Si plusieurs clés ont le même texte, passez le jeu en anglais, notez le texte anglais et cherchez-le dans le
  fichier `en_us.json` de Mojang (`python3 tools/minecraft.py fetch 26.3` le place dans
  `~/.cache/corsu/minecraft/26.3/`) ; la clé à côté est celle à signaler.
- Ne pas trouver la clé n'est pas grave : l'écran et le texte vu suffisent.

## 5. Signaler

Ouvrez un ticket avec le modèle **Traduction** :
<https://github.com/Platykalt/corsu/issues/new?template=translation.yml>

- **Texte vu** : copiez-le exactement.
- **Où** : « Minecraft Java » + la version (par exemple 26.3 ou 1.12.2) + l'écran (par exemple *Options → Paramètres vidéo, curseur Distance d'affichage*).
- **Clé** : si vous l'avez trouvée.
- **Corse proposé** : facultatif.
- **Remarques** : ce qui ne va pas (débordement, sens, anglais restant…), et joignez
  la capture.

Un ticket par problème est le plus simple à suivre. Pour un écran entier sans souci, un petit « écran X vérifié,
rien à signaler » est utile aussi : il permet de marquer ces clés `ok` dans la colonne `in_game` (et seulement celle-là : un essai d'affichage ne vaut pas relecture de la langue) de
[inventory.tsv](../../minecraft/java/inventory.tsv).
