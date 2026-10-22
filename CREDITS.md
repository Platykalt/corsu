# Credits

## Translations Corsu reuses

Corsu's lexicon reuses Corsican translations published by other free software projects, under their own licences
(given per section in `lexicon/lexicon-upstream.tsv` and `lexicon/lexicon-mozilla.tsv`). Their texts are kept as
published; Corsu's own adaptations go in `lexicon/lexicon-fixes.tsv` and are listed in `lexicon/corrections.tsv`.

- **Patriccollu di Santa Maria è Sichè** has translated many programs into Corsican within the programs' own
  projects (upstream), over many years. The list [Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica)
  counts 47 translated programs, 3 awaiting publication and 3 in progress (README of 15 March 2026). Corsu uses this
  work in two ways:
  - it **switches on** the Corsican translation shipped with VLC, Audacity, Tenacity, fre:ac, Poedit, PDFsam Basic,
    FileZilla, HandBrake, VeraCrypt, 7-Zip, Notepad++, WinMerge and SumatraPDF, by changing only their language
    setting (the translation stays the translator's and the program's);
  - it **imports as reference vocabulary** most of the translations in `lexicon/lexicon-upstream.tsv` (Audacity, VLC
    and VLC for Android, WinMerge, wxWidgets, Notepad++, Thunderbird for Android, fre:ac, Tenacity, Poedit,
    OpenTracks, Inno Setup), to translate other programs consistently. Some of those sections also have other
    translators.

  Patriccollu has not reviewed Corsu's own texts, and the repository states no licence: Corsu links to it and does not copy
  it.
- **The Corsican Mozilla team** on Pontoon: Firefox for Android and iOS, Focus, Mozilla VPN (MPL-2.0), imported as
  reference vocabulary.

## Linguistic resources consulted

Corsu checks words against public resources (INFCOR by ADECEC, the BDLC of the Università di Corsica, Educorsica by
Canopé, Wiktionary, Vikipedia, Apertium, Unicode CLDR…), listed with their terms in
[resources/README.md](resources/README.md). Consulting a resource does not mean its owner reviewed or approved Corsu;
none has. Rights apply to a work or a database (a dictionary, a table, a collection such as INFCOR), not to the
linguistic facts in it: a Corsican word or its spelling belongs to no publisher. Corsu does not copy works or
databases whose terms do not allow it; when a correction rests on one, the entry consulted is named.

### U Cunghjugarellu (Canopé de Corse)

*U Cunghjugarellu, la conjugaison corse* (Ghjuvan Battistu Paoli, Canopé de Corse, 2024) was consulted to check
Corsican verb forms: the present and imperfect indicative of 21 everyday verbs, with the northern and southern
versions as the book labels them. The words and conjugated forms of Corsican belong to no one; the book describes
them. Its page on Educorsica places the downloadable documents under CC BY-NC-ND 2.0 France, and the PDF reserves
reproduction: these notices concern the publication (its text, tables, layout and examples), not the language. No
explanation or example of the book is reproduced. The forms checked are listed one per row, with the book's table
number, in `keyboard/data/sources/cunghjugarellu.tsv`; the keyboard packages contain only words and their weights.
What was taken, how, and a possible narrower form of that file are in
[docs/keyboard-sources.md](docs/keyboard-sources.md#u-cunghjugarellu-canopé-de-corse). Our thanks go to Canopé de
Corse and to the author for this reference.

## Source texts

- **Julian Gough**, the End Poem of Minecraft, dedicated by him to the public domain (CC0 1.0); Corsu's optional
  pack translates it.

## Hyprland and Noctalia (optional component)

- Hyprland configuration modules adapt option names and structure from Hyprland's example hyprland.lua and wiki
  (BSD-3-Clause, hyprwm).
- The Noctalia profile and co.json follow Noctalia 5.3's documented configuration and translation keys (MIT,
  noctalia-dev); Corsican texts are Corsu's (GPL-3.0-or-later).

## AI and human review

Where each lexicon row comes from, as far as the files and the Git history show it, is in
[lexicon/PROVENANCE.md](lexicon/PROVENANCE.md): identified imports, rows created or adapted with an AI assistant
(commits co-signed by Claude), and 872 rows whose initial origin is not recorded. Those are not counted as human
translations.

Corsu's Minecraft texts and the VLC complement were written by AI, and most reviews of Corsu's own texts so far are
AI reviews. They are never counted as human validation: see [lexicon/REVIEWS.md](lexicon/REVIEWS.md) and
[minecraft/java/STATUS.md](minecraft/java/STATUS.md).

## Reviewers

Corsican speakers who review Corsu's texts are listed here, if they wish, with what they reviewed. None is listed
yet.
