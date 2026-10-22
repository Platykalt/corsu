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
                changed = put(text, setting['key'], setting['original'])
                if setting.get('created') and not changed.strip():
                    # A file Corsu created for its own block, empty again: it goes, as it was before.
                    path.unlink()
                else:
                    atomic_write(path, encode(changed, newline, bom))
        except Exception:
            return False
        return True
    if setting['type'] == 'defaults':
        if defaults_get(setting['domain'], setting['key']) == setting['installed']:
            defaults_put(setting['domain'], setting['key'], setting['original'])
        return True
    if setting['type'] == 'defaults-plist':
        try:
            current = defaults_value(setting['domain'], setting['key'])
        except ValueError:
            return False  # unreadable now: kept, tried again next time
        if current is not None and plist_fragment(current) == setting['installed']:
            original = setting['original']
            defaults_write_value(setting['domain'], setting['key'],
                                 None if original is None else plist_value(original))
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


def _java_prefs_entry(text, key):
    """The <entry key=… value=…/> of one key in a Java Preferences file (java.util.prefs on Linux: prefs.xml of one
    node, <map><entry key="…" value="…"/>…</map>), as (regex match, element), or (None, None). The whole file must be
    a well-formed <map>."""
    import re as _re
    import xml.etree.ElementTree as _tree
    if _tree.fromstring(text.encode('utf-8')).tag != 'map':
        raise ValueError('not a Java preferences file')
    for match in _re.finditer(r'<entry\b[^>]*?(?:/>|>\s*</entry>)', text):
        element = _tree.fromstring(match.group(0))
        if element.get('key') == key:
            return match, element
    return None, None


def _java_prefs_get(text, key):
    element = _java_prefs_entry(text, key)[1]
    return None if element is None else element.get('value')


def _java_prefs_put(text, key, value):
    import re as _re
    from xml.sax.saxutils import escape
    match, _ = _java_prefs_entry(text, key)
    if value is None:
        if not match:
            return text
        start, end = match.span()
        line_start, line_end = text.rfind('\n', 0, start) + 1, text.find('\n', end)
        line_end = len(text) if line_end < 0 else line_end + 1
        if not text[line_start:start].strip() and not text[end:line_end].strip():
            start, end = line_start, line_end
        return text[:start] + text[end:]
    # Written as Java writes it: double quotes, and line breaks kept through character references.
    quoted = {'"': '&quot;', '\n': '&#10;', '\r': '&#13;', '\t': '&#9;'}
    element = f'<entry key="{escape(key, quoted)}" value="{escape(value, quoted)}"/>'
    if match:
        return text[:match.start()] + element + text[match.end():]
    empty = _re.search(r'<map\b([^>]*?)\s*/>', text)
    if empty:  # what Java writes for a node without keys: <map MAP_XML_VERSION="1.0"/>
        return text[:empty.start()] + f'<map{empty.group(1)}>\n  {element}\n</map>' + text[empty.end():]
    closing = text.rfind('</map>')
    line_start = text.rfind('\n', 0, closing) + 1
    if text[line_start:closing].strip():
        return text[:closing] + element + text[closing:]
    siblings = _re.findall(r'\n([ \t]*)<entry\b', text[:line_start])
    indent = siblings[-1] if siblings else text[line_start:closing] + '  '
    return text[:line_start] + indent + element + '\n' + text[line_start:]


def _block_span(text, name):
    import re as _re
    quoted = _re.escape(name)
    return _re.search(rf'^# corsu:begin {quoted}[ \t]*\r?\n(.*?)^# corsu:end {quoted}[ \t]*(?:\r?\n|\Z)', text,
                      _re.M | _re.S)


def _block_get(text, name):
    """The lines between `# corsu:begin <name>` and `# corsu:end <name>`, or None when there is no such block."""
    match = _block_span(text, name)
    return match.group(1).replace('\r\n', '\n') if match else None


def _block_put(text, name, value):
    """Replace, add (at the end) or remove (value None) one marked block; every line outside it stays as it is."""
    match = _block_span(text, name)
    if value is None:
        return text[:match.start()] + text[match.end():] if match else text
    body = value if not value or value.endswith('\n') else value + '\n'
    block = f'# corsu:begin {name}\n{body}# corsu:end {name}\n'
    if match:
        return text[:match.start()] + block + text[match.end():]
    return text + ('' if not text or text.endswith('\n') else '\n') + block


