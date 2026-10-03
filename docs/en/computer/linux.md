# Installing Corsu on Linux

[Français](../../fr/ordinateur/linux.md)

The quickest way is one line in a terminal:

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

It downloads the latest release, checks its SHA-256 checksum and starts the installer. To do it by hand, download
[corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz), extract it and run `./"Install for Linux.sh"` from the `corsu` folder.

The Corsu app opens in its own window. The programs found are all ticked: untick what you do not want, click
Continue, read what Corsu will change, then click Install. Without a graphical session, or with `--text`, everything
happens in the terminal: Enter installs everything ticked, and a number ticks or unticks one item. Some steps ask for your password: translating a browser installed by your distribution,
and the system translations used by GTK programs and terminal commands.

Corsu uses the distribution's Python 3.10 or newer, which current distributions include: with WebKitGTK it gives
Corsu its window. Without it, the archive (x86_64 processors) carries its own Python; Corsu then opens in Chrome,
Chromium or the browser.

## Differences between distributions

- Arch, CachyOS, Manjaro, Fedora, openSUSE, Debian: the Firefox package from the distribution works.
- Ubuntu installs Firefox as a Snap, which cannot be translated. Install Mozilla's Firefox instead, from
  [Mozilla's APT repository](https://support.mozilla.org/kb/install-firefox-linux) or the tarball from mozilla.org.
- Flatpak versions of Firefox, Chrome or Discord are sealed and cannot be translated.
- The desktop translation needs KDE Plasma and its French translations. On GNOME and other desktops, Corsu
  translates the browsers and Discord, and the system translations still cover GTK programs and terminal commands.

Close the programs before confirming and open them again afterwards. Log out and back in to see Plasma in Corsican.
For Discord, see [Discord](../discord.md).

## Changing your mind

Open the Corsu app from the application menu to add a program, pause the terminal for an hour, switch a part off, or
remove Corsu. From a terminal: `python3 src/installer.py --disable terminal --hours 1`, `--enable terminal`,
`--uninstall`.
