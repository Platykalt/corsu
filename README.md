# Corsu

Corsu puts the interface of everyday software in Corsican: Firefox, Chrome and Opera GX, Discord, and the KDE
Plasma desktop. It works on Windows, macOS and Linux, and it can be switched off or removed at any time.

**Download:**
[Windows](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip) ·
[macOS](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz) ·
[Linux](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz)

[Lire en français](README.fr.md)

## Install on Windows

1. Download [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip).
2. Right-click the file, choose *Extract All*, then open the `corsu` folder.
3. Double-click `install.cmd`. Windows may ask you to confirm that you want to run a downloaded file.
4. Choose what to translate and accept the list of changes.

Corsu needs Python 3.10 or newer. If it is missing, `install.cmd` offers to install it for you with `winget`.

You can also install from PowerShell in one line:

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/get.ps1 | iex
```

## Install on macOS or Linux

Open a terminal and run:

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/get.sh | sh
```

This downloads the latest release, checks its SHA-256 checksum and starts the installer. If you prefer to do it
by hand, download the archive for your system, extract it and run `./install.sh` from the `corsu` folder.

## What the installer does

It looks for the programs on your computer and asks which ones to translate:

```
Select what you want to translate:
  [x] 1. Firefox: menus, settings and error pages
  [x] 2. Chrome, Opera GX and other Chromium browsers
  [x] 3. Discord: interface through Vencord
Type numbers to toggle (e.g. "2 3"), Enter to continue, q to quit:
```

Before changing anything it prints what it is about to do and waits for your answer. It then adds a
**Corsu Setup** shortcut (Start menu, application menu, or `~/Applications` on macOS). Open it later to add
programs, switch Corsican off, or uninstall. The downloaded archive can be deleted afterwards.

Close Firefox, Chrome and Discord before installing and reopen them afterwards. On Linux, log out and back in
for the Plasma desktop.

## What is translated

| Program | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Firefox | yes | yes | yes |
| Chrome, Opera, Opera GX, Edge, Brave, Vivaldi | yes | not yet | yes |
| Discord (with Vencord) and Vesktop | yes | yes | yes |
| KDE Plasma desktop and Qt applications | | | yes |

Only the interface is translated: menus, buttons, settings, error pages. Websites, messages and anything you
type stay as they are. Corsu works offline and never reads your messages, profiles or documents. A label that
has no Corsican translation yet stays in French.

[docs/components.md](docs/components.md) explains exactly what each part changes on your computer.

## The translations

Corsu's word list, the lexicon, has about 50,000 entries. More than 12,000 of them are reviewed translations,
most of them by Patriccollu di Santa Maria è Sichè for Firefox, Thunderbird, VLC, Audacity, Notepad++ and other
free software ([lexicon/](lexicon/)). The rest are drafts that follow the same vocabulary and still need checking
by Corsican speakers.

If you spot a mistake, open an issue or correct the line yourself: see [CONTRIBUTING.md](CONTRIBUTING.md).

## Phones

Apple, Google and Samsung do not let outside projects translate their systems, but several apps already speak
Corsican. [docs/phones.md](docs/phones.md) explains how to use them on an iPhone or an Android phone.

## Switch off or uninstall

Open **Corsu Setup**, or run one of these from the `corsu` folder (use `py -3` instead of `python3` on Windows):

```sh
python3 src/installer.py --disable     # back to French, keeps everything ready to switch on again
python3 src/installer.py --enable
python3 src/installer.py --uninstall   # restores the original files and settings
```

Corsu keeps a backup of every file it changes. Files you edit yourself afterwards are left alone.

## More

- [docs/components.md](docs/components.md): what each component changes, and where
- [docs/phones.md](docs/phones.md): Corsican on iPhone and Android
- [docs/development.md](docs/development.md): project layout, tests, building a release
- [CHANGELOG.md](CHANGELOG.md)

Corsu is free software under the [GNU GPL v3](LICENSE) or later. Translations taken from other projects keep
their original license, noted in each file of [lexicon/](lexicon/). Vencord and its installer keep their own
licenses.
