# Lot 07 · Batch 07 — Questions ouvertes / Open questions

Les décisions qui restent à prendre (voir decisions-2.md, decisions.md, review.md).
The decisions still to be made (see decisions-2.md, decisions.md, review.md).

**34 questions, 66 clés / keys.** Durée estimée / estimated time: 30–60 min.

> **Fr.** Ces traductions ont été produites puis revues par une IA, sans relecture humaine jusqu'ici. Rien ici n'est
> « validé ». Votre avis de locuteur ou locutrice du corse est ce qui manque.
>
> **En.** These translations were produced and then revised by an AI, with no human review so far. Nothing here is
> "validated". Your judgement as a Corsican speaker is what is missing.

## Comment répondre · How to answer

1. **Dans ce fichier** : écrivez sous « Votre réponse » de chaque question. « OK » suffit si le corse est naturel ;
   sinon, écrivez la forme que vous utiliseriez. Vous pouvez sauter une question.
   **In this file**: write under "Your answer" for each question. "OK" is enough if the Corsican is natural;
   otherwise write the form you would use. You may skip any question.
2. **Ou par ticket** · **or by issue**: [nouveau ticket « Traduction »](https://github.com/Platykalt/corsu/issues/new?template=translation.yml) ; mettez la clé (par ex.
   `selectServer.add`) dans le champ **Clé / Key**, votre proposition dans **Corse proposé**.
3. **Ou dans un tableur** · **or in a spreadsheet**: [07-open-questions.tsv](07-open-questions.tsv) contient les mêmes questions
   (colonnes key, english, corsican, context, question) ; ajoutez une colonne pour vos réponses.

**Important.** Une réponse de locuteur est enregistrée comme **relecture humaine** seulement, pas comme
vérification en jeu : l'affichage dans Minecraft (place sur les boutons, contexte) reste à vérifier à part.
A speaker's answer is recorded as **human review only**, not as an in-game check: how the text looks in Minecraft
(button space, context) is checked separately.

Notation : « ¶ » marque un retour à la ligne dans le texte du jeu ; `%s` est remplacé par le jeu (un nom, un nombre).
Notation: "¶" marks a line break in the game text; `%s` is filled in by the game (a name, a number).

---

### 07.01 — Add Server

