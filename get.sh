#!/bin/sh
# Download the latest Corsu release for this computer, check its SHA-256 and start the installer.
#   curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/get.sh | sh
set -eu
case "$(uname -s)" in
    Linux) name=corsu-linux.tar.gz ;;
    Darwin) name=corsu-macos.tar.gz ;;
    *) echo "Corsu supports Linux, macOS and Windows. On Windows, use get.ps1." >&2; exit 1 ;;
esac
base=https://github.com/Platykalt/corsu/releases/latest/download
dir=$(mktemp -d "${TMPDIR:-/tmp}/corsu.XXXXXX")
echo "Downloading $name..."
curl -fsSL "$base/$name" -o "$dir/$name"
curl -fsSL "$base/$name.sha256" -o "$dir/$name.sha256"
if command -v sha256sum >/dev/null 2>&1; then
    (cd "$dir" && sha256sum -c "$name.sha256" >/dev/null)
else
    (cd "$dir" && shasum -a 256 -c "$name.sha256" >/dev/null)
fi
tar xzf "$dir/$name" -C "$dir"
# The installer asks questions: read the answers from the terminal, not from this piped script.
if (: </dev/tty) 2>/dev/null; then
    exec "$dir/corsu/install.sh" "$@" </dev/tty
fi
exec "$dir/corsu/install.sh" "$@"
