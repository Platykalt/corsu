#!/bin/sh
# Install Corsu on macOS: double-click this file. Release archives bring their own Python, with what Corsu's window
# needs; from the source code, Python 3.10 or newer is required.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# At the top of a release archive, or in the install/ folder of the source code.
if [ -d "$here/src" ]; then corsu_dir=$here; else corsu_dir=$(dirname -- "$here"); fi
case "$(uname -m)" in arm64) processor=aarch64 ;; *) processor=x86_64 ;; esac
bundled="$corsu_dir/runtime/$processor/python/bin/python3"
if [ -x "$bundled" ]; then
    # Files from a downloaded archive are quarantined; this one was opened on purpose, so its Python may run.
    xattr -dr com.apple.quarantine "$corsu_dir/runtime" 2>/dev/null || true
    python=$bundled
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    python=python3
else
    echo 'Corsu needs Python 3.10 or newer. Get it from https://www.python.org/downloads/macos/ and open this file again.' >&2
    exit 1
fi
# Without options, open the Corsu app; --text keeps everything in the terminal.
if [ $# -eq 0 ]; then
    exec "$python" "$corsu_dir/src/app.py"
fi
[ "${1:-}" = --text ] && shift
exec "$python" "$corsu_dir/src/installer.py" "$@"
