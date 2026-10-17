"""The window's appearance: theme, palette, accent, density and an optional personal background image.

Everything lives in corsu.DATA/appearance/ (docs/window-design.md, "Server interface"):

- settings.json: {"format": 1, ...} (see DEFAULTS). Missing → defaults; damaged → defaults, the damaged file kept as
  settings.json.damaged and the copy kept by the previous save (settings.json.previous) used when it is good.
  Unknown keys are ignored; older formats go through migrate().
- background-<first 16 hex of its sha256>.<webp|jpg|png>: the person's picture as the page prepared it (scaled down
  and re-encoded in the browser). The server never receives or opens a path: only bytes POSTed through allowed(),
  checked by magic bytes and by parsing their header and chunk structure here (stdlib only), stored under a name it
  derives itself, and served back only by the name recorded in settings.json.

Nothing here touches installation.json or any file of an installed part; resetting removes only this folder's files.
`handle(method, path, body, headers, allowed)` answers the appearance routes as (status, body, content type), or None
for any other path. `allowed` is the window's allowed() (a callable) or a boolean.
"""
import hashlib
import json
import os
import re
import struct
import threading
import urllib.parse
import zlib
from pathlib import Path

import corsu

FORMAT = 1
THEMES = ('system', 'light', 'dark')
PALETTES = ('maquis', 'mare', 'granitu', 'tramontu', 'notte')
DENSITIES = ('comfortable', 'compact')
BACKGROUNDS = ('none', 'image')
DIM_MAX = 0.85
BLUR_MAX = 24
DEFAULTS = {'format': FORMAT, 'theme': 'system', 'palette': 'maquis', 'accent': None, 'density': 'comfortable',
            'background': 'none', 'image': None, 'dim': 0.55, 'blur': 0}

# The page sends a picture it has already scaled to at most 2560 px on its long side and re-encoded (WebP or JPEG);
# these limits leave room for that and refuse anything else before it is read.
MAX_BODY = 8 * 1024 * 1024
MAX_SETTINGS_BODY = 16 * 1024
MAX_SIDE = 4096
MAX_PIXELS = 4096 * 4096
KINDS = {'png': 'image/png', 'jpg': 'image/jpeg', 'webp': 'image/webp'}
FILE_NAME = re.compile(r'^background-[0-9a-f]{16}\.(png|jpg|webp)$')
ACCENT = re.compile(r'^#[0-9a-fA-F]{6}$')
LOCK = threading.RLock()


class Invalid(ValueError):
    """Refused content; `code` is what the page shows a message for."""

    def __init__(self, code, detail=''):
        super().__init__(f'{code}: {detail}' if detail else code)
        self.code = code


def folder():
    return corsu.DATA / 'appearance'


def settings_path():
    return folder() / 'settings.json'


# Image checks ------------------------------------------------------------------------------------------------------

def png_size(data):
    """(width, height) of a complete PNG: every chunk inside the data with a correct CRC, IHDR first, IDAT present,
    IEND last and nothing after it."""
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise Invalid('not_image')
    position, size, seen_data = 8, None, False
    while True:
        if position + 12 > len(data):
            raise Invalid('damaged', 'PNG chunk cut short')
        length, kind = struct.unpack('>I4s', data[position:position + 8])
        end = position + 12 + length
        if length > 0x7fffffff or end > len(data):
            raise Invalid('damaged', 'PNG chunk cut short')
        body = data[position + 8:position + 8 + length]
        if zlib.crc32(kind + body) != struct.unpack('>I', data[end - 4:end])[0]:
            raise Invalid('damaged', 'PNG checksum')
        if size is None:
            if kind != b'IHDR' or length != 13:
                raise Invalid('damaged', 'PNG without IHDR')
            size = struct.unpack('>II', body[:8])
        elif kind == b'IDAT':
            seen_data = True
        elif kind == b'IEND':
            if end != len(data) or not seen_data:
                raise Invalid('damaged', 'PNG ends wrongly')
            return size
        position = end


