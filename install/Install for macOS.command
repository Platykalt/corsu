#!/bin/sh
# Install Corsu on macOS: double-click this file. Needs Python 3.10 or newer.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# At the top of a release archive, or in the install/ folder of the source code.
if [ -d "$here/src" ]; then corsu_dir=$here; else corsu_dir=$(dirname -- "$here"); fi
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo 'Corsu needs Python 3.10 or newer. Get it from https://www.python.org/downloads/macos/ and open this file again.' >&2
    exit 1
fi
# Without options, open the Corsu Setup window; --text keeps everything in the terminal.
if [ $# -eq 0 ]; then
    exec python3 "$corsu_dir/src/app.py"
fi
[ "${1:-}" = --text ] && shift
exec python3 "$corsu_dir/src/installer.py" "$@"
