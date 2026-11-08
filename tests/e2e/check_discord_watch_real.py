#!/usr/bin/env python3
"""Run the Discord start watch (src/discord_watch.py) against a COPY of the real Discord client, isolated in a
headless weston, and check the state it decides from Discord's own log only (no debugging port).

Usage: check_discord_watch_real.py CLIENT --expect STATE[,STATE…] [--vencord DIST] [--settings SETTINGS_JSON]
                                   [--offline] [--work DIR] [--window S] [--no-sandbox]
  CLIENT   a Linux Discord app folder, e.g. ~/.config/discord/app-1.0.168 (only read: copied into DIR).
  DIST     a Vencord dist/ folder: the copy then starts through the official installer's launcher, as installed.
  --offline  every connection goes to a closed local proxy (127.0.0.1:9): Discord cannot reach its servers.
Examples: Vencord 1.15.9 with Discord 1.0.168 → --expect vencord-error; Corsu 0.28.4's build → --expect ok,ok-corsu;
--offline → --expect network,slow (never vencord-error).

Pieces come from check_discord_real_start.py (copy, launcher asar, isolation). Corsu's own data goes to DIR too:
run it with HOME=$(mktemp -d). Exit 0 when the decided state is one of the expected ones.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
from check_discord_real_start import PROTECTED, prepare  # noqa: E402
import corsu  # noqa: E402
import discord_watch  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('client', nargs='?', type=Path)
    parser.add_argument('--expect', required=True)
    parser.add_argument('--vencord', type=Path)
    parser.add_argument('--settings', type=Path)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--work', type=Path)
    parser.add_argument('--window', type=float, default=discord_watch.WINDOW)
    parser.add_argument('--no-sandbox', action='store_true')
    args = parser.parse_args()
    if not args.client or not (args.client / 'Discord').is_file():
        print('SKIP: no real Discord client folder given')
        return 0
    if not shutil.which('weston'):
        print('SKIP: weston (headless compositor) not installed; refusing to open windows on the desktop')
        return 0
    work = (args.work or Path(tempfile.mkdtemp(prefix='discord-watch-real-'))).resolve()
    if any(work.is_relative_to(path.resolve()) for path in PROTECTED if path.exists()):
        raise SystemExit(f'Refusing to work inside a real installation: {work}')
    if work.exists() and any(work.iterdir()):
        raise SystemExit(f'Work folder not empty: {work}')
    work.mkdir(parents=True, exist_ok=True)
    # The watcher records its state in Corsu's data folder: here, never the person's.
    corsu.DATA = work / 'corsu-data'
    home, copy = prepare(args.client.resolve(), work, args.vencord and args.vencord.resolve(), args.settings)
    runtime = Path(tempfile.mkdtemp(prefix='cdw-', dir='/tmp' if Path('/tmp').is_dir() else None))
    environment = {'PATH': '/usr/bin:/bin', 'HOME': str(home), 'XDG_CONFIG_HOME': str(home / '.config'),
                   'XDG_RUNTIME_DIR': str(runtime), 'WAYLAND_DISPLAY': 'corsu-headless', 'LANG': 'fr_FR.UTF-8'}
    weston = subprocess.Popen(['weston', '--backend=headless', '--socket=corsu-headless', '--width=1280',
                               '--height=800', '--idle-time=0'], env=environment, start_new_session=True,
                              stdout=open(work / 'weston.log', 'wb'), stderr=subprocess.STDOUT)
    for _ in range(50):
        if (runtime / 'corsu-headless').exists():
            break
        time.sleep(0.1)
    else:
        weston.terminate()
        raise SystemExit(f'The headless compositor did not start; see {work}/weston.log')
    user_data = home / '.config/discord'
    log = user_data / 'logs/renderer_js.log'
    command = [str(copy / 'Discord'), '--ozone-platform=wayland', f'--user-data-dir={user_data}',
               *(['--no-sandbox'] if args.no_sandbox else []),
               *(['--proxy-server=http://127.0.0.1:9', '--proxy-bypass-list=<-loopback>'] if args.offline else [])]
    offset = discord_watch.size(log)
    started = time.time()
    discord = subprocess.Popen(command, cwd=work, env=environment, start_new_session=True,
                               stdout=open(work / 'stderr.log', 'wb'), stderr=subprocess.STDOUT)
    try:
        # The same watch as the desktop-entry wrapper; liveness is the started process (the person's own Discord
        # may be open on this machine, so "any Discord process" would always be true here).
        record = discord_watch.watch(discord_watch.LogFollower(log, offset), lambda: discord.poll() is None, started,
                                     'shortcut', copy, args.window, check_offscreen=lambda: None)
    finally:
        for process in (discord, weston):
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        shutil.rmtree(runtime, ignore_errors=True)
    expected = args.expect.split(',')
    (work / 'watch.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: record[key] for key in ('state', 'app_version', 'decided_at', 'started_at')}, indent=2))
    print(f'decided after {record["decided_at"] - started:.1f} s; evidence:')
    for item in record['evidence']:
        print(f'  {item["kind"]:9} {item["line"][:160]}')
    print(f'Logs: {log}, {work}/stderr.log, {work}/watch.json')
    passed = record['state'] in expected
    print('PASS' if passed else f'FAIL: state {record["state"]}, expected {" or ".join(expected)}')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
