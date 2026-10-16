# Corsican language resources

Corsu checks its translations against outside resources. This page lists them, with what each one can prove and on
what terms it can be used. Inventory made on 2026-10-16.

**A dictionary entry is lexical evidence, not a sentence validator.** A word found in a resource shows the word exists
with that meaning; it says nothing about the grammar of the sentence around it. A word missing from a resource is not
therefore wrong: none of the downloadable resources below is a full dictionary of Corsican.

## Downloaded and reusable

`python3 tools/fetch_resources.py` downloads these into `~/.local/share/corsu/resources` (or `$CORSU_RESOURCES`) and
writes `manifest.json` there with each file's URL, date, size and SHA-256. They are not committed: some are large, and
Patriccollu's repository has no license. The list, with URLs and licenses, is [sources.json](sources.json).

| Resource | What it is good for | Size | License |
| --- | --- | --- | --- |
| Mozilla Pontoon terminology (`co.v2.tbx`) | software terms chosen by the Corsican Mozilla team | about 211 terms | Mozilla project content |
| Mozilla Pontoon translation memory (`co.all-projects.tmx`) | how sentences of Firefox for Android and iOS, Focus, VPN were translated | 3.6 MB | Mozilla project content |
| English Wiktionary, Corsican entries (Kaikki JSONL) | meanings, inflections, some regional labels | about 900 words | CC BY-SA 4.0 / GFDL |
| Wikizziunariu dump | Corsican Wiktionary pages | about 9,600 pages | CC BY-SA 4.0 |
| Vikipedia dump | whether and how often a form is used in written Corsican | about 9,500 articles | CC BY-SA 4.0 |
| Apertium `apertium-cos.cos.dix` | lemmas and inflection paradigms | about 6,300 entries, last updated 2021 | GPL-3.0 |
| Unicode CLDR `co.xml` | language, country, month and day names | 78 KB | Unicode License v3 |
| Tatoeba Corsican sentences | example sentences | 55 sentences | CC BY 2.0 FR |
| OPUS translatewiki co-en | MediaWiki interface strings | about 1,300 pairs | per project |
| Patriccollu, Lingua_Corsa-Infurmatica | notes and translation memories of the main Corsican software translator | 4.5 MB | none stated: local consultation only |

`python3 tools/corsican_words.py index` builds `words.tsv` from them (about 218,000 forms). Then
`python3 tools/corsican_words.py lookup word …` shows, for each word, its Vikipedia count, whether Apertium and
Mozilla's terminology have it, and its Wiktionary glosses.

The variants are mostly unlabelled. Vikipedia and Mozilla use the standard written Corsican of most publications;
Wiktionary sometimes marks a form as Cismontane (northern) or Ultramontane (southern).

## Lookup only

These are the larger dictionaries. None offers an export or a license allowing a copy, so Corsu does not download them.
Check uncertain words in them by hand.

| Resource | Owner | Contents | Conditions |
| --- | --- | --- | --- |
| [INFCOR](https://www.adecec.net/infcor/) | ADECEC | Corsican dictionary with French, Italian and English equivalents and variant forms; the largest one available | No license stated. The site's robots.txt excludes its `/try/` pages, so Corsu does not query it automatically. A bulk copy would need ADECEC's agreement. |
| [BDLC, Banca Dati di a Lingua Corsa](https://bdlc.univ-corse.fr/bdlc/corse.php) | Università di Corsica, UMR CNRS LISA 6240 | dialect atlas: forms by village, phonetics, audio | "Aucune reproduction ou représentation ne peut être réalisée en contravention avec les droits de la BDLC". Its TAL corpora are downloadable: Wikipedia 2019 (CC BY-SA 3.0), Bible and A Piazzetta (CC BY-NC-SA 4.0, non-commercial). |
| [Sapienzia](https://www.sapienzia.io) | private | dictionary, conjugation, machine translation | terms forbid mass extraction; its machine translation is not a reference |
| [Educorsica lessicu](https://www.educorsica.fr/lessicu/), [cunghjugazione](https://www.educorsica.fr/cunghjugazione/) | Canopé di Corsica | school terminology (with a computing domain), conjugation | no license stated |
| ADECEC, Bastia and Ajaccio thematic lexicons (PDF) | ADECEC, cities | French-Corsican word lists by topic; Bastia's manga list has *videoghjocu* | no license stated |

No public Corsican spellchecker (Hunspell) was found, and no Corsican terminology for video games beyond a few words.
Most Minecraft terms in [minecraft/java/glossary.tsv](../minecraft/java/glossary.tsv) are therefore proposals.
