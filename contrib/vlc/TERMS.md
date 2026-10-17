# VLC 3.0.x Corsican drafts: AI review, terminology and open questions

Full AI review of the 1,760 drafts of `co.po` on 2026-10-17, in two thematic batches with one reviewer per entry
(interfaces and display: 881 entries; processing modules: 879), then a cross-batch consistency pass. Per-entry
verdicts, notes and the original drafts are in `review.json`. This is not a review by a Corsican speaker: every draft
keeps its fuzzy flag until one validates it.

Counts: 1,757 drafts reviewed by AI (1,580 kept as drafted, 177 corrected; the consistency pass corrected 3 of them),
3 uncertain (left out of the experimental build).

## Batch 1: interfaces and display
Sources: Patriccollu's upstream entries in `contrib/vlc/co.po` (quoted as `EN = CO`), and Corsican catalogues of other projects in `lexicon/memory/*.jsonl`: VLC for Android, wxWidgets, Mozilla, Audacity/Tenacity and others.

Typography follows the upstream file: a space before `:` `?` `!`, the apostrophe ’, « » around quoted UI words, and the source's `...` or `…` kept. Every colon in this batch already had a space before it.

### Established terms (attested)

| EN | CO | Attestation |
|---|---|---|
| release (compressor) | dillinata | `Release time = Tempu di dillinata` |
| attack | attaccu | `Attack time = Tempu d’attaccu` |
| knee radius / makeup gain | raghju di u ghjinochju / guadagnu makeup | upstream compressor options |
| preset | prerigatura | `Equalizer preset = Prerigatura di l’ugualizatore` (upstream also has two stray "preset") |
| tuning | rigatura | `System Tuning Spaces = spazii di rigatura di u sistema` |
| tuner | tuner | `Tuner properties = Pruprietà di u tuner` |
| raw | dati grossi | `Save raw codec data = Arregistrà i dati grossi di u cudecu` |
| dump | viutà / viutatura | `Dump module = Modulu di viutatura` |
| algorithm | metoda di calculu | `Enable noise reduction algorithm = Attivà a metoda di calculu di riduzzione di trostu` |
| noise | trostu | `Noise reduction = Riduzzione di trostu` |
| grain | grombulu | `Grain = Grombulu` |
| flicker | scintillime | `Power line frequency anti-flicker filter = Filtru antiscintillime…` |
| deblocking | sblucchime | `Deactivate the deblocking loop filter = … filtru d’iterazione di sblucchime` |
| loop (playlist mode) | iterazione | `Toggle Normal/Loop/Repeat playlist modes = … Nurmale/Iterazione/Ripete` |
| always on top | sempre sopra | `Always on top = Sempre sopra` |
| dark / bright (style) | scuru / chjaru | `Dark = Scuru` |
| detection | scuperta | `Autodetect subtitle files = Scuperta autumatica…` |
| extended | allargatu | Qt `Extended panel`, upstream "pannellu allargatu" |
| native | d’urigine / nativu | `Use the native fullscreen mode = … modu d’urigine di screnu sanu`; `Prefer native stream recording = … nativu` |
| original | uriginale | `Original = Uriginale` (not "urigginale") |
| workaround | suluzione/soluzione timpuraria | `Workaround for France = Soluzione timpuraria per a Francia` |
| clipboard | preme’papei | `Open &Location from clipboard = … da u preme'papei`; Mozilla catalogues |
| trash | curbella | Mozilla VPN / Focus: "l’icona di a curbella" |
| palette | tavuletta | VLC for Android (Patriccollu): `Palette (pulls colors from the media cover) = Tavuletta (…)` |
| Del key | Suppr | wxWidgets Corsican: `Del` (keyboard key) = `Suppr` |
| algorithm, by default | in modu predefinitu / U valore predefinitu hè… | upstream "By default" strings; "per difettu" is also attested 409 times in other Corsican catalogues, so it was kept |
| All (prefs) / Main interfaces / Password | Tutti / Interfaccie principale / Parolla d’intesa | upstream; used in the httpd.c menu path |
| interfaces (plural) | interfaccie | upstream spelling (not "interfacce") |
| device | apparechju | `DVD device = Apparechju DVD` (upstream uses apparechju, not periferica) |
| No X found | Nisunu X trovu | `No video devices found = Nisunu apparechju video trovu` |
| Manage Streams | Urganizà i Flussi | upstream |
| Library (web UI) | Bibliuteca | `Hide / Show Library = Piattà / Affissà a Bibliuteca` |
| rate (playback) | cadenza | `Normal rate = Cadenza nurmale` |

