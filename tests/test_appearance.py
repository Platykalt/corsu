"""The window's appearance (src/appearance.py): image checks, settings storage, reset, migration and persistence.

Every image here is built in the test (no file of the person's is read); every path lives in a temporary HOME."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from unittest.mock import patch

import appearance
import corsu
import installer
import update
from tests.test_installer import Isolated

SRC = Path(__file__).resolve().parent.parent / 'src'


def png(width=2, height=2, extra=b''):
    """A real, decodable RGB PNG."""
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    rows = b''.join(b'\0' + bytes([40, 120, 100]) * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'') + extra)


def png_header_only(width, height):
    """A structurally complete PNG declaring any size (its pixel data is not checked by the server)."""
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\0' * 16)) + chunk(b'IEND', b''))


def jpeg(width=3, height=2):
    """A JPEG's structure: SOI, APP0, DQT, SOF0 with the size, SOS, scan bytes, EOI."""
    def segment(marker, body):
        return b'\xff' + bytes([marker]) + struct.pack('>H', len(body) + 2) + body
    return (b'\xff\xd8' + segment(0xe0, b'JFIF\0\x01\x01\0\0\x01\0\x01\0\0') + segment(0xdb, b'\0' + bytes(64))
            + segment(0xc0, b'\x08' + struct.pack('>HH', height, width) + b'\x01\x01\x11\x00')
            + segment(0xda, b'\x01\x01\x00\x00\x3f\x00') + b'\x12\x34\x56\xff\x00\x78' + b'\xff\xd9')


def riff(*chunks):
    body = b'WEBP' + b''.join(kind + struct.pack('<I', len(data)) + data + (b'\0' if len(data) % 2 else b'')
                              for kind, data in chunks)
    return b'RIFF' + struct.pack('<I', len(body)) + body


def webp_lossless(width=5, height=4):
    bits = (width - 1) | ((height - 1) << 14)
    return riff((b'VP8L', b'\x2f' + struct.pack('<I', bits) + b'\0\0\0'))


def webp_lossy(width=7, height=6):
    return riff((b'VP8 ', b'\x10\x02\x00\x9d\x01\x2a' + struct.pack('<HH', width, height) + b'\0' * 8))


def webp_extended(width=7, height=6, flags=0):
    canvas = bytes([flags, 0, 0, 0]) + (width - 1).to_bytes(3, 'little') + (height - 1).to_bytes(3, 'little')
    return riff((b'VP8X', canvas), (b'VP8 ', b'\x10\x02\x00\x9d\x01\x2a' + struct.pack('<HH', width, height) + b'\0' * 8))


