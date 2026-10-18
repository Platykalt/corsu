# Minecraft review of October 2026: round 3 (counts, sensitive decisions, sources)

AI work again (one agent, then a separate AI sub-agent that consulted the same passages itself). **Human
validation: 0.** An AI verification is not a speaker's review, and a re-checked sample is not a validation of the
rest. Per-decision records: [round3.tsv](round3.tsv); the same decisions per text, with their validation levels, in
the contextual memory [`lexicon/memory/minecraft-java.jsonl`](../../../lexicon/memory/minecraft-java.jsonl).

## 1. Counts, reconciled

Several numbers were quoted for this review. They count different things:

| Indicator | Round 1 | Round 2 | Round 3 | Where it is measured |
| --- | --- | --- | --- | --- |
| Change proposals examined by the verifier | 239 (58 concrete + 181 language) | 41 deferred rows + 4 older-name rows (H01–H04) | 11 decisions re-examined (round3.tsv) | REJECTED.tsv, APPLIED.tsv |
| Applied decision rows | 133 (130 proposals + 3 verifier extensions) | 12 (R2-01 to R2-12) | 0 | APPLIED.tsv: 145 rows |
| Rejected | 68 (7 concrete + 61 language) | — | — | REJECTED.tsv, verdict "rejected" |
| Deferred | 41 (8 concrete + 33 language) | 30 still deferred = 28 of the 41 + H01, H02 | 30 (unchanged, see section 4) | REJECTED.tsv, verdict "deferred" |
| Resolved from the deferred | — | 13 of the 41: 10 by a change, 3 kept with evidence (U01, B11, L62) | — | REJECTED.tsv rows `-r2` |
| Text listings in APPLIED.tsv (one per row and key) | 1,197 | 27 | — | the `key(s)` column; 66 texts are listed in two rows (for example the oak fences, changed by P01 *querciu* and by B02 *chjudenda*) |
| Distinct texts changed in the round | **1,131** (779 in `co_fr.json`, 352 in `history.json`) | **27** (14 + 13) | **0** | `git diff` of the data between 87188c0 → e9e3252 (round 1) and e9e3252 → 38d3dce (round 2) |
| Successive edits, rounds 1 + 2 | 1,131 + 27 = **1,158** | | | the "1 158" announced |
| Distinct texts changed over rounds 1 + 2 | **1,157** (792 + 365) | | | diff 87188c0 → 38d3dce: one text was changed in both rounds, `commands.team.option.collisionRule.unchanged` (*digià → dighjà* in L123, then *collisione → cullisione* in R2-04) |

So "1,131 texts" (round 1) and "27 texts" (round 2) are distinct texts per round; "1,158" is the number of edits;
**1,157** is the number of texts that differ from the state before the review. "41 deferred" is round 1's count;
after round 2, 28 of them are still deferred, plus two older-name questions (H01, H02): **30 deferred rows**.
APPLIED.tsv round-2 rows listed 24 key names for 27 texts because three rows abbreviated their keys (R2-04,
R2-11, R2-12); the full keys are now written out. Round 1's listings cover exactly the 1,131 changed texts (checked
against the diff: none missing, none extra).

## 2. The INFCOR incident and how it is prevented

**What happened.** On 2026-10-18, between 12:18:52 and 12:42:40, the AI agent that proposed the concrete-name
corrections sent **219 scripted requests** to INFCOR, ADECEC's online Corsican dictionary (139 French and 80
Corsican search words, a few seconds apart), and kept the answers in its scratch folder
(`dl/infcor/*.json`, with `queries.log`). INFCOR is an interactive application with no stated licence and no
per-entry address; Corsu's rule was already to consult it by hand only ([docs/keyboard-sources.md](../../../docs/keyboard-sources.md)).
The agent was stopped; the incident is recorded in [docs/continuite.md](../../../docs/continuite.md).

**What it means for the data.** Rounds 1 and 2 cite INFCOR entries read from that cache (no new query was sent in
the verification or in rounds 2 and 3). Those entries are real answers of the dictionary, but they were obtained
against the project's rule: every INFCOR reference in APPLIED.tsv, round3.tsv and glossary.tsv is marked "cached"
and is listed in section 5 to be **re-consulted by hand, one entry at a time**. Until then they are leads, not
established references.