def jpeg_size(data):
    """(width, height) from a JPEG's frame header, walking its segments up to the scan; the data must end with EOI."""
    if not data.startswith(b'\xff\xd8\xff'):
        raise Invalid('not_image')
    if not data.endswith(b'\xff\xd9'):
        raise Invalid('damaged', 'JPEG cut short')
    position, size = 2, None
    while True:
        while position < len(data) and data[position] == 0xff and position + 1 < len(data) and data[position + 1] == 0xff:
            position += 1  # fill bytes
        if position + 4 > len(data) or data[position] != 0xff:
            raise Invalid('damaged', 'JPEG segment')
        marker = data[position + 1]
        if marker in (0x01,) or 0xd0 <= marker <= 0xd7:
            position += 2
            continue
        length = struct.unpack('>H', data[position + 2:position + 4])[0]
        if length < 2 or position + 2 + length > len(data):
            raise Invalid('damaged', 'JPEG segment cut short')
        if 0xc0 <= marker <= 0xcf and marker not in (0xc4, 0xc8, 0xcc):
            if length < 8:
                raise Invalid('damaged', 'JPEG frame header')
            height, width = struct.unpack('>HH', data[position + 5:position + 9])
            size = (width, height)
        if marker == 0xda:
            if size is None:
                raise Invalid('damaged', 'JPEG without frame header')
            return size
        if marker == 0xd9:
            raise Invalid('damaged', 'JPEG without image data')
        position += 2 + length


