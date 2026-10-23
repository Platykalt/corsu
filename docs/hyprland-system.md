# Hyprland session: system integration

How Corsu's optional Hyprland + Noctalia component fits next to Plasma without changing it. Detection and the
generated files are in `src/hyprland_system.py` (tests: `tests/test_hyprland_system.py`). Versions this note was
checked against (CachyOS, 22 October 2026): Hyprland 0.56.2 (aquamarine 0.15.1), Noctalia 5.3.0, uwsm 0.27.1,
xdg-desktop-portal 1.22.1, xdg-desktop-portal-hyprland (XDPH) 1.4.1, xdg-desktop-portal-kde 6.8.1, NVIDIA 615.78.08.

"Read" below means read in the package files, the source or the documentation; "seen" means observed on the
maintainer's laptop (Acer Predator PHN18-72, Plasma 6.8 session). Nothing here was observed inside a running
Hyprland session yet.

## Session start: use "Hyprland (uwsm-managed)"

The hyprland package installs two login entries (read): `hyprland.desktop` (`Exec=/usr/bin/start-hyprland`) and
`hyprland-uwsm.desktop` (`Exec=uwsm start -e -D Hyprland hyprland.desktop`, `TryExec=uwsm`).

Corsu recommends the **uwsm-managed** entry:

