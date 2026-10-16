"""Real VLC on Linux (CI): Corsu switches its menu entry to Corsican, and VLC then speaks Corsican.

Run after `apt-get install vlc-bin vlc-plugin-base vlc-l10n`. Uses a throwaway HOME, so nothing of the machine's own
settings is touched. Checks: the Corsican catalogue exists and how much it covers; Corsu writes the menu entry; the
command in that entry, run as the menu would run it, prints VLC's help in Corsican; switching off removes the entry.
"""
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    home = Path(tempfile.mkdtemp(prefix='corsu-vlc-'))
    os.environ.update(HOME=str(home), LANG='fr_FR.UTF-8', LANGUAGE='', LC_ALL='', LC_MESSAGES='', CORSU_USER_LEXICON=os.devnull)
    import corsu
    corsu.HOME, corsu.DATA, corsu.STATE = home, home / 'data', home / 'data/state.json'
    import apps
    from apps import vlc
    import engine
    [installation] = [item for item in vlc.VLC().find() if 'Flatpak' not in item.kind]
    print('found:', installation.describe(), 'catalog:', installation.catalog, 'reason:', installation.reason)
    assert installation.usable, installation.reason
    corsican = engine.read_mo(installation.catalog.read_bytes())
    corsu.install(['vlc'])
    entry = home / '.local/share/applications/vlc.desktop'
    exec_line = next(line for line in entry.read_text().splitlines() if line.startswith('Exec='))
    print(exec_line)
    command = [part for part in shlex.split(exec_line[5:]) if not part.startswith('%')]
    command = command[:command.index('env') + 2] + ['vlc', '-I', 'dummy', '--help'] if command[0] == 'env' else command
    output = subprocess.run(command, capture_output=True, text=True, timeout=60).stdout
    english = subprocess.run(['env', 'LANGUAGE=C', 'vlc', '-I', 'dummy', '--help'], capture_output=True, text=True,
                             timeout=60).stdout
    shown = [value.decode('utf-8', 'replace') for key, value in corsican.items()
             if key and len(value) > 12 and value.decode('utf-8', 'replace') in output]
    print(f'VLC help lines shown in Corsican: {len(shown)}; e.g. {shown[:3]}')
    assert output != english and shown, 'VLC did not show Corsican text'
    corsu.disable(['vlc'])
    assert not entry.exists(), 'the menu entry is still there after switching off'
    corsu.uninstall()
    print('VLC: switched to Corsican, shown in Corsican, switched back')


if __name__ == '__main__':
    main()
