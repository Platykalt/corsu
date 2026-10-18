import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from contextlib import redirect_stdout
from unittest.mock import patch

import corsu

APP = Path(__file__).resolve().parent.parent / 'src/app'
ICO = APP / 'corsu.ico'
ICNS = APP / 'corsu.icns'
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def ico_entries(data):
    """(width, height, image bytes) for each entry of an ICO file, checking the container on the way."""
    reserved, kind, count = struct.unpack('<HHH', data[:6])
    assert (reserved, kind) == (0, 1), 'not an icon file'
    entries = []
    for index in range(count):
        width, height, colours, zero, planes, bits, size, offset = struct.unpack(
            '<BBBBHHII', data[6 + 16 * index:6 + 16 * (index + 1)])
        assert zero == 0 and offset + size <= len(data), f'entry {index} is malformed'
        entries.append((width or 256, height or 256, data[offset:offset + size]))
    return entries


class IconFileTests(unittest.TestCase):
    def test_icon_holds_every_size_as_a_valid_png(self):
        entries = ico_entries(ICO.read_bytes())
        self.assertEqual([width for width, _, _ in entries], [16, 24, 32, 48, 64, 128, 256])
        for width, height, image in entries:
            with self.subTest(size=width):
                self.assertEqual(width, height)
                self.assertTrue(image.startswith(PNG_SIGNATURE))
                self.assertEqual(image[12:16], b'IHDR')
                self.assertEqual(struct.unpack('>II', image[16:24]), (width, height))
                # 8-bit RGBA, so the rounded corners stay transparent.
                self.assertEqual(image[24:26], bytes([8, 6]))
                offset, chunks = len(PNG_SIGNATURE), b''
                while offset < len(image):
                    length, chunk = struct.unpack('>I4s', image[offset:offset + 8])
                    if chunk == b'IDAT':
                        chunks += image[offset + 8:offset + 8 + length]
                    offset += 12 + length
                rows = zlib.decompress(chunks)
                self.assertEqual(len(rows), height * (1 + 4 * width))


def png_check(test, image, size):
    """A complete 8-bit RGBA PNG of `size` pixels (the rounded corners stay transparent)."""
    test.assertTrue(image.startswith(PNG_SIGNATURE))
    test.assertEqual(struct.unpack('>II', image[16:24]), (size, size))
    test.assertEqual(image[24:26], bytes([8, 6]))
    offset, chunks = len(PNG_SIGNATURE), b''
    while offset < len(image):
        length, chunk = struct.unpack('>I4s', image[offset:offset + 8])
        if chunk == b'IDAT':
            chunks += image[offset + 8:offset + 8 + length]
        offset += 12 + length
    test.assertEqual(len(zlib.decompress(chunks)), size * (1 + 4 * size))


class OtherIconFormatTests(unittest.TestCase):
    """The same drawing (src/app/corsu.svg, through tools/make_icon.py) for macOS and the Linux window."""

    def test_icns_holds_every_macos_size(self):
        data = ICNS.read_bytes()
        self.assertEqual(data[:4], b'icns')
        self.assertEqual(struct.unpack('>I', data[4:8])[0], len(data))
        found, offset = {}, 8
        while offset < len(data):
            kind, length = data[offset:offset + 4], struct.unpack('>I', data[offset + 4:offset + 8])[0]
            found[kind] = data[offset + 8:offset + length]
            offset += length
        sizes = {b'icp4': 16, b'icp5': 32, b'icp6': 64, b'ic07': 128, b'ic08': 256, b'ic09': 512, b'ic10': 1024,
                 b'ic11': 32, b'ic12': 64, b'ic13': 256, b'ic14': 512}
        self.assertEqual(set(found), set(sizes))
        for kind, size in sizes.items():
            with self.subTest(kind=kind):
                png_check(self, found[kind], size)

    def test_window_pngs_and_ico_are_the_same_images(self):
        pngs = {int(path.stem.split('-')[1]): path.read_bytes() for path in (APP / 'icons').glob('corsu-*.png')}
        self.assertEqual(sorted(pngs), [16, 24, 32, 48, 64, 128, 256])
        for width, _, image in ico_entries(ICO.read_bytes()):
            with self.subTest(size=width):
                png_check(self, pngs[width], width)
                self.assertEqual(image, pngs[width])

    def test_logo_is_drawn_without_fonts(self):
        # A <text> logo depends on the fonts of each computer (it was "co" in Georgia or DejaVu Serif).
        svg = (APP / 'corsu.svg').read_text(encoding='utf-8')
        self.assertNotIn('<text', svg)
        self.assertIn('viewBox="0 0 64 64"', svg)


class WindowsShortcutTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        # A Windows user folder with a space and an accented letter.
        self.home = Path(directory.name) / 'Utilizatore è spaziu'
        self.data = self.home / 'AppData/Local/corsu'
        config = self.home / 'AppData/Roaming'
        self.links = []
        for patcher in (patch.object(corsu, 'PLATFORM', 'windows'), patch.object(corsu, 'HOME', self.home),
                        patch.object(corsu, 'DATA', self.data), patch.object(corsu, 'STATE', self.data / 'installation.json'),
                        patch.object(corsu, 'CONFIG', config),
                        patch.object(corsu, 'START_MENU', config / 'Microsoft/Windows/Start Menu/Programs'),
                        patch.object(corsu.subprocess, 'run', side_effect=self.powershell)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def powershell(self, command, check=False, env=None, **_):
        """Stand-in for WScript.Shell: the shortcut records what the script would have set from the environment."""
        self.assertEqual(command[0], 'powershell')
        # Paths travel only through the environment, never through the command line PowerShell parses.
        self.assertNotIn(str(self.home), ' '.join(command))
        fields = {name: env[name] for name in ('CORSU_TARGET', 'CORSU_ARGUMENTS', 'CORSU_DIR', 'CORSU_ICON')}
        self.links.append(fields)
        Path(env['CORSU_LINK']).write_text(json.dumps(fields), encoding='utf-8')

    def test_corsu_shortcut_shows_the_icon_kept_outside_releases(self):
        corsu.setup_shortcut(corsu.Installer())
        icon = self.data / 'corsu.ico'
        self.assertEqual(self.links[-1]['CORSU_ICON'], f'{icon},0')
        self.assertEqual(icon.read_bytes(), ICO.read_bytes())
        self.assertNotIn('releases', self.links[-1]['CORSU_ICON'])
        shortcut = corsu.START_MENU / 'Corsu.lnk'
        self.assertEqual(json.loads(shortcut.read_text(encoding='utf-8'))['CORSU_ICON'], f'{icon},0')
        files = corsu.load_state()['files']
        self.assertIn(str(icon), files)
        self.assertIn(str(shortcut), files)

    def test_rerun_is_harmless_and_gives_an_old_shortcut_its_icon(self):
        # A shortcut written by an earlier version, without an icon.
        corsu.windows_link(corsu.Installer(), corsu.START_MENU / 'Corsu.lnk', 'pythonw.exe', '"app.py"')
        self.assertEqual(self.links[-1]['CORSU_ICON'], '')
        for _ in range(2):
            corsu.setup_shortcut(corsu.Installer())
            shortcut = json.loads((corsu.START_MENU / 'Corsu.lnk').read_text(encoding='utf-8'))
            self.assertEqual(shortcut['CORSU_ICON'], f'{self.data / "corsu.ico"},0')
        self.assertEqual(len(corsu.load_state()['files']), 2)

    def test_changed_icon_is_preserved(self):
        corsu.setup_shortcut(corsu.Installer())
        (self.data / 'corsu.ico').write_bytes(b'my own icon')
        with self.assertRaises(RuntimeError):
            corsu.setup_shortcut(corsu.Installer())
        self.assertEqual((self.data / 'corsu.ico').read_bytes(), b'my own icon')

    def test_uninstall_removes_the_icon(self):
        corsu.setup_shortcut(corsu.Installer())
        with patch.object(corsu, 'PLATFORM', 'linux'), redirect_stdout(io.StringIO()):
            corsu.uninstall()
        self.assertFalse((self.data / 'corsu.ico').exists())
        self.assertFalse((corsu.START_MENU / 'Corsu.lnk').exists())


if __name__ == '__main__':
    unittest.main()