**Où / Where:** D1. Server list. The file uses *servitore* (Mozilla's word); the Discord drafts of Corsu use *servore*.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `selectServer.add` | Add Server | Nouveau serveur | **Aghjunghje un servitore** |
| `multiplayer.title` | Play Multiplayer | Multijoueur | **Ghjucà à parechji** |

**Question:** Is *servitore* natural for a game server and a Discord server? Does *servore* exist for you?

**Votre réponse / Your answer:**

> 

### 07.02 — Sweet Berries

**Où / Where:** D2. Feminine plural of adjectives in -e. Current convention: *-e* (*Baghe dolce*, *Liane pendente*, *Criature ostile*, *Terre sterile*), as in most Vikipedia texts and Mozilla's translations; Apertium and Wiktionary give *-i*.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `item.minecraft.sweet_berries` | Sweet Berries | Baies sucrées | **Baghe dolce** |
| `block.minecraft.weeping_vines` | Weeping Vines | Lianes pleureuses | **Liane pendente** |
| `soundCategory.hostile` | Hostile Mobs | Créatures hostiles | **Criature ostile** |
| `biome.minecraft.end_barrens` | End Barrens | Terres stériles de l'End | **Terre sterile di l'End** |

**Question:** Which do you write: *e baghe dolce* or *e baghe dolci*? *e criature ostile* or *ostili*? And with a noun in *-ioni*: *e vostre infurmazioni persunali* or *persunale* (`menu.custom_screen_info.contents`)?

**Votre réponse / Your answer:**

> 

### 07.03 — Sneak

**Où / Where:** D4. Sneak = crouch. Button: options button, about 22 characters fit including ": value"; longest Corsican label here: 18 characters.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `key.sneak` | Sneak | S'accroupir | **Accuvacciassi** |
| `stat.minecraft.sneak_time` | Sneak Time | Temps passé accroupi | **Tempu accuvacciatu** |

**Question:** What is the everyday verb for crouching: *accuvacciassi*, *acciucciassi*, another?

**Votre réponse / Your answer:**

> 

### 07.04 — Plant a seed and watch it grow

**Où / Where:** D5. Seeds: changed to the plural *sumente*; the singular was avoided.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `advancements.husbandry.plant_seed.description` | Plant a seed and watch it grow | Plantez une graine et regardez-la pousser. | **Piantate sumente è fighjatele cresce** |
| `subtitles.entity.sniffer.drop_seed` | Sniffer drops seed | Renifleur qui trouve des graines | **Annusadore lascia sumente** |
| `item.minecraft.pumpkin_seeds` | Pumpkin Seeds | Graines de citrouille | **Sumente di zucca** |

**Question:** Is the singular *una sumente* or *una sumenta*? Is *sumente* your word for garden seeds?

**Votre réponse / Your answer:**

> 

### 07.05 — Bush

**Où / Where:** D6. A single bush block (and its dead form).

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.bush` | Bush | Buisson | **Arbustu** |
| `block.minecraft.dead_bush` | Dead Bush | Buisson mort | **Arbustu seccu** |

**Question:** *Arbustu / Arbustu seccu*, or *Machja / Machja secca*? Does *machja* name a single bush for you, or only the maquis?

**Votre réponse / Your answer:**

> 

### 07.06 — Experience Orb

**Où / Where:** D7. Experience points and levels.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `entity.minecraft.experience_orb` | Experience Orb | Orbe d'expérience | **Sfera di sperienza** |
| `commands.experience.query.levels` | %s has %s experience levels | %s a %s niveau(x) d'expérience | **%s hà %s livelli di sperienza** |

**Question:** *sperienza*, *esperienza* (Mozilla) or *spirienza*?

**Votre réponse / Your answer:**

> 

### 07.07 — Red Per Pale

**Où / Where:** D8. Banner heraldry (full list in 04-banner-heraldry.md).

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.banner.half_vertical.red` | Red Per Pale | Parti, au premier de gueules | **Partitu rossu** |
| `block.minecraft.banner.diagonal_right.red` | Red Per Bend | Tranché, au premier de gueules | **Trinciatu rossu** |

**Question:** Keep Italian-style heraldic terms (*Partitu*, *Trinciatu*) or use plain descriptions (*Mità diritta*, *Mità in diagunale*)?

**Votre réponse / Your answer:**

> 

### 07.08 — Chicken clucks

**Où / Where:** D9. Sound verbs whose current form has another meaning in the resources (full list in 05-animal-sounds.md).

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `subtitles.entity.chicken.ambient` | Chicken clucks | Gloussement de poule | **Ghjallina cocca** |
| `subtitles.entity.wolf.pant` | Wolf pants | Halètement de loup | **Lupu ansa** |

**Question:** *Ghjallina cocca* (*cocca* is found only as a mushroom) and *Lupu ansa* (*ansa* found only as "river bend"): which verbs?

**Votre réponse / Your answer:**

> 

### 07.09 — Lukewarm Ocean

**Où / Where:** D10. Ocean between warm and cold.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `biome.minecraft.lukewarm_ocean` | Lukewarm Ocean | Océan tiède | **Oceanu tepidu** |
| `biome.minecraft.deep_lukewarm_ocean` | Deep Lukewarm Ocean | Océan tiède profond | **Oceanu tepidu prufondu** |

**Question:** *tepidu*, or another word for lukewarm?

**Votre réponse / Your answer:**

> 

### 07.10 — Potent Sulfur

**Où / Where:** D11. New 26.3 block that erupts like a geyser. FR *Soufre concentré*, IT *Zolfo concentrato*.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.potent_sulfur` | Potent Sulfur | Soufre concentré | **Zolfu putente** |

**Question:** *Zolfu putente* (powerful) or *Zolfu cuncentratu*?

**Votre réponse / Your answer:**

> 

### 07.11 — Gilded Blackstone

**Où / Where:** D12. Blackstone with gold in it. Changed from *durata* (which also means "duration").

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.gilded_blackstone` | Gilded Blackstone | Roche noire dorée | **Petranera indurata** |

**Question:** *Petranera indurata* or *Petranera dorata*? Is *induratu* the word for gilded?

**Votre réponse / Your answer:**

> 

### 07.12 — Dappled Forest

**Où / Where:** D13. New 26.3 forest biome; FR and IT call it amber. Changed from *chjazzata* (not found) to *ambrata*.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `biome.minecraft.dappled_forest` | Dappled Forest | Forêt ambrée | **Furesta ambrata** |

**Question:** *Furesta ambrata* or *Furesta machjata* (spotted)? Please check the biome in game if you can.

**Votre réponse / Your answer:**

> 

### 07.13 — Novice

**Où / Where:** D14. Villager trade levels (Novice, Apprentice, Journeyman).

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `merchant.level.1` | Novice | Novice | **Principiante** |
| `merchant.level.2` | Apprentice | Apprenti | **Apprendista** |
| `merchant.level.3` | Journeyman | Compagnon | **Cumpagnu** |

**Question:** *Principiante*, *Apprendista*, *Cumpagnu*: natural for trade ranks? Alternative for Apprentice: *Garzone*?

**Votre réponse / Your answer:**

> 

### 07.14 — Copper Bulb

**Où / Where:** Q2. Two light blocks.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.copper_bulb` | Copper Bulb | Ampoule en cuivre | **Lampadina di ramu** |
| `block.minecraft.redstone_lamp` | Redstone Lamp | Lampe à redstone | **Lampada di redstone** |

**Question:** *Lampadina di ramu* and *Lampada di redstone*, or *Lampa* for one of them?

**Votre réponse / Your answer:**

> 

### 07.15 — Sculk Shrieker

**Où / Where:** Q6. Sculk block that shrieks.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.sculk_shrieker` | Sculk Shrieker | Hurleur sculk | **Urladore di sculk** |

**Question:** *Urladore di sculk* (from *urlà*): natural? *-adore* or *-atore*?

**Votre réponse / Your answer:**

> 

### 07.16 — Zombified Piglin

**Où / Where:** Q7.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `entity.minecraft.zombified_piglin` | Zombified Piglin | Piglin zombifié | **Piglin zumbificatu** |

**Question:** *Piglin zumbificatu* or *zombificatu*?

**Votre réponse / Your answer:**

> 

### 07.17 — Orange Poplar Leaves

**Où / Where:** Q8. Colour adjective *aranciu/arancia*, plural *arance*.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.orange_poplar_leaves` | Orange Poplar Leaves | Feuilles de peuplier orange | **Foglie di piobbu arance** |

**Question:** *Foglie di piobbu arance* reads like "oranges" (fruit). Better: invariable *aranciu*, or *di culore aranciu*?

**Votre réponse / Your answer:**

> 

### 07.18 — Nether Wart

**Où / Where:** Q9. A red fungus of the Nether.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.nether_wart` | Nether Wart | Verrues du Nether | **Verruca di u Nether** |
| `item.minecraft.nether_wart` | Nether Wart | Verrues du Nether | **Verruca di u Nether** |

**Question:** *Verruca di u Nether* looks Italian. Is *porru* the Corsican word for wart, and would *Porru di u Nether* work?

**Votre réponse / Your answer:**

> 

### 07.19 — Sea Pickle

**Où / Where:** Q10. Glowing sea creature.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.sea_pickle` | Sea Pickle | Cornichon de mer | **Cucumaru di mare** |

**Question:** *Cucumaru di mare*: natural?

**Votre réponse / Your answer:**

> 

### 07.20 — Allium

**Où / Where:** Q11. Flowers and plants.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.allium` | Allium | Allium | **Agliu salvaticu** |
| `block.minecraft.cornflower` | Cornflower | Bleuet | **Fiurdalisu** |
| `block.minecraft.azure_bluet` | Azure Bluet | Houstonie bleue | **Houstonia celeste** |
| `block.minecraft.lily_pad` | Lily Pad | Nénuphar | **Foglia di ninfea** |

**Question:** *Agliu salvaticu*, *Fiurdalisu*, *Houstonia celeste*, *Foglia di ninfea*: local names?

**Votre réponse / Your answer:**

> 

### 07.21 — Small Dripleaf

**Où / Where:** Q1. Cave plant whose leaf tilts.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.small_dripleaf` | Small Dripleaf | Petite foliogoutte | **Foglia à goccia chjuca** |
| `block.minecraft.big_dripleaf` | Big Dripleaf | Grande foliogoutte | **Foglia à goccia grande** |

**Question:** *Foglia à goccia chjuca / grande*: natural?

**Votre réponse / Your answer:**

> 

### 07.22 — Frosted Ice

**Où / Where:** Q14. Unattested adjectives.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.frosted_ice` | Frosted Ice | Glace givrée | **Ghjacciu brinatu** |
| `block.minecraft.chipped_anvil` | Chipped Anvil | Enclume ébréchée | **Ancùdina intaccata** |
| `block.minecraft.damaged_anvil` | Damaged Anvil | Enclume endommagée | **Ancùdina dannighjata** |

**Question:** *Ghjacciu brinatu*, *Ancùdina intaccata / dannighjata*: natural? Is *ancùdina* your word for an anvil?

**Votre réponse / Your answer:**

> 

### 07.23 — Lush Caves

**Où / Where:** Q16. Biome names (*Grotte verde* follows the D2 convention).

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `biome.minecraft.lush_caves` | Lush Caves | Cavernes luxuriantes | **Grotte verde** |
| `biome.minecraft.jagged_peaks` | Jagged Peaks | Pics dentelés | **Pinzi dentati** |

**Question:** *Grotte verde* (Lush Caves) and *Pinzi dentati* (Jagged Peaks): natural?

**Votre réponse / Your answer:**

> 

### 07.24 — Parched

**Où / Where:** Q17. New 26.x mobs (a dried skeleton, a mummified camel). FR *Desséché*, *Dromadaire momifié*.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `entity.minecraft.parched` | Parched | Desséché | **Scheletru arsu** |
| `entity.minecraft.camel_husk` | Camel Husk | Dromadaire momifié | **Cammellu seccu** |

**Question:** *Scheletru arsu* (burnt) or *Scheletru seccu* (dried)? *Cammellu seccu*: natural?

**Votre réponse / Your answer:**

> 

### 07.25 — Feed a Snifflet

**Où / Where:** Q18–19. Coined baby names (Snifflet, Ghastling).

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `advancements.husbandry.feed_snifflet.description` | Feed a Snifflet | Nourrissez un reniflet. | **Date da manghjà à un annusadurellu** |
| `subtitles.entity.ghastling.ambient` | Ghastling coos | Gazouillis de Ghastelin | **Ghastinu canticchjeghja** |

**Question:** *annusadurellu* and *Ghastinu*: acceptable coinages?

**Votre réponse / Your answer:**

> 

### 07.26 — Trident thunder cracks

**Où / Where:** Q27.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `subtitles.item.trident.thunder` | Trident thunder cracks | Tonnerre de trident | **Tonu di u tridente scoppia** |

**Question:** *Tonu di u tridente scoppia*: is *tonu* thunder here (not "tone")?

**Votre réponse / Your answer:**

> 

### 07.27 — Blowback

**Où / Where:** Q28–29. Advancement titles with proverbs.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `advancements.adventure.blowback.title` | Blowback | Œil pour œil, vent pour vent | **Chì sumena ventu ricoglie timpesta** |
| `advancements.adventure.two_birds_one_arrow.title` | Two Birds, One Arrow | D'une flèche deux coups | **Dui pichjoni cù una freccia** |

**Question:** *Chì sumena ventu ricoglie timpesta* and *Dui pichjoni cù una freccia*: right wording? Is there a Corsican idiom for "two birds with one stone"?

**Votre réponse / Your answer:**

> 

### 07.28 — Husbandry

**Où / Where:** Q31. Tab for breeding and farming.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `advancements.husbandry.root.title` | Husbandry | Agriculture | **Agricultura** |

**Question:** *Agricultura* or *Allevu*?

**Votre réponse / Your answer:**

> 

### 07.29 — When equipped:

**Où / Where:** Q34. Tooltip headers ("When equipped:", "When saddled:").

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `item.modifiers.any` | When equipped: | À l'usage : | **Quandu hè equipatu :** |
| `item.modifiers.saddle` | When saddled: | En selle : | **Quandu hè insellatu :** |

**Question:** *equipatu*, *insellatu*: natural?

**Votre réponse / Your answer:**

> 

### 07.30 — Sheaf Pottery Sherd

**Où / Where:** Q35. Pottery sherds.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `item.minecraft.sheaf_pottery_sherd` | Sheaf Pottery Sherd | Tesson de poterie d'épis | **Cocciu di vasu di mannella** |
| `item.minecraft.snort_pottery_sherd` | Snort Pottery Sherd | Tesson de poterie de renifleur | **Cocciu di vasu di sbuffu** |
| `item.minecraft.mourner_pottery_sherd` | Mourner Pottery Sherd | Tesson de poterie de pleureur | **Cocciu di vasu di luttu** |

**Question:** *mannella* (sheaf), *sbuffu* (snort), *luttu* (mourner): natural?

**Votre réponse / Your answer:**

> 

### 07.31 — Left Shift

**Où / Where:** Q36. Shift key names.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `key.keyboard.left.shift` | Left Shift | Maj. gauche | **Maiuscule manca** |
| `key.keyboard.right.shift` | Right Shift | Maj. droite | **Maiuscule diritta** |

**Question:** *Maiuscule manca / diritta*: right form for the Shift keys? Alternative: *Maiuscula manca*, *Tastu maiuscule*.

**Votre réponse / Your answer:**

> 

### 07.32 — %shp

**Où / Where:** Q40. Health points after the player name ("%s PS").

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `multiplayer.player.list.hp` | %shp | %s PV | **%s PS** |

**Question:** *PS* (punti di salute): understandable?

**Votre réponse / Your answer:**

> 

### 07.33 — ON

**Où / Where:** Review 2026-10: on/off values. Button: options button, about 22 characters fit including ": value"; longest Corsican label here: 2 characters.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `options.on` | ON | Oui | **Sì** |
| `options.off` | OFF | Non | **Nò** |

**Question:** *Sì / Nò* or *Attivu / Inattivu*?

**Votre réponse / Your answer:**

> 

### 07.34 — Ominous Banner

**Où / Where:** Q3. Ominous.

| Clé · Key | English | Français (officiel) | Corse actuel · Corsican now |
| --- | --- | --- | --- |
| `block.minecraft.ominous_banner` | Ominous Banner | Bannière funeste | **Stendardu funestu** |
| `item.minecraft.ominous_bottle` | Ominous Bottle | Fiole funeste | **Buttiglia funesta** |

**Question:** *funestu* or *minacciosu*?

**Votre réponse / Your answer:**

> 
