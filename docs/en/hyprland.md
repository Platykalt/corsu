# Hyprland and Noctalia

[Français](../fr/hyprland.md)

Corsu can put a [Hyprland](https://hyprland.org) session with the Noctalia panel in Corsican and, if you ask for it,
add its own desktop profile. **Corsu never installs a desktop**: you install Hyprland, Noctalia, uwsm and
xdg-desktop-portal-hyprland with your distribution; Corsu detects them. This part exists on Linux only and has so far
been tried on simulated folders only (no real Hyprland has run it).

## What you need

| Program | Version | Why |
| --- | --- | --- |
| Hyprland | 0.55 or newer | the Lua configuration the profile uses |
| Noctalia | 5.x | its TOML settings and JSON catalogues |
| uwsm | any | the session language goes through `~/.config/uwsm/env-hyprland`, which only uwsm reads |
| xdg-desktop-portal-hyprland | any | the portals (screenshots, screen sharing) of the Hyprland session |

Corsu says what it finds: in the window (Add page), in `corsu.py status` (the `hyprland` entry: versions, verdict,
state of both parts) and in the text menu (`app.py --text`). Without Hyprland both choices stay listed, greyed out,
with the reason; with a Hyprland too old they are "blocked" with the version needed.

## Two separate choices

- **Hyprland and Noctalia** (`hyprland`, the language): Corsu's Corsican catalogue for Noctalia and its language set
  to Corsican; in the Hyprland session, Corsican first for programs, then your languages and English for what is not
  translated yet (for example `LANGUAGE=co:fr_FR:en`). Nothing visual changes.
- **Corsu desktop profile for Hyprland** (`hyprland-profile`), **never ticked in advance**: ready Lua modules (keys,
  windows, input), the portals of the Hyprland session and Corsu's look for Noctalia (maquis and sea palette). You can
  take the language without the profile, or the profile without the language.

## Files changed

| File | Part | How |
| --- | --- | --- |
| `~/.config/uwsm/env-hyprland` | language (`language` block), profile (`profile` block) | a block between `# corsu:begin …` and `# corsu:end …`; your lines around it stay |
| `~/.local/share/noctalia/translations/co.json` | language | Corsu's file |
| `~/.config/noctalia/settings.toml` | language (`language`), profile (look settings) | one value at a time, the previous one kept |
| `~/.config/hypr/corsu/*.lua`, `machine.lua` | profile | Corsu's files; `machine.lua` comes from detection (keyboard, scale, graphics card) |
| `~/.config/hypr/hyprland.lua` | profile | written **only when you have none**; yours is kept |
| `~/.config/hypr/user.lua` | — | **never read nor written** by Corsu: your settings go there |
| `~/.config/xdg-desktop-portal/hyprland-portals.conf` | profile | read only when the desktop is Hyprland; kept if it is yours |
| `~/.config/noctalia/colorschemes/` | profile | Corsu's palette |

Plasma is not touched: no global variable, no system file, and neither `kdeglobals`, `gtk-3.0/settings.ini`, `gtk-4.0`,
`mimeapps.list` nor `plasma-workspace/env/corsu.sh` (the tests check them byte for byte).

## Switching on, off, updating

- **Switching on twice adds nothing**: each file is tracked in `installation.json` with its digest, each block and
  value with the value before.
- **Switching off** gives back only what is still Corsu's: a block you edited, a value changed in Noctalia, a file
  you edited stay as they are; a file that existed before Corsu comes back byte for byte; a file Corsu created goes.
  Switching the profile off removes the `hyprland.lua` Corsu wrote: Hyprland then uses its default configuration.
  Log out of the Hyprland session and back in.
- **Updates and repairs** keep your settings: what you changed in Noctalia, `user.lua`, and any Corsu file you edited
  (left as it is, with a message in the window and the log); unchanged files get the new version.
- **Put Corsu's look back** (the profile's button in the window, `r` in the text menu, or
  `installer.py --hyprland-reset-look`): the profile's palette and look settings come back; your other Noctalia
  settings, the language, Hyprland and `user.lua` do not move. A palette you had edited is first copied to
  `~/.local/share/corsu/backups/hyprland-reset/`.

## Command line

```sh
python3 src/installer.py --components hyprland                    # the language only
python3 src/installer.py --components hyprland hyprland-profile   # language and profile
python3 src/installer.py --disable hyprland-profile               # remove the profile, keep the language
python3 src/installer.py --hyprland-reset-look
python3 src/corsu.py status                                       # the "hyprland" entry
```

A first installation without a list (`--yes`) never takes the profile; an update keeps the parts already chosen,
switched on or off.
