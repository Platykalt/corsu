"""Corsu's window belongs to Corsu: the application name and icon desktops show (window, taskbar or Dock, Alt+Tab,
applications menu) come from Corsu's menu entry or its own icons, not from Python or a browser."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import corsu
import window

SRC = Path(__file__).resolve().parent.parent / 'src'


class LinuxEntryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        data = self.home / '.local/share/corsu'
        for patcher in (patch.object(corsu, 'PLATFORM', 'linux'), patch.object(corsu, 'HOME', self.home),
                        patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', data / 'installation.json')):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_entry_name_and_window_class_are_one_name(self):
        # KWin and GNOME Shell (Wayland) look for <app_id>.desktop; X11 desktops compare WM_CLASS with StartupWMClass.
        with redirect_stdout(io.StringIO()):
            corsu.setup_shortcut(corsu.Installer())
        entries = list((self.home / '.local/share/applications').glob('*.desktop'))
        self.assertEqual([entry.stem for entry in entries], [window.WINDOW_CLASS])
        text = entries[0].read_text(encoding='utf-8')
        self.assertIn(f'\nStartupWMClass={window.WINDOW_CLASS}\n', text)
        icon = next(line[5:] for line in text.splitlines() if line.startswith('Icon='))
        self.assertTrue(Path(icon).is_file(), icon)
        self.assertEqual(Path(icon).read_bytes(), (SRC / 'app/corsu.svg').read_bytes())

    def test_window_icons_cover_small_and_large_places(self):
        sizes = [int(path.stem.split('-')[1]) for path in window.ICONS]
        self.assertEqual(sizes, [16, 24, 32, 48, 64, 128, 256])

    @unittest.skipUnless(shutil.which('python3'), 'no python3')
    def test_gtk_gets_corsus_application_name(self):
        # In a separate process: GLib's program name can be set once. Without PyGObject the check cannot run.
        code = ('import sys; sys.path.insert(0, sys.argv[1]); import window\n'
                'if not window.linux_identity(): print("no-gi"); raise SystemExit\n'
                'from gi.repository import GLib, Gdk\n'
                'print(GLib.get_prgname(), Gdk.get_program_class(), GLib.get_application_name())')
        result = subprocess.run([sys.executable, '-c', code, str(SRC)], capture_output=True, text=True,
                                env={**os.environ, 'HOME': tempfile.gettempdir()})
        self.assertEqual(result.returncode, 0, result.stderr)
        if result.stdout.strip() == 'no-gi':
            self.skipTest('PyGObject (gi) not installed')
        self.assertEqual(result.stdout.split(), [window.WINDOW_CLASS, window.WINDOW_CLASS, 'Corsu'])


class MacApplicationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        data = self.home / 'Library/Application Support/corsu'
        for patcher in (patch.object(corsu, 'PLATFORM', 'macos'), patch.object(corsu, 'HOME', self.home),
                        patch.object(corsu, 'DATA', data), patch.object(corsu, 'STATE', data / 'installation.json'),
                        patch.object(corsu.subprocess, 'run', side_effect=self.osacompile)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def osacompile(self, command, check=False, **_):
        """Stand-in for osacompile: an applet with the generic script icon."""
        self.assertEqual(command[0], 'osacompile')
        applet = Path(command[command.index('-o') + 1])
        (applet / 'Contents/Resources').mkdir(parents=True)
        (applet / 'Contents/Resources/applet.icns').write_bytes(b'generic script icon')
        (applet / 'Contents/Info.plist').write_text('<plist/>', encoding='utf-8')

    def test_applet_shows_corsus_icon(self):
        corsu.setup_shortcut(corsu.Installer())
        icon = self.home / 'Applications/Corsu.app/Contents/Resources/applet.icns'
        self.assertEqual(icon.read_bytes(), (SRC / 'app/corsu.icns').read_bytes())


class FakeEvent:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self


class PywebviewTests(unittest.TestCase):
    """pywebview runs the window on Windows (WebView2) and macOS (WKWebView): its identity is set before it starts."""

    def fake_webview(self, calls):
        module = types.ModuleType('webview')
        created = types.SimpleNamespace(events=types.SimpleNamespace(shown=FakeEvent()))
        module.create_window = lambda *args, **kwargs: calls.append(('create', args[0])) or created
        module.start = lambda **kwargs: calls.append(('start', kwargs))
        return module, created

    def test_windows_sets_app_id_first_and_icon_once_shown(self):
        calls = []
        module, created = self.fake_webview(calls)
        with patch.dict(sys.modules, {'webview': module}), patch.object(corsu, 'PLATFORM', 'windows'), \
                patch.object(window, 'windows_identity', lambda: calls.append(('identity',))), \
                patch.object(window, 'windows_window_icon', lambda: calls.append(('icon',)) or 1):
            self.assertTrue(window.with_pywebview('http://127.0.0.1:1/'))
            self.assertEqual([call[0] for call in calls], ['identity', 'create', 'start'])
            for handler in created.events.shown.handlers:
                handler()
        self.assertEqual(calls[-1], ('icon',))
        self.assertEqual(window.APP_USER_MODEL_ID, 'Platykalt.Corsu')
        # No PNG for pywebview's Windows backend: System.Drawing.Icon throws on it and ends Corsu.
        self.assertEqual(calls[2], ('start', {}))

    def test_macos_sets_dock_identity_first(self):
        calls = []
        module, created = self.fake_webview(calls)
        with patch.dict(sys.modules, {'webview': module}), patch.object(corsu, 'PLATFORM', 'macos'), \
                patch.object(window, 'macos_identity', lambda: calls.append(('identity',))):
            window.with_pywebview('http://127.0.0.1:1/')
        self.assertEqual([call[0] for call in calls], ['identity', 'create', 'start'])
        self.assertEqual(created.events.shown.handlers, [])
        # Unchanged since 0.27.0: Cocoa puts the PNG on the Dock.
        self.assertEqual(calls[2], ('start', {'icon': str(window.ICONS[-1])}))

    def test_linux_gives_pywebview_the_png_icon(self):
        calls = []
        module, _ = self.fake_webview(calls)
        with patch.dict(sys.modules, {'webview': module}), patch.object(corsu, 'PLATFORM', 'linux'), \
                patch.object(window, 'linux_identity', lambda: None):
            window.with_pywebview('http://127.0.0.1:1/')
        self.assertEqual(calls[-1], ('start', {'icon': str(window.ICONS[-1])}))

    def test_a_failing_identity_does_not_keep_the_window_closed(self):
        calls = []
        module, _ = self.fake_webview(calls)

        def broken():
            raise OSError('no shell32')
        with patch.dict(sys.modules, {'webview': module}), patch.object(corsu, 'PLATFORM', 'windows'), \
                patch.object(window, 'windows_identity', broken), redirect_stdout(io.StringIO()) as output:
            self.assertTrue(window.with_pywebview('http://127.0.0.1:1/'))
        self.assertIn('no shell32', output.getvalue())
        self.assertEqual([call[0] for call in calls], ['create', 'start'])


if __name__ == '__main__':
    unittest.main()
