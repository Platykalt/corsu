#!/bin/sh
# Install Corsu on Linux: run ./"Install for Linux.sh" from this folder. Uses Python 3.10 or newer when the system
# has it (its GTK bindings give Corsu its window), otherwise the Python bundled in release archives.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# At the top of a release archive, or in the install/ folder of the source code.
if [ -d "$here/src" ]; then corsu_dir=$here; else corsu_dir=$(dirname -- "$here"); fi
bundled="$corsu_dir/runtime/$(uname -m)/python/bin/python3"
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    python=python3
elif [ -x "$bundled" ]; then
    python=$bundled
else
    echo 'Corsu needs Python 3.10 or newer. Install it with your distribution package manager.' >&2
    exit 1
fi
# Without options, in a graphical session, open the Corsu app; --text keeps everything in the terminal.
if [ $# -eq 0 ] && { [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; }; then
    exec "$python" "$corsu_dir/src/app.py"
fi
[ "${1:-}" = --text ] && shift
exec "$python" "$corsu_dir/src/installer.py" "$@"
