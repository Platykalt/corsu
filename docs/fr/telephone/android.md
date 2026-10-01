# Le corse sur un téléphone Android

[English](../../en/phone/android.md)

Android et One UI (Samsung) ne proposent pas le corse, et seuls Google ou Samsung pourraient l'ajouter. Plusieurs
applications existent pourtant déjà en corse, traduites pour la plupart par Patriccollu di Santa Maria è Sichè, et
vous pouvez vous en servir dès aujourd'hui.

## Clavier

Gboard, le clavier de Google, a une disposition corse avec suggestions de mots. Dans les réglages de Gboard, ouvrez
Langues, touchez Ajouter un clavier et choisissez Corse.

## Applications en corse

Firefox, Firefox Focus, Thunderbird, K-9 Mail, VLC et OpenTracks sont disponibles en corse. VLC a son propre réglage
de langue. Les autres suivent la liste des langues du téléphone, qui ne propose pas le corse. On peut l'ajouter depuis
un ordinateur avec [ADB](https://developer.android.com/tools/adb), après avoir activé le débogage USB du téléphone :

```sh
adb shell settings put system system_locales co-FR,fr-FR
```

Redémarrez le téléphone. Les applications qui ont le corse l'utilisent, et le reste reste en français. Rechoisir sa
langue dans les réglages du téléphone annule le changement.

Sous Android 13 ou plus récent, on peut aussi ne changer qu'une seule application :

```sh
adb shell cmd locale set-app-locales org.mozilla.firefox --locales co-FR
```

## Le système lui-même

LineageOS, une version libre d'Android qui fonctionne sur certains téléphones Samsung, est traduit par des bénévoles
sur [Crowdin](https://crowdin.com/project/lineageos). Le sarde, le frioulan et le gallois y sont déjà ; le corse
pourrait y être ajouté de la même façon. Google a ajouté le galicien et le basque à Android après une demande du
gouvernement galicien.
