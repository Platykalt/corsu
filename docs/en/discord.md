# Discord in Corsican

[Français](../fr/discord.md)

Corsu translates Discord through Vencord, an open-source modification of the Discord app, with a small plugin
that replaces the interface text. Messages, server names and user names are never changed.

## Desktop app (Windows, macOS, Linux)

1. Install Corsu (or open the Corsu app again) and keep Discord ticked in the list. If Discord is open, Corsu patches it anyway;
   it takes effect the next time Discord starts.
2. Quit Discord completely (from the tray icon, not only the window) and open it again.
3. In Discord, open User Settings, then Language, and choose **Français** or **English**. The plugin translates from
   those two languages. Any other language, Portuguese for example, stays as it is.

To check that it works, open User Settings and scroll down the left column: Vencord's own section should be there,
and the Plugins page should list Corsu as enabled. The settings labels should now be in Corsican.

Vesktop, a Discord app that already includes Vencord, works the same way: tick Vesktop in the installer.

## Troubleshooting

- **Discord stuck on "Starting" or no longer starting.** See [Discord start: alerts and rescue mode](discord-start.md)
  ("Start without the translation" button, manual procedure).
- **Still in another language.** Discord's language setting wins: set it to Français or English. The Corsu plugin
  shows a reminder when Discord is in any other language.
- **No Vencord section in the settings.** Discord updated itself and removed the patch. Open the Corsu app again, or
  run the installer with only Discord ticked.
- **Linux, Discord installed by the distribution.** Recent packages keep the program in
  `~/.config/discord/app-<version>`. Corsu patches the newest one. After a Discord update, open the Corsu app again.
- **Flatpak Discord.** Not supported: use the regular package or Vesktop.
- **You already used Vencord.** Corsu replaces it with a Vencord build that includes the Corsu plugin. Your other
  Vencord plugins and settings are kept.

## If Discord no longer starts and Corsu cannot help

Corsu's help when Discord gets stuck (alert, "Start without the translation" button) is in Corsu's own window. It
does not help when that window does not open, or when Corsu itself is what broke. What it covers, precisely:

- **Linux**: a start from Discord's menu entry or at login is watched as it happens (a notification if it gets
  stuck). Other starts (terminal, another launcher, Discord restarting itself after an update) are only seen
  afterwards, by Corsu's window.
- **Windows and macOS**: no start is watched as it happens and no notification is sent when Discord starts. Corsu's
  window, while it is open, reads Discord's log every 30 seconds and shows the last start's problem. If you do not
  open Corsu's window, nothing tells you.
- Corsu's notifications follow the system's Do Not Disturb (Focus Assist, Focus): none is forced through.

These ways back do **not** need Corsu's window. Quit Discord completely first (also from its icon in the
notification area).

1. **Put Discord's original archive back** (Discord then starts without the translation, nothing else changes). In
   Discord's `resources` folder, the official Vencord installer kept the original as `_app.asar`: copy it over
   `app.asar` and keep `_app.asar`.
   - Windows (PowerShell; the last command opens the newest `app-<version>` folder):
     ```powershell
     $resources = (Get-ChildItem "$env:LOCALAPPDATA\Discord\app-*" | Sort-Object { [version]($_.Name -replace '^app-') } | Select-Object -Last 1).FullName + "\resources"
     Copy-Item "$resources\_app.asar" "$resources\app.asar"
     ```
     Discord PTB and Canary: `DiscordPTB` and `DiscordCanary` instead of `Discord`.
   - Linux: `cp ~/.config/discord/app-<version>/resources/_app.asar ~/.config/discord/app-<version>/resources/app.asar`
     (every `app-<version>` folder that has an `_app.asar`), or `/opt/discord/resources/`.
   - macOS: `cp /Applications/Discord.app/Contents/Resources/_app.asar /Applications/Discord.app/Contents/Resources/app.asar`
   - No `_app.asar`, or a very small one (a few hundred bytes)? Corsu kept its own copy of the original: in
     `installation.json` in Corsu's data folder (`%LOCALAPPDATA%\corsu` on Windows, `~/.local/share/corsu` on Linux,
     `~/Library/Application Support/corsu` on macOS), the entry of that `app.asar` names it under `"backup"` (a file in
     the `backups` folder next to it). Copy that file over `app.asar`.
2. **Or reinstall Discord** with Discord's own installer from discord.com (on Windows, uninstall Discord from Settings,
   Apps first). A fresh Discord has no Vencord. Your account, servers and messages are on Discord's servers; Discord
   keeps its local settings.
3. **Or remove Corsu's change to Discord from a terminal**, without the window, with the installer of a Corsu
   release archive (`installer.py --uninstall` removes everything Corsu changed, Discord included). Note:
   `installer.py --disable discord` only switches the Corsu plugin off; Vencord itself still loads, so it does not
   help when Vencord is what stops Discord.

Afterwards, an update or repair of Corsu with Discord ticked puts the translation back (a Discord put back by hand
counts as unchanged): untick Discord until a Corsu version says it fixes the problem, or, once Corsu's window opens,
use its rescue mode, which Corsu's updates leave alone. Details: [Discord start: alerts and rescue mode](discord-start.md).

## Web version (discord.com in a browser)

Not supported yet. The Corsu plugin is built into Corsu's copy of Vencord, which only runs in the desktop app.

## Phone apps

Not possible. Discord's phone apps cannot be modified, and Discord does not offer Corsican.
