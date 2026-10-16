"""PLACEHOLDER, replaced by agent A's module at integration (see minecraft/java/MULTIVERSION.md, Interfaces).

Same interface as the real module, but only the version in minecraft/java/VERSION (26.3) is supported, with the
pack src/minecraft.py built before several versions were handled (minecraft.pack_from_sources()).
"""
import json
import re

import corsu

SOURCE = corsu.ROOT / 'minecraft/java'


def _version():
    path = SOURCE / 'VERSION'
    return path.read_text(encoding='utf-8').strip() if path.exists() else None


def supported_versions():
    """Release ids Corsu builds a pack for (optional in the contract; src/minecraft.py uses it in its messages)."""
    return [_version()] if _version() else []


def target(version):
    if not version or version != _version():
        return None
    mcmeta = json.loads((SOURCE / 'pack.mcmeta').read_text(encoding='utf-8'))
    total = len(json.loads((SOURCE / 'co_fr.json').read_text(encoding='utf-8')))
    return {'lang_format': 'json', 'lang_file': 'assets/minecraft/lang/co_fr.json', 'language_code': 'co_fr',
            'pack_format': mcmeta['pack'].get('min_format'), 'mcmeta': mcmeta['pack'], 'supported': True,
            'coverage': {'translated': total, 'total': total}, 'note': 'placeholder'}


def build_pack(version):
    entry = target(version)
    if entry is None:
        raise ValueError(f'no pack for Minecraft {version}')
    import minecraft
    return minecraft.pack_from_sources(), {**entry['coverage'], 'missing': 0}


def base_version(text):
    """The game version inside a launcher's version id (fabric-loader-0.16.9-1.21.1 -> 1.21.1), or None."""
    # 1.x releases, or year-numbered ones (26.3); a loader's own version (0.16.9, 47.2.0) is not one.
    found = [token for token in re.findall(r'(?<![\w.])(\d+\.\d+(?:\.\d+)?)(?![\w.])', text or '')
             if token.startswith('1.') or 24 < int(token.split('.')[0]) < 40]
    return found[0] if found else None
