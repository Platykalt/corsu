Download the file for your system, extract it, and start the installer:

| System | File | Then |
| --- | --- | --- |
| Windows 10 or 11 | `corsu-windows.zip` | double-click `install.cmd` |
| macOS | `corsu-macos.tar.gz` | run `./install.sh` in Terminal |
| Linux | `corsu-linux.tar.gz` | run `./install.sh` |

Or install in one line: `irm https://raw.githubusercontent.com/Platykalt/corsu/main/get.ps1 | iex` on Windows
(PowerShell), `curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/get.sh | sh` on macOS and Linux.

Each file has a `.sha256` checksum next to it. Python 3.10 or newer is required; on Windows `install.cmd` offers to
install it. Every archive here was installed and tested on its own system before this release was published.

See [CHANGELOG.md](https://github.com/Platykalt/corsu/blob/main/CHANGELOG.md) for what changed.
