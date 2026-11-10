#!/usr/bin/env python3
"""The whole Discord recovery path against a COPY of the real Discord client, isolated in a headless weston with a
private D-Bus session: injection by the official installer, a failing start, the notification and its button, the
recovery window's API, "start without the translation", a reactivation that fails while Discord stays open (then
"finish the restore"), and a reactivation that starts but cannot prove the translation loaded.

Usage: check_discord_recovery_real.py CLIENT --bad DIST --good DIST --installer BINARY --work DIR [--no-sandbox]
  CLIENT     a Linux Discord app folder, e.g. ~/.config/discord/app-1.0.168 (only read: copied into DIR).
  --bad      a Vencord dist/ that fails with this Discord (Vencord 1.15.9 with Discord 1.0.168).
  --good     Corsu's own build (Vencord/dist of a release archive).
  --installer  VencordInstallerCli-linux, the binary src/release.json pins (copied, checked by its sha256).
  --work     an empty folder outside any real installation: HOME, Corsu's data and the copies all go there.

Nothing of the person's own Discord, profile or Corsu is read or changed: HOME, XDG folders, the Wayland display
and the D-Bus session all point into DIR, and the "is Discord open" check only counts the processes of the copy.
Without an account, Discord stays on its login page, where Vencord never reaches the WebpackReady stage that starts
the Corsu plugin: a reactivation can only end "not confirmed" here, which is what this checks. Exit 0 when every step
holds; each step prints PASS or FAIL.
"""
import argparse
import http.client
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

# A notification server for the private bus: records each Notify, then "clicks" its default action after 3 s.
NOTIFICATION_SERVER = r'''
import json, sys, threading
from gi.repository import Gio, GLib
record = sys.argv[1]
XML = """<node><interface name="org.freedesktop.Notifications">
<method name="Notify"><arg type="s" direction="in"/><arg type="u" direction="in"/><arg type="s" direction="in"/>
<arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="as" direction="in"/><arg type="a{sv}" direction="in"/>
<arg type="i" direction="in"/><arg type="u" direction="out"/></method>
<method name="CloseNotification"><arg type="u" direction="in"/></method>
<method name="GetCapabilities"><arg type="as" direction="out"/></method>
<method name="GetServerInformation"><arg type="s" direction="out"/><arg type="s" direction="out"/><arg type="s" direction="out"/><arg type="s" direction="out"/></method>
<signal name="ActionInvoked"><arg type="u"/><arg type="s"/></signal>
<signal name="NotificationClosed"><arg type="u"/><arg type="u"/></signal>
</interface></node>"""
node = Gio.DBusNodeInfo.new_for_xml(XML)
count = [0]
def call(connection, sender, path, interface, method, parameters, invocation):
    if method == "Notify":
        count[0] += 1
        number = count[0]
        app, _, icon, title, body, actions, hints, timeout = parameters.unpack()
        with open(record, "a") as handle:
            handle.write(json.dumps({"id": number, "app": app, "title": title, "body": body, "actions": actions}) + "\n")
        invocation.return_value(GLib.Variant("(u)", (number,)))
        def click():
            connection.emit_signal(None, path, interface, "ActionInvoked", GLib.Variant("(us)", (number, "default")))
            return False
        GLib.timeout_add_seconds(3, click)
    elif method == "GetCapabilities":
        invocation.return_value(GLib.Variant("(as)", (["actions", "body"],)))
    elif method == "GetServerInformation":
        invocation.return_value(GLib.Variant("(ssss)", ("test", "corsu", "1", "1.2")))
    else:
        invocation.return_value(None)
def acquired(connection, name):
    connection.register_object("/org/freedesktop/Notifications", node.interfaces[0], call, None, None)
Gio.bus_own_name(Gio.BusType.SESSION, "org.freedesktop.Notifications", Gio.BusNameOwnerFlags.NONE, acquired, None, None)
GLib.MainLoop().run()
'''

# What the notification's button starts, recorded instead of opening a window on the desktop.
RECORDER = 'import json, sys; open(sys.argv[1], "w").write(json.dumps(sys.argv[2:]))'

RESULTS = []