def _toml_header(line):
    import re as _re
    match = _re.match(r'\s*(\[\[?)\s*([^\[\]]+?)\s*\]\]?\s*(?:#.*)?$', line)
    if not match:
        return None
    # An array of tables is never one of Corsu's sections.
    return ('[[' + match.group(2)) if match.group(1) == '[[' else match.group(2)


def _toml_lines(text, spec):
    """(lines, index of the key's line or None, index where the section ends or None when it is missing). The
    section '' is the top of the file, before the first table."""
    import re as _re
    section, name = spec
    lines = text.splitlines(keepends=True)
    key = _re.compile(rf'\s*{_re.escape(name)}\s*=')
    current, found, end = '', None, None
    for index, line in enumerate(lines):
        header = _toml_header(line)
        if header is not None:
            if current == section and end is None:
                end = index
            current = header
            continue
        if current == section and found is None and key.match(line):
            found = index
    if current == section and end is None:
        end = len(lines)
    return lines, found, end


def _toml_get(text, spec):
    """The raw value of one key of a TOML table (`["general", "language"]` → '"co"'), as written; None when absent."""
    lines, found, _ = _toml_lines(text, spec)
    if found is None:
        return None
    return lines[found].split('=', 1)[1].strip()


def _toml_put(text, spec, value):
    """Set one key of a TOML table, keeping the line's own spacing; None removes the line (and the table header when
    nothing is left in it). Other lines stay byte for byte."""
    section, name = spec
    lines, found, end = _toml_lines(text, spec)
    newline = '\r\n' if '\r\n' in text else '\n'
    if value is None:
        if found is None:
            return text
        del lines[found]
        if section:
            start = next(index for index, line in enumerate(lines) if _toml_header(line) == section)
            following = next((index for index in range(start + 1, len(lines)) if _toml_header(lines[index]) is not None),
                             len(lines))
            if not any(line.strip() for line in lines[start + 1:following]):
                begin = start - 1 if start > 0 and not lines[start - 1].strip() else start
                del lines[begin:following]
        return ''.join(lines)
    if found is not None:
        line = lines[found]
        prefix = line.split('=', 1)[0] + '='
        spacing = ' ' if line.split('=', 1)[1].startswith(' ') else ''
        ending = line[len(line.rstrip('\r\n')):]
        lines[found] = f'{prefix}{spacing}{value}{ending}'
        return ''.join(lines)
    entry = f'{name} = {value}{newline}'
    if end is None:
        if lines and not lines[-1].endswith(('\n', '\r')):
            lines[-1] += newline
        if lines and lines[-1].strip():
            lines.append(newline)
        lines += [f'[{section}]{newline}', entry]
        return ''.join(lines)
    position = end
    while position > 0 and not lines[position - 1].strip():
        position -= 1
    if position > 0 and not lines[position - 1].endswith(('\n', '\r')):
        lines[position - 1] += newline
    lines.insert(position, entry)
    return ''.join(lines)


FILE_KINDS = {
    'json': (_json_get, _json_put),
    'xml': (_xml_get, _xml_put),
    'line': (_line_get, _line_put),
    # One value at a path of named elements, e.g. fre:ac's
    # <configuration name="default"><section name="Settings"><value name="Language">.
    'xml-path': (_xml_path_get, _xml_path_put),
    # One key of a Java Preferences node on Linux (~/.java/.userPrefs/<node>/prefs.xml), e.g. PDFsam's locale.
    'java-prefs': (_java_prefs_get, _java_prefs_put),
    # A block of lines between `# corsu:begin <name>` and `# corsu:end <name>` in a file the person shares with Corsu,
    # e.g. uwsm's ~/.config/uwsm/env-hyprland.
    'block': (_block_get, _block_put),
    # One key of a TOML table, [section, key], the value as TOML writes it ('"co"', 'true', '0.9').
    'toml': (_toml_get, _toml_put),
}


