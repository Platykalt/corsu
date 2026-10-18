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

<!-- corsu:phone-variants:en The files really attached to the latest published release. When the next version is
     published, move here the rows of the "In the next version" table that it carries. -->
| File | Name in Keyman | Version | Content | Download |
| --- | --- | --- | --- | --- |
| `corsu-keyboard.kmp` | `platykalt.co.corsu` | 1.0 (published with Corsu 0.25.1) | general dictionary, 19,805 words taken from Corsu's lexicon; loses the capital letters of words and still holds a few stray words (English words, product names, fragments), defects fixed in the next version | [latest published release](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) ([SHA-256 checksum](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp.sha256)) |

"Version" is the dictionary package's version, which Keyman shows (see step 5); it does not follow Corsu's version
numbers.

### In the next version (not published yet)

| File | Name in Keyman | Version | Content |
| --- | --- | --- | --- |
| `corsu-keyboard.kmp` | Corsu | 1.1 | the shared vocabulary, about 13,000 words (stray words removed), no regional preference; keeps the capital letters of words |
| `corsu-keyboard-cismuntincu.kmp` | Corsu – Cismuntincu (experimental) | 1.1 | the same vocabulary, preferring the forms of the Cismonte; experimental, the regional forms cover only part of the words (361 words weighted differently) |
| `corsu-keyboard-pumuntincu.kmp` | Corsu – Pumuntincu (experimental) | 1.1 | the same vocabulary, preferring the forms of the Pumonte; experimental, same limit |

All three are for the Corsican language (`co`) and the EuroLatin (SIL) keyboard. One is enough: see
[Choosing a regional dictionary](#choosing-a-regional-dictionary). To try them before they are published:
[Trying the next version's dictionary (candidate)](#trying-the-next-versions-dictionary-candidate).

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
   the dictionary, `platykalt.co.corsu` for the package published today ("Corsu" for the next version's). To see its
   version, tap it, then the blue **i** icon next to its name: the screen shows the **Dictionary version**, to compare
   with the [Available dictionaries](#available-dictionaries) table. Go back without tapping **Uninstall
   dictionary**.
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
app. Then check the version as in step 5.

## Trying the next version's dictionary (candidate)

The next Corsu version's dictionary (package **version 1.1**, named **"Corsu"** in Keyman) is not published yet. You
can try it beforehand: the project's build pipeline (GitHub Actions) produces it on every change. It is not a
published release: it may still change, and nothing was tried on an iPhone (the steps follow Keyman
18.0's help).

1. **Sign in to GitHub** in Safari (a free account is enough): GitHub only hands these files to signed-in
   accounts (signed out, the link shows a "404" page).
2. **Download the archive** [keyboard-packages](https://github.com/Platykalt/corsu/actions/runs/39161059937/artifacts/12149352996) (commit `146d2cf` on `next-0.26`) (opening the link starts the download). It arrives in **Files** › **Downloads** as `keyboard-packages.zip`.
   GitHub deletes it after 90 days (on 16 January 2027); a newer link will then be given here.
3. **Extract it** in the **Files** app, tap `keyboard-packages.zip`; iOS creates a `keyboard-packages` folder next
   to it. It holds `corsu-keyboard.kmp`, `corsu-keyboard-cismuntincu.kmp`,
   `corsu-keyboard-pumuntincu.kmp` and their `.sha256` checksums. For the general dictionary, take
   **`corsu-keyboard.kmp`**, without renaming it.
4. **First remove the installed dictionary**: **Settings** › **Installed Languages** › **Corsican** ›
   **Dictionaries** › the dictionary › **i** icon › **Uninstall dictionary**. Restart Keyman (see [Updating](#updating)).
5. **Install** `corsu-keyboard.kmp` from the folder: in Keyman, **Settings** › **Install From File** ›
   **Browse**, then pick it in the `keyboard-packages` folder. The package screen should show "Corsu" and version 1.1;
   tap **Install**, then **Done**.
6. **Restart Keyman, then check** as in step 5: **Dictionaries** lists "Corsu" (not
   `platykalt.co.corsu`), and the **Dictionary version** is 1.1. In the middle of a
   sentence, type `Ecc`: the banner should suggest "Eccu" with its capital (the published dictionary suggests "eccu").

**Going back to the published dictionary**: uninstall "Corsu" the same way (step 4 above), restart Keyman, then
install `corsu-keyboard.kmp` downloaded from the [published link](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp)
(steps 3 and 4 of [Install](#install)). After another restart, **Dictionaries** lists `platykalt.co.corsu` again, version 1.0.

The full test list with expected results is in French: [Essai en 5 minutes](../../fr/telephone/essai-5-minutes.md).

## Choosing a regional dictionary

<!-- corsu:phone-variants:en The regional variants come with the next version. -->
With the next version, two experimental dictionaries will prefer the forms of the Cismonte or of the Pumonte. On
iPhone, according to Keyman 18.0's code (not tried on an iPhone), you choose the dictionary in **Settings** ›
**Installed Languages** › **Corsican**, under **Dictionaries**, and the choice is kept for the language. Then restart
Keyman as for an update, then check the name shown (step 5).

Before they are published, both variants are in the same archive as the candidate dictionary: see
[Trying the next version's dictionary](#trying-the-next-versions-dictionary-candidate).

## Capitals and sentence start

- **The capital at the start of a sentence comes from the EuroLatin keyboard, not from the dictionary.** It turns on
  at the start of a field and after `.`, `?` or `!` followed by a space. It does not turn on after a line break
  without punctuation, nor after `."`; it wrongly turns on after `M. `. There is no setting to turn it off: tap Shift
  to cancel it.
- **Suggestions lose the capital** with the published release's dictionary: `Ecc` can become "eccu". This is fixed
  in the next version's packages, which keep the typed case ("Eccu") and capitalise suggestions at the start of a
  sentence. Meanwhile, finish the word on the keyboard or put the capital back.
  <!-- corsu:phone-casing At release time: say it is fixed in the published release. -->

## Automatic correction

Keyman 18.0, the stable version, **has no automatic correction**: corrections are offered in the banner and only
apply when you tap them. The Corsu dictionary does not control this setting. Keyman 19, still in beta, adds **Apply
corrections automatically**; it will appear on the Corsican screen once Keyman 19 is the stable version. It stays
optional: in our tests with the beta, automatic correction sometimes wrongly replaced names that are not in the
dictionary.

## Returning to a word

Moving the cursor changes nothing in the text. Suggestions follow the part of the word **left of the cursor**, and a
chosen suggestion replaces only that part: with the cursor inside `ell|a`, choosing "ellu" gives "ellu a". This is a
Keyman limit: it deletes nothing right of the cursor. So put the cursor **at the end of the word** (or delete the word
and type it again) before picking a suggestion.

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
