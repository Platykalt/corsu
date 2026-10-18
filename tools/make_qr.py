#!/usr/bin/env python3
"""Build the QR codes of the window's « On the phone » page (src/app/qr/*.svg), with no outside service.

Each code points to the public guide of one platform on GitHub (the docs on main), never to the computer's own
address. The SVG files are committed, so the window needs no QR code at run time; rerun this only when an address in
TARGETS changes. `--check` compares the committed files with what this script makes now, and `--png` also writes a
PNG next to each SVG (in a folder you name), for a decoder such as zbarimg.

The encoder is written here with the standard library, after the QR Code specification (ISO/IEC 18004): byte mode,
error correction level M, the smallest version that fits (1 to 10), the mask with the lowest penalty.

    python3 tools/make_qr.py [--check] [--png FOLDER]
"""
import argparse
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'src/app/qr'
DOCS = 'https://github.com/Platykalt/corsu/blob/main/docs/'
# File name → address. Corsican uses the French guides (there are no Corsican ones).
TARGETS = {
    'android-fr.svg': DOCS + 'fr/telephone/android.md',
    'iphone-fr.svg': DOCS + 'fr/telephone/iphone.md',
    'android-en.svg': DOCS + 'en/phone/android.md',
    'iphone-en.svg': DOCS + 'en/phone/iphone.md',
}
QUIET = 4   # light modules around the code, as the specification asks

# Per version (index 1 to 10), level M: error correction codewords per block, and number of blocks.
ECC_PER_BLOCK = [None, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26]
BLOCKS = [None, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5]
FORMAT_M = 0   # the two format bits of level M


def raw_modules(version):
    """Modules left for data and error correction once the function patterns are drawn."""
    count = (16 * version + 128) * version + 64
    if version >= 2:
        aligns = version // 7 + 2
        count -= (25 * aligns - 10) * aligns - 55
        if version >= 7:
            count -= 36
    return count


def data_codewords(version):
    return raw_modules(version) // 8 - ECC_PER_BLOCK[version] * BLOCKS[version]


