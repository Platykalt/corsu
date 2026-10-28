"""No console window flashes while Corsu's window is open on Windows (CI runner), from the extracted release archive.

Corsu's window runs under pythonw.exe, which has no console. Every console program it starts (powershell, tasklist…)
without CREATE_NO_WINDOW gets a console of its own, shown for as long as it runs: people saw PowerShell windows open
and close the whole time the window was open (0.28.2), from the process list read for the window's refreshes.

Usage: check_windows_consoles.py --root EXTRACTED_RELEASE [--python ARCHIVE_PYTHON] [--seconds 40]
                                 [--published 0.28.2]

For the archive given (expected: no console window), and with --published for that published release, downloaded
and checked against its .sha256 (expected: console windows, so the check is shown to see the bug):
1. A throwaway user folder with a Minecraft (Prism Launcher) instance; Corsu installs Minecraft and 7-Zip from the
   archive with the archive's Python. Then a second game folder appears (the window looks for new ones) and a
   WinMerge folder with its Corsican file (a program the window finds and checks for running).
2. Corsu is started from the Start menu shortcut the installer wrote (Corsu.lnk, opened through the shell as a click
   does): its page polls /api/state every 1.5 s. Watched while idle (--seconds, at least 10 refreshes), then while
   the page's own calls run: 7-Zip switched off and on again (/api/switch, the installer under pythonw.exe), an
   update check (/api/update/check), the plan of an installation (/api/plan), then idle again.
3. While it runs: every process created under Corsu (process list read every 10 ms, command line read at once,
   parents kept after a process ends; conhost.exe under a program means a console was given to it), and every
   window shown on the desktop as it is shown (SetWinEventHook EVENT_OBJECT_SHOW, out of context: an event per
   window, however briefly it lives, no polling).
4. A console window is: a window of a console program under Corsu, or a console or Windows Terminal window
   (which belongs to WindowsTerminal.exe where Terminal hosts new consoles, as on the Windows Server 2025 runner)
   shown within 2 s of a console program Corsu started. Also fails when Corsu started no console program at all
   (the check would then prove nothing). Prints each program started under Corsu: command line, parent, how often.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_windows_window import archive_python, step, windows_of  # noqa: E402
from e2e import fake_prism_instance, isolated_environment  # noqa: E402

RELEASES = 'https://github.com/Platykalt/corsu/releases/download'
# Console programs Corsu (or a library) may start; a window of one of them shown is a flash.
CONSOLE_PROGRAMS = {'powershell.exe', 'pwsh.exe', 'cmd.exe', 'conhost.exe', 'openconsole.exe', 'tasklist.exe',
                    'wmic.exe', 'reg.exe', 'where.exe', 'taskkill.exe', 'python.exe', 'git.exe', 'node.exe'}
CONSOLE_CLASSES = {'ConsoleWindowClass', 'CASCADIA_HOSTING_WINDOW_CLASS', 'PseudoConsoleWindow'}

if sys.platform == 'win32':
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    ntdll = ctypes.WinDLL('ntdll')

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD), ('th32ProcessID', wintypes.DWORD),
                    ('th32DefaultHeapID', ctypes.c_size_t), ('th32ModuleID', wintypes.DWORD),
                    ('cntThreads', wintypes.DWORD), ('th32ParentProcessID', wintypes.DWORD),
                    ('pcPriClassBase', ctypes.c_long), ('dwFlags', wintypes.DWORD), ('szExeFile', ctypes.c_wchar * 260)]

    class UNICODE_STRING(ctypes.Structure):
        _fields_ = [('Length', wintypes.USHORT), ('MaximumLength', wintypes.USHORT), ('Buffer', ctypes.c_void_p)]

    WINEVENTPROC = ctypes.WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND, wintypes.LONG,
                                      wintypes.LONG, wintypes.DWORD, wintypes.DWORD)
    kernel32.CreateToolhelp32Snapshot.argtypes, kernel32.CreateToolhelp32Snapshot.restype = [wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.OpenProcess.argtypes, kernel32.OpenProcess.restype = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    ntdll.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.ULONG,
                                                ctypes.POINTER(wintypes.ULONG)]
    ntdll.NtQueryInformationProcess.restype = ctypes.c_long
    user32.SetWinEventHook.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.HMODULE, WINEVENTPROC, wintypes.DWORD,
                                       wintypes.DWORD, wintypes.DWORD]
    user32.SetWinEventHook.restype = wintypes.HANDLE
    user32.UnhookWinEvent.argtypes = [wintypes.HANDLE]
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetAncestor.argtypes, user32.GetAncestor.restype = [wintypes.HWND, wintypes.UINT], wintypes.HWND
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

EVENT_OBJECT_SHOW, WINEVENT_OUTOFCONTEXT, WINEVENT_SKIPOWNPROCESS, WM_QUIT = 0x8002, 0x0000, 0x0002, 0x0012


def processes():
    """{pid: (parent pid, executable name)} of every process now."""
    found = {}
    snapshot = kernel32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if snapshot in (None, ctypes.c_void_p(-1).value):
        return found
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            found[entry.th32ProcessID] = (entry.th32ParentProcessID, entry.szExeFile)
            ok = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return found


def command_line(pid):
    """The command line of a running process (ProcessCommandLineInformation), or '' when it cannot be read."""
    handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ''
    try:
        buffer = ctypes.create_string_buffer(65536)
        size = wintypes.ULONG()
        if ntdll.NtQueryInformationProcess(handle, 60, buffer, len(buffer), ctypes.byref(size)) != 0:
            return ''
        text = UNICODE_STRING.from_buffer(buffer)
        return ctypes.wstring_at(text.Buffer, text.Length // 2) if text.Buffer else ''
    finally:
        kernel32.CloseHandle(handle)


class Monitor:
    """New processes (traced from the process list every 10 ms) and windows shown (WinEvent hook)."""

    def __init__(self):
        self.root = None
        self.start = time.monotonic()
        self.lock = threading.Lock()
        self.known = {}      # pid -> (parent pid, name, seconds since start, command line)
        self.before = set(processes())
        self.shown = []      # (seconds, class, title, pid)
        self.marks = []      # (seconds, what the test did)
        self.stopping = False

    def mark(self, text):
        when = time.monotonic() - self.start
        self.marks.append((when, text))
        print(f'{when:6.1f} s  {text}', flush=True)

    def chain(self, pid):
        """Names from pid up to the root, or None when pid does not descend from the root."""
        names, seen = [], set()
        while pid and pid not in seen and self.root:
            seen.add(pid)
            if pid == self.root:
                return names + ['(Corsu)']
            entry = self.known.get(pid)
            if not entry:
                return None
            names.append(entry[1])
            pid = entry[0]
        return None

    def refresh(self):
        now = processes()
        with self.lock:
            # A process older than the watch that ended frees its id for a new one.
            self.before &= set(now)
            for pid, (parent, name) in now.items():
                if pid not in self.known and pid not in self.before:
                    self.known[pid] = (parent, name, time.monotonic() - self.start, command_line(pid))

    def trace(self):
        while not self.stopping:
            self.refresh()
            time.sleep(0.01)

    def hook(self):
        self.thread_id = kernel32.GetCurrentThreadId()

        def shown(hook, event, hwnd, object_id, child_id, thread, when):
            if object_id != 0 or child_id != 0 or not hwnd or user32.GetAncestor(hwnd, 2) != hwnd:  # GA_ROOT
                return
            name, title, pid = ctypes.create_unicode_buffer(256), ctypes.create_unicode_buffer(256), wintypes.DWORD()
            user32.GetClassNameW(hwnd, name, 256)
            user32.GetWindowTextW(hwnd, title, 256)
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            # The process may end at once: read the process list now, so its parents are known.
            self.refresh()
            with self.lock:
                self.shown.append((time.monotonic() - self.start, name.value, title.value, pid.value))

        self.callback = WINEVENTPROC(shown)
        handle = user32.SetWinEventHook(EVENT_OBJECT_SHOW, EVENT_OBJECT_SHOW, None, self.callback, 0, 0,
                                        WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS)
        assert handle, f'SetWinEventHook failed ({ctypes.get_last_error()})'
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            pass
        user32.UnhookWinEvent(handle)

    def __enter__(self):
        self.tracer = threading.Thread(target=self.trace, daemon=True)
        self.tracer.start()
        self.hook_thread = threading.Thread(target=self.hook, daemon=True)
        self.hook_thread.start()
        time.sleep(0.5)
        return self

    def __exit__(self, *_):
        self.stopping = True
        user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
        self.tracer.join(5)
        self.hook_thread.join(5)

    def children(self):
        """[(seconds, name, parent name, command line)] of every process created under the root."""
        with self.lock:
            return sorted((entry[2], entry[1], (self.known.get(entry[0]) or (0, '(Corsu)'))[1], entry[3])
                          for pid, entry in self.known.items() if self.chain(pid) is not None)


def published(version, folder):
    """The published Windows archive of `version`, checked against its .sha256 and extracted: its root."""
    folder.mkdir(parents=True, exist_ok=True)
    for name in ('corsu-windows.zip', 'corsu-windows.zip.sha256'):
        request = urllib.request.Request(f'{RELEASES}/v{version}/{name}', headers={'User-Agent': 'corsu-e2e'})
        with urllib.request.urlopen(request, timeout=300) as response:
            (folder / name).write_bytes(response.read())
    expected = (folder / 'corsu-windows.zip.sha256').read_text(encoding='utf-8').split()[0].lower()
    actual = hashlib.sha256((folder / 'corsu-windows.zip').read_bytes()).hexdigest()
    assert actual == expected, f'published {version} archive: checksum {actual} is not {expected}'
    print(f'published {version} archive checked: sha256 {actual}')
    with zipfile.ZipFile(folder / 'corsu-windows.zip') as archive:
        archive.extractall(folder / 'extracted')
    return folder / 'extracted/corsu'


def prepare(root, python, home, environment):
    step(f'A throwaway user folder; Corsu installs Minecraft and 7-Zip from {root}')
    version = (root / 'minecraft/java/VERSION').read_text(encoding='utf-8').strip()
    fake_prism_instance(home, version)
    command = [str(python), 'src/installer.py', '--components', 'minecraft', '7zip', '--yes']
    print('+ ' + ' '.join(command), flush=True)
    result = subprocess.run(command, cwd=root, env=environment, text=True, encoding='utf-8', errors='replace')
    assert result.returncode == 0, f'installation failed ({result.returncode})'
    # A game folder created since: the window looks for new ones (and whether Minecraft runs there).
    added = home / 'AppData/Roaming/PrismLauncher/instances' / version
    shutil.move(str(added), str(added.with_name(version + ' (2)')))
    fake_prism_instance(home, version)
    # A program the window finds and checks for running (WinMerge rewrites its settings when it quits).
    winmerge = home / 'AppData/Local/Programs/WinMerge'
    (winmerge / 'Languages').mkdir(parents=True)
    (winmerge / 'WinMergeU.exe').write_bytes(b'')
    (winmerge / 'Languages/Corsican.po').write_text('msgid ""\nmsgstr ""\n', encoding='utf-8')
    link = Path(environment['APPDATA']) / 'Microsoft/Windows/Start Menu/Programs/Corsu.lnk'
    assert link.is_file(), f'the installer wrote no Start menu shortcut at {link}'
    return link


def api(session, path, body=None, timeout=10):
    """Corsu's answer to `path`, called as its page does (X-Corsu, the window's key)."""
    address = urllib.parse.urlsplit(session['url'])
    connection = http.client.HTTPConnection('127.0.0.1', address.port, timeout=timeout)
    headers = {'X-Corsu': '1', 'X-Corsu-Key': session['key'], 'Host': f'127.0.0.1:{address.port}'}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    try:
        connection.request('POST' if body is not None else 'GET', path,
                           body=json.dumps({'language': 'en', **body}).encode() if body is not None else None,
                           headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read() or b'null')
    finally:
        connection.close()


def wait_job(monitor, session, what, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status, state = api(session, '/api/state')
        job = state['job']
        if not job['running']:
            monitor.mark(f'{what}: done, ok={job["ok"]}; last lines: {job["lines"][-2:]}')
            assert job['ok'], f'{what} failed: {job["lines"][-10:]}'
            return state
        time.sleep(0.5)
    raise AssertionError(f'{what}: still running after {timeout} s')


def observe(link, environment, seconds):
    step(f'Corsu opened from its Start menu shortcut ({link.name}), watched idle {seconds} s, through its page\'s '
         'calls, then idle again')
    data = Path(environment['LOCALAPPDATA']) / 'corsu'
    saved = dict(os.environ)
    with Monitor() as monitor:
        # The shell opens the shortcut as a click does, with this (throwaway) user's folders.
        os.environ.update(environment)
        try:
            os.startfile(str(link))  # noqa: S606
        finally:
            os.environ.clear()
            os.environ.update(saved)
        monitor.mark('shortcut opened')
        deadline, found = time.monotonic() + 120, []
        while time.monotonic() < deadline and not found:
            with monitor.lock:
                candidates = [pid for pid, entry in monitor.known.items() if entry[1].lower() == 'pythonw.exe']
            for pid in candidates:
                found = windows_of(pid, 'Corsu')
                if found:
                    monitor.root = pid
                    break
            time.sleep(0.5)
        assert found, 'no Corsu window from the shortcut within 120 s'
        print(f'Corsu: pythonw.exe pid {monitor.root}, {monitor.known[monitor.root][3]}')
        process = None
        try:
            monitor.mark('window shown')
            session = json.loads((data / 'setup-session.json').read_text(encoding='utf-8'))
            time.sleep(seconds)
            monitor.mark(f'idle {seconds} s ({int(seconds / 1.5)} refreshes of the page)')
            status, state = api(session, '/api/state')
            assert status == 200, status
            print('parts: ' + ', '.join(f'{item["name"]}={"on" if item["on"] else "off"}' for item in state['items']
                                        if item['installed']))
            for on in (False, True):
                monitor.mark(f'/api/switch 7zip on={on}')
                status, answer = api(session, '/api/switch', {'components': ['7zip'], 'on': on})
                assert status == 200 and answer.get('started'), (status, answer)
                wait_job(monitor, session, f'switch 7zip on={on}')
                time.sleep(5)
            monitor.mark('/api/update/check')
            assert api(session, '/api/update/check', {})[0] == 200
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline and api(session, '/api/state')[1]['update']['checking']:
                time.sleep(0.5)
            update = api(session, '/api/state')[1]['update']
            monitor.mark(f'update check done: status {update["status"]}, latest {update["latest"]}, error {update["error"]}')
            monitor.mark('/api/plan minecraft')
            status, plan = api(session, '/api/plan', {'components': ['minecraft']}, timeout=120)
            monitor.mark(f'plan: HTTP {status}, ok={plan.get("ok")}')
            time.sleep(seconds / 2)
            monitor.mark(f'idle {seconds / 2:.0f} s more')
            user32.PostMessageW(found[0][0], 0x0010, 0, 0)  # WM_CLOSE
            monitor.mark('WM_CLOSE sent to the window')
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline and monitor.root in processes():
                time.sleep(0.5)
            monitor.mark('Corsu ended' if monitor.root not in processes() else 'Corsu still running after 90 s')
        finally:
            if monitor.root in processes():
                subprocess.run(['taskkill', '/PID', str(monitor.root), '/T', '/F'], capture_output=True, timeout=60)
            log = data / 'logs/corsu.log'
            if log.is_file():
                print('\n-- corsu.log (end):\n' + log.read_text(encoding='utf-8', errors='replace')[-2500:])
    return monitor


def shorten(command):
    """A command line without the throwaway folder's random part, cut to a readable length."""
    command = re.sub(r'corsu-consoles-\w+', 'corsu-consoles-…', command)
    return command if len(command) <= 240 else command[:237] + '…'


