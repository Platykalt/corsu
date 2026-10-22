# Corsu's profile for Noctalia 5.3

Read in Noctalia's source (tag `v5.3.0`) and its user documentation (`docs/user/configuration/index.mdx`). Not yet
observed in a running Noctalia.

## Where Noctalia keeps what

| What | Where | Owner |
| --- | --- | --- |
| Base configuration | every `*.toml` directly in `$NOCTALIA_CONFIG_HOME/noctalia/`, else `$XDG_CONFIG_HOME/noctalia/` (`~/.config/noctalia/`), merged in alphabetical order, later files winning (`src/config/config_service.cpp:382-399`, `deepMerge` 1407-1429) | the person, and Corsu's files below |
| Choices made in Settings, setup wizard, IPC | `~/.local/state/noctalia/settings.toml`, merged last, so it wins (`config_service.cpp:564-571`) | Noctalia |
| UI state | `~/.local/state/noctalia/state.toml` | Noctalia |
| Wallpaper choice | `settings.toml`, `[wallpaper.default] path` and `[wallpaper.monitors.<output>] path` (`src/config/config_overrides.cpp:2304-2345`) | Noctalia |
| Setup wizard done | `~/.local/state/noctalia/.setup-complete` (`config_service.cpp:571`, `679-686`) | Noctalia |
| Custom palettes | `~/.config/noctalia/palettes/<name>.json` | the person, and Corsu's palettes |

Corsu writes only in the base layer and never touches `~/.local/state/noctalia/`. Whatever the person changes in
Noctalia's Settings goes to `settings.toml` and keeps winning after restarts and after Corsu updates its files.

## Files Corsu writes (profile component)

| Source in this folder | Written to | When |
| --- | --- | --- |
| `00-corsu-profile.toml` | `~/.config/noctalia/00-corsu-profile.toml` | profile enabled; replaced on update while its digest is still Corsu's |
| `palettes/Corsu-Maquis.json`, `palettes/Corsu-Mare.json` | `~/.config/noctalia/palettes/` | profile enabled |
| `qt6ct.conf` (`@CONFIG_HOME@` replaced by the absolute config folder) | `~/.config/qt6ct/qt6ct.conf` | profile enabled and no such file yet |
| `00-corsu-language.toml` | `~/.config/noctalia/00-corsu-language.toml` | **language** component (see `../translations/LOADING.md`) |

The `00-` prefix sorts them before `config.toml` and any other file the person writes, so theirs win. A person who
uses `[include] autoload = false` loads only the files they list: Corsu's files are then ignored, which is their
choice.

## Resetting the visual profile

- Inside Noctalia: **Reset Page** on a Settings page (Theme, Bar…) removes the person's overrides of that page from
  `settings.toml` (`clearOverrides`, `src/shell/settings/settings_window_mutations.cpp:175-200`), which brings back
  Corsu's values.
- From Corsu: rewrite `00-corsu-profile.toml` and the palettes from these sources. Other settings in `settings.toml`
  (wallpaper, language, widgets the person added) stay as they are. Corsu does not edit `settings.toml`: it is
  Noctalia's file, rewritten by the running shell.

## Theme templates and files shared with Plasma

Built-in templates run only when listed in `theme.templates.builtin_ids` (empty by default,
`src/config/config_types.h:1753-1754`). The profile lists only `qt`:

- `qt` writes `~/.config/qt5ct/colors/noctalia.conf` and `~/.config/qt6ct/colors/noctalia.conf` (new files). qt6ct
  is read only where `QT_QPA_PLATFORMTHEME=qt6ct`, which A's env-hyprland sets for the Hyprland session only; Plasma
  never reads it. `qt6ct.conf` points qt6ct to that colour file.
- `kcolorscheme` stays off: its post action edits `~/.config/kdeglobals` (`src/theme/kde_color_scheme.cpp:198`),
  Plasma's main settings file.
- `gtk3`/`gtk4` stay off: `gtk/apply.sh` appends an import to `~/.config/gtk-3.0/gtk.css` and `gtk-4.0/gtk.css` and
  sets the GTK theme through GSettings, all shared with Plasma.
- `theme.sync_color_scheme` is off for the same reason (it writes `org.gnome.desktop.interface color-scheme`).
- Hyprland's `cursor.sync_gsettings_theme` is off in `config/corsu/look.lua` for the same reason.

A person can still turn any template on in Settings; that choice is theirs and lands in `settings.toml`.

## Key help

`00-corsu-profile.toml` declares a launcher provider `/tasti` (`[shell.launcher.dmenu.entry.corsu-keys]`, documented in
`docs/user/launcher/index.mdx`, "Persistent dmenu entries"). It lists `$XDG_RUNTIME_DIR/corsu/hypr-keys.tsv`, which
`config/corsu/binds.lua` writes at each Hyprland config load from the same table it binds (`config/corsu/keys.lua`).
SUPER + F1 opens the launcher on `/tasti`. Choosing a line does nothing (`exec = "true"`; without `exec` Noctalia would
copy the line to the clipboard). Noctalia has no keybinding cheat sheet of its own.

## Palettes

`Corsu-Maquis` (default) and `Corsu-Mare` reuse the colours of Corsu's own window (`src/app/style.css`, palettes
`maquis` and `mare`): accent, surfaces, text, plus `granitu` as tertiary. Text on each surface and on each accent keeps
a contrast of at least 4.5:1 (`tests/test_hyprland_config.py`).

Noctalia 5.3 is MIT-licensed; the profile follows its documented keys (`example.toml`, `docs/user/`) without copying
its files.
