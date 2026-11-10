"""A native notification from Corsu (docs/dev/discord-watch.md): one per incident, never taking the focus.

notify(title, body, action, incident) -> bool. True when the system showed it (or already did for this incident);
False when no notification service can be used: the caller keeps its state, which Corsu's window shows next time.
Every platform shows it under Corsu's name, as an ordinary notification: the system's do-not-disturb (Focus Assist,
Focus) applies, nothing asks to bypass it.
- Linux: org.freedesktop.Notifications through gdbus, with Corsu's icon and an "Open" button that opens Corsu's window
  on the page `action` (a small process waits for the click until the notification closes, at most WAIT_SECONDS).
  Without gdbus, notify-send, without the button.
- Windows: a toast under Corsu's own AppUserModelID (the window's), registered for the current user with Corsu's name
  and icon; a click opens Corsu's window on the page through the corsu-recovery: link registered with it. Sent by
  Windows PowerShell started without any console window (corsu.hidden).
- macOS: osascript's display notification, titled Corsu, without a button. macOS shows it with Script Editor's icon.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from xml.sax.saxutils import escape

import corsu

# Pages a notification may open, and the form of an incident id (the watcher writes UUIDs).
PAGES = {'discord-recovery'}
INCIDENT = re.compile(r'[\w-]{1,64}')
SENT = 'discord-watch/notified.json'
KEEP = 50
# How long the Linux helper waits for a click on the notification's button.
WAIT_SECONDS = 1800
# Windows: the AppUserModelID of Corsu's window (window.py), and the link a click on a toast opens.
APP_ID = 'Platykalt.Corsu'
PROTOCOL = 'corsu-recovery'
CLASSES = 'Software\\Classes'
TOAST = ("$ErrorActionPreference = 'Stop'; "
         "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
         "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null; "
         "$x = New-Object Windows.Data.Xml.Dom.XmlDocument; $x.LoadXml($env:CORSU_TOAST); "
         "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($env:CORSU_TOAST_APP)"
         ".Show([Windows.UI.Notifications.ToastNotification]::new($x))")


def sent():
    try:
        found = json.loads((corsu.DATA / SENT).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    return [item for item in found if isinstance(item, str)] if isinstance(found, list) else []


def remember(incident):
    path = corsu.DATA / SENT
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.corsu-tmp')
    temporary.write_text(json.dumps([*[item for item in sent() if item != incident], incident][-KEEP:]), encoding='utf-8')
    os.replace(temporary, path)


def window_command(action, incident):
    """Corsu's window on page `action` for this incident: the copy of Corsu this module belongs to."""
    command = [sys.executable, str(corsu.SRC / 'app.py')]
    if action in PAGES:
        command += ['--page', action]
        if incident and INCIDENT.fullmatch(incident):
            command += ['--incident', incident]
    return command


def gvariant(text):
    return "'" + str(text).replace('\\', '\\\\').replace("'", "\\'") + "'"


def linux(title, body, action, incident):
    gdbus = shutil.which('gdbus')
    if gdbus:
        label = 'Apre' if corsu.corsican() else corsu.t('Open', 'Ouvrir')
        # '--': the last argument, -1 (server's default duration), must not be read as an option.
        actions = f'[{gvariant("default")}, {gvariant(label)}, {gvariant("open")}, {gvariant(label)}]' if action else '@as []'
        # urgency 1 (normal): shown like any notification, never over a full-screen game, no focus taken.
        hints = "{'desktop-entry': <'corsu-setup'>, 'urgency': <byte 1>}"
        icon = str(corsu.SRC / 'app/corsu.svg')
        try:
            result = subprocess.run([gdbus, 'call', '--session', '--dest', 'org.freedesktop.Notifications',
                                     '--object-path', '/org/freedesktop/Notifications',
                                     '--method', 'org.freedesktop.Notifications.Notify', '--', 'Corsu', '0', gvariant(icon),
                                     gvariant(title), gvariant(body), actions, hints, '-1'],
                                    capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            result = None
        found = re.search(r'uint32 (\d+)', result.stdout) if result and result.returncode == 0 else None
        if found:
            if action:
                # shortcut: a click in the instant before the helper listens is missed; the window still shows it.
                subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'wait', found.group(1),
                                  *window_command(action, incident)],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
            return True
    notify_send = shutil.which('notify-send')
    if notify_send:
        try:
            return subprocess.run([notify_send, '--app-name=Corsu', '--urgency=normal',
                                   f'--icon={corsu.SRC / "app/corsu.svg"}', title, body],
                                  capture_output=True, timeout=10).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False
    return False


