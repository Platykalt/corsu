"""A native notification from Corsu (docs/dev/discord-watch.md): one per incident, never taking the focus.

notify(title, body, action, incident) -> bool. True when the system showed it (or already did for this incident);
False when no notification service can be used: the caller keeps its state, which Corsu's window shows next time.
- Linux: org.freedesktop.Notifications through gdbus, with an "Open" button that opens Corsu's window on the page
  `action` (a small process waits for the click, until the notification closes); the notification server applies
  the person's do-not-disturb setting. Without gdbus, notify-send, without the button.
- Windows: a toast from Windows PowerShell started without any console window (corsu.hidden), no button.
- macOS: osascript's display notification, no button.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from xml.sax.saxutils import escape

import corsu

# Pages a notification may open, and the form of an incident id (the watcher writes UUIDs).
PAGES = {'discord-recovery'}
INCIDENT = re.compile(r'[\w-]{1,64}')
SENT = 'discord-watch/notified.json'
KEEP = 50
# How long the Linux helper waits for a click on the notification's button.
WAIT_SECONDS = 1800
POWERSHELL_APP = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe'
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
        label = corsu.t('Open', 'Ouvrir')
        # '--': the last argument, -1 (server's default duration), must not be read as an option.
        actions = f'[{gvariant("default")}, {gvariant(label)}, {gvariant("open")}, {gvariant(label)}]' if action else '@as []'
        # urgency 1 (normal): shown like any notification, never over a full-screen game, no focus taken.
        hints = "{'desktop-entry': <'corsu-setup'>, 'urgency': <byte 1>}"
        try:
            result = subprocess.run([gdbus, 'call', '--session', '--dest', 'org.freedesktop.Notifications',
                                     '--object-path', '/org/freedesktop/Notifications',
                                     '--method', 'org.freedesktop.Notifications.Notify', '--', 'Corsu', '0', 'dialog-warning',
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
            return subprocess.run([notify_send, '--app-name=Corsu', '--urgency=normal', title, body],
                                  capture_output=True, timeout=10).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False
    return False


def wait_for_click(number, command, seconds=WAIT_SECONDS):
    """Linux helper: open `command` when notification `number`'s button (or the notification) is clicked; stop when
    it closes or after `seconds`."""
    monitor = subprocess.Popen(['gdbus', 'monitor', '--session', '--dest', 'org.freedesktop.Notifications',
                                '--object-path', '/org/freedesktop/Notifications'],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    deadline = time.monotonic() + seconds
    try:
        for line in monitor.stdout:
            if time.monotonic() > deadline:
                break
            if f'(uint32 {number},' not in line:
                continue
            if '.ActionInvoked' in line and re.search(r"'(default|open)'", line):
                subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
                break
            if '.NotificationClosed' in line:
                break
    finally:
        monitor.kill()


def windows(title, body, action, incident):
    xml = (f'<toast><visual><binding template="ToastGeneric"><text>{escape(title)}</text><text>{escape(body)}</text>'
           '</binding></visual></toast>')
    try:
        result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', TOAST],
                                **corsu.hidden(capture_output=True, timeout=30,
                                               env={**os.environ, 'CORSU_TOAST': xml, 'CORSU_TOAST_APP': POWERSHELL_APP}))
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def macos(title, body, action, incident):
    try:
        return subprocess.run(['osascript', '-e', 'on run argv', '-e',
                               'display notification (item 2 of argv) with title (item 1 of argv)', '-e', 'end run',
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