# Reed-Solomon over GF(256) with the polynomial 0x11D.
def gf_multiply(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def rs_divisor(degree):
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = gf_multiply(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = gf_multiply(root, 0x02)
    return result


def rs_remainder(data, divisor):
    result = [0] * len(divisor)
    for byte in data:
        factor = byte ^ result.pop(0)
        result.append(0)
        for i, coefficient in enumerate(divisor):
            result[i] ^= gf_multiply(coefficient, factor)
    return result


def codewords(text):
    """The data in byte mode, padded, split into blocks, each with its error correction, then interleaved."""
    data = text.encode('utf-8')
    for version in range(1, 11):
        capacity = data_codewords(version)
        if 4 + 8 + 8 * len(data) <= capacity * 8:
            break
    else:
        raise ValueError(f'too long for this encoder: {text}')
    bits = [0, 1, 0, 0] + [(len(data) >> i) & 1 for i in reversed(range(8))]
    for byte in data:
        bits += [(byte >> i) & 1 for i in reversed(range(8))]
    bits += [0] * min(4, capacity * 8 - len(bits))
    bits += [0] * (-len(bits) % 8)
    stream = [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(stream) < capacity:
        stream.append(pad)
        pad ^= 0xEC ^ 0x11

    blocks, ecc_length = BLOCKS[version], ECC_PER_BLOCK[version]
    raw = raw_modules(version) // 8
    short_blocks = blocks - raw % blocks
    short_length = raw // blocks
    divisor = rs_divisor(ecc_length)
    split, start = [], 0
    for i in range(blocks):
        length = short_length - ecc_length + (0 if i < short_blocks else 1)
        block = stream[start:start + length]
        start += length
        ecc = rs_remainder(block, divisor)
        if i < short_blocks:
            block.append(None)   # keeps the columns aligned; skipped when interleaving
        split.append(block + ecc)
    result = []
    for i in range(len(split[0])):
        for j, block in enumerate(split):
            if i != short_length - ecc_length or j >= short_blocks:
                result.append(block[i])
    return version, result


class Symbol:
    def __init__(self, version):
        self.version = version
        self.size = version * 4 + 17
        self.dark = [[False] * self.size for _ in range(self.size)]
        self.function = [[False] * self.size for _ in range(self.size)]

    def set_function(self, x, y, dark):
        self.dark[y][x] = dark
        self.function[y][x] = True

    def alignment_positions(self):
        if self.version == 1:
            return []
        count = self.version // 7 + 2
        step = (self.version * 8 + count * 3 + 5) // (count * 2 - 2) * 2
        return [6] + [self.size - 7 - i * step for i in reversed(range(count - 1))]

    def draw_function_patterns(self):
        size = self.size
        for i in range(size):
            self.set_function(6, i, i % 2 == 0)
            self.set_function(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < size and 0 <= y < size:
                        self.set_function(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        positions = self.alignment_positions()
        last = len(positions) - 1
        for i, cx in enumerate(positions):
            for j, cy in enumerate(positions):
                if (i, j) in ((0, 0), (0, last), (last, 0)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.set_function(cx + dx, cy + dy, max(abs(dx), abs(dy)) != 1)
        self.draw_format(0)   # reserves the format areas; drawn again with the chosen mask
        if self.version >= 7:
            remainder = self.version
            for _ in range(12):
                remainder = (remainder << 1) ^ ((remainder >> 11) * 0x1F25)
            bits = self.version << 12 | remainder
            for i in range(18):
                bit = (bits >> i) & 1 == 1
                a, b = size - 11 + i % 3, i // 3
                self.set_function(a, b, bit)
                self.set_function(b, a, bit)

    def draw_format(self, mask):
        data = FORMAT_M << 3 | mask
        remainder = data
        for _ in range(10):
            remainder = (remainder << 1) ^ ((remainder >> 9) * 0x537)
        bits = (data << 10 | remainder) ^ 0x5412
        bit = lambda i: (bits >> i) & 1 == 1
        size = self.size
        for i in range(6):
            self.set_function(8, i, bit(i))
        self.set_function(8, 7, bit(6))
        self.set_function(8, 8, bit(7))
        self.set_function(7, 8, bit(8))
        for i in range(9, 15):
            self.set_function(14 - i, 8, bit(i))
        for i in range(8):
            self.set_function(size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.set_function(8, size - 15 + i, bit(i))
        self.set_function(8, size - 8, True)   # the module that is always dark

    def draw_codewords(self, data):
        size, i, total = self.size, 0, len(data) * 8
        right = size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vertical in range(size):
                for j in range(2):
                    x = right - j
                    upward = (right + 1) & 2 == 0
                    y = size - 1 - vertical if upward else vertical
                    if not self.function[y][x] and i < total:
                        self.dark[y][x] = (data[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    def apply_mask(self, mask):
        rule = MASKS[mask]
        for y in range(self.size):
            for x in range(self.size):
                if not self.function[y][x] and rule(x, y):
                    self.dark[y][x] = not self.dark[y][x]

    def penalty(self):
        size, score = self.size, 0
        lines = [row[:] for row in self.dark] + [[self.dark[y][x] for y in range(size)] for x in range(size)]
        finder = [True, False, True, True, True, False, True]
        for line in lines:
            run = 1
            for i in range(1, size + 1):
                if i < size and line[i] == line[i - 1]:
                    run += 1
                    continue
                if run >= 5:
                    score += 3 + run - 5
                run = 1
            # A finder-like pattern with four light modules on one side (outside the symbol counts as light).
            padded = [False] * 4 + line + [False] * 4
            for i in range(len(padded) - 6):
                if padded[i:i + 7] == finder and (not any(padded[max(0, i - 4):i]) and i >= 4
                                                  or not any(padded[i + 7:i + 11]) and i + 11 <= len(padded)):
                    score += 40
        for y in range(size - 1):
            for x in range(size - 1):
                if self.dark[y][x] == self.dark[y][x + 1] == self.dark[y + 1][x] == self.dark[y + 1][x + 1]:
                    score += 3
        dark = sum(map(sum, self.dark))
        total = size * size
        score += ((abs(dark * 20 - total * 10) + total - 1) // total - 1) * 10
        return score


MASKS = [
    lambda x, y: (x + y) % 2 == 0,
    lambda x, y: y % 2 == 0,
    lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0,
    lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: x * y % 2 + x * y % 3 == 0,
    lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
]


def encode(text, mask=None):
    """The QR code of `text` as rows of booleans (True = dark), without the quiet zone. `mask` forces one mask."""
    version, data = codewords(text)
    best = None
    for candidate in range(8) if mask is None else [mask]:
        symbol = Symbol(version)
        symbol.draw_function_patterns()
        symbol.draw_codewords(data)
        symbol.apply_mask(candidate)
        symbol.draw_format(candidate)
        score = symbol.penalty()
        if best is None or score < best[0]:
            best = (score, symbol)
    return best[1].dark


def svg(text):
    rows = encode(text)
    side = len(rows) + 2 * QUIET
    path = ''.join(f'M{x + QUIET} {y + QUIET}h1v1h-1z' for y, row in enumerate(rows) for x, dark in enumerate(row) if dark)
    # Dark on a white square in every theme: phones read it best that way. Made by tools/make_qr.py.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" shape-rendering="crispEdges">'
            f'<title>{text}</title><rect width="{side}" height="{side}" fill="#fff"/>'
            f'<path fill="#000" d="{path}"/></svg>\n')


def png(text, scale=8):
    rows = encode(text)
    side = (len(rows) + 2 * QUIET) * scale
    raw = bytearray()
    for y in range(side):
        raw.append(0)
        my = y // scale - QUIET
        for x in range(side):
            mx = x // scale - QUIET
            dark = 0 <= my < len(rows) and 0 <= mx < len(rows) and rows[my][mx]
            raw.append(0 if dark else 255)

    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', side, side, 8, 0, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true', help='compare the committed files, change nothing')
    parser.add_argument('--png', type=Path, help='also write a PNG of each code in this folder')
    options = parser.parse_args(arguments)
    stale = []
    for name, url in TARGETS.items():
        target = FOLDER / name
        content = svg(url)
        if options.check:
            if not target.is_file() or target.read_text(encoding='utf-8') != content:
                stale.append(name)
        else:
            FOLDER.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
            print(f'{target.relative_to(ROOT)} → {url}')
        if options.png:
            options.png.mkdir(parents=True, exist_ok=True)
            (options.png / name.replace('.svg', '.png')).write_bytes(png(url))
    if stale:
        print('Out of date (run tools/make_qr.py): ' + ', '.join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
