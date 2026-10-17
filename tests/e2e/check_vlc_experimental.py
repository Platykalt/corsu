#!/usr/bin/env python3
"""Real VLC shows the texts of an experimental Corsican catalogue (contrib/vlc) in Corsican.

Usage: check_vlc_experimental.py --mo EXPERIMENTAL.mo [--upstream UPSTREAM.mo] [--vlc vlc] [--min 20]
                                 [--mode datapath|bwrap|installed] [--probe MSGID ...] [--locale fr_FR.UTF-8]

  python3 tools/vlcpo.py build /tmp/exp.mo                     # reviewed drafts (default statuses)
  python3 tools/vlcpo.py build /tmp/up.mo --include=none       # upstream only
  python3 tests/e2e/check_vlc_experimental.py --mo /tmp/exp.mo --upstream /tmp/up.mo

VLC 3.0.x binds its text domain to config_GetDataDir() + "/../locale" (src/modules/textdomain.c); on Linux,
config_GetDataDir() is $VLC_DATA_PATH when set, else <prefix>/share/vlc found from libvlccore's own path
(src/linux/dirs.c), so /usr/share/locale for distribution packages. The catalogue is put in front of VLC without
touching any system file:
  --mode datapath   (default) a throwaway tree <tmp>/share/vlc (one link per entry of the system data folder, Lua
                    scripts included) and <tmp>/share/locale (the .mo as co, links to the system vlc.mo of every other
                    language for the fallbacks), and VLC started with VLC_DATA_PATH=<tmp>/share/vlc. No privileges.
  --mode bwrap      VLC started by bubblewrap with the .mo bind-mounted read-only over
                    /usr/share/locale/co/LC_MESSAGES/vlc.mo (needs bwrap, unprivileged user namespaces, and that file
                    to exist: Debian/Ubuntu ship it in vlc-l10n).
  --mode installed  the catalogue is already where VLC reads it (a throwaway machine or container); only checked.
VLC runs with a throwaway HOME: nothing of the account's own VLC settings is read or written.

The probe texts are chosen at run time, so the check does not depend on which drafts end up reviewed: every message
of the experimental .mo that the upstream .mo does not translate (all of them without --upstream), that is not
translated as itself, and whose English text VLC prints in its full help (vlc -I dummy -H, with LANGUAGE=C). --probe
gives the list instead. PASS needs at least --min of them printed in Corsican with LANGUAGE=co; with --upstream, the
same check runs with the upstream catalogue, where those texts must stay English (the control).
Stdlib only. Exit 1 on any FAIL.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

TARGET = '/usr/share/locale/co/LC_MESSAGES/vlc.mo'
failures = []


def check(condition, message):
    print(('PASS ' if condition else 'FAIL ') + message)
    if not condition:
        failures.append(message)
    return condition


def read_mo(path):
    """{msgid: msgstr} as text, for plain messages (no context, no plural)."""
    data = Path(path).read_bytes()
    order = {b'\xde\x12\x04\x95': '<', b'\x95\x04\x12\xde': '>'}.get(data[:4])
    if not order:
        raise SystemExit(f'{path}: not a gettext .mo catalogue')
    _, _, count, ids, values = struct.unpack(order + '5I', data[:20])
    entries = {}
    for index in range(count):
        key_length, key_offset = struct.unpack(order + '2I', data[ids + 8 * index:ids + 8 * index + 8])
        value_length, value_offset = struct.unpack(order + '2I', data[values + 8 * index:values + 8 * index + 8])
        key = data[key_offset:key_offset + key_length]
        if key and b'\x00' not in key and b'\x04' not in key:
            entries[key.decode('utf-8')] = data[value_offset:value_offset + value_length].decode('utf-8')
    return entries


def flat(text):
    """Whitespace collapsed: VLC wraps its help text to the terminal width."""
    return re.sub(r'\s+', ' ', text).strip()


WORK = Path(tempfile.mkdtemp(prefix='corsu-vlc-exp-'))


def data_tree(mo, system_data):
    """<WORK>/<n>/share/vlc and share/locale as described above; returns the VLC_DATA_PATH value."""
    base = WORK / str(len(list(WORK.iterdir()))) / 'share'
    data, locale = base / 'vlc', base / 'locale'
    data.mkdir(parents=True)
    for entry in Path(system_data).iterdir():
        (data / entry.name).symlink_to(entry)
    for catalogue in (Path(system_data).parent / 'locale').glob('*/LC_MESSAGES/vlc.mo'):
        language = catalogue.parent.parent.name
        if language != 'co':
            (locale / language / 'LC_MESSAGES').mkdir(parents=True)
            (locale / language / 'LC_MESSAGES/vlc.mo').symlink_to(catalogue)
    (locale / 'co/LC_MESSAGES').mkdir(parents=True)
    shutil.copyfile(mo, locale / 'co/LC_MESSAGES/vlc.mo')
    return str(data)


def run_help(arguments, mo, mode, language, locale):
    home = WORK / 'home'
    home.mkdir(exist_ok=True)
    environment = {**os.environ, 'LANG': locale, 'LC_ALL': '', 'LC_MESSAGES': '', 'LANGUAGE': language,
                   'COLUMNS': '200', 'HOME': str(home), 'XDG_CONFIG_HOME': str(home / '.config'),
                   'XDG_DATA_HOME': str(home / '.local/share'), 'XDG_CACHE_HOME': str(home / '.cache')}
    environment.pop('VLC_DATA_PATH', None)
    command = [arguments.vlc, '--no-plugins-cache', '-I', 'dummy', '-H']
    if mo and mode == 'datapath':
        environment['VLC_DATA_PATH'] = data_tree(mo, arguments.system_data)
    if mo and mode == 'bwrap':
        command = [arguments.bwrap, '--dev-bind', '/', '/', '--ro-bind', str(Path(mo).resolve()), TARGET, '--',
                   *command]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace',
                            env=environment, timeout=180)
    if result.returncode:
        print(result.stderr[-2000:])
    return result.returncode, result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--mo', required=True, help='experimental catalogue')
    parser.add_argument('--upstream', help='upstream-only catalogue (the control)')
    parser.add_argument('--vlc', default='vlc')
    parser.add_argument('--bwrap', default='bwrap')
    parser.add_argument('--mode', choices=('datapath', 'bwrap', 'installed'), default='datapath')
    parser.add_argument('--system-data', default='/usr/share/vlc', help="VLC's own data folder (datapath mode)")
    parser.add_argument('--min', type=int, default=20, help='probe texts that must be shown in Corsican')
    parser.add_argument('--probe', nargs='+', help='English messages to look for instead of choosing them')
    parser.add_argument('--locale', default='fr_FR.UTF-8', help='a UTF-8 locale other than C (gettext ignores '
                        'LANGUAGE under C)')
    arguments = parser.parse_args()

    version = subprocess.run([arguments.vlc, '--version'], capture_output=True, text=True).stdout.splitlines()
    print('VLC:', version[0] if version else '?')
    if arguments.mode == 'datapath' and not check(Path(arguments.system_data).is_dir(),
                                                  f'VLC data folder {arguments.system_data} exists'):
        return 1
    if arguments.mode == 'bwrap':
        if not check(bool(shutil.which(arguments.bwrap)), f'bubblewrap found ({arguments.bwrap})'):
            return 1
        if not check(Path(TARGET).is_file(), f'{TARGET} exists (bwrap can only cover an existing file)'):
            return 1
    experimental = read_mo(arguments.mo)
    upstream = read_mo(arguments.upstream) if arguments.upstream else {}

    code, english = run_help(arguments, None, 'installed', 'C', arguments.locale)
    check(code == 0 and len(english) > 10000, f'English full help printed ({len(english)} characters)')
    english_flat = flat(english)
    if arguments.probe:
        probes = [(msgid, experimental.get(msgid)) for msgid in arguments.probe]
        missing = [msgid for msgid, value in probes if value is None]
        check(not missing, f'every --probe text is in {arguments.mo}' + (f'; missing: {missing[:5]}' if missing else ''))
        probes = [(msgid, value) for msgid, value in probes if value is not None]
    else:
        probes = [(msgid, value) for msgid, value in experimental.items()
                  if msgid not in upstream and value and flat(value) != flat(msgid) and len(flat(msgid)) >= 12]
    shown = [(msgid, value) for msgid, value in probes if flat(msgid) in english_flat]
    print(f'probe texts: {len(probes)} new in the experimental catalogue, {len(shown)} of them printed by this VLC')
    # A text whose Corsican is also part of a longer English line proves nothing: keep the distinctive ones.
    shown = [(msgid, value) for msgid, value in shown if flat(value) not in english_flat]
    if upstream:
        # Nor one that upstream already uses inside another translation (same Corsican, other English).
        upstream_text = '\n'.join(flat(value) for value in upstream.values())
        shown = [(msgid, value) for msgid, value in shown if flat(value) not in upstream_text]
    if not check(len(shown) >= arguments.min, f'at least {arguments.min} probe texts printed by this VLC '
                 f'({len(shown)})'):
        return 1

    code, corsican = run_help(arguments, arguments.mo, arguments.mode, 'co', arguments.locale)
    check(code == 0, 'VLC ran with the experimental catalogue and LANGUAGE=co')
    corsican_flat = flat(corsican)
    translated = [(msgid, value) for msgid, value in shown if flat(value) in corsican_flat]
    still_english = [msgid for msgid, value in shown if flat(value) not in corsican_flat]
    check(len(translated) >= arguments.min,
          f'{len(translated)}/{len(shown)} probe texts shown in Corsican (need {arguments.min})')
    for msgid, value in translated[:8]:
        print(f'  {flat(msgid)[:70]!r} -> {flat(value)[:70]!r}')
    if still_english:
        print(f'  not shown in Corsican ({len(still_english)}), e.g. {[flat(m)[:60] for m in still_english[:5]]}')

    if arguments.upstream:
        code, control = run_help(arguments, arguments.upstream, arguments.mode, 'co', arguments.locale)
        control_flat = flat(control)
        check(code == 0, 'VLC ran with the upstream catalogue and LANGUAGE=co')
        english_there = [msgid for msgid, _ in translated if flat(msgid) in control_flat]
        corsican_there = [msgid for msgid, value in translated if flat(value) in control_flat]
        # English may be hidden where the same words sit inside a longer message upstream translates: 95 % is enough.
        check(len(english_there) >= 0.95 * len(translated) and not corsican_there,
              f'control: with the upstream catalogue those texts stay English ({len(english_there)}/{len(translated)}'
              f' English, {len(corsican_there)} Corsican)')
        known = [value for msgid, value in upstream.items() if len(flat(value)) > 20 and flat(msgid) in english_flat]
        upstream_shown = sum(flat(value) in control_flat for value in known)
        check(upstream_shown > 0, f'control: upstream Corsican is shown ({upstream_shown}/{len(known)} upstream '
              'texts of the help), so the catalogue was really loaded')
    print('FAIL' if failures else 'PASS', 'VLC experimental catalogue')
    return 1 if failures else 0


if __name__ == '__main__':
    try:
        code = main()
    finally:
        shutil.rmtree(WORK, ignore_errors=True)
    sys.exit(code)
