"""Reversible edits of one setting in a program's own configuration file.

Programs rewrite their configuration themselves, so Corsu never restores a whole file: it records the value a setting
had, sets its own, and on the way back puts the old value only while the setting still holds Corsu's value. A value
the person changed since is theirs and stays. Each edit is recorded in Corsu's state before the file is written, and
the file is replaced atomically, so an interrupted run can still be undone.
"""
import json
from pathlib import Path

import corsu


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.corsu-tmp')
    temp.write_bytes(data)
    temp.replace(path)


def read_text(path):
    """(text, newline) of a UTF-8 file, ('', '\\n') when missing. ValueError for anything Corsu cannot rewrite safely."""
    path = Path(path)
    if not path.exists():
        return '', '\n'
    data = path.read_bytes()
    bom = data.startswith(b'\xef\xbb\xbf')
    try:
        text = data[3:].decode('utf-8') if bom else data.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError(f'{path}: not UTF-8') from None
    return ('﻿' if bom else '') + text, '\r\n' if '\r\n' in text else '\n'


def ini_get(text, section, key):
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            current = stripped[1:-1]
        elif current == section and '=' in stripped and stripped.partition('=')[0].strip() == key:
            return stripped.partition('=')[2].strip()
    return None


def ini_set(text, section, key, value, newline='\n'):
    """Set (or remove, when value is None) one key of an INI-style file, leaving every other line as it is."""
    lines = text.splitlines()
    result, current, done, section_end = [], None, False, None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            if current == section and not done:
                section_end = len(result)
            current = stripped[1:-1]
        elif current == section and '=' in stripped and stripped.partition('=')[0].strip() == key:
            if not done and value is not None:
                result.append(f'{key}={value}')
            done = True
            continue
        result.append(line)
    if current == section and not done:
        section_end = len(result)
    if not done and value is not None:
        if section_end is None:
            if result and result[-1].strip():
                result.append('')
            result += [f'[{section}]', f'{key}={value}']
        else:
            # After the section's last non-empty line.
            position = section_end
            while position > 0 and not result[position - 1].strip():
                position -= 1
            result.insert(position, f'{key}={value}')
    if value is None:
        result = drop_empty_section(result, section)
    return newline.join(result) + (newline if result else '')


def drop_empty_section(lines, section):
    """An empty [section] left after removing its last key goes too, with the blank line before it."""
    for index, line in enumerate(lines):
        if line.strip() == f'[{section}]':
            rest = lines[index + 1:]
            following = next((i for i, item in enumerate(rest) if item.strip().startswith('[')), len(rest))
            if not any(item.strip() for item in rest[:following]):
                start = index - 1 if index > 0 and not lines[index - 1].strip() else index
                return lines[:start] + rest[following:]
    return lines


def set_ini(installer, component, path, section, key, value):
    """Set one INI key for a component; recorded with its original value. Raises ValueError if unreadable."""
    path = Path(path)
    text, newline = read_text(path)
    name = f'{path}#[{section}]{key}'
    record = installer.state['files'].get(name)
    original = record['original'] if record else ini_get(text, section, key)
    installer.state['files'][name] = {'backup': None, 'mode': None, 'toggle': True, 'component': component,
                                      'setting': {'type': 'ini', 'file': str(path), 'section': section, 'key': key,
                                                  'original': original, 'installed': value},
                                      'installed_sha256': ''}
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    atomic_write(path, ini_set(text, section, key, value, newline).encode('utf-8'))


def registry_get(key, name):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            return winreg.QueryValueEx(handle, name)
    except OSError:
        return None


def registry_set(key, name, value):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as handle:
        if value is None:
            try:
                winreg.DeleteValue(handle, name)
            except OSError:
                pass
        else:
            winreg.SetValueEx(handle, name, 0, value[1], value[0])


def set_registry(installer, component, key, name, value, kind):
    """Set one HKEY_CURRENT_USER value for a component (Windows), recorded with its original value and type."""
    record_name = f'HKCU\\{key}\\{name}'
    record = installer.state['files'].get(record_name)
    original = record['setting']['original'] if record else registry_get(key, name)
    installer.state['files'][record_name] = {'backup': None, 'mode': None, 'toggle': True, 'component': component,
                                             'setting': {'type': 'registry', 'key': key, 'name': name,
                                                         'original': list(original) if original else None,
                                                         'installed': [value, kind]},
                                             'installed_sha256': ''}
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    registry_set(key, name, (value, kind))


def revert(record):
    """Put one setting back if it still holds Corsu's value. True when the record can be dropped."""
    setting = record['setting']
    if setting['type'] == 'ini':
        path = Path(setting['file'])
        if not path.exists():
            return True
        try:
            text, newline = read_text(path)
        except ValueError:
            return False
        if ini_get(text, setting['section'], setting['key']) == setting['installed']:
            atomic_write(path, ini_set(text, setting['section'], setting['key'], setting['original'],
                                       newline).encode('utf-8'))
        return True
    if setting['type'] == 'registry':
        current = registry_get(setting['key'], setting['name'])
        if current and list(current) == setting['installed']:
            registry_set(setting['key'], setting['name'], tuple(setting['original']) if setting['original'] else None)
        return True
    return False
