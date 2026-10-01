#!/usr/bin/env python3
"""Local, reversible Corsican UI overlay. No cloud translation or account access."""
import argparse
import configparser
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import struct
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

import engine
from engine import make_mo, make_qm, read_mo, read_qm, translate, WORDS

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent
HOME = Path.home()
PLATFORM = 'windows' if sys.platform == 'win32' else 'macos' if sys.platform == 'darwin' else 'linux'
if PLATFORM == 'windows':
    DATA = Path(os.environ.get('LOCALAPPDATA', HOME / 'AppData/Local')) / 'corsu'
    CONFIG = Path(os.environ.get('APPDATA', HOME / 'AppData/Roaming'))
elif PLATFORM == 'macos':
    DATA = HOME / 'Library/Application Support/corsu'
    CONFIG = HOME / 'Library/Application Support'
else:
    DATA = HOME / '.local/share/corsu'
    CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', HOME / '.config'))
STATE = DATA / 'installation.json'


def french():
    """Speak French when the computer does; CORSU_LANG=en or fr overrides."""
    import locale
    choice = os.environ.get('CORSU_LANG') or os.environ.get('LANGUAGE') or os.environ.get('LC_ALL') \
        or os.environ.get('LC_MESSAGES') or os.environ.get('LANG') or (locale.getlocale()[0] or '')
    return choice.lower().startswith(('fr', 'co', 'french'))


def t(english, francais):
    return francais if french() else english
LEXICON = engine.LEXICON
FRENCH_CATALOGS = Path('/usr/share/locale/fr/LC_MESSAGES')
QT_TRANSLATIONS = Path('/usr/share/qt6/translations')
CATALOG_SUFFIX = 'locale/co/LC_MESSAGES'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_zip(path):
    """Also handle Mozilla's optimized ZIPs, whose central directory is first."""
    raw = Path(path).read_bytes()
    try:
        return zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        end = raw.rfind(b'PK\x05\x06')
        if end < 0:
            raise
        fields = list(struct.unpack('<4s4H2IH', raw[end:end + 22]))
        offset, size = fields[6], fields[5]
        if raw[offset:offset + 4] != b'PK\x01\x02':
            raise ValueError('Unsupported omni.ja central directory')
        rebuilt = raw[:end] + raw[offset:offset + size]
        fields[6] = end
        rebuilt += struct.pack('<4s4H2IH', *fields) + raw[end + 22:]
        return zipfile.ZipFile(io.BytesIO(rebuilt))


FTL_ENTRY = re.compile(r'^(\s*(?:[\w-]+|\.[\w-]+)\s*=[ \t]*)([^\r\n]*)(\r?\n)?$')
FTL_VARIANT = re.compile(r'^(\s*\*?\[[\w-]+\]\s+)([^\r\n]+)(\r?\n)?$')


def ftl_units(text):
    """Group each Fluent entry with its indented continuation lines.

    Indented attribute definitions such as `.label = …` start their own entry.
    """
    unit = []
    for line in text.splitlines(keepends=True):
        if unit and re.match(r'^[ \t]+\S', line) and not re.match(r'^\s*\.?[\w-]+\s*=', line):
            unit.append(line)
            continue
        if unit:
            yield unit
        unit = [line]
    if unit:
        yield unit


def ftl_messages(text):
    """Split a Fluent file into (id, block) pairs; comments and blanks get id None."""
    block, ident = [], None
    for line in text.splitlines(keepends=True):
        start = re.match(r'^(-?[A-Za-z][\w-]*)\s*=', line)
        if start or (line.strip() and not line[0].isspace()) or (ident is None and block and not line.strip()):
            if block:
                yield ident, ''.join(block)
            block, ident = [], start[1] if start else None
        block.append(line)
    if block:
        yield ident, ''.join(block)


def merge_ftl(english, french):
    """Keep the English file's structure and use each French message whose id still exists,
    so a French pack from another Firefox version never drops or breaks messages."""
    known = {ident: block for ident, block in ftl_messages(french) if ident}
    output, merged = [], 0
    for ident, block in ftl_messages(english):
        if ident in known:
            replacement = known[ident]
            # Trailing blank lines belong to the English layout.
            tail = block[len(block.rstrip('\n')):]
            block = replacement.rstrip('\n') + (tail or '\n')
            merged += 1
        output.append(block)
    return ''.join(output), merged


def patch_ftl(text):
    """Translate literal Fluent values, single line or multiline. Never identifiers,
    selectors, placeables or access keys."""
    count = 0
    output = []
    for unit in ftl_units(text):
        entry = FTL_ENTRY.match(unit[0])
        selector = any('->' in line or FTL_VARIANT.match(line) or line.strip() == '}' for line in unit)
        if entry and not selector and not re.search(r'\.(accesskey|key)\s*=', entry[1]):
            parts = [entry[2].strip()] + [line.strip() for line in unit[1:]]
            value = ' '.join(part for part in parts if part)
            result = translate(value) if value else value
            if value and result != value:
                count += 1
                output.append(entry[1].rstrip() + ' ' + result + ('\n' if unit[-1].endswith('\n') else ''))
                continue
        for line in unit:
            variant = FTL_VARIANT.match(line)
            if variant:
                result = translate(variant[2])
                if result != variant[2]:
                    count += 1
                    line = variant[1] + result + (variant[3] or '')
            output.append(line)
    return ''.join(output), count


class Installer:
    def __init__(self):
        DATA.mkdir(parents=True, exist_ok=True)
        self.state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'files': {}}

    def write(self, path, data, mode=None, toggle=False):
        path = Path(path)
        data = data.encode() if isinstance(data, str) else data
        key = str(path)
        record = self.state['files'].get(key)
        if record and path.exists() and digest(path.read_bytes()) != record['installed_sha256']:
            raise RuntimeError(f'File changed since installation; preserving it: {path}')
        if record is None:
            record = {'backup': None, 'mode': None}
            if path.exists():
                backup = DATA / 'backups' / digest(key.encode())
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup)
                record.update(backup=str(backup), mode=path.stat().st_mode & 0o777)
            self.state['files'][key] = record
        path.parent.mkdir(parents=True, exist_ok=True)
        # Toggles are the switches that activate Corsican; `disable` reverts only those.
        record['toggle'] = record.get('toggle', False) or toggle
        record['installed_sha256'] = digest(data)
        # Record backup before mutation, so an interrupted install remains reversible.
        STATE.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
        temp = path.with_name(path.name + '.corsu-tmp')
        temp.write_bytes(data)
        temp.chmod(mode if mode is not None else (record['mode'] or 0o644))
        temp.replace(path)

    def json_settings(self, path, changes, toggle=False):
        path = Path(path)
        document = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        previous = self.state['files'].get(str(path), {})
        saved = previous.get('json_changes', {})
        for field, value in changes.items():
            node = document
            parts = field.split('/')
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            if field not in saved:
                saved[field] = {'existed': parts[-1] in node, 'original': node.get(parts[-1])}
            saved[field]['installed'] = value
            node[parts[-1]] = value
        # App-managed files change with window positions and ordinary settings.
        # Preserve those changes on subsequent installation and uninstallation.
        if previous and path.exists() and 'json_changes' in previous:
            previous['installed_sha256'] = digest(path.read_bytes())
        self.write(path, json.dumps(document, indent=4) + '\n', toggle=toggle)
        self.state['files'][str(path)]['json_changes'] = saved
        STATE.write_text(json.dumps(self.state, indent=2), encoding='utf-8')

    def add_line(self, path, line):
        """Add one line to a file the user owns, such as ~/.bashrc. Uninstall removes only that line."""
        path = Path(path)
        text = path.read_text(encoding='utf-8') if path.exists() else ''
        if line not in text.splitlines():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + ('' if not text or text.endswith('\n') else '\n') + line + '\n', encoding='utf-8')
        self.state['files'][str(path)] = {'backup': None, 'mode': None, 'toggle': False, 'line': line}
        STATE.write_text(json.dumps(self.state, indent=2), encoding='utf-8')

    def tree(self, path, source):
        """Install a whole directory, such as a macOS application bundle. Uninstall removes it."""
        path = Path(path)
        record = self.state['files'].get(str(path))
        if path.exists() and record is None:
            raise RuntimeError(f'Preserving an existing application not created by Corsu: {path}')
        self.state['files'][str(path)] = {'backup': None, 'mode': None, 'tree': True, 'toggle': False}
        STATE.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
        if path.exists():
            shutil.rmtree(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, path, symlinks=True)

    def external_file(self, path, original):
        """Record a file changed by the official Discord installer."""
        path = Path(path)
        key = str(path)
        if key not in self.state['files']:
            backup = DATA / 'backups' / digest(key.encode())
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(original)
            self.state['files'][key] = {'backup': str(backup), 'mode': path.stat().st_mode & 0o777}
        self.state['files'][key]['installed_sha256'] = digest(path.read_bytes())
        STATE.write_text(json.dumps(self.state, indent=2), encoding='utf-8')