def wait_for_click(number, command, seconds=WAIT_SECONDS):
    """Linux helper: open `command` when notification `number`'s button (or the notification) is clicked; stop when
    it closes or after `seconds`, even when the bus stays silent."""
    monitor = subprocess.Popen(['gdbus', 'monitor', '--session', '--dest', 'org.freedesktop.Notifications',
                                '--object-path', '/org/freedesktop/Notifications'],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    # Reading blocks until the bus says something: the deadline ends the monitor, which ends the reading.
    deadline = threading.Timer(seconds, monitor.kill)
    deadline.daemon = True
    deadline.start()
    try:
        for line in monitor.stdout:
            if f'(uint32 {number},' not in line:
                continue
            if '.ActionInvoked' in line and re.search(r"'(default|open)'", line):
                subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
                break
            if '.NotificationClosed' in line:
                break
    finally:
        deadline.cancel()
        monitor.kill()


def windows_keys():
    """What Windows needs, for the current user only, to show Corsu's toasts as Corsu's: its AppUserModelID with
    Corsu's name and icon (an id Windows does not know shows no toast), and the corsu-recovery: link a click opens.
    The link starts Corsu's window on the recovery page and ignores the rest of the address: a web page that opens
    such a link can do no more than open that page. Written again before each toast, so it names the current copy."""
    icon = max(corsu.SRC.glob('app/icons/corsu-*.png'), key=lambda path: int(path.stem.split('-')[1]))
    command = subprocess.list2cmdline([str(corsu.python_launcher()), str(corsu.SRC / 'app.py'), '--page', 'discord-recovery'])
    return {f'{CLASSES}\\AppUserModelId\\{APP_ID}': {'DisplayName': 'Corsu', 'IconUri': str(icon)},
            f'{CLASSES}\\{PROTOCOL}': {'': 'URL:Corsu', 'URL Protocol': ''},
            f'{CLASSES}\\{PROTOCOL}\\shell\\open\\command': {'': command}}


def windows_register():
    import winreg
    for key, values in windows_keys().items():
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as handle:
            for name, value in values.items():
                winreg.SetValueEx(handle, name, 0, winreg.REG_SZ, value)


def windows_unregister():
    """Uninstall: Corsu's registration for its toasts goes away (keys deleted from the deepest)."""
    try:
        import winreg
    except ImportError:  # not Windows (a test of the Windows path elsewhere)
        return
    keys = [*windows_keys(), f'{CLASSES}\\{PROTOCOL}\\shell\\open', f'{CLASSES}\\{PROTOCOL}\\shell']
    for key in sorted(keys, key=lambda key: key.count('\\'), reverse=True):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
        except OSError:
            pass


def windows(title, body, action, incident):
    try:
        windows_register()
    except (OSError, ValueError, ImportError):
        return False  # never shown under another program's name instead
    click = f' activationType="protocol" launch="{PROTOCOL}:{action}"' if action else ''
    xml = (f'<toast{click}><visual><binding template="ToastGeneric"><text>{escape(title)}</text><text>{escape(body)}</text>'
           '</binding></visual></toast>')
    try:
        result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', TOAST],
                                **corsu.hidden(capture_output=True, timeout=30,
                                               env={**os.environ, 'CORSU_TOAST': xml, 'CORSU_TOAST_APP': APP_ID}))
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def macos(title, body, action, incident):
    try:
        return subprocess.run(['osascript', '-e', 'on run argv', '-e',
                               'display notification (item 2 of argv) with title "Corsu" subtitle (item 1 of argv)', '-e', 'end run',
                               title, body], capture_output=True, timeout=15).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def notify(title, body, action=None, incident=None):
    incident = str(incident) if incident is not None and INCIDENT.fullmatch(str(incident)) else None
    if incident and incident in sent():
        return True
    show = {'linux': linux, 'windows': windows, 'macos': macos}.get(corsu.PLATFORM)
    shown = bool(show and show(title, body, action if action in PAGES else None, incident))
    if shown and incident:
        try:
            remember(incident)
        except OSError:
            pass
    return shown


if __name__ == '__main__' and len(sys.argv) > 3 and sys.argv[1] == 'wait' and sys.argv[2].isdigit():
    wait_for_click(sys.argv[2], sys.argv[3:])
