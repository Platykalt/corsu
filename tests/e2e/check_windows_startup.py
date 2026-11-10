"""Corsu starts on a real Windows (CI runner) whatever its window does, and a broken installation is repaired from a
newly downloaded archive without the Corsu window and without uninstalling.

A Windows user reported "Corsu no longer opens, no update was offered; it worked again after removing Corsu". Before
0.28.4 the window ran in Corsu's own process under pythonw.exe: a crash of the window engine (WebView2 through
pywebview's .NET thread) ended Corsu with its server, and any error at start was written to the log only, nothing on
screen. "Install for Windows.cmd" without options opened that same window, so a broken window also blocked a repair.

Usage: check_windows_startup.py --root EXTRACTED_RELEASE --archive corsu-windows.zip [--published 0.28.3]

In a throwaway user folder whose path has a space and accents (as many Windows user names do):
1. The published release (--published, downloaded and checked against its .sha256) is installed with 7-Zip and
   Minecraft; 7-Zip is switched off, the appearance and the auto_update preference are changed. Its Start menu
   shortcut's target is then started as a click does and shows the bugs: killing the window's process ends Corsu
   (nothing else opens), and with every port of Corsu taken it ends without a word on screen.
2. Repair: this archive (--archive) is extracted into a new folder and its "Install for Windows.cmd" is run without
   options while Corsu's ports are taken, so its window cannot start: the .cmd must fall back to the installer in
   text mode (answering "y"), which updates the installation. Then the extracted folder is deleted. The choices
   (switched-off 7-Zip, components), appearance, preferences and backups are those of before, and the shortcut
   points into %LOCALAPPDATA%\\corsu only.
3. The installed shortcut's target, after the archive is gone:
   - durable start: a visible window titled "Corsu" (from Corsu's window process), Corsu and that window still there
     75 s later, past window.LOAD_SECONDS (the page in the window redeemed its ticket, or the window would have been
     replaced), a screenshot that is not a blank window; closed with WM_CLOSE, Corsu ends by itself with code 0;
   - the window's process killed (as a crash of WebView2 or .NET would end it): Corsu keeps running, says so in its
     log, and opens its page in the browser (BROWSER, recorded) with a ticket of its own, which gets Corsu's key;
   - every port taken: a message box titled "Corsu" says why, where the log is and how to repair; once closed, Corsu
     ends with code 1.
Every wait is bounded; Corsu's log is printed at the end.
"""
import argparse
import contextlib
import ctypes
from ctypes import wintypes
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_windows_consoles import processes, published  # noqa: E402
from check_windows_window import kill, screenshot, step, user32, window_of_family, windows_of  # noqa: E402
from e2e import fake_prism_instance, isolated_environment  # noqa: E402

PORTS = range(7744, 7754)
WM_CLOSE = 0x0010
# The published copy's own modules, run from its installed release folder.
CUSTOMIZE = ('import sys; sys.path.insert(0, "src"); import appearance, update; settings = appearance.load(); '
             'settings.update(theme="dark", palette="notte"); appearance.save(settings); '
             'update.set_preference("auto_update", True)')
READ_LINK = ('[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; '
             '$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:CORSU_LINK); '
             '$s.TargetPath; $s.Arguments; $s.WorkingDirectory')
COLORS = ('Add-Type -AssemblyName System.Drawing; $b = [System.Drawing.Bitmap]::FromFile($env:CORSU_PNG); '
          '$c = @{}; for ($x = 0; $x -lt $b.Width; $x += 6) { for ($y = 0; $y -lt $b.Height; $y += 6) '
          '{ $c[$b.GetPixel($x, $y).ToArgb()] = 1 } }; $c.Count')

# Stands in for the browser (webbrowser reads BROWSER): writes the address Corsu opens, so the check can use it.
RECORD = 'import sys; open(sys.argv[1], "w", encoding="utf-8").write(sys.argv[2])'
CHILD_CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumChildWindows.argtypes = [wintypes.HWND, CHILD_CALLBACK, wintypes.LPARAM]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]


