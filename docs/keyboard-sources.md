# Sources of the keyboard vocabulary

The Corsican word lists of the Keyman keyboard (`keyboard/data/shared.tsv`, `cismuntincu.tsv`, `pumuntincu.tsv`) are
built by `keyboard/data/tools/make_vocab.py`. Each row names, in its `source` column, the source that attests the
word (an openly licensed one first when several do), and in its `license` column the licence of that source. The weights and
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
- **Licence Ouverte / Etalab 2.0** (INSEE's official commune names, through geo.api.gouv.fr): free reuse with
  attribution, given here; compatible with CC BY and the GPL.
- **Corsu's lexicon**: the words come from Corsu's own translations (GPL-3.0-or-later) and from translations
  imported from other projects, which keep their licence (MPL-2.0, Apache-2.0, GPL-2.0-or-later, MIT, wxWindows,
  Inno Setup licence; see `lexicon/`). All allow redistribution; their `license` value is `corsu-lexicon-mixed`.
- **ADECEC pages and U Cunghjugarellu** are reference works consulted to *check* single word forms. Their
  `license` value, `attestation-only`, says how they were used; it attributes no licence to the words, which are
  facts of the language and belong to no one. Rows that an openly licensed source also has cite that source
  instead (the order changes no weight); the forms checked in the reference works stay listed in
  `keyboard/data/sources/`. U Cunghjugarellu is described in detail below.
- Patriccollu's `Lingua_Corsa-Infurmatica` repository, which has no licence file, is **not** used.

## Sources

| id | What it is | Licence | What was taken |
|---|---|---|---|
| `vikipedia` | Corsican Wikipedia, dump `cowiki-latest-pages-articles.xml.bz2` fetched 2026-10-16 (https://dumps.wikimedia.org/cowiki/), "Vikipedia contributors" | CC BY-SA 4.0 | Word counts in the prose of main-namespace articles (templates, tables, links and references removed). The ~1,380 botanical stub articles generated from one table (`{\| align="right" rules="all"`) are left out: they were a quarter of the text and put "spezia", "pianta", "sinonimi" among the top words. A word counts as attested when it occurs 5 times or more. |
| `wiktionary` | Wiktionary, Corsican entries, through the kaikki.org extract `kaikki.org-dictionary-Corsican.jsonl` fetched 2026-10-16 (https://kaikki.org/dictionary/Corsican/) | CC BY-SA 4.0 and GFDL | Headwords and inflected forms, as attestations. Entries tagged Cismontane / Ultramontane / Northern / Southern for the variety pairs (numbers, bellu/beddu, collu/coddu, ride/rida…). |
| `apertium` | apertium-cos dictionary, `apertium-cos.cos.dix` (https://github.com/apertium/apertium-cos) | GPL-3.0 | Lemmas, as attestations. |
| `tatoeba` | Tatoeba, Corsican sentences, `cos_sentences.tsv.bz2` (56 sentences) (https://tatoeba.org) | CC BY 2.0 FR | Words of the sentences, as attestations of everyday usage, and a minimum weight for them. |
| `adecec` | ADECEC thematic lexicons, pages `le-temps-qu'il-fait.html` and `la-cuisine.html` of https://adecec.net/data/new_lessichi/html/, consulted 2026-10-18 | none stated | 53 weather and food words checked one by one (`keyboard/data/sources/adecec.tsv`). |
| `cunghjugarellu` | *U Cunghjugarellu, la conjugaison corse*, Ghjuvan Battistu Paoli, preface Ghjacintu Ottaviani, Canopé de Corse, ISBN 978-2-240-05710-5, legal deposit December 2024, https://www.educorsica.fr/phocadownload/pdf/u_cunghjugarellu.pdf, consulted 2026-10-18 | publication: see "U Cunghjugarellu" below (book page: CC BY-NC-ND 2.0 FR; PDF: reproduction reserved) | Present and imperfect indicative forms of 21 everyday verbs in the book's *supranacciu* and *suttanacciu* versions, as checked facts (`keyboard/data/sources/cunghjugarellu.tsv`, with the table number of each form). |
| `cowiki-lingua-corsa` | Vikipedia, article "Lingua corsa", revision 403108 (2026-06-07), table "Esempii di parolle in pumuntincu è in cismuntincu (Taravesu è Sartinesu)", https://co.wikipedia.org/wiki/Lingua_corsa | CC BY-SA 4.0 | 28 northern/southern word pairs, with the Taravesu and Sartinesu columns kept apart. |
| `frwiki-corse-langue` | Wikipédia, article "Corse (langue)", revision 239896905 (2026-09-28), sections "Zone de transition" and "Sud de la Corse", https://fr.wikipedia.org/wiki/Corse_(langue) | CC BY-SA 4.0 | 7 northern/southern pairs (fratellu/frateddu, surella/suredda, figliolu/fiddolu, vogliu/voddu, pastore/pastori, nazione/nazioni, accattà/cumprà) and the description of the varieties and transition zones. |
| `wikidata` | Wikidata, Corsican labels (`rdfs:label`, language `co`) of the communes of Haute-Corse and Corse-du-Sud and of Corsica's main places (pievi, natural regions, departments, mountains, passes, rivers, lakes, islands, capes), three SPARQL queries to https://query.wikidata.org/sparql run on 2026-10-18 by `keyboard/data/tools/fetch_places.py` (`keyboard/data/sources/places.tsv`, 548 items). The `source` column gives the item, e.g. `wikidata:Q1153494` (Zicavu) | CC0 1.0 | The words of the labels as place names (446 words, plus *Vizzani*, the Vikipedia title of Vezzani, from `keyboard/data/sources/place-titles.tsv`; details in REVIEW.md, "Place names"). Aliases and other languages' labels are not used. The Vikipedia dump only cross-checks them (case, frequency). |
| `cog` | INSEE, Code officiel géographique: official names of the 360 communes of Corse-du-Sud and Haute-Corse, two requests to https://geo.api.gouv.fr/departements/{2A,2B}/communes on 2026-10-18 by `keyboard/data/tools/fetch_communes.py` (`keyboard/data/sources/communes-official.tsv`). The `source` column gives the commune code, e.g. `cog:2A032` (Bastelicaccia) | Licence Ouverte / Etalab 2.0 | The words of the official names that the Corsican names do not already give (221 words: *Bastelicaccia*, *Zicavo*, *Ajaccio*, *Sartène*…), at a low weight, so that a legitimate official spelling typed on purpose is known and kept (REVIEW.md, "Place names"). |
| `homographs` | `keyboard/data/sources/homographs.tsv`, Corsu's own list of common words written like a capitalised name of the list, each with its evidence (*corti*: Apertium's adjective *cortu* and 62 lowercase uses in Vikipedia). Wiktionary's common (non-name) forms that match a name are added the same way under the `wiktionary` source (*orsu*, *argentu*, *mansu*…) | GPL-3.0-or-later (the list); evidence from GPL-3.0 and CC BY-SA 4.0 sources | The lowercase common word next to the name, so that a word typed on purpose in lowercase is not turned into the name (REVIEW.md). |
| `acronyms` | `keyboard/data/sources/acronyms.tsv`, Corsu's own short list of acronyms with a reason to be typed in Corsican text about the language (ADECEC, INFCOR, BDLC), each with its reference | GPL-3.0-or-later (the list) | The acronym in capitals at a low weight, so that auto-correction keeps it. |
| `corsu-lexicon` | Corsu's own lexicons: `lexicon/lexicon.tsv`, `lexicon-fixes.tsv`, `lexicon-mozilla.tsv`, `lexicon-upstream.tsv` | `corsu-lexicon-mixed` (see above) | Words of software interfaces. Used only for words no external source has, with status `corsu-lexicon`, and as a small part of the weight (2 % of a Vikipedia occurrence). Being in a "reviewed" file (Mozilla, Patriccollu's translations) does not make a word attested here. |
| `ai` | Words proposed by the AI agent that built the list | GPL-3.0-or-later | 11 everyday words found in no source above (status `ai-proposal`), listed in REVIEW.md for checking. |

## U Cunghjugarellu (Canopé de Corse)

**What the publisher states.** The book's page on Educorsica (https://www.educorsica.fr/ouvrages/536-u-cunghjugarellu,
consulted 2026-10-18) says "Les documents peuvent être téléchargés et sont placés sous licence creative commons pour
un usage non commercial" and links to CC BY-NC-ND 2.0 France (https://creativecommons.org/licenses/by-nc-nd/2.0/fr/);
its footer reads "Copyright © 2023 CRDP de Corse - Tous droits réservés". The PDF
(https://www.educorsica.fr/phocadownload/pdf/u_cunghjugarellu.pdf, 302 pages, consulted 2026-10-18) has a general
reservation: "toute représentation ou reproduction intégrale ou partielle faite sans le consentement du Canopé est
illicite". These notices concern the publication (its text, tables, layout, explanations and examples). They are
not a licence on Corsican words, conjugated forms or grammar rules, which a book describes but does not own; a
legal deposit records a publication, not ownership of the language. They neither prove that every reuse is
forbidden nor guarantee that every extraction is allowed.

**What Corsu took, and how.** On 2026-10-18 an AI agent read the PDF and wrote down, verb by verb, the present and
imperfect indicative of 21 everyday verbs (tables 1, 2, 3, 23-27, 29, 30, 32, 35, 64, 81, 87, 89, 92, 94-96, 100 of
the book, both versions): `keyboard/data/sources/cunghjugarellu.tsv`, 511 rows, 368 distinct forms, each with the
book's table number, tense, person and version as its reference. No explanation, example sentence, other tense or
page layout was copied. All 368 forms occur in the PDF's text (automated check, 2026-10-18; not a human review).

**What reaches the keyboard packages.** Only words and weights (`keyboard/*/source/wordlist.tsv`): the 368 forms
among the list's words, with no table number, tense, person or label. Of the 368, 187 are also written by an openly
licensed source (Wiktionary, Tatoeba, Vikipedia at least 5 times, Apertium); 181 have no such second source (84 seen
fewer than 5 times in Vikipedia or only in Corsu's lexicon, 97 nowhere else: mostly imperfect plurals such as
*pudiami*, *scriviate*, *tiniami*). The book's *supranacciu* / *suttanacciu* versions decide 253 of the 361 words
weighted differently by the northern and southern preferences.

**Three different uses, assessed separately.**

1. *Checking a linguistic fact* (does *cantavami* exist, is *socu* a southern form of "I am"): this is what each
   form is used for. A correct form is not removed because it was checked in this book.
2. *Reusing explanations, written examples or original editorial choices*: no text or example of the book is
   reused. The one editorial element the data follows is the book's split of each form into *supranacciu* and
   *suttanacciu* (and its choice of the "Sud" imperfect over the Alta Rocca one); it decides which side a form is
   favoured on, and it agrees with the other sources where they overlap (Vikipedia's table: *simu* / *semi*,
   *esse* / *essa*).
3. *Extracting and redistributing a data collection*: the closest thing is `sources/cunghjugarellu.tsv` in the public
   repository, two tenses of 21 of the book's 100 tables, re-laid one form per row. If the maintainer judges that
   file too close to an extraction, a targeted correction would be to keep the forms (they are conjugation facts,
   most of them regular) and replace the per-cell file by Corsu's own paradigm rules for the regular verbs, with
   only the irregular forms listed with their reference. That changes no word and no weight in the packages; it
   only changes how the repository records them. Nothing is blocked meanwhile.

## Consulted but not used

- **INFCOR** (https://adecec.net/infcor): an interactive application with no per-entry address and no stated licence;
  it was not queried automatically. The entries to check by hand are listed in REVIEW.md.
- **Vikipedia's `{{c-supranu}}` / `{{c-suttanu}}` templates**: they are "article under construction" notices written
  in a northern or southern spelling, not a label of the article's variety (1,668 northern, 10 southern); they cannot
  split the corpus by variety.