- uwsm starts the `hyprland.desktop` entry, so `start-hyprland` (Hyprland's watchdog with safe mode) still runs.
- It reads `~/.config/uwsm/env-hyprland` for this desktop only, exports the result to the systemd user manager and,
  with dbus-broker (installed here, seen), to D-Bus activation, and **unsets it when the session ends** (uwsm README).
  Plasma started afterwards does not inherit Hyprland's variables.
- It activates `graphical-session.target`, which XDPH's unit is bound to (`PartOf=graphical-session.target`, read),
  and runs XDG autostart through systemd.

Logging out must go through `uwsm stop`, not Hyprland's `exit` dispatcher (Hyprland wiki, UWSM page). SDDM remembers
the last session (`RememberLastSession=true`, seen): after one Hyprland login, the next login proposes Hyprland.

## Where the session variables go

| Place | Read by | Use |
| --- | --- | --- |
| `~/.config/uwsm/env-hyprland` | uwsm, as shell, before Hyprland starts, only when `XDG_CURRENT_DESKTOP` holds `Hyprland` (file name is the desktop name lowercased); exported to systemd user units and D-Bus-activated services | **Corsu's block**, between `# corsu:begin` / `# corsu:end` |
| `~/.config/uwsm/env` | uwsm, for every uwsm-managed desktop | not used by Corsu (would leak into other uwsm desktops) |
| `hl.env()` in `hyprland.lua` | the Hyprland process and what it starts itself; Hyprland exports only a fixed list to systemd/D-Bus (`DISPLAY WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE XDG_CURRENT_DESKTOP QT_QPA_PLATFORMTHEME PATH XDG_DATA_DIRS`, read in the binary) | not used for Corsu's variables: portals, the KDE file dialog and D-Bus-started programs would not see `LANGUAGE` |
| `~/.config/plasma-workspace/env/corsu.sh` | Plasma only | Corsu's KDE component; untouched |

The Hyprland wiki says the same: with uwsm, put variables in uwsm's files, `AQ_*`/`HYPR*` in `env-hyprland`, and avoid
`hl.env()`.

### The block Corsu writes

Each line is written only when its condition holds:

- `LANGUAGE=co:<languages>`: built like `apps.corsican_first()` (Corsican, then the person's languages from
  `LANGUAGE`, else `LC_ALL`, `LC_MESSAGES`, `LANG`). On this laptop it gives `co:fr` because Plasma's session has
  `LANGUAGE=co:fr`; `LANG` is `en_US.UTF-8`, so the same function run from a bare console would give `co:en_US`.
- `QT_QPA_PLATFORMTHEME=qt6ct`: only when qt6ct's plugin is installed.
- `XDG_MENU_PREFIX=plasma-`: only `/etc/xdg/menus/plasma-applications.menu` exists (seen) and Plasma alone sets the
  prefix; without it KDE programs (Dolphin's "Open with", the KDE file dialog) find no application menu outside Plasma.
- `XCURSOR_THEME`/`XCURSOR_SIZE` from Plasma's `kcminputrc` when the theme is installed; `HYPRCURSOR_*` only when the
  theme also has a hyprcursor manifest.
- `AQ_DRM_DEVICES`: only when aquamarine's own choice differs from the one wanted (see below). Never on this laptop.

Not written, on purpose:

- `WLR_NO_HARDWARE_CURSORS`: a wlroots variable; Hyprland has used aquamarine, not wlroots, since 0.42. Cursor problems
  are handled by Hyprland's `no_hardware_cursors` cursor option, in the Lua configuration.
- `GBM_BACKEND=nvidia-drm`: Mesa's GBM loader already loads `<DRM driver>_gbm.so`, and nvidia-utils ships
  `/usr/lib/gbm/nvidia-drm_gbm.so` (seen). Forcing it would also apply to processes rendering on the Intel card.
- `__GLX_VENDOR_LIBRARY_NAME=nvidia`: GLX only (Xwayland programs), and part of per-program offload (`prime-run`).
  Session-wide it breaks GLX programs whenever Xwayland renders on the Intel card.
- `LIBVA_DRIVER_NAME`: both `iHD` and `nvidia` VA-API drivers are installed (seen); libva picks the one matching the
  card the program opens. Forcing one breaks video decoding for programs on the other card.
- `NVD_BACKEND`, `ELECTRON_OZONE_PLATFORM_HINT`, `GDK_BACKEND`, `QT_QPA_PLATFORM`, `SDL_VIDEODRIVER`: per-program
  choices with known breakage (the wiki warns about several); nothing in Corsu's scope needs them.
- XDG base variables: uwsm sets them.

## Graphics cards

### What this laptop has (seen, read-only)

| Card | PCI slot | Driver | Outputs | boot_vga |
| --- | --- | --- | --- | --- |
| `card1` (number changes between boots) | `0000:00:02.0` Intel Arrow Lake | i915 (xe also loaded, unused) | DP-1, DP-2 (disconnected; probably the USB-C ports, `/sys/class/typec` has two) | 0 |
| `card2` | `0000:01:00.0` RTX 5070 Laptop | nvidia 615.78.08 open, `modeset=Y fbdev=Y` | **eDP-1 connected** (AUO, 2560x1600, 387x242 mm from EDID), HDMI-A-1, DP-3 | 1 |

Stable names: `/dev/dri/by-path/pci-0000:00:02.0-card`, `/dev/dri/by-path/pci-0000:01:00.0-card`. The backlight is
`nvidia_0`, `nvidia_wmi_ec_backlight` is loaded, and `/proc/driver/nvidia/gpus/0000:01:00.0/power` says
"Runtime D3 status: Not supported" (it cannot power down while it drives the panel).

**Graphics switch (MUX).** The built-in panel is wired to the NVIDIA card and the NVIDIA card is the boot VGA device,
which a hybrid-only laptop cannot do: this laptop has a hardware switch and it is currently set to the dedicated
card. Linux exposes no control for it here: `acer-wmi` (with the out-of-tree `predator_sense` attributes:
`backlight_timeout`, `battery_calibration`, `battery_limiter`, `boot_animation_sound`, `fan_speed`, `lcd_override`,
`usb_charging`) has no GPU-mode attribute, and there is no `/sys/class/firmware-attributes` device. The switch is set
in the firmware setup or PredatorSense on Windows. Corsu does not touch it.

### What Hyprland does by itself

aquamarine 0.8 and later (read in `src/backend/drm/DRM.cpp` of 0.15.1): without `AQ_DRM_DEVICES` it opens **every**
KMS card, puts the boot VGA card first, then moves in front the card with the most *connected* built-in panels
(eDP, LVDS, DSI). The first card renders; outputs on the others get a copy (multi-GPU blit).

- **Panel on the NVIDIA card (this laptop now):** NVIDIA renders and drives eDP-1, HDMI-A-1 and DP-3 directly.
  An external screen on DP-1/DP-2 (Intel) works through a copy to the Intel card. `prime-run` is pointless here:
  everything already runs on NVIDIA.
- **Panel on the Intel card (switch set to hybrid):** Intel renders and drives the panel and its own outputs. Screens on
  HDMI-A-1/DP-3 still work because the NVIDIA card stays in the list, but they wake it. Programs that need the NVIDIA
  card are started with `prime-run` (`__NV_PRIME_RENDER_OFFLOAD=1 __VK_LAYER_NV_optimus=NVIDIA_only
  __GLX_VENDOR_LIBRARY_NAME=nvidia`, installed by nvidia-prime) (launchers that honour `PrefersNonDefaultGPU=true` do the same; not checked for
  Noctalia's); these variables are per program, never in the session file.
- **Single card:** nothing to choose.

Because the order is computed at each start, it follows the switch when it is changed in the firmware.

### When Corsu writes `AQ_DRM_DEVICES`

`aq_drm_devices()` gives the wanted order (the card with the connected built-in panel first, then the others, by
their by-path names; None with one card). `gpu_lines()` writes it only when it differs from aquamarine's own order,
which in practice means a machine with built-in panels on two cards. On this laptop it writes nothing.

The by-path names cannot be put in the variable as they are: `AQ_DRM_DEVICES` is split on `:` and
`pci-0000:01:00.0-card` contains colons (Hyprland wiki, Multi-GPU; aquamarine splits with `CVarList(..., ':')`).
`/dev/dri/cardN` must not be written either (numbers change between boots). Corsu's lines therefore resolve each
by-path name to its card node **when uwsm sources the file at login**, skip a card that is absent, and leave the
variable unset if none is found, so Hyprland never starts without a GPU. A udev rule giving a colon-free name would also
work but needs root; it is not needed.

Optional, not done: listing only the Intel card (hybrid mode, no external screen on NVIDIA) could let the NVIDIA card
sleep longer, but outputs on the NVIDIA card would then stay dark. Not tested.

### Scale

`suggested_scale()` aims at about 110 logical pixels per inch for a built-in panel and 96 for a monitor, among scales
that divide the resolution into whole pixels, without overshooting by more than 0.1. For eDP-1 (2560x1600, 387 mm wide,
168 ppi) it suggests **1.6**; the person uses **1** in Plasma (`kwinoutputconfig.json`, seen, with a 48-pixel
cursor). `outputs()` returns both; the profile should keep the Plasma value when there is one, so that both sessions
look the same, and offer the suggestion.

## Keyboard

`keyboard()` reads Plasma's `kxkbrc` first (only when `Use=true`), then `localectl status`, then
`/etc/X11/xorg.conf.d/00-keyboard.conf`. Here: no `kxkbrc` layout section, `localectl` gives `X11 Layout: fr`
(AZERTY), no variant, model or options (seen). Hyprland's `kb_layout`, `kb_variant`, `kb_model`, `kb_options` take the
same comma-separated values.

## Portals

xdg-desktop-portal looks for `<desktop>-portals.conf` (desktop name lowercased) in `~/.config/xdg-desktop-portal/`
first, then the system folders; the first file found is used as a whole (portals.conf(5)). Plasma keeps
`/usr/share/xdg-desktop-portal/kde-portals.conf`; Corsu writes `~/.config/xdg-desktop-portal/hyprland-portals.conf`,
which replaces the packaged `hyprland-portals.conf` (`default=hyprland;gtk`) only in Hyprland. With the backends
installed here (gtk, kde, kwallet, plasmanotify, plus hyprland once XDPH is installed):

```ini
# Written by Corsu for the Hyprland session; Plasma uses kde-portals.conf.
[preferred]
default=hyprland;gtk
org.freedesktop.impl.portal.FileChooser=kde;gtk
org.freedesktop.impl.portal.Settings=kde;gtk
org.freedesktop.impl.portal.Secret=kwallet
```

- **hyprland** (XDPH): Screenshot, ScreenCast, GlobalShortcuts, InputCapture (its `.portal` file, read). XDPH has no
  file dialog.
- **FileChooser = kde**: the same dialog, places and bookmarks as in Plasma; this exact override is the one documented
  on the wiki's XDPH page. The KDE backend is D-Bus-activated through `plasma-xdg-desktop-portal-kde.service`, whose
  `After=plasma-core.target` is an ordering, not a requirement, so it starts outside Plasma. Its ScreenCast and
  RemoteDesktop need KWin and must never be chosen under Hyprland; listing only FileChooser keeps them unused.
  gtk is the fallback when the KDE backend is absent. Firefox uses the portal dialog only with
  `widget.use-xdg-desktop-portal.file-picker = 1`.
- **Settings = kde;gtk**: light/dark preference and accent colour come from Plasma's `kdeglobals` first (as in Plasma's
  own file), so programs look the same in both sessions without Corsu writing shared files.
- **Secret = kwallet**: `ksecretd` owns `org.freedesktop.secrets` and the kwallet portal (seen); the portal is
  D-Bus-activatable (`org.freedesktop.impl.portal.desktop.kwallet.service`). There is no gnome-keyring.
- Not chosen: **plasmanotify** (lives in plasmashell); notifications go through gtk's Notification backend to
  Noctalia's notification daemon. Inhibit stays with gtk.

Corsu writes only the backends that exist (`portals_conf()` reads `/usr/share/xdg-desktop-portal/portals/`).

## Screen sharing

Needs: pipewire 1.6.10 and wireplumber 0.5.18 (installed, seen), XDPH, and the portal file above. XDPH's picker is
Qt 6; Qt 6.12's Wayland plugin is in qt6-base (seen), so no separate qt6-wayland is needed. `grim` and `slurp` are
optional dependencies for XDPH's screenshot portal (not installed). If DMA-BUF sharing between cards fails (black
picture), `force_shm = true` in `~/.config/hypr/xdph.conf` is XDPH's documented workaround (profile side).

How to test, inside the Hyprland session, distinguishing a launch from a real share:

1. Portal running: `systemctl --user status xdg-desktop-portal-hyprland` is active and
   `busctl --user list | grep portal.desktop.hyprland` shows the name.
2. Routing: `/usr/lib/xdg-desktop-portal -r -v` (replaces the running one, for the test only) logs which backend
   serves each interface: ScreenCast must say hyprland, FileChooser kde.
3. Launch only: Firefox, `https://mozilla.github.io/webrtc-landing/gum_test.html`, "Screen capture": XDPH's picker
   appears. That proves the portal call, not the picture.
4. Real share: after choosing a screen, the page's preview must **move** (open a clock or drag a window), and
   `pw-top` must show a video node from xdg-desktop-portal-hyprland with a running state while sharing.
5. Discord: the official client is Electron; under Xwayland it only sees Xwayland windows (wiki). Vesktop (installed)
   uses the portal. The test is the stream preview seen by a second account or device, not the picker. OBS (not
   installed): "Screen Capture (PipeWire)" source, preview must move.

## Lid, sleep, idle

- logind has no overrides here (`/etc/systemd/logind.conf` holds only `[Login]`, no drop-ins, seen), so its
  defaults apply: lid closed suspends on battery and on mains; with an external screen connected ("docked") it does
  nothing. In Plasma, PowerDevil handles the lid instead; PowerDevil's autostart is `OnlyShowIn=KDE` (seen), so in
  Hyprland logind decides.
- Noctalia locks before sleep (`lock_before_suspend`, default true, Noctalia docs) via logind's sleep delay
  inhibitor, offers an idle inhibitor ("caffeine"), and serves `org.freedesktop.ScreenSaver` so browsers and video
  players can hold the screen on (read in the binary). No separate idle daemon is needed.
- Turning the panel off when the lid closes while docked would need a Hyprland switch binding; the profile has none
  yet (none in `src/hyprland/config`), so with the lid closed and an external screen the internal panel stays on as
  far as Hyprland is concerned. Not checked on a real docked laptop.

## Wallet at login

SDDM's PAM file loads `pam_kwallet5.so` in `auth` and `session` (seen), whatever session is chosen, and leaves
`PAM_KWALLET5_LOGIN` (a socket) in the session's environment. The wallet is only opened when
`/usr/lib/pam_kwallet_init` sends the password to that socket. Plasma runs it from `plasma-kwallet-pam.service`, which
only Plasma's target pulls in; the XDG autostart copy has `X-systemd-skip=true` (seen), so uwsm's systemd autostart
skips it. **The Hyprland session must run `/usr/lib/pam_kwallet_init` once at start** (profile, when the file exists),
otherwise the first program asking for a secret prompts for the wallet password. Not yet observed in a session.

## Administrator prompts (polkit)

Only one polkit agent can register per session. Plasma's (`polkit-kde-authentication-agent-1`) autostarts only in KDE
(`OnlyShowIn=KDE`, seen), so in Hyprland there is none unless Noctalia's is enabled. Noctalia 5.3 has a native agent
(links libpolkit-agent-1, read) controlled by `polkit_agent` in its settings, **default false** (Noctalia docs:
"register Noctalia's native polkit authentication agent"). The profile should set it to true; `checks()` reports when it
is off.

## What Plasma provides and who covers it in Hyprland

| Function | Plasma | Hyprland session |
| --- | --- | --- |
| Notifications | plasmashell | Noctalia (`[notification] enable_daemon`, claims `org.freedesktop.Notifications`) |
| System tray | plasmashell | Noctalia (StatusNotifier watcher) |
| Wi-Fi passwords | plasma-nm | Noctalia's NetworkManager secret agent (read in the binary) |
| Bluetooth pairing | bluedevil | Noctalia's BlueZ agent (read in the binary) |
| polkit | polkit-kde-agent | Noctalia, once `polkit_agent = true` |
| Wallet unlock | plasma-kwallet-pam.service | `/usr/lib/pam_kwallet_init` from the Hyprland autostart |
| Power profiles | PowerDevil + power-profiles-daemon | Noctalia + the same power-profiles-daemon 0.30 (system setting, shared) |
| Lid and idle | PowerDevil | logind defaults + Noctalia |
| Removable drives | KDE's automounter (kded) | none automatic: udisks2 2.11 is installed, Dolphin mounts on click. Noctalia leaves mounting to other programs (its README). An automounter such as udiskie is not installed and not added |
| Application menu for KDE programs | `XDG_MENU_PREFIX=plasma-` | same line in Corsu's block |
| KDE Connect | XDG autostart | same (its entry has no `OnlyShowIn`) |

## Noctalia's menu entry

`dev.noctalia.Noctalia.desktop` (Exec `noctalia --daemon`, category Settings) appears in Plasma's menu; started from
there it would put a second shell over Plasma. Corsu adds a user copy built from the system entry by
`hyprland_only_entry()`, with `OnlyShowIn=Hyprland;` (any `OnlyShowIn`/`NotShowIn` of the original dropped). It is
generated rather than kept as a template so the command follows the package. For that reason `src/hyprland/session/`
holds no template: the env block, the portal file and this entry are all generated from the machine.

## Rollback

What enabling adds (component side, tracked in Corsu's state):

| File | Added content | Undo |
| --- | --- | --- |
| `~/.config/uwsm/env-hyprland` | the block between `# corsu:begin` and `# corsu:end` | `remove_block()`; delete the file only if Corsu created it and it is now empty |
| `~/.config/xdg-desktop-portal/hyprland-portals.conf` | whole file | delete if unchanged since; the packaged `hyprland-portals.conf` applies again |
| `~/.local/share/applications/dev.noctalia.Noctalia.desktop` | Hyprland-only copy | delete if unchanged since; the system entry applies again |
| `~/.config/hypr/…`, Noctalia files | profile and translation | see `src/hyprland/README.md` |

By hand: delete the lines between the markers and the two other files, then log out. Nothing outside the home folder
is written; Plasma's files (`kde-portals.conf`, `plasma-workspace/env/corsu.sh`, `kdeglobals`, `kcminputrc`) are
only read. Removing Hyprland itself is the person's package manager's job (`pacman -Rns` of the packages they
installed); in SDDM, choose "Plasma" again once.

No step needs root.

## Sources

- Hyprland wiki (git version of 22 October 2026, commit c66e8de):
  https://wiki.hypr.land/configuring/core/environment-variables/,
  https://wiki.hypr.land/configuring/extra/multi-gpu/, https://wiki.hypr.land/useful-utilities/uwsm/,
  https://wiki.hypr.land/useful-utilities/screen-sharing/,
  https://wiki.hypr.land/hypr-ecosystem/user/xdg-desktop-portal-hyprland/
- aquamarine 0.15.1: https://github.com/hyprwm/aquamarine/blob/v0.15.1/docs/env.md and `src/backend/drm/DRM.cpp`
  (device order; built-in panel priority since commit a3dda0d, aquamarine 0.8.0)
- uwsm 0.27.1 README: https://github.com/Vladimir-csp/uwsm/blob/v0.27.1/README.md
- portals.conf(5), xdg-desktop-portal 1.22: https://flatpak.github.io/xdg-desktop-portal/docs/portals.conf.html
  (and `man portals.conf` installed)
- NVIDIA 615.78.08 README: https://download.nvidia.com/XFree86/Linux-x86_64/615.78.08/README/primerenderoffload.html,
  .../README/gbm.html, .../README/dynamicpowermanagement.html, .../README/wayland-issues.html
- Noctalia 5 docs: https://docs.noctalia.dev/noctalia/configuration/shell/ (polkit_agent, lock_before_suspend),
  https://docs.noctalia.dev/noctalia/services/notifications/,
  https://docs.noctalia.dev/noctalia/compositor-settings/hyprland/; package README (`/usr/share/doc/noctalia/README.md`)
- Package files of hyprland 0.56.2-4.1, xdg-desktop-portal-hyprland 1.4.1-2.1, noctalia 5.3.0-1.1 (read, not run)
