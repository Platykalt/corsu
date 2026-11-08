# Discord start: alerts and rescue mode

[Français](../fr/discord-demarrage.md)

Discord's translation goes through Vencord. When Discord changes the way it loads, Vencord can stop working and
Discord stay stuck on "Starting" (this happened with Corsu 0.28.3 and Discord 1.0.168). Corsu therefore watches
Discord's starts and offers ways out. This page says what is watched, what the buttons do, and how to undo it all by
hand.

## What raises an alert

Corsu reads Discord's log (`logs/renderer_js.log` in Discord's folder), never Discord itself, and classifies the last
start:

| What Corsu saw | What it says |
|---|---|
| An error mentioning Vencord before Discord showed up | *probably* an incompatibility with the translation |
| Another error before Discord showed up | a problem at start, cause not determined |
| Nothing decisive after a few minutes, Discord still open | slow start, cause unknown |
| Discord's connection or update failing | network or Discord's servers; the translation is probably not the cause |
| The window opened outside the screen (Linux Hyprland only) | window off screen |

Corsu never states a cause as certain: a log shows what happened, not always why.

## Which starts are watched

- **Linux**: when Discord is opened from its menu entry or started with the session, Corsu starts it and then watches
  it for a few minutes; a notification appears if there is a problem (unless Do Not Disturb is on: the system
  decides).
- **Windows and macOS**: Discord rewrites its own shortcuts at each update, so Corsu does not replace them. The
  problem is found afterwards, when Corsu's window opens.
- **Not covered**: Discord restarted by its own updater (the next start is watched), Discord started from a terminal
  or another launcher.

To stop the watch on Linux (Discord gets its own menu entry back): `installer.py --discord-watch off`;
`--discord-watch on` turns it back on. The choice is kept across updates.

Without a notification service nothing pops up: the incident stays recorded and Corsu's window shows it (Discord row
on the home page). One notification per incident.

## The "Discord" page of Corsu's window

It opens from the notification's button or from the Discord row on the home page.

- **Look for an update**: the same check as the About page. The page says what is true: update available, Corsu up
  to date, check impossible, update installed but Discord still open with the old version, or development copy. An
  update is never presented as the fix: its release notes say what it fixes.
- **Start without the translation**: puts Discord in *rescue mode*. Corsu puts back Discord's original archive (kept
  at installation and checked); Discord then starts in French or English. Discord must be closed: Corsu never closes
  Discord for you. While rescue mode is on, Corsu's updates and repairs do not put the translation back by themselves.
- **Put the translation back** (in rescue mode): reinstalls the translation, then watches the next start; if it fails
  again, Discord returns to rescue mode.
- **Try again**: starts Discord again, watched (only when Discord is closed).
- **Show the diagnostic**: the observed state, the Discord, Corsu and Vencord versions, and the log lines that
  decided (personal data removed).
- **Later**: the incident stays recorded but no longer asks for your attention.

## Limits

- The watch reads a log: if Discord changes its messages, a start can be classified "slow" instead of "error".
- Without signing in to an account, a successful start is Discord's sign-in page.
- Rescue mode only applies to the Discord installation Corsu changed itself, with a checked original copy. Otherwise
  the button says why, and the manual procedure below still works.

## Manual procedure

If Corsu's window does not open or the button refuses, you can put the original Discord back yourself. The official
Vencord installer put Discord's original archive next to its own, named `_app.asar`.

1. Quit Discord completely (also from its icon in the notification area).
2. Copy `_app.asar` over `app.asar`, in Discord's `resources` folder. Keep `_app.asar`.
   - **Linux**: in Discord's application folder, for example `~/.config/discord/app-1.0.168/resources/` (recent
     distribution Discord; take the highest number) or `/opt/discord/resources/`:
     `cp ~/.config/discord/app-1.0.168/resources/_app.asar ~/.config/discord/app-1.0.168/resources/app.asar`
   - **Windows**: `%LOCALAPPDATA%\Discord\app-<highest version>\resources\`. In PowerShell:
     `Copy-Item "$env:LOCALAPPDATA\Discord\app-1.0.9999\resources\_app.asar" "$env:LOCALAPPDATA\Discord\app-1.0.9999\resources\app.asar"`
     (replace `1.0.9999` with your version).
   - **macOS**: `/Applications/Discord.app/Contents/Resources/`:
     `cp /Applications/Discord.app/Contents/Resources/_app.asar /Applications/Discord.app/Contents/Resources/app.asar`
3. Open Discord again: it starts without the translation.

To put the translation back later, open Corsu's window again (or rerun the installer with Discord ticked) once a
compatible version is available. If `_app.asar` is missing or very small (a few hundred bytes), it is not the
original archive: reinstall Discord.
