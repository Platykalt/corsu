#!/bin/sh
set -eu
corsu_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$corsu_dir/installer.py" "$@"
