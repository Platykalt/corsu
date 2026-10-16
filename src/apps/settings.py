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


def encode(text, newline, bom=False):
    """The file's bytes with its own line endings for every line, added ones too, and its byte order mark."""
    if newline == '\r\n':
        text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    return (b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8')


def read_body(path):
    """(text without byte order mark, newline, had a byte order mark): a mark would hide the first line's key."""
    text, newline = read_text(path)
    return text.lstrip('\ufeff'), newline, text.startswith('\ufeff')


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
    text, newline, bom = read_body(path)
    name = f'{path}#[{section}]{key}'
    record = installer.state['files'].get(name)
    original = record['setting']['original'] if record else ini_get(text, section, key)
    installer.state['files'][name] = {'backup': None, 'mode': None, 'toggle': True, 'component': component,
                                      'setting': {'type': 'ini', 'file': str(path), 'section': section, 'key': key,
                                                  'original': original, 'installed': value},
                                      'installed_sha256': ''}
    corsu.save_state(installer.state)
    atomic_write(path, encode(ini_set(text, section, key, value, newline), newline, bom))


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
    corsu.save_state(installer.state)
    registry_set(key, name, (value, kind))


def revert(record):
    """Put one setting back if it still holds Corsu's value. True when the record can be dropped."""
    setting = record['setting']
    if setting['type'] == 'ini':
        path = Path(setting['file'])
        if not path.exists():
            return True
        try:
            text, newline, bom = read_body(path)
        except ValueError:
            return False
        if ini_get(text, setting['section'], setting['key']) == setting['installed']:
            atomic_write(path, encode(ini_set(text, setting['section'], setting['key'], setting['original'], newline),
                                      newline, bom))
        return True
    if setting['type'] == 'file':
        path = Path(setting['file'])
        if not path.exists():
            return True
        get, put = FILE_KINDS[setting['kind']]
        try:
            text, newline, bom = read_body(path)
            if get(text, setting['key']) == setting['installed']:
                atomic_write(path, encode(put(text, setting['key'], setting['original']), newline, bom))
        except Exception:
            return False
        return True
    if setting['type'] == 'defaults':
        if defaults_get(setting['domain'], setting['key']) == setting['installed']:
            defaults_put(setting['domain'], setting['key'], setting['original'])
        return True
    if setting['type'] == 'registry':
        current = registry_get(setting['key'], setting['name'])
        if current and list(current) == setting['installed']:
            registry_set(setting['key'], setting['name'], tuple(setting['original']) if setting['original'] else None)
        return True
    return False


# Values inside a program's own file. Each kind is a (read, write) pair on the file's text; write(text, None) removes
# the value Corsu added. The file must already exist: programs create it at their first start, and Corsu never
# invents a whole configuration file.
def _json_get(text, key):
    import json as _json
    node = _json.loads(text) if text.strip() else {}
    for part in key.split('/'):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _json_put(text, key, value):
    import json as _json
    document = _json.loads(text) if text.strip() else {}
    node, parts = document, key.split('/')
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    if value is None:
        node.pop(parts[-1], None)
    else:
        node[parts[-1]] = value
    return _json.dumps(document, indent=2, ensure_ascii=False) + '\n'


def _element(tag, attribute, name):
    import re as _re
    return _re.compile(rf'<{tag}\s+{attribute}="{_re.escape(name)}"\s*(?:/>|>(.*?)</{tag}>)', _re.S)


def _xml_get(text, spec):
    tag, attribute, name, _ = spec
    match = _element(tag, attribute, name).search(text)
    return (match.group(1) or '') if match else None


def _xml_put(text, spec, value):
    tag, attribute, name, parent = spec
    pattern = _element(tag, attribute, name)
    if value is None:
        import re as _re
        whole_line = _re.compile(r'^[ \t]*' + pattern.pattern + r'[ \t]*\r?\n', _re.S | _re.M)
        if whole_line.search(text):
            return whole_line.sub('', text, count=1)
        return pattern.sub('', text, count=1)
    element = f'<{tag} {attribute}="{name}">{value}</{tag}>'
    if pattern.search(text):
        return pattern.sub(lambda match: element, text, count=1)
    closing = text.rfind(f'</{parent}>')
    if closing < 0:
        raise ValueError(f'no </{parent}> element')
    line_start = text.rfind('\n', 0, closing) + 1
    before = text[line_start:closing]
    if before.strip():
        return text[:closing] + element + text[closing:]
    # On its own line, one step deeper than the closing tag.
    return text[:line_start] + before + '\t' + element + '\n' + text[line_start:]


def _line_get(text, key):
    import re as _re
    match = _re.search(rf'^{_re.escape(key)}\s*=\s*(.*?)\s*$', text, _re.M)
    return match.group(1) if match else None


def _line_put(text, key, value):
    import re as _re
    pattern = _re.compile(rf'^{_re.escape(key)}\s*=.*\n?', _re.M)
    if value is None:
        return pattern.sub('', text, count=1)
    if pattern.search(text):
        return pattern.sub(lambda match: f'{key} = {value}\n', text, count=1)
    return f'{key} = {value}\n' + text


def _xml_path_spans(text, steps):
    """Spans (outer start, outer end, inner start, inner end) of the elements along steps, each step a
    [tag, attribute, name] inside the previous one, outermost first; stops at the first one missing. The whole file
    must be well-formed XML. Elements on the path must not contain an element of their own tag."""
    import re as _re
    import xml.etree.ElementTree as _tree
    _tree.fromstring(text.encode('utf-8'))  # malformed: raises, and the file is never rewritten
    spans, start, end = [], 0, len(text)
    for tag, attribute, name in steps:
        opening = _re.compile(rf'<{tag}\s(?:[^>]*?\s)?{attribute}\s*=\s*(["\']){_re.escape(name)}\1[^>]*?(/?)>')
        match = opening.search(text, start, end)
        if not match:
            break
        if match.group(2):
            spans.append((match.start(), match.end(), match.end(), match.end()))
            break
        closing = text.find(f'</{tag}>', match.end(), end)
        if closing < 0:
            raise ValueError(f'no </{tag}>')
        spans.append((match.start(), closing + len(tag) + 3, match.end(), closing))
        start, end = match.end(), closing
    return spans


def _xml_path_get(text, steps):
    from xml.sax.saxutils import unescape
    spans = _xml_path_spans(text, steps)
    if len(spans) < len(steps):
        return None
    return unescape(text[spans[-1][2]:spans[-1][3]], {'&quot;': '"', '&apos;': "'"})


def _xml_path_put(text, steps, value):
    from xml.sax.saxutils import escape
    spans = _xml_path_spans(text, steps)
    tag, attribute, name = steps[-1]
    if value is None:
        if len(spans) < len(steps):
            return text
        start, end = spans[-1][:2]
        line_start, line_end = text.rfind('\n', 0, start) + 1, text.find('\n', end)
        line_end = len(text) if line_end < 0 else line_end + 1
        if not text[line_start:start].strip() and not text[end:line_end].strip():
            start, end = line_start, line_end
        return text[:start] + text[end:]
    quoted = escape(name, {'"': '&quot;'})
    element = f'<{tag} {attribute}="{quoted}">{escape(value)}</{tag}>'
    if len(spans) == len(steps):
        start, end = spans[-1][:2]
        return text[:start] + element + text[end:]
    if len(spans) < len(steps) - 1 or spans[-1][2] == spans[-1][3] and text[spans[-1][1] - 2] == '/':
        missing = steps[len(spans)]
        raise ValueError(f'no <{missing[0]} {missing[1]}="{missing[2]}">')
    inner_start, closing = spans[-1][2:]
    line_start = text.rfind('\n', 0, closing) + 1
    before = text[max(line_start, inner_start):closing]
    if line_start <= inner_start or before.strip():
        return text[:closing] + element + text[closing:]
    import re as _re
    siblings = _re.findall(r'\n([ \t]*)<', text[inner_start:line_start])
    indent = siblings[-1] if siblings else before + ' '
    return text[:line_start] + indent + element + '\n' + text[line_start:]


FILE_KINDS = {
    'json': (_json_get, _json_put),
    'xml': (_xml_get, _xml_put),
    'line': (_line_get, _line_put),
    # One value at a path of named elements, e.g. fre:ac's
    # <configuration name="default"><section name="Settings"><value name="Language">.
    'xml-path': (_xml_path_get, _xml_path_put),
}


def set_file_value(installer, component, path, kind, key, value):
    """One value in a program's own settings file, recorded with its original. ValueError if the file is missing
    or cannot be read safely."""
    path = Path(path)
    if not path.exists():
        raise ValueError(f'{path}: not created yet (start the program once)')
    text, newline, bom = read_body(path)
    get, put = FILE_KINDS[kind]
    spec = list(key) if isinstance(key, (list, tuple)) else key
    name = f'{path}#{json.dumps(spec)}'
    record = installer.state['files'].get(name)
    try:
        original = record['setting']['original'] if record else get(text, spec)
        changed = put(text, spec, value)
    except ValueError:
        raise
    except Exception as error:  # a malformed file: never rewritten
        raise ValueError(f'{path}: {error}') from None
    installer.state['files'][name] = {'backup': None, 'mode': None, 'toggle': True, 'component': component,
                                      'setting': {'type': 'file', 'kind': kind, 'file': str(path), 'key': spec,
                                                  'original': original, 'installed': value},
                                      'installed_sha256': ''}
    corsu.save_state(installer.state)
    atomic_write(path, encode(changed, newline, bom))


def defaults_get(domain, key):
    import subprocess
    result = subprocess.run(['defaults', 'read', domain, key], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def defaults_put(domain, key, value):
    import subprocess
    command = ['defaults', 'delete', domain, key] if value is None else ['defaults', 'write', domain, key, '-string', value]
    subprocess.run(command, capture_output=True, check=value is not None)


def set_defaults(installer, component, domain, key, value):
    """One macOS preference (`defaults write <domain> <key> -string <value>`), recorded with its original."""
    name = f'defaults:{domain}:{key}'
    record = installer.state['files'].get(name)
    original = record['setting']['original'] if record else defaults_get(domain, key)
    installer.state['files'][name] = {'backup': None, 'mode': None, 'toggle': True, 'component': component,
                                      'setting': {'type': 'defaults', 'domain': domain, 'key': key,
                                                  'original': original, 'installed': value},
                                      'installed_sha256': ''}
    corsu.save_state(installer.state)
    defaults_put(domain, key, value)
