#!/bin/sh
# Install Corsu on Linux: run ./"Install for Linux.sh" from this folder. Needs Python 3.10 or newer.
set -eu
corsu_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo 'Corsu needs Python 3.10 or newer. Install it with your distribution package manager.' >&2
    exit 1
fi
exec python3 "$corsu_dir/src/installer.py" "$@"