def best_translation(source, fallback):
    """Prefer the English source label, fall back to the French one, else give up."""
    for candidate in (source, fallback):
        if not candidate:
            continue
        result = translate(candidate)
        # Never let a generic label alter a variable or markup contract.
        if result != candidate and engine.signature(result) == engine.signature(source or candidate):
            return result
    return None


def gettext_catalogs(installer, stats):
    """Build user gettext catalogs for Corsican from the installed French ones."""
    header = ('Content-Type: text/plain; charset=UTF-8\nLanguage: co\n'
              'Plural-Forms: nplurals=2; plural=(n != 1);\n').encode()
    for source in sorted(FRENCH_CATALOGS.glob('*.mo')):
        try:
            entries = read_mo(source.read_bytes())
        except (ValueError, struct.error, IndexError):
            continue
        translated = {b'': header}
        for key, value in entries.items():
            if not key:
                continue
            context, marker, body = key.partition(b'\x04')
            singular, _, plural = (body if marker else key).partition(b'\x00')
            forms = value.split(b'\x00')
            stats['source_entries'] += 1
            try:
                if plural:
                    if len(forms) < 2:
                        continue
                    results = [best_translation(text.decode(), fallback.decode())
                               for text, fallback in ((singular, forms[0]), (plural, forms[1]))]
                    if None in results:
                        continue
                    translated[key] = '\x00'.join(results).encode()
                else:
                    result = best_translation(singular.decode(), forms[0].decode())
                    if result is None:
                        continue
                    translated[key] = result.encode()
            except UnicodeDecodeError:
                continue
        if len(translated) > 1:
            installer.write(HOME / '.local/share' / CATALOG_SUFFIX / source.name, make_mo(translated))
            stats['catalogs'] += 1
            stats['translated_entries'] += len(translated) - 1


def qt_catalogs(installer, stats, sources, target, rename=None):
    """Build Qt `.qm` catalogs: KDE framework dialogs and Qt's own standard buttons."""
    for source in sorted(sources):
        try:
            catalog = read_qm(source.read_bytes())
        except (ValueError, struct.error, IndexError):
            continue
        messages = []
        for message in catalog['messages']:
            english = message.get('source', '')
            forms = message['translations']
            if not english or not forms:
                continue
            stats['qt_source_entries'] += 1
            if len(forms) > 1:
                results = [best_translation('', form) for form in forms[:2]]
            else:
                results = [best_translation(english, forms[0])]
            if None in results:
                continue
            messages.append({**message, 'translations': results})
        if not messages:
            continue
        name = rename(source.name) if rename else source.name
        installer.write(target / name, make_qm(messages))
        stats['qt_catalogs'] += 1
        stats['qt_translated_entries'] += len(messages)


TERMINAL_OFF = 'terminal-off'
POSIX_HOOK = """# Corsu: the Corsu app can switch the terminal back to French, for a while or until switched on again.
corsu_off="{off}"
if [ -f "$corsu_off" ]; then
    corsu_until=$(cat "$corsu_off" 2>/dev/null)
    if [ -z "$corsu_until" ] || [ "$(date +%s)" -lt "$corsu_until" ]; then
        LANGUAGE=$(printf '%s' "${{LANGUAGE:-}}" | sed -e 's/^co://' -e 's/:co:/:/g' -e 's/:co$//'); export LANGUAGE
    else
        rm -f "$corsu_off"
    fi
fi
unset corsu_off corsu_until
"""
FISH_HOOK = """# Corsu: the Corsu app can switch the terminal back to French, for a while or until switched on again.
set -l corsu_off "{off}"
if test -f $corsu_off
    set -l corsu_until (cat $corsu_off 2>/dev/null)
    if test -z "$corsu_until"; or test (date +%s) -lt $corsu_until
        set -gx LANGUAGE (string replace -r '^co:' '' -- "$LANGUAGE")
    else
        rm -f $corsu_off
    end
end
"""


def terminal_hooks(installer):
    """Let new terminals follow the terminal switch in the Corsu app (bash, zsh and fish)."""
    off = DATA / TERMINAL_OFF
    hook = DATA / 'terminal.sh'
    installer.write(hook, POSIX_HOOK.format(off=off))
    installer.write(CONFIG / 'fish/conf.d/corsu.fish', FISH_HOOK.format(off=off))
    line = f'[ -f {shlex.quote(str(hook))} ] && . {shlex.quote(str(hook))}  # Corsu'
    for name in ('.bashrc', '.zshrc'):
        if (HOME / name).exists():
            installer.add_line(HOME / name, line)


def kde(installer, qt_system=False):
    stats = {'catalogs': 0, 'translated_entries': 0, 'source_entries': 0, 'desktop_entries': 0,
             'qt_catalogs': 0, 'qt_translated_entries': 0, 'qt_source_entries': 0}
    gettext_catalogs(installer, stats)
    qt_catalogs(installer, stats, FRENCH_CATALOGS.glob('*.qm'), HOME / '.local/share' / CATALOG_SUFFIX)
    if qt_system:
        qt_catalogs(installer, stats, QT_TRANSLATIONS.glob('*_fr.qm'), DATA / 'qt6/translations',
                    rename=lambda name: name.replace('_fr.qm', '_co.qm'))
    locale = HOME / '.config/plasma-localerc'
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    if locale.exists():
        config.read(locale)
    if not config.has_section('Translations'):
        config.add_section('Translations')
    config['Translations']['LANGUAGE'] = 'co:fr'
    buffer = io.StringIO()
    config.write(buffer, space_around_delimiters=False)
    installer.write(locale, buffer.getvalue(), toggle=True)
    installer.write(HOME / '.config/plasma-workspace/env/corsu.sh',
                    '#!/bin/sh\nexport LANGUAGE=co:fr\n', 0o755, toggle=True)
    terminal_hooks(installer)
    for source in sorted(Path('/usr/share/applications').glob('*.desktop')):
        target = HOME / '.local/share/applications' / source.name
        text = (target if target.exists() else source).read_text(encoding='utf-8')
        output = []
        section = []
        changes = 0

        def flush_section():
            nonlocal changes
            existing = {line.split('=', 1)[0]: line.split('=', 1)[1].rstrip('\n')
                        for line in section if '=' in line and not line.startswith('#')}
            replacements = {}
            for key in ('Name', 'GenericName', 'Comment'):
                for candidate in (existing.get(key, ''), existing.get(key + '[fr]', '')):
                    converted = translate(candidate)
                    if converted != candidate:
                        replacements[key + '[co]'] = converted
                        break
            for line in section:
                if line.split('=', 1)[0] not in replacements:
                    output.append(line)
            for key, value in replacements.items():
                if output and not output[-1].endswith('\n'):
                    output[-1] += '\n'
                output.append(f'{key}={value}\n')
            changes += len(replacements)

        for line in text.splitlines(keepends=True):
            if line.startswith('[') and section:
                flush_section()
                section = []
            section.append(line)
        flush_section()
        if changes:
            installer.write(target, ''.join(output))
            stats['desktop_entries'] += 1
    return stats


