# Historical and geographic names of Corsica: reference inventory

`sources/historical-places.tsv` lists, with a reference for each spelling, names of Corsican micro-regions,
historical regions and divisions, pievi (pièves), dioceses, episcopal sees and Genoese provinces. It is a reference
inventory for the Keyman keyboard dictionaries. **The build does not read it**: `tools/make_vocab.py` and the word
lists are unchanged. Whatever goes into `shared.tsv` from it is a separate, reviewed step.

This is **not** "all historical names of Corsica". It covers the categories above, as far as the reference lists
named below allow checking. Every other kind of historical name (hamlets, castles, seigneuries, cantons before
1973, Roman and Ptolemaic names, parishes and *cappelle*) is out of scope.

## Format

UTF-8, LF, `#` comment lines at the top, then one header row and one row per (spelling, category):

| Column | Content |
|---|---|
| `name` | The spelling exactly as attested: capitals, accents, hyphens and spaces kept. An article (*E Vallerustie*, *A Costa*, *A Terra di i Signori*) is kept only when a source writes it as part of the name; the bare form has its own row only when it is attested bare. Apostrophes are ASCII, as in the rest of `keyboard/data`. |
| `canonical` | The preferred Corsican form of the place (equal to `name` on the preferred row). It is empty when the sources read give no Corsican form (5 French pieve names, some French micro-region names, *Province de Corse*). |
| `usage` | The language of this spelling: `co`, `fr`, `it` (`co-historical` and `la` are allowed but not used yet). When one spelling is both Corsican and French (*Vallerustie*, *Orezza*, *Mariana*), there is a single `co` row and the note says "same spelling also fr". |
| `category` | `micro-region`, `historical-region`, `pieve`, `diocese`, `episcopal-see`, `province`, `historical-division`. A pieve, a diocese and a micro-region can share a name without being the same territory: each gets its own row (*Nebbiu* is a pieve, a diocese, a province, a royal juridiction and a micro-region). `historical-region` is not used: the large historical areas (Cismonte/Pumonte, Terra di Comune, Terra di i Signori) are under `historical-division`. |
| `period` | When it matters ("Genoese period (created 1570-1660)", "12th c. to 1563", "district 1790"), otherwise empty or "present-day". |
| `status` | `accepted`: written so, as the name of this place in this category, in the cited source. `uncertain`: one weak attestation (a Wikidata label alone, a section heading, an uncited lead sentence) or a disputed name. `deferred`: a historical (Italianate) spelling or a name out of scope for the keyboard. |
| `reference` | Page and section, with the revision id for Wikipedia pages, or the publication and page. |
| `note` | Why a row is uncertain, alternative names, links between rows. |

## Method

- Pages were read one at a time on 2026-10-19 (about 35 page reads). No dictionary (INFCOR/ADECEC, BDLC or any
  other) was queried, nothing was crawled, and no Wikidata query was run for this file. The Wikidata labels already
  in `sources/places.tsv` are cited as corroboration only: a row that rests on a Wikidata label alone is `uncertain`.
- Only names were taken from descriptions and quotations, never ordinary vocabulary.
- No variant was made up by analogy. Each spelling has its own attestation, including the written stress accents
  (*Tàlcini*, *Càrbini*, *Òpinu*) that the Corsican Vikipedia list uses in some paragraphs and not others.
- Vikipedia (co) is cited as such: it is the source for Corsican spelling, but most of its pages cite no source
  for the spelling itself.

## Reference inventories (what each category was checked against)

