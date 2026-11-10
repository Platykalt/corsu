"""Corsu's own window: the app page in a window with Corsu's name and icon, not a browser tab.

The first that works is used: pywebview (bundled with the standalone Corsu programs, using the web engine of the
system: WebView2 on Windows, WebKit on macOS), WebKitGTK on Linux, a Chromium-based browser's app window (Edge,
Chrome, Chromium, Brave), then an ordinary browser tab. `show` returns True when it waited for the window to close.

The window runs in a process of its own (this file, run as a program): an engine that crashes (a .NET exception in
pywebview's WinForms thread ends the whole process, Corsu 0.27.0) or never shows the page then takes only the window
with it, and Corsu, still serving its page, opens it in the browser instead.
"""
import faulthandler
import os
from pathlib import Path
import shutil
import subprocess
import sys
import webbrowser

import corsu

TITLE = 'Corsu'
# How long the page has to load in the window (the page then redeems its ticket) before the browser is used instead:
# a WebView2 that fails to start leaves a blank window, its process alive.
LOAD_SECONDS = 60
SIZE = (1040, 780)
APP = Path(__file__).resolve().parent / 'app'
ICON = APP / 'corsu.svg'
# The window's own icons (tools/make_icon.py draws them from corsu.svg): X11 title bars, taskbars and Alt+Tab read
# them from the window; Windows from the .ico; the macOS Dock from the .icns.
ICONS = sorted(APP.glob('icons/corsu-*.png'), key=lambda path: int(path.stem.split('-')[1]))
ICO = APP / 'corsu.ico'
ICNS = APP / 'corsu.icns'
# Which application the window belongs to, so that desktops show Corsu's name and logo on it, not Python's or a
# browser's. Linux: the Wayland app_id and the X11 WM_CLASS are the program name GLib is given, which must be the name
# of the menu entry (corsu-setup.desktop, its StartupWMClass too): KWin and GNOME Shell find a Wayland window's icon
# only through that entry. Windows: an AppUserModelID of Corsu's own, so the taskbar does not group the window with
# Python's.
WINDOW_CLASS = corsu.DESKTOP_ID
APP_USER_MODEL_ID = 'Platykalt.Corsu'


def linux_identity():
    """Give this process Corsu's application name before any window exists (GTK reads it when the window is made)."""
    try:
        import gi
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gdk, GLib
    except (ImportError, ValueError):
        return False
    GLib.set_prgname(WINDOW_CLASS)
    GLib.set_application_name(TITLE)
    # X11 WM_CLASS is (program name, program class); GDK would otherwise write the class "Corsu-setup".
    Gdk.set_program_class(WINDOW_CLASS)
    return True


def gtk_icons():
    from gi.repository import GdkPixbuf, GLib
    pixbufs = []
    for path in ICONS:
        try:
            pixbufs.append(GdkPixbuf.Pixbuf.new_from_file(str(path)))
        except GLib.Error:
            continue
    return pixbufs


def windows_identity():
    """Windows groups taskbar buttons by AppUserModelID; pythonw.exe's would put Corsu under Python's icon and name."""
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ctypes.c_wchar_p(APP_USER_MODEL_ID))
        return True
    except (AttributeError, OSError):
        return False


