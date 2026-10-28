"""No console window flashes while Corsu's window is open on Windows (CI runner), from the extracted release archive.

Corsu's window runs under pythonw.exe, which has no console. Every console program it starts (powershell, tasklist…)
without CREATE_NO_WINDOW gets a console of its own, shown for as long as it runs: people saw PowerShell windows open
and close the whole time the window was open (0.28.2), from the process list read for the window's refreshes.

Usage: check_windows_consoles.py --root EXTRACTED_RELEASE [--python ARCHIVE_PYTHON] [--seconds 75]

1. A throwaway user folder with a Minecraft (Prism Launcher) instance; Corsu installs Minecraft from the archive with
   the archive's Python. A second instance is added afterwards (a new game folder the window looks for), and a
   WinMerge folder with its Corsican file (a program the window finds and checks for running).
2. Corsu as its shortcut starts it (pythonw.exe src/app.py): its page polls /api/state every 1.5 s.
3. While it runs: every process created under Corsu's pythonw.exe is traced (process list read every 10 ms, parents
   kept after a process ends), and every window shown on the desktop is caught as it is shown (SetWinEventHook,
   EVENT_OBJECT_SHOW, out of context: an event per window, however briefly it lives, no polling).
4. Fails when a console window (ConsoleWindowClass, or any window of a console program) of a process under Corsu is
   shown; also fails when Corsu started no console program at all (the check would then prove nothing). Prints each
   program started under Corsu with its parent and how often.
"""
import argparse
import ctypes
from ctypes import wintypes
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_windows_window import archive_python, kill, step, windows_of  # noqa: E402
from e2e import fake_prism_instance, isolated_environment  # noqa: E402

# Console programs Corsu (or a library) may start; a window of one of them shown is a flash.
CONSOLE_PROGRAMS = {'powershell.exe', 'pwsh.exe', 'cmd.exe', 'conhost.exe', 'openconsole.exe', 'tasklist.exe',
                    'wmic.exe', 'reg.exe', 'where.exe', 'taskkill.exe', 'python.exe', 'git.exe', 'node.exe'}
CONSOLE_CLASSES = {'ConsoleWindowClass', 'CASCADIA_HOSTING_WINDOW_CLASS', 'PseudoConsoleWindow'}

