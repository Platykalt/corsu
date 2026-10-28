# Feuille de route

[English](../en/roadmap.md)

Ce qui suit est **prévu ou envisagé**, pas disponible, sauf les lignes marquées « fait ». Ce qui marche aujourd'hui est dans
[Ce qui marche, et où](compatibilite.md). État établi le 19 octobre 2026 ; version publiée : 0.28.3.

**Fait dans la 0.26.0** : pour le clavier Keyman, un dictionnaire qui garde les majuscules tapées et des préférences
régionales expérimentales (Cismuntincu, Pumuntincu) ; pour Minecraft Java, une nouvelle relecture par IA des textes
(octobre 2026), toujours sans relecture par un locuteur.

## Ce qui existe déjà en corse ailleurs

La plupart de ces traductions sont l'œuvre de Patriccollu di Santa Maria è Sichè. Sa liste fait référence :
[Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica) (47 logiciels traduits, 3 en
attente de publication, 3 en cours). Corsu en reprend une partie dans `lexicon/` (voir `tools/import_translations.py`).
Les pourcentages viennent des API de Pontoon et de Hosted Weblate ; les autres projets n'en publient pas sans compte.

| Logiciel | Où vit la traduction | État constaté | Repris par Corsu |
| --- | --- | --- | --- |
| Firefox pour Android | Pontoon | 2 533 chaînes approuvées sur 2 548 | oui (lexique) |
| Firefox pour iOS, Focus Android et iOS, Mozilla VPN | Pontoon | 91 à 100 % | oui |
| **Firefox de bureau, Thunderbird de bureau** | — | Mozilla ne les publie pas en corse : pas de paquet de langue `co` pour la version 158.0 ([liste des paquets](https://archive.mozilla.org/pub/firefox/releases/158.0/linux-x86_64/xpi/)), projets non ouverts au corse sur [Pontoon](https://pontoon.mozilla.org/api/v2/locales/co/), aucun paquet communautaire trouvé sur addons.mozilla.org | Corsu construit sa propre traduction de Firefox (techniquement possible, non officielle) |
| Thunderbird pour Android | Hosted Weblate | 92,8 % | oui |
| Tenacity | Hosted Weblate | 98,4 % | oui |
| OpenTracks | Hosted Weblate | 76,1 % | oui |
| Notepad++, WinMerge | dépôt du projet | à jour (WinMerge revu le 6 octobre 2026) | oui |
| Poedit, Audacity | Crowdin / Transifex / dépôt | publiés | oui |
| HandBrake | Transifex / dépôt | publié | non : GPL-2.0-only, incompatible avec la GPL-3.0 de Corsu (corse disponible dans le logiciel) |
| VLC (bureau) | Transifex | partiel, dernière révision 2017 | oui |
| VeraCrypt, SumatraPDF, PDFsam, FileZilla | dépôt du projet | publiés | non : déjà en corse dans le logiciel |
| 7-Zip, Inno Setup, NSIS, Paint.NET, Mp3tag, OmegaT… | selon le projet | listés par Patriccollu, non vérifiés ici | non |
| CCleaner, Video DownloadHelper | — | abandonnés (plus maintenu / corse retiré) | non |
| LibreOffice, GIMP, Inkscape, KeePassXC, F-Droid, OsmAnd, Luanti | — | pas de corse trouvé | non |

## Prochains chantiers, par ordre

### Réalisables tout de suite

| Chantier | Bénéfice | Solution | Preuve de faisabilité | Volume estimé (méthode) | Effort | Maintenance | Prochaine action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minecraft Java : installation automatique | le corse devient la langue du jeu sans manipulation | composant `minecraft` de l'installeur : pack copié dans chaque dossier de jeu, `lang:co_fr` dans `options.txt` | fait : 26.3 dans 0.22.0, 87 versions dans 0.23.0 ; testé sur des dossiers simulés | — | fait | à chaque version du jeu | essai réel par un joueur |
| Minecraft Java : relecture | traduction fiable du jeu le plus joué | relecture par un locuteur, clé par clé, statut dans `inventory.tsv` | traduction complète livrée (26.3) | 8 559 chaînes (`en_us.json` 26.3) | élevé | faible | relire d'abord interface, objets, blocs |
| Minecraft Java : essai en jeu | preuve que le pack se charge | lancer 26.3 avec le pack, parcourir menus, inventaire, mort, sous-titres | 26.3 lancée une fois avec le pack sur l'instance du mainteneur (16 octobre 2026), journal du jeu seulement | 1 parcours | faible | à chaque version | parcours écran par écran, captures à l'appui |
| Minecraft Java : versions suivantes | suivre Mojang | `tools/minecraft.py diff` puis `inventory` | outil livré | 26.2 → 26.3 : 436 chaînes ajoutées, 56 modifiées (`tools/minecraft.py diff`) | faible | régulier | lancer `diff 26.3 26.4` à la sortie |
| Discord : relecture des libellés courts | corriger les contresens visibles | relecture sémantique par lots, corrections tracées | premier lot fait (voir `lexicon/corrections.tsv`) | environ 9 900 libellés de 1 à 5 mots | moyen | faible | relire les lignes « medium/low » |
| Lexique : traductions importées incohérentes | éviter les « Profil → Forzà un Prufilu » | `engine.loose_french` + `lexicon-fixes.tsv` | fait | 92 entrées touchées | fait | nulle | signaler les erreurs aux projets d'origine |

### Nécessitent une étude ou un partenariat

| Chantier | Bénéfice | Solution envisagée | Contraintes et blocages | Volume (méthode) | Prochaine action |
| --- | --- | --- | --- | --- | --- |
| Minecraft Bedrock | Windows, Android, iOS | pack global `texts/co_FR.lang` + `languages.json` + `language_names.json` | clés différentes de Java ; consoles fermées ; plantage si le pack est retiré avec la langue active | environ 13 000 lignes (`en_US.lang` de Mojang) | réutiliser la terminologie Java, aligner les clés par texte anglais |
| Minecraft officiel (Crowdin) | corse dans le jeu et le lanceur sans pack | le corse est déjà une langue cible du [projet Crowdin de Minecraft](https://crowdin.com/project/minecraft/co) et de celui du lanceur, sans être publié | Mojang décide de la publication ; conditions de cession des droits non trouvées ; il faudrait des textes relus | 8 559 + lanceur | décider d'abord de la licence des textes ([LICENSING.md](../../minecraft/java/LICENSING.md)) |
| Outil de contribution (Crowdin ou Weblate) pour Corsu | permettre à des locuteurs de relire sans Git | Weblate Libre (gratuit pour les projets libres publics) ou Crowdin open source ; tous deux lisent JSON, Crowdin aussi TSV | Crowdin exige [un projet de plus de 3 mois avec une communauté active et des nouvelles à jour](https://crowdin.com/page/open-source-project-setup-request) : Corsu (commencé le 30 septembre 2026) ne remplit pas encore ces conditions | — | essayer d'abord le formulaire de ticket et `inventory.tsv`, puis Weblate Libre quand des relecteurs se présentent |
| Firefox de bureau officiel | Firefox en corse sans Corsu | demande à Mozilla, qui [n'accepte pas une nouvelle langue avec un seul traducteur actif](https://discourse.mozilla.org/t/about-requesting-a-new-locale-for-firefox/86515) et demande d'abord plusieurs traducteurs actifs sur les petits projets | une tentative de 2010 a été close sans suite ([bug 599312](https://bugzilla.mozilla.org/show_bug.cgi?id=599312)) | à mesurer sur les fichiers de Firefox | constituer une équipe de plusieurs traducteurs avec l'équipe `co` de Pontoon |
| Stardew Valley | jeu populaire, langues ajoutées officiellement prises en charge (1.5.5+) | `Data/AdditionalLanguages` via Content Patcher, distribué sur Nexus | polices à fournir ; textes sous droit du jeu | à mesurer sur les fichiers du jeu | vérifier le volume et les conditions de Nexus |
| RimWorld, Factorio | mods de langue sur Steam Workshop / portail de mods | dossier `Languages/` ou `locale/co/` | non vérifié qu'un code de langue nouveau soit reconnu | à mesurer | test avec un mod minimal |
| Luanti (Minetest), Mindustry, Wesnoth, SuperTuxKart, OpenTTD | jeux libres | contribuer en amont (Weblate, Transifex, PR) | relecture amont nécessaire | à mesurer | ouvrir le corse sur le Weblate de Luanti |
| Telegram | messagerie | paquet de langue personnalisé (translations.telegram.org) | non vérifié pour le corse | — | vérifier |

### Steam : ce qui est possible et ce qui ne l'est pas

1. **Client Steam** : pas de corse officiel ni de mécanisme pris en charge. Steamworks [ne gère que ses langues](https://partner.steamgames.com/doc/store/localization/languages)
   (« the only set of languages supported by Steamworks APIs »), et son serveur de traduction, passé sur
   valve.crowdin.com, ne propose pas le corse ; aucune procédure publique pour en ajouter une n'a été trouvée.
   Techniquement, des modifications non officielles du client (injection de CSS ou de JavaScript, comme Millennium)
   peuvent remplacer des textes sur son propre ordinateur, mais elles ne sont pas prises en charge par Valve, sont
   effacées par les mises à jour et Corsu ne les propose pas.
2. **Site et boutique Steam** : pas de corse officiel ; le choix de langue est géré par les serveurs de Valve. Un
   script dans le navigateur pourrait remplacer des libellés sur sa propre machine, comme Corsu le fait pour Google ;
   ce n'est pas étudié.
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
