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
| KDE Plasma desktop and KDE programs | | | Used daily |
| GTK programs and terminal commands | | | Expected |

**Tested** means the CI installs Corsu on that system before every release, starts the program and reads its text
in Corsican. **Partly tested** means the CI checks that Corsu patches Discord and restores it, but does not open
Discord itself. **Used daily** means a Corsican speaker uses it every day. **Expected** means the code is there but
nobody has checked it on that system yet: please report how it goes. **Not supported** means Corsu does not do it,
usually because the system prevents it.

## Phones

| | Android | iPhone |
| --- | --- | --- |
| System menus | Not possible | Not possible |
| Firefox, Firefox Focus | In Corsican (Mozilla) | In Corsican (Mozilla) |
| Thunderbird, VLC | In Corsican | VLC in Corsican |
| Discord | Not possible | Not possible |
| Corsican keyboard | Gboard | Keyman |

The phone apps listed come in Corsican from their makers; Corsu does not change them. See [Android](phone/android.md)
and [iPhone](phone/iphone.md).

## Google and other websites

Corsu does not translate websites, but Firefox and the Chromium browsers tell websites that you prefer Corsican.
Sites that offer Corsican, Google among them, then show it, unless your account says otherwise. Google uses your
account's language first, and that also decides the language of its AI. To get Google in Corsican:

1. Open [myaccount.google.com/language](https://myaccount.google.com/language) and choose **Corsu** as your preferred
   language.
2. Without a Google account, open [search settings](https://www.google.com/preferences?hl=co#languages) and choose
   **Corsu**.
