# Variantes terminologiques : stockage, raccourci, sondage

Revue automatisée du 2026-10-16 sur `lexicon/lexicon.tsv`. Les variantes ont été tranchées **par concept** (selon le sens du texte source) et non selon leur fréquence. Toutes les modifications sont consignées dans `corrections.tsv` (family = `terminology`, statut « applied, automated review (needs a speaker) »). Il faudra qu'un locuteur les valide.

Sources consultées, de la plus forte à la plus faible pour le vocabulaire logiciel :

- **Mozilla co** : `lexicon-mozilla.tsv`, mémoire TMX Pontoon `co.all-projects.tmx`, glossaire TBX `co.v2.tbx`. Il s'agit des traductions relues de Patriccollu di Santa Maria è Sichè et de l'équipe corse de Mozilla.
- **Patriccollu hors Mozilla** : `lexicon-upstream.tsv` (VLC, Audacity, Thunderbird, HandBrake, OpenTracks…) et le dépôt `Lingua_Corsa-Infurmatica.zip`, avec ses notes `.md` et les mémoires TMX d'Audacity et de Poedit.
- **Corpus généraux** : `tools/corsican_words.py lookup` (Vikipedia, Apertium, Wiktionary).

## A. Stockage / allocation / emplacement : `almacenamentu` vs `allucamentu`

### Concepts trouvés (lignes du lexique avant correction)

