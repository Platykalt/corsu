#!/bin/sh
# Download the latest Corsu release for this computer, check its SHA-256 and start the installer.
# Running it again updates (or repairs) the installed Corsu: parts and choices are kept, parts switched off stay off.
#   curl -fsSL https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.sh | sh
set -eu
case "$(uname -s)" in
    Linux) name=corsu-linux.tar.gz; installer="Install for Linux.sh" ;;
    Darwin) name=corsu-macos.tar.gz; installer="Install for macOS.command" ;;
    *) echo "Corsu supports Linux, macOS and Windows. On Windows, use install/get.ps1." >&2; exit 1 ;;
esac
# CORSU_DOWNLOAD_BASE: a development override pointing at another folder of the same archives and .sha256 files
# (a test build, file:// works). SHA-256 only proves the download matches the .sha256 fetched from the SAME base,
# i.e. the transfer was not corrupted; it does not prove where the files come from. The authenticity of the
# official release rests on HTTPS to github.com, not on the checksum. A non-default base is announced below.
base=${CORSU_DOWNLOAD_BASE:-https://github.com/Platykalt/corsu/releases/latest/download}
if [ -n "${CORSU_DOWNLOAD_BASE:-}" ]; then
    echo "Corsu: downloading from CORSU_DOWNLOAD_BASE=$base, not the official releases (SHA-256 checks the transfer, not the source)." >&2
fi
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
    exec "$dir/corsu/$installer" "$@" </dev/tty
fi
exec "$dir/corsu/$installer" "$@"
