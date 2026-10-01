# Discord in Corsican

[Français](../fr/discord.md)

Corsu translates Discord through Vencord, an open-source modification of the Discord app, with a small plugin
that replaces the interface text. Messages, server names and user names are never changed.

## Desktop app (Windows, macOS, Linux)

1. Run the Corsu installer and keep Discord ticked in the list. If Discord is open, the installer patches it anyway;
   it takes effect the next time Discord starts.
2. Quit Discord completely (from the tray icon, not only the window) and open it again.
3. In Discord, open User Settings, then Language, and choose **Français** or **English**. The plugin translates from
   those two languages. Any other language, Portuguese for example, stays as it is.

To check that it works, open User Settings and scroll down the left column: Vencord's own section should be there,
and the Plugins page should list Corsu as enabled. The settings labels should now be in Corsican.

Vesktop, a Discord app that already includes Vencord, works the same way: tick Vesktop in the installer.

## Troubleshooting

- **Still in another language.** Discord's language setting wins: set it to Français or English. The Corsu plugin
  shows a reminder when Discord is in any other language.
- **No Vencord section in the settings.** Discord updated itself and removed the patch. Open the Corsu app again, or
  run the installer with only Discord ticked.
- **Linux, Discord installed by the distribution.** Recent packages keep the program in
  `~/.config/discord/app-<version>`. Corsu patches the newest one. After a Discord update, open the Corsu app again.
- **Flatpak Discord.** Not supported: use the regular package or Vesktop.
- **You already used Vencord.** Corsu replaces it with a Vencord build that includes the Corsu plugin. Your other
  Vencord plugins and settings are kept.

## Web version (discord.com in a browser)

Not supported yet. The Corsu plugin is built into Corsu's copy of Vencord, which only runs in the desktop app.

## Phone apps

Not possible. Discord's phone apps cannot be modified, and Discord does not offer Corsican.
