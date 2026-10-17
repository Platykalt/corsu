#!/usr/bin/env python3
"""Corsu switches VLC's experimental Corsican complement on and off, and real VLC started from the menu entry
Corsu writes shows the new texts in Corsican (Linux, system package of VLC 3.0.x).

Usage: check_vlc_complement.py [--vlc /usr/bin/vlc] [--locale fr_FR.UTF-8] [--min 20]
Uses the HOME and XDG folders of the environment, which must be throwaway ones. Runs this checkout's installer:
  --components vlc --vlc-complement on   the menu entry starts VLC with VLC_DATA_PATH; the help text VLC prints
                                         (-I dummy -H) shows at least --min texts of the complement in Corsican
  --vlc-complement off                   the variable and Corsu's VLC folder are gone (and the menu entry when
                                         VLC has no Corsican catalogue of its own); none of those texts in Corsican
  --uninstall                            the menu entry is gone
Stdlib only. Exit 1 on any FAIL.
"""
import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from apps import vlc_complement  # noqa: E402

failures = []


def check(condition, message):
    print(('PASS ' if condition else 'FAIL ') + message)
    if not condition:
        failures.append(message)
    return condition


def flat(text):
    return re.sub(r'\s+', ' ', text).strip()


def installer(*arguments):
    result = subprocess.run([sys.executable, str(ROOT / 'src/installer.py'), '--yes', *arguments],
                            capture_output=True, text=True, encoding='utf-8')
    print(result.stdout[-1500:])
    check(result.returncode == 0, f'installer {" ".join(arguments)} (exit {result.returncode})' +
          (f'\n{result.stderr[-2000:]}' if result.returncode else ''))


def entry():
    path = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share') / 'applications/vlc.desktop'
    if not path.exists():
        path = Path.home() / '.local/share/applications/vlc.desktop'
    return path


def main_exec():
    """(environment, command) of the main Exec line of Corsu's menu entry."""
    text = entry().read_text(encoding='utf-8')
    line = re.search(r'^Exec=(.*)$', text, re.M).group(1)
    words = shlex.split(line.replace('%%', '%'))
    environment = {}
    if words[0] == 'env':
        words.pop(0)
        while '=' in words[0]:
            name, _, value = words.pop(0).partition('=')
            environment[name] = value
    return environment, [word for word in words if not word.startswith('%')]


def run_help(vlc, locale, environment):
    variables = {name: value for name, value in os.environ.items() if name not in ('VLC_DATA_PATH', 'LANGUAGE')}
    variables.update(LANG=locale, LC_ALL='', LC_MESSAGES='', COLUMNS='200', **environment)
    result = subprocess.run([vlc, '--no-plugins-cache', '-I', 'dummy', '-H'], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', env=variables, timeout=180)
    return flat(result.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vlc', default='/usr/bin/vlc')
    parser.add_argument('--locale', default='fr_FR.UTF-8')
    parser.add_argument('--min', type=int, default=20)
    arguments = parser.parse_args()
    upstream, added = vlc_complement.entries()
    english = run_help(arguments.vlc, arguments.locale, {'LANGUAGE': 'C'})
    upstream_text = '\n'.join(flat(value) for value in upstream.values())
    probes = [(flat(key), flat(value)) for key, value in added.items()
              if '\x00' not in key and '\x04' not in key and len(flat(key)) >= 12 and flat(key) in english
              and flat(value) not in english and flat(value) not in upstream_text]
    if not check(len(probes) >= arguments.min, f'{len(probes)} complement texts printed by this VLC in English'):
        return 1

    installer('--components', 'vlc', '--vlc-complement', 'on')
    environment, command = main_exec()
    data = Path(environment.get('VLC_DATA_PATH', ''))
    check('VLC_DATA_PATH' in environment and (data / '../locale/co/LC_MESSAGES/vlc.mo').is_file(),
          f'the menu entry starts VLC with VLC_DATA_PATH={data}')
    check(environment.get('LANGUAGE', '').startswith('co'), f'and LANGUAGE={environment.get("LANGUAGE")}')
    corsican = run_help(command[0], arguments.locale, environment)
    shown = [key for key, value in probes if value in corsican]
    check(len(shown) >= arguments.min, f'{len(shown)}/{len(probes)} complement texts shown in Corsican '
          f'(need {arguments.min})')
    for key, value in probes[:5]:
        print(f'  {key[:60]!r} -> {value[:60]!r}')

    installer('--vlc-complement', 'off')
    if Path('/usr/share/locale/co/LC_MESSAGES/vlc.mo').exists():
        environment, command = main_exec()
        check('VLC_DATA_PATH' not in environment and environment.get('LANGUAGE', '').startswith('co'),
              'complement off: the menu entry keeps Corsican first, without VLC_DATA_PATH')
    else:
        check(not entry().exists(), 'complement off, and this VLC has no Corsican of its own: no menu entry')
        environment, command = {'LANGUAGE': 'co'}, [arguments.vlc]
    check(not data.parent.parent.exists(), f'complement off: {data.parent.parent} removed')
    upstream_run = run_help(command[0], arguments.locale, environment)
    still = [key for key, value in probes if value in upstream_run]
    # VLC's own catalogue then: English, or French where LANGUAGE=co:fr falls back to it.
    check(not still, f'complement off: none of those texts is shown in Corsican ({len(still)})')

    installer('--uninstall')
    check(not entry().exists(), 'uninstalled: the menu entry is gone')
    print('FAIL' if failures else 'PASS', 'VLC complement through Corsu')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
