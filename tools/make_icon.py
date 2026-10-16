#!/usr/bin/env python3
"""Build src/app/corsu.ico, the Windows icon of the Corsu shortcut, from src/app/corsu.svg.

The icon is committed, so packaging and installing need no image tool; rerun this only when the SVG changes.
Rasterising needs rsvg-convert (librsvg) or ImageMagick; the ICO container itself is written here with the
standard library. Every size is stored as PNG, which Windows reads since Vista.

    python3 tools/make_icon.py [--output PATH]
"""
import argparse
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / 'src/app/corsu.svg'
ICO = ROOT / 'src/app/corsu.ico'
SIZES = (16, 24, 32, 48, 64, 128, 256)
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def rasterise(svg, size, output):
    if shutil.which('rsvg-convert'):
        command = ['rsvg-convert', '--width', str(size), '--height', str(size), '--format', 'png',
                   '--output', str(output), str(svg)]
    elif shutil.which('magick') or shutil.which('convert'):
        tool = shutil.which('magick') or shutil.which('convert')
        command = [tool, '-background', 'none', '-density', str(72 * size * 4 // 64), str(svg),
                   '-resize', f'{size}x{size}', f'PNG32:{output}']
    else:
        raise SystemExit('Install rsvg-convert (librsvg) or ImageMagick to rasterise the icon.')
    subprocess.run(command, check=True)
    return output.read_bytes()


def strip_png(data):
    """Keep only the chunks that draw the image, so rebuilding gives the same bytes (no timestamps or tool names)."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError('rasteriser did not produce a PNG')
    kept, offset = [PNG_SIGNATURE], len(PNG_SIGNATURE)
    while offset < len(data):
        length, kind = struct.unpack('>I4s', data[offset:offset + 8])
        end = offset + 12 + length
        if kind in (b'IHDR', b'PLTE', b'tRNS', b'IDAT', b'IEND'):
            kept.append(data[offset:end])
        offset = end
    return b''.join(kept)


def png_size(data):
    width, height = struct.unpack('>II', data[16:24])
    return width, height


def build_ico(images):
    """An ICO file whose entries are the given PNG images, smallest first."""
    header = struct.pack('<HHH', 0, 1, len(images))
    offset = 6 + 16 * len(images)
    directory, payload = b'', b''
    for data in images:
        width, height = png_size(data)
        # Sizes of 256 are written as 0 in the one-byte fields.
        directory += struct.pack('<BBBBHHII', width % 256, height % 256, 0, 0, 1, 32, len(data), offset)
        payload += data
        offset += len(data)
    return header + directory + payload


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output', type=Path, default=ICO)
    parser.add_argument('--keep-png', type=Path, help='also save each rasterised size in this folder, to look at')
    arguments = parser.parse_args()
    images = []
    with tempfile.TemporaryDirectory() as directory:
        for size in SIZES:
            data = strip_png(rasterise(SVG, size, Path(directory) / f'{size}.png'))
            if png_size(data) != (size, size):
                raise SystemExit(f'Rasterised {size}px icon has size {png_size(data)}')
            zlib.decompress(b''.join(_idat(data)))  # A truncated image fails here, not on the user's desktop.
            images.append(data)
            if arguments.keep_png:
                arguments.keep_png.mkdir(parents=True, exist_ok=True)
                (arguments.keep_png / f'corsu-{size}.png').write_bytes(data)
    arguments.output.write_bytes(build_ico(images))
    print(f'Wrote {arguments.output} ({", ".join(map(str, SIZES))} px)', file=sys.stderr)


def _idat(data):
    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        length, kind = struct.unpack('>I4s', data[offset:offset + 8])
        if kind == b'IDAT':
            yield data[offset + 8:offset + 8 + length]
        offset += 12 + length


if __name__ == '__main__':
    main()
