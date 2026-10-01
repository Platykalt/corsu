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
import zipfile

import engine
from engine import make_mo, make_qm, read_mo, read_qm, translate, WORDS

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
DATA = HOME / '.local/share/corsu'
STATE = DATA / 'installation.json'
LEXICON = engine.LEXICON
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', HOME / '.config'))
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
        self.state = json.loads(STATE.read_text()) if STATE.exists() else {'files': {}}

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
        STATE.write_text(json.dumps(self.state, indent=2))
        temp = path.with_name(path.name + '.corsu-tmp')
        temp.write_bytes(data)
        temp.chmod(mode if mode is not None else (record['mode'] or 0o644))
        temp.replace(path)

    def json_settings(self, path, changes, toggle=False):
        path = Path(path)
        document = json.loads(path.read_text()) if path.exists() else {}
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
        STATE.write_text(json.dumps(self.state, indent=2))

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
        STATE.write_text(json.dumps(self.state, indent=2))


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
    for source in sorted(Path('/usr/share/applications').glob('*.desktop')):
        target = HOME / '.local/share/applications' / source.name
        text = (target if target.exists() else source).read_text()
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


def firefox_runtime():
    source = Path('/usr/lib/firefox')
    fr_path = ROOT / 'vendor/firefox-fr.xpi'
    version = configparser.ConfigParser()
    version.read(source / 'application.ini')
    app_version = version['App']['Version']
    fr = zipfile.ZipFile(fr_path) if fr_path.exists() else None
    # Messages are merged by id, so a French pack from another version is still usable.
    use_fr = fr is not None
    fingerprint = hashlib.sha256(LEXICON.read_bytes() + Path(__file__).read_bytes())
    for file in ('omni.ja', 'browser/omni.ja', 'application.ini', 'platform.ini'):
        fingerprint.update((source / file).read_bytes())
    for file in sorted(source.rglob('*')):
        if file.is_file():
            stat = file.stat()
            fingerprint.update(f'{file.relative_to(source)}:{stat.st_size}:{stat.st_mtime_ns}'.encode())
    if use_fr:
        fingerprint.update(fr_path.read_bytes())
    target = DATA / 'firefox' / fingerprint.hexdigest()[:16]
    if (target / 'corsu-report.json').exists():
        return target, json.loads((target / 'corsu-report.json').read_text())
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='build-', dir=target.parent))
    try:
        shutil.copytree(source, stage, dirs_exist_ok=True, symlinks=True)
        stats = {'version': app_version, 'translated_values': 0, 'ftl_files': 0,
                 'fallback': 'fr' if use_fr else 'en-US', 'partial': True}
        for name in ('omni.ja', 'browser/omni.ja'):
            with read_zip(source / name) as original, zipfile.ZipFile(stage / name, 'w', zipfile.ZIP_DEFLATED) as output:
                for info in original.infolist():
                    data = original.read(info.filename)
                    if info.filename.endswith('.ftl') and '/en-US/' in info.filename:
                        french_name = ('browser/' if name.startswith('browser/') else '') + info.filename.replace('/en-US/', '/fr/')
                        if use_fr and french_name in fr.namelist():
                            data, merged = merge_ftl(data.decode(), fr.read(french_name).decode())
                            data = data.encode()
                            stats['french_messages'] = stats.get('french_messages', 0) + merged
                        patched, count = patch_ftl(data.decode())
                        data = patched.encode()
                        stats['translated_values'] += count
                        stats['ftl_files'] += 1
                    elif info.filename.endswith('.properties') and '/locale/' in info.filename:
                        lines = []
                        for line in data.decode('utf-8').splitlines(keepends=True):
                            match = re.match(r'^([^#!\s][^=\n]*=)([^\n]*)(\n)?$', line)
                            if match:
                                value = translate(match[2])
                                stats['translated_values'] += int(value != match[2])
                                line = match[1] + value + (match[3] or '')
                            lines.append(line)
                        data = ''.join(lines).encode()
                    output.writestr(info.filename, data)
        # Keep the normal profile and extension signature checks; do not relax security.
        prefs = stage / 'defaults/pref/corsu.js'
        prefs.parent.mkdir(parents=True, exist_ok=True)
        prefs.write_text('pref("intl.locale.requested", "en-US");\n')
        (stage / 'corsu-report.json').write_text(json.dumps(stats, indent=2))
        stage.rename(target)
        return target, stats
    except BaseException:
        shutil.rmtree(stage)
        raise
    finally:
        if fr:
            fr.close()