class FirefoxInstall:
    """A system Firefox: `root` is copied whole; `resources` holds omni.ja and application.ini."""

    def __init__(self, root):
        self.root = Path(root)
        self.app = 'Firefox.app' if PLATFORM == 'macos' else ''
        self.resources = 'Contents/Resources' if PLATFORM == 'macos' else ''
        self.binary = {'windows': 'firefox.exe', 'macos': 'Contents/MacOS/firefox'}.get(PLATFORM, 'firefox')

    def version(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.root / self.resources / 'application.ini', encoding='utf-8')
        return config['App']['Version']


def firefox_candidates():
    if os.environ.get('CORSU_FIREFOX'):
        return [Path(os.environ['CORSU_FIREFOX'])]
    if PLATFORM == 'windows':
        bases = [os.environ.get('ProgramFiles'), os.environ.get('ProgramW6432'), os.environ.get('ProgramFiles(x86)'),
                 os.environ.get('LOCALAPPDATA')]
        return [Path(base) / 'Mozilla Firefox' for base in bases if base]
    if PLATFORM == 'macos':
        return [Path('/Applications/Firefox.app'), HOME / 'Applications/Firefox.app']
    return [Path('/usr/lib/firefox'), Path('/usr/lib64/firefox'), Path('/opt/firefox'), Path('/usr/lib/firefox-esr')]


def firefox_install():
    """Find the system Firefox. Snap and Flatpak builds are sealed and cannot be copied."""
    for candidate in firefox_candidates():
        install = FirefoxInstall(candidate)
        if (install.root / install.resources / 'application.ini').exists() and (install.root / install.binary).exists():
            return install
    return None


def french_pack(version):
    """The French Firefox language pack for this exact version, verified against Mozilla's
    published SHA512SUMS. Fall back to the bundled pack; messages are merged by id anyway."""
    cache = DATA / 'langpacks' / f'fr-{version}.xpi'
    if cache.exists():
        return cache
    base = f'https://archive.mozilla.org/pub/firefox/releases/{version}/'
    if not os.environ.get('CORSU_OFFLINE'):
        try:
            with urllib.request.urlopen(base + 'SHA512SUMS', timeout=20) as response:
                sums = response.read().decode()
            expected = next(line.split()[0] for line in sums.splitlines() if line.endswith(' linux-x86_64/xpi/fr.xpi'))
            with urllib.request.urlopen(base + 'linux-x86_64/xpi/fr.xpi', timeout=60) as response:
                data = response.read()
            if hashlib.sha512(data).hexdigest() == expected:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_bytes(data)
                return cache
            print('Warning: French language pack checksum mismatch; using the bundled pack.', file=sys.stderr)
        except (OSError, StopIteration, ValueError):
            pass
    bundled = ROOT / 'vendor/firefox-fr.xpi'
    return bundled if bundled.exists() else None


def merge_properties(native, french):
    """Use the French value of every key that still exists; keep the native file's layout."""
    known = {}
    for line in french.splitlines():
        match = PROPERTY.match(line)
        if match:
            known[match[1].strip()] = match[2]
    output, merged = [], 0
    for line in native.splitlines(keepends=True):
        match = PROPERTY.match(line.rstrip('\r\n'))
        if match and match[1].strip() in known:
            line = match[1] + '=' + known[match[1].strip()] + line[len(line.rstrip('\r\n')):]
            merged += 1
        output.append(line)
    return ''.join(output), merged


PROPERTY = re.compile(r'^([^#!\s][^=\n]*?)=([^\n]*)$')
PLATFORM_FLAGS = {'windows': 'WINNT', 'macos': 'Darwin', 'linux': 'LikeUnix'}
LANGPACK_PLATFORMS = {'windows': 'win', 'macos': 'macosx', 'linux': 'linux'}


def locale_directories(bundle, manifest):
    """Map each packaged chrome locale directory to its directory in the French pack."""
    result = {}
    try:
        lines = bundle.read('chrome/chrome.manifest').decode().splitlines()
    except KeyError:
        return result
    resources = manifest['languages']['fr']['chrome_resources']
    for line in lines:
        fields = line.split()
        if len(fields) < 4 or fields[0] != 'locale':
            continue
        flags = [field.split('=', 1)[1] for field in fields[4:] if field.startswith('os=')]
        if flags and PLATFORM_FLAGS[PLATFORM] not in flags:
            continue
        french = resources.get(fields[1])
        if isinstance(french, dict):
            french = french.get(LANGPACK_PLATFORMS[PLATFORM])
        if french:
            result['chrome/' + fields[3]] = french
    return result


def packaged_locale(bundle):
    """Firefox builds package one interface locale; a French Windows build packages `fr`."""
    for name in bundle.namelist():
        match = re.match(r'^localization/([A-Za-z-]+)/', name)
        if match:
            return match[1]
    return 'en-US'


def review_options():
    """Options chosen in the Corsu app (see review.py)."""
    try:
        return json.loads((DATA / 'review.json').read_text(encoding='utf-8')).get('options', {})
    except (OSError, ValueError):
        return {}