| Concept (source FR/EN) | Formes trouvées | Lignes |
|---|---|---|
| stockage, stocker, stocké (storage, store) | almacenamentu / almacenà / almacenatu… | 150 |
| idem | allucamentu / allucà / allucatu (déjà conformes) | 29 |
| allocation, allouer (allocate) | allucazione / allucà / allucatu (déjà conformes) | 21 (+2 « d'alluca » sans accent) |
| idem | alluccà / alluccazione / prealluccatu (double c) | 10 |
| emplacement (location, Krita) | allucamentu | 11 |

### Preuves

| Forme | Vikipedia | Apertium | Pontoon TBX/TMX | Patriccollu | Verdict |
|---|---|---|---|---|---|
| almacenamentu, almacenà | 0 | 0 | 0 | 0 | emprunt à l'espagnol (*almacenamiento*), non attesté |
| allucamentu | 1 | – | TBX `storage` = allucamentu ; TMX « Persistent Storage » = Allucamentu permanente, « File storage » = Allucamentu di schedariu | VLC « apparechju d'allucamentu », Audacity « discu d'allucamentu », HandBrake « allucamentu di u flussu » (allocation) | **retenu pour stockage** |
| allucà | – | – | TMX « store data in persistent storage » = allucà dati | – | **retenu (stocker)** |
| allucazione | 0 | oui | – | – | retenu (allocation) |
| alluccà, alluccazione | 0 | 0 | 0 | 0 | coquille (double c) |
| emplacement | – | – | « Location » = Lucalizazione / Pusizione | « Default download location » = Locu predefinitu, « existe déjà à cet emplacement » = in stu locu | **locu** (allucamentu y créerait une collision avec « stockage ») |

Patriccollu emploie aussi **memoria** pour la mémoire de stockage interne (« memoria interna ») et **attribuisce / attribuzione** pour l'allocation de mémoire (Audacity, FFmpeg). Ce sont des alternatives, pas des erreurs.

### Convention

- stockage → **allucamentu** ; stocker → **allucà** (allucatu/-a/-i/-e, allucendu).
- allocation → **allucazione** ; allouer → **allucà**, toujours avec un seul c. **Attribuzione** reste possible, à arbitrer par un locuteur.
- emplacement de fichier ou de ressource → **locu** (pluriel lochi).

### Appliqué

- 146 lignes almacen- → alluc-
- 10 lignes alluccà → allucà
- 2 lignes d'alluca → d'allucà
- 11 lignes Krita allucamentu (emplacement) → locu, avec les articles adaptés (u locu, i lochi)

## B. Raccourci : `scurciatoghja` vs `accurtatoghju`

### Concepts trouvés

| Concept | accurtatoghju/-i (masc.) | formes féminines ou autres (scurciatoghja/-e, scurciatoia/-e, accurtatoia/-e, accurtatoghja/-e, scurtatoghji) |
|---|---|---|
| raccourci clavier (keybind, keyboard shortcut) | ≈ 90 | ≈ 53 |
| autres raccourcis (bureau ou fichier, raccourci de site dans Chrome/Opera, raccourci de commande) | ≈ 255 | ≈ 78 |

Aucune ligne n'avait le sens de « chemin plus court » (itinéraire). Quatre lignes ont le sens d'abréviation ou d'alias (util-linux sfdisk, wget, git), signalées plus bas.

### Preuves

| Forme | Vikipedia | Pontoon TMX | Patriccollu | Verdict |
|---|---|---|---|---|
| accurtatoghju / accurtatoghji | 1 (« un accurtatoghju Pin ») | ≈ 100 unités, tous les sens : site, écran d'accueil, barre d'outils, Siri | Audacity « accurtatoghji di tastera » (clavier), VLC « accurtatoghju per u lanciadore » (lanceur) ; 24 occurrences dans ses TMX | **retenu, masculin** |
| scurtatoghji | – | 1 unité isolée (« Shortcuts ») | – | variante isolée |
| scurciatoia | 1 | 0 | 0 | italianisme (*scorciatoia*) |
| scurciatoghja, accurtatoia, accurtatoghja | 0 | 0 | 0 | non attestés |

### Convention

Un seul terme pour tous les sens : **accurtatoghju** (m.), pluriel **accurtatoghji**. Pour le clavier : **accurtatoghju di tastera**, forme de Patriccollu. Le lexique alterne encore *tastiera* et *tastera* ; ce point n'a pas été traité ici.

### Appliqué

131 lignes corrigées. Le passage au masculin a été fait avec ses accords : un/l'/st'/nisun/u vostru, les participes et adjectifs (squassatu, persunalizati, disattivati, predefiniti…) et les pronoms (attivalli, unu). Il ne reste plus aucune forme féminine.

## C. Sondage : `scandagliu` vs `sundagiu` vs `sundaghju`

### Concepts trouvés

| Concept | scandagliu | sundagiu | sundaghju |
|---|---|---|---|
| sondage d'opinion / vote (Discord « Poll ») | 26 | 8 | 5 |
| questionnaire (survey, enquête : Firefox, Chrome) | – | – | 3 |
| sonde, sondage technique (blkid probe, fréquence de sondage Krita) | 4 | 2 | 1 |

### Preuves

| Forme | Vikipedia | Apertium | Pontoon | Patriccollu | Verdict |
|---|---|---|---|---|---|
| sundaghju | 3 (sondages d'opinion) | – | 0 | 0 | **retenu (poll)** |
| sundagiu | 0 | oui | 0 | 0 | variante graphique légitime |
| scandagliu | 0 | 0 | 0 | 0 | non attesté ; en italien *scandaglio* désigne la sonde de profondeur, pas le sondage d'opinion |
| inchiesta | 11 | oui | 21 unités (Survey = Inchiesta, Take Survey = Risponde à l'inchiesta, Complete this survey = Participà à l'inchiesta) | idem dans lexicon-mozilla | **retenu (survey)** |
| sullicitazione | – | – | – | Thunderbird : polling = sullicitazione | piste pour le « polling » technique |

### Convention

- Sondage Discord (poll) → **sundaghju**, pluriel **sundaghji**. La graphie en -aghju est attestée sur Vikipedia et suit le modèle de messaghju et linguaghju. Patriccollu écrit cependant spiunagiu en -agiu : les deux graphies se défendent.
- Questionnaire (survey, enquête) → **inchiesta** (f.).
- Sondage technique (probe) : non tranché, voir plus bas.

### Appliqué

- 26 lignes scandagliu → sundaghju
- 8 lignes sundagiu → sundaghju
- 3 lignes questionnaire → inchiesta : 8236 « Participà à l'inchiesta », 18257 « a nostra inchiesta », 19477 « st'inchiesta »

## Total

337 lignes modifiées dans `lexicon.tsv`, uniquement dans le champ corse. Le nombre de lignes (119 364) et la fin de fichier sont inchangés. Les 337 lignes correspondantes sont ajoutées à `corrections.tsv`.

## À valider par un locuteur (non modifié ou incertain)

1. **Formes conjuguées de allucà** : 9515 (almacenanu), 26775 (almaceneghja), 29678 (almacenemu), 79298 (almaceneghja) sont restées telles quelles. La forme accentuée sur le radical est à choisir : *alloca / allocanu*, *alluca / allucanu* ou *allucheghja* ? Il faut aussi trancher *allucemu* ou *allochemu*.
2. **Allocation** : faut-il garder allucà/allucazione ou adopter attribuisce/attribuzione comme Patriccollu (Audacity, FFmpeg) ? Cela concerne environ 33 lignes.
3. **Emplacement → locu** (Krita 55299–55469, confiance moyenne) : pusizione ou lucalizazione pourraient mieux convenir à certaines lignes. À vérifier en particulier « creà u locu di a risorsa ».
4. **Sonde ou sondage technique** (util-linux/blkid) : lignes 80472 et 81662 (sundagiu), 83257, 84250, 84251 et 84304 (scandagliu). Ici *scandagliu* (sonde) a peut-être un sens défendable. Autres pistes : *sonda* ou *sundaghju* ?
5. **Fréquence de sondage** (Krita 49639, « Frequenza di sundaghju ») : il s'agit en fait du *polling*. Faut-il *sullicitazione* comme Thunderbird ?
6. **Raccourci au sens d'abréviation ou d'alias** : 79747, 79748, 86775 et 92816 sont passés à accurtatoghju (confiance moyenne). Un mot comme *abbreviatura* ou *sigla* serait peut-être plus juste.
7. **sundaghju ou sundagiu** : le choix de graphie est une unification. À confirmer, car Patriccollu écrit *spiunagiu*.
8. **tastiera ou tastera** dans « accurtatoghju di tastiera » : il reste une incohérence en dehors du périmètre de cette revue.
