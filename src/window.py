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
ICON = Path(__file__).resolve().parent / 'app/corsu.svg'
# Same name as StartupWMClass in the menu entry, so desktops show Corsu's icon on its window.
WINDOW_CLASS = 'corsu'


def with_pywebview(url):
    try:
        import webview
    except ImportError:
        return False
    webview.create_window(TITLE, url, width=SIZE[0], height=SIZE[1], min_size=(640, 480))
    webview.start()
    return True


def with_webkitgtk(url):
    if corsu.PLATFORM != 'linux' or not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        return False
    # WebKitGTK's DMA-BUF renderer leaves the window blank with some graphics drivers (NVIDIA: "Failed to create
    # GBM buffer"); the shared-memory path works everywhere and a settings page needs nothing faster.
    os.environ.setdefault('WEBKIT_DISABLE_DMABUF_RENDERER', '1')
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
    GLib.set_prgname(WINDOW_CLASS)
    GLib.set_application_name(TITLE)
    window = Gtk.Window(title=TITLE)
    window.set_default_size(*SIZE)
    try:
        window.set_icon_from_file(str(ICON))
    except GLib.Error:
        pass
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