def firefox_runtime():
    install = firefox_install()
    if install is None:
        raise RuntimeError('No supported Firefox found. Install Firefox from mozilla.org or your distribution.')
    app_version = install.version()
    resources = install.root / install.resources
    fingerprint = hashlib.sha256(b''.join(path.read_bytes() for path in engine.LEXICONS if path.exists())
                                 + Path(__file__).read_bytes()
                                 + b''.join(path.read_bytes() for path in sorted((SRC / 'firefox').glob('*'))))
    fingerprint.update(json.dumps(review_options(), sort_keys=True).encode())
    for file in ('omni.ja', 'browser/omni.ja', 'application.ini', 'platform.ini'):
        if (resources / file).exists():
            fingerprint.update((resources / file).read_bytes())
    for file in sorted(install.root.rglob('*')):
        if file.is_file() and not file.is_symlink():
            stat = file.stat()
            fingerprint.update(f'{file.relative_to(install.root).as_posix()}:{stat.st_size}:{stat.st_mtime_ns}'.encode())
    target = DATA / 'firefox' / fingerprint.hexdigest()[:16]
    if (target / 'corsu-report.json').exists():
        return target, json.loads((target / 'corsu-report.json').read_text(encoding='utf-8'))
    target.parent.mkdir(parents=True, exist_ok=True)
    fr_path = french_pack(app_version)
    fr = zipfile.ZipFile(fr_path) if fr_path else None
    stage = Path(tempfile.mkdtemp(prefix='build-', dir=target.parent))
    try:
        app = stage / install.app
        shutil.copytree(install.root, app, dirs_exist_ok=True, symlinks=True)
        french_names = set(fr.namelist()) if fr else set()
        manifest = json.loads(fr.read('manifest.json')) if fr else None
        stats = {'version': app_version, 'translated_values': 0, 'ftl_files': 0, 'french_messages': 0,
                 'fallback': 'fr' if fr else None, 'french_pack': manifest['version'] if fr else None,
                 'platform': PLATFORM, 'partial': True}
        for name in ('omni.ja', 'browser/omni.ja'):
            if not (resources / name).exists():
                continue
            prefix = 'browser/' if name.startswith('browser/') else ''
            with read_zip(resources / name) as original, \
                    zipfile.ZipFile(app / install.resources / name, 'w', zipfile.ZIP_DEFLATED) as output:
                locale = packaged_locale(original) if prefix else stats.setdefault('locale', packaged_locale(original))
                directories = locale_directories(original, manifest) if fr else {}
                for info in original.infolist():
                    data = original.read(info.filename)
                    if info.filename.endswith('.ftl') and f'/{locale}/' in info.filename:
                        text = data.decode()
                        french_name = prefix + info.filename.replace(f'/{locale}/', '/fr/')
                        if french_name in french_names:
                            text, merged = merge_ftl(text, fr.read(french_name).decode())
                            stats['french_messages'] += merged
                        text, count = patch_ftl(text)
                        data = text.encode()
                        stats['translated_values'] += count
                        stats['ftl_files'] += 1
                    elif info.filename.endswith('.properties') and '/locale/' in info.filename:
                        text = data.decode('utf-8')
                        base = next((path for path in directories if info.filename.startswith(path)), None)
                        if base is not None:
                            french_name = directories[base] + info.filename[len(base):]
                            if french_name in french_names:
                                text, merged = merge_properties(text, fr.read(french_name).decode('utf-8'))
                                stats['french_messages'] += merged
                        lines = []
                        for line in text.splitlines(keepends=True):
                            match = re.match(r'^([^#!\s][^=\n]*=)([^\n]*)(\n)?$', line)
                            if match:
                                value = translate(match[2])
                                stats['translated_values'] += int(value != match[2])
                                line = match[1] + value + (match[3] or '')
                            lines.append(line)
                        data = ''.join(lines).encode()
                    output.writestr(info.filename, data)
                if prefix:
                    for module_name, module_data in google_modules().items():
                        output.writestr('modules/corsu/' + module_name, module_data)
        locale = stats.setdefault('locale', 'en-US')
        # Keep the normal profile and extension signature checks; do not relax security.
        prefs = app / install.resources / 'defaults/pref/corsu.js'
        prefs.parent.mkdir(parents=True, exist_ok=True)
        # Websites that offer Corsican (Google among them) use it first, then French. The autoconfig file
        # completes Google's own Corsican interface; it exists only in this copy of Firefox.
        prefs.write_text(f'pref("intl.locale.requested", "{locale}");\n'
                         'pref("intl.accept_languages", "co, fr, en-US, en");\n'
                         'pref("general.config.filename", "corsu.cfg");\n'
                         'pref("general.config.obscure_value", 0);\n'
                         'pref("general.config.sandbox_enabled", false);\n'
                         # The copy cannot become the default browser itself: its folder changes with each update.
                         'pref("browser.shell.checkDefaultBrowser", false);\n'
                         # Set in the Corsu app: hovering a completed Google label shows the original text.
                         f'pref("corsu.showOriginal", {str(bool(review_options().get("showOriginal"))).lower()});\n',
                         encoding='utf-8')
        google_labels(app / install.resources)
        # Corsu rebuilds this copy when the system Firefox updates; its own updater would undo the translation.
        policies_path = app / install.resources / 'distribution/policies.json'
        policies = json.loads(policies_path.read_text(encoding='utf-8')) if policies_path.exists() else {}
        policies.setdefault('policies', {})['DisableAppUpdate'] = True
        policies_path.parent.mkdir(parents=True, exist_ok=True)
        policies_path.write_text(json.dumps(policies, indent=2), encoding='utf-8')
        if PLATFORM == 'macos':
            # Changed resources break the bundle seal; an ad-hoc signature keeps Gatekeeper satisfied.
            subprocess.run(['xattr', '-cr', str(app)], check=False)
            subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(app)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        (stage / 'corsu-report.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
        stage.rename(target)
        return target, stats
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    finally:
        if fr:
            fr.close()


GOOGLE_DOMAINS = ('google.com', 'google.fr', 'google.it', 'google.be', 'google.ch', 'google.ca', 'google.co.uk',
                  'google.de', 'google.es', 'google.pt', 'google.com.br')


def lexicon_section(name):
    """Source texts of the `# <name>:` section of lexicon.tsv, which runs to the next `# …:` heading."""
    keys, inside = [], False
    for line in LEXICON.read_text(encoding='utf-8').splitlines():
        if line.startswith('# '):
            inside = line.startswith(f'# {name}:')
            continue
        fields = line.split('|')
        if inside and len(fields) == 3:
            keys.extend(engine.normalize(key.strip()) for key in fields[:2] if key.strip())
    return keys


def google_labels(resources):
    """Write the autoconfig file that starts the Google module (kept in browser/omni.ja, see google_modules)."""
    config = (SRC / 'firefox/corsu.cfg').read_text(encoding='utf-8').replace('HOSTS', json.dumps(list(GOOGLE_DOMAINS)))
    (resources / 'corsu.cfg').write_text(config, encoding='utf-8')


def google_modules():
    """The module that puts Corsican on Google's buttons and menus where Google's own Corsican interface falls
    back to French or English, with its dictionary. Search results and other websites are left alone."""
    # Only Google's own labels: every page process loads this file, so it stays a few kilobytes.
    labels = {}
    for line in (SRC / 'firefox/google-labels.txt').read_text(encoding='utf-8').splitlines():
        if line and not line.startswith('#') and WORDS.get(line, line) != line:
            labels[line] = WORDS[line]
    labels.update({key: WORDS[key] for key in lexicon_section('Google') if key in WORDS})
    return {'CorsuChild.sys.mjs': (SRC / 'firefox/CorsuChild.sys.mjs').read_bytes(),
            'dictionary.mjs': ('export const words = ' + json.dumps(labels, ensure_ascii=False, separators=(',', ':'))
                               + ';\n').encode('utf-8')}


def firefox_directory(runtime):
    """The folder Firefox names its installation after: the application bundle on macOS."""
    return Path(runtime) / firefox_install().app if PLATFORM == 'macos' else Path(runtime)


def firefox_executable(runtime):
    install = firefox_install()
    return Path(runtime) / install.app / install.binary


def generate():
    plugin = ROOT / 'Vencord/src/userplugins/corsu'
    plugin.mkdir(parents=True, exist_ok=True)
    # Discord shows short interface labels: leave out long sentences and terminal messages, which only
    # make the plugin heavier.
    terminal = re.compile(r'%[-0-9.]*[sdlucfx]|(^|\s)--?\w|\\n|\t')
    words = {key: value for key, value in WORDS.items() if len(key) <= 40 and not terminal.search(key)}
    # Sentences written for Discord are kept whatever their length.
    words.update({key: WORDS[key] for key in lexicon_section('Discord') if key in WORDS})
    (plugin / 'dictionary.json').write_text(json.dumps(words, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    for name in ('index.ts', 'translate.ts'):
        shutil.copy2(SRC / 'discord-plugin' / name, plugin / name)


# Mozilla's copy of CityHash64 (version 1.0.2). Firefox names each installation's section of profiles.ini with
# this hash of the installation directory.
MASK = 0xFFFFFFFFFFFFFFFF
K0, K1, K2, K3 = 0xc3a5c85c97cb3127, 0xb492b66fbe98f273, 0x9ae16a3b2f90404f, 0xc949d7c7509e6557


def city_hash64(data):
    def fetch64(i):
        return int.from_bytes(data[i:i + 8], 'little')

    def rotate(value, shift):
        return value if shift == 0 else ((value >> shift) | (value << (64 - shift))) & MASK

    def shift_mix(value):
        return value ^ (value >> 47)

    def hash16(u, v):
        a = ((u ^ v) * 0x9ddfea08eb382d69) & MASK
        a ^= a >> 47
        b = ((v ^ a) * 0x9ddfea08eb382d69) & MASK
        b ^= b >> 47
        return (b * 0x9ddfea08eb382d69) & MASK

    def weak32(i, a, b):
        w, x, y, z = fetch64(i), fetch64(i + 8), fetch64(i + 16), fetch64(i + 24)
        a = (a + w) & MASK
        b = rotate((b + a + z) & MASK, 21)
        c = a
        a = (a + x + y) & MASK
        b = (b + rotate(a, 44)) & MASK
        return (a + z) & MASK, (b + c) & MASK

    n = len(data)
    if n <= 16:
        if n > 8:
            a, b = fetch64(0), fetch64(n - 8)
            return hash16(a, rotate((b + n) & MASK, n)) ^ b
        if n >= 4:
            a = int.from_bytes(data[:4], 'little')
            return hash16((n + (a << 3)) & MASK, int.from_bytes(data[n - 4:], 'little'))
        if n:
            y, z = data[0] + (data[n >> 1] << 8), n + (data[n - 1] << 2)
            return (shift_mix(((y * K2) ^ (z * K3)) & MASK) * K2) & MASK
        return K2
    if n <= 32:
        a, b = (fetch64(0) * K1) & MASK, fetch64(8)
        c, d = (fetch64(n - 8) * K2) & MASK, (fetch64(n - 16) * K0) & MASK
        return hash16((rotate((a - b) & MASK, 43) + rotate(c, 30) + d) & MASK, (a + rotate(b ^ K3, 20) - c + n) & MASK)
    if n <= 64:
        halves = []
        for start, end in ((0, n - 16), (n - 32, n - 16)):
            z = fetch64(24) if start == 0 else fetch64(n - 8)
            a = ((fetch64(0) + (n + fetch64(n - 16)) * K0) & MASK) if start == 0 else (fetch64(16) + fetch64(n - 32)) & MASK
            b, c = rotate((a + z) & MASK, 52), rotate(a, 37)
            a = (a + fetch64(8 if start == 0 else n - 24)) & MASK
            c = (c + rotate(a, 7)) & MASK
            a = (a + fetch64(16 if start == 0 else n - 16)) & MASK
            halves.append(((a + z) & MASK, (b + rotate(a, 31) + c) & MASK))
        (vf, vs), (wf, ws) = halves
        r = shift_mix((((vf + ws) & MASK) * K2 + ((wf + vs) & MASK) * K0) & MASK)
        return (shift_mix((r * K0 + vs) & MASK) * K2) & MASK
    x, y, z = fetch64(0), fetch64(n - 16) ^ K1, fetch64(n - 56) ^ K0
    v, w = weak32(n - 64, n, y), weak32(n - 32, (n * K1) & MASK, K0)
    z = (z + shift_mix(v[1]) * K1) & MASK
    x = (rotate((z + x) & MASK, 39) * K1) & MASK
    y = (rotate(y, 33) * K1) & MASK
    for i in range(0, (n - 1) & ~63, 64):
        x = (rotate((x + y + v[0] + fetch64(i + 16)) & MASK, 37) * K1) & MASK
        y = (rotate((y + v[1] + fetch64(i + 48)) & MASK, 42) * K1) & MASK
        x ^= w[1]
        y ^= v[0]
        z = rotate(z ^ w[0], 33)
        v = weak32(i, (v[1] * K1) & MASK, (x + w[0]) & MASK)
        w = weak32(i + 32, (z + w[1]) & MASK, y)
        z, x = x, z
    return hash16((hash16(v[0], w[0]) + shift_mix(y) * K1 + z) & MASK, (hash16(v[1], w[1]) + x) & MASK)


def install_section(directory):
    """The profiles.ini section that holds the default profile of the Firefox installed in `directory`."""
    return 'Install%016X' % city_hash64(str(directory).encode('utf-16-le'))


def read_ini(path):
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    config.read(path, encoding='utf-8')
    return config


def write_ini(path, config):
    with path.open('w', encoding='utf-8') as file:
        config.write(file, space_around_delimiters=False)


def link_profile(directory, profile):
    """Make the Firefox copy in `directory` open `profile` even when started without Corsu's launcher, for example
    as the default browser. Otherwise Firefox gives every new installation directory a new, empty profile."""
    section = install_section(directory)
    for base in firefox_profile_roots():
        if not (base / 'profiles.ini').exists():
            continue
        try:
            value = profile.relative_to(base).as_posix()
        except ValueError:
            continue
        for name in ('profiles.ini', 'installs.ini'):
            path = base / name
            config = read_ini(path)
            if config.has_section(section) and config[section].get('Default') == value:
                continue
            config[section] = {'Default': value, 'Locked': '1'}
            write_ini(path, config)
        return


def unlink_profile(directory):
    section = install_section(directory)
    for base in firefox_profile_roots():
        for name in ('profiles.ini', 'installs.ini'):
            path = base / name
            if path.exists():
                config = read_ini(path)
                if config.remove_section(section):
                    write_ini(path, config)


def firefox_profile_roots():
    if PLATFORM == 'windows':
        return [CONFIG / 'Mozilla/Firefox']
    if PLATFORM == 'macos':
        return [CONFIG / 'Firefox']
    return [HOME / '.config/mozilla/firefox', HOME / '.mozilla/firefox']


def firefox_profile():
    """The profile the system Firefox opens; failing that, the only default. Firefox asks when it is ambiguous."""
    install = firefox_install()
    system = install_section(install.root) if install else None
    for base in firefox_profile_roots():
        config = read_ini(base / 'profiles.ini')
        if system and config.has_section(system) and config[system].get('Default'):
            defaults = {config[system]['Default']}
        else:
            defaults = {config[section].get('Default') for section in config.sections()
                        if section.startswith('Install') and config[section].get('Default')}
        if not defaults:
            defaults = {config[section].get('Path') for section in config.sections()
                        if section.startswith('Profile') and config[section].get('Default') == '1'}
        if len(defaults) != 1:
            continue
        name = defaults.pop()
        path = Path(name)
        if not path.is_absolute():
            path = base / path
        if path.is_dir():
            return path
    return None


def newtab_strings(profile, locale):
    """Firefox can update its New Tab page on its own, into the profile, and that update brings its own English
    text. Translate it the same way as the rest of Firefox; the copy's autoconfig file then uses this folder."""
    xpi = profile / 'extensions/newtab@mozilla.org.xpi'
    target = DATA / 'newtab'
    if not xpi.exists():
        shutil.rmtree(target, ignore_errors=True)
        return None
    stamp = f'{xpi.stat().st_size}:{xpi.stat().st_mtime_ns}:{locale}:{digest(Path(__file__).read_bytes())}'
    if (target / 'source.txt').exists() and (target / 'source.txt').read_text(encoding='utf-8') == stamp:
        return target
    shutil.rmtree(target, ignore_errors=True)
    prefix = f'locales/{locale}/'
    with zipfile.ZipFile(xpi) as bundle:
        names = set(bundle.namelist())
        for name in sorted(names):
            if not (name.startswith(prefix) and name.endswith('.ftl')):
                continue
            text = bundle.read(name).decode('utf-8')
            french = 'locales/fr/' + name[len(prefix):]
            if french in names:
                text, _ = merge_ftl(text, bundle.read(french).decode('utf-8'))
            text, _ = patch_ftl(text)
            output = target / locale / name[len(prefix):]
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding='utf-8')
    target.mkdir(parents=True, exist_ok=True)
    (target / 'source.txt').write_text(stamp, encoding='utf-8')
    return target


def repair_default_browser():
    """When a Corsu copy is made the default browser, Firefox records its exact folder, which changes with every
    Firefox update, in a menu entry without an icon. Point the default browser back at the Firefox Corsu entry."""
    if PLATFORM != 'linux':
        return
    applications = HOME / '.local/share/applications'
    if not (applications / 'firefox.desktop').exists():
        return
    stale = []
    for entry in applications.glob('userapp-*.desktop'):
        exec_line = re.search(r'^Exec=(.*)$', entry.read_text(encoding='utf-8', errors='replace'), re.M)
        if exec_line and DATA / 'firefox' in Path(re.sub(r'\s+%\w.*$', '', exec_line[1]).strip('"')).parents:
            stale.append(entry)
    if not stale:
        return
    for mimeapps in (CONFIG / 'mimeapps.list', applications / 'mimeapps.list'):
        if not mimeapps.exists():
            continue
        text = original = mimeapps.read_text(encoding='utf-8')
        for entry in stale:
            text = text.replace(entry.name, 'firefox.desktop')
        text = re.sub(r'(?<![\w.-])firefox\.desktop;(?:firefox\.desktop;)+', 'firefox.desktop;', text)
        if text != original:
            mimeapps.write_text(text, encoding='utf-8')
    for entry in stale:
        entry.unlink()


def running_executables():
    paths = set()
    if PLATFORM == 'linux':
        for process in Path('/proc').iterdir():
            try:
                paths.add(os.readlink(process / 'exe'))
            except OSError:
                continue
        return paths
    command = (['powershell', '-NoProfile', '-Command', '(Get-Process).Path'] if PLATFORM == 'windows'
               else ['ps', '-axo', 'comm='])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def prune_runtimes(current):
    """Remove the copies left by earlier Firefox versions, unless one of them is still running."""
    running = running_executables()
    if running is None:
        return
    for directory in (DATA / 'firefox').iterdir():
        if directory == current or not directory.is_dir():
            continue
        if any(path.startswith(str(directory) + os.sep) for path in running):
            continue
        unlink_profile(firefox_directory(directory))
        shutil.rmtree(directory, ignore_errors=True)


def firefox_arguments(rest, locale='en-US'):
    # Explicit profile selection takes precedence over our discovered default.
    selectors = {'-profile', '--profile', '-p', '--p', '-profilemanager', '--profilemanager'}
    if any(arg.lower().split('=', 1)[0] in selectors for arg in rest):
        return ['-UILocale', locale, *rest]
    profile = firefox_profile()
    selection = ['-profile', str(profile)] if profile else ['-ProfileManager']
    return [*selection, '-UILocale', locale, *rest]


def status():
    """Read installation health without building or changing app settings."""
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'files': {}}
    counts = {'managed': len(state['files']), 'missing': [], 'changed': []}
    for name, record in state['files'].items():
        path = Path(name)
        if not path.exists():
            counts['missing'].append(name)
        elif record.get('tree') or record.get('line'):
            continue
        elif record.get('json_changes'):
            document = json.loads(path.read_text(encoding='utf-8'))
            for field, saved in record['json_changes'].items():
                node = document
                for part in field.split('/'):
                    node = node.get(part) if isinstance(node, dict) else None
                if node != saved['installed']:
                    counts['changed'].append(f'{name}: {field}')
        elif digest(path.read_bytes()) != record['installed_sha256']:
            counts['changed'].append(name)
    report_path = DATA / 'report.json'
    profile = firefox_profile()
    print(json.dumps({'enabled': not disabled_marker().exists(),
                      'components': state.get('components', []),
                      'installation': counts,
                      'lexicon_entries': len(WORDS),
                      'firefox_profile': str(profile) if profile else None,
                      'last_build': json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else None},
                     ensure_ascii=False, indent=2))


def python_launcher():
    """The interpreter launchers call; pythonw.exe avoids a console window on Windows."""
    executable = Path(sys.executable)
    windowed = executable.with_name('pythonw.exe')
    return windowed if PLATFORM == 'windows' and windowed.exists() else executable


def windows_link(installer, path, target, arguments, icon=None, toggle=False):
    """Create a Windows `.lnk` shortcut through the Shell, and track it like any managed file."""
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory) / 'shortcut.lnk'
        script = ('$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:CORSU_LINK); '
                  '$s.TargetPath = $env:CORSU_TARGET; $s.Arguments = $env:CORSU_ARGUMENTS; '
                  '$s.WorkingDirectory = $env:CORSU_DIR; if ($env:CORSU_ICON) { $s.IconLocation = $env:CORSU_ICON }; $s.Save()')
        subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script], check=True, env={
            **os.environ, 'CORSU_LINK': str(temporary), 'CORSU_TARGET': str(target), 'CORSU_ARGUMENTS': arguments,
            'CORSU_DIR': str(ROOT), 'CORSU_ICON': icon or ''})
        installer.write(path, temporary.read_bytes(), toggle=toggle)


