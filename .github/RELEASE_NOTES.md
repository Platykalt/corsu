| System | Download | Then |
| --- | --- | --- |
| Windows 10 or 11 | `corsu-windows.zip` | extract it and double-click `Install for Windows.cmd` |
| macOS | `corsu-macos.tar.gz` | double-click `Install for macOS.command` |
| Linux | `corsu-linux.tar.gz` | run `./"Install for Linux.sh"` |

The [installation guides](https://github.com/Platykalt/corsu/tree/main/docs) explain each step and the warnings
Windows and macOS show for downloaded scripts.

To install in one line: `irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex` in
PowerShell on Windows, or `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh` in
Terminal on macOS and Linux.

Each file has a `.sha256` checksum next to it. Corsu needs Python 3.10 or newer; on Windows the installer offers to
install it. Every archive was installed and tested on its own system before this release was published.

[CHANGELOG.md](https://github.com/Platykalt/corsu/blob/main/CHANGELOG.md) lists what changed.