| Category | Reference list | Notes |
|---|---|---|
| Dioceses (6) | Collectivité Territoriale de Corse, *Cathédrales et pro-cathédrales de Corse*, Direction du Patrimoine, 2008, p. 3 (PDF on isula.corsica). Corsican forms: the Vikipedia (co) diocese articles and the *Lista di e pieve di Corsica*. | Six dioceses: Mariana, Nebbio/Nebbiu, Accia, Aleria, Sagone, Ajaccio/Aiacciu. Accia was created in 1133 from Rostino (Aleria) and Ampugnani (Mariana) and suppressed in 1563. The 1801 bull suppressed Mariana, Accia, Aleria, Sagone and Nebbio. The list asked for (Mariana, Nebbiu, Aleria, Sagone, Aiacciu, Accia) is confirmed. |
| Episcopal sees | Same CTC publication, pp. 4-14 and the map on p. 14 (after G. Moracchini-Mazel). | The cathedral or pro-cathedral towns: Lucciana (Mariana), Bastia (Mariana from 1571), Cervione (Aleria from 1578), Vico (Sagone from 1572) and Calvi (from 1625), Saint-Florent (Nebbio), Ajaccio. Corsican forms only where read: San Fiurenzu, Vicu, Cervioni. |
| Pievi | Vikipedia (co), *Lista di e pieve di Corsica* (rev. 405153): the pievi of each diocese after Moracchini-Mazel, *Les églises romanes de Corse* (1967), plus the pievi Giustiniani counts in *Dialogo nominato Corsica* (tr. A.-M. Graziani, 1993). Completed by the Vikipedia navbox *Template:Pievi di Corsica* (rev. 405424, 76 pievi of all periods) and, for French forms, *Catégorie:Piève de Corse* and *Liste des pièves de Corse* on Wikipédia (fr). | 105 pievi have at least one accepted Corsican spelling; 5 have only a French form (Conca, Freto, Regino, Rogliano, Vivario). All 55 Wikidata pieve items of `places.tsv` (54 distinct labels) are covered. These lists mix periods: Giustiniani's medieval pievi, the 16th-century administrative pievi (Ferringule, Oletta, Patrimoniu) and the later Genoese ones (Algaiola, Avretu, Seneca, Tuda, Vechju…). The Vikipedia list itself warns that Moracchini-Mazel's reconstruction is not accepted by all researchers. |
| Genoese provinces | Wikipédia (fr), *Corse (province)* § Histoire: the eleven provinces created between 1570 and 1660, with French article titles and Corsican display forms. Cross-checked with *Liste des pièves de Corse* § Provinces et fiefs (after F. M. Accinelli, early 18th c.). | The two lists disagree: Accinelli has 10 provinces and 4 fiefs (Nonza, Brando, Canari, Istria) and 15 juridictions. Neither is an institutional source: this category needs a historical publication (Graziani, Serpentini). |
| Other divisions | Royal juridictions to 1790 and the nine districts of 1790: *Liste des pièves de Corse* § Pieves sous l'administration française and § Pievi au XVIIIe. Departments Golo/Liamone: *Histoire de la Corse*, *Géographie de la Corse*. Cismonte/Pumonte, Diquà/Dilà da i Monti: Vikipedia (co) *Ugo Colonna*, *Castagniccia*, *Orezza*, *Conti di Corsica*; Wikipédia (fr) *Deçà des Monts*, *Delà des Monts*. Terra di Comune / Terra di i Signori: Wikipédia (fr) *Sambucucciu d'Alandu*, *Géographie de la Corse*, *Noblesse corse*; Vikipedia (co) *Cunventu d'Orezza*. | No closed reference list. |
| Micro-regions | No institutional list was found. Rows come from Vikipedia (co) *Castagniccia* (its *regione minore*), Wikipédia (fr) *Microrégions de Corse* and *Géographie de la Corse*, the tourist office of Pasquale Paoli (Rustinu / Vallerustie / Caccia) and the Wikidata regions of `places.tsv`. | Not a closed inventory: present-day micro-regions vary with the body that defines them (Parc naturel régional, tourist offices, communautés de communes), as *Microrégions de Corse* itself says. The Università di Corsica's "Inventaire préliminaire du patrimoine bâti … (micro-régions de la Corse)" (M3C) is organised by canton (Bustanico, Alto-di-Casaconi…), so it does not give micro-region names. |

## Vallerustie (priority)