START_MENU = CONFIG / 'Microsoft/Windows/Start Menu/Programs'


def windows_shortcut(installer, firefox):
    command = DATA / 'bin/firefox-corsu.cmd'
    installer.write(command, f'@"{python_launcher()}" "{SRC / "corsu.py"}" launch-firefox %*\r\n')
    windows_link(installer, START_MENU / 'Firefox Corsu.lnk', python_launcher(),
                 f'"{SRC / "corsu.py"}" launch-firefox', str(firefox.root / firefox.binary) + ',0', toggle=True)


def macos_application(installer):
    """A small AppleScript applet, so Firefox Corsu appears in Launchpad and Spotlight."""
    target = HOME / 'Applications/Firefox Corsu.app'
    command = f'exec {shlex.quote(sys.executable)} {shlex.quote(str(SRC / "corsu.py"))} launch-firefox >/dev/null 2>&1 &'
    with tempfile.TemporaryDirectory() as directory:
        applet = Path(directory) / 'Firefox Corsu.app'
        script = 'do shell script ' + json.dumps(command)
        subprocess.run(['osacompile', '-o', str(applet), '-e', script], check=True)
        installer.tree(target, applet)


def setup_shortcut(installer):
    """The Corsu entry in the applications menu: switch parts on and off, add programs, uninstall."""
    app = SRC / 'app.py'
    # Versions before 0.11 called the entry "Corsu Setup"; take the old shortcut away so only one remains.
    for old in (START_MENU / 'Corsu Setup.lnk', HOME / 'Applications/Corsu Setup.app'):
        record = installer.state['files'].pop(str(old), None)
        if record and record.get('tree'):
            shutil.rmtree(old, ignore_errors=True)
        elif record:
            restore(old, record)
    if PLATFORM == 'windows':
        windows_link(installer, START_MENU / 'Corsu.lnk', python_launcher(), f'"{app}"')
    elif PLATFORM == 'macos':
        command = f'exec {shlex.quote(sys.executable)} {shlex.quote(str(app))} >/dev/null 2>&1 &'
        with tempfile.TemporaryDirectory() as directory:
            applet = Path(directory) / 'Corsu.app'
            subprocess.run(['osacompile', '-o', str(applet), '-e', 'do shell script ' + json.dumps(command)], check=True)
            installer.tree(HOME / 'Applications/Corsu.app', applet)
    else:
        installer.write(HOME / '.local/share/applications/corsu-setup.desktop',
                        '[Desktop Entry]\nType=Application\nName=Corsu\n'
                        'GenericName=Corsican language\nGenericName[fr]=Langue corse\nGenericName[co]=Lingua corsa\n'
                        'Comment=Choose which programs are in Corsican\nComment[fr]=Choisir les logiciels en corse\n'
                        f'Exec=python3 {shlex.quote(str(app))}\nTerminal=false\nIcon={SRC / "app/corsu.svg"}\n'
                        'Categories=Settings;\n')


