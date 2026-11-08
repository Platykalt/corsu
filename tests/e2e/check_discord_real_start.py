#!/usr/bin/env python3
"""Start a COPY of the real Discord desktop client, isolated, and decide through DevTools whether it gets past the
splash ("Starting") to a usable web UI, with or without a Vencord build.

Usage: check_discord_real_start.py CLIENT [--vencord DIST] [--settings SETTINGS_JSON] [--work DIR] [--timeout S]
  CLIENT    a Linux Discord app folder (holding Discord and resources/app.asar), e.g. ~/.config/discord/app-1.0.168.
            Only read: it is copied into DIR. Skipped (exit 0) when not given or missing.
  DIST      a Vencord dist/ folder (copied); the copy's app.asar becomes the official installer's launcher requiring
            DIST/patcher.js, _app.asar the original archive. Without it, Discord runs unmodified.
  SETTINGS  Vencord settings.json for the isolated profile, e.g. {"plugins": {"Corsu": {"enabled": true}}}.

The client runs with its own HOME, XDG_CONFIG_HOME, --user-data-dir and XDG_RUNTIME_DIR, inside a headless weston
compositor (nothing appears on screen), with host updates skipped. It never touches the person's Discord, Vencord
or Corsu folders and only stops the processes it started.
Without an account the expected usable state is the LOGIN page (#app-mount drawn, login form); the gateway and
logged-in UI are not reached. Writes stderr.log, console.jsonl and result.json in DIR; exit 1 when the UI was not
reached, or Vencord/the Corsu plugin did not start when expected.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_chromium import DevTools  # noqa: E402

PROTECTED = [Path.home() / name for name in ('.config/discord', '.config/Vencord', '.local/share/corsu')]

PROBE = r'''(() => {
  const mount = document.querySelector('#app-mount');
  const V = window.Vencord;
  const corsu = V && V.Plugins && V.Plugins.plugins && V.Plugins.plugins.Corsu;
  const env = window.GLOBAL_ENV || {};
  return {
    url: location.href, title: document.title,
    mountChildren: mount ? mount.childElementCount : -1,
    mountText: mount ? mount.innerText.slice(0, 160) : '',
    login: !!document.querySelector('input[name="email"], input[name="password"], [class*="qrLogin"], [class*="authBox"]'),
    app: !!document.querySelector('nav[aria-label], [class*="guilds"], [data-list-id="guildsnav"]'),
    vencord: typeof V === 'object' && V !== null,
    vencordVersion: V && (V.version || (V.Updater && V.Updater.gitHash)) || null,
    corsuPresent: !!corsu, corsuStarted: !!(corsu && corsu.started),
    corsuEnabled: !!(V && V.Settings && V.Settings.plugins && V.Settings.plugins.Corsu && V.Settings.plugins.Corsu.enabled),
    sentry: env.SENTRY_TAGS || null, releaseChannel: env.RELEASE_CHANNEL || null,
    scripts: [...document.scripts].map(s => s.src).filter(Boolean),
  };
})()'''

BUILD = r'''(async () => {
  for (const src of [...document.scripts].map(s => s.src).filter(Boolean)) {
    try {
      const text = await (await fetch(src)).text();
      const m = text.match(/buildNumber\D{1,6}(\d{6,})/) || text.match(/build_number\D{1,6}(\d{6,})/);
      if (m) return {buildNumber: m[1], asset: src};
    } catch (e) {}
  }
  return null;
})()'''


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def launcher_asar(patcher):
    """The asar VencordInstallerCli writes (app_asar.go WriteAppAsar): index.js requires patcher.js."""
    index = ('require(' + json.dumps(str(patcher)) + ')').encode()
    package = b'{\n\t"name": "discord",\n\t"main": "index.js"\n}'
    header = json.dumps({'files': {'index.js': {'size': len(index), 'offset': '0'},
                                   'package.json': {'size': len(package), 'offset': str(len(index))}}},
                        separators=(',', ':')).encode()
    aligned = (len(header) + 3) & ~3
    return struct.pack('<4i', 4, aligned + 8, aligned + 4, len(header)) + header.ljust(aligned, b'0') + index + package


def is_launcher(data):
    return len(data) < 65536 and b'patcher.js' in data


def prepare(client, work, dist, settings):
    home = work / 'home'
    root = home / '.config/discord'
    copy = root / client.name
    shutil.copytree(client, copy, symlinks=True)
    # Discord's updater needs its record next to the app folder, or it tries to install over the running copy.
    if (client.parent / 'installer.db').is_file():
        shutil.copy2(client.parent / 'installer.db', root / 'installer.db')
    (root / 'settings.json').write_text(json.dumps({'SKIP_HOST_UPDATE': True, 'SKIP_MODULE_UPDATE': True}))
    resources = copy / 'resources'
    original = next(data for data in ((resources / name).read_bytes() for name in ('_app.asar', 'app.asar')
                                      if (resources / name).is_file()) if not is_launcher(data))
    (resources / '_app.asar').unlink(missing_ok=True)
    (resources / 'app.asar').write_bytes(original)
    if dist:
        target = work / 'Vencord/dist'
        shutil.copytree(dist, target)
        (resources / '_app.asar').write_bytes(original)
        (resources / 'app.asar').write_bytes(launcher_asar(target / 'patcher.js'))
        vencord = home / '.config/Vencord/settings'
        vencord.mkdir(parents=True)
        (vencord / 'settings.json').write_text(settings.read_text() if settings else '{}')
    return home, copy


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('client', nargs='?', type=Path)
    parser.add_argument('--vencord', type=Path)
    parser.add_argument('--settings', type=Path)
    parser.add_argument('--work', type=Path)
    parser.add_argument('--timeout', type=float, default=90)
    # CI runners have no setuid chrome-sandbox; never needed on a person's machine.
    parser.add_argument('--no-sandbox', action='store_true')
    args = parser.parse_args()
    if not args.client or not (args.client / 'Discord').is_file():
        print('SKIP: no real Discord client folder given')
        return 0
    if not shutil.which('weston'):
        print('SKIP: weston (headless compositor) not installed; refusing to open windows on the desktop')
        return 0
    work = (args.work or Path(tempfile.mkdtemp(prefix='discord-real-'))).resolve()
    if any(work.is_relative_to(path.resolve()) for path in PROTECTED if path.exists()):
        raise SystemExit(f'Refusing to work inside a real installation: {work}')
    if work.exists() and any(work.iterdir()):
        raise SystemExit(f'Work folder not empty: {work}')
    work.mkdir(parents=True, exist_ok=True)
    expect_corsu = False
    if args.settings:
        expect_corsu = bool(json.loads(args.settings.read_text()).get('plugins', {}).get('Corsu', {}).get('enabled'))
    home, copy = prepare(args.client.resolve(), work, args.vencord and args.vencord.resolve(), args.settings)
    # Unix socket paths are limited to 108 bytes: the compositor's socket lives in a short folder.
    runtime = Path(tempfile.mkdtemp(prefix='cdr-', dir='/tmp' if Path('/tmp').is_dir() else None))
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
    port = free_port()
    stderr = open(work / 'stderr.log', 'wb')
    discord = subprocess.Popen([str(copy / 'Discord'), '--ozone-platform=wayland', f'--remote-debugging-port={port}',
                                f'--user-data-dir={home / ".config/discord"}', '--enable-logging=stderr', *(['--no-sandbox'] if args.no_sandbox else [])],
                               cwd=work, env=environment, start_new_session=True, stdout=stderr, stderr=subprocess.STDOUT)
    console = open(work / 'console.jsonl', 'w', encoding='utf-8')
    result = {'client': str(args.client), 'vencord': str(args.vencord) if args.vencord else None,
              'settings': json.loads(args.settings.read_text()) if args.settings else None,
              'work': str(work), 'exceptions': [], 'errors': []}
    try:
        result.update(watch(port, discord, console, result, args.timeout, bool(args.vencord)))
    finally:
        console.close()
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
    state = result.get('state') or {}
    result['passed_splash'] = state.get('mountChildren', 0) > 0 and (state.get('login') or state.get('app'))
    failures = []
    if not result['passed_splash']:
        failures.append('main window did not reach the login page or the app')
    if args.vencord and not state.get('vencord'):
        failures.append('window.Vencord missing')
    # Vencord starts plugins like Corsu at WebpackReady, i.e. on the gateway's CONNECTION_OPEN: only after a login.
    if expect_corsu and not state.get('corsuEnabled'):
        failures.append('Corsu plugin not enabled')
    if expect_corsu and state.get('app') and not state.get('corsuStarted'):
        failures.append('Corsu plugin not started')
    result['corsu_patches_applied'] = sum('patch by Corsu' in item for item in open(work / 'console.jsonl', encoding='utf-8'))
    result['failures'] = failures
    (work / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = {key: result.get(key) for key in ('passed_splash', 'failures', 'build')}
    summary['state'] = {key: state.get(key) for key in ('url', 'mountChildren', 'login', 'app', 'vencord',
                                                        'vencordVersion', 'corsuPresent', 'corsuEnabled', 'corsuStarted', 'sentry')}
    summary['corsu_patches_applied'] = result['corsu_patches_applied']
    summary['exceptions'] = [item['text'] for item in result['exceptions']][:10]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    # NoTrack throws this on purpose to stop Sentry; the RPC port is taken when another Discord is open.
    unexpected = [item for item in result['exceptions'] if 'Sentry successfully disabled' not in item['text']
                  and 'EADDRINUSE' not in item['text']]
    if unexpected:
        print('First unexpected uncaught exception:\n' + unexpected[0]['text'] + '\n' + unexpected[0]['stack'])
    if not state.get('app'):
        print('Note: not logged in, so the login page is the usable state; Corsu (WebpackReady) starts only after login.')
    print(f'Logs: {work}/stderr.log, {work}/console.jsonl, {work}/result.json')
    print('PASS' if not failures else 'FAIL: ' + '; '.join(failures))
    return 1 if failures else 0


def stack_text(trace):
    return '\n'.join(f'    at {frame.get("functionName") or "<anonymous>"} ({frame["url"]}:{frame["lineNumber"] + 1}:'
                     f'{frame["columnNumber"] + 1})' for frame in (trace or {}).get('callFrames', []))


def watch(port, discord, console, result, timeout, vencord):
    deadline = time.monotonic() + timeout
    while True:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=1) as response:
                browser = json.load(response)['webSocketDebuggerUrl']
            break
        except OSError:
            if discord.poll() is not None or time.monotonic() > deadline:
                return {'state': None, 'exit': discord.poll()}
            time.sleep(0.05)
    tools = DevTools(browser)
    sessions = {}  # session id -> target info

    def send(method, session):
        tools.counter += 1
        data = json.dumps({'id': tools.counter, 'method': method, 'params': {}, 'sessionId': session}).encode()
        mask = os.urandom(4)
        tools.socket.sendall(bytes([0x81, 0x80 | len(data)]) + mask + bytes(byte ^ mask[index % 4]
                                                                             for index, byte in enumerate(data)))

    def handle(event):
        method, params, session = event.get('method'), event.get('params', {}), event.get('sessionId')
        if method == 'Target.attachedToTarget':
            info = params['targetInfo']
            if info['type'] == 'page':
                sessions[params['sessionId']] = info
                for call in ('Runtime.enable', 'Log.enable'):
                    send(call, params['sessionId'])
            # A paused target answers only once resumed, so these are sent without waiting for replies.
            send('Runtime.runIfWaitingForDebugger', params['sessionId'])
        elif method == 'Target.targetInfoChanged' and session is None:
            for key, info in sessions.items():
                if info['targetId'] == params['targetInfo']['targetId']:
                    sessions[key] = params['targetInfo']
        elif method == 'Runtime.exceptionThrown':
            details = params['exceptionDetails']
            text = (details.get('exception') or {}).get('description') or details.get('text')
            item = {'page': sessions.get(session, {}).get('url'), 'text': text.split('\n')[0],
                    'stack': stack_text(details.get('stackTrace')) or text}
            result['exceptions'].append(item)
            console.write(json.dumps({'exception': item}, ensure_ascii=False) + '\n')
        elif method == 'Runtime.consoleAPICalled':
            text = ' '.join(str(arg.get('value', arg.get('description', ''))) for arg in params['args'])
            item = {'page': sessions.get(session, {}).get('url'), 'type': params['type'], 'text': text,
                    'stack': stack_text(params.get('stackTrace')) if params['type'] in ('error', 'assert') else ''}
            console.write(json.dumps(item, ensure_ascii=False) + '\n')
            if params['type'] in ('error', 'assert'):
                result['errors'].append(item)
        elif method == 'Log.entryAdded' and params['entry']['level'] == 'error':
            console.write(json.dumps({'log': params['entry']}, ensure_ascii=False) + '\n')

    tools.call('Target.setDiscoverTargets', {'discover': True})
    tools.call('Target.setAutoAttach', {'autoAttach': True, 'waitForDebuggerOnStart': True, 'flatten': True})
    for info in tools.call('Target.getTargets')['targetInfos']:
        if info['type'] == 'page' and not info['attached']:
            tools.call('Target.attachToTarget', {'targetId': info['targetId'], 'flatten': True})
    state, reached, last_probe = None, None, 0
    while time.monotonic() < deadline and discord.poll() is None:
        while tools.events:
            handle(tools.events.pop(0))
        if time.monotonic() - last_probe > 2:
            last_probe = time.monotonic()
            main_window = [key for key, info in sessions.items() if 'discord' in info.get('url', '')
                           and 'splash' not in info.get('url', '') and info.get('url', '').startswith('http')]
            for key in main_window:
                try:
                    state = tools.call('Runtime.evaluate', {'expression': PROBE, 'returnByValue': True},
                                       session=key)['result'].get('value')
                except RuntimeError:
                    continue
            usable = state and state['mountChildren'] > 0 and (state['login'] or state['app'])
            if usable and reached is None:
                reached = time.monotonic()
            # A few seconds more so late plugin start-up and errors are recorded.
            if reached and time.monotonic() - reached > (10 if vencord else 4):
                break
        tools.socket.settimeout(0.5)
        try:
            tools.events.append(json.loads(tools._frame()))
        except socket.timeout:
            pass
        except (EOFError, OSError):
            break
        finally:
            tools.socket.settimeout(30)
    build = None
    for key, info in sessions.items():
        if state and info.get('url') == state.get('url'):
            try:
                build = tools.call('Runtime.evaluate', {'expression': BUILD, 'awaitPromise': True,
                                                        'returnByValue': True}, session=key)['result'].get('value')
            except (RuntimeError, OSError, EOFError):
                pass
    while tools.events:
        handle(tools.events.pop(0))
    return {'state': state, 'build': build, 'exit': discord.poll(),
            'seconds_to_ui': round(reached - (deadline - timeout), 1) if reached else None}


if __name__ == '__main__':
    sys.exit(main())
