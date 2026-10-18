# Write Corsican on Android

[Français](../../fr/telephone/android.md) · [iPhone](iphone.md)

Two pieces, both free:

- **Keyman** provides the keyboard. It is an app by SIL, installed from the Play Store. Its EuroLatin (SIL) layout
  has every Corsican letter.
- **Corsu** provides the dictionary: as you type, it suggests Corsican words in the banner above the keyboard and
  offers the right spelling of a mistyped word.

The Corsu desktop app is not needed. The dictionary is neither a sentence translator nor a full grammar checker: it
works word by word.

This guide follows Keyman for Android 18.0 (stable 18.0.254 as of 16 October 2026). Button names come from Keyman's
official help and the translation files of that version; another version may change them. There are no screenshots.

## Available dictionaries

| File | Content | Download |
| --- | --- | --- |
| `corsu-keyboard.kmp` | general dictionary, about 17,000 common Corsican words | [latest published release](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) |

<!-- The files really attached to the latest published release. Add a row only when the published release has the
     file. -->
Other variants are being prepared; they will appear in this table once published.

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
   usually lands in the Downloads folder.
4. **Import it into Keyman.** Menu › **Settings** › **Install Keyboard or Dictionary** › **Install from local
   file**, then pick `corsu-keyboard.kmp` in Downloads. If Android asks for access to files, allow it (Keyman asks
   only once). Keyman shows the "Corsu" package and its version: tap **Install**, then **OK** after the welcome page.
5. **Choose the dictionary.** **Settings** › **Installed languages** › **Corsican**: at the bottom of the screen,
   **Dictionary** should name Corsu (it may show its identifier, `platykalt.co.corsu`). If not, tap it and choose it
   (the installed dictionary has a check mark).
6. **Set suggestions** on the same screen. Keyman 18.0 offers three choices: *Disable suggestions*, *Predictions
   only* (words suggested, no corrections) and *Predictions with corrections* (words suggested and typos corrected).
   Choose **Predictions with corrections**. Keyman 18.0 for Android has no auto-correction: a correction shows in the
   banner and applies when you tap it.
7. **Make Keyman the phone's keyboard.** Menu › **Settings** › **Enable Keyman as system-wide keyboard** (also under
   **Get Started**). Android's keyboard screen opens: turn **Keyman** on, then answer **OK** to the two confirmation
   messages. Android warns there that a keyboard can read what you type; it shows this for any added keyboard.
   Afterwards, when a keyboard is on screen, the keyboard icon at the bottom right lets you pick Keyman.
8. **Try it.** In a notes or messages app, choose Keyman and type `bonghj`: the banner should suggest "bonghjornu". Type
   `grazzie`: it should suggest "grazie"; tap it to correct.

## If something goes wrong

- **The file won't open.** Go through Keyman (step 4) rather than the file itself. Check that the download finished
  and that the file is named `corsu-keyboard.kmp`; otherwise download it again. If access to files was refused, see
  [Grant Storage Permission](https://help.keyman.com/products/android/18.0/troubleshooting/grant-storage-permission).
- **Corsican doesn't appear.** **Installed languages** should list Corsican with EuroLatin (SIL). If EuroLatin was
  installed for another language only, redo step 2 searching for `Corsican`.
- **No suggestions.** The active keyboard must be EuroLatin (SIL) for Corsican (not for French or English); on the
  Corsican screen, the choice must not be *Disable suggestions* and the dictionary must be Corsu.
- **Capitals disappear.** With the published dictionary, picking a suggestion can replace a word started with a
  capital by its lower-case form. The problem is known; a fix is prepared but not published yet. Meanwhile, finish
  the word on the keyboard or put the capital back.
  <!-- Provisional wording: the release lead adjusts it when the fix is published. -->
- **Auto-correction doesn't apply.** That is how Keyman 18.0 for Android works: corrections are offered in the
  banner, to tap.
- **Back to your usual keyboard.** Tap the keyboard icon at the bottom right of the screen (or the globe key on the
  Keyman keyboard) and pick your usual keyboard. To remove the dictionary:
  [Removing Dictionaries](https://help.keyman.com/products/android/18.0/basic/uninstalling-dictionaries).

## Keyman help pages used

- [Installing Custom Keyboards/Dictionaries](https://help.keyman.com/products/android/18.0/basic/installing-custom-packages)
- [How To - Download and Install a Keyman Keyboard](https://help.keyman.com/products/android/18.0/start/installing-keyboards)
- [Adding Dictionaries](https://help.keyman.com/products/android/18.0/basic/installing-dictionaries)
- [Using the Settings Screen](https://help.keyman.com/products/android/18.0/basic/config/)
- [Enabling Keyman as a System-Wide Keyboard](https://help.keyman.com/products/android/18.0/start/enabling-system-keyboard)
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
