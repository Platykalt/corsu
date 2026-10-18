# Write Corsican on iPhone

[Français](../../fr/telephone/iphone.md) · [Android](android.md)

Two pieces, both free:

- **Keyman** provides the keyboard. It is an app by SIL, installed from the App Store. Its EuroLatin (SIL) layout has
  every Corsican letter.
- **Corsu** provides the dictionary: as you type, it suggests Corsican words in the banner above the keyboard and
  offers the right spelling of a mistyped word.

The Corsu desktop app is not needed. The dictionary is neither a sentence translator nor a full grammar checker: it
works word by word.

This guide follows Keyman for iPhone and iPad 18.0 (stable 18.0.254 as of 16 October 2026). Button names come from
Keyman's official help and the translation files of that version; another version may change them. There are no
screenshots.

## Available dictionaries

| File | Content | Download |
| --- | --- | --- |
| `corsu-keyboard.kmp` | general dictionary, about 17,000 common Corsican words | [latest published release](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) |

<!-- The files really attached to the latest published release. Add a row only when the published release has the
     file. -->
Other variants are being prepared; they will appear in this table once published.

## Install

1. **Install Keyman** from the [App Store](https://apps.apple.com/app/keyman/id933676545) (also linked from
   [keyman.com/iphone](https://keyman.com/iphone/)).
2. **Add the EuroLatin (SIL) keyboard for Corsican.** In Keyman, open **Settings** › **Installed Languages** and tap
   **+** at the top right. Search for `Corsican`, pick **EuroLatin (SIL)** and tap the green **Install Keyboard**
   button. If the installer lets you choose languages, keep **Corsican**, then tap **Install** at the top right.
   The Corsu dictionary belongs to the Corsican language (code `co`): it is only used when EuroLatin is used for
   Corsican.
3. **Download the dictionary** in Safari:
   [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp).
4. **Import it into Keyman.** Safari offers to open the file: tap **Open in "Keyman"**. If the file is already in
   Files, look for **Open in "Keyman"**, or in Keyman use **Settings** › **Install From File** ("Browse for .kmp
   files") and the **Browse** option at the bottom right. Keyman shows the "Corsu" package: keep Corsican, tap
   **Install** at the top right, then **Done** after the welcome page.
5. **Check the dictionary.** **Settings** › **Installed Languages** › **Corsican**: the **Dictionaries** part should
   list Corsu (it may show its identifier, `platykalt.co.corsu`).
6. **Set suggestions** on the same screen, under **Language Settings**: turn on **Enable predictions**, then **Enable
   corrections** (the second switch only shows once predictions are on). Keyman 18.0 has no auto-correction setting:
   corrections are offered in the banner and apply when you tap them.
7. **Add Keyman to the iPhone's keyboards.** Open **Settings** › **General** › **Keyboard** › **Keyboards** › **Add
   New Keyboard…**, tap **Keyman** under "Third-party keyboards", then **Keyman - Keyman** and turn on **Allow Full
   Access**.
   *Why Full Access?* Keyman's help says that because of an iOS 16 issue, this setting must stay on for the Keyman
   keyboard to display normally; before iOS 16 it was only needed to change some preferences. It is not something the
   Corsu dictionary needs on its own. iOS shows its usual third-party keyboard warning at that point.
   Afterwards, while typing, the globe key switches between keyboards.
8. **Try it.** In Notes or Messages, choose Keyman with the globe key and type `bonghj`: the banner should suggest
   "bonghjornu". Type `grazzie`: it should suggest "grazie"; tap it to correct.

## If something goes wrong

- **The file won't open.** Open it from Keyman: **Settings** › **Install From File**, then **Browse**. Check that the
  download finished and that the file is named `corsu-keyboard.kmp`.
- **Corsican doesn't appear.** **Installed Languages** should list Corsican with EuroLatin (SIL). If EuroLatin was
  installed for another language only, redo step 2 searching for `Corsican`.
- **No suggestions.** The active keyboard must be EuroLatin (SIL) for Corsican; on the Corsican screen, **Enable
  predictions** must be on and the dictionary listed. Check Full Access too (step 7).
- **Capitals disappear.** With the published dictionary, picking a suggestion can replace a word started with a
  capital by its lower-case form. The problem is known; a fix is prepared but not published yet. Meanwhile, finish
  the word on the keyboard or put the capital back.
  <!-- Provisional wording: the release lead adjusts it when the fix is published. -->
- **Auto-correction doesn't apply.** That is how Keyman 18.0 works: corrections are offered in the banner, to tap.
- **Back to your usual keyboard.** Tap the globe key until your usual keyboard shows. To take Keyman off the list:
  **Settings** › **General** › **Keyboard** › **Keyboards** › **Edit**.

## Keyman help pages used

- [How To - Adding a Keyboard](https://help.keyman.com/products/iphone-and-ipad/18.0/start/searching-for-keyboards)
- [Installing Custom Keyboards/Dictionaries](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/installing-custom-keyboards-dictionaries)
- [How To - Keyboard and Dictionary Installation](https://help.keyman.com/products/iphone-and-ipad/18.0/start/installing-packages)
- [Language Settings](https://help.keyman.com/products/iphone-and-ipad/18.0/basic/language-settings)
- [How To - Installing Keyman as a System Keyboard](https://help.keyman.com/products/iphone-and-ipad/18.0/start/installing-system-keyboard)
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