def set_block(installer, component, path, name, value):
    """One marked block in a file the person may also edit, recorded like set_file_value(). Unlike a program's
    settings file, the file may be missing (uwsm reads it when present): Corsu then creates it, and removes it again
    when taking its last block out. ValueError if the file cannot be read safely."""
    path = Path(path)
    text, newline, bom = read_body(path)
    name_key = f'{path}#{json.dumps(name)}'
    record = installer.state['files'].get(name_key)
    if record:
        original, created = record['setting']['original'], record['setting'].get('created', False)
    else:
        original = _block_get(text, name)
        # Created by Corsu: missing, or holding nothing but Corsu's own blocks.
        import re as _re
        rest = _re.sub(r'^# corsu:begin (\S+)[ \t]*\r?\n.*?^# corsu:end \1[ \t]*(?:\r?\n|\Z)', '', text, flags=_re.M | _re.S)
        created = not path.exists() or not rest.strip()
    body = value if not value or value.endswith('\n') else value + '\n'
    installer.state['files'][name_key] = {'backup': None, 'mode': None, 'toggle': True, 'component': component,
                                          'setting': {'type': 'file', 'kind': 'block', 'file': str(path), 'key': name,
                                                      'original': original, 'installed': body, 'created': created},
                                          'installed_sha256': ''}
    corsu.save_state(installer.state)
    atomic_write(path, encode(_block_put(text, name, body), newline, bom))


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


# Typed macOS preferences: an array such as a per-application AppleLanguages, or any other property list value, kept
# with its exact type. Read with `defaults export <domain> -` (the whole domain as an XML property list, parsed with
# plistlib) and written with `defaults write <domain> <key> '<XML fragment>'`, so cfprefsd, which caches preferences,
# stays the only one writing the file. The values are recorded in Corsu's state as XML fragments (`<array>…</array>`),
# which keep strings, numbers, booleans, dates and data apart. Only one application's own domain: the global domain
# (the system's language list) is never written.
GLOBAL_DOMAINS = ('-g', '-globaldomain', 'nsglobaldomain', '.globalpreferences')


def check_app_domain(domain):
    name = str(domain).strip()
    if not name or name.lower() in GLOBAL_DOMAINS or name.lower().endswith(('/.globalpreferences',
                                                                          '/.globalpreferences.plist')):
        raise ValueError(f'{domain!r}: not an application\'s own preferences')
    return name


def plist_fragment(value):
    """The XML element of one property list value: ['co', 'fr'] -> '<array><string>co</string>…</array>'."""
    import plistlib
    import re as _re
    document = plistlib.dumps(value, fmt=plistlib.FMT_XML, sort_keys=False).decode('utf-8')
    inner = document[document.index('<plist version="1.0">') + len('<plist version="1.0">'):document.rindex('</plist>')]
    return _re.sub(r'>\s+<', '><', inner.strip())


def plist_value(fragment):
    import plistlib
    return plistlib.loads(('<?xml version="1.0" encoding="UTF-8"?>\n<plist version="1.0">'
                           f'{fragment}</plist>').encode('utf-8'))


def defaults_value(domain, key):
    """The typed value of one key (None when absent). ValueError when `defaults` cannot read the domain."""
    import plistlib
    import subprocess
    result = subprocess.run(['defaults', 'export', str(domain), '-'], capture_output=True)
    if result.returncode != 0:
        if b'does not exist' in result.stderr:
            return None
        raise ValueError(f'defaults export {domain}: {result.stderr.decode("utf-8", "replace").strip()}')
    try:
        values = plistlib.loads(result.stdout) if result.stdout.strip() else {}
    except Exception as error:
        raise ValueError(f'defaults export {domain}: {error}') from None
    return values.get(key) if isinstance(values, dict) else None


def defaults_write_value(domain, key, value):
    """Write one typed value in an application's own domain (None: delete the key)."""
    import subprocess
    domain = check_app_domain(domain)
    if value is None:
        subprocess.run(['defaults', 'delete', domain, key], capture_output=True)
    else:
        subprocess.run(['defaults', 'write', domain, key, plist_fragment(value)], capture_output=True, check=True)


def set_defaults_value(installer, component, domain, key, value):
    """One typed preference of an application (e.g. the array AppleLanguages), recorded with its original value and
    type, or its absence. Put back by revert() only while it still holds Corsu's value."""
    domain = check_app_domain(domain)
    name = f'defaults:{domain}:{key}'
    record = installer.state['files'].get(name)
    if record:
        original = record['setting']['original']
    else:
        current = defaults_value(domain, key)
        original = None if current is None else plist_fragment(current)
    installer.state['files'][name] = {'backup': None, 'mode': None, 'toggle': True, 'component': component,
                                      'setting': {'type': 'defaults-plist', 'domain': domain, 'key': key,
                                                  'original': original, 'installed': plist_fragment(value)},
                                      'installed_sha256': ''}
    corsu.save_state(installer.state)
    defaults_write_value(domain, key, value)