### Terminological proposals (no direct attestation; reasoned)

- **Dimensione d’affissamentu** for "Display size", the playlist view's icon size. "Affissera" means the monitor and would be wrong here. *Affissamentu* is the regular noun from upstream *affissà*.
- **[Affissà]** as the ncurses help heading "[Display]". It follows upstream `Display = Affissà`, a verb used as a section name.
- **Ghjocu di puzzle**, **Cartone animatu**, **Tasselli di musaica**, **reta di maglie** (projectM mesh) and **tessitura** (texture) are kept as drafted. They are plain descriptive renderings with no upstream equivalent.
- **Addulcisce** for the video effect "Soften" (uncertain, see below).

### Flagged words found in this batch

- **sfarfallime** (2 entries: "Anti-Flickering" and "no flickering"): not attested in upstream or in the Corsican memory. Patriccollu coined **antiscintillime** for anti-flicker, so it was replaced by *scintillime* / *Antiscintillime*. Verdict: unattested AI coinage, replaced by the upstream coinage.
- **tavuletta** ("Use a dark palette"): an **established term**. Patriccollu uses *Tavuletta* for "Palette" in VLC for Android (`lexicon/memory/vlc-for-android.jsonl`, key `palette`). Kept.
- **Addolce** ("Soften"): this form is not attested. Corsican translations do attest *addulcitu* ("adouci") and *Addulcitore*, which point to the infinitive *addulcisce* (or *addulcì*). Verdict: **uncertain**. The proposal is *Addulcisce*, by analogy with upstream *Invertisce* used as an infinitive label.
- mudellatura, accolta, imbulighju: none occur in this batch. *accoglie* ("collect", privacy text) is an ordinary verb and was kept.

### Uncertain cases

| id | Source | VLC context | Proposal |
|---|---|---|---|
| 002095affa24 | "Soften" | Qt Video Effects > Essential, checkbox (video_effects.h:1336) | Addulcisce (a speaker should confirm the infinitive: addulcisce or addulcì) |

## Batch 2: processing modules
Sources: Patriccollu's upstream co.po (cited by English msgid); the Corsu translation memory
(`lexicon/memory/*.jsonl`, imported files only, no `corsu-*` rows); INFCOR (queried through
`https://adecec.net/infcor/try/swift.php`); the VLC 3.0.x sources; the fr/it/es/de/pt_BR/ca catalogues of 3.0.x.

### Established terms (attested), applied in this batch

