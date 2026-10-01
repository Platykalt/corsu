# Corsican on an Android phone

[Français](../../fr/telephone/android.md)

Android and Samsung's One UI do not offer Corsican, and only Google or Samsung could add it. Several apps already
come in Corsican, most of them translated by Patriccollu di Santa Maria è Sichè, and you can use them today.

## Keyboard

Gboard, Google's keyboard, has a Corsican layout with word suggestions. In Gboard's settings, open Languages, tap
Add keyboard and choose Corsican.

Corsu also has its own word prediction and spelling correction, built from its 17,000 most used Corsican words. It
runs in the free [Keyman](https://play.google.com/store/apps/details?id=com.tavultesoft.kmapro) keyboard:

1. Install Keyman from the Play Store and add the EuroLatin (SIL) keyboard, which has every Corsican letter.
2. On the phone, download [corsu-keyboard.kmp](https://github.com/Platykalt/corsu/releases/latest/download/corsu-keyboard.kmp) and open it: Keyman installs it.
3. Keyman now suggests and corrects Corsican words as you type.

There is no Corsican grammar checker yet, only spelling and word suggestions.

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

LineageOS, a free version of Android that runs on some Samsung phones, is translated by volunteers on
[Crowdin](https://crowdin.com/project/lineageos). Sardinian, Friulian and Welsh are already there; Corsican could be
added the same way. Google added Galician and Basque to Android after the Galician government asked.