def class_name(hwnd):
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def dialog_text(hwnd):
    texts = []

    def collect(child, _):
        buffer = ctypes.create_unicode_buffer(4096)
        user32.GetWindowTextW(child, buffer, 4096)
        texts.append(buffer.value)
        return True
    user32.EnumChildWindows(hwnd, CHILD_CALLBACK(collect), 0)
    return '\n'.join(texts)


@contextlib.contextmanager
def ports_taken():
    """Every port Corsu may serve on, held by this process: Corsu cannot start its server."""
    held = []
    try:
        for port in PORTS:
            holder = socket.socket()
            # SO_REUSEADDR binds even while connections of a Corsu that just ended linger (TIME_WAIT); Corsu, which
            # asks for the port alone (SO_EXCLUSIVEADDRUSE), is still refused it.
            holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                holder.bind(('127.0.0.1', port))
            except OSError:
                holder.close()
                continue  # Held by another program already: Corsu cannot have it either.
            holder.listen()
            held.append(holder)
        yield
    finally:
        for holder in held:
            holder.close()


def shortcut(link):
    result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', READ_LINK], capture_output=True,
                            env={**os.environ, 'CORSU_LINK': str(link)}, timeout=120)
    target, arguments, folder = result.stdout.decode('utf-8').lstrip('﻿').splitlines()[:3]
    return target, arguments, folder


def start(link, environment):
    """Corsu as its Start menu shortcut starts it: its target and arguments, in its folder."""
    target, arguments, folder = shortcut(link)
    print(f'shortcut: "{target}" {arguments} (in {folder})')
    return subprocess.Popen(f'"{target}" {arguments}', cwd=folder, env=environment)


def log_text(data):
    log = data / 'logs/corsu.log'
    return log.read_text(encoding='utf-8', errors='replace') if log.is_file() else ''