| EN | CO | Attestation |
|---|---|---|
| milliseconds / microseconds | milliseconde / microseconde | upstream "Caching value for local files, in milliseconds" -> "in milliseconde" (the drafts had "millisecondi") |
| override (v) | supranà | upstream "This overrides the routing table" -> "supraneghja"; "Override the name and version…" -> "Supranà…" |
| apply (to) | appiecà | upstream "will be applied to outputted audio" -> "appiecatu"; "Affettà" is used only for the Apply button |
| support (n) | pigliata in carica | upstream "Blu-ray Disc support (libbluray)" -> "Pigliata in carica di u discu Blu-ray" |
| payload | carica ghjuvevule | upstream "SRT maximum payload size (bytes)" |
| rate control | cuntrollu di frequenza | upstream x264 "Multipass ratecontrol" -> "Cuntrollu di frequenza multipassi" |
| offset | spustime (pl. spustimi) | upstream "Chapter offset in ms" -> "Spustime di i capituli"; "Offsets in order" -> "Spustimi in ordine" |
| top-left corner | scornu superiore manca | upstream snapshot preview / video window position strings |
| separated by | staccati da | upstream "separated by colons" -> "staccati da dui punti" |
| conversion | cunversione | upstream "Qualità di a cunversione", "Cunversioni di crominanza" (the drafts had "cunverzione") |
| crop (n) | runzicatura | upstream "Video cropping" -> "Runzicatura di a video" |
| filtering | filtrazione | upstream "Audio filtering failed" -> "A filtrazione audio hè fiascata" |
| experimental | esperimentale | upstream "Input slave (experimental)" |
| adjust | adattà / adattazione | upstream "Gamma adjust." -> "Adattazione gamma." |
| Phosphor (deinterlace mode) | Fosfuru | upstream "Phosphor" -> "Fosfuru" |
| keychain | portachjavi | upstream (HTTP/TLS certificate help: "in u portachjavi"); INFCOR portachjavi |
| storage | magazinu | VLC for Android (Patriccollu): "Storages" -> "Magazini" |
| stored | arregistratu | Thunderbird: "stored encrypted" -> "arregistrate cifrate" |
| unlock / unlocked | spalancà / spalancatu; noun spalancata | Mozilla Android and Thunderbird (Patriccollu): "Unlock" -> "Spalancà", "screen unlocked" -> "screnu spalancatu"; INFCOR spalancata |
| deprecated | disusatu | INFCOR disusatu: "chì ùn hè più adupratu"; "obsolettu" is not attested |
| odd / even (CSA key) | dispara / para | INFCOR disparu (impair); upstream "The even CSA encryption key" -> "A chjave para" |
| softening / smoothing | addulcimentu | INFCOR addulcimentu (adoucissement) |
| wrapper | incapsulamentu | consistent with this batch's OpenCV wrapper entries (fr "encapsulation") |
| display (n) | affissera | Patriccollu in Notepad++, Audacity, Thunderbird: "Display" -> "Affissera" |
| timestamp | stampiglia | upstream "Use sequential numbers instead of timestamps" |
| raw | grossu | upstream "Raw audio encoder" -> "Cudificatore audio grossu Raw" |
| dump | viutatura | upstream "Dump module" -> "Modulu di viutatura" |
| packetizer | impacchittatore | upstream |
| keystore | magazinu di chjave | upstream "Preferred keystore list" |
| screensaver | risparmiatore di screnu | upstream "Disable screensaver" |
| marquee | testu inquadratu | upstream "Marquee" |

### Words flagged as possibly invented

| Word | In this batch | Finding | Decision |
|---|---|---|---|
| accolta | "TLS support for OS X and iOS", "TLS server support for OS X" | Established word, wrong sense. INFCOR: accolta = accueil; réunion, assemblée. Patriccollu uses it for "Home" / home page. It does not mean "support". | fix -> "Pigliata in carica…" (upstream term) |
| mudellatura | "Shaping delay (ms)" and the long text on shaping | Established word, other sense. INFCOR: mudellatura = modelage (sculpting). For TS bitrate shaping it is a terminological proposal, calqued on Italian "modellamento del traffico" (it.po keeps "shaping"; fr.po paraphrases "Tampon du multiplexeur"). | uncertain (kept as the proposal); alternatives: "regulazione di u flussu binariu", "lisciatura" |
| imbulighju | "Chromecast demux wrapper" | Established word, wrong sense. INFCOR imbulighjata / imbuleghju = mélange, confusion. | fix -> "Dimultiplessore d’incapsulamentu Chromecast" |
| Addolce (addolcimentu) | "Softening value", antiflicker smoothing | Spelling not attested. INFCOR spells it addulcimentu (adoucissement), with the verb addulcì / addulcisce. | fix -> "addulcimentu" |
| sfarfallime | not in this batch (antiflicker labels here do not use it) | Not attested. INFCOR only has sfarfallà = papillonner (to flit about). Upstream uses "antiscintillime" for anti-flicker. | n/a |
| tavuletta | not in this batch | Patriccollu uses it for "Palette" (VLC for Android). | n/a |