def windows_window_icon(icon=None):
    """Put Corsu's icon on this process's windows (title bar, taskbar, Alt+Tab): pywebview gives its window the icon
    of the executable, Python's. Returns the number of windows changed."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                  wintypes.UINT]
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = wintypes.LPARAM
    path = str(icon or (corsu.DATA / 'corsu.ico' if (corsu.DATA / 'corsu.ico').is_file() else ICO))
    image_icon, load_from_file, default_size = 1, 0x10, 0x40
    big = user32.LoadImageW(None, path, image_icon, user32.GetSystemMetrics(11), user32.GetSystemMetrics(12),
                            load_from_file)
    small = user32.LoadImageW(None, path, image_icon, user32.GetSystemMetrics(49), user32.GetSystemMetrics(50),
                              load_from_file)
    if not big and not small:
        big = small = user32.LoadImageW(None, path, image_icon, 0, 0, load_from_file | default_size)
    if not big:
        return 0
    windows = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def collect(hwnd, _):
        process = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process))
        if process.value == os.getpid() and user32.IsWindowVisible(hwnd):
            windows.append(hwnd)
        return True
    user32.EnumWindows(callback_type(collect), 0)
    set_icon, icon_small, icon_big = 0x0080, 0, 1
    for hwnd in windows:
        user32.SendMessageW(hwnd, set_icon, icon_big, big)
        user32.SendMessageW(hwnd, set_icon, icon_small, small or big)
    return len(windows)


def macos_identity():
    """The Dock shows the running process's name and icon: Python's, unless told otherwise before the app starts."""
    try:
        from AppKit import NSApplication, NSImage
        from Foundation import NSBundle
    except ImportError:
        return False
    bundle = NSBundle.mainBundle()
    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
    if info is not None:
        # Read by the menu bar for the application menu's title.
        info['CFBundleName'] = TITLE
    image = NSImage.alloc().initWithContentsOfFile_(str(ICNS))
    if image is not None:
        NSApplication.sharedApplication().setApplicationIconImage_(image)
    return True


def with_pywebview(url):
    try:
        import webview
    except ImportError:
        return False
    identity = {'windows': windows_identity, 'macos': macos_identity}.get(corsu.PLATFORM, linux_identity)
    try:
        identity()
    except Exception as error:
        print(f'{identity.__name__}: {error}', flush=True)
    window = webview.create_window(TITLE, url, width=SIZE[0], height=SIZE[1], min_size=(640, 480))
    if corsu.PLATFORM == 'windows':
        try:
            log_dotnet_crashes()
        except Exception as error:
            print(f'log_dotnet_crashes: {error}', flush=True)
        def shown():
            try:
                windows_window_icon()
            except Exception as error:
                print(f'windows_window_icon: {error}', flush=True)
        window.events.shown += shown
    # No PNG icon for pywebview on Windows: its WinForms backend loads it with System.Drawing.Icon, which throws on a
    # PNG in a .NET thread and ends the whole program (Corsu 0.27.0 on a real Windows); the window gets corsu.ico from
    # windows_window_icon() above. GTK and Qt (Linux) put the PNG on the window, Cocoa (macOS) on the Dock, as before.
    webview.start(**({'icon': str(ICONS[-1])} if corsu.PLATFORM != 'windows' and ICONS else {}))
    return True


def log_dotnet_crashes():
    """A .NET exception nobody catches in pywebview's WinForms thread ends the process without a Python traceback: put
    it in the log first. pythonnet is loaded as pywebview's WinForms backend loads it (webview/platforms/winforms.py)."""
    try:
        import clr  # noqa: F401
    except Exception:
        os.environ['PYTHONNET_RUNTIME'] = 'coreclr'
        import clr  # noqa: F401
    from System import AppDomain, UnhandledExceptionEventHandler

    def report(sender, details):
        print(f'.NET exception ending the window: {details.ExceptionObject}', flush=True)
    AppDomain.CurrentDomain.UnhandledException += UnhandledExceptionEventHandler(report)


def with_webkitgtk(url):
    if corsu.PLATFORM != 'linux' or not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        return False
    # WebKitGTK's DMA-BUF renderer leaves the window blank with some graphics drivers (NVIDIA: "Failed to create
    # GBM buffer"); the shared-memory path works everywhere and a settings page needs nothing faster.
    os.environ.setdefault('WEBKIT_DISABLE_DMABUF_RENDERER', '1')
    # Before GTK starts: importing Gtk opens the display, and the X11 windows made then take the program name of that
    # moment ("app.py").
    linux_identity()
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        for version in ('4.1', '4.0'):
            try:
                gi.require_version('WebKit2', version)
                break
            except ValueError:
                continue
        else:
            return False
        from gi.repository import GLib, Gtk, WebKit2
    except (ImportError, ValueError):
        return False
    # GTK's start-up gave the X11 class its own capitalised form ("Corsu-setup"): set it again.
    linux_identity()
    window = Gtk.Window(title=TITLE)
    window.set_default_size(*SIZE)
    # Every size, so that each place (title bar 16px, Alt+Tab 64px or more) takes a drawn one, not a scaled one.
    icons = gtk_icons()
    if icons:
        Gtk.Window.set_default_icon_list(icons)
        window.set_icon_list(icons)
    view = WebKit2.WebView()
    # Links to other sites (help pages, GitHub) open in the browser, not inside Corsu's window.
    def decide(view, decision, kind):
        if kind == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION or kind == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            target = decision.get_navigation_action().get_request().get_uri()
            if not target.startswith(url.split('#')[0].rstrip('/')):
                webbrowser.open(target)
                decision.ignore()
                return True
        return False
    view.connect('decide-policy', decide)
    view.load_uri(url)
    window.add(view)
    window.connect('destroy', Gtk.main_quit)
    window.show_all()
    Gtk.main()
    return True