class Base(Isolated):
    def handle(self, method, path, body=b'', allowed=True):
        return appearance.handle(method, path, body, {}, allowed)

    def tree(self, root):
        """{relative path: sha256} of every file under root, links included as their target text."""
        found = {}
        for path in sorted(Path(root).rglob('*')):
            if path.is_symlink():
                found[str(path.relative_to(root))] = 'link:' + os.readlink(path)
            elif path.is_file():
                found[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return found


class ImageCheckTests(Base):
    def test_good_images_and_their_sizes(self):
        self.assertEqual(appearance.inspect(png(4, 3)), ('png', 4, 3))
        self.assertEqual(appearance.inspect(jpeg(30, 20)), ('jpg', 30, 20))
        self.assertEqual(appearance.inspect(webp_lossless(5, 4)), ('webp', 5, 4))
        self.assertEqual(appearance.inspect(webp_lossy(7, 6)), ('webp', 7, 6))
        self.assertEqual(appearance.inspect(webp_extended(7, 6)), ('webp', 7, 6))

    def assertRefused(self, data, code):
        with self.assertRaises(appearance.Invalid) as caught:
            appearance.inspect(data)
        self.assertEqual(caught.exception.code, code, caught.exception)

    def test_wrong_magic(self):
        self.assertRefused(b'GIF89a\x01\x00\x01\x00\x00\x00\x00;', 'not_image')
        self.assertRefused(b'<!doctype html><script>alert(1)</script>', 'not_image')
        self.assertRefused(b'', 'not_image')
        self.assertRefused(b'BM' + bytes(60), 'not_image')
        self.assertRefused(b'\0\0\0\x1cftypavif' + bytes(40), 'not_image')

    def test_truncated(self):
        for good in (png(), jpeg(), webp_lossless(), webp_lossy()):
            for cut in (len(good) - 1, len(good) // 2, 12):
                with self.subTest(kind=good[:4], cut=cut), self.assertRaises(appearance.Invalid) as caught:
                    appearance.inspect(good[:cut])
                self.assertEqual(caught.exception.code, 'damaged')

    def test_corrupted_png_checksum(self):
        data = bytearray(png())
        data[40] ^= 0xff
        self.assertRefused(bytes(data), 'damaged')

    def test_polyglots_and_disguised_html(self):
        html = b'<html><body><script>fetch("/api/uninstall")</script></body></html>'
        self.assertRefused(png(extra=html), 'damaged')
        self.assertRefused(webp_lossless() + html, 'damaged')
        self.assertRefused(jpeg() + html, 'damaged')
        self.assertRefused(b'\x89PNG\r\n\x1a\n' + html, 'damaged')
        self.assertRefused(b'RIFF' + struct.pack('<I', len(html) + 4) + b'WEBP' + html, 'damaged')
        self.assertRefused(webp_extended(flags=0x02), 'not_image')  # animated

    def test_dimensions(self):
        self.assertRefused(png_header_only(appearance.MAX_SIDE + 1, 10), 'dimensions')
        self.assertRefused(png_header_only(10, 100000), 'dimensions')
        self.assertRefused(png_header_only(0, 10), 'dimensions')
        self.assertRefused(jpeg(65535, 65535), 'dimensions')
        self.assertRefused(webp_lossless(16384, 16384), 'dimensions')
        self.assertEqual(appearance.inspect(png_header_only(4096, 4096))[1:], (4096, 4096))

    def test_body_limits(self):
        self.assertEqual(appearance.body_limit('/api/appearance/background?x=1&y=2'), appearance.MAX_BODY)
        self.assertEqual(appearance.body_limit('/api/appearance'), appearance.MAX_SETTINGS_BODY)
        status, body, _ = self.handle('POST', '/api/appearance/background', b'\0' * (appearance.MAX_BODY + 1))
        self.assertEqual((status, body['error']), (413, 'too_large'))
        status, body, _ = self.handle('POST', '/api/appearance', b'{' + b' ' * appearance.MAX_SETTINGS_BODY + b'}')
        self.assertEqual(status, 413)
        self.assertFalse((self.data / 'appearance').exists() and any((self.data / 'appearance').iterdir()))


class RouteTests(Base):
    def test_every_route_needs_allowed(self):
        appearance.store_background(png())
        for method, path in (('GET', '/appearance/settings'), ('GET', '/appearance/background'),
                             ('GET', '/appearance/background?v=1'), ('POST', '/api/appearance'),
                             ('POST', '/api/appearance/background'), ('POST', '/api/appearance/reset'),
                             ('POST', '/api/appearance/background/remove')):
            with self.subTest(path=path):
                self.assertEqual(self.handle(method, path, b'{}', allowed=False)[0], 403)
                self.assertEqual(self.handle(method, path, b'{}', allowed=lambda: False)[0], 403)
        self.assertTrue((self.data / 'appearance' / 'settings.json').exists(), 'nothing reset by a refused call')

    def test_other_paths_are_not_answered(self):
        for path in ('/', '/api/state', '/appearance/background/../../installation.json', '/appearance/../installation.json',
                     '/appearance/background-0123456789abcdef.png', '/appearance/settings.json'):
            self.assertIsNone(self.handle('GET', path), path)

    def test_upload_store_and_serve(self):
        data = webp_lossless(8, 6)
        status, settings, _ = self.handle('POST', '/api/appearance/background?x=20&y=70', data)
        self.assertEqual(status, 200, settings)
        name = f'background-{hashlib.sha256(data).hexdigest()[:16]}.webp'
        self.assertEqual(settings['background'], 'image')
        self.assertEqual({key: settings['image'][key] for key in ('file', 'type', 'bytes', 'width', 'height', 'x', 'y')},
                         {'file': name, 'type': 'image/webp', 'bytes': len(data), 'width': 8, 'height': 6, 'x': 20, 'y': 70})
        self.assertEqual((self.data / 'appearance' / name).read_bytes(), data)
        self.assertEqual(self.handle('GET', '/appearance/background?v=whatever'), (200, data, 'image/webp'))

    def test_bad_focus_and_bad_uploads_change_nothing(self):
        appearance.store_background(png())
        before = self.tree(self.data)
        for path, body in (('/api/appearance/background?x=101', png(3, 3)), ('/api/appearance/background?x=-1', png(3, 3)),
                           ('/api/appearance/background?y=../../x', png(3, 3)),
                           ('/api/appearance/background', b'<html></html>'), ('/api/appearance/background', png()[:30])):
            with self.subTest(path=path, body=body[:8]):
                self.assertIn(self.handle('POST', path, body)[0], (400, 415))
        self.assertEqual(self.tree(self.data), before)

    def test_replacement_removes_the_previous_only_after_saving(self):
        first, second = png(2, 2), png(3, 3)
        appearance.store_background(first)
        old = self.data / 'appearance' / f'background-{hashlib.sha256(first).hexdigest()[:16]}.png'
        self.assertTrue(old.exists())
        real = appearance.write_atomic

        def failing(path, data):
            if path.name == 'settings.json':
                raise OSError(28, 'No space left on device')
            return real(path, data)

        with patch.object(appearance, 'write_atomic', failing):
            status, body, _ = self.handle('POST', '/api/appearance/background', second)
        self.assertEqual(status, 500)
        self.assertTrue(old.exists(), 'the previous picture stays when the new settings could not be saved')
        self.assertEqual(appearance.load()['image']['file'], old.name)
        self.assertEqual(self.handle('GET', '/appearance/background')[1], first)
        self.assertEqual(list((self.data / 'appearance').glob('*.corsu-tmp')), [])
        status, body, _ = self.handle('POST', '/api/appearance/background', second)
        self.assertEqual(status, 200)
        self.assertFalse(old.exists())
        self.assertEqual(sorted(path.name for path in (self.data / 'appearance').glob('background-*')), [body['image']['file']])

    def test_only_the_recorded_file_is_served(self):
        appearance.store_background(png())
        path = self.data / 'appearance' / 'settings.json'
        secret = self.data / 'installation.json'
        secret.write_text('{"files": {}}', encoding='utf-8')
        for name in ('../installation.json', '/etc/passwd', 'background-0123456789abcdef.png/../../installation.json',
                     'settings.json', 'background-ZZZZ.png'):
            saved = json.loads(path.read_text(encoding='utf-8'))
            saved['image']['file'] = name
            path.write_text(json.dumps(saved), encoding='utf-8')
            with self.subTest(name=name):
                self.assertEqual(self.handle('GET', '/appearance/background')[0], 404)
                self.assertIsNone(self.handle('GET', '/appearance/settings')[1]['image'])

    def test_missing_corrupted_or_linked_picture_falls_back(self):
        settings = appearance.store_background(png())
        picture = self.data / 'appearance' / settings['image']['file']
        picture.write_bytes(png(5, 5))  # same name, other content: the hash in the name no longer matches
        status, answer, _ = self.handle('GET', '/appearance/settings')
        self.assertEqual((status, answer['background'], answer['image'], answer.get('image_problem')), (200, 'none', None, True))
        self.assertEqual(self.handle('GET', '/appearance/background')[0], 404)
        picture.unlink()
        self.assertEqual(self.handle('GET', '/appearance/background')[0], 404)
        outside = self.home / 'outside.png'
        outside.write_bytes(png())
        try:
            picture.symlink_to(outside)
        except OSError:
            self.skipTest('no symbolic links here')
        self.assertEqual(self.handle('GET', '/appearance/background')[0], 404)


class SettingsTests(Base):
    def test_defaults_when_nothing_is_saved(self):
        self.assertEqual(appearance.load(), appearance.DEFAULTS)
        status, answer, kind = self.handle('GET', '/appearance/settings')
        self.assertEqual((status, answer['theme'], answer['palette'], answer['background']), (200, 'system', 'maquis', 'none'))
        self.assertFalse((self.data / 'appearance').exists(), 'reading writes nothing')

    def test_changes_are_validated_and_saved_atomically(self):
        status, answer, _ = self.handle('POST', '/api/appearance', json.dumps(
            {'theme': 'dark', 'palette': 'notte', 'accent': '#AA3366', 'density': 'compact', 'dim': 0.5, 'blur': 99,
             'language': 'co', 'unknown': 1}).encode())
        self.assertEqual(status, 200, answer)
        saved = json.loads((self.data / 'appearance' / 'settings.json').read_text(encoding='utf-8'))
        self.assertEqual((saved['format'], saved['theme'], saved['palette'], saved['accent'], saved['density'],
                          saved['dim'], saved['blur']), (1, 'dark', 'notte', '#aa3366', 'compact', 0.5, 24))
        self.assertNotIn('unknown', saved)
        for bad in ({'theme': 'neon'}, {'accent': 'red'}, {'accent': 'url(x)'}, {'dim': 'a'}, {'blur': True},
                    {'background': 'image'}, {'palette': None}, [1, 2]):
            with self.subTest(bad=bad):
                self.assertEqual(self.handle('POST', '/api/appearance', json.dumps(bad).encode())[0], 400)
        self.assertEqual(self.handle('POST', '/api/appearance', b'not json')[0], 400)
        self.assertEqual(appearance.load()['theme'], 'dark', 'a refused change leaves the saved settings')
        self.assertEqual(list((self.data / 'appearance').glob('*.corsu-tmp')), [])
        self.assertFalse((self.data / 'appearance' / 'settings.json.previous').exists())
        appearance.update({'theme': 'light'})
        self.assertEqual(json.loads((self.data / 'appearance' / 'settings.json.previous').read_text(encoding='utf-8'))['theme'], 'dark')

    def test_focus_may_move_but_the_file_is_the_servers(self):
        appearance.store_background(png())
        answer = self.handle('POST', '/api/appearance', json.dumps(
            {'image': {'x': 10, 'y': 90, 'file': '../installation.json', 'bytes': 1}}).encode())[1]
        self.assertEqual((answer['image']['x'], answer['image']['y']), (10, 90))
        self.assertTrue(answer['image']['file'].startswith('background-'))

    def test_damaged_settings_give_defaults_and_are_kept(self):
        folder = self.data / 'appearance'
        folder.mkdir(parents=True)
        (self.data / 'installation.json').write_text('{"files": {}}', encoding='utf-8')
        record = (self.data / 'installation.json').read_bytes()
        (folder / 'settings.json').write_bytes(b'{"theme": "dark", "pal')
        self.assertEqual(appearance.load(), appearance.DEFAULTS)
        self.assertEqual((folder / 'settings.json.damaged').read_bytes(), b'{"theme": "dark", "pal')
        self.assertEqual((self.data / 'installation.json').read_bytes(), record)
        for content in (b'[1, 2]', b'\xff\xfe\x00', b'null'):
            (folder / 'settings.json').write_bytes(content)
            self.assertEqual(appearance.load(), appearance.DEFAULTS)
        # A save keeps the previous good copy, used when the file is damaged afterwards.
        appearance.update({'theme': 'light'})
        appearance.update({'theme': 'dark'})
        (folder / 'settings.json').write_bytes(b'{oops')
        self.assertEqual(appearance.load()['theme'], 'light')
        self.assertEqual(self.handle('GET', '/appearance/settings')[0], 200)

    def test_migration(self):
        folder = self.data / 'appearance'
        folder.mkdir(parents=True)
        (folder / 'settings.json').write_text(json.dumps({'theme': 'dark', 'blur': True, 'old_key': 3}), encoding='utf-8')
        self.assertEqual((appearance.load()['format'], appearance.load()['blur'], appearance.load()['theme']), (1, 12, 'dark'))
        self.assertEqual(appearance.migrate({'blur': False})['blur'], 0)
        self.assertEqual(appearance.migrate({'format': 1, 'blur': 6}), {'format': 1, 'blur': 6})
        # A newer Corsu's file (after going back to an older version): known keys still used, the rest ignored.
        (folder / 'settings.json').write_text(json.dumps({'format': 7, 'palette': 'mare', 'sparkles': 'yes'}), encoding='utf-8')
        loaded = appearance.load()
        self.assertEqual((loaded['palette'], loaded['format']), ('mare', 1))
        self.assertNotIn('sparkles', loaded)


class ResetTests(Base):
    def test_reset_touches_only_appearance(self):
        # An installation: its record, the kept originals, a release, preferences and a translated program's file.
        (self.data / 'releases/0123456789abcdef/src').mkdir(parents=True)
        (self.data / 'releases/0123456789abcdef/src/release.json').write_text('{"version": "0.25.0"}', encoding='utf-8')
        (self.data / 'backups').mkdir()
        (self.data / 'backups/abc').write_bytes(b'original catalogue')
        (self.data / 'preferences.json').write_text('{"auto_update": true}', encoding='utf-8')
        component = self.home / '.local/share/locale/co/LC_MESSAGES/vlc.mo'
        component.parent.mkdir(parents=True)
        component.write_bytes(b'\xde\x12\x04\x95catalogue')
        corsu.save_state({'files': {str(component): {'installed_sha256': hashlib.sha256(component.read_bytes()).hexdigest()}},
                          'components': ['vlc']})
        corsu.save_state(corsu.load_state())
        appearance.update({'theme': 'dark', 'accent': '#123456'})
        appearance.store_background(png())
        (self.data / 'appearance' / 'settings.json.damaged').write_bytes(b'{')
        before = {key: value for key, value in self.tree(self.home).items() if not key.startswith('data/appearance')}
        status, answer, _ = self.handle('POST', '/api/appearance/reset')
        self.assertEqual(status, 200)
        self.assertEqual({key: answer[key] for key in appearance.DEFAULTS}, appearance.DEFAULTS)
        self.assertEqual(list((self.data / 'appearance').iterdir()), [])
        self.assertEqual(self.tree(self.home), before, 'installation.json, backups, releases and components identical')
        self.assertEqual(self.handle('GET', '/appearance/background')[0], 404)

    def test_reset_does_not_follow_links(self):
        outside = self.home / 'precious'
        outside.mkdir()
        (outside / 'keep.txt').write_text('mine', encoding='utf-8')
        folder = self.data / 'appearance'
        folder.mkdir(parents=True)
        try:
            (folder / 'linked').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('no symbolic links here')
        appearance.reset()
        self.assertEqual((outside / 'keep.txt').read_text(encoding='utf-8'), 'mine')


class PersistenceTests(Base):
    """The settings live in corsu.DATA/appearance, which updates, repairs and uninstalling leave alone."""

    def saved(self):
        appearance.update({'theme': 'dark', 'palette': 'tramontu', 'density': 'compact'})
        return appearance.store_background(png(6, 4), 30, 60)

    def test_update_and_repair_clean_ups_leave_appearance(self):
        settings = self.saved()
        before = self.tree(self.data / 'appearance')
        current, old = self.release('0.25.0'), self.release('0.23.0')
        corsu.save_state({'files': {}, 'release': {'version': '0.25.0', 'folder': str(current)}})
        (self.data / 'tmp/update-x').mkdir(parents=True)
        os.utime(self.data / 'tmp/update-x', (0, 0))
        with patch.object(installer, 'clients_running', return_value=False):
            installer.prune_releases(current)
        update.clean_downloads(self.data / 'tmp')
        installer.prune_runtimes()
        installer.clean_leftovers(self.data)
        self.assertFalse(old.exists(), 'the clean-up did run')
        self.assertEqual(self.tree(self.data / 'appearance'), before)
        self.assertEqual(appearance.load(), settings)

    def test_nothing_in_update_repair_or_uninstall_deletes_data_wholesale(self):
        """Deletions in the installer, updater and uninstaller name Corsu's own subfolders or recorded files: none
        is the data folder itself, and none names the appearance folder."""
        for name in ('installer.py', 'update.py', 'corsu.py'):
            text = (SRC / name).read_text(encoding='utf-8')
            self.assertNotIn('appearance', text, name)
            for call in re.findall(r'rmtree\(([^,)]*)', text):
                self.assertNotIn(call.strip(), ('DATA', 'corsu.DATA', "corsu.DATA.parent", 'DATA.parent'), name)

    def test_uninstall_keeps_appearance_like_corsus_other_own_files(self):
        settings = self.saved()
        (self.data / 'preferences.json').write_text('{"auto_update": true}', encoding='utf-8')
        corsu.save_state({'files': {}})
        with patch.object(corsu, 'unlink_profiles', lambda: None), patch.object(corsu, 'repair_default_browser', lambda: None):
            import io
            from contextlib import redirect_stdout
            with redirect_stdout(io.StringIO()):
                corsu.uninstall()
        self.assertTrue((self.data / 'preferences.json').exists())
        self.assertEqual(appearance.load(), settings)

    def run_copy(self, folder, code):
        """Run `code` with a copy of Corsu's src in `folder` (another release, or the folder it was launched from)."""
        script = ('import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import corsu; '
                  'corsu.DATA = Path(sys.argv[2]); import appearance, json; ' + code)
        return subprocess.run([sys.executable, '-I', '-c', script, str(folder), str(self.data)], capture_output=True,
                              text=True, encoding='utf-8', env={**os.environ, 'HOME': str(self.home)}, check=True).stdout

    def test_settings_survive_a_new_release_folder_and_the_launch_folder_being_deleted(self):
        launch = self.home / 'Downloads/corsu-0.25.0'
        shutil.copytree(SRC, launch / 'src', ignore=shutil.ignore_patterns('__pycache__'))
        self.run_copy(launch / 'src', "appearance.update({'theme': 'light', 'palette': 'granitu', 'accent': '#336699'}); "
                                      f"appearance.store_background(bytes.fromhex('{png(9, 5).hex()}'), 15, 85)")
        shutil.rmtree(launch)
        release = self.data / 'releases' / '00112233445566aa'
        shutil.copytree(SRC, release / 'src', ignore=shutil.ignore_patterns('__pycache__'))
        output = self.run_copy(release / 'src', "print(json.dumps(appearance.public(appearance.load())))")
        loaded = json.loads(output)
        self.assertEqual((loaded['theme'], loaded['palette'], loaded['accent'], loaded['background']),
                         ('light', 'granitu', '#336699', 'image'))
        self.assertEqual((loaded['image']['width'], loaded['image']['height'], loaded['image']['x'], loaded['image']['y']),
                         (9, 5, 15, 85))


if __name__ == '__main__':
    unittest.main()