Other unattested coinages fixed: "multipari" -> "à parechji pari"; "sfilarinu" -> "chì sfila"; "filtrera" -> "filtrazione";
"almagazinà" -> "arregistrà"; "allucamentu" (storage) -> "magazinu". The agent nouns "Listatore" (lister) and
"Ricercadore" (finder) are kept. INFCOR attests ricercadore (chercheur, a person). Listatore is a regular derivation from listà.

### Music genre names (modules/meta_engine/ID3Genres.h)

- **Origin.** `ID3_ppsz_genres[]` has 148 entries (`ID3_GENRES_COUNT 148`). Indexes 0–79 are the ID3v1
  standard list. Indexes 80–147 are the Winamp extensions, taken from id3.org's compliance notes. Entry index = source line − 33.
- **Function.** In 3.0.x only `modules/demux/mp4/meta.c` uses the table (checked with Sourcegraph). For an MP4 `gnre`
  atom it calls `vlc_meta_SetGenre(p_meta, ID3_ppsz_genres[i_genre - 1])`. That stores the **untranslated English
  string**: there is no `_()` call. The Qt info panel shows the stored string. If the user saves the panel, the
  string is written back to the file (`input_item_SetGenre`). In 3.0.x the translations are therefore extracted but
  never shown, and never used for matching. They become visible only if a future version translates at display
  time. In that case an edited, translated genre could be written into files. This argues for conservative translations.
- **What upstream Corsican does.** Patriccollu translates single common words: Dance -> Ballu,
  Soundtrack -> Musica di filmu, Ambient -> Ambienza, Vocal -> Voce, Classical -> Classicu, Instrumental ->
  Strumentale, Game -> Ghjocu, Noise -> Trostu, Bass -> Bassa, Space -> Spaziu, Comedy -> Cumedia, Latin -> Latinu,
  Celtic -> Celtu, Chorus -> Coru, Speech -> Discussione, Other -> Altru. He keeps style names and every compound style
  label in English: Classic Rock, Alternative Rock, Death Metal, Acid, Industrial, Acoustic, Pranks, Euro-Techno…
  fr, it, es and de translate compounds ("Rock classique", "Rock classico").
- **Policy (applied).** (1) Translate stand-alone common-word labels: Meditativu, Etnicu, Goticu, Elettronicu,
  Cultu, Amerindianu, Musiche di spettaculu, Tribale, Retrò, Avanguardia, Umore, Musica di camera, Sunata, Sinfunia,
  Satira, Folclore, Ballata, Duettu, Assolu di batteria, A cappella, Terrore. (2) Keep style names verbatim (Punk,
  Darkwave, Jungle, Big Band, Easy Listening, Power Ballad, Slow Jam…). (3) Keep compound labels headed by a style
  name in their source form, as upstream does for Classic Rock and Alternative Rock. This reverted 15 drafts:
  Instrumental Pop/Rock, Southern Rock, Christian Rap, National Folk, Gothic/Progressive/Psychedelic/Symphonic/Slow Rock,
  Rhythmic Soul, Polsk Punk, Christian Gangsta Rap, Contemporary Christian, Christian Rock. The index→string mapping is not touched.
- **Negerpunk.** Index 133, source line 166, in the Winamp extension range. fr, it, de, es and pt_BR all keep "Negerpunk"
  verbatim (ca's msgstr differs). It is a historical data label that VLC stores untranslated anyway. Decision: keep
  the source label verbatim (the draft already does). Do not translate, gloss or correct it. Any change belongs upstream,
  in the source table, not in one catalogue.

### Uncertain (left out of the experimental build)

| id | Source | Context | Proposal |
|---|---|---|---|
| e6440397f117 | Shaping delay (ms) | mux/mpeg/ts.c:137, TS muxer option label (bitrate shaping into slices of constant bitrate) | "Ritardu di mudellatura (ms)" (draft); alternatives "Ritardu di regulazione di u flussu binariu (ms)", "Ritardu di lisciatura (ms)" |
| cab4a543cc92 | If enabled, and shaping is specified, the TS muxer will place the boundaries at the end of I pictures… | mux/mpeg/ts.c:144, long help of the same feature | draft kept; follow whatever term is chosen for the label |