**Prevention.**
- Every agent prompt for this work carries the rule "no automated querying of INFCOR", including for sub-agents
  (the round-3 sub-agent sent none; it read the existing cache only).
- `tests/test_sources_policy.py` fails if any program in the repository contains an INFCOR address.
- Other resources are consulted page by page within their terms of use (round 3: one fetch of the ADECEC
  *La chaudronnerie* page; the Chemins de fer de la Corse lexicon PDF downloaded once, its pages 101 and 127
  viewed as images, no text copied since the PDF forbids copying).
- Suggested for the maintainer (not changed by an agent): add the rule to AGENTS.md.

## 3. Sensitive decisions re-examined

Method, for each: (1) exact sense in the game; (2) exact entry or page of the source, read again; (3) homonymy,
polysemy, regional variant or mistranslation; (4) independent attestation where one source was not enough;
(5) confirm, correct or defer, in proportion to the evidence. Justifications of the forms "this word means
something else", "looks like Italian", "not found / 0 hits", "frequent in our own lexicon" or a general reference
without an entry were treated as leads only: a change stands only where the new word is positively attested with
the game's sense.

| Id | Decision | Current | Sources read in round 3 | Verdict |
| --- | --- | --- | --- | --- |
| T01 | B15, B15+ Rail family | *Ragliu*, *Ragliu alimentatu / rilevatore / attivatore*; old *Nant'à e raglie* | ADECEC *La chaudronnerie* "rail (nm) : raglia (nf)"; Chemins de fer de la Corse, *Lexique*, printed p. 101 (*ragliu esterioru dirittu*, *ragliu interiore curbu*, *raglie appicciate-aghjunte*, *raglie unte*, *mette-pone e raglie*), p. 127 (*strada ferrata*); INFCOR *ragliu / raglia* n.m. (cache) | **confirmed**, justification corrected |
| T02 | R2-01 Thunder | *Tonu rimbomba*, *piova è à tonu*, *Tonu di u tridente* | ADECEC *Le temps qu'il fait* (5 passages), *La géographie*, *A frutta*, *La maison* (*paratonu*); Vikipedia thunder uses | **confirmed**, justification corrected |
| T03 | P07 Dandelion | *Radichju* (m) | INFCOR *radichju* (EN dandelion, Taraxacum; "fiori turchini"), *lumera*, *strigliulu* (cache); ADECEC *La cuisine* "pissenlit : radichju" and "radis : … radichju"; Vikipedia article *Radichju* = radish, text "radichju (Taraxacum)" | confirmed as an attested, polysemous term; speaker to confirm |
| T04 | B04 Sign | *Cartella* (f) | INFCOR *cartella* (EN "placard, sign"), *cartellu*, *avisu* (cache); ADECEC *Ghjochi è ghjoculi* "cartellu : … 2. Affiche" | confirmed as a preference: the old *cartellu* was not plainly wrong; speaker to confirm |
| T05 | F04 Cake | *Pastadolce* (m) | INFCOR *pastadolce* (EN cake), *torta* (tarte, tourte) (cache); ADECEC *La cuisine* "gâteau : pastadolce, dolce", "tarte : torta" | **confirmed** |
| T06 | B06 Smithing Table, Toolsmith | *Bancu di stazzunaru*, *Stazzunaru d'attrezzi* | ADECEC *La chaudronnerie* "établi : bancu", "forge : stazzona"; INFCOR *stazzunaru*, *ferrale* (cache) | Smithing Table confirmed as a **compound built from attested words** (not attested as a unit); Toolsmith deferred on *attrezzi* |
| T07 | A01 Sheep (kept) | *Pecura* (f) | INFCOR *pecura* "brebis, mouton, ovin; Estens. …", *muntone* SIN "pecura (Sudu)" (cache); ADECEC; Vikipedia *Pecura* (species article; says the term is reserved for the ewe) | **kept**: no better contextual proof |
| T08 | R01 Diorite (rejected change) | *Diorite* | INFCOR *petra uchjata* (diorita in a definition, cache); Vikipedia *diurita* 1 | **deferred**: *diurita* not forced by graphic analogy |
| T09 | P06 Moss | *murzu / murzosu* | INFCOR *marmuzzu* (SIN murzu), *murzosu* (moussu), 19 *muscu-* entries (cache) | **confirmed**, justification corrected (rests on *murzu*, not on "muscu = musk") |
| T10 | A04 Squid | *Totanu* | INFCOR *totanu* (EN squid), *calamaru* (inkwell) (cache) | **confirmed**, justification corrected |
| T11 | L115, L116 Donkey, Mule | *raglia* | no entry in the caches; homograph of *raglia* (rail, f.) | **deferred** |

