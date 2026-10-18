# Write Corsican on Android

[Français](../../fr/telephone/android.md) · [iPhone](iphone.md)

**No Corsu installation on a computer is needed**: everything happens on the phone.

**Download the dictionary: [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp)**
(latest published release, to open in Keyman: see [Install](#install)). The file is attached to Corsu's releases but
works on its own.

Two pieces, both free:

- **Keyman** provides the keyboard. It is an app by SIL, installed from the Play Store. Its EuroLatin (SIL) layout
  has every Corsican letter.
- **Corsu** provides the dictionary: as you type, it suggests Corsican words in the banner above the keyboard and
  offers the right spelling of a mistyped word.

The dictionary is neither a sentence translator nor a full grammar checker: it works word by word.

This guide follows Keyman for Android 18.0 (stable 18.0.254 as of 16 October 2026). Button names come from Keyman's
official help and the translation files of that version; another version may change them. There are no screenshots.

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

1. **Install Keyman** from the [Play Store](https://play.google.com/store/apps/details?id=com.tavultesoft.kmapro)
   (or from [keyman.com/android](https://keyman.com/android/)).
2. **Add the EuroLatin (SIL) keyboard for Corsican.** In Keyman, open the menu, then **Settings** › **Installed
   languages**, and tap **+** at the bottom right. Search for `Corsican` (`l:id:co` works too), pick **EuroLatin
   (SIL)** and tap the green install button. If the installer asks for languages, keep **Corsican**. Keyman then looks
   for a Corsican dictionary on its own site and may answer "No dictionary to download": that is expected, Corsu's
   dictionary is installed in the next step.
   The Corsu dictionary belongs to the Corsican language (code `co`): it is only used when EuroLatin is used for
   Corsican.
3. **Download the dictionary** on the phone:
   [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp). The file
   usually lands in the Downloads folder. Keep exactly that name: if the browser renamed it `corsu-keyboard(1).kmp` or
   `corsu-keyboard (1).kmp`, rename it (see [Updating](#updating)).
4. **Import it into Keyman.** Menu › **Settings** › **Install Keyboard or Dictionary** › **Install from local
   file**, then pick `corsu-keyboard.kmp` in Downloads. If Android asks for access to files, allow it (Keyman asks
   only once). Keyman shows the "Corsu" package and its version: tap **Install**, then **OK** after the welcome page.
5. **Check the dictionary.** **Settings** › **Installed languages** › **Corsican**: at the bottom of the screen,
   **Dictionary** names the active dictionary, `platykalt.co.corsu` for the package published today ("Corsu" for the
   next version's). To see its version, tap **Dictionary**, then the checked dictionary: the "Dictionary: …" screen
   shows the **Dictionary version** (Keyman shows the package's version there), to compare with the
   [Available dictionaries](#available-dictionaries) table. Go back without tapping **Uninstall dictionary**.
6. **Set suggestions** on the same screen. Keyman 18.0 offers three choices: *Disable suggestions*, *Predictions
   only* (words suggested, no corrections) and *Predictions with corrections* (words suggested and typos corrected).
   Choose **Predictions with corrections**. There is no automatic correction in this version: see
   [Automatic correction](#automatic-correction).
7. **Make Keyman the phone's keyboard.** Menu › **Settings** › **Enable Keyman as system-wide keyboard** (also under
   **Get Started**). Android's keyboard screen opens: turn **Keyman** on, then answer **OK** to the two confirmation
   messages. Android warns there that a keyboard can read what you type; it shows this for any added keyboard.
   Afterwards, when a keyboard is on screen, the keyboard icon at the bottom right lets you pick Keyman.
8. **Try it.** In a notes or messages app, choose Keyman and type `bonghj`: the banner should suggest "bonghjornu". Type
   `grazzie`: it should suggest "grazie"; tap it to correct.

## Updating

Download the new file and install it as in step 4, **under the same name** `corsu-keyboard.kmp`. Keyman takes the
package's identity from the file name: if the browser added a suffix (`corsu-keyboard(1).kmp`,
`corsu-keyboard (1).kmp`), rename the file before installing it, or delete the old download first. Your settings are
kept. **Then restart Keyman**: until then, the old dictionary keeps answering. To restart it, switch to another
keyboard and back to Keyman, or force-stop the Keyman app in Android's settings. Then check the version as in step 5.

## Trying the next version's dictionary (candidate)

The next Corsu version's dictionary (package **version 1.1**, named **"Corsu"** in Keyman) is not published yet. You
can try it beforehand: the project's build pipeline (GitHub Actions) produces it on every change. It is not a
published release: it may still change, and it was only tried on an Android 14 emulator, not on a
real phone.

1. **Sign in to GitHub** in the phone's browser (a free account is enough): GitHub only hands these files to signed-in
   accounts (signed out, the link shows a "404" page).
2. **Download the archive** [keyboard-packages](https://github.com/Platykalt/corsu/actions/runs/39140018508/artifacts/12141617671) (opening the link starts the download). It arrives as `keyboard-packages.zip`.
   GitHub deletes it after 90 days (on 16 January 2027); a newer link will then be given here.
3. **Extract it** with the phone's files app (Files by Google: tap the `.zip` file, then **Extract**). The folder you get holds `corsu-keyboard.kmp`, `corsu-keyboard-cismuntincu.kmp`,
   `corsu-keyboard-pumuntincu.kmp` and their `.sha256` checksums. For the general dictionary, take
   **`corsu-keyboard.kmp`**, without renaming it.
4. **First remove the installed dictionary**: **Settings** › **Installed languages** › **Corsican** ›
   **Dictionary** › the checked dictionary › **Uninstall dictionary** › **Delete**. Restart Keyman (see [Updating](#updating)).
5. **Install** `corsu-keyboard.kmp` from the extracted folder as in step 4 (**Install from local
   file**). The package screen should show "Corsu" and version 1.1.
6. **Restart Keyman, then check** as in step 5: **Dictionary** names "Corsu" (not
   `platykalt.co.corsu`), and the **Dictionary version** is 1.1. In the middle of a
   sentence, type `Ecc`: the banner should suggest "Eccu" with its capital (the published dictionary suggests "eccu").

**Going back to the published dictionary**: uninstall "Corsu" the same way (step 4 above), restart Keyman, then
install `corsu-keyboard.kmp` downloaded from the [published link](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp)
(steps 3 and 4 of [Install](#install)). After another restart, **Dictionary** names `platykalt.co.corsu` again, version 1.0.

The full test list with expected results is in French: [Essai en 5 minutes](../../fr/telephone/essai-5-minutes.md).

## Choosing a regional dictionary

<!-- corsu:phone-variants:en The regional variants come with the next version. -->
With the next version, two experimental dictionaries will prefer the forms of the Cismonte or of the Pumonte. On
Android, **only one dictionary is active per language: the first one installed**. Installing a second Corsu package
adds it to the list, but the old one stays active. To switch:

1. **Settings** › **Installed languages** › **Corsican** › **Dictionary** › the active dictionary › **Uninstall
   dictionary**;
2. install the package you want (step 4) if it is not installed yet;
3. restart Keyman (see [Updating](#updating)), then check the name shown (step 5).

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

Keyman 18.0, the stable version, **has no automatic correction**: corrections are offered in the banner and only apply
when you tap them. The Corsu dictionary does not control this setting. Keyman 19, still in beta, adds the choice
*Predictions with auto-corrections*; it will appear on the Corsican screen once Keyman 19 is the stable version. It
stays optional. In our tests of the 19.0.309 beta's engine (outside the app), a word that is in the dictionary is
always kept as typed, but a missing word may be replaced: a name by a close name ("Bastelicaccia" by "Bastilicaccia"
when only the latter is in the dictionary), or a lowercase word by the name spelled the same ("corti" by "Corti" when
"corti" is missing).

## Returning to a word

Moving the cursor changes nothing in the text. Suggestions follow the part of the word **left of the cursor**.

- **Cursor at the end of the word**: the chosen suggestion replaces the whole word. This is the safe gesture, whatever
  the dictionary.
- **Cursor inside the word**, with the published dictionary (1.0): the suggestion replaces only the part left of the
  cursor, and the end of the old word stays on its right. In "Dopu ell|a vene", choosing "ellu" gives
  "Dopu ellu a vene": that "a" is not an added word but the end of "ella", to be deleted by hand. Likewise, `ca|sa`
  then "casa" gives "casa sa". Keyman does not delete anything right of the cursor by itself.
- **Cursor inside the word**, with the next version's dictionary (1.1): the suggestion replaces the whole word,
  "Dopu ellu vene". The dictionary asks Keyman to delete the end of the word, which Keyman for Android does. Observed
  in the engine of Keyman 18.0.254 and 19.0.309 (beta) and in the Keyman 18.0.254 app on an Android 14 emulator, not
  on a phone.
  Two Keyman limits remain: if the word is followed by punctuation, a space is added before it (`Aiacc|iu.` then
  "Aiacciu" gives "Aiacciu ."); and the undo Keyman offers right after (backspace, then the word in quotes) does not
  bring back the end of the old word.
- **After adding or deleting a letter inside the word**, it is the same case: suggestions follow the part left of the
  cursor, and the rule above applies.
- **Selected word**: type the first letters of the word you want (they replace the selection), then pick the
  suggestion. Tapping a suggestion without typing replaces the selection with a sentence-start suggestion, capitalised
  ("Eccu a Di di Petru."): behaviour of Keyman's engine, observed in its engine only.

## If something goes wrong

- **The file won't open.** Go through Keyman (step 4) rather than the file itself. Check that the download finished
  and that the file is named `corsu-keyboard.kmp`; otherwise download it again. If access to files was refused, see
  [Grant Storage Permission](https://help.keyman.com/products/android/18.0/troubleshooting/grant-storage-permission).
- **Corsican doesn't appear.** **Installed languages** should list Corsican with EuroLatin (SIL). If EuroLatin was
  installed for another language only, redo step 2 searching for `Corsican`.
- **No suggestions.** The active keyboard must be EuroLatin (SIL) for Corsican (not for French or English); on the
  Corsican screen, the choice must not be *Disable suggestions* and a Corsu dictionary must be named.
- **Nothing changed after an update or a dictionary change.** Restart Keyman (see [Updating](#updating)). If the file
  had a `(1)` suffix, rename it and install it again.
- **Capitals disappear.** See [Capitals and sentence start](#capitals-and-sentence-start).
- **Automatic correction doesn't apply.** See [Automatic correction](#automatic-correction).
- **Back to your usual keyboard.** Tap the keyboard icon at the bottom right of the screen and pick your usual
  keyboard. The globe key on the Keyman keyboard does it too: with a single Keyman keyboard installed, a short press
  goes back to the previous system keyboard; a long press opens the language list, with **Other Input Methods** at the
  bottom ([Switching Between Keyboards](https://help.keyman.com/products/android/18.0/basic/switching-between-keyboards)).
  To remove the dictionary:
  [Removing Dictionaries](https://help.keyman.com/products/android/18.0/basic/uninstalling-dictionaries).

## Where this comes from

The steps follow Keyman 18.0's official help and that version's own files (list below). The behaviour described
(active dictionary, updates, capitals, returning to a word) was observed with the Keyman 18.0.254 engine and the
Keyman 18.0.254 app on an Android 14 emulator, not on a real phone.

## Keyman help pages used

- [Installing Custom Keyboards/Dictionaries](https://help.keyman.com/products/android/18.0/basic/installing-custom-packages)
- [How To - Download and Install a Keyman Keyboard](https://help.keyman.com/products/android/18.0/start/installing-keyboards)
- [Adding Dictionaries](https://help.keyman.com/products/android/18.0/basic/installing-dictionaries)
- [Using the Settings Screen](https://help.keyman.com/products/android/18.0/basic/config/)
- [Enabling Keyman as a System-Wide Keyboard](https://help.keyman.com/products/android/18.0/start/enabling-system-keyboard)
- [Install Keyboard or Dictionary](https://help.keyman.com/products/android/18.0/basic/config/install-keyboard-or-dictionary)
- [Removing Dictionaries](https://help.keyman.com/products/android/18.0/basic/uninstalling-dictionaries)
- [Switching Between Keyboards](https://help.keyman.com/products/android/18.0/basic/switching-between-keyboards)
- [Using the Banner on the Keyboard](https://help.keyman.com/products/android/18.0/basic/using-the-banner)
- The **Dictionary version** shown is the package's: see Keyman 18.0's code
  ([dictionary screen](https://github.com/keymanapp/keyman/blob/stable-18.0/android/KMEA/app/src/main/java/com/keyman/engine/ModelInfoActivity.java),
  [package reading](https://github.com/keymanapp/keyman/blob/stable-18.0/android/KMEA/app/src/main/java/com/keyman/engine/packages/LexicalModelPackageProcessor.java)).
- The three suggestion choices come from Keyman 18.0's own files
  ([texts](https://github.com/keymanapp/keyman/tree/stable-18.0/android/KMEA/app/src/main/res),
  [language screen](https://github.com/keymanapp/keyman/blob/stable-18.0/android/KMEA/app/src/main/res/layout/language_settings_list_layout.xml),
  where auto-correction is switched off for 18.0).

## Other keyboards

Gboard, Google's keyboard, also has a Corsican layout with word suggestions: in Gboard's settings, open Languages, tap
Add keyboard and choose Corsican. The Corsu dictionary does not install there; it only works in Keyman.

## Apps in Corsican

Firefox, Firefox Focus, Thunderbird, K-9 Mail, VLC and OpenTracks include Corsican. VLC has its own language setting.
The others follow the phone's language list, which does not offer Corsican. You can add it from a computer with
[ADB](https://developer.android.com/tools/adb), after turning on USB debugging on the phone:

```sh
adb shell settings put system system_locales co-FR,fr-FR
```

Restart the phone. Apps that include Corsican use it, and everything else stays in French. Choosing your language
again in the phone's settings undoes it.

On Android 13 or later you can switch a single app instead:

```sh
adb shell cmd locale set-app-locales org.mozilla.firefox --locales co-FR
```

## The system itself

Android and Samsung's One UI do not offer Corsican, and only Google or Samsung could add it. LineageOS, a free version
of Android that runs on some Samsung phones, is translated by volunteers on
[Crowdin](https://crowdin.com/project/lineageos). Sardinian, Friulian and Welsh are already there; Corsican could be
added the same way. Google added Galician and Basque to Android after the Galician government asked.
