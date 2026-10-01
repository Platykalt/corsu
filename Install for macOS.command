#!/bin/sh
# Install Corsu on macOS: double-click this file. Needs Python 3.10 or newer.
set -eu
corsu_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo 'Corsu needs Python 3.10 or newer. Get it from https://www.python.org/downloads/macos/ and open this file again.' >&2
    exit 1
fi
exec python3 "$corsu_dir/src/installer.py" "$@"
