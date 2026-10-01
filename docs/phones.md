# Corsican on phones

Neither iOS nor Android can be translated by an outside project: only Apple, Google and Samsung can add a
system language. What you can do today is use the apps that already ship a Corsican translation, most of them
translated by Patriccollu di Santa Maria è Sichè.

## iPhone and iPad

1. Open *Settings › General › Language & Region* and tap *Add Language…*.
2. Choose *Corsican* (*Corsu*). Keep your current language first in the list if you want the rest of the phone
   unchanged.
3. Apps that include Corsican, such as Firefox and Firefox Focus, now display it. You can also pick the language
   of a single app in *Settings › (app name) › Language*.

For typing, the free [Keyman](https://apps.apple.com/app/keyman/id933676545) app has a EuroLatin keyboard that
covers all Corsican letters. There is no Corsican spell checker or word prediction on iOS yet.

## Android and Samsung Galaxy

- **Keyboard:** Gboard has a Corsican keyboard. Open Gboard's settings, then *Languages › Add keyboard ›
  Corsican*.
- **Apps in Corsican:** Firefox, Firefox Focus, Thunderbird (and K-9 Mail), VLC, OpenTracks. VLC has its own
  language setting; the others follow the phone's language list.

Android does not list Corsican in its language settings. You can still add it with a computer and
[ADB](https://developer.android.com/tools/adb) (USB debugging enabled):

```sh
adb shell settings put system system_locales co-FR,fr-FR
```

Restart the phone. Apps that ship Corsican use it, and everything else stays in French. To undo it, choose your
language again in the phone's settings.

On Android 13 and later you can also set Corsican for one app only:

```sh
adb shell cmd locale set-app-locales org.mozilla.firefox --locales co-FR
```

## A Corsican system language

The system menus themselves (One UI, Android, iOS) need the manufacturer:

- **LineageOS**, a free Android system that runs on some Samsung phones, translates through volunteers on
  [Crowdin](https://crowdin.com/project/lineageos). Sardinian, Friulian and Welsh are already there; Corsican could
  be added the same way.
- **Apple and Google** have added regional languages after official requests. Slovenian came to iOS after a
  change in Slovenian law and a public campaign; Galician and Basque came to Android after a request from the
  Galician government.
- Android and iOS take their date formats and language names from Unicode CLDR, where Corsican is still
  incomplete. Completing it is a useful first step.
