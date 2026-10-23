"""Corsu's own window: the app page in a window with Corsu's name and icon, not a browser tab.

The first that works is used: pywebview (bundled with the standalone Corsu programs, using the web engine of the
system: WebView2 on Windows, WebKit on macOS), WebKitGTK on Linux, a Chromium-based browser's app window (Edge,
Chrome, Chromium, Brave), then an ordinary browser tab. `show` returns True when it waited for the window to close.
"""
import os
from pathlib import Path
import shutil
import subprocess
import webbrowser

import corsu

TITLE = 'Corsu'
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


def show(url, mode='window'):
    """Show Corsu at `url`. Returns True when this waited until the window was closed."""
    if mode == 'window':
        for attempt in (with_pywebview, with_webkitgtk, with_app_window):
            try:
                if attempt(url):
                    return True
            except Exception as error:
                # A broken engine must not keep Corsu from opening; the next way is tried.
                print(f'{attempt.__name__}: {error}', flush=True)
    webbrowser.open(url)
    return False