def desktop(installer, firefox=True, vesktop=True):
    if PLATFORM == 'windows':
        if firefox:
            windows_shortcut(installer, firefox_install())
        return
    if PLATFORM == 'macos':
        if firefox:
            macos_application(installer)
        return
    launcher = HOME / '.local/bin/firefox-corsu'
    if firefox:
        installer.write(launcher, f'#!/bin/sh\nexec python3 {shlex.quote(str(SRC / "corsu.py"))} launch-firefox "$@"\n', 0o755)
    entries = ([('firefox.desktop', str(launcher))] if firefox else []) + ([('vesktop.desktop', None)] if vesktop else [])
    for desktop_id, executable in entries:
        existing = HOME / '.local/share/applications' / desktop_id
        original = existing if existing.exists() else Path('/usr/share/applications') / desktop_id
        if not original.exists():
            continue
        text = original.read_text(encoding='utf-8')
        if executable:
            text = re.sub(r'^Exec=(?:/usr/lib/firefox/firefox|/usr/bin/firefox|firefox)(?=\s|$)', f'Exec={executable}', text, flags=re.M)
        name = 'Firefox Corsu' if executable else 'Vesktop Corsu'
        text = re.sub(r'^Name=.*$', 'Name=' + name, text, count=1, flags=re.M)
        text = re.sub(r'^Name\[(?:co|fr)\]=.*\n?', '', text, flags=re.M)
        text = text.replace('[Desktop Entry]\n', f'[Desktop Entry]\nName[co]={name}\nName[fr]={name}\n', 1)
        installer.write(existing, text, toggle=True)