def report(monitor, label):
    step(f'{label}: programs started under Corsu')
    children = monitor.children()
    counts = {}
    for when, name, parent, command in children:
        entry = counts.setdefault((name.lower(), parent.lower(), shorten(command)), [0, when, when])
        entry[0] += 1
        entry[2] = when
    for (name, parent, command), (count, first, last) in sorted(counts.items(), key=lambda item: item[1][1]):
        print(f'x{count:<3} {name} (parent {parent}) first {first:.1f} s, last {last:.1f} s: {command}')
    consoles = [child for child in children if child[1].lower() in CONSOLE_PROGRAMS - {'conhost.exe', 'python.exe'}]
    step(f'{label}: windows shown on the desktop while Corsu ran')
    flashes = []
    started = [when for when, *_ in consoles]
    for when, name, title, pid in monitor.shown:
        chain = monitor.chain(pid)
        mine = chain is not None
        program = chain[0].lower() if chain else ''
        # Where Windows Terminal hosts new consoles (Windows 11, Server 2025), the window shown belongs to
        # WindowsTerminal.exe, not to a process under Corsu: a console window shown within 2 s of a console program
        # Corsu started counts as that program's.
        after = mine or any(0 <= when - start <= 2.0 for start in started)
        print(f'{when:6.1f} s  class {name!r} title {title!r} pid {pid} '
              + (f'under Corsu: {" < ".join(chain)}' if mine else 'not under Corsu')
              + (' (just after a console program Corsu started)' if not mine and after and name in CONSOLE_CLASSES else ''))
        if (mine and program in CONSOLE_PROGRAMS) or (after and name in CONSOLE_CLASSES):
            flashes.append((when, name, title, chain or ['(console host)']))
    hosts = sum(1 for child in children if child[1].lower() == 'conhost.exe')
    print(f'\n{label}: {len(children)} processes started under Corsu, {len(consoles)} of them console programs, '
          f'{hosts} conhost.exe; {len(flashes)} console windows shown')
    for when, name, title, chain in flashes:
        print(f'FLASH at {when:.1f} s: {name} {title!r} of {" < ".join(chain)}')
    assert consoles, f'{label}: Corsu started no console program while watched: this check would prove nothing'
    return flashes