if sys.platform == 'win32':
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    user32 = ctypes.WinDLL('user32', use_last_error=True)

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD), ('th32ProcessID', wintypes.DWORD),
                    ('th32DefaultHeapID', ctypes.c_size_t), ('th32ModuleID', wintypes.DWORD),
                    ('cntThreads', wintypes.DWORD), ('th32ParentProcessID', wintypes.DWORD),
                    ('pcPriClassBase', ctypes.c_long), ('dwFlags', wintypes.DWORD), ('szExeFile', ctypes.c_wchar * 260)]

    WINEVENTPROC = ctypes.WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND, wintypes.LONG,
                                      wintypes.LONG, wintypes.DWORD, wintypes.DWORD)
    kernel32.CreateToolhelp32Snapshot.argtypes, kernel32.CreateToolhelp32Snapshot.restype = [wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
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


class Monitor:
    """Processes created under `root` (traced from the process list every 10 ms) and windows shown (WinEvent hook)."""

    def __init__(self):
        self.root = None
        self.start = time.monotonic()
        self.lock = threading.Lock()
        self.known = {}      # pid -> (parent pid, name, first seen, seconds since start)
        self.before = set(processes())
        self.shown = []      # (seconds, class, title, pid, chain of names up to the root or None)
        self.stopping = False
        self.hook_thread = None

    def chain(self, pid):
        """Names from pid up to the root, or None when pid does not descend from the root."""
        names, seen = [], set()
        while pid and pid not in seen:
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
                    self.known[pid] = (parent, name, time.monotonic() - self.start)

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
                self.shown.append((time.monotonic() - self.start, name.value, title.value, pid.value, self.chain(pid.value)))

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
        """[(seconds, name, parent name)] of every process created under the root."""
        with self.lock:
            return sorted((entry[2], entry[1], (self.known.get(entry[0]) or (0, '(Corsu)'))[1])
                          for pid, entry in self.known.items() if self.chain(pid) is not None)


def prepare(root, python, home, environment):
    step('A throwaway user folder: a Minecraft instance, Corsu installs Minecraft from the archive')
    version = (root / 'minecraft/java/VERSION').read_text(encoding='utf-8').strip()
    fake_prism_instance(home, version)
    command = [str(python), 'src/installer.py', '--components', 'minecraft', '--yes']
    print('+ ' + ' '.join(command), flush=True)
    result = subprocess.run(command, cwd=root, env=environment, text=True, encoding='utf-8', errors='replace')
    assert result.returncode == 0, f'installation failed ({result.returncode})'
    # A game folder created since: the window looks for it (and whether Minecraft runs there).
    added = home / 'AppData/Roaming/PrismLauncher/instances' / version
    shutil.move(str(added), str(added.with_name(version + ' (2)')))
    fake_prism_instance(home, version)
    # A program the window finds and checks for running (WinMerge rewrites its settings when it quits).
    winmerge = home / 'AppData/Local/Programs/WinMerge'
    (winmerge / 'Languages').mkdir(parents=True)
    (winmerge / 'WinMergeU.exe').write_bytes(b'')
    (winmerge / 'Languages/Corsican.po').write_text('msgid ""\nmsgstr ""\n', encoding='utf-8')


def observe(root, python, environment, seconds):
    step(f'Corsu as its shortcut starts it (pythonw.exe src/app.py), watched for {seconds} s')
    pythonw = python.with_name('pythonw.exe')
    assert pythonw.is_file(), f'missing {pythonw}'
    data = Path(environment['LOCALAPPDATA']) / 'corsu'
    with Monitor() as monitor:
        process = subprocess.Popen([str(pythonw), str(root / 'src/app.py')], cwd=str(root), env=environment)
        monitor.root = process.pid
        try:
            deadline, found = time.monotonic() + 120, []
            while time.monotonic() < deadline and process.poll() is None and not found:
                found = windows_of(process.pid, 'Corsu')
                time.sleep(0.5)
            assert found, f'no Corsu window within 120 s (exit code {process.poll()})'
            print(f'window shown {time.monotonic() - monitor.start:.1f} s after start; watching {seconds} s more', flush=True)
            time.sleep(seconds)
            assert process.poll() is None, f'Corsu ended while watched (exit code {process.returncode})'
            user32.PostMessageW(found[0][0], 0x0010, 0, 0)  # WM_CLOSE
            try:
                process.wait(timeout=90)
            except subprocess.TimeoutExpired:
                pass
        finally:
            kill(process)
            log = data / 'logs/corsu.log'
            if log.is_file():
                print('\n-- corsu.log (end):\n' + log.read_text(encoding='utf-8', errors='replace')[-3000:])
    return monitor


def report(monitor):
    step('Programs started under Corsu')
    children = monitor.children()
    counts = {}
    for when, name, parent in children:
        entry = counts.setdefault((name.lower(), parent.lower()), [0, when, when])
        entry[0] += 1
        entry[2] = when
    for (name, parent), (count, first, last) in sorted(counts.items()):
        print(f'{name:28} parent {parent:22} x{count:<4} first {first:6.1f} s, last {last:6.1f} s')
    consoles = [child for child in children if child[1].lower() in CONSOLE_PROGRAMS - {'conhost.exe', 'python.exe'}]
    step('Windows shown on the desktop while Corsu ran')
    flashes = []
    for when, name, title, pid, chain in monitor.shown:
        mine = chain is not None
        print(f'{when:6.1f} s  class {name!r} title {title!r} pid {pid} '
              + (f'under Corsu: {" < ".join(chain)}' if mine else 'not under Corsu'))
        program = chain[0].lower() if chain else ''
        if mine and (name in CONSOLE_CLASSES or program in CONSOLE_PROGRAMS):
            flashes.append((when, name, title, chain))
    print(f'\n{len(children)} processes started under Corsu, {len(consoles)} of them console programs; '
          f'{len(flashes)} console windows shown')
    for when, name, title, chain in flashes:
        print(f'FLASH at {when:.1f} s: {name} {title!r} of {" < ".join(chain)}')
    assert consoles, 'Corsu started no console program while watched: this check would prove nothing'
    assert not flashes, f'{len(flashes)} console windows shown while Corsu\'s window was open'


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--python', help='The archive\'s python.exe (default: runtime/x86_64/python/python.exe)')
    parser.add_argument('--seconds', type=int, default=75)
    args = parser.parse_args()
    assert sys.platform == 'win32', 'Windows only'
    root = args.root.resolve()
    python = archive_python(root, args.python)
    home = Path(tempfile.mkdtemp(prefix='corsu-consoles-'))
    environment = {**isolated_environment(home), 'PYTHONUTF8': '1'}
    prepare(root, python, home, environment)
    report(observe(root, python, environment, args.seconds))
    print('\nNo console window shown.')


if __name__ == '__main__':
    main()
