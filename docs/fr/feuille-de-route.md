# Feuille de route

[English](../en/roadmap.md)

Ce qui suit est **prévu ou envisagé**, pas disponible. Ce qui marche aujourd'hui est dans
[Ce qui marche, et où](compatibilite.md). État établi le 16 octobre 2026.

## Ce qui existe déjà en corse ailleurs

La plupart de ces traductions sont l'œuvre de Patriccollu di Santa Maria è Sichè. Sa liste fait référence :
[Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica) (47 logiciels traduits, 3 en
attente de publication, 3 en cours). Corsu en reprend une partie dans `lexicon/` (voir `tools/import_translations.py`).
Les pourcentages viennent des API de Pontoon et de Hosted Weblate ; les autres projets n'en publient pas sans compte.

| Logiciel | Où vit la traduction | État constaté | Repris par Corsu |
| --- | --- | --- | --- |
| Firefox pour Android | Pontoon | 2 533 chaînes approuvées sur 2 548 | oui (lexique) |
| Firefox pour iOS, Focus Android et iOS, Mozilla VPN | Pontoon | 91 à 100 % | oui |
| **Firefox de bureau, Thunderbird de bureau** | — | **aucun corse chez Mozilla** (pas de paquet `co`) | Corsu fournit sa propre traduction de Firefox |
| Thunderbird pour Android | Hosted Weblate | 92,8 % | oui |
| Tenacity | Hosted Weblate | 98,4 % | oui |
| OpenTracks | Hosted Weblate | 76,1 % | oui |
| Notepad++, WinMerge | dépôt du projet | à jour (WinMerge revu le 6 octobre 2026) | oui |
| Poedit, HandBrake, Audacity | Crowdin / Transifex / dépôt | publiés | oui |
| VLC (bureau) | Transifex | partiel, dernière révision 2017 | oui |
| VeraCrypt, SumatraPDF, PDFsam, FileZilla | dépôt du projet | publiés | non : déjà en corse dans le logiciel |
| 7-Zip, Inno Setup, NSIS, Paint.NET, Mp3tag, OmegaT… | selon le projet | listés par Patriccollu, non vérifiés ici | non |
| CCleaner, Video DownloadHelper | — | abandonnés (plus maintenu / corse retiré) | non |
| LibreOffice, GIMP, Inkscape, KeePassXC, F-Droid, OsmAnd, Luanti | — | pas de corse trouvé | non |

## Prochains chantiers, par ordre

### Réalisables tout de suite

| Chantier | Bénéfice | Solution | Preuve de faisabilité | Volume estimé (méthode) | Effort | Maintenance | Prochaine action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minecraft Java : relecture | traduction fiable du jeu le plus joué | relecture par un locuteur, clé par clé, statut dans `inventory.tsv` | traduction complète livrée (26.3) | 8 559 chaînes (`en_us.json` 26.3) | élevé | faible | relire d'abord interface, objets, blocs |
| Minecraft Java : essai en jeu | preuve que le pack se charge | lancer 26.3 avec le pack, parcourir menus, inventaire, mort, sous-titres | mécanisme lu dans le code de 26.3 | 1 parcours | faible | à chaque version | essai par quelqu'un qui possède le jeu |
| Minecraft Java : versions suivantes | suivre Mojang | `tools/minecraft.py diff` puis `inventory` | outil livré | 26.2 → 26.3 : 436 chaînes ajoutées, 56 modifiées (`tools/minecraft.py diff`) | faible | régulier | lancer `diff 26.3 26.4` à la sortie |
| Discord : relecture des libellés courts | corriger les contresens visibles | relecture sémantique par lots, corrections tracées | premier lot fait (voir `lexicon/corrections.tsv`) | environ 9 900 libellés de 1 à 5 mots | moyen | faible | relire les lignes « medium/low » |
| Lexique : traductions importées incohérentes | éviter les « Profil → Forzà un Prufilu » | `engine.loose_french` + `lexicon-fixes.tsv` | fait | 92 entrées touchées | fait | nulle | signaler les erreurs aux projets d'origine |

### Nécessitent une étude ou un partenariat

| Chantier | Bénéfice | Solution envisagée | Contraintes et blocages | Volume (méthode) | Prochaine action |
| --- | --- | --- | --- | --- | --- |
| Minecraft Bedrock | Windows, Android, iOS | pack global `texts/co_FR.lang` + `languages.json` + `language_names.json` | clés différentes de Java ; consoles fermées ; plantage si le pack est retiré avec la langue active | environ 13 000 lignes (`en_US.lang` de Mojang) | réutiliser la terminologie Java, aligner les clés par texte anglais |
| Minecraft officiel (Crowdin) | corse dans le jeu sans pack | proposer les traductions sur crowdin.com/project/minecraft/co | Mojang décide ; droits cédés à Mojang ; pas de réutilisation libre ensuite | 8 559 + lanceur | demander l'avis de l'auteur du projet avant toute contribution |
| Firefox de bureau officiel | Firefox en corse sans Corsu | demander l'ouverture du projet `firefox` pour `co` sur Pontoon | équipe Mozilla corse peu active ; décision Mozilla | à mesurer sur les fichiers de Firefox | contacter l'équipe `co` de Pontoon |
| Stardew Valley | jeu populaire, langues ajoutées officiellement prises en charge (1.5.5+) | `Data/AdditionalLanguages` via Content Patcher, distribué sur Nexus | polices à fournir ; textes sous droit du jeu | à mesurer sur les fichiers du jeu | vérifier le volume et les conditions de Nexus |
| RimWorld, Factorio | mods de langue sur Steam Workshop / portail de mods | dossier `Languages/` ou `locale/co/` | non vérifié qu'un code de langue nouveau soit reconnu | à mesurer | test avec un mod minimal |
| Luanti (Minetest), Mindustry, Wesnoth, SuperTuxKart, OpenTTD | jeux libres | contribuer en amont (Weblate, Transifex, PR) | relecture amont nécessaire | à mesurer | ouvrir le corse sur le Weblate de Luanti |
| Telegram | messagerie | paquet de langue personnalisé (translations.telegram.org) | non vérifié pour le corse | — | vérifier |

### Steam : ce qui est possible et ce qui ne l'est pas

1. **Client Steam** : non. Valve ne propose que ses langues d'interface (31) et n'accepte pas de nouvelle langue sur
   son serveur de traduction. Modifier les fichiers du client serait écrasé à chaque mise à jour.
2. **Site et boutique Steam** : non, même raison ; le corse ne figure même pas dans la liste des langues qu'un jeu
   peut déclarer.
3. **Jeux distribués sur Steam** : jeu par jeu, selon le mécanisme du jeu (voir le tableau ci-dessus).
4. **Workshop** : seulement pour les jeux qui l'ouvrent aux mods de langue (RimWorld par exemple), à vérifier pour
   chacun.
5. **Outil d'installation de traductions** : Corsu pourrait installer et mettre à jour des packs de jeux comme il le
   fait pour Firefox, mais seulement jeu par jeu ; il n'existe pas de mécanisme commun.

### Pistes spéculatives

- Dictionnaire libre FR-CO : demander à l'ADECEC une licence ou un export d'INFCOR.
- Correcteur orthographique Hunspell corse : aucun n'existe publiquement ; à construire à partir des formes attestées
  (`tools/corsican_words.py`).
- Mémoire de traduction commune Corsu + Pontoon + Weblate, avec contexte et provenance, partagée avec les autres
  traducteurs.
