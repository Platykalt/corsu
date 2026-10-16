# Optional texts pack: End Poem and splashes

`end.txt` and `splashes.txt` translate `assets/minecraft/texts/end.txt` and `splashes.txt` from Minecraft Java 26.3.
They are not language files: a resource pack that contains them **replaces these texts whatever language is
selected**, so they ship as an optional pack, separate from the Corsican language pack.

## Provenance and licensing

- **End Poem**: the source text is by Julian Gough, who released it under CC0 1.0 in December 2022
  (<https://theeggandtherock.com/p/i-wrote-a-story-for-a-friend>). The Corsican translation is a derivative of that
  CC0 text.
- **Splashes**: Mojang text. The translation is a derivative work, in the same position as the language file
  `co_fr.json`.

## Format

- `end.txt`: 151 lines, same blank lines, every `§` code (including the obfuscated `§f§k§a§b§3` / `§f§k§a§b§2`
  runs) and every `PLAYERNAME` kept in place. The two voices are kept (`§3`, `§2`). The voices address the player as
  *tù* (intimate, as in a poem), unlike the *voi* of the game's instructions.
- `splashes.txt`: 454 lines in the source order (the game picks some splashes by index on special dates).
  Splashes addressed to the player use *voi*, as in STYLE.md.

## Kept in English (or unchanged) and why

Splash line numbers: 17 25 32 40 45 46 61 62 67 78 79 114 125 127 129 135 136 141 143 148 149 150 153 154 155 161
162 181 183 186 188 225 240 245 254 255 263 274 275 276 277 278 279 280 281 282 284 288 289 290 293 297 303 305 308
309 333 338 340 361 394 399 400 407 408 431 444 451.

- Names, titles, cheats and in-jokes about people: Indev, Minecraft, Peter Griffin, Matt Damon, Flaxkikare,
  Pumpakungen, Technologic, GNU Terry Pratchett, Testificates, Fnord, idspispopd, 90210, OICU812, Zoglin!?
- Code and code-like jokes: `20 GOTO 10!`, `Lennart lennart = new Lennart();`, `if not ok then return end`,
  `.party()!`, `/give @a hugs 64` (a command, kept runnable-looking), `Java 16 + 1 + 4 * 2 = 25!`, `#minecraftfarms`,
  `sqrt(-1) love you!` (the pun needs English "i love you").
- `umop-apisdn!` (upside-down English, ASCII trick that has no Corsican equivalent in plain ASCII).
- Lines already in another language: Herregud!, Une baguette!, Cogito ergo sum!, Jag känner en bot!, and the
  greetings 277–282 (Japanese, Korean, Welsh, Polish, Chinese, Greek).
- Song lyrics and memes quoted as such: Hot tamale (78), Play him off, keyboard cat (79), Consummate V's (150),
  Kick it root down (162), Stop, hammertime (254), Funk soul brother (275), That's Numberwang (308), Aww man (399),
  Chicken Jockey (451, the film meme, not a game name).
- Sounds and interjections: Teetsuuuuoooo / Kaaneeeedaaaa, Wow!, Khaaaaaaaaan!, DRR! DRR! DRR!, Mmmph, mmph!,
  HURNERJSGER?, doot doot, Ahhhhhh!, Nooooooooooooo!, Sniff sniff..., pls rt, ...!, GOTY!, l33t!, Indie!
- Formatting jokes: `§1C§2o§3l§4o§5r§6m§7a§8t§9i§ac` (one colour code per letter; translating would change the codes)
  and `§kFUNKY LOL` (obfuscated anyway).
- 408 *Black lives matter!*: kept as the name of the movement; the lines that follow it (409–415) are translated.
- 263 *Ghoughpteighbteau tchoghs!*: an English-spelling joke ("potato chips") that cannot be carried over.

Wordplay recreated in Corsican rather than copied: 37 *Megliu chè u mele!* (bee's knees → better than honey),
63 *Ceci n'est pas un screnu d'accolta!*, 171 *Avà cù ghj è chj!* (åäö → Corsican trigraphs), 238 *U pane hè pain!*,
243 *madia* (bread chest), 248 *Capu di zucca!*, 258 *Ùn evita mai micca...* (a real double negative),
294 *avucatu* (avocado and lawyer), 325 *Stranu, ma micca straneru!*, 337 *ci pò ragnu!* (broken grammar kept),
346 absolute/relative coordinates, 401 *È u mo piccone!*, 405 *Vaniglia!*, 441 *Sta rena hè suspetta*
(the game's *Rena suspetta*), 427 uses the glossary's *urladore di sculk*. Intentional typos kept as typos:
121 *Ballmeu!*, 122 *siicretu*, 170 *Anlizatu*, 419.

## Uncertain lines (for a Corsican speaker)

End Poem (`end.txt`):
- 9 *Ùn hà micca abbandunatu* for "did not give up" (*ùn hà micca mullatu* would be more colloquial).
- 25 *sculpì* (the infinitive was not found in the local word list; *sculpitu* was).
- 43 *stu mondu chì vo pigliate*: switches to *voi* because "them" (the players) are addressed.
- 53 *U ghjucadore perde a pacenzia* for "is growing restless".
- 71 *cum'è s'è vo fussite cose separate* (you + the universe as plural subject); *movi e dite*, *i to membri*.
- 73 *Jinn* and *Poltergeist* kept as loanwords.
- 93 *racoltu*, *betu*; 97 *ADN* (Corsican Vikipedia usage) for DNA.
- 105, 113 *Zittu* for "Shush" (masculine; the voices have no stated gender).
- 109 *fattu d'energia fatta di spentu è d'accesu* for "offs and ons".
- 143 *chì si gusta* for "tasting itself".
- 123–147 use the literary past *disse*, *si discitò*, *sunniò*, *principiò*.

Splashes (`splashes.txt`):
- 6 *Bellu, senza esagerà!* (moderately attractive), 54 *Dentistu gratisi!*, 60 *Guadagna u so pane!* (bacon idiom).
- 49, 193, 376 *bachi* for software bugs (no reviewed Corsican term found; Italian *baco* model).
- 159 *Avanti tutta!* (Star Trek "Engage!"), 206 *sfoghi* (rash), 207 *"Autologicu" u hè!*, 210 truthiness,
  213 *Hè rivuluziunariu!* (ground-breaking pun lost), 214 the stray apostrophe joke is lost.
- 226, 452 *Terre luntane* for the Far Lands (not a game string in `co_fr.json`).
- 316 *cagnoli* (puppies), 331 *mezaninu*, 383 *gomitu* (elbow), 395 *Sopracciglie folte*, 392 *granfa*
  — none of these was found in the word list.
- 422 *Prestu, à u rammu!* (accent joke on "coppah"), 429 *CRA CRA!*, 430 *Squadra gracchjante!* (Croak team),
  440 *Fattu cù lavamore!* (lava + amore, for "lave").
- 435, 438 *validu/validi* for "valid" in the identity sense.