def install(components=None, qt_system=False):
    components = set(components or ['firefox', 'desktop', 'vesktop'])
    dist = ROOT / 'Vencord/dist'
    if 'vesktop' in components and not (dist / 'vencordDesktopRenderer.js').exists():
        raise RuntimeError('Build Vencord before installing.')
    runtime, firefox_stats = firefox_runtime() if 'firefox' in components else (None, None)
    installer = Installer()
    kde_stats = kde(installer, qt_system=qt_system) if 'desktop' in components else None
    if qt_system and kde_stats:
        kde_stats['qt_system_catalogs'] = system_catalogs(installer)
    plugin_settings = {'plugins/Corsu/enabled': True, 'autoUpdate': False, 'autoUpdateNotification': False}
    if 'vesktop' in components:
        installer.json_settings(CONFIG / 'vesktop/state.json', {'vencordDir': str(dist)})
        # Prevent the upstream updater from replacing this custom plugin build.
        installer.json_settings(CONFIG / 'vesktop/settings/settings.json', plugin_settings, toggle=True)
    if 'discord' in components:
        installer.json_settings(CONFIG / 'Vencord/settings/settings.json', plugin_settings, toggle=True)
    desktop(installer, firefox='firefox' in components, vesktop='vesktop' in components)
    if runtime:
        profile = firefox_profile()
        if profile:
            link_profile(firefox_directory(runtime), profile)
        repair_default_browser()
    chromium_stats = None
    if 'chromium' in components:
        import chromium
        chromium_stats = chromium.install(installer)
    installer.state['components'] = sorted(set(installer.state.get('components', [])) | components)
    installer.state['qt_system'] = qt_system or installer.state.get('qt_system', False)
    installer.state['disabled'] = sorted(set(installer.state.get('disabled', [])) - components)
    installer.state['enabled'] = True
    STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    disabled_marker().unlink(missing_ok=True)
    clients = sorted({'Vesktop' if name == 'vesktop' else 'Discord' for name in components
                      if name in ('vesktop', 'discord')})
    report = {'kde': kde_stats, 'firefox': firefox_stats, 'chromium': chromium_stats, 'firefox_runtime': str(runtime) if runtime else None,
              'discord': {'clients': clients, 'plugin': 'Corsu', 'dictionary_labels': len(WORDS), 'partial': True},
              'components': sorted(components), 'enabled': True,
              'scope': 'Interface labels only; no translation of messages or arbitrary websites.'}
    (DATA / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(t('Installed: ', 'Installé : ') + component_names(components & set(COMPONENT_LABELS)))


def vencord_installer():
    """The official Vencord installer for this platform and its pinned SHA-256."""
    manifest = json.loads((SRC / 'release.json').read_text(encoding='utf-8'))
    entry = manifest['installers'][PLATFORM]
    return ROOT / 'vendor' / entry['file'], entry['sha256']


def disabled_marker():
    return DATA / 'disabled'


COMPONENT_LABELS = {
    'firefox': ('Firefox', 'Firefox'),
    'chromium': ('Chrome, Opera GX and other Chromium browsers', 'Chrome, Opera GX et autres navigateurs Chromium'),
    'discord': ('Discord', 'Discord'), 'vesktop': ('Vesktop', 'Vesktop'),
    'desktop': ('KDE Plasma desktop and programs', 'Bureau et programmes KDE Plasma'),
    'terminal': ('Terminal commands', 'Commandes du terminal'),
}


def component_names(names):
    return ', '.join(t(*COMPONENT_LABELS[name]) if name in COMPONENT_LABELS else name for name in sorted(names))


def load_state():
    return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'files': {}}


def switchable(state=None):
    """The parts that can be switched on and off one by one, in display order."""
    state = state or load_state()
    installed = set(state.get('components', []))
    parts = [name for name in ('firefox', 'chromium', 'discord', 'vesktop', 'desktop') if name in installed]
    if 'desktop' in installed and PLATFORM == 'linux':
        parts.append('terminal')
    return parts


def terminal_paused_until():
    """None when the terminal is in Corsican, 0 when switched off, else the time it comes back on."""
    path = DATA / TERMINAL_OFF
    if not path.exists():
        return None
    text = path.read_text(encoding='utf-8').strip()
    if text and int(text) <= __import__('time').time():
        path.unlink(missing_ok=True)
        return None
    return int(text) if text else 0


def is_disabled(component, state=None):
    if disabled_marker().exists():
        return True
    if component == 'terminal':
        return terminal_paused_until() is not None
    return component in (state or load_state()).get('disabled', [])


def component_of(name, record):
    """Which switchable part a managed file belongs to."""
    if record.get('component'):
        return record['component']
    if record.get('chromium'):
        return 'chromium'
    lower = name.replace('\\', '/').lower()
    if 'vencord/settings' in lower:
        return 'discord'
    if 'vesktop' in lower:
        return 'vesktop'
    if 'firefox' in lower:
        return 'firefox'
    if 'local state' in lower or any(word in lower for word in ('chrome', 'chromium', 'opera', 'brave', 'edge', 'vivaldi')):
        return 'chromium'
    return 'desktop'


def restore(path, record):
    """Return one managed file to its pre-installation content. False when the user changed it."""
    if path.exists() and digest(path.read_bytes()) != record['installed_sha256']:
        return False
    if record.get('backup'):
        shutil.copy2(record['backup'], path)
        if record.get('mode') is not None:
            path.chmod(record['mode'])
    else:
        path.unlink(missing_ok=True)
    return True


def disable(components=None, hours=None):
    """Return applications to their previous language, keeping everything Corsu built.

    With no list, every part is switched off. `hours` pauses the terminal only for that long.
    Only the switches are reverted, so `enable` is fast and needs no rebuild.
    """
    if not STATE.exists():
        print(t('Corsu is not installed.', 'Corsu n\'est pas installé.'))
        return
    installer = Installer()
    everything = components is None
    targets = set(switchable(installer.state)) if everything else set(components)
    if 'terminal' in targets:
        DATA.mkdir(parents=True, exist_ok=True)
        until = '' if not hours else str(int(__import__('time').time() + hours * 3600))
        (DATA / TERMINAL_OFF).write_text(until, encoding='utf-8')
    preserved = []
    packs = {name: record for name, record in installer.state['files'].items()
             if record.get('chromium') and 'chromium' in targets}
    if packs:
        import chromium
        chromium.restore(packs)
        for name in packs:
            installer.state['files'].pop(name)
    for name, record in list(installer.state['files'].items()):
        if not record.get('toggle') or component_of(name, record) not in targets:
            continue
        path = Path(name)
        if record.get('json_changes'):
            fields = {field: False if field.endswith('/enabled') else saved['original']
                      for field, saved in record['json_changes'].items()
                      if field.endswith('/enabled') or saved['existed']}
            if fields and path.exists():
                installer.json_settings(path, fields, toggle=True)
            continue
        if restore(path, record):
            installer.state['files'].pop(name)
        else:
            preserved.append(name)
    installer.state['disabled'] = sorted(set(installer.state.get('disabled', [])) | (targets - {'terminal'}))
    installer.state['enabled'] = not everything and installer.state.get('enabled', True)
    STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    if everything:
        disabled_marker().write_text('Corsu is switched off. Open the Corsu app to switch it on again.\n', encoding='utf-8')
    for name in preserved:
        print(t(f'Left alone because you changed it: {name}', f'Laissé tel quel car vous l\'avez modifié : {name}'))
    names = component_names(targets)
    print(t(f'Back to the original language: {names}. Restart these programs'
            + ('; log out and back in for the desktop.' if 'desktop' in targets else '.'),
            f'Retour à la langue d\'origine : {names}. Redémarrez ces logiciels'
            + (' ; déconnectez-vous et reconnectez-vous pour le bureau.' if 'desktop' in targets else '.')))