def generate():
    plugin = ROOT / 'Vencord/src/userplugins/corsu'
    plugin.mkdir(parents=True, exist_ok=True)
    (plugin / 'dictionary.json').write_text(json.dumps(WORDS, ensure_ascii=False, indent=2))
    for name in ('index.ts', 'translate.ts'):
        shutil.copy2(ROOT / 'plugin' / name, plugin / name)


def firefox_profile():
    """Find the existing default; let Firefox choose when selection is ambiguous."""
    for base in (HOME / '.config/mozilla/firefox', HOME / '.mozilla/firefox'):
        config = configparser.ConfigParser(interpolation=None)
        config.read(base / 'profiles.ini')
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


def firefox_arguments(rest):
    # Explicit profile selection takes precedence over our discovered default.
    selectors = {'-profile', '--profile', '-p', '--p', '-profilemanager', '--profilemanager'}
    if any(arg.lower().split('=', 1)[0] in selectors for arg in rest):
        return ['-UILocale', 'en-US', *rest]
    profile = firefox_profile()
    selection = ['-profile', str(profile)] if profile else ['-ProfileManager']
    return [*selection, '-UILocale', 'en-US', *rest]


def status():
    """Read installation health without building or changing app settings."""
    state = json.loads(STATE.read_text()) if STATE.exists() else {'files': {}}
    counts = {'managed': len(state['files']), 'missing': [], 'changed': []}
    for name, record in state['files'].items():
        path = Path(name)
        if not path.exists():
            counts['missing'].append(name)
        elif record.get('json_changes'):
            document = json.loads(path.read_text())
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
                      'last_build': json.loads(report_path.read_text()) if report_path.exists() else None},
                     ensure_ascii=False, indent=2))