def corsu_window(process, timeout=120):
    """(hwnd, owner pid) of Corsu's own window (not a message box), or (None, None)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and process.poll() is None:
        for hwnd, _, owner in window_of_family(process.pid):
            if class_name(hwnd) != '#32770':
                return hwnd, owner
        time.sleep(0.5)
    return None, None


def window_crash(link, environment, data, label):
    """Kill the window's process as a crash would end it. Returns (Corsu survived, address it opened in the browser,
    whether that page gets Corsu's key, Corsu's log since)."""
    step(f'{label}: the window\'s process killed, as a crash of its engine ends it')
    before = len(log_text(data))
    folder = Path(tempfile.mkdtemp(prefix='corsu-browser-'))
    record = folder / 'opened.txt'
    (folder / 'record.py').write_text(RECORD, encoding='utf-8')
    # webbrowser splits BROWSER as a POSIX command line: forward slashes, no spaces in these paths.
    browser = ' '.join(str(path).replace('\\', '/') for path in (sys.executable, folder / 'record.py', record))
    process = start(link, {**environment, 'BROWSER': browser + ' %s'})
    redeemed = False
    try:
        hwnd, owner = corsu_window(process)
        assert hwnd, f'{label}: no Corsu window within 120 s (code {process.poll()})'
        print(f'window {hwnd:#x} of process {owner} (Corsu {process.pid}); killing {owner}')
        subprocess.run(['taskkill', '/PID', str(owner), '/T', '/F'], capture_output=True, timeout=60)
        time.sleep(15)
        survived = process.poll() is None
        opened = record.read_text(encoding='utf-8') if record.is_file() else None
        if survived and opened and '#t=' in opened:
            # What the page in the browser does first: exchange its ticket for the key.
            port = int(opened.split('#')[0].rstrip('/').rsplit(':', 1)[1])
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
            connection.request('POST', '/api/key', body=json.dumps({'ticket': opened.split('#t=')[1]}),
                               headers={'Host': f'127.0.0.1:{port}', 'X-Corsu': '1', 'Content-Type': 'application/json',
                                        'Origin': f'http://127.0.0.1:{port}'})
            response = connection.getresponse()
            redeemed = response.status == 200 and bool(json.loads(response.read()).get('key'))
            connection.close()
        print(f'{label}: Corsu still running 15 s later: {survived} (code {process.returncode}); opened in the '
              f'browser: {opened or "nothing"}; that page gets the key: {redeemed}')
    finally:
        kill(process)
    tail = log_text(data)[before:]
    print(f'-- {label}, Corsu\'s log since start:\n{tail[-2500:]}')
    return survived, opened, redeemed, tail


def start_failure(link, environment, label):
    """Start Corsu with all its ports taken. Returns (exit code, text of a message box titled Corsu or None)."""
    step(f'{label}: every port of Corsu taken, started from its shortcut')
    text = None
    with ports_taken():
        process = start(link, environment)
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline and process.poll() is None and text is None:
                for hwnd, _ in windows_of(process.pid, 'Corsu'):
                    if class_name(hwnd) == '#32770':
                        text = dialog_text(hwnd)
                        print(f'{label}: message box:\n{text}')
                        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                time.sleep(0.5)
            code = process.wait(timeout=60)
        finally:
            kill(process)
    print(f'{label}: Corsu ended with code {code}; message box shown: {text is not None}')
    return code, text


def kept(data):
    """What a repair or update must keep."""
    state = json.loads((data / 'installation.json').read_text(encoding='utf-8'))
    backups = data / 'backups'
    return {'components': sorted(state.get('components', [])), 'disabled': sorted(state.get('disabled', [])),
            'appearance': json.loads((data / 'appearance/settings.json').read_text(encoding='utf-8')),
            'preferences': json.loads((data / 'preferences.json').read_text(encoding='utf-8')),
            'backups': sorted(str(path.relative_to(backups)) for path in backups.rglob('*') if path.is_file())
            if backups.is_dir() else []}


def run(command, environment, cwd, **options):
    print('+ ' + ' '.join(map(str, command)), flush=True)
    result = subprocess.run(command, cwd=cwd, env=environment, capture_output=True, timeout=900, **options)
    text = (result.stdout or b'').decode('utf-8', errors='replace') + (result.stderr or b'').decode('utf-8', errors='replace')
    print(text[-4000:])
    return result.returncode, text


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--root', type=Path, required=True, help='This release, extracted (for its version)')
    parser.add_argument('--archive', type=Path, required=True, help='This release\'s corsu-windows.zip')
    parser.add_argument('--published', default='0.28.3')
    args = parser.parse_args()
    version = json.loads((args.root / 'src/release.json').read_text(encoding='utf-8'))['version']
    # A user folder as many people have: a space and accented letters in its path.
    home = Path(tempfile.mkdtemp(prefix='corsu startup Pàulu Còrsu '))
    environment = {**isolated_environment(home), 'PYTHONUTF8': '1'}
    data = Path(environment['LOCALAPPDATA']) / 'corsu'
    link = Path(environment['APPDATA']) / 'Microsoft/Windows/Start Menu/Programs/Corsu.lnk'
    failures = []
    try:
        step(f'Published {args.published} installed in {home}')
        old = published(args.published, Path(tempfile.mkdtemp(prefix='corsu-published-')))
        old_python = old / 'runtime/x86_64/python/python.exe'
        fake_prism_instance(home, (old / 'minecraft/java/VERSION').read_text(encoding='utf-8').strip())
        code, _ = run([str(old_python), 'src/installer.py', '--components', 'minecraft', '7zip', '--yes'], environment, old)
        assert code == 0, f'installing {args.published} failed ({code})'
        assert run([str(old_python), 'src/installer.py', '--disable', '7zip'], environment, old)[0] == 0
        target, arguments, folder = shortcut(link)
        assert run([str(old_python), '-c', CUSTOMIZE], environment, folder)[0] == 0
        before = kept(data)
        print(f'kept before the repair: {json.dumps(before, ensure_ascii=False)}')
        assert before['disabled'] == ['7zip'], before

        survived, opened, _, _ = window_crash(link, environment, data, f'Published {args.published}')
        print(f'Published {args.published}: Corsu ended with its window, nothing opened instead: '
              f'{not survived and not opened} (the bug this check guards against)')
        if survived or opened:
            failures.append(f'published {args.published} survived its window: this check no longer shows the bug')
        code, text = start_failure(link, environment, f'Published {args.published}')
        print(f'Published {args.published}: ended without a word on screen: {text is None} (code {code})')
        if text is not None:
            failures.append(f'published {args.published} showed a message: this check no longer shows the bug')

        step(f'Repair: this archive ({version}) extracted, its "Install for Windows.cmd" run without options while '
             'Corsu\'s window cannot start')
        download = Path(tempfile.mkdtemp(prefix='téléchargement Corsu '))
        with zipfile.ZipFile(args.archive) as archive:
            archive.extractall(download)
        command = download / 'corsu/Install for Windows.cmd'
        with ports_taken():
            code, text = run(['cmd', '/c', str(command)], {**environment, 'CI': 'true'}, download, input=b'y\n')
        if 'The Corsu window could not open' not in text:
            failures.append('the .cmd did not fall back to the text installer when the window could not start')
        if f'updating it to {version}' not in text:
            failures.append(f'the .cmd\'s text installer did not update {args.published} to {version}')
        shutil.rmtree(download)
        print(f'{download} deleted')
        after = kept(data)
        print(f'kept after the repair: {json.dumps(after, ensure_ascii=False)}')
        # An update may add preferences and backups of its own; what was there stays as it was.
        changed = [name for name in ('components', 'disabled', 'appearance') if after[name] != before[name]]
        changed += [f'preference {name}' for name, value in before['preferences'].items()
                    if after['preferences'].get(name) != value]
        changed += [f'backup {name}' for name in before['backups'] if name not in after['backups']]
        if changed:
            failures.append(f'the repair changed what it must keep: {", ".join(changed)}')
        target, arguments, folder = shortcut(link)
        app = Path(arguments.strip().strip('"'))
        installed = json.loads((app.parent / 'release.json').read_text(encoding='utf-8'))['version']
        print(f'shortcut after the repair: "{target}" {arguments}; release {installed}')
        # Resolved: a temporary folder may be given in its short 8.3 form (RUNNER~1).
        if not all(Path(path).resolve().is_relative_to(data.resolve()) for path in (target, app, folder)):
            failures.append(f'the shortcut points outside {data}: {target} {arguments} {folder}')
        if installed != version:
            failures.append(f'the shortcut starts {installed}, not {version}')

        step(f'{version} from its shortcut, the archive deleted: a lasting window with its page')
        process = start(link, environment)
        try:
            hwnd, owner = corsu_window(process)
            assert hwnd, f'no Corsu window within 120 s (code {process.poll()})'
            print(f'window {hwnd:#x} of process {owner} (Corsu {process.pid})')
            time.sleep(75)
            alive = process.poll() is None and owner in processes()
            shown = bool(user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd))
            loaded = 'did not load' not in log_text(data)
            picture = Path(os.environ.get('CORSU_E2E_ARTIFACTS') or tempfile.gettempdir()) / 'windows-startup-window.png'
            picture.parent.mkdir(parents=True, exist_ok=True)
            screenshot(hwnd, picture)
            colors = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', COLORS],
                                    capture_output=True, text=True, env={**os.environ, 'CORSU_PNG': str(picture)},
                                    timeout=120).stdout.strip()
            print(f'75 s later: Corsu and its window process running: {alive}; window visible: {shown}; page loaded '
                  f'in the window (not replaced by the browser): {loaded}; colours in the screenshot: {colors}')
            if not (alive and shown and loaded and colors.isdigit() and int(colors) > 20):
                failures.append('the window did not last with its page')
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            code = process.wait(timeout=90)
            print(f'closed with WM_CLOSE: Corsu ended by itself, code {code}')
            if code != 0:
                failures.append(f'Corsu ended with code {code} after its window was closed')
        finally:
            kill(process)

        survived, opened, redeemed, tail = window_crash(link, environment, data, version)
        if not (survived and redeemed and "Corsu's window stopped" in tail):
            failures.append('a crashed window did not leave Corsu running with its page in the browser')

        code, text = start_failure(link, environment, version)
        if code != 1 or not text or r'logs\corsu.log' not in text or 'Install for Windows.cmd' not in text:
            failures.append(f'a start failure did not show its message box (code {code}, text {text!r})')
    finally:
        log = log_text(data)
        print(f'\n-- {data / "logs/corsu.log"} (end):\n{log[-6000:]}')
    if failures:
        raise SystemExit('FAILED:\n- ' + '\n- '.join(failures))
    print('\nAll checks passed.')


if __name__ == '__main__':
    main()
