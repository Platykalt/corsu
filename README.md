# Corsu

Corsu translates the menus and settings of Firefox, Chrome, Opera GX and Discord into Corsican. On Linux it
also translates the KDE Plasma desktop. It runs on Windows, macOS and Linux, and you can switch back to French
at any time.

[Version française](README.fr.md)

## Download

| | |
| --- | --- |
| Windows | [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip) |
| macOS | [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz) |
| Linux | [corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz) |

On Windows, extract the zip (right-click, Extract All), open the `corsu` folder and double-click `install.cmd`.
Windows may ask whether you really want to run a downloaded file. If Python is not installed, the script offers
to install it.

On macOS and Linux, extract the archive and run `./install.sh` from the `corsu` folder.

You can also do it in one line. In PowerShell on Windows:

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/get.ps1 | iex
```

In a terminal on macOS or Linux:

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/get.sh | sh
```

## Using it

The installer shows what it found on your computer and lets you choose:

```
Select what you want to translate:
  [x] 1. Firefox: menus, settings and error pages
  [x] 2. Chrome, Opera GX and other Chromium browsers
  [x] 3. Discord: interface through Vencord
Type numbers to toggle (e.g. "2 3"), Enter to continue, q to quit:
```

It then tells you what it is going to change and waits for a yes. Close the programs before you answer and open
them again afterwards.

The installer adds a shortcut called Corsu Setup. Open it later to add another program, to go back to French,
or to remove Corsu. It keeps a copy of every file it changes, so removing it puts your computer back as it was.

Firefox and Discord work on all three systems. Chrome, Opera GX, Edge, Brave and Vivaldi work on Windows and
Linux; macOS support for them is not done yet. [docs/components.md](docs/components.md) explains what Corsu
changes for each program.

Only the program itself is translated, never websites or messages. Text that has no Corsican translation yet
stays in French.

## Translations

Corsu has about 60,000 translated phrases. About 13,000 of them come from other free software, most of them
translated by Patriccollu di Santa Maria è Sichè: Firefox for Android and iOS, Thunderbird, VLC, Audacity,
Notepad++ and others. The rest were written for Corsu and follow his vocabulary. They have not all been checked
by a Corsican speaker yet.

If you see a wrong or clumsy translation, please [open an issue](https://github.com/Platykalt/corsu/issues/new?template=translation.yml)
with the text and where you saw it. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to correct the files
directly.

## Phones

Apple, Google and Samsung decide which languages their phones offer, and Corsican is not one of them yet. Some
apps are already in Corsican though, Firefox among them. [docs/phones.md](docs/phones.md) explains how to use
them.

## Other documents

[docs/development.md](docs/development.md) describes the code, the tests and how a release is made.
[CHANGELOG.md](CHANGELOG.md) lists the changes in each version.

Corsu is free software, released under the [GNU GPL](LICENSE), version 3 or later. Translations taken from other
projects keep their own license, given at the top of each file in [lexicon/](lexicon/).
