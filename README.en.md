# Corsu

Corsu puts the menus and settings of Firefox, Chrome, Opera GX and Discord in Corsican, and on Linux also the KDE
Plasma desktop and terminal commands. It works on Windows, macOS and Linux, and each part can be switched off and
on again at any time.

[Français](README.md) · [Why Corsu](docs/en/why-corsu.md) · [What works where](docs/en/compatibility.md)

## Install on a computer

| System | Download | Then | Guide |
| --- | --- | --- | --- |
| Windows | [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip) | extract it, double-click `Install for Windows.cmd` | [Windows](docs/en/computer/windows.md) |
| macOS | [corsu-macos.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-macos.tar.gz) | double-click `Install for macOS.command` | [macOS](docs/en/computer/macos.md) |
| Linux | [corsu-linux.tar.gz](https://github.com/Platykalt/corsu/releases/latest/download/corsu-linux.tar.gz) | run `./"Install for Linux.sh"` | [Linux](docs/en/computer/linux.md) |

Or in one line. In PowerShell on Windows:

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
```

In Terminal on macOS or Linux:

```sh
curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
```

The installer shows what it found, with everything ticked: Enter installs it all. It says what it will change
before doing it, and keeps a copy of every file it changes. The Corsu Setup shortcut then lets you add a program,
pause a part, or remove everything.

For Discord, set its language to Français or English: see [Discord in Corsican](docs/en/discord.md).

## On a phone

Android and iOS menus cannot be translated by an outside project, but Firefox, Thunderbird, VLC and other apps
already come in Corsican, and Gboard has a Corsican keyboard. See [Android](docs/en/phone/android.md) and
[iPhone](docs/en/phone/iphone.md).

## Translations

Corsu has about 77,000 translated phrases. More than 13,000 come from other free software, most of them translated
by Patriccollu di Santa Maria è Sichè: Firefox for Android and iOS, Thunderbird, VLC, Audacity, Notepad++ and
others. The rest were written for Corsu with the same vocabulary.

Does a translation look wrong or clumsy? [Open an issue](https://github.com/Platykalt/corsu/issues/new?template=translation.yml)
with the text and where you saw it, or correct the line yourself: see [CONTRIBUTING.md](CONTRIBUTING.md).

To practise Corsican with someone, or on your own: [Sapienzia](https://www.sapienzia.io),
[Astutu](https://astutu.corsica), [LIV](https://liv.corsica).

## More

- [Why Corsu](docs/en/why-corsu.md)
- [What Corsu changes](docs/en/what-corsu-changes.md)
- [What works where](docs/en/compatibility.md)
- [Development](docs/en/developers.md) and [CHANGELOG.md](CHANGELOG.md)

Corsu is free software, released under the [GNU GPL](LICENSE), version 3 or later. Translations taken from other
projects keep their own license, given at the top of each file in [lexicon/](lexicon/).
