# Installing Corsu on macOS

[Français](../../fr/ordinateur/macos.md)

The simplest way is to open Terminal (Applications, then Utilities) and paste:

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

It downloads the latest release, checks its SHA-256 checksum and opens the Corsu app. The
programs found are all ticked: untick what you do not want, click Continue, read what Corsu will change, then click
Install.

You can also download [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz), open the `corsu` folder and double-click
`Install for macOS.command`. macOS will probably refuse the first time because the file is not signed by a
registered developer: open System Settings, then Privacy & Security, click Open Anyway next to the message, and
open the file again.

There is nothing else to install: the archive carries its own Python, for Intel and Apple Silicon Macs alike. From
the source code, Python 3.10 or newer is needed, available from [python.org](https://www.python.org/downloads/macos/).

On macOS Corsu translates Firefox and Discord. Firefox in Corsican opens from the Firefox Corsu app in your
Applications folder. Chrome, Opera GX and the other Chromium browsers are not supported on macOS: changing their
files breaks their signature and their access to saved passwords. For Discord, see [Discord](../discord.md).

## Changing your mind

Open the Corsu app from the Applications folder to add a program, switch a part off, or remove Corsu.