| Spelling | Where | Exact text |
|---|---|---|
| Vallerustie | Università di Corsica, M3C notice 95519 (Aiti; A. Casanova, J.-F. Guignon; collection "Inventaire préliminaire du patrimoine de la Corse (bâti) … micro-régions de la Corse") | "Aiti est situé sur le canton de Bustanico, plus précisément dans la pieve de Vallerustie." |
| E Vallerustie | Office de tourisme Pasquale Paoli, page *Rustinu / Vallerustie*, § Cambia | "Cambia est situé dans la pieve d’E Vallerustie" |
| Vallerustie | Same page: title "Rustinu / Vallerustie", heading "Les communes de Rustinu / Vallerustie", § San Lurenzu | "San Lorenzo, ou San Lurenzu di Vallerustie est situé en centre corse" |
| Vallerustie | Vikipedia (co), *Vallerustie* (rev. 363903) | "Vallerustie hè u nome d'un anziana pieve di Corsica à u Medievu. Facia parte di a diòcesi d'Aleria." Map caption: "Lucalizazione di a pieve di E Vallerustie". |
| Vallerustie (micro-region) | Vikipedia (co), *Castagniccia* | "e regione minore vicinante di u Casaccuni, di u Rustinu è di u Vallerustie" (masculine *u*, against the feminine plural *E* of the tourist office) |
| Vallerustie (fr) | Wikipédia (fr), *Vallerustie*, *Microrégions de Corse* | "Vallerustie est une ancienne piève de Corse … elle relevait de la province de Corte sur le plan civil et du diocèse d'Aléria sur le plan religieux." |
| Valle Rustia (it, 16th c.) | Wikipédia (fr), *Liste des pièves de Corse*, table of the 16th century (after A.-D. Monti) | row "Valle Rustia … pieve"; the 18th-century table (Accinelli) of the same page writes "Pieve di Vallerustie" |

Conclusions: *Vallerustie* (one word, capital V) is the form used in Corsican and in French. *E Vallerustie* is
attested with the article as part of the name, and the bare form is attested too: both are `accepted`. No source
read writes "Valle Rustie" or "Vallerustia" (a web search for both found nothing), so neither is listed. *Valle Rustia*
is a 16th-century Italian spelling and is `deferred`. The pieve covered San Lurenzu, Aiti, Lanu, Erone, Rusiu,
Carticasi and Cambia (Vikipedia), in the diocese of Aleria and the Genoese province of Corte. *Vallerustie* is
neither in `places.tsv` (Wikidata has no co label for it) nor in `shared.tsv`.

## Counts (2026-10-19)

330 rows; 269 distinct spellings (229 of them in at least one accepted row, 150 distinct accepted Corsican
spellings). Usage: 206 co, 100 fr, 24 it.

| Category | accepted | uncertain | deferred | total |
|---|---:|---:|---:|---:|
| pieve | 184 | 5 | 10 | 199 |
| historical-division | 39 | 6 | 7 | 52 |
| micro-region | 31 | 11 | 0 | 42 |
| province | 17 | 1 | 1 | 19 |
| diocese | 9 | 0 | 0 | 9 |
| episcopal-see | 9 | 0 | 0 | 9 |
| **total** | **289** | **23** | **18** | **330** |

## Comparison with shared.tsv (accepted Corsican spellings, 150)

Case-sensitive comparison with `shared.tsv` at bff7ba1:

- **Already an entry (66)**: Aiacciu, Aleria, Alisgiani, Ampugnani, Appiettu, Aregnu, Balagna, Bastia, Bevincu,
  Bigornu, Bonifaziu, Boziu, Brandu, Bunifaziu, Calvi, Campulori, Canari, Capicorsu, Carbini, Casacconi, Casàccuni,
  Casinca, Castagniccia, Cavru, Celavu, Cervioni, Chjumi, Chjurlinu, Cinarca, Cismonte, Corti, Cruzinu, Cursa, Custera,
  Ferringule, Figari, Ghjunsani, Ghjuvellina, Istria, Liamone, Lota, Lumiu, Luri, Matra, Moriani, Nebbiu, Niolu, Nonza,
  Oletta, Olmia, Opinu, Orezza, Portivechju, Pumonte, Rustinu, Salogna, Sartè, Siscu, Talcini, Tallà, Tavagna, Tuani,
  Tuda, Tuminu, Venacu, Àrmitu.
- **Multi-word names whose words are all entries (3)**: San Fiurenzu, Seve Infora, Seve Ingrentu.
- **Only as a lowercase common word (25)**: A Costa, A Porta, A Porta d'Ampugnani, A Terra di i Signori, Caccia,
  Canale, Castellu, Ortu, Patrimoniu, Pinu, Quadru, Rogna, Rosulu, Santa Riparata, Santu Andria, Santu Petru, Serra,
  Sia, Terra di i Signori, Vaddi, Valle, Vechju, Verde, Vicu, l'Isula Rossa. These need the capitalised form only if
  the keyboard does not capitalise suggestions at the start of a name.