def scenario(root, python, label, seconds):
    home = Path(tempfile.mkdtemp(prefix='corsu-consoles-'))
    environment = {**isolated_environment(home), 'PYTHONUTF8': '1'}
    link = prepare(root, python, home, environment)
    flashes = report(observe(link, environment, seconds), label)
    # Leave the runner's registry as it was (7-Zip's language).
    subprocess.run([str(python), str(sorted((Path(environment['LOCALAPPDATA']) / 'corsu/releases').glob('*/src/installer.py'))[-1]),
                    '--uninstall', '--yes'], env=environment, capture_output=True, text=True, timeout=300)
    return flashes


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--python', help='The archive\'s python.exe (default: runtime/x86_64/python/python.exe)')
    parser.add_argument('--seconds', type=int, default=40)
    parser.add_argument('--published', help='Also a published release (e.g. 0.28.2), expected to show console windows')
    args = parser.parse_args()
    assert sys.platform == 'win32', 'Windows only'
    failures = []
    if args.published:
        old = published(args.published, Path(tempfile.mkdtemp(prefix='corsu-published-')))
        flashes = scenario(old, archive_python(old, None), f'published {args.published}', args.seconds)
        if flashes:
            print(f'\nAS EXPECTED: published {args.published} shows {len(flashes)} console windows')
        else:
            failures.append(f'published {args.published} showed no console window: the check does not see the bug')
    root = args.root.resolve()
    flashes = scenario(root, archive_python(root, args.python), 'this archive', args.seconds)
    if flashes:
        failures.append(f'this archive: {len(flashes)} console windows shown while Corsu\'s window was open')
    print()
    for failure in failures:
        print('FAIL ' + failure)
    assert not failures, failures
    print('No console window shown by this archive.')


if __name__ == '__main__':
    main()
