**Français** · [English](#english)

| Système | Fichier | Ensuite |
| --- | --- | --- |
| Windows 10 ou 11 | `corsu-windows.zip` | décompresser, double-cliquer sur `Install for Windows.cmd` |
| macOS | `corsu-macos.tar.gz` | double-cliquer sur `Install for macOS.command` |
| Linux | `corsu-linux.tar.gz` | lancer `./"Install for Linux.sh"` |

En une ligne : `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex` dans PowerShell sous
Windows, ou `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh` dans le Terminal sous
macOS et Linux. Les [guides](https://github.com/Platykalt/corsu/tree/main/docs/fr) expliquent chaque étape.
L'application Corsu s'ouvre alors dans votre navigateur.

Chaque fichier a sa somme de contrôle `.sha256`. Corsu a besoin de Python 3.10 ou plus récent ; sous Windows,
l'installeur propose de l'installer. Chaque archive a été installée et testée sur son système avant la publication.

## English

| System | File | Then |
| --- | --- | --- |
| Windows 10 or 11 | `corsu-windows.zip` | extract it and double-click `Install for Windows.cmd` |
| macOS | `corsu-macos.tar.gz` | double-click `Install for macOS.command` |
| Linux | `corsu-linux.tar.gz` | run `./"Install for Linux.sh"` |

In one line: `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex` in PowerShell on
Windows, or `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh` in Terminal on
macOS and Linux. The [guides](https://github.com/Platykalt/corsu/tree/main/docs/en) explain each step.
The Corsu app then opens in your browser.

Each file has a `.sha256` checksum. Corsu needs Python 3.10 or newer; on Windows the installer offers to install
it. Every archive was installed and tested on its own system before this release was published.

[CHANGELOG.md](https://github.com/Platykalt/corsu/blob/main/CHANGELOG.md)