def check(name, passed, detail=''):
    RESULTS.append(bool(passed))
    print(f'{"PASS" if passed else "FAIL"}: {name}{" (" + str(detail) + ")" if detail else ""}', flush=True)
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('client', nargs='?', type=Path)
    parser.add_argument('--bad', type=Path, required=True)
    parser.add_argument('--good', type=Path, required=True)
    parser.add_argument('--installer', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--no-sandbox', action='store_true')
    args = parser.parse_args()
    if not args.client or not (args.client / 'Discord').is_file():
        print('SKIP: no real Discord client folder given')
        return 0
    for tool in ('weston', 'dbus-daemon', 'gdbus'):
        if not shutil.which(tool):
            print(f'SKIP: {tool} not installed; refusing to use the desktop session')
            return 0
    work = args.work.resolve()
    real = [Path.home() / name for name in ('.config', '.local', '.cache')] + [Path('/usr'), Path('/opt')]
    if any(work.is_relative_to(path) for path in real):
        raise SystemExit(f'Refusing to work inside a real installation: {work}')
    if work.exists() and any(work.iterdir()):
        raise SystemExit(f'Work folder not empty: {work}')
    home, runtime = work / 'home', work / 'run'
    for folder in (home, runtime):
        folder.mkdir(parents=True)
    runtime.chmod(0o700)
    # Everything below, Corsu included, sees only DIR. Set before importing corsu, which reads HOME at import.
    os.environ.update({'HOME': str(home), 'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_DATA_HOME': str(home / '.local/share'),
                       'XDG_CACHE_HOME': str(home / '.cache'), 'XDG_RUNTIME_DIR': str(runtime),
                       'WAYLAND_DISPLAY': 'corsu-headless', 'LANG': 'fr_FR.UTF-8', 'LANGUAGE': 'fr', 'CORSU_LANG': 'fr'})
    os.environ.pop('DISPLAY', None)
    bus = subprocess.Popen(['dbus-daemon', '--session', '--nofork', '--print-address=1'], stdout=subprocess.PIPE,
                           text=True, start_new_session=True)
    os.environ['DBUS_SESSION_BUS_ADDRESS'] = bus.stdout.readline().strip()
    notifications = work / 'notifications.jsonl'
    server = subprocess.Popen([sys.executable, '-c', NOTIFICATION_SERVER, str(notifications)], start_new_session=True)
    weston = subprocess.Popen(['weston', '--backend=headless', '--socket=corsu-headless', '--width=1280', '--height=800',
                               '--idle-time=0'], start_new_session=True, stdout=open(work / 'weston.log', 'wb'),
                              stderr=subprocess.STDOUT)
    for _ in range(50):
        if (runtime / 'corsu-headless').exists():
            break
        time.sleep(0.1)
    try:
        return run(args, work, home, notifications)
    finally:
        stop_copy(None)
        for process in (server, weston, bus):
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


COPY = {}


def copy_pids():
    """The processes of the isolated copy only: the person's own Discord may be open on this computer."""
    found = []
    for exe in Path('/proc').glob('[0-9]*/exe'):
        try:
            if Path(os.readlink(exe)).is_relative_to(COPY['path']):
                found.append(int(exe.parent.name))
        except (OSError, ValueError):
            continue
    return found


def stop_copy(_unused, seconds=20):
    """Quit the isolated copy (SIGTERM, Electron's normal quit), and wait until its processes are gone."""
    if 'path' not in COPY:
        return True
    for pid in copy_pids():
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.time() + seconds
    while copy_pids() and time.time() < deadline:
        time.sleep(0.5)
    for pid in copy_pids():
        os.kill(pid, signal.SIGKILL)
    time.sleep(1)
    return not copy_pids()


def fake_root(work, name, dist, binary, manifest):
    """A Corsu copy as installer.install_discord sees it: src/release.json, vendor/<installer>, Vencord/dist."""
    root = work / name
    (root / 'src').mkdir(parents=True)
    shutil.copy2(manifest, root / 'src/release.json')
    entry = json.loads(manifest.read_text(encoding='utf-8'))['installers']['linux']
    (root / 'vendor').mkdir()
    shutil.copy2(binary, root / 'vendor' / entry['file'])
    shutil.copytree(dist, root / 'Vencord/dist')
    return root


def run(args, work, home, notifications):
    sys.path.insert(0, str(REPO / 'src'))
    sys.path.insert(0, str(HERE))
    from check_discord_real_start import prepare
    import corsu
    import discord_watch
    import installer
    import notify
    import app
    assert corsu.DATA.is_relative_to(work), corsu.DATA
    copy = prepare(args.client.resolve(), work, None, None)[1]
    COPY['path'] = copy
    original = (copy / 'resources/app.asar').read_bytes()
    user_data = home / '.config/discord'
    command = [str(copy / 'Discord'), '--ozone-platform=wayland', f'--user-data-dir={user_data}',
               *(['--no-sandbox'] if args.no_sandbox else [])]
    log = user_data / 'logs/renderer_js.log'
    # The watcher and the window, pointed at the copy: its command, its processes. Everything else is the real code.
    discord_watch.default_command = lambda *where: list(command)
    discord_watch.discord_running = lambda *names: bool(copy_pids())
    app.still_open = lambda name: bool(copy_pids()) if name == 'discord' else False
    clicked = work / 'clicked.json'
    real_window = notify.window_command
    notify.window_command = lambda action, incident: [sys.executable, '-c', RECORDER, str(clicked),
                                                      *real_window(action, incident)]
    manifest = REPO / 'src/release.json'
    bad = fake_root(work, 'corsu-old', args.bad.resolve(), args.installer.resolve(), manifest)
    good = fake_root(work, 'corsu-new', args.good.resolve(), args.installer.resolve(), manifest)
    app_asar = copy / 'resources/app.asar'

    print('1. Injection by the official installer (an incompatible build)', flush=True)
    installer.ROOT = bad
    installer.install_discord(copy)
    check('app.asar is the launcher of the incompatible build',
          installer.vencord_launcher(app_asar.read_bytes()) and str(bad) in app_asar.read_text(errors='replace'))

    print('2. A watched start that fails, its notification and its button', flush=True)
    record = discord_watch.launch(command, 'shortcut')
    check('the watch decides vencord-error', record and record['state'] == 'vencord-error', record and record['state'])
    check('Discord is still open (stuck), nothing closed it', bool(copy_pids()))
    deadline = time.time() + 15
    while not clicked.exists() and time.time() < deadline:
        time.sleep(0.5)
    sent = [json.loads(line) for line in notifications.read_text().splitlines()] if notifications.exists() else []
    check('one notification on the private bus', len(sent) == 1, json.dumps(sent, ensure_ascii=False)[:300])
    if sent:
        check('in French, the cause worded as probable', 'probablement' in sent[0]['body'], sent[0]['body'])
    opened = json.loads(clicked.read_text()) if clicked.exists() else []
    check('the button opens the recovery window for this incident',
          opened[2:] == ['--page', 'discord-recovery', '--incident', record['incident']] and opened[1].endswith('app.py'),
          ' '.join(opened))
    again = discord_watch.alert({**record, 'notified': False})
    check('no second notification for the same incident',
          again['notified'] and len(notifications.read_text().splitlines()) == 1)

    print('3. The recovery window (its server, with its key, as the page calls it)', flush=True)
    threading.Thread(target=app.serve, args=('none', None, app.page_query(opened)), daemon=True).start()
    deadline = time.time() + 20
    while not app.ACCESS.url and time.time() < deadline:
        time.sleep(0.2)
    url = app.ACCESS.url

    def call(path, body=None):
        address = url.split('//', 1)[1].rstrip('/')
        connection = http.client.HTTPConnection(*address.split(':'), timeout=10)
        headers = {'X-Corsu': '1', 'X-Corsu-Key': app.ACCESS.key, 'Host': address, 'Content-Type': 'application/json'}
        connection.request('POST' if body is not None else 'GET', path,
                           body=json.dumps(body).encode() if body is not None else None, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read() or b'null')

    def discord():
        return call('/api/state')[1]['discord']

    def act(name, wait=420):
        status, answer = call(f'/api/discord/{name}', {'incident': discord().get('incident')})
        deadline = time.time() + wait
        while time.time() < deadline:
            action = discord()['action']
            if action and action['name'] == name and not action['running']:
                return action['result']
            time.sleep(1)
        return {'timeout': True, 'status': status, 'answer': answer}

    shown = discord()
    check('the window shows the problem, with the evidence',
          shown['row'] == 'problem' and shown['state'] == 'vencord-error' and shown['evidence'], shown['row'])

    def started_without_vencord(since, seconds=150):
        """The button's own start (a watcher process of its own): the copy's next session reaches Discord's UI with no
        Vencord line. Read from Discord's log, since that process may count the person's own Discord as open."""
        deadline = time.time() + seconds
        while time.time() < deadline:
            text = log.read_bytes()[since:].decode('utf-8', errors='replace') if log.exists() else ''
            groups = discord_watch.sessions(discord_watch.parse(text))
            kinds = {entry['kind'] for entry in groups[-1]} if groups else set()
            if 'ui' in kinds:
                return copy_pids() and not kinds & {'vencord', 'corsu'}
            time.sleep(1)
        return False

    print('4. "Start without the translation"', flush=True)
    result = act('rescue')
    check('refused while Discord is open, Discord left open', result.get('reason') == 'running' and copy_pids(), result)
    check('Discord quit (in the test, by its normal SIGTERM)', stop_copy(None))
    offset = log.stat().st_size if log.exists() else 0
    settings = home / '.config/Vencord/settings/settings.json'
    kept = settings.read_bytes() if settings.is_file() else None
    result = act('rescue')
    shown = discord()
    check('rescue mode, the original archive back', result.get('ok') and (shown['rescue'] or {}).get('phase') == 'rescue'
          and app_asar.read_bytes() == original, result)
    check('the button started Discord, and it started without Vencord (as its label says)',
          result.get('started') and started_without_vencord(offset), result)
    check('nothing else changed: Vencord\'s copy of the original and its settings kept',
          (copy / 'resources/_app.asar').read_bytes() == original
          and (settings.read_bytes() if settings.is_file() else None) == kept)
    installer.ROOT = good
    installer.install_discord(copy)
    check('a repair or update leaves Discord alone in rescue mode', app_asar.read_bytes() == original)
    stop_copy(None)

    print('5. A reactivation that fails while Discord stays open, then "finish the restore"', flush=True)
    installer.ROOT = bad
    result = act('reactivate')
    shown = discord()
    check('reported as failed: restore pending, not as reactivated',
          result.get('reason') == 'restore-pending' and not result.get('ok'), result)
    check('rescue.json kept, phase restore-pending', (shown['rescue'] or {}).get('phase') == 'restore-pending'
          and discord_watch.in_rescue(), shown['rescue'])
    check('Discord left open, its archive not replaced under it',
          copy_pids() and installer.vencord_launcher(app_asar.read_bytes()))
    installer.ROOT = good
    installer.install_discord(copy)
    check('no reinjection while the restore waits', str(bad) in app_asar.read_text(errors='replace'))
    stop_copy(None)
    offset = log.stat().st_size
    result = act('rescue')
    check('finish the restore: back to rescue, original archive', result.get('ok')
          and (discord()['rescue'] or {}).get('phase') == 'rescue' and app_asar.read_bytes() == original, result)
    check('and Discord started again without the translation', result.get('started') and started_without_vencord(offset))
    stop_copy(None)

    print('6. A reactivation with the current build: Discord starts, the translation is not proved', flush=True)
    result = act('reactivate')
    shown = discord()
    check('reported "not confirmed", never as reactivated', result.get('reason') == 'unconfirmed' and not result.get('ok'),
          result)
    check('rescue mode kept, phase verifying', (shown['rescue'] or {}).get('phase') == 'verifying', shown['rescue'])
    check('the current build is injected', str(good) in app_asar.read_text(errors='replace'))
    stop_copy(None)
    # A start that proves it (the Corsu plugin seen starting) needs a signed-in Discord: settled from its log line.
    proof = {'state': 'ok-corsu', 'started_at': time.time(), 'client': str(copy)}
    check('a start that shows the Corsu plugin ends rescue mode', discord_watch.settle_reactivation(proof) == ''
          and not discord_watch.in_rescue())
    print(f'Work folder: {work}')
    return 0 if all(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