def desktop(installer, firefox=True, vesktop=True):
    launcher = HOME / '.local/bin/firefox-corsu'
    if firefox:
        installer.write(launcher, f'#!/bin/sh\nexec python3 {shlex.quote(str(ROOT / "corsu.py"))} launch-firefox "$@"\n', 0o755)
    entries = ([('firefox.desktop', str(launcher))] if firefox else []) + ([('vesktop.desktop', None)] if vesktop else [])
    for desktop_id, executable in entries:
        existing = HOME / '.local/share/applications' / desktop_id
        original = existing if existing.exists() else Path('/usr/share/applications') / desktop_id
        if not original.exists():
            continue
        text = original.read_text()
        if executable:
            text = re.sub(r'^Exec=(?:/usr/lib/firefox/firefox|/usr/bin/firefox|firefox)(?=\s|$)', f'Exec={executable}', text, flags=re.M)
        name = 'Firefox — Corsu' if executable else 'Discord — Corsu (Vesktop)'
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
    installer.state['components'] = sorted(set(installer.state.get('components', [])) | components)
    installer.state['qt_system'] = qt_system or installer.state.get('qt_system', False)
    installer.state['enabled'] = True
    STATE.write_text(json.dumps(installer.state, indent=2))
    disabled_marker().unlink(missing_ok=True)
    clients = sorted({'Vesktop' if name == 'vesktop' else 'Discord' for name in components
                      if name in ('vesktop', 'discord')})
    report = {'kde': kde_stats, 'firefox': firefox_stats, 'firefox_runtime': str(runtime) if runtime else None,
              'discord': {'clients': clients, 'plugin': 'Corsu', 'dictionary_labels': len(WORDS), 'partial': True},
              'components': sorted(components), 'enabled': True,
              'scope': 'Interface labels only; no translation of messages or arbitrary websites.'}
    (DATA / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


def disabled_marker():
    return DATA / 'disabled'


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


def disable():
    """Return every application to its previous language, keeping the built catalogs.

    Only the switches are reverted, so `enable` is fast and needs no rebuild.
    """
    if not STATE.exists():
        print('No installation recorded.')
        return
    installer = Installer()
    preserved = []
    for name, record in list(installer.state['files'].items()):
        if not record.get('toggle'):
            continue
        path = Path(name)
        if record.get('json_changes'):
            fields = {field: False for field in record['json_changes'] if field.endswith('/enabled')}
            if fields and path.exists():
                installer.json_settings(path, fields, toggle=True)
            continue
        if restore(path, record):
            installer.state['files'].pop(name)
        else:
            preserved.append(name)
    installer.state['enabled'] = False
    STATE.write_text(json.dumps(installer.state, indent=2))
    DATA.mkdir(parents=True, exist_ok=True)
    disabled_marker().write_text('Corsu is disabled. Run: python3 corsu.py enable\n')
    for name in preserved:
        print(f'Preserved changed file: {name}')
    print('Corsu disabled. Restart applications; log out and back in for Plasma.\n'
          'Catalogs and builds are kept for a fast: python3 corsu.py enable')


def enable():
    """Switch Corsican back on using the components recorded at installation."""
    if not STATE.exists():
        print('No installation recorded.')
        return
    state = json.loads(STATE.read_text())
    components = set(state.get('components') or ['firefox', 'desktop', 'vesktop'])
    if 'vesktop' in components and not (ROOT / 'Vencord/dist/vencordDesktopRenderer.js').exists():
        components.discard('vesktop')
    install(components, qt_system=state.get('qt_system', False))
    print('Corsu enabled. Restart applications; log out and back in for Plasma.')


def uninstall():
    if not STATE.exists():
        print('No installation recorded.')
        return
    state = json.loads(STATE.read_text())
    remaining = {}
    for name, record in state['files'].items():
        path = Path(name)
        if record.get('json_changes') and path.exists():
            document = json.loads(path.read_text())
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
            path.write_text(json.dumps(document, indent=4) + '\n')
            continue
        if path.exists() and digest(path.read_bytes()) != record['installed_sha256']:
            remaining[name] = record
            print(f'Preserved changed file; original backup: {record["backup"]}: {name}')
            continue
        if record.get('system'):
            system_remove([path])
            continue
        if record.get('discord_location') and not os.access(path.parent, os.W_OK):
            binary = ROOT / 'vendor/VencordInstallerCli-linux'
            manifest = json.loads((ROOT / 'release.json').read_text())
            if digest(binary.read_bytes()) != manifest['installer_sha256']:
                raise RuntimeError('Official installer checksum mismatch; preserving Discord.')
            subprocess.run(['pkexec', str(binary), '-uninstall', '-location', record['discord_location']], check=True)
            if not path.exists() or digest(path.read_bytes()) != digest(Path(record['backup']).read_bytes()):
                remaining[name] = record
                print(f'Discord restore needs review; original backup: {record["backup"]}')
            continue
        restore(path, record)
    STATE.write_text(json.dumps({'files': remaining}, indent=2))
    disabled_marker().unlink(missing_ok=True)
    print('Restored unchanged managed settings. Local builds retained in ' + str(DATA))


def system_catalogs(installer):
    """Copy generated Qt catalogs into Qt's own translation directory.

    Qt reads its standard dialog strings only from a system directory, so this step asks for
    administrator authentication. Every file is recorded and removed again by `--uninstall`.
    """
    files = sorted((DATA / 'qt6/translations').glob('*_co.qm'))
    if not files:
        return []
    command = ['cp', '-f', *map(str, files), str(QT_TRANSLATIONS)]
    if not os.access(QT_TRANSLATIONS, os.W_OK):
        command = ['pkexec', *command]
    subprocess.run(command, check=True)
    installed = []
    for file in files:
        target = QT_TRANSLATIONS / file.name
        installer.state['files'][str(target)] = {
            'backup': None, 'mode': 0o644, 'toggle': False, 'system': True,
            'installed_sha256': digest(target.read_bytes())}
        installed.append(target.name)
    STATE.write_text(json.dumps(installer.state, indent=2))
    return installed


def system_remove(paths):
    """Remove root-owned Qt catalogs this installation added, asking for authentication."""
    existing = [str(path) for path in paths if path.exists()]
    if not existing:
        return
    command = ['rm', '-f', *existing]
    if not os.access(Path(existing[0]).parent, os.W_OK):
        command = ['pkexec', *command]
    subprocess.run(command, check=True)


def launch_firefox(rest):
    """Run the translated build, or the ordinary system Firefox while Corsu is disabled."""
    if disabled_marker().exists():
        system = Path('/usr/lib/firefox/firefox')
        os.execv(str(system), [str(system), *rest])
    runtime, _ = firefox_runtime()
    # Reuse the existing profile instead of migrating personal data.
    os.execv(str(runtime / 'firefox'), [str(runtime / 'firefox'), *firefox_arguments(rest)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['generate', 'install', 'uninstall', 'status', 'enable', 'disable',
                                           'prepare-firefox', 'launch-firefox'])
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
        print(runtime)
        print(json.dumps(stats))
    else:
        launch_firefox(rest)


if __name__ == '__main__':
    main()
