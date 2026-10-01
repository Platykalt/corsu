# Corsican on a phone

Only Apple, Google and Samsung can add a language to their phone systems, so Corsu cannot translate them. Several
apps already include Corsican, though, mostly thanks to Patriccollu di Santa Maria è Sichè, and you can use them
today.

## iPhone

Open Settings, then General, then Language & Region, and tap Add Language. Choose Corsican (Corsu). If you put it
second in the list, the rest of the phone stays in your current language.

Apps that include Corsican, Firefox and Firefox Focus for example, now show it. You can also change the language
of one app only, in Settings, then the app's name, then Language.

To type in Corsican, the free [Keyman](https://apps.apple.com/app/keyman/id933676545) app has a EuroLatin keyboard
with every letter you need. There is no Corsican spell checker on the iPhone yet.

## Android

Gboard, Google's keyboard, has a Corsican layout. In Gboard's settings, open Languages, tap Add keyboard and pick
Corsican.

Firefox, Firefox Focus, Thunderbird, K-9 Mail, VLC and OpenTracks include Corsican. VLC has its own language
setting. The others follow the phone's language list, where Android does not offer Corsican. You can still add it
from a computer with [ADB](https://developer.android.com/tools/adb), after turning on USB debugging:

```sh
adb shell settings put system system_locales co-FR,fr-FR
```

Restart the phone afterwards. Apps that include Corsican use it, and everything else stays in French. Picking
your language again in the phone's settings undoes it.

On Android 13 or later you can set Corsican for a single app instead:

```sh
adb shell cmd locale set-app-locales org.mozilla.firefox --locales co-FR
```

## The system itself

LineageOS, a free version of Android that runs on some Samsung phones, is translated by volunteers on
[Crowdin](https://crowdin.com/project/lineageos). Sardinian, Friulian and Welsh are already there, and Corsican
could be added the same way.

Apple and Google have added regional languages before, after official requests. Apple added Slovenian once a
Slovenian law required it and people had campaigned for it. Google added Galician and Basque to Android after the
Galician government asked.

Phones also take their date formats and language names from Unicode CLDR, where Corsican is incomplete.
Finishing it would help any future request.
