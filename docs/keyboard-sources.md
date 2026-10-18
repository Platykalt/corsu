# Sources of the keyboard vocabulary

The Corsican word lists of the Keyman keyboard (`keyboard/data/shared.tsv`, `cismuntincu.tsv`, `pumuntincu.tsv`) are
built by `keyboard/data/tools/make_vocab.py`. Each row names, in its `source` column, the source that attests the
word (the strongest one when several do), and in its `license` column the licence of that source. The weights and
their scale are explained in [keyboard/data/REVIEW.md](../keyboard/data/REVIEW.md).

No message, conversation or personal data was collected. Online pages were consulted one at a time; the large
resources are the public dumps that `tools/fetch_resources.py` already downloads for the project, read locally.

## Licence compatibility

The keyboard model is distributed under the GNU GPL version 3 (`keyboard/platykalt.co.corsu/LICENSE.md`), and Corsu
under GPL-3.0-or-later.

- A word list is mostly facts (single words and how often they occur), not the expression of a text. Where a source
  is still treated as licensed material, its licence allows our use:
- **CC BY-SA 4.0** (Vikipedia, Wikipedia, Wiktionary): Creative Commons declared CC BY-SA 4.0 one-way compatible with
  GPLv3 (8 October 2015, https://creativecommons.org/share-your-work/licensing-considerations/compatible-licenses/).
  Material adapted from it may be released under GPLv3, with attribution, which this page gives.
- **CC BY 2.0 FR** (Tatoeba): a permissive licence that asks for attribution, given here.
- **GPL-3.0** (Apertium): the same licence.
- **CC0 1.0** (Wikidata): a public domain dedication; no condition. The source is still named on every row.
- **Corsu's lexicon**: the words come from Corsu's own translations (GPL-3.0-or-later) and from translations
  imported from other projects, which keep their licence (MPL-2.0, Apache-2.0, GPL-2.0-or-later, MIT, wxWindows,
  Inno Setup licence; see `lexicon/`). All allow redistribution; their `license` value is `corsu-lexicon-mixed`.
- **ADECEC pages and U Cunghjugarellu** carry no free licence (the book says all rights reserved). They are used only
  to *check* that a single word form exists; no text, table or page layout is reproduced. Their `license` value is
  `attestation-only`. The maintainer should confirm that this use suits him before a release.
- Patriccollu's `Lingua_Corsa-Infurmatica` repository, which has no licence file, is **not** used.

## Sources

| id | What it is | Licence | What was taken |
|---|---|---|---|
| `vikipedia` | Corsican Wikipedia, dump `cowiki-latest-pages-articles.xml.bz2` fetched 2026-10-16 (https://dumps.wikimedia.org/cowiki/), "Vikipedia contributors" | CC BY-SA 4.0 | Word counts in the prose of main-namespace articles (templates, tables, links and references removed). The ~1,380 botanical stub articles generated from one table (`{\| align="right" rules="all"`) are left out: they were a quarter of the text and put "spezia", "pianta", "sinonimi" among the top words. A word counts as attested when it occurs 5 times or more. |
| `wiktionary` | Wiktionary, Corsican entries, through the kaikki.org extract `kaikki.org-dictionary-Corsican.jsonl` fetched 2026-10-16 (https://kaikki.org/dictionary/Corsican/) | CC BY-SA 4.0 and GFDL | Headwords and inflected forms, as attestations. Entries tagged Cismontane / Ultramontane / Northern / Southern for the variety pairs (numbers, bellu/beddu, collu/coddu, ride/rida…). |
| `apertium` | apertium-cos dictionary, `apertium-cos.cos.dix` (https://github.com/apertium/apertium-cos) | GPL-3.0 | Lemmas, as attestations. |
| `tatoeba` | Tatoeba, Corsican sentences, `cos_sentences.tsv.bz2` (56 sentences) (https://tatoeba.org) | CC BY 2.0 FR | Words of the sentences, as attestations of everyday usage, and a minimum weight for them. |
| `adecec` | ADECEC thematic lexicons, pages `le-temps-qu'il-fait.html` and `la-cuisine.html` of https://adecec.net/data/new_lessichi/html/, consulted 2026-10-18 | none stated | 53 weather and food words checked one by one (`keyboard/data/sources/adecec.tsv`). |
| `cunghjugarellu` | *U Cunghjugarellu, la conjugaison corse*, Ghjuvan Battistu Paoli, preface Ghjacintu Ottaviani, Canopé de Corse, ISBN 978-2-240-05710-5, legal deposit December 2024, https://educorsica.fr/phocadownload/pdf/u_cunghjugarellu.pdf, consulted 2026-10-18 | all rights reserved | Present and imperfect indicative forms of 21 everyday verbs in the book's *supranacciu* and *suttanacciu* versions (`keyboard/data/sources/cunghjugarellu.tsv`, with the table number of each form). |
| `cowiki-lingua-corsa` | Vikipedia, article "Lingua corsa", revision 403108 (2026-06-07), table "Esempii di parolle in pumuntincu è in cismuntincu (Taravesu è Sartinesu)", https://co.wikipedia.org/wiki/Lingua_corsa | CC BY-SA 4.0 | 28 northern/southern word pairs, with the Taravesu and Sartinesu columns kept apart. |
| `frwiki-corse-langue` | Wikipédia, article "Corse (langue)", revision 239896905 (2026-09-28), sections "Zone de transition" and "Sud de la Corse", https://fr.wikipedia.org/wiki/Corse_(langue) | CC BY-SA 4.0 | 7 northern/southern pairs (fratellu/frateddu, surella/suredda, figliolu/fiddolu, vogliu/voddu, pastore/pastori, nazione/nazioni, accattà/cumprà) and the description of the varieties and transition zones. |
| `wikidata` | Wikidata, Corsican labels (`rdfs:label`, language `co`) of the communes of Haute-Corse and Corse-du-Sud and of Corsica's main places (pievi, natural regions, departments, mountains, passes, rivers, lakes, islands, capes), three SPARQL queries to https://query.wikidata.org/sparql run on 2026-10-18 by `keyboard/data/tools/fetch_places.py` (`keyboard/data/sources/places.tsv`, 548 items). The `source` column gives the item, e.g. `wikidata:Q1153494` (Zicavu) | CC0 1.0 | The words of the labels as place names (446 words; details in REVIEW.md, "Place names"). Aliases and other languages' labels are not used. The Vikipedia dump only cross-checks them (case, frequency). |
| `corsu-lexicon` | Corsu's own lexicons: `lexicon/lexicon.tsv`, `lexicon-fixes.tsv`, `lexicon-mozilla.tsv`, `lexicon-upstream.tsv` | `corsu-lexicon-mixed` (see above) | Words of software interfaces. Used only for words no external source has, with status `corsu-lexicon`, and as a small part of the weight (2 % of a Vikipedia occurrence). Being in a "reviewed" file (Mozilla, Patriccollu's translations) does not make a word attested here. |
| `ai` | Words proposed by the AI agent that built the list | GPL-3.0-or-later | 11 everyday words found in no source above (status `ai-proposal`), listed in REVIEW.md for checking. |

## Consulted but not used

- **INFCOR** (https://adecec.net/infcor): an interactive application with no per-entry address and no stated licence;
  it was not queried automatically. The entries to check by hand are listed in REVIEW.md.
- **Vikipedia's `{{c-supranu}}` / `{{c-suttanu}}` templates**: they are "article under construction" notices written
  in a northern or southern spelling, not a label of the article's variety (1,668 northern, 10 southern); they cannot
  split the corpus by variety.