def webp_size(data):
    """(width, height) of a still WebP: the RIFF size matches the data exactly, every chunk fits, and the image is
    a VP8 or VP8L bitstream (VP8X allowed, animation refused)."""
    if len(data) < 12 or data[:4] != b'RIFF' or data[8:12] != b'WEBP':
        raise Invalid('not_image')
    if struct.unpack('<I', data[4:8])[0] + 8 != len(data):
        raise Invalid('damaged', 'WebP size')
    position, size, canvas = 12, None, None
    while position < len(data):
        if position + 8 > len(data):
            raise Invalid('damaged', 'WebP chunk cut short')
        kind, length = data[position:position + 4], struct.unpack('<I', data[position + 4:position + 8])[0]
        body = data[position + 8:position + 8 + length]
        if len(body) != length:
            raise Invalid('damaged', 'WebP chunk cut short')
        if position == 12 and kind not in (b'VP8 ', b'VP8L', b'VP8X'):
            raise Invalid('not_image', 'WebP first chunk')
        if kind == b'VP8X':
            if length < 10:
                raise Invalid('damaged', 'WebP VP8X')
            if body[0] & 0x02:
                raise Invalid('not_image', 'animated WebP')
            canvas = (int.from_bytes(body[4:7], 'little') + 1, int.from_bytes(body[7:10], 'little') + 1)
        elif kind in (b'ANIM', b'ANMF'):
            raise Invalid('not_image', 'animated WebP')
        elif kind == b'VP8 ' and size is None:
            if length < 10 or body[3:6] != b'\x9d\x01\x2a':
                raise Invalid('damaged', 'WebP VP8 header')
            width, height = struct.unpack('<HH', body[6:10])
            size = (width & 0x3fff, height & 0x3fff)
        elif kind == b'VP8L' and size is None:
            if length < 5 or body[0] != 0x2f:
                raise Invalid('damaged', 'WebP VP8L header')
            bits = int.from_bytes(body[1:5], 'little')
            size = ((bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1)
        position += 8 + length + (length & 1)
    if position != len(data) or size is None:
        raise Invalid('damaged', 'WebP without image')
    if canvas and canvas != size:
        raise Invalid('damaged', 'WebP canvas')
    return size


def inspect(data):
    """(extension, width, height) of an acceptable picture, else Invalid."""
    if len(data) > MAX_BODY:
        raise Invalid('too_large')
    if data.startswith(b'\x89PNG'):
        extension, (width, height) = 'png', png_size(data)
    elif data.startswith(b'\xff\xd8'):
        extension, (width, height) = 'jpg', jpeg_size(data)
    elif data.startswith(b'RIFF'):
        extension, (width, height) = 'webp', webp_size(data)
    else:
        raise Invalid('not_image')
    if not (1 <= width <= MAX_SIDE and 1 <= height <= MAX_SIDE) or width * height > MAX_PIXELS:
        raise Invalid('dimensions', f'{width}×{height}')
    return extension, width, height


# Settings ----------------------------------------------------------------------------------------------------------

def migrate(saved):
    """Bring saved settings of an older format to FORMAT. Format 0 is settings written before the format number
    (blur was a switch then: true became the usual 12 px)."""
    saved = dict(saved)
    version = saved.get('format', 0)
    if not isinstance(version, int) or version < 0:
        version = 0
    if version == 0:
        if isinstance(saved.get('blur'), bool):
            saved['blur'] = 12 if saved['blur'] else 0
        version = 1
    # Future formats: `if version == 1: ...; version = 2`.
    saved['format'] = FORMAT
    return saved


def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        raise Invalid('bad_value')
    return min(high, max(low, value))


def image_record(value):
    """A stored picture's record, or None when anything in it is off."""
    if not isinstance(value, dict) or not isinstance(value.get('file'), str) or not FILE_NAME.match(value['file']):
        return None
    try:
        return {'file': value['file'], 'type': KINDS[value['file'].rsplit('.', 1)[1]],
                'bytes': int(value['bytes']), 'width': int(value['width']), 'height': int(value['height']),
                'x': round(number(value.get('x', 50), 0, 100)), 'y': round(number(value.get('y', 50), 0, 100))}
    except (KeyError, TypeError, ValueError):
        return None


def clean(saved):
    """DEFAULTS overridden by every valid known value of `saved`; unknown keys and bad values are dropped."""
    result = dict(DEFAULTS)
    for name, allowed_values in (('theme', THEMES), ('palette', PALETTES), ('density', DENSITIES),
                                 ('background', BACKGROUNDS)):
        if saved.get(name) in allowed_values:
            result[name] = saved[name]
    if isinstance(saved.get('accent'), str) and ACCENT.match(saved['accent']):
        result['accent'] = saved['accent'].lower()
    for name, high in (('dim', DIM_MAX), ('blur', BLUR_MAX)):
        try:
            result[name] = number(saved.get(name, DEFAULTS[name]), 0, high)
        except Invalid:
            pass
    result['dim'] = round(result['dim'], 2)
    result['blur'] = round(result['blur'])
    result['image'] = image_record(saved.get('image'))
    if result['image'] is None:
        result['background'] = 'none'
    return result


def read_json(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('not an object')
    return value


def load():
    """The saved settings, cleaned; defaults when there are none. A damaged file is kept aside (settings.json.damaged)
    and the copy kept by the previous save is used when it is good."""
    path = settings_path()
    with LOCK:
        try:
            return clean(migrate(read_json(path)))
        except FileNotFoundError:
            return dict(DEFAULTS)
        except (OSError, ValueError, UnicodeDecodeError):
            pass
        damaged = path.with_name(path.name + '.damaged')
        try:
            data = path.read_bytes()
            if not damaged.exists() or damaged.read_bytes() != data:
                write_atomic(damaged, data)
        except OSError:
            pass
        try:
            return clean(migrate(read_json(path.with_name(path.name + '.previous'))))
        except (OSError, ValueError, UnicodeDecodeError):
            return dict(DEFAULTS)


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.corsu-tmp')
    try:
        with open(temporary, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def save(settings):
    """Write settings.json atomically, keeping the previous good copy next to it."""
    path = settings_path()
    with LOCK:
        settings = clean(settings)
        try:
            read_json(path)
            write_atomic(path.with_name(path.name + '.previous'), path.read_bytes())
        except (OSError, ValueError, UnicodeDecodeError):
            pass
        write_atomic(path, json.dumps(settings, indent=2).encode('utf-8'))
        return settings


def update(changes):
    """Apply the page's changes to the saved settings. Only known keys; a bad value refuses the whole change."""
    if not isinstance(changes, dict):
        raise Invalid('bad_value')
    with LOCK:
        settings = load()
        for name, allowed_values in (('theme', THEMES), ('palette', PALETTES), ('density', DENSITIES),
                                     ('background', BACKGROUNDS)):
            if name in changes:
                if changes[name] not in allowed_values:
                    raise Invalid('bad_value', name)
                settings[name] = changes[name]
        if 'accent' in changes:
            if changes['accent'] is not None and not (isinstance(changes['accent'], str) and ACCENT.match(changes['accent'])):
                raise Invalid('bad_value', 'accent')
            settings['accent'] = changes['accent'] and changes['accent'].lower()
        for name, high in (('dim', DIM_MAX), ('blur', BLUR_MAX)):
            if name in changes:
                settings[name] = number(changes[name], 0, high)
        if 'image' in changes:
            # The page may only move the focal point; the file and its facts are the server's.
            focus = changes['image']
            if not isinstance(focus, dict):
                raise Invalid('bad_value', 'image')
            if settings['image']:
                for axis in ('x', 'y'):
                    if axis in focus:
                        settings['image'][axis] = round(number(focus[axis], 0, 100))
        if settings['background'] == 'image' and not usable_image(settings):
            raise Invalid('no_image')
        return save(settings)


# Background picture -----------------------------------------------------------------------------------------------

def usable_image(settings):
    """The recorded picture's bytes when its file is there, a regular file, the recorded size, matching the hash in
    its name and still a valid picture; else None."""
    record = settings.get('image')
    if not record:
        return None
    path = folder() / record['file']
    try:
        if not path.is_file() or path.is_symlink() or path.stat().st_size != record['bytes']:
            return None
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest()[:16] != record['file'][len('background-'):][:16]:
            return None
        inspect(data)
    except (OSError, Invalid):
        return None
    return data


def store_background(data, x=50, y=50):
    """Check and keep a new picture; the previous one is removed only once the new one and the settings naming it
    are saved. Returns the new settings."""
    extension, width, height = inspect(data)
    name = f'background-{hashlib.sha256(data).hexdigest()[:16]}.{extension}'
    with LOCK:
        write_atomic(folder() / name, data)
        settings = load()
        settings.update(background='image', image={'file': name, 'type': KINDS[extension], 'bytes': len(data),
                                                   'width': width, 'height': height, 'x': x, 'y': y})
        settings = save(settings)
        remove_backgrounds(keep=name)
        return settings


def remove_backgrounds(keep=None):
    for path in folder().glob('background-*'):
        if path.name != keep and not path.is_dir():
            try:
                path.unlink()
            except OSError:
                pass


def remove_background():
    with LOCK:
        settings = load()
        settings.update(background='none', image=None)
        settings = save(settings)
        remove_backgrounds()
        return settings


def reset():
    """Every appearance file removed (settings, pictures, kept copies); nothing outside DATA/appearance is touched
    and nothing is followed through a link."""
    with LOCK:
        place = folder()
        if place.is_symlink():
            place.unlink()
            return dict(DEFAULTS)
        if place.is_dir():
            for path in place.iterdir():
                if path.is_symlink() or path.is_file():
                    try:
                        path.unlink()
                    except OSError:
                        pass
        return dict(DEFAULTS)


def public(settings):
    """Settings as the page gets them: a picture that is missing or damaged is left out (plain background)."""
    settings = dict(settings)
    if settings['image'] and usable_image(settings) is None:
        settings.update(image=None, background='none', image_problem=True)
    if settings.get('image'):
        settings['image'] = {**settings['image'], 'version': settings['image']['file'][len('background-'):][:16]}
    return settings


def body_limit(path):
    """The largest body the server reads for this POST path (checked against Content-Length before reading)."""
    return MAX_BODY if urllib.parse.urlsplit(path).path == '/api/appearance/background' else MAX_SETTINGS_BODY


JSON = 'application/json; charset=utf-8'


def handle(method, path, body, headers, allowed):
    """(status, body, content type) for an appearance route, or None for any other path.

    Every route needs allowed(): the picture too, which the page fetches with its X-Corsu header and shows through a
    blob: URL, so another site, another local account or a rebound domain name never reads it."""
    parts = urllib.parse.urlsplit(path)
    route = parts.path
    if route not in ('/appearance/settings', '/appearance/background', '/api/appearance',
                     '/api/appearance/background', '/api/appearance/reset', '/api/appearance/background/remove'):
        return None
    if not (allowed() if callable(allowed) else allowed):
        return 403, {'error': 'forbidden'}, JSON
    try:
        if method == 'GET' and route == '/appearance/settings':
            return 200, public(load()), JSON
        if method == 'GET' and route == '/appearance/background':
            settings = load()
            data = usable_image(settings)
            if data is None:
                return 404, {'error': 'not found'}, JSON
            return 200, data, settings['image']['type']
        if method != 'POST' or not route.startswith('/api/'):
            return 405, {'error': 'method not allowed'}, JSON
        body = body or b''
        if len(body) > body_limit(route):
            return 413, {'error': 'too_large'}, JSON
        if route == '/api/appearance/background':
            query = urllib.parse.parse_qs(parts.query)
            focus = []
            for axis in ('x', 'y'):
                value = query.get(axis, ['50'])[0]
                if not re.fullmatch(r'\d{1,3}', value) or int(value) > 100:
                    raise Invalid('bad_value', axis)
                focus.append(int(value))
            return 200, public(store_background(bytes(body), *focus)), JSON
        if route == '/api/appearance/reset':
            return 200, public(reset()), JSON
        if route == '/api/appearance/background/remove':
            return 200, public(remove_background()), JSON
        try:
            changes = json.loads(body or b'{}')
        except ValueError:
            raise Invalid('bad_value', 'JSON') from None
        if isinstance(changes, dict):
            changes = {name: value for name, value in changes.items() if name != 'language'}
        return 200, public(update(changes)), JSON
    except Invalid as error:
        status = {'too_large': 413, 'not_image': 415}.get(error.code, 400)
        return status, {'error': error.code}, JSON
    except OSError as error:
        return 500, {'error': 'not_saved', 'detail': error.strerror or str(error)}, JSON
