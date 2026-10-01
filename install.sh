#!/bin/sh
# Corsu installer for Linux and macOS. Requires Python 3.10 or newer.
set -eu
corsu_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo 'Python 3.10 or newer is required. Install it with your package manager (macOS: xcode-select --install).' >&2
    exit 1
fi
exec python3 "$corsu_dir/src/installer.py" "$@"
