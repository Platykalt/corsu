# Minecraft Bedrock en corse : prototype et protocole d'essai

**Expérimental, jamais essayé en jeu.** Ce pack n'est pas une partie prise en charge de Corsu : il n'est ni dans
l'application d'installation ni dans le pack Java, et rien ne garantit qu'il fonctionne. État détaillé et sources :
[minecraft/bedrock/STATUS.md](../../minecraft/bedrock/STATUS.md) et [STUDY.md](../../minecraft/bedrock/STUDY.md).
CE PACK N'EST PAS UN PRODUIT OFFICIEL MINECRAFT ; IL N'EST NI APPROUVÉ PAR MOJANG OU MICROSOFT, NI ASSOCIÉ À EUX.

## Ce que c'est

Un pack de ressources **global** qui ajoute une langue « Corsu (Corsica) » (code `co_FR`) à Minecraft Bedrock 26.50
(Windows, Android, iOS). Il contient 4 272 des 13 340 textes du jeu, tous repris de la traduction Java de Corsu quand
le texte anglais est identique et que le sens est le même (noms de blocs, d'objets, de créatures, sous-titres, messages
de mort, une partie des options). Le reste n'est pas traduit : on ne sait pas encore si le jeu affichera l'anglais ou
la clé brute (`menu.play`) ; c'est la première chose à observer. Aucun de ces textes n'a été relu par un locuteur.

Consoles (Xbox, PlayStation, Switch) : impossible, elles n'acceptent pas les packs importés.

## Fabriquer le pack

```sh
python3 tools/bedrock.py fetch   # télécharge en_US.lang de Mojang (bedrock-samples v1.26.50.4) dans ~/.cache/corsu
python3 tools/bedrock.py check   # 0 erreur attendue ; code de sortie 1 sinon
python3 tools/bedrock.py build   # écrit dist/corsu-minecraft-bedrock-v1.26.50.4.mcpack et affiche son SHA-256
```

Le fichier de Mojang sert seulement aux vérifications ; il n'entre ni dans le dépôt ni dans le pack.

## Protocole d'essai (30 minutes)

Prévoir un appareil où un plantage du jeu ne coûte rien, et noter pour chaque étape « ok » ou ce qui se passe, avec
une capture, la plateforme et la version exacte du jeu (écran titre, en bas).

### 1. Importer

- **Windows** : double-cliquer sur le fichier `.mcpack`. Minecraft s'ouvre.
- **Android** : ouvrir le fichier depuis le gestionnaire de fichiers ou le téléchargement, choisir Minecraft.
- **iOS / iPadOS** : dans l'app Fichiers, toucher le fichier, puis « Ouvrir dans Minecraft » (ou Partager → Minecraft).

Attendu : un message d'import réussi (« Successfully imported "Corsu (lingua corsa)" »). Noter tout message d'erreur
mot pour mot.

### 2. Activer le pack et choisir la langue

1. Paramètres → **Ressources globales** : dans « Mes packs », activer « Corsu (lingua corsa) ».
2. Paramètres → **Langue** : « Corsu (Corsica) » doit figurer dans la liste, **et toutes les autres langues aussi**.
   La choisir.

### 3. Ce qu'il faut regarder

| Où | Attendu en corse | Attendu en anglais (non traduit) |
| --- | --- | --- |
| Écran titre | — | Play, Settings… : noter si c'est l'anglais ou des clés comme `menu.play` |
| Paramètres | « Ozzioni », Difficultà, Campu visivu, Lingua | la plupart des autres réglages |
| Créer un monde | Creà un mondu novu, Creativu, Sopravivenza | le reste de l'écran |
| Inventaire créatif | Terra, Troncu di querciu, Bancu di fabbricazione, Cascia, Diamante, Spada di diamante, Mela, Pane, Arcu, Pozione di cura, Libru incantatu | noms des onglets |
| Créatures (œufs ou rencontre) | Zombi, Vacca, Paisanu | — |
| Sous-titres activés, près d'un zombi | « Zombi si lamenta » | — |
| Mort par chute | « <votre nom> hà toccu terra troppu forte » (le nom bien placé) | — |
| Comment jouer | — | tout : noter anglais ou clés brutes |

Noter aussi : lettres à, è, ì, ò, ù et apostrophes bien affichées ; un texte qui déborde ou qui est coupé ; un espace
ou un signe en trop en fin de texte ; un plantage.

### 4. Retirer le pack et rendre la langue

Toujours dans cet ordre :

1. Paramètres → Langue : revenir à la langue d'avant (par exemple Français (France)).
2. Paramètres → Ressources globales : désactiver « Corsu (lingua corsa) ».
3. Pour le supprimer : Paramètres → Stockage → Packs de ressources → « Corsu (lingua corsa) » → Supprimer.
4. Relancer le jeu : la langue d'avant doit être là, les mondes et les autres packs inchangés.

La documentation communautaire ([wiki.bedrock.dev](https://wiki.bedrock.dev/text/text-intro)) dit que le jeu plante si
l'on désactive le pack **avant** de changer de langue. Ce n'est pas vérifié. Ne l'essayer volontairement que sur un
appareil de test, après avoir fait l'essai normal, et noter ce qui se passe au relancement (langue rétablie ? plantage
à chaque démarrage ?). Si le jeu ne démarre plus, réimporter le pack, choisir une autre langue, puis le retirer dans
l'ordre ci-dessus.

### 5. Rapporter

Plateforme, version du jeu, date, et le résultat de chaque étape, à reporter dans
[STATUS.md](../../minecraft/bedrock/STATUS.md) (§ 4 liste les questions ouvertes). Tant que ce n'est pas fait, le pack
reste un prototype.
