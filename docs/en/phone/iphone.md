# Write Corsican on iPhone

[Français](../../fr/telephone/iphone.md) · [Android](android.md)

**No Corsu installation on a computer is needed**: everything happens on the iPhone.

**Download the dictionary: [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp)**
(latest published release, to open in Keyman: see [Install](#install)). The file is attached to Corsu's releases but
works on its own.

Two pieces, both free:

- **Keyman** provides the keyboard. It is an app by SIL, installed from the App Store. Its EuroLatin (SIL) layout has
  every Corsican letter.
- **Corsu** provides the dictionary: as you type, it suggests Corsican words in the banner above the keyboard and
  offers the right spelling of a mistyped word.

The dictionary is neither a sentence translator nor a full grammar checker: it works word by word.

This guide follows Keyman for iPhone and iPad 18.0 (stable 18.0.254 as of 16 October 2026). Button names come from
Keyman's official help and the translation files of that version; another version may change them. There are no
screenshots.

## Available dictionaries

<!-- corsu:phone-variants:en The files really attached to the latest published release (Corsu 0.26.0: the three
     1.1 packages). When a later version is published, list here only the files it carries. -->
| File | Name in Keyman | Version | Content | Download |
| --- | --- | --- | --- | --- |
| `corsu-keyboard.kmp` | Corsu | 1.1 (published with Corsu 0.26.0) | general dictionary: the shared vocabulary, 13,213 words (stray words removed), no regional preference; keeps the capital letters of words | [latest published release](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) ([SHA-256 checksum](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp.sha256)) |
| `corsu-keyboard-cismuntincu.kmp` | Corsu – Cismuntincu (experimental) | 1.1 (published with Corsu 0.26.0) | the same vocabulary, preferring the forms of the Cismonte; experimental, the regional forms cover only part of the words (361 words weighted differently) | [latest published release](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-cismuntincu.kmp) ([SHA-256 checksum](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-cismuntincu.kmp.sha256)) |
| `corsu-keyboard-pumuntincu.kmp` | Corsu – Pumuntincu (experimental) | 1.1 (published with Corsu 0.26.0) | the same vocabulary, preferring the forms of the Pumonte; experimental, same limit | [latest published release](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-pumuntincu.kmp) ([SHA-256 checksum](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-pumuntincu.kmp.sha256)) |

"Version" is the dictionary package's version, which Keyman shows (see step 5); it does not follow Corsu's version
numbers.

All three are for the Corsican language (`co`) and the EuroLatin (SIL) keyboard. One is enough: see
[Choosing a regional dictionary](#choosing-a-regional-dictionary).

## Install

1. **Install Keyman** from the [App Store](https://apps.apple.com/app/keyman/id933676545) (also linked from
   [keyman.com/iphone](https://keyman.com/iphone/)).
2. **Add the EuroLatin (SIL) keyboard for Corsican.** In Keyman, open **Settings** › **Installed Languages** and tap
   **+** at the top right. Search for `Corsican`, pick **EuroLatin (SIL)** and tap the green **Install Keyboard**
   button. If the installer lets you choose languages, keep **Corsican**, then tap **Install** at the top right.
   The Corsu dictionary belongs to the Corsican language (code `co`): it is only used when EuroLatin is used for
   Corsican.
3. **Download the dictionary** in Safari:
   [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp). Keep exactly
   that name (see [Updating](#updating)).
4. **Import it into Keyman.** Safari offers to open the file: tap **Open in "Keyman"**. If the file is already in
   Files, look for **Open in "Keyman"**, or in Keyman use **Settings** › **Install From File** ("Browse for .kmp
   files") and the **Browse** option at the bottom right. Keyman shows the "Corsu" package: keep Corsican, tap
   **Install** at the top right, then **Done** after the welcome page.
5. **Check the dictionary.** **Settings** › **Installed Languages** › **Corsican**: the **Dictionaries** part lists
   the dictionary: "Corsu" for the general dictionary. To see its version, tap it, then the blue **i** icon next to
   its name: the screen shows the **Dictionary version**, to compare with the [Available
   dictionaries](#available-dictionaries) table. Go back without tapping **Uninstall dictionary**.
6. **Set suggestions** on the same screen, under **Language Settings**: turn on **Enable predictions**, then **Enable
   corrections** (the second switch only shows once predictions are on). There is no automatic correction in this
   version: see [Automatic correction](#automatic-correction).
7. **Add Keyman to the iPhone's keyboards.** Open **Settings** › **General** › **Keyboard** › **Keyboards** › **Add
   New Keyboard…**, tap **Keyman** under "Third-party keyboards", then **Keyman - Keyman** and turn on **Allow Full
   Access**.
   *Why Full Access?* Keyman's help says that because of an iOS 16 issue, this setting must stay on for the Keyman
   keyboard to display normally; before iOS 16 it was only needed to change some preferences. It is not something the
   Corsu dictionary needs on its own. iOS shows its usual third-party keyboard warning at that point.
   Afterwards, while typing, the globe key switches between keyboards.
8. **Try it.** In Notes or Messages, choose Keyman with the globe key and type `bonghj`: the banner should suggest
   "bonghjornu". Type `grazzie`: it should suggest "grazie"; tap it to correct.

## Updating

Download the new file and open it in Keyman as in step 4, **under the same name** `corsu-keyboard.kmp`: Keyman takes
the package's identity from the file name. If a suffix was added (`corsu-keyboard(1).kmp`, `corsu-keyboard (1).kmp`),
rename the file in Files before opening it. Your settings are kept. **Then restart Keyman**: until then, the old
dictionary may keep answering. Switch to another keyboard with the globe key and back to Keyman, or close the Keyman
app. Then check the version as in step 5: 1.1 for the packages published with Corsu 0.26.0. A dictionary installed
before Corsu 0.26.0 is named `platykalt.co.corsu` in Keyman, version 1.0: update it.

The full test list with expected results is in French: [Essai en 5 minutes](../../fr/telephone/essai-5-minutes.md).

## Choosing a regional dictionary

<!-- corsu:phone-variants:en Both regional variants are published since Corsu 0.26.0 (1.1 packages). -->
Two experimental dictionaries prefer the forms of the Cismonte or of the Pumonte:
[corsu-keyboard-cismuntincu.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-cismuntincu.kmp)
and
[corsu-keyboard-pumuntincu.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard-pumuntincu.kmp)
(same vocabulary, partial coverage: see [Available dictionaries](#available-dictionaries)). Install them as in step 4,
under their exact file names. On iPhone, according to Keyman 18.0's code (not tried on an iPhone), you choose the
dictionary in **Settings** › **Installed Languages** › **Corsican**, under **Dictionaries**, and the choice is kept
for the language. Then restart Keyman as for an update, then check the name shown (step 5).

To go back to the general dictionary, choose "Corsu" (version 1.1) the same way.

## Capitals and sentence start

- **The capital at the start of a sentence comes from the EuroLatin keyboard, not from the dictionary.** It turns on
  at the start of a field and after `.`, `?` or `!` followed by a space. It does not turn on after a line break
  without punctuation, nor after `."`, `…`, `:`, `;` or `«`; it wrongly turns on after `M. `. There is no setting to
  turn it off: tap Shift to cancel it.
- **Suggestions keep the case you typed** since Corsu 0.26.0 (1.1 packages): in the middle of a sentence, `Ecc`
  suggests "Eccu", and at the start of a sentence suggestions are capitalised. With the old 1.0 package (named
  `platykalt.co.corsu` in Keyman), `Ecc` could become "eccu": if you still have it, [update it](#updating), then
  restart Keyman.
  <!-- corsu:phone-casing Fixed since Corsu 0.26.0 (package 1.1); the 1.0 package lost the capital. -->

## Automatic correction

Keyman 18.0, the stable version, **has no automatic correction**: corrections are offered in the banner and only apply
when you tap them. The Corsu dictionary does not control this setting. Keyman 19, still in beta, adds **Apply
corrections automatically**; it will appear on the Corsican screen once Keyman 19 is the stable version. It stays
optional. In our tests of the 19.0.309 beta's engine (outside the app), a word that is in the dictionary is always
kept as typed, but a missing word may be replaced: a name by a close name ("Bastelicaccia" by "Bastilicaccia" when
only the latter is in the dictionary), or a lowercase word by the name spelled the same ("corti" by "Corti" when
"corti" is missing). The 1.1 dictionary (Corsu 0.26.0) has these forms ("Bastelicaccia", "corti" next to "Corti",
"Vizzani", acronyms such as "ADECEC"); a word still missing, a street name for instance, may still be replaced.

The 1.2 dictionary (next version of Corsu, not published yet) also knows about 5,900 more forms found in its sources:
plurals and feminines ("tradizioni", "fundata", "partuti", which the 19.0.309 engine replaced by "tradizione",
"fundatu", "partiti") and the verb forms of Wiktionary ("manghjatu"); and an elided word whose second part it knows
("L'ADECEC", "d'abitanti") is kept. Verb forms it lacks ("ghjocanu", "vedemu") may still be replaced.

## Returning to a word

Moving the cursor changes nothing in the text. Suggestions follow the part of the word **left of the cursor**, and a
chosen suggestion replaces only that part: the end of the old word stays right of the cursor. In "Dopu ell|a vene",
choosing "ellu" gives "Dopu ellu a vene": that "a" is not an added word but the end of "ella", to be deleted by hand.
Likewise, `ca|sa` then "casa" gives "casa sa".

On iPhone this is also true with the 1.1 dictionary (Corsu 0.26.0): it asks Keyman to delete the end of the word (which
Keyman for Android does), but Keyman for iPhone ignores that request, in 18.0 as in the 19.0 beta (from its code; not
tried on an iPhone). The safe gestures:

- put the cursor **at the end of the word** before picking a suggestion: it then replaces the whole word;
- or select the word, type its first letters (they replace the selection), then pick the suggestion;
- or delete the word and type it again.

Other cases, observed in the engine of Keyman 18.0.254 and 19.0.309 with the iPhone user agent, not on an
iPhone:

- **Punctuation already after the word**, cursor at its end: with the 1.2 dictionary (next version of Corsu, not
  published yet), `Aiacc|.` then "Aiacciu" gives "Aiacciu." (with 1.1, Keyman added a space: "Aiacciu ."). With the
  cursor inside the word, the end of the old word stays, as above, and a space keeps it apart.
- **Punctuation typed after a tapped suggestion**: Keyman adds a space after the word you tap, and Keyman 18 keeps it
  when you then type `.` or `,` ("casa ."). Tap Backspace once (it removes the space only), then type the mark.
  Keyman 19 (beta) removes that space itself.
- **Regional forms**: when the banner offers both forms (zitellu, ziteddu), tap the one you want; to change a word
  already written, put the cursor at its end and tap the other form.
- **Apostrophes**: elided words are suggested whole (`l'is` gives "l'isula"). If the text uses the typographic
  apostrophe `’`, the 1.2 dictionary keeps it ("l’isula").

## If something goes wrong

- **The file won't open.** Open it from Keyman: **Settings** › **Install From File**, then **Browse**. Check that the
  download finished and that the file is named `corsu-keyboard.kmp`.
- **Corsican doesn't appear.** **Installed Languages** should list Corsican with EuroLatin (SIL). If EuroLatin was
  installed for another language only, redo step 2 searching for `Corsican`.
- **No suggestions.** The active keyboard must be EuroLatin (SIL) for Corsican; on the Corsican screen, **Enable
  predictions** must be on and the dictionary listed. Check Full Access too (step 7).
- **Nothing changed after an update.** Restart Keyman (see [Updating](#updating)). If the file had a `(1)` suffix,
  rename it and open it in Keyman again.
- **Capitals disappear.** See [Capitals and sentence start](#capitals-and-sentence-start).
- **Automatic correction doesn't apply.** See [Automatic correction](#automatic-correction).
- **Back to your usual keyboard.** A short press on the globe key moves to the next keyboard; a long press opens
  Keyman's menu, where **Close Keyman** moves to the next keyboard that is not Keyman
  ([Switching between keyboards](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/switching-between-keyboards)). To take Keyman off the list:
  **Settings** › **General** › **Keyboard** › **Keyboards** › **Edit**.

## Where this comes from

The steps follow Keyman 18.0's official help and that version's own files (list below). The behaviour described
(updates, capitals, returning to a word) was observed with the Keyman 18.0.254 engine, which Android and iOS share,
and with the Android app; nothing was tried on an iPhone.

## Keyman help pages used

- [How To - Adding a Keyboard](https://help.keyman.com/products/iphone-and-ipad/18.0/start/searching-for-keyboards)
- [Installing Custom Keyboards/Dictionaries](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/installing-custom-keyboards-dictionaries)
- [How To - Keyboard and Dictionary Installation](https://help.keyman.com/products/iphone-and-ipad/18.0/start/installing-packages)
- [Language Settings](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/language-settings)
- [How To - Installing Keyman as a System Keyboard](https://help.keyman.com/products/iphone-and-ipad/18.0/start/installing-system-keyboard)
- [Switching between keyboards](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/switching-between-keyboards)
- [Using the Settings Screen](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/config/)
- Labels checked against Keyman 18.0's translation files
  ([engine](https://github.com/keymanapp/keyman/blob/stable-18.0/ios/engine/KMEI/KeymanEngine/en.lproj/Localizable.strings),
  [app](https://github.com/keymanapp/keyman/blob/stable-18.0/ios/keyman/Keyman/Keyman/en.lproj/Localizable.strings)).

## Apps in Corsican

iOS does not offer Corsican as a system language; only Apple could add it. Apps that include Corsican can still use
it.

1. Open Settings, then General, then Language & Region, and tap Add Language.
2. Choose Corsican (Corsu). If you put it second in the list, the rest of the phone keeps your current language.
3. Apps that include Corsican, Firefox and Firefox Focus for example, now show it. You can also change the language
   of one app in Settings, then the app's name, then Language.

Apple added Slovenian in 2024, a few months after a Slovenian law required it and a public campaign. No such request
has been made for Corsican so far.