def enable(components=None):
    """Switch Corsican back on, for every part or for the ones listed."""
    if not STATE.exists():
        print(t('Corsu is not installed.', 'Corsu n\'est pas installé.'))
        return
    state = load_state()
    parts = set(switchable(state))
    targets = parts if components is None else set(components) & parts
    disabled = set(state.get('disabled', []))
    if disabled_marker().exists():
        # Everything was off: the parts not switched on now stay off.
        disabled |= parts - targets - {'terminal'}
        if 'terminal' not in targets and 'terminal' in parts:
            (DATA / TERMINAL_OFF).write_text('', encoding='utf-8')
        disabled_marker().unlink()
    if 'terminal' in targets:
        (DATA / TERMINAL_OFF).unlink(missing_ok=True)
    state['disabled'] = sorted(disabled - targets)
    STATE.write_text(json.dumps(state, indent=2), encoding='utf-8')
    rebuild = targets - {'terminal'}
    if 'vesktop' in rebuild and not (ROOT / 'Vencord/dist/vencordDesktopRenderer.js').exists():
        rebuild.discard('vesktop')
    if rebuild:
        install(rebuild, qt_system=state.get('qt_system', False) and 'desktop' in rebuild)
    names = component_names(targets)
    print(t(f'In Corsican again: {names}. Restart these programs'
            + ('; log out and back in for the desktop.' if 'desktop' in targets else '.'),
            f'De nouveau en corse : {names}. Redémarrez ces logiciels'
            + (' ; déconnectez-vous et reconnectez-vous pour le bureau.' if 'desktop' in targets else '.')))


def uninstall():
    if not STATE.exists():
        print(t('Corsu is not installed.', 'Corsu n\'est pas installé.'))
        return
    state = json.loads(STATE.read_text(encoding='utf-8'))
    remaining = {}
    packs = {name: record for name, record in state['files'].items() if record.get('chromium')}
    if packs:
        import chromium
        chromium.restore(packs)
    for name, record in state['files'].items():
        path = Path(name)
        if record.get('chromium'):
            continue
        if record.get('line'):
            if path.exists():
                lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
                path.write_text(''.join(line for line in lines if line.rstrip('\n') != record['line']), encoding='utf-8')
            continue
        if record.get('tree'):
            shutil.rmtree(path, ignore_errors=True)
            continue
        if record.get('json_changes') and path.exists():
            document = json.loads(path.read_text(encoding='utf-8'))
            for field, saved in record['json_changes'].items():
                node = document
                parts = field.split('/')
                for part in parts[:-1]:
                    node = node.get(part, {})
                if node.get(parts[-1]) == saved['installed']:
                    if saved['existed']:
                        node[parts[-1]] = saved['original']
                    else:
                        node.pop(parts[-1], None)
            path.write_text(json.dumps(document, indent=4) + '\n', encoding='utf-8')
            continue
        if path.exists() and digest(path.read_bytes()) != record['installed_sha256']:
            remaining[name] = record
            print(t(f'Left alone because you changed it: {name} (original copy: {record["backup"]})',
                    f'Laissé tel quel car vous l\'avez modifié : {name} (copie d\'origine : {record["backup"]})'))
            continue
        if record.get('system'):
            system_remove([path])
            continue
        if record.get('discord_location') and not os.access(path.parent, os.W_OK):
            if PLATFORM != 'linux':
                remaining[name] = record
                print(f'Discord is read-only; rerun the uninstaller as administrator: {name}')
                continue
            binary, expected = vencord_installer()
            if not binary.exists() or digest(binary.read_bytes()) != expected:
                raise RuntimeError('Official installer checksum mismatch; preserving Discord.')
            subprocess.run(['pkexec', str(binary), '-uninstall', '-location', record['discord_location']], check=True)
            if not path.exists() or digest(path.read_bytes()) != digest(Path(record['backup']).read_bytes()):
                remaining[name] = record
                print(f'Discord restore needs review; original backup: {record["backup"]}')
            continue
        restore(path, record)
        leftover = path.with_name('_app.asar')
        if record.get('discord_location') and record.get('backup') and leftover.is_file() \
                and digest(leftover.read_bytes()) == digest(Path(record['backup']).read_bytes()):
            # The official installer moved the original aside; it is restored in place now.
            leftover.unlink()
    STATE.write_text(json.dumps({'files': remaining}, indent=2), encoding='utf-8')
    disabled_marker().unlink(missing_ok=True)
    (DATA / TERMINAL_OFF).unlink(missing_ok=True)
    print(t(f'Original files and settings are back. Corsu\'s own files stay in {DATA}; you can delete that folder.',
            f'Les fichiers et réglages d\'origine sont remis. Les fichiers de Corsu restent dans {DATA} ; '
            'vous pouvez supprimer ce dossier.'))


SYSTEM_LOCALE = Path('/usr/share/locale/co/LC_MESSAGES')


def system_catalogs(installer):
    """Copy the generated catalogs where programs outside KDE look for them.

    KDE programs read `~/.local/share/locale`, but GTK programs, terminal commands and Qt's own
    dialogs only read system directories, so this step asks for administrator rights once. Files that
    belong to an installed package are never overwritten. `--uninstall` removes everything copied.
    """
    pairs = [(file, QT_TRANSLATIONS / file.name) for file in sorted((DATA / 'qt6/translations').glob('*_co.qm'))]
    for file in sorted((HOME / '.local/share' / CATALOG_SUFFIX).glob('*.mo')):
        target = SYSTEM_LOCALE / file.name
        if target.exists() and str(target) not in installer.state['files']:
            continue
        pairs.append((file, target))
    pairs = [(source, target) for source, target in pairs
             if not target.exists() or digest(target.read_bytes()) != digest(source.read_bytes())]
    if pairs:
        script = 'set -e; mkdir -p "$1"; shift; while [ "$#" -gt 1 ]; do cp -f -- "$1" "$2"; chmod 644 "$2"; shift 2; done'
        command = ['sh', '-c', script, 'corsu', str(SYSTEM_LOCALE), *[str(path) for pair in pairs for path in pair]]
        if not (os.access(QT_TRANSLATIONS, os.W_OK) and os.access(SYSTEM_LOCALE.parent.parent, os.W_OK)):
            command = ['pkexec', *command]
        subprocess.run(command, check=True)
    installed = []
    for source, target in pairs:
        installer.state['files'][str(target)] = {
            'backup': None, 'mode': 0o644, 'toggle': False, 'system': True,
            'installed_sha256': digest(target.read_bytes())}
        installed.append(target.name)
    STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    return installed


def system_remove(paths):
    """Remove the system-wide catalogs this installation added, asking for authentication."""
    existing = [str(path) for path in paths if path.exists()]
    if not existing:
        return
    command = ['rm', '-f', *existing]
    if not os.access(Path(existing[0]).parent, os.W_OK):
        command = ['pkexec', *command]
    subprocess.run(command, check=True)


def launch_firefox(rest):
    """Run the translated build, or the ordinary system Firefox while Corsu is disabled."""
    if is_disabled('firefox'):
        install = firefox_install()
        command = [str(install.root / install.binary), *rest]
    else:
        runtime, stats = firefox_runtime()
        locale = stats.get('locale', 'en-US')
        profile = firefox_profile()
        if profile:
            link_profile(firefox_directory(runtime), profile)
            strings = newtab_strings(profile, locale)
            if strings:
                os.environ['CORSU_NEWTAB'] = str(strings)
        repair_default_browser()
        prune_runtimes(runtime)
        # Reuse the existing profile instead of migrating personal data.
        command = [str(firefox_executable(runtime)), *firefox_arguments(rest, locale)]
    if PLATFORM == 'windows':
        # execv on Windows spawns a child and returns at once, confusing shortcuts and consoles.
        subprocess.Popen(command, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        return
    os.execv(command[0], command)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['generate', 'install', 'uninstall', 'status', 'enable', 'disable',
                                           'prepare-firefox', 'launch-firefox', 'launch-chromium', 'chromium-refresh'])
    args, rest = parser.parse_known_args()
    if args.action == 'generate':
        generate()
    elif args.action == 'install':
        install()
    elif args.action == 'uninstall':
        uninstall()
    elif args.action == 'status':
        status()
    elif args.action == 'enable':
        enable()
    elif args.action == 'disable':
        disable()
    elif args.action == 'prepare-firefox':
        runtime, stats = firefox_runtime()
        print(firefox_executable(runtime))
        print(json.dumps(stats))
    elif args.action == 'launch-chromium':
        import chromium
        chromium.launch(rest[0], rest[1:])
    elif args.action == 'chromium-refresh':
        import chromium
        print(json.dumps(chromium.refresh(), ensure_ascii=False))
    else:
        launch_firefox(rest)


if __name__ == '__main__':
    main()