- **New (56)**: Accia, Algaiola, Armitu, Attallà, Attalà, Avretu, Bisughjè, Bivincu, Calinzana, Campuloru, Casaccuni,
  Chjappella, Cruscaglia, Cuvasina, Cànari, Càrbini, Cèlavu, Dilà da i Monti, Diquà da i Monti, E Vallerustie,
  Falasorma, Liòli, Luzzipeu, Marana, Mariana, Mercoriu, Mizana, Ostriconi, Paomia, Pumonti, Reonda, Ròsulu, Sagone,
  Sagri, San Ghjuvanni di Brùmica, San Quilicu, Sant'Andria, Scupamena, Seneca, Sevindentru, Sorru Inghjò, Sorru Insù,
  Sorru in Ghjò, Sorru in Sù, Talavu, Tàlavu, Tàlcini, Tòcchisu, Urnanu, Urtolu, Urtòlu, Valincu, Vallerustie,
  Vighjanu, Vighjeni, Òpinu.

Whether the accented variants (*Tàlcini*, *Càrbini*, *Òpinu*…) belong in the keyboard is an editorial choice: they
are attested, but only in one paragraph of one Vikipedia page each.

## Gaps and uncertain cases

- **Pievi**: the reference list is a Vikipedia page built on Moracchini-Mazel and Giustiniani. Neither book was read
  here, and the list's own counts differ between paragraphs (Sagone: "vinti pieve" listed, twelve in Giustiniani).
  No Corsican form was found for Conca, Freto, Regino, Rogliano and Vivario. Some names in the French list were
  left out: "Sorno in sù", probably a misprint for Sorru in Sù. The Italianate spellings Ostricone, Rosolo,
  Sevendentro, Talabo, Veggeni, Tocchisi, Bisogeni, La Costa and Capo Bianco are listed as `deferred`. The 16th- and
  18th-century tables of *Liste des pièves de Corse* (Cachia, Carbeni, Pieve di Ampugnai…) were not transcribed.
- **Same-name conflicts**: *Seve Infora* is labelled Paomia in French on Wikidata, while the Corsican list keeps
  Paomia apart and gives *Sevinfora* as another name of Sia (`uncertain`). Bigornu and Custera are both accepted:
  the French list equates Bigorno with Costiera. Mariana and Marana name the same pieve. *Lama*, *Ustriconi*,
  *Bonifaziu* (as a pieve), *Capu Biancu* and *Vaddincu* rest on Wikidata labels alone (`uncertain`).
- **Provinces**: the 11-province list and the 10 + 4 fiefs list come only from Wikipédia. *Capi Corsu* (two words)
  is found only there (`uncertain`); elsewhere the form is *Capicorsu*. An institutional or scholarly list of the
  Genoese provinces and juridictions (e.g. Archives de Corse, A.-M. Graziani, A. L. Serpentini) is still needed.
- **Terra di u Cumunu** is `uncertain`. Vikipedia (co) uses it, but A.-M. Graziani, quoted in *Géographie de la Corse*,
  says "La Terra di u Cumunu n'a jamais existé": the historical name is *Terra di Comune* (the land of the Commune
  of Genoa). The Italian *Di quà dai monti*, *Di là dai monti*, *Banda di dentro* and *Banda di fuori* come from
  uncited Wikipédia leads (`uncertain`). *Pumonti* is attested only in French Wikipedia leads.
- **Micro-regions**: the Corsican section headings of *Microrégions de Corse* (Curtinese, Sartinesu, Viculacciu,
  Tavignanu, Fiumorbu, Taravu-Ornanu, Gravona-Prunelli, Bagnaja) are `uncertain`. The Parc naturel régional's
  *territoires de vie* and the Collectivité de Corse's planning areas were not read. *Strinse* and *Gaghju* have one
  Vikipedia mention each.
- **Sources not reached**: Archives de Corse (no page on the pievi or provinces was found), the Università's
  "Lieux de mémoire de la Corse médiévale", and printed works (Moracchini-Mazel 1967, Giustiniani/Graziani 1993,
  *Dictionnaire historique de la Corse*, 2006). Each of them could promote or correct rows.
- Agostino Giustiniani's own Italian forms were not read in the original. The `it` rows are the forms Wikipédia
  quotes.
