# Credits

## Translations Corsu reuses

Corsu's lexicon reuses Corsican translations published by other free software projects, under their own licences
(given per section in `lexicon/lexicon-upstream.tsv` and `lexicon/lexicon-mozilla.tsv`). Their texts are kept as
published; Corsu's own adaptations go in `lexicon/lexicon-fixes.tsv` and are listed in `lexicon/corrections.tsv`.

- **Patriccollu di Santa Maria è Sichè** has translated many programs into Corsican within the programs' own
  projects (upstream), over many years. His list, [Lingua_Corsa-Infurmatica](https://github.com/Patriccollu/Lingua_Corsa-Infurmatica),
  counts 47 translated programs, 3 awaiting publication and 3 in progress (README of 15 March 2026). Corsu uses his
  work in two ways:
  - it **switches on** the Corsican translation shipped with VLC, Audacity, Tenacity, fre:ac, Poedit, PDFsam Basic,
    FileZilla, HandBrake, VeraCrypt, 7-Zip, Notepad++, WinMerge and SumatraPDF, by changing only their language
    setting (the translation stays his and the program's);
  - it **imports as reference vocabulary** most of the translations in `lexicon/lexicon-upstream.tsv` (Audacity, VLC
    and VLC for Android, WinMerge, wxWidgets, Notepad++, Thunderbird for Android, fre:ac, Tenacity, Poedit,
    OpenTracks, Inno Setup), to translate other programs consistently. Some of those sections also have other
    translators.

  He has not reviewed Corsu's own texts, and his repository states no licence: Corsu links to it and does not copy
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

## Source texts

- **Julian Gough**, the End Poem of Minecraft, dedicated by him to the public domain (CC0 1.0); Corsu's optional
  pack translates it.

## AI and human review

Corsu's Minecraft texts and the VLC complement were written by AI, and most reviews of Corsu's own texts so far are
AI reviews. They are never counted as human validation: see [lexicon/REVIEWS.md](lexicon/REVIEWS.md) and
[minecraft/java/STATUS.md](minecraft/java/STATUS.md).

## Reviewers

Corsican speakers who review Corsu's texts are listed here, if they wish, with what they reviewed. None is listed
yet.
