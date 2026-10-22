# Hyprland + Noctalia in Corsu (optional component)

Work in progress on branch `hyprland` (from `next-0.28`). Nothing here is published.

## What Corsu does and does not do

- Corsu never installs a desktop. The person installs Hyprland and Noctalia with their distribution; Corsu detects
  them and offers two separate choices:
  - **`hyprland`, language**: Noctalia's interface in Corsican, Corsican first for programs started in the Hyprland
    session (`LANGUAGE`), with an explicit fallback for missing texts. Nothing visual changes.
  - **`hyprland-profile`, Corsu desktop profile** (optional, off by default for other people): a ready-to-use Hyprland
    configuration (keys, input, window rules, portals per session) and Corsu's look for Noctalia (maquis/sea palette).
- Plasma stays as it is: no global variable, no system file, no change to files shared with Plasma
  (`kdeglobals`, `gtk-3.0/settings.ini`, `gtk-4.0`, dconf, `mimeapps.list`) unless named in this file with a reason.
- Every file Corsu writes goes through the existing tracking (`installer.state['files']`, digests, `apps/settings.py`
  for single values) so that repeated activation adds nothing twice, and disabling gives back only what is still
  Corsu's, leaving the person's later changes.

## Versions targeted (CachyOS, 22 October 2026)

hyprland 0.56.2 (Lua configuration: `/usr/share/hypr/hyprland.lua`, stubs `/usr/share/hypr/stubs/hl.meta.lua`),
noctalia 5.3.0 (native C++, TOML config, JSON translations in `/usr/share/noctalia/assets/translations/`),
xdg-desktop-portal-hyprland 1.4.1, uwsm 0.27.1. The CachyOS preset `cachyos-hypr-noctalia` is **not** used: it
conflicts with `cachyos-kde-settings` (which carries SDDM's Wayland greeter configuration) and installs a global
`/etc/profile.d/Hyprland.sh`; it is GPL-1.0-only, so none of its files are copied here.

## Layout (owners while the work is split)

| Path | Owner | Content |
| --- | --- | --- |
| `src/hyprland_system.py`, `tests/test_hyprland_system.py`, `docs/hyprland-system.md` | A | detection (versions, GPUs and which card drives which connector, keyboard layout, outputs), session environment lines, portal configuration, checks |
| `src/hyprland/session/` | A | per-session files: uwsm `env-hyprland` template, `xdg-desktop-portal/hyprland-portals.conf`, menu entry overrides limited to Hyprland |
| `src/hyprland/config/` | B | Hyprland Lua: `hyprland.lua` starter (written only when the person has none), `corsu/*.lua` modules managed by Corsu, `user.lua` left to the person |
| `src/hyprland/noctalia/` | B | Noctalia profile (settings, palette, key help) |
| `src/hyprland/translations/` | B | Noctalia Corsican catalogue `co.json`, `PROVENANCE.md`, `LOADING.md` (how Noctalia loads it durably) |
| `tests/test_hyprland_config.py`, `tests/test_noctalia_translation.py` | B | config syntax, placeholders and plurals kept |
| `src/apps/hyprland.py`, wiring in `src/installer.py`, `src/corsu.py`, `src/app/*` | C | the component: detect, state, enable, disable, restore, profile apart from language |
| `tests/test_hyprland.py`, `docs/fr/hyprland.md`, `docs/en/hyprland.md` | C | tests in isolated folders, documentation |

Files on the person's computer once enabled:

- `~/.config/uwsm/env-hyprland`: read by uwsm only for the Hyprland session (Corsu block between markers).
- `~/.config/xdg-desktop-portal/hyprland-portals.conf`: used only when `XDG_CURRENT_DESKTOP=Hyprland`.
- `~/.config/hypr/corsu/*.lua`: Corsu's modules (profile); `~/.config/hypr/corsu/machine.lua` generated from detection
  (keyboard, scale, GPU); `~/.config/hypr/hyprland.lua` loads them, then `~/.config/hypr/user.lua` last.
- Noctalia: see `translations/LOADING.md` and `noctalia/` for the exact files.

Machine-specific values (connector names, card paths, scale) are never written in templates: they come from detection
at enable time.
