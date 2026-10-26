# What works where

[Français](../fr/compatibilite.md)

| Program | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Firefox | Tested | Tested | Tested, used daily |
| Google Chrome | Tested | Not supported | Tested |
| Opera GX | Expected | Not supported | Tried by hand |
| Opera, Edge, Brave, Vivaldi, Chromium | Expected | Not supported | Expected |
| Discord desktop app | Partly tested | Partly tested | Partly tested, used daily |
| Vesktop | Expected | Expected | Expected |
| Discord in a browser | Not supported | Not supported | Not supported |
| Safari | | Not possible | |
| Google's buttons and menus (in Firefox Corsu) | Tried by hand | Expected | Tried by hand |
| KDE Plasma desktop and KDE programs | Not supported | Not supported | Used daily |
| Minecraft: Java Edition 1.6.1 → 26.3, 87 versions (resource pack) | Checked without running the game | Checked without running the game | Checked without running the game |
| GTK programs and terminal commands | | | Expected |
| Hyprland session and Noctalia, optional ([details](hyprland.md)) | | | Development branch, not in 0.28.0 |

Programs that already have their own Corsican translation (VLC, Audacity, Poedit, 7-Zip…), and the systems for
each, are in [Translation status](translation-status.md).

**Tested** means the CI installs Corsu on that system before every release, starts the program and reads its text
in Corsican. **Partly tested** means the CI checks that Corsu patches Discord and restores it, but does not open
Discord itself. **Used daily** means a Corsican speaker uses it every day. **Expected** means the code is there but
nobody has checked it on that system yet: please report how it goes. **Development branch** means the code is on a
separate branch, in no published release, and was tried only on the maintainer's computer. **Not supported** means
Corsu does not do it, usually because the system prevents it. Safari is part of macOS: Apple protects it and only offers the
languages of macOS, which does not include Corsican.

KDE Plasma is a Linux desktop. Some KDE programs (Kate, Krita, Okular…) also run on Windows and macOS, but Corsu
only translates them on Linux. **Checked without running the game** means the translation file is complete and
each Minecraft version's own code reads it and renders every text without error (`tools/mcversions.py verify`,
exceptions in [COMPATIBILITY.md](../../minecraft/java/COMPATIBILITY.md)). Only 26.3 has been loaded in a game (the
maintainer's Prism instance), with no visual check of every screen.

## Phones

| | Android | iPhone |
| --- | --- | --- |
| System menus | Not possible | Not possible |
| Firefox, Firefox Focus | In Corsican (Mozilla) | In Corsican (Mozilla) |
| Thunderbird, VLC | In Corsican | VLC in Corsican |
| Discord | Not possible | Not possible |
| Corsican keyboard | Gboard, or Keyman with the Corsu dictionary | Keyman with the Corsu dictionary |

The phone apps listed come in Corsican from their makers; Corsu does not change them. The Corsu dictionary for
Keyman suggests words and corrections; with Keyman 18 there is no automatic correction. See [Android](phone/android.md)
and [iPhone](phone/iphone.md).

## Google and other websites

Corsu does not translate websites, with one exception: in Firefox Corsu, the buttons and menus Google leaves in
French or English are completed in Corsican. Firefox and the Chromium browsers also tell websites that you prefer
Corsican.
Sites that offer Corsican, Google among them, then show it, unless your account says otherwise. Google uses your
account's language first, and that also decides the language of its AI. To get Google in Corsican:

1. Open [myaccount.google.com/language](https://myaccount.google.com/language) and choose **Corsu** as your preferred
   language.
2. Without a Google account, open [search settings](https://www.google.com/preferences?hl=co#languages) and choose
   **Corsu**.

Answers from Google's AI (AI Overview, AI Mode, Gemini) are written by Google at search time. Corsu cannot choose
their language, and Corsican is not among the languages Google guarantees for these answers: they sometimes start in
Corsican and then switch to French. Asking in Corsican and adding "rispondi in corsu" makes a Corsican answer more
likely. For an AI that speaks Corsican, see [LIV](https://liv.corsica) and [Astutu](https://astutu.corsica).
