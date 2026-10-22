"""Corsu's own window on a real Windows (CI runner), from the extracted release archive and its own Python.

Corsu 0.27.0 closed at start on Windows: it gave pywebview a PNG icon, which pywebview's WinForms backend loads with
System.Drawing.Icon; that throws on a PNG inside a .NET thread and ends the program with its local server.

Usage: check_windows_window.py --root EXTRACTED_RELEASE [--python ARCHIVE_PYTHON]

1. The icon Corsu puts on its window (src/app/corsu.ico) is in the archive and is an ICO file.
2. With the archive's Python and its pythonnet: System.Drawing.Icon loads corsu.ico, and throws on the PNG
   0.27.0 handed to pywebview (so this check would have seen that crash); user32 LoadImageW loads corsu.ico, as
   window.windows_window_icon does.
3. The 0.27.0 call itself, pywebview's start(icon=PNG), with the archive's pywebview: the program ends without
   keeping a window.
4. Corsu as its shortcut starts it (pythonw.exe src/app.py, no --browser), with a throwaway user folder: a visible
   top-level window titled "Corsu" of that process appears, the process is still alive seconds later, the local
   server answers, the window carries an icon; a screenshot is saved in CORSU_E2E_ARTIFACTS; the window is closed
   with WM_CLOSE and the program ends by itself.
Every wait is bounded; on failure Corsu's log is printed.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
ICO_HEADER = b'\x00\x00\x01\x00'

user32 = ctypes.WinDLL('user32', use_last_error=True) if sys.platform == 'win32' else None
if user32:
    for name, arguments, result in (
            ('GetWindowThreadProcessId', [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD),
            ('IsWindowVisible', [wintypes.HWND], wintypes.BOOL), ('IsWindow', [wintypes.HWND], wintypes.BOOL),
            ('GetWindowTextW', [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int),
            ('GetWindowRect', [wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL),
            ('PostMessageW', [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM], wintypes.BOOL),
            ('SendMessageW', [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM], wintypes.LPARAM)):
        getattr(user32, name).argtypes, getattr(user32, name).restype = arguments, result


def step(text):
    print(f'\n== {text}', flush=True)


def archive_python(root, given):
    python = Path(given) if given else root / 'runtime/x86_64/python/python.exe'
    assert python.is_file(), f'no Python in the archive at {python}'
    return python


def check_ico(root):
    step('corsu.ico in the archive')
    ico = root / 'src/app/corsu.ico'
    assert ico.is_file(), f'missing {ico}'
    header = ico.read_bytes()[:6]
    assert header[:4] == ICO_HEADER, f'{ico} is not an ICO file (header {header.hex()})'
    print(f'{ico}: {ico.stat().st_size} bytes, ICO header {header[:4].hex()}, {int.from_bytes(header[4:6], "little")} images')
    return ico


PROBE = r'''
import ctypes, os, sys
from ctypes import wintypes
ico, png = sys.argv[1], sys.argv[2]
try:
    import clr
except Exception:
    os.environ['PYTHONNET_RUNTIME'] = 'coreclr'
    import clr
clr.AddReference('System.Drawing')
from System.Drawing import Icon
icon = Icon(ico)
print(f'System.Drawing.Icon(corsu.ico): loaded, {icon.Width}x{icon.Height}')
icon.Dispose()
try:
    Icon(png)
except Exception as error:
    print(f'System.Drawing.Icon(PNG): throws {type(error).__name__}: {error}')
else:
    print('System.Drawing.Icon(PNG): loaded (unexpected)')
    sys.exit(3)
user32 = ctypes.windll.user32
user32.LoadImageW.restype = wintypes.HANDLE
user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
handle = user32.LoadImageW(None, ico, 1, 32, 32, 0x10)
print(f'user32 LoadImageW(corsu.ico, 32x32): handle {handle}')
sys.exit(0 if handle else 4)
'''


def largest_png(root):
    icons = sorted((root / 'src/app/icons').glob('corsu-*.png'), key=lambda path: int(path.stem.split('-')[1]))
    assert icons, 'no PNG icons in src/app/icons'
    return icons[-1]


def check_dotnet(python, ico, png):
    step('System.Drawing.Icon and LoadImageW with the archive\'s Python (pythonnet)')
    result = subprocess.run([str(python), '-I', '-c', PROBE, str(ico), str(png)], capture_output=True, text=True,
                            timeout=180)
    print(result.stdout + result.stderr)
    assert result.returncode == 0, f'probe failed with exit code {result.returncode}'
    assert 'System.Drawing.Icon(PNG): throws' in result.stdout, 'the PNG did not make System.Drawing.Icon throw'


# What window.py did in 0.27.0 on every system: a window, then start(icon=<largest PNG>).
REPRODUCE = r'''
import sys
import webview
webview.create_window('Corsu 0.27.0 icon', 'about:blank', width=400, height=300)
webview.start(icon=sys.argv[1])
print('webview.start returned')
'''


def windows_of(pid, title=None):
    found = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def collect(hwnd, _):
        process = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process))
        if process.value == pid and user32.IsWindowVisible(hwnd):
            buffer = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buffer, 256)
            if title is None or buffer.value == title:
                found.append((hwnd, buffer.value))
        return True
    user32.EnumWindows(callback_type(collect), 0)
    return found


def kill(process):
    if process.poll() is None:
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=60)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass


def check_reproduces_027(python, png):
    step('0.27.0\'s call, webview.start(icon=PNG), with the archive\'s pywebview')
    with tempfile.TemporaryDirectory() as folder:
        log = Path(folder) / 'out.txt'
        with log.open('w', encoding='utf-8') as output:
            process = subprocess.Popen([str(python), '-I', '-c', REPRODUCE, str(png)], stdout=output,
                                       stderr=subprocess.STDOUT)
            deadline, seen = time.monotonic() + 90, []
            while time.monotonic() < deadline and process.poll() is None:
                seen = windows_of(process.pid, 'Corsu 0.27.0 icon') or seen
                time.sleep(0.5)
            alive = process.poll() is None
            kill(process)
        text = log.read_text(encoding='utf-8', errors='replace')
    print(text[-4000:])
    print(f'exit code {process.returncode}; still running after 90 s: {alive}; window seen: {bool(seen)}')
    assert not alive, '0.27.0\'s call did not end the program: this check no longer shows the 0.27.0 crash'
    assert 'webview.start returned' not in text, 'start(icon=PNG) returned normally'
    assert 'Icon' in text or process.returncode != 0, 'the program ended without the icon error'


def screenshot(hwnd, target):
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    script = ('Add-Type -AssemblyName System.Drawing; '
              f'$b = New-Object System.Drawing.Bitmap {width}, {height}; '
              '$g = [System.Drawing.Graphics]::FromImage($b); '
              f'$g.CopyFromScreen({rect.left}, {rect.top}, 0, 0, $b.Size); '
              f'$b.Save("{target}", [System.Drawing.Imaging.ImageFormat]::Png)')
    result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script], capture_output=True,
                            text=True, timeout=60)
    print(f'screenshot {target} ({width}x{height}): exit code {result.returncode} {result.stderr.strip()}')


def check_native_window(root, python):
    step('Corsu as its shortcut starts it: pythonw.exe src/app.py, no --browser')
    pythonw = python.with_name('pythonw.exe')
    assert pythonw.is_file(), f'missing {pythonw}'
    home = Path(tempfile.mkdtemp(prefix='corsu-window-'))
    env = {**os.environ, 'USERPROFILE': str(home), 'APPDATA': str(home / 'AppData/Roaming'),
           'LOCALAPPDATA': str(home / 'AppData/Local'), 'PYTHONUTF8': '1'}
    for name in ('APPDATA', 'LOCALAPPDATA'):
        Path(env[name]).mkdir(parents=True, exist_ok=True)
    data = Path(env['LOCALAPPDATA']) / 'corsu'
    artifacts = Path(os.environ.get('CORSU_E2E_ARTIFACTS') or tempfile.gettempdir())
    artifacts.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen([str(pythonw), str(root / 'src/app.py')], cwd=str(root), env=env)
    ok = False
    try:
        deadline, found = time.monotonic() + 120, []
        while time.monotonic() < deadline and process.poll() is None and not found:
            found = windows_of(process.pid, 'Corsu')
            time.sleep(0.5)
        assert process.poll() is None, f'Corsu ended before showing its window (exit code {process.returncode})'
        assert found, 'no visible top-level window titled "Corsu" of the process within 120 s'
        hwnd = found[0][0]
        print(f'window {hwnd:#x} titled {found[0][1]!r} of process {process.pid}, '
              f'{time.monotonic() - deadline + 120:.1f} s after start')
        # Time for the page to load and draw, and for a late crash to show.
        time.sleep(8)
        assert process.poll() is None, f'Corsu ended after showing its window (exit code {process.returncode})'
        assert user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd), 'the Corsu window went away'
        print(f'process {process.pid} still running 8 s later; window still visible')
        session = json.loads((data / 'setup-session.json').read_text(encoding='utf-8'))
        with urllib.request.urlopen(session['url'].replace('localhost', '127.0.0.1'), timeout=10) as response:
            print(f'local server {session["url"]}: HTTP {response.status}, {len(response.read())} bytes')
            assert response.status == 200
        big, small = (user32.SendMessageW(hwnd, 0x007F, kind, 0) for kind in (1, 0))  # WM_GETICON big, small
        print(f'window icons: big {big:#x}, small {small:#x}')
        assert big or small, 'the window has no icon'
        screenshot(hwnd, artifacts / 'windows-corsu-window.png')
        step('Closing the window (WM_CLOSE)')
        user32.PostMessageW(hwnd, 0x0010, 0, 0)
        try:
            # After its window closes Corsu waits CLOSED_IDLE_SECONDS (30 s) for nothing else to do, then ends.
            code = process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            raise AssertionError('Corsu did not end within 90 s of its window closing')
        print(f'Corsu ended by itself after its window closed, exit code {code}')
        assert code == 0, f'exit code {code}'
        ok = True
    finally:
        kill(process)
        log = data / 'logs/corsu.log'
        text = log.read_text(encoding='utf-8', errors='replace') if log.is_file() else '(no log)'
        print(f'\n-- {log}{"" if ok else " (failure)"}:\n' + (text[-3000:] if ok else text[-20000:]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--python', help='The archive\'s python.exe (default: runtime/x86_64/python/python.exe)')
    parser.add_argument('--skip-reproduce', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    python = archive_python(root, args.python)
    ico = check_ico(root)
    png = largest_png(root)
    check_dotnet(python, ico, png)
    if not args.skip_reproduce:
        check_reproduces_027(python, png)
    check_native_window(root, python)
    print('\nAll checks passed.')


if __name__ == '__main__':
    main()
