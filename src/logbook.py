"""Corsu's log: everything the installer, the updater and the Corsu app print, plus the full details of any error.

The file is `logs/corsu.log` in Corsu's data folder (`%LOCALAPPDATA%\\corsu` on Windows,
`~/Library/Application Support/corsu` on macOS, `~/.local/share/corsu` on Linux). It is kept to a few
megabytes and never leaves the computer; people can attach it to a bug report.
"""
import datetime
import os
import platform
import sys
import traceback
from pathlib import Path

import corsu

LIMIT = 2_000_000


def path():
    return corsu.DATA / 'logs/corsu.log'


def _open():
    target = path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size > LIMIT:
            target.replace(target.with_suffix('.old.log'))
        return target.open('a', encoding='utf-8', errors='replace')
    except OSError:
        return None


def write(text):
    handle = _open()
    if handle is None:
        return
    with handle:
        stamp = datetime.datetime.now().isoformat(timespec='seconds')
        for line in str(text).splitlines() or ['']:
            handle.write(f'{stamp} {line}\n')


class Tee:
    """Copy a stream (stdout or stderr) into the log while it still prints as usual."""

    def __init__(self, stream):
        self.stream = stream
        self.pending = ''

    def write(self, text):
        if self.stream is not None:
            try:
                self.stream.write(text)
            except (OSError, ValueError):
                pass
        self.pending += text
        if '\n' in self.pending:
            lines, self.pending = self.pending.rsplit('\n', 1)
            write(lines)
        return len(text)

    def flush(self):
        if self.stream is not None:
            try:
                self.stream.flush()
            except (OSError, ValueError):
                pass

    def reconfigure(self, **options):
        if self.stream is not None and hasattr(self.stream, 'reconfigure'):
            self.stream.reconfigure(**options)

    def __getattr__(self, name):
        return getattr(self.stream, name)


def start(program):
    """Record a header for this run and copy all output into the log."""
    write(f'=== {program} {" ".join(sys.argv[1:])}')
    version = 'unknown'
    try:
        import json
        version = json.loads((corsu.SRC / 'release.json').read_text(encoding='utf-8'))['version']
    except (OSError, ValueError, KeyError):
        pass
    write(f'Corsu {version} · Python {platform.python_version()} · {platform.platform()} · {sys.executable}')
    sys.stdout = Tee(sys.stdout)
    sys.stderr = Tee(sys.stderr)


def failure(error):
    """Log the full traceback of an unexpected error; return the message to show."""
    write(''.join(traceback.format_exception(type(error), error, error.__traceback__)))
    return corsu.t(
        f'Corsu stopped because of an unexpected error: {error}\nThe details are in {path()}.\n'
        'Please attach that file to a bug report: https://github.com/Platykalt/corsu/issues/new?template=bug.yml',
        f'Corsu s\'est arrêté à cause d\'une erreur inattendue : {error}\nLes détails sont dans {path()}.\n'
        'Joignez ce fichier à un signalement : https://github.com/Platykalt/corsu/issues/new?template=bug.yml')


def open_folder():
    """Show the log folder in the file manager."""
    folder = path().parent
    folder.mkdir(parents=True, exist_ok=True)
    import subprocess
    if corsu.PLATFORM == 'windows':
        os.startfile(folder)  # noqa: S606 (opens the folder in Explorer)
    elif corsu.PLATFORM == 'macos':
        subprocess.Popen(['open', str(folder)])
    else:
        subprocess.Popen(['xdg-open', str(folder)])
    return str(folder)
