#!/usr/bin/env python3
"""Windows: Corsu's Discord notification shows under Corsu's own name, not "Windows PowerShell".

Runs src/notify.py's Windows path for real on this account: it registers Corsu's AppUserModelID (HKEY_CURRENT_USER,
with Corsu's name and icon) and the corsu-recovery: link a click opens, shows one toast, then asks Windows which
toasts it keeps for that id (ToastNotificationManager.History). The registration is removed at the end, as Corsu's
uninstall does. Not checked here: the click itself (no one to click on a CI runner) and how the toast looks.
For CI runners and throwaway accounts: it writes to the current user's registry. Exit 0 when every step holds.
"""
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / 'src'))

import notify  # noqa: E402

RESULTS = []
HISTORY = ("[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] "
           "| Out-Null; [Windows.UI.Notifications.ToastNotificationManager]::History.GetHistory('{0}').Count")


def check(name, passed, detail=''):
    RESULTS.append(bool(passed))
    print(f'{"PASS" if passed else "FAIL"}: {name}{" (" + str(detail) + ")" if detail else ""}', flush=True)


def kept(app_id):
    found = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', HISTORY.format(app_id)],
                           capture_output=True, text=True, timeout=60)
    text = (found.stdout or '').strip()
    return (int(text) if text.isdigit() else None), (found.stderr or '').strip()[:300]


def registered():
    import winreg
    values = {}
    for key, names in notify.windows_keys().items():
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
                values[key] = {name: winreg.QueryValueEx(handle, name)[0] for name in names}
        except OSError:
            values[key] = None
    return values


def main():
    if sys.platform != 'win32':
        print('SKIP: Windows only')
        return 0
    try:
        check('the toast is accepted by Windows', notify.windows('Discord', 'Corsu: notification check',
                                                                 'discord-recovery', None))
        values = registered()
        identity = values[f'{notify.CLASSES}\\AppUserModelId\\{notify.APP_ID}'] or {}
        check("registered under Corsu's name and icon", identity.get('DisplayName') == 'Corsu'
              and Path(identity.get('IconUri', '')).is_file(), identity)
        command = (values[f'{notify.CLASSES}\\{notify.PROTOCOL}\\shell\\open\\command'] or {}).get('', '')
        check('a click opens Corsu on the recovery page', command.endswith('app.py --page discord-recovery'), command)
        count, error = kept(notify.APP_ID)
        check("Windows keeps the toast under Corsu's AppUserModelID", count is not None and count >= 1,
              f'count {count} {error}')
    finally:
        notify.windows_unregister()
    check('uninstall removes the registration', all(value is None for value in registered().values()))
    return 0 if all(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