def chromium_browsers():
    names = ['microsoft-edge', 'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'brave',
             'brave-browser']
    found = [shutil.which(name) for name in names]
    if corsu.PLATFORM == 'windows':
        for base in (os.environ.get('ProgramFiles(x86)', ''), os.environ.get('ProgramFiles', ''),
                     os.environ.get('LOCALAPPDATA', '')):
            found += [str(Path(base) / 'Microsoft/Edge/Application/msedge.exe'),
                      str(Path(base) / 'Google/Chrome/Application/chrome.exe')]
    elif corsu.PLATFORM == 'macos':
        found += ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
                  '/Applications/Chromium.app/Contents/MacOS/Chromium']
    return [path for path in found if path and Path(path).is_file()]


def with_app_window(url):
    for browser in chromium_browsers():
        # A profile of its own makes a separate browser process, which ends when the window closes.
        profile = corsu.DATA / 'window-profile'
        try:
            subprocess.run([browser, f'--app={url}', f'--user-data-dir={profile}', f'--class={WINDOW_CLASS}',
                            f'--window-size={SIZE[0]},{SIZE[1]}', '--no-first-run', '--no-default-browser-check'],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError:
            continue
    return False


def native(url):
    """The window itself, in the process `show` starts: the first engine that works. 0 once it was closed."""
    for attempt in (with_pywebview, with_webkitgtk, with_app_window):
        try:
            if attempt(url):
                return 0
        except Exception as error:
            # A broken engine must not keep Corsu from opening; the next way is tried.
            print(f'{attempt.__name__}: {error}', flush=True)
    return 1


def crash_file():
    import logbook
    return logbook.path().with_name('window-crash.log')


def run_window(url, loaded=None):
    """Run the window in a process of its own until it is closed. None when it worked, else why it did not: it ended
    abnormally, or `loaded()` was still false LOAD_SECONDS after it started (it is then ended)."""
    # The address carries the page's ticket: passed in the environment, which other accounts cannot read, unlike a
    # command line.
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve())],
                               **corsu.hidden(env={**os.environ, 'CORSU_WINDOW_URL': url}))
    try:
        process.wait(timeout=LOAD_SECONDS if loaded else None)
    except subprocess.TimeoutExpired:
        if not loaded():
            process.kill()
            process.wait()
            return corsu.t(f'The page did not load in Corsu\'s window within {LOAD_SECONDS} s.',
                           f'La page ne s\'est pas chargée dans la fenêtre de Corsu en {LOAD_SECONDS} s.')
        process.wait()
    if process.returncode == 0:
        return None
    try:
        # What faulthandler wrote if the window process crashed (native code, no Python traceback otherwise).
        dump = crash_file().read_text(encoding='utf-8', errors='replace').strip()
    except OSError:
        dump = ''
    if dump:
        print(dump, flush=True)
    # Windows gives crash codes as NTSTATUS values, read in hexadecimal (0xc0000005, 0xe0434352 for .NET).
    code = f'{process.returncode:#x}' if process.returncode > 255 else str(process.returncode)
    return corsu.t(f'Corsu\'s window stopped (code {code}).', f'La fenêtre de Corsu s\'est arrêtée (code {code}).')


def show(url, mode='window', loaded=None, again=None):
    """Show Corsu at `url`. Returns True when this waited until the window was closed. When the window fails (see
    run_window), the browser opens instead, at `again()` when given: the failed window may have used `url`'s ticket."""
    if mode == 'window':
        failure = run_window(url, loaded)
        if failure is None:
            return True
        print(failure + ' ' + corsu.t('Corsu opens in the browser instead.', 'Corsu s\'ouvre dans le navigateur à la place.'),
              flush=True)
        url = again() if again else url
    webbrowser.open(url)
    return False


if __name__ == '__main__':
    import logbook
    logbook.start('window')
    try:
        crash = crash_file().open('w', encoding='utf-8')
        faulthandler.enable(crash, all_threads=True)
    except OSError:
        pass
    raise SystemExit(native(os.environ.pop('CORSU_WINDOW_URL', '')))