### Rail (B15) in detail

- Sense in the game: the track block a minecart runs on; Powered, Detector and Activator are redstone variants;
  "On A Rail" (old achievement) is a long minecart journey.
- Sources: two independent sources give the railway sense: ADECEC's *La chaudronnerie* (feminine singular *raglia*)
  and the Corsican railway company's lexicon (masculine singular *ragliu* with masculine adjectives; plural *raglie*
  with feminine plural agreement). INFCOR (cache) has *ragliu* n.m., variant *raglia*.
- Reasoning corrected: "*binariu* means binary, so it cannot mean a rail" is withdrawn. *Binariu* is used for
  "binary" in Vikipedia and in this file's keypad key, but a word can carry both senses (Italian *binario*). The
  change is a documented terminological preference (the railway term, and one word per sense inside the file), not
  the proof that *Binariu* is wrong. Keeping *Ragliu* is supported; it is not replaced by *Binariu* on another AI's
  claim.
- Forms checked one by one, not derived from one entry: *Ragliu* (m. sg.); *Ragliu alimentatu*, *Ragliu
  rilevatore*, *Ragliu attivatore* (masculine adjectives, as *ragliu interiore curbu*; the three adjectives are the
  game's own compounds, not in the railway lexicon); old title *Nant'à e raglie* (plural, feminine article *e*, as
  *mette-pone e raglie*). A speaker could prefer ADECEC's *raglia* (f.) in the singular: then every adjective would
  change (*raglia alimentata*…). *Raglia* is also the verb "brays" in the donkey and mule subtitles; the names use
  *ragliu*, so the two never meet.

### Thunder (R2-01) in detail

*Tonu* is attested for "tonnerre" in four ADECEC lexicons and used in that sense in Vikipedia; it is polysemous
(also tone, and pitch in the old `/playsound` usage "[tonu]"). *Tronu* means throne in every text consulted (98
Vikipedia occurrences read, Wiktionary): that shows why *tonu* is clearer, not that *tronu* cannot be a regional
word for thunder. That question stays in the manual list (INFCOR "tonnerre", "tronu").

### Applied rows with a fragile justification (not re-verdicted one by one)

These applied rows of round 1 give "not found", "Italian form" or "means something else" as part of their reason
(A04, A06, A07, F01, F03, P01–P04, P06–P08, P10, P11, P13, R05, R06, M01, M02, M04, B01, B02, B05, B07–B09, I02,
I04, I05, B14, B15, A16, and language rows L14, L16, L30, L31, L98, L103, L118, L123, L126, L138, L165, L175, L188,
L193, L198, L201). In each, the change also cites a positive attestation of the new form (an entry with the game's
sense, or the form used elsewhere in the file), which is what the change rests on; the negative part is a lead
only. Round 3 re-read in detail only the rows in the table above. Those resting on a single INFCOR entry from the
cache are in the manual list (section 5).

## 4. Deferred cases after round 3

All 30 deferred rows (REJECTED.tsv, verdict "deferred", ids `-r2`) were re-read against the local caches; no new
evidence was enough to decide one, so none was changed:

- concrete: R11 *cinabru* (no entry), R12 *petrame* (ADECEC *La géographie* "pierraille : petricaglia" is a new lead,
  not a match for Cobblestone), M11 *lingottu* (ADECEC "lingot : asta, astone"), B13 *cocciu* (ADECEC *piattini* =
  tessons), U03 *stillicciu* (INFCOR *stalattita*, *candeleru*; ADECEC "stalactites de glace : stalattitte,
  candileri, candilotti");
- language: L114 (verb *sciaccheghja*), L4, L29, L82–L84 (focus), L53, L58, L66, L91, L102, L105–L107, L115–L116
  (*raglia* / *annitrisce*), L120 (*grugna*), L157–L161, L199 (*aghjurnà* / *mette à livellu*);
- older names: H01 (*Ovu generatore* + name), H02 (*Lampabile*);
- added in round 3: *attrezzi* in Toolsmith (T06), *Diorite* (T08).

## 5. Manual consultations still needed

Nothing below may be done by script.

**INFCOR, by hand, one entry at a time** (to replace the cached answers of the incident):
- entries cited by applied decisions: *totanu*, *calamaru* (A04); *apa* (A05); *camellu* (A06); *cudutu*,
  *capaccione* (A07); *patecca* (F01); *custiglietta* (F02); *caccaò* (F03); *pastadolce*, *torta* (F04);
  *querciu* (P01); *biolu* (P02); *abetu* (P03); *chjarasgiu* (P04); *marmuzzu*, *murzosu*, *muscu* (P06);
  *radichju*, *strigliulu*, *lumera* (P07); *pappaveru* (P08); *rosulaghju* (P10); *pigonia* (P11); *lillà* (P12);
  *nenufaru* (P13); *petra rinaghja* (R05); *gravetta* (R06); *arzilla*, *calcinella* (R07); *lapislazzuli* (R10);
  *mattone* (M01); *astracu* (M02); *tappettu* (M03); *tinta* (M04); *caterazza* (B01); *palancatu*, *sticcatu*
  (B02); *cartella*, *cartellu* (B04); *incudine / ancutina* (B05); *stazzunaru*, *ferrale* (B06); *trimoghja*
  (B07); *pulpitru* (B08); *spunga* (B09); *vagunettu* (I01); *zattera* (I02); *catinetta* (I04); *orillogiu*
  (I05); *torchja* (B14); *ragliu / raglia* (B15); *cunciadore* (A16); *stalattita* (R2-06); *macina*, *mola*
  (B11); *pecura*, *muntone* (A01);
- open questions: "tonnerre" and *tronu* (regional thunder?); "cinabre"; "pierraille", *petrame*, *petricaglia*;
  "lingot"; "tesson", *piattinu*; "stalagmite", "concrétion"; "braire", "hennir", *raglià*, *annitrisce*;
  "grogner", *grugnà*; "diorite"; "outil" (*attrezzu*); "mettre à jour", "mise à niveau".

**Other resources, page by page:**
- ADECEC lexicon pages already read (cached copies of 2026-10-18; re-open in a browser to confirm): *La
  chaudronnerie* (rail, établi, forge, lingot), *Le temps qu'il fait* (tonnerre), *La géographie* (tonnerre,
  récolter, pierraille), *La cuisine* (gâteau, tarte, pissenlit, radis), *La maison* (échelle), *Filage et tissage*
  (brebis, mouton), *Ghjochi è ghjoculi* (cartellu, tessons);
- G. M. Weber, *A matina* (CRDP Corsica 2013), vocabulary p. 108 (*pecura*): cited by round 1, not re-opened;
- a Corsican geology text for *diorite / diorita / diurita*;
- a speaker for every row marked "speaker" in round3.tsv and REJECTED.tsv.

Done by hand in round 3 (one consultation each): ADECEC *La chaudronnerie* (fetched once); Chemins de fer de la
Corse, *Lexique* (PDF downloaded once), printed pages 101 and 127 viewed as images.

## 6. Data, memory and checks

- Texts changed in round 3: **0**. No decision was corrected in its wording in the game; only justifications,
  references and statuses were corrected (APPLIED.tsv B15 and R2-01, concrete.md, glossary.tsv). Nothing to
  propagate across versions; the agreement of every form of the re-examined decisions was checked in 26.3 and in
  `history.json` (gender, plural, articles).
- Contextual memory: `tools/mcmemory.py` writes one entry per text a decision touched (1,157 changed texts + 20
  texts of kept or deferred decisions = 1,177), with key, versions, sense, current Corsican, decision, references
  and three separate validation levels (`ai_proposal`, `ai_review`, `human: none`). No English text is stored (only
  its hash). The entries are marked `"reuse": "same-app"` and `engine.lookup` / `tools/tm.py match` never offer
  them to another program, so Minecraft's *Cartella* (sign) or *Ragliu* cannot become another program's "Sign" or
  "Rail" (the Bio/Organicu and Profil/Force Profile kind of contamination); tests in `tests/test_memory.py` and
  `tests/test_mcmemory.py`.
- Checks after round 3 (Python checks and checks with the game's code kept apart): see TRACKING.md, round 3.
