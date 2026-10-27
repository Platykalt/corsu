# Hyprland and Noctalia

[Français](../fr/hyprland.md)

> **Status: in development, not in the published release.** The code is on the development branch
> [`hyprland`](https://github.com/Platykalt/corsu/tree/hyprland), separate from the stable release: the published
> release, 0.28.2, does not contain it. Linux only; checked only on CachyOS with Hyprland 0.56.2 and Noctalia
> 5.3.0, and part of the checks are still to be done ([Checks](#checks)). Optional: installing Corsu never replaces
> your desktop; these parts are chosen one by one and the Plasma session stays.

[Hyprland](https://hyprland.org) is a Linux desktop where windows arrange themselves side by side; Noctalia adds the
top bar, the application launcher, notifications, the lock screen and settings. Corsu brings:

- **the Corsican translation of Noctalia**, and Corsican first for programs started in the Hyprland session;
- **optionally, a Corsu desktop profile**: ready key bindings, Corsu's look (maquis and sea palettes) and a guided
  configuration from the Corsu window, which detects what is installed, explains each choice and can remove it all.

**Corsu never installs a desktop**: you install Hyprland and Noctalia with your distribution, Corsu detects them.
Plasma stays installed and can be chosen at every login.

## Checks

Status on 23 October 2026, on one computer only: the maintainer's CachyOS laptop (Intel + NVIDIA RTX 5070, internal
panel wired to the NVIDIA), Hyprland 0.56.2, Noctalia 5.3.0, uwsm 0.27.1, Hyprland portal 1.4.1.

**Done**

- Configuration validated by `Hyprland --verify-config` and `noctalia config validate`.
- Real Hyprland in a **nested test session** (Hyprland inside a screenless virtual KWin, private D-Bus session bus,
  system bus hidden): configuration loaded without errors, 66 binds registered, `fr` keyboard, Noctalia started and
  in Corsican (welcome, bar, session menu, key help). Screenshots [below](#screenshots).
- Development build 0.28.0 from the branch installed on that computer with both parts; going back to 0.27.0 (then
  the published release) tried in a throwaway folder.
- A real Hyprland login reached the desktop; the KWallet wallet asked for its password and opened once that password
  was typed. This confirms that step only, not the rest of the session.
- CI: the branch's latest successful run ([39846551021](https://github.com/Platykalt/corsu/actions/runs/39846551021))
  covers commit `d687579`; the branch's later commits have no successful CI run yet.

**Still to check**

- Real use of the session: shortcuts typed on the AZERTY keyboard, launcher, settings, network, Bluetooth.
- Hybrid graphics (internal panel wired to the NVIDIA card).
- Battery and brightness.
- Suspend and resume, closing the lid.
- Locking and unlocking.
- Screen sharing: a real share in Firefox, Discord or OBS (starting the program proves nothing).
- Portals (file chooser, screenshots).
- Administrator authentication (polkit password prompt).
- Distributions other than CachyOS.
- Noctalia's Corsican: of 3,126 texts, 382 match a published Corsican translation, 267 existing Corsu usage, 2,375
  are AI proposals; none reviewed by a speaker
  ([provenance](https://github.com/Platykalt/corsu/blob/hyprland/src/hyprland/translations/PROVENANCE.md)).

## Screenshots

*Test environment (nested session)*, not a real login: 1280 × 720 virtual screen, without network or Bluetooth. On a
real screen the bar also shows network, Bluetooth, tray and brightness.

| Noctalia welcome (language only, without the profile) | Bar (with the profile) | Session menu |
| --- | --- | --- |
| ![Noctalia welcome in Corsican, test environment (nested session)](../images/hyprland/noctalia-welcome-co.png) | ![Noctalia bar, test environment (nested session)](../images/hyprland/noctalia-bar-co.png) | ![Session menu in Corsican, test environment (nested session)](../images/hyprland/noctalia-session-co.png) |

With the profile the welcome does not open: it would save its own colours over Corsu's. In the session menu Noctalia
cuts names that are too long ("Chjode a s…" for "Chjode a sessione", log out).

## What to install

| Package | What for |
| --- | --- |
| `hyprland` (0.55 or newer) | the desktop; the profile uses its Lua configuration |
| `noctalia` (5.x) | the bar, launcher, notifications, lock screen |
| `uwsm` | starts the session; the session language goes through `~/.config/uwsm/env-hyprland`, which only uwsm reads |
| `xdg-desktop-portal-hyprland` | the portals of the Hyprland session (screenshots, screen sharing) |
| `qt6ct` (advised with the profile) | colours of Qt programs, in the Hyprland session only |

The test computer (CachyOS) also has `wl-clipboard`, `cliphist`, `brightnessctl` and `libnewt` (the latter is used by
the `uwsm start select` menu); Corsu does not ask for them. On CachyOS, with the administrator password:

```sh
sudo pacman -S hyprland noctalia uwsm xdg-desktop-portal-hyprland qt6ct
```

Do not install the `cachyos-hypr-noctalia` preset: it conflicts with `cachyos-kde-settings`, which carries the
configuration of Plasma's login screen. On another distribution package names and availability may differ; not
tried yet.

## Getting the development build

These parts are in no published release: the usual install command installs 0.28.2, without them. To try them you
need the `hyprland` branch; this is for testers, not for daily use.

```sh
git clone --branch hyprland https://github.com/Platykalt/corsu.git corsu-hyprland
cd corsu-hyprland
./install/"Install for Linux.sh"
```

The Corsu window opens. In **Add**, tick **Hyprland and Noctalia** and, if you want it, **Corsu desktop profile for
Hyprland**, then follow the steps. Note: this replaces the installed Corsu with the development build, which calls
itself 0.28.2 too but is not the published 0.28.2. To go back to the published release, see [Going back](#going-back).

## Two separate choices

- **Hyprland and Noctalia** (`hyprland`, the language): Corsu's Corsican catalogue for Noctalia and its language set
  to Corsican; in the Hyprland session, Corsican first for programs, then your languages and English for what is not
  translated yet (for example `LANGUAGE=co:fr_FR:en`). Nothing visual changes. Ticked in advance only when Corsu
  finds a compatible Hyprland **and** Noctalia 5; otherwise offered unticked, or greyed out with the reason.
- **Corsu desktop profile for Hyprland** (`hyprland-profile`), **never ticked in advance**: ready Lua modules (keys,
  windows, input), the portals of the Hyprland session and Corsu's look for Noctalia. You can take the language
  without the profile, or the profile without the language.

The profile hides Noctalia from Plasma's menu (started from Plasma it would add a second panel over Plasma's): this
is the only visible change in Plasma, and it goes with the profile. Corsu says what it finds in the window (Add
page), in `corsu.py status` (the `hyprland` entry) and in the text menu (`app.py --text`).

## First login

1. **Save your documents and close your programs**: switching session closes everything that is open.
2. Log out of Plasma.
3. On the login screen choose the **"Hyprland (uwsm-managed)"** session (the session list is usually at the bottom of
   the screen), then type your password. Take that entry: the session language and a clean shutdown depend on it.
   The login screen then remembers the last session chosen.
4. **The KWallet wallet** may ask for a password. It is the vault where Plasma keeps your saved passwords (Wi-Fi,
   accounts, browser). Its password can differ from your login password: type **the wallet's password**. When it is
   the same as the login password the wallet should open by itself (intended, not observed yet). Do not delete the
   wallet or remove its password to make the question go away: your saved passwords are in it.

## Using the desktop

What follows applies with the Corsu desktop profile. **Super** is the Windows key (the Windows logo, between Ctrl
and Alt). **Super + F1** shows the list of shortcuts at any time, in Corsican.

- **Open a program**: **Super + Space**, or the magnifier on the left of the bar, opens the launcher; type the start
  of the name and press Enter.
- **Sound, network, brightness**: the icons on the right of the bar (click them), or the control centre with
  **Super + S**; the keyboard's volume and brightness keys work too.
- **Wallpaper and look**: **Super + W** picks the wallpaper; **Super + ,** opens Noctalia's settings (colours,
  bar…). Corsu's palette is "Corsu-Maquis", "Corsu-Mare" is the other one. Your choices in the settings always win;
  to get Corsu's look back see [Switching on, off, updating](#switching-on-off-updating).
- **Lock**: **Super + L**. When idle the screen locks after 10 minutes and turns off after 11.
- **Log out, restart, shut down**: **Super + Escape** (or Ctrl + Alt + Delete, or the button on the right of the
  bar) opens the session menu: "Chjode a sessione" logs out.
- **Back to Plasma**: log out, then choose **Plasma (Wayland)** on the login screen. Nothing needs uninstalling.

### Profile shortcuts

The full list, the same as **Super + F1** and as the branch's
[`keys.lua`](https://github.com/Platykalt/corsu/blob/hyprland/src/hyprland/config/corsu/keys.lua). Profile only:
without it, the shortcuts are those of your own Hyprland configuration.

| Keys | Effect |
| --- | --- |
| **Noctalia** | |
| Super + Space | open or close the application launcher |
| Super + F1 | show the key help |
| Super + S | open or close the control centre |
| Super + V | clipboard history |
| Super + N | switch "Do not disturb" on or off |
| Super + , | Noctalia settings |
| Super + W | pick the wallpaper |
| Super + L | lock the screen |
| Super + Escape | session menu (log out, restart, shut down…) |
| Ctrl + Alt + Delete | session menu (log out, restart, shut down…) |
| Alt + Tab | switch between windows |
| Print | screenshot of an area |
| Super + Shift + S | screenshot of an area |
| Shift + Print | screenshot of the whole screen |
| **Programs** | |
| Super + Enter | open a terminal (Konsole) |
| Super + E | open the file manager (Dolphin) |
| Super + B | open the web browser (Firefox) |
| **Windows** | |
| Super + Q | close the window |
| Alt + F4 | close the window |
| Super + M | maximise the window, or give it back its size |
| Super + F | full screen, or leave it |
| Super + T | floating window, or tiled with the others |
| Super + ← → ↑ ↓ | go to the window on the left, right, above, below |
| Super + Shift + ← → ↑ ↓ | move the window left, right, up, down |
| Super + left click held | move the window with the mouse |
| Super + right click held | resize the window with the mouse |
| **Workspaces** | |
| Super + 1 … 0 (number row) | go to workspace 1 to 10 |
| Super + Shift + 1 … 0 (number row) | send the window to workspace 1 to 10 |
| Super + Ctrl + → | next workspace |
| Super + Ctrl + ← | previous workspace |
| Super + wheel down | next workspace |
| Super + wheel up | previous workspace |
| **Laptop and multimedia keys** (also work on the lock screen) | |
| Volume + / Volume − | raise / lower the volume (repeats while held) |
| Mute | mute or unmute the sound |
| Microphone mute | mute or unmute the microphone |
| Brightness + / Brightness − | raise / lower the brightness (repeats while held) |
| Play, Pause | play or pause |
| Next, Previous | next track, previous track |

The number row works on an AZERTY keyboard without Shift: these are the & é " ' ( - è _ ç à keys. Corsu may replace
Konsole, Dolphin and Firefox with the programs found on the computer. On a touchpad, three fingers swiped left or
right change workspace, as in Plasma.

## Files changed

| File | Part | How |
| --- | --- | --- |
| `~/.config/uwsm/env-hyprland` | language (`language` block: `LANGUAGE`, `NOCTALIA_ASSETS_DIR`), profile (`profile` block: `qt6ct` Qt theme, cursor, menu prefix, graphics card order when needed) | two blocks between `# corsu:begin …` and `# corsu:end …`; your lines around them stay |
| `~/.local/share/corsu/noctalia/assets/` | language | Corsu's folder: Noctalia's assets (links) plus a `co.json` built at each run; kept when the language is switched off, as the lock screen of a Noctalia already running reads it again |
| `~/.config/noctalia/00-corsu-language.toml` | language | Corsu's layer (`lang = "co"`); a language picked in Noctalia's settings wins |
| `~/.config/noctalia/00-corsu-profile.toml`, `~/.config/noctalia/palettes/` | profile | Corsu's look layer and palettes; your choices in the settings win |
| `~/.local/state/noctalia/settings.toml` | — | your choices in Noctalia's settings: never changed by Corsu |
| `~/.config/hypr/corsu/*.lua`, `machine.lua` | profile | Corsu's files; `machine.lua` comes from detection (keyboard, outputs and scale) |
| `~/.config/hypr/hyprland.lua` | profile | written **only when you have none**, never rewritten afterwards; yours is kept (add `require("corsu.init")` to it) |
| `~/.config/hypr/user.lua` | — | **never read nor written** by Corsu: your settings go there |
| `~/.config/xdg-desktop-portal/hyprland-portals.conf` | profile | read only when the desktop is Hyprland; kept if it is yours |
| `~/.config/qt6ct/qt6ct.conf` | profile | written only when missing; read only in the Hyprland session |
| `~/.local/share/applications/dev.noctalia.Noctalia.desktop` | profile | a copy of Noctalia's entry with `OnlyShowIn=Hyprland`: Noctalia no longer shows in Plasma's menu |

Plasma is not touched: no global variable, no system file, and neither `kdeglobals`, `gtk-3.0/settings.ini`,
`gtk-4.0`, `mimeapps.list` nor `plasma-workspace/env/corsu.sh` (the tests check them byte for byte). Technical
details (session, graphics cards, portals):
[hyprland-system.md](https://github.com/Platykalt/corsu/blob/hyprland/docs/hyprland-system.md), on the branch.

## Switching on, off, updating

- **Switching on twice adds nothing**: each file is tracked in `installation.json` with its digest, each block and
  value with the value before.
- **Switching off** gives back only what is still Corsu's: a block you edited, a value changed in Noctalia, a file
  you edited stay as they are; a file that existed before Corsu comes back byte for byte; a file Corsu created goes.
  Switching the profile off removes the `hyprland.lua` Corsu wrote: Hyprland then uses its default configuration.
  Log out of the Hyprland session and back in.
- **Updates and repairs** keep your settings: what you changed in Noctalia, `user.lua`, and any Corsu file you edited
  (left as it is, with a message); unchanged files get the new version.
- **Put Corsu's look back** (the profile's button in the window, `r` in the text menu, or
  `installer.py --hyprland-reset-look`): Corsu's palettes and look layer come back, even edited (your version is
  first copied to `~/.local/share/corsu/backups/hyprland-reset/`). What you chose in Noctalia's settings always wins:
  the "Reset Page" button of each settings page goes back to Corsu's look there.

## Going back

Each step stands on its own; do only the ones you need.

1. **Back to Plasma**: log out (Super + Escape, "Chjode a sessione"), then choose **Plasma (Wayland)** on the login
   screen. Nothing is removed.
2. **Remove what Corsu added for Hyprland**: switch both parts off in the Corsu window, or from the branch's
   folder:

   ```sh
   python3 src/installer.py --yes --disable hyprland hyprland-profile
   ```

   Removed: Corsu's blocks in `~/.config/uwsm/env-hyprland`, `~/.config/hypr/corsu/`, the `~/.config/hypr/hyprland.lua`
   Corsu created, `~/.config/noctalia/00-corsu-*.toml`, the `Corsu-*.json` palettes,
   `~/.config/xdg-desktop-portal/hyprland-portals.conf` and `~/.config/qt6ct/qt6ct.conf` when Corsu created them, and
   the copy of Noctalia's entry. **Kept**: your settings made in Noctalia (`~/.local/state/noctalia/settings.toml`),
   `~/.config/hypr/user.lua`, any file you edited (with a message) and the `~/.local/share/corsu/noctalia/assets/`
   folder.
3. **Back to Corsu 0.28.2**, the published release, after step 2 (0.28.0 refuses the Hyprland parts still recorded and does not install; nothing is damaged):

   ```sh
   ~/.local/share/corsu/bin/corsu-python ~/.local/share/corsu/releases/<current folder>/src/update.py --install --version 0.28.2 --allow-downgrade
   ```

   The current folder is `release.folder` in `~/.local/share/corsu/installation.json`. Your other Corsu choices
   (Firefox, Plasma…) are kept.
4. **Uninstall Hyprland and Noctalia** if you no longer want them (CachyOS, administrator password):

   ```sh
   sudo pacman -Rns hyprland xdg-desktop-portal-hyprland uwsm noctalia qt6ct
   ```

   Add the other packages installed for it if nothing else uses them.

## Command line

From the branch's folder:

```sh
python3 src/installer.py --components hyprland                    # the language only
python3 src/installer.py --components hyprland hyprland-profile   # language and profile
python3 src/installer.py --disable hyprland-profile               # remove the profile, keep the language
python3 src/installer.py --hyprland-reset-look
python3 src/corsu.py status                                       # the "hyprland" entry
```

A first installation without a list (`--yes`) never takes the profile; an update keeps the parts already chosen,
switched on or off. See also [Installing Corsu on Linux](computer/linux.md).
