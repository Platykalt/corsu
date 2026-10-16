# Minecraft in Corsican: translation conventions

These rules apply to `co_fr.json`. They are provisional: they follow the spelling used by the reviewed Corsican
software translations in `lexicon/` (mostly Patriccollu di Santa Maria è Sichè), and every choice below can be
revised by a Corsican speaker. Terms live in [glossary.tsv](glossary.tsv).

## Spelling

- Standard written Corsican as used in software: *ghj*, *chj*, final *-u* for masculine nouns (*bloccu*, *mondu*),
  articles *u, a, i, e, l'*, contractions *di u → di u* (written separately), *à u, in u, nant'à u*.
- *-zione* in most words (*pozione*, *generazione*, *rigenerazione*), *-zzione* where Patriccollu's translations
  write it (*ozzione/ozzioni*, *azzione*, *interazzione*, *discrizzione*, *prutezzione*). When in doubt, search
  `lexicon/lexicon-mozilla.tsv` and `lexicon/lexicon-upstream.tsv`.
- Negation *ùn … micca*; *ùn* before a verb, *nun* is not used.
- Apostrophes are straight (`'`), as in the game's files.

## Capitalisation and register

- Sentence case for names and labels: *Scala di quercia*, not *Scala Di Quercia*. Proper names keep their capital
  (*Nether*, *End*, *Creeper*).
- Buttons and menu items: infinitive (*Arregistrà*, *Rinasce*, *Lascià u mondu*), as Corsican software does.
- Instructions and help texts address the player as *voi* (plural of politeness), like Firefox and Thunderbird in
  Corsican: *Sciglite*, *Appughjate*. Advancement titles are free, short, and may play on words in Corsican rather than
  copy the English pun.
- Subtitles describe a sound: subject + present tense verb (*Pecura bela*, *Porta si chjode*).

## Names

- Creatures with invented English names (Creeper, Enderman, Ghast, Blaze, Wither, Shulker, Piglin, Hoglin, Zoglin,
  Allay, Breeze, Vex, Strider, Endermite, Slime) keep them, as the Italian and French translations do.
- Animals, plants, tools and materials take their ordinary Corsican name (*pecura*, *filetta*, *accetta*, *ramu*).
- Compound names follow Corsican order: noun + *di* + material, or noun + adjective agreeing in gender and number:
  *Lastra di quercia*, *Lana rossa*, *Vetru tintu turchinu*, *Scale di petra lisciata*.

## Colours (masculine / feminine)

| English | Corsican |
| --- | --- |
| White | biancu / bianca |
| Light Gray | grisgiu chjaru / grisgia chjara |
| Gray | grisgiu / grisgia |
| Black | neru / nera |
| Brown | marrone (invariable singular), pl. marroni |
| Red | rossu / rossa |
| Orange | aranciu / arancia |
| Yellow | ghjallu / ghjalla |
| Lime | verde limone (invariable) |
| Green | verde |
| Cyan | cianu / ciana |
| Light Blue | celeste |
| Blue | turchinu / turchina |
| Purple | purpurinu / purpurina |
| Magenta | magenta (invariable) |
| Pink | rusulinu / rusulina |

## Placeholders and markup

- Keep every `%s`, `%1$s`, `%2$s` … and `%%`. Words can move around them; when the order changes, number them
  (`%2$s … %1$s`). `tools/minecraft.py check` refuses a string that loses, adds or breaks an argument.
- Keep `§` formatting codes and line breaks (`\n`) exactly.
- Key names on the keyboard (`key.keyboard.*`) are translated only where the key has a word on it (*Spaziu*,
  *Entrata*, *Maiuscule manca*); symbols stay.
