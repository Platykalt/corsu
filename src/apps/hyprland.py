"""Hyprland and Noctalia: Corsican for the Hyprland session and, as a separate choice, Corsu's desktop profile.

Corsu never installs a desktop. When the person has Hyprland (0.55 or newer, configured in Lua) and Noctalia 5, it
offers two parts, chosen apart (src/hyprland/README.md):

- `hyprland`, the language: Noctalia's interface in Corsican (Corsu's catalogue, where Noctalia reads it, and its
  language setting) and Corsican first for programs started in the Hyprland session (`LANGUAGE`, with the person's
  own languages after it for texts not translated yet). Nothing visual changes.
- `hyprland-profile`, the desktop profile, never ticked by default: Corsu's Hyprland Lua modules, the portals of the
  Hyprland session and Corsu's look for Noctalia.

Every file goes through Corsu's record (installer.state['files']): whole files Corsu owns are written with their
digest, the person's own files get one marked block (uwsm's env-hyprland) or single values (Noctalia's settings), so
switching on twice adds nothing twice and switching off gives back only what is still Corsu's. A file the person
edited since is left as it is, with a message; ~/.config/hypr/user.lua is never read nor written. Plasma is never
touched: every file here is read only by the Hyprland session, uwsm or Noctalia.

The detection and the session values come from src/hyprland_system.py and the templates from src/hyprland/ when
they are there; until then this module has its own minimal stand-ins (see `system()`).
"""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time

import corsu
import apps
from apps import settings

LANGUAGE, PROFILE = 'hyprland', 'hyprland-profile'
# Hyprland reads a Lua configuration from 0.55 on; Noctalia's TOML settings and JSON catalogues are those of 5.x.
MINIMUM_HYPRLAND = (0, 55)
NOCTALIA_MAJOR = 5
# Corsu's templates (owners B and A in src/hyprland/README.md). Tests point this at stand-ins.
TEMPLATES = corsu.SRC / 'hyprland'
# Noctalia's packaged assets: its catalogues (the reference for the coverage of Corsu's) and everything else it loads.
NOCTALIA_ASSETS = Path('/usr/share/noctalia/assets')
PORTAL_FILES = (Path('/usr/share/xdg-desktop-portal/portals/hyprland.portal'),)
LUA_STARTER = 'hyprland.lua'
# Noctalia's menu entry: a copy shown only in Hyprland (started from Plasma's menu it would put a second shell over
# Plasma), rebuilt from the system entry by src/hyprland_system.py.
NOCTALIA_ENTRY = 'dev.noctalia.Noctalia.desktop'
# Noctalia merges every *.toml of ~/.config/noctalia in alphabetical order, then what its Settings window saved
# (~/.local/state/noctalia/settings.toml), which wins. Corsu's layers sort first (src/hyprland/noctalia/).
NOCTALIA_LANGUAGE_FILE, NOCTALIA_PROFILE_FILE = '00-corsu-language.toml', '00-corsu-profile.toml'


def paths():
    """Where each file goes, from the person's folders (read again each time: tests change them)."""
    config = corsu.CONFIG
    return {'env': config / 'uwsm/env-hyprland',
            'portals': config / 'xdg-desktop-portal/hyprland-portals.conf',
            'hypr': config / 'hypr',
            'modules': config / 'hypr/corsu',
            'starter': config / 'hypr' / LUA_STARTER,
            'user': config / 'hypr/user.lua',
            'noctalia': config / 'noctalia',
            'noctalia_palettes': config / 'noctalia/palettes',
            'qt6ct': config / 'qt6ct/qt6ct.conf',
            # Corsu's own folder: Noctalia's assets with Corsu's catalogue added (NOCTALIA_ASSETS_DIR).
            'assets': corsu.DATA / 'noctalia/assets'}


# Files Plasma reads, or shared with it: never written by this module (tests check them byte for byte).
PLASMA_FILES = ('kdeglobals', 'gtk-3.0/settings.ini', 'gtk-4.0/settings.ini', 'plasma-workspace/env/corsu.sh',
                'mimeapps.list', 'plasma-localerc')


def system():
    """src/hyprland_system.py (detection and session values) when this copy has it, else None."""
    try:
        import hyprland_system
    except ImportError:
        return None
    return hyprland_system


# ---------------------------------------------------------------------------------------------------------------
# Detection

def default_run(command):
    """The output of a short command, or None when it is missing or fails."""
    if not shutil.which(command[0]):
        return None
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return (result.stdout or result.stderr) if result.returncode == 0 else None


RUN = default_run
CACHE = {'key': None, 'time': 0.0, 'value': None}


def version_tuple(text):
    match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', text or '')
    return tuple(int(part) for part in match.groups() if part is not None) if match else None


def version_text(text):
    found = version_tuple(text)
    return '.'.join(map(str, found)) if found else None


def detect(run=None):
    """{'hyprland', 'noctalia', 'uwsm': version or None, 'portal': bool}: what is installed here, looked up again
    at most every 20 seconds."""
    run = run or RUN
    if CACHE['key'] is run and time.monotonic() - CACHE['time'] < 20:
        return dict(CACHE['value'])
    found = None
    helper = system()
    if helper is not None and hasattr(helper, 'versions'):
        # Its own runner (English output) unless a test gave one.
        found = dict(helper.versions() if run is default_run else helper.versions(run))
    if found is None:
        hyprland = run(['Hyprland', '--version']) or run(['hyprland', '--version'])
        noctalia = run(['noctalia', '--version'])
        uwsm = run(['uwsm', 'version'])
        if uwsm is None and shutil.which('uwsm'):
            uwsm = 'uwsm'
        found = {'hyprland': version_text(hyprland), 'noctalia': version_text(noctalia),
                 'uwsm': version_text(uwsm) or ('yes' if uwsm else None),
                 'portal': any(path.exists() for path in PORTAL_FILES)}
    # uwsm read from a package database only: still there when its command is.
    uwsm = found.get('uwsm') or ('yes' if run is default_run and shutil.which('uwsm') else None)
    found = {'hyprland': found.get('hyprland'), 'noctalia': found.get('noctalia'), 'uwsm': uwsm,
             'portal': bool(found.get('portal') or found.get('xdph') or any(path.exists() for path in PORTAL_FILES))}
    CACHE.update(key=run, time=time.monotonic(), value=dict(found))
    return found


def verdict(found):
    """Each piece: 'missing', 'old' (too old for Corsu), 'other' (a major version Corsu does not know) or 'ok'."""
    hyprland = version_tuple(found.get('hyprland'))
    noctalia = version_tuple(found.get('noctalia'))
    return {'hyprland': 'missing' if not hyprland else 'old' if hyprland[:2] < MINIMUM_HYPRLAND else 'ok',
            'noctalia': 'missing' if not noctalia else 'old' if noctalia[0] < NOCTALIA_MAJOR
            else 'other' if noctalia[0] > NOCTALIA_MAJOR else 'ok',
            'uwsm': 'ok' if found.get('uwsm') else 'missing',
            'portal': 'ok' if found.get('portal') else 'missing'}


MINIMUM_TEXT = '.'.join(map(str, MINIMUM_HYPRLAND))
# Why a part is not offered or left alone, in the window's three languages; corsu.t() picks French or English for
# the installer. The Corsican lines are AI proposals (AGENTS.md, rule 3), not reviewed by a speaker yet.
REASONS = {
    'hyprland_missing': {
        'co': "Hyprland ùn hè micca stallatu. Corsu ùn stalla micca scagni : stallate Hyprland cù a vostra distribuzione s'è voi u vulete.",
        'fr': 'Hyprland n\'est pas installé. Corsu n\'installe pas de bureau : installez Hyprland avec votre distribution si vous le voulez.',
        'en': 'Hyprland is not installed. Corsu does not install desktops: install Hyprland with your distribution if you want it.'},
    'hyprland_old': {
        'co': f'Hyprland {{version}} hè troppu vechju : Corsu hà bisognu di {MINIMUM_TEXT} o più novu (cunfigurazione in Lua).',
        'fr': f'Hyprland {{version}} est trop ancien : Corsu a besoin de {MINIMUM_TEXT} ou plus récent (configuration en Lua).',
        'en': f'Hyprland {{version}} is too old: Corsu needs {MINIMUM_TEXT} or newer (Lua configuration).'},
    'uwsm_missing': {
        'co': "uwsm ùn hè micca stallatu : a lingua di a sessione Hyprland passa per ~/.config/uwsm/env-hyprland, chì uwsm sulu leghje.",
        'fr': 'uwsm n\'est pas installé : la langue de la session Hyprland passe par ~/.config/uwsm/env-hyprland, que seul uwsm lit.',
        'en': 'uwsm is not installed: the Hyprland session language goes through ~/.config/uwsm/env-hyprland, which only uwsm reads.'},
    'noctalia_version': {
        'co': 'Noctalia {version} : Corsu cunnosce solu Noctalia 5.',
        'fr': 'Noctalia {version} : Corsu ne connaît que Noctalia 5.',
        'en': 'Noctalia {version}: Corsu only knows Noctalia 5.'},
    'templates_missing': {
        'co': "I schedarii {what} mancanu in sta copia di Corsu.",
        'fr': 'Les fichiers {what} manquent dans cette copie de Corsu.',
        'en': 'The {what} files are missing from this copy of Corsu.'},
}


def reason(key, language=None, **values):
    texts = REASONS[key]
    if language is None:
        return corsu.t(texts['en'], texts['fr']).format(**values)
    return texts[language].format(**values)


def unavailable(found=None):
    """{'co', 'fr', 'en'} explaining why neither part can be offered here, or None when Hyprland is usable."""
    if corsu.PLATFORM != 'linux':
        return None
    found = detect() if found is None else found
    state = verdict(found)['hyprland']
    if state == 'missing':
        return dict(REASONS['hyprland_missing'])
    if state == 'old':
        return {language: text.format(version=found['hyprland']) for language, text in REASONS['hyprland_old'].items()}
    return None


def summary(found=None):
    """One line of what was found, for `corsu.py status`, the text menu and the installer's menu."""
    found = detect() if found is None else found
    state = verdict(found)
    present, missing = [], []
    for name, label in (('hyprland', 'Hyprland'), ('noctalia', 'Noctalia'), ('uwsm', 'uwsm'),
                        ('portal', 'xdg-desktop-portal-hyprland')):
        value = found.get(name)
        if not value:
            missing.append(label)
        else:
            present.append(f'{label} {value}' if isinstance(value, str) and value != 'yes' else label)
    parts = [', '.join(present)] if present else []
    if missing:
        parts.append(corsu.t('not installed: ', 'non installé : ') + ', '.join(missing))
    if state['hyprland'] == 'ok':
        verdict_text = corsu.t('Compatible with Corsu.', 'Compatible avec Corsu.')
    elif state['hyprland'] == 'old':
        verdict_text = reason('hyprland_old', version=found['hyprland'])
    else:
        verdict_text = corsu.t('Not offered: Corsu does not install desktops.',
                               'Non proposé : Corsu n\'installe pas de bureau.')
    return 'Hyprland — ' + '; '.join(parts) + '. ' + verdict_text


def status(state=None):
    """What `corsu.py status` shows about Hyprland: versions, verdict and the two parts' state."""
    state = corsu.load_state() if state is None else state
    found = detect()
    parts = {}
    for component in (LANGUAGE, PROFILE):
        installed = component in state.get('components', [])
        result = state.get('results', {}).get(component, {})
        parts[component] = {'installed': installed,
                            'on': installed and not corsu.is_disabled(component, state),
                            'activation': result.get('activation'),
                            'files': sorted(name for name, record in state.get('files', {}).items()
                                            if record.get('component') == component)}
    helper = system()
    findings = []
    if helper is not None and hasattr(helper, 'checks') and found.get('hyprland'):
        # Readable findings (login entry, portals, graphics cards, qt6ct, KWallet) from src/hyprland_system.py.
        try:
            findings = [{'level': level, 'text': text} for level, text in helper.checks(home=corsu.HOME)]
        except (OSError, ValueError, KeyError) as error:
            findings = [{'level': 'warning', 'text': str(error)}]
    return {'found': found, 'verdict': verdict(found), 'summary': summary(found), 'parts': parts, 'checks': findings}


# ---------------------------------------------------------------------------------------------------------------
# Templates and generated values

def template(*parts):
    path = TEMPLATES.joinpath(*parts)
    return path if path.exists() else None


def modules():
    """Corsu's Lua modules: {name: bytes}, from src/hyprland/config/corsu/."""
    folder = template('config', 'corsu')
    if folder is None:
        return {}
    return {path.name: path.read_bytes() for path in sorted(folder.glob('*.lua')) if path.name != 'machine.lua'}


def lua(value):
    """A Lua literal for machine.lua: strings, numbers, booleans, lists and tables of them."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, dict):
        return '{ ' + ', '.join(f'{key} = {lua(item)}' for key, item in value.items() if item is not None) + ' }'
    if isinstance(value, (list, tuple)):
        return '{ ' + ', '.join(lua(item) for item in value) + ' }'
    return json.dumps(str(value), ensure_ascii=False)


def machine_values():
    """What src/hyprland_system.py finds here, in the shape corsu/machine_values.lua reads: keyboard and outputs."""
    helper = system()
    if helper is None:
        return {}
    values = {}
    if hasattr(helper, 'keyboard'):
        keyboard = helper.keyboard(home=corsu.HOME)
        if keyboard:
            values['keyboard'] = {key: keyboard.get(key, '') for key in ('layout', 'variant', 'model', 'options')}
    if hasattr(helper, 'outputs') and hasattr(helper, 'gpus'):
        monitors = []
        for output in helper.outputs(helper.gpus(), corsu.HOME):
            scale = output.get('plasma') or output.get('suggested')
            monitors.append({'output': output['name'], 'mode': output.get('plasma_mode') or 'preferred',
                             'position': 'auto',
                             'scale': scale if scale else None})
        if monitors:
            values['monitors'] = monitors
    return values


def machine_lua():
    """~/.config/hypr/corsu/machine.lua: the values found on this computer (keyboard, outputs and their scale). Never a
    template: connector names differ from one computer to the next."""
    helper = system()
    if helper is not None and hasattr(helper, 'machine_lua'):
        return helper.machine_lua()
    values = machine_values()
    lines = ['-- Written by Corsu from what it found on this computer when the profile was switched on; rewritten at',
             '-- each update unless you change it. Put your own settings in ~/.config/hypr/user.lua instead.',
             'return {']
    lines += [f'    {key} = {lua(value)},' for key, value in values.items()]
    return '\n'.join(lines + ['}']) + '\n'


def env_profile_lines():
    """The profile's lines for uwsm's env-hyprland (graphics cards, Qt theme, cursor, menu prefix), from
    src/hyprland_system.py: its block without markers, comments about the block, nor LANGUAGE (the other part's).
    Empty when this copy has none."""
    helper = system()
    if helper is None or not hasattr(helper, 'env_block'):
        return ''
    try:
        block = helper.env_block(dict(os.environ), home=corsu.HOME, cards=helper.gpus() if hasattr(helper, 'gpus') else None)
    except TypeError:
        block = helper.env_block()
    lines = [line for line in block.splitlines()
             if not line.strip().startswith('# corsu:') and not line.startswith('export LANGUAGE=')
             and not re.match(r'# (Written by Corsu|Corsu rewrites)', line)]
    return '\n'.join(lines).strip('\n') + '\n' if any(line.strip() and not line.startswith('#') for line in lines) else ''


PORTALS = ('[preferred]\n'
           'default=hyprland;gtk\n'
           'org.freedesktop.impl.portal.FileChooser=gtk\n'
           'org.freedesktop.impl.portal.Settings=gtk\n')


def portals_conf():
    """The portals of the Hyprland session only: xdg-desktop-portal reads hyprland-portals.conf when
    XDG_CURRENT_DESKTOP is Hyprland, so Plasma keeps its own."""
    helper = system()
    if helper is not None and hasattr(helper, 'portals_conf'):
        return helper.portals_conf()
    path = template('session', 'hyprland-portals.conf')
    return path.read_text(encoding='utf-8') if path else PORTALS


LANGUAGE_TAG = re.compile(r'[A-Za-z0-9_@.-]+')


def person_languages():
    """The person's languages, without Corsican: Plasma's choice when there is one (read only; Corsu run from a
    terminal or a TTY may not see the desktop's LANG), else this session's."""
    plasma = corsu.CONFIG / 'plasma-localerc'
    try:
        value = settings.ini_get(settings.read_body(plasma)[0], 'Translations', 'LANGUAGE') if plasma.exists() else None
    except ValueError:
        value = None
    languages = [item for item in (value or '').split(':') if item and not item.startswith('co')]
    # Only language tags: the value goes into a file the session's shell reads.
    languages = [item for item in languages or apps.session_languages() if LANGUAGE_TAG.fullmatch(item)]
    return languages or ['fr']


def language_value():
    """Corsican first, then the person's languages, then English: what programs fall back to, said explicitly."""
    languages = ['co', *person_languages()]
    if 'en' not in languages:
        languages.append('en')
    return ':'.join(dict.fromkeys(languages))


def language_lines(assets=None):
    """The language block of env-hyprland; with `assets`, Noctalia also loads Corsu's catalogue from there."""
    value = language_value()
    fallback = value.split(':', 1)[1].replace(':', ', ')
    lines = ('# Corsican first in the Hyprland session, then ' + fallback + ' for texts not translated yet.\n'
             f'export LANGUAGE={shlex.quote(value)}\n')
    if assets:
        lines += ('# Noctalia\'s assets with Corsu\'s Corsican catalogue added (rebuilt by Corsu at each update).\n'
                  f'export NOCTALIA_ASSETS_DIR={shlex.quote(str(assets))}\n')
    return lines


def toml_entries(text):
    """[([section, key], raw value)] of a simple TOML file (tables and `key = value` lines, one per line)."""
    entries, section = [], ''
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        header = settings._toml_header(stripped)
        if header is not None:
            section = header
            continue
        if '=' in stripped:
            key, _, value = stripped.partition('=')
            entries.append(([section, key.strip()], value.strip()))
    return entries


def look():
    """Corsu's look for Noctalia from src/hyprland/noctalia/: ({file name: bytes} of the palettes, the profile layer's
    bytes or None, qt6ct.conf's text or None)."""
    palettes = template('noctalia', 'palettes')
    files = {path.name: path.read_bytes() for path in sorted(palettes.iterdir()) if path.is_file()} if palettes else {}
    profile = template('noctalia', NOCTALIA_PROFILE_FILE)
    qt6ct = template('noctalia', 'qt6ct.conf')
    return files, profile.read_bytes() if profile else None, qt6ct.read_text(encoding='utf-8') if qt6ct else None


def translation():
    path = template('translations', 'co.json')
    return path.read_bytes() if path else None


# What Noctalia checks before using a NOCTALIA_ASSETS_DIR (isAssetRoot, src/hyprland/translations/LOADING.md).
ASSET_ROOT = ('emoji.json', 'fonts/noctalia-tabler.ttf', 'templates/builtin.toml', 'translations/en.json')


def flatten(document, prefix=''):
    found = {}
    for key, value in (document.items() if isinstance(document, dict) else ()):
        if isinstance(value, dict):
            found.update(flatten(value, f'{prefix}{key}.'))
        elif isinstance(value, str):
            found[f'{prefix}{key}'] = value
    return found


def nest(flat):
    document = {}
    for key, value in flat.items():
        node, parts = document, key.split('.')
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return document


def source_hashes():
    """{key: first hex digits of the SHA-1 of the English text co.json translates}, or None when this copy has no list."""
    path = template('translations', 'co.source-hashes.tsv')
    if path is None:
        return None
    hashes = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if line and not line.startswith('#'):
            fields = line.split('\t')
            if len(fields) >= 2:
                hashes[fields[0]] = fields[1]
    return hashes


def read_catalogue(name):
    try:
        return flatten(json.loads((NOCTALIA_ASSETS / 'translations' / name).read_text(encoding='utf-8')))
    except (OSError, ValueError):
        return {}


def catalogue():
    """(co.json for the bundle, Corsican texts used): the installed French catalogue for Noctalia's keys, with Corsu's
    Corsican over it where the English it translates is unchanged; Noctalia adds English for the rest. Never an empty
    text (Noctalia shows an empty one as a missing key). None without Corsu's catalogue."""
    import hashlib
    data = translation()
    if data is None:
        return None, 0
    english, hashes = read_catalogue('en.json'), source_hashes()
    result = {key: value for key, value in read_catalogue('fr.json').items() if key in english and value}
    used = 0
    for key, value in flatten(json.loads(data)).items():
        if key not in english or not value:
            continue
        if hashes is not None and not hashlib.sha1(english[key].encode('utf-8')).hexdigest().startswith(hashes.get(key) or '-'):
            continue  # the English changed since it was translated: French or English shows until it is again
        result[key] = value
        used += 1
    return (json.dumps(nest(result), ensure_ascii=False, indent=2) + '\n').encode('utf-8'), used


def build_assets():
    """Corsu's folder for NOCTALIA_ASSETS_DIR: every entry of Noctalia's packaged assets linked, translations linked
    one by one, plus the co.json built by catalogue(). Rebuilt whole at each run (a Noctalia update adds files); None
    when Noctalia's assets are incomplete or Corsu's catalogue is missing, so the variable never names a folder Noctalia
    would refuse. Never removed when the language is switched off: a running Noctalia's lock screen still needs it."""
    data, _ = catalogue()
    target = paths()['assets']
    if data is None or not all((NOCTALIA_ASSETS / name).exists() for name in ASSET_ROOT):
        return None
    staged, old = target.with_name(target.name + '.corsu-new'), target.with_name(target.name + '.corsu-old')
    for leftover in (staged, old):
        if leftover.is_symlink() or leftover.is_file():
            leftover.unlink()
        elif leftover.exists():
            shutil.rmtree(leftover)
    (staged / 'translations').mkdir(parents=True)
    for entry in NOCTALIA_ASSETS.iterdir():
        if entry.name != 'translations':
            (staged / entry.name).symlink_to(entry)
    for entry in (NOCTALIA_ASSETS / 'translations').iterdir():
        if entry.name != 'co.json':
            (staged / 'translations' / entry.name).symlink_to(entry)
    (staged / 'translations/co.json').write_bytes(data)
    if target.exists():
        target.rename(old)
    staged.rename(target)
    shutil.rmtree(old, ignore_errors=True)
    return target


def coverage():
    """'N/M': Corsican texts Noctalia will show against its English catalogue, when both can be read."""
    _, used = catalogue()
    total = len(read_catalogue('en.json'))
    return f'{used}/{total}' if total else (f'{used}' if used else None)


# ---------------------------------------------------------------------------------------------------------------
# Writing through Corsu's record

def own_file(installer, component, path, data, notes, force=False):
    """Write a whole file Corsu owns. A file Corsu did not write, or one changed since, is left as it is with a note
    (unless `force`: the person asked to put Corsu's back, the changed copy is kept next to the backups)."""
    path = Path(path)
    data = data.encode('utf-8') if isinstance(data, str) else data
    key = str(path)
    record = installer.state['files'].get(key)
    if path.exists():
        current = path.read_bytes()
        if record is None:
            notes.append(corsu.t(f'yours, left as it is: {path}', f'à vous, laissé tel quel : {path}'))
            return False
        if not corsu.owned(current, record):
            if not force:
                notes.append(corsu.t(f'changed since, left as it is: {path}', f'modifié depuis, laissé tel quel : {path}'))
                return False
            kept = corsu.DATA / 'backups/hyprland-reset' / time.strftime('%Y%m%d-%H%M%S') / path.name
            kept.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, kept)
            record['installed_sha256'], record['pending_sha256'] = corsu.digest(current), None
            notes.append(corsu.t(f'your version kept in {kept}', f'votre version gardée dans {kept}'))
        elif current == data and record.get('component') == component and record.get('toggle'):
            return True
    installer.write(path, data, toggle=True, component=component)
    return True


def own_block(installer, component, path, name, value, notes):
    """One marked block in a file the person shares with Corsu (uwsm's env-hyprland). False, with a note, when the
    person changed Corsu's block since: the caller reports the part as not refreshed."""
    key = f'{path}#{json.dumps(name)}'
    record = installer.state['files'].get(key)
    if record and Path(path).exists():
        current = settings._block_get(settings.read_body(path)[0], name)
        if current is not None and current != record['setting']['installed']:
            notes.append(corsu.t(f'block changed since, left as it is: {path}',
                                 f'bloc modifié depuis, laissé tel quel : {path}'))
            return False
    settings.set_block(installer, component, path, name, value)
    return True


def own_new_file(installer, component, path, data, notes, hint=None):
    """A file Corsu writes only when the person has none (hyprland.lua, qt6ct.conf) and never rewrites afterwards:
    switching off still removes it while it is unchanged."""
    path = Path(path)
    if str(path) in installer.state['files']:
        record = installer.state['files'][str(path)]
        if record.get('component') != component or not record.get('toggle'):
            record.update(component=component, toggle=True)
            corsu.save_state(installer.state)
        return True
    if path.exists():
        notes.append(hint or corsu.t(f'yours, left as it is: {path}', f'à vous, laissé tel quel : {path}'))
        return False
    return own_file(installer, component, path, data, notes)


# ---------------------------------------------------------------------------------------------------------------
# The two parts

class Hyprland(apps.App):
    """Common to both parts: found when Hyprland is installed, whatever its version (the reason then says why)."""
    validation = {'simulated': True, 'real_app': [], 'visual': False, 'linguistic_review': False}
    # Not ticked unless the person asks (installer.choose, the window's Add page, a first `--yes` installation).
    opt_in = False
    kinds = {}

    def kind(self, key):
        return corsu.t(*self.kinds[key])

    def key_of(self, installation):
        return next(key for key, labels in self.kinds.items() if installation.kind in labels)

    def window_text(self, found=None):
        """The row's description with what was found, in the window's three languages."""
        found = detect() if found is None else found
        versions = ', '.join(f'{label} {found[name]}' for name, label in (('hyprland', 'Hyprland'), ('noctalia', 'Noctalia'))
                             if found.get(name))
        return {language: (label, f'{detail} ({versions})' if versions else detail)
                for language, (label, detail) in self.description.items()}

    def plan_line(self, installation):
        if not installation.usable:
            return corsu.t('left alone: ', 'laissé tel quel : ') + installation.reason
        return self.plans[self.key_of(installation)]()

    def blocked(self, installation, notes):
        """Why this installation is not (re)applied: the last note, with the others as the action; printed."""
        installation.action = '; '.join(notes[:-1]) or corsu.t(
            'Put the block back as Corsu wrote it, or delete it, then switch on again',
            'Remettez le bloc comme Corsu l\'avait écrit, ou supprimez-le, puis réactivez')
        return notes[-1]

    def leave(self, installer, installation):
        """Left alone now (Hyprland gone or too old): what an earlier run wrote stays until switched off."""


class Language(Hyprland):
    id, name = LANGUAGE, 'Hyprland'

    @property
    def opt_in(self):
        """Ticked in advance only when a compatible Hyprland and Noctalia are both here: Corsu translates what is
        installed and installs no desktop."""
        state = verdict(detect())
        return not (state['hyprland'] == 'ok' and state['noctalia'] == 'ok')

    # The Corsican texts are AI proposals (AGENTS.md, rule 3).
    description = {
        'co': ('Hyprland è Noctalia', "Noctalia in corsu è u corsu prima per i prugrammi di a sessione Hyprland. Nunda ùn cambia per Plasma."),
        'fr': ('Hyprland et Noctalia', 'Noctalia en corse, et le corse d\'abord pour les programmes de la session Hyprland. Rien ne change pour Plasma.'),
        'en': ('Hyprland and Noctalia', 'Noctalia in Corsican, and Corsican first for programs of the Hyprland session. Nothing changes for Plasma.')}
    kinds = {'session': ('Hyprland session', 'session Hyprland'), 'noctalia': ('Noctalia', 'Noctalia')}
    plans = {
        'session': lambda: corsu.t(
            f'Corsican first, then your languages, in a marked block of {paths()["env"]} (read by uwsm for Hyprland only)',
            f'le corse d\'abord, puis vos langues, dans un bloc marqué de {paths()["env"]} (lu par uwsm pour Hyprland seulement)'),
        'noctalia': lambda: corsu.t(
            f'Corsican in {paths()["noctalia"] / NOCTALIA_LANGUAGE_FILE}, Corsu\'s catalogue in {paths()["assets"]}; '
            'a language you pick in Noctalia\'s Settings window wins',
            f'le corse dans {paths()["noctalia"] / NOCTALIA_LANGUAGE_FILE}, le catalogue de Corsu dans {paths()["assets"]} ; '
            'une langue choisie dans la fenêtre Réglages de Noctalia l\'emporte')}

    def find(self):
        found = detect()
        state = verdict(found)
        if state['hyprland'] == 'missing' or corsu.PLATFORM != 'linux':
            return []
        where = paths()
        result = []
        why = action = None
        if state['hyprland'] == 'old':
            why = reason('hyprland_old', version=found['hyprland'])
            action = corsu.t('Update Hyprland, then add it again in Corsu', 'Mettez Hyprland à jour, puis ajoutez-le à nouveau dans Corsu')
        elif state['uwsm'] == 'missing':
            why = reason('uwsm_missing')
            action = corsu.t('Install uwsm and start Hyprland through it', 'Installez uwsm et démarrez Hyprland avec lui')
        result.append(apps.Installation(self, self.kind('session'), where['env'], found['hyprland'], reason=why, action=action))
        if found.get('noctalia'):
            data = translation()
            why = None
            if state['noctalia'] != 'ok':
                why = reason('noctalia_version', version=found['noctalia'])
            elif data is None or template('noctalia', NOCTALIA_LANGUAGE_FILE) is None:
                why = reason('templates_missing', what='Noctalia (co.json, 00-corsu-language.toml)')
            result.append(apps.Installation(self, self.kind('noctalia'), where['noctalia'] / NOCTALIA_LANGUAGE_FILE,
                                            found['noctalia'], coverage=coverage() if data else None, reason=why))
        return result

    def noctalia_usable(self):
        return any(self.key_of(item) == 'noctalia' and item.usable for item in self.find())

    def enable(self, installer, installation):
        where, notes = paths(), []
        if self.key_of(installation) == 'session':
            # Noctalia finds "co" only through the assets folder: built before the variable names it.
            assets = build_assets() if self.noctalia_usable() else None
            if not own_block(installer, self.id, where['env'], 'language', language_lines(assets), notes):
                return self.blocked(installation, notes)
        else:
            if build_assets() is None:
                notes.append(corsu.t(f'Noctalia\'s assets not found in {NOCTALIA_ASSETS}: it stays in English',
                                     f'ressources de Noctalia introuvables dans {NOCTALIA_ASSETS} : il reste en anglais'))
            own_file(installer, self.id, where['noctalia'] / NOCTALIA_LANGUAGE_FILE,
                     template('noctalia', NOCTALIA_LANGUAGE_FILE).read_bytes(), notes)
        installation.action = '; '.join(notes) or None
        for note in notes:
            print(f'  {note}')
        return None


class Profile(Hyprland):
    id = PROFILE
    opt_in = True

    @property
    def name(self):
        return corsu.t('Corsu desktop profile for Hyprland', 'Profil de bureau Corsu pour Hyprland')

    description = {
        'co': ('Prufilu di scagnu Corsu per Hyprland', "Facultativu. Una cunfigurazione Hyprland pronta (tasti, finestre, portali) è l'aspettu di Corsu per Noctalia. U vostru user.lua ùn hè mai toccu. Noctalia ùn s'affaccia più in u listinu di Plasma, per ùn lancià un secondu pannellu sopra à Plasma."),
        'fr': ('Profil de bureau Corsu pour Hyprland', 'Facultatif. Une configuration Hyprland prête (touches, fenêtres, portails) et l\'apparence Corsu pour Noctalia. Votre user.lua n\'est jamais touché. Noctalia n\'apparaît plus dans le menu de Plasma, pour ne pas y lancer un second panneau.'),
        'en': ('Corsu desktop profile for Hyprland', 'Optional. A ready Hyprland configuration (keys, windows, portals) and Corsu\'s look for Noctalia. Your user.lua is never touched. Noctalia no longer shows in Plasma\'s menu, so a second panel is not started over Plasma.')}
    kinds = {'config': ('Hyprland configuration', 'configuration Hyprland'), 'look': ('Noctalia look', 'apparence de Noctalia')}
    plans = {
        'config': lambda: corsu.t(
            f'Corsu\'s Lua modules in {paths()["modules"]}, {paths()["starter"]} only if you have none, the Hyprland '
            f'session\'s portals in {paths()["portals"]}; {paths()["user"]} stays yours',
            f'les modules Lua de Corsu dans {paths()["modules"]}, {paths()["starter"]} seulement si vous n\'en avez pas, '
            f'les portails de la session Hyprland dans {paths()["portals"]} ; {paths()["user"]} reste à vous'),
        'look': lambda: corsu.t(
            f'Corsu\'s palettes in {paths()["noctalia_palettes"]} and its look in {paths()["noctalia"] / NOCTALIA_PROFILE_FILE}; '
            'what you change in Noctalia\'s Settings window wins and stays',
            f'les palettes Corsu dans {paths()["noctalia_palettes"]} et son apparence dans {paths()["noctalia"] / NOCTALIA_PROFILE_FILE} ; '
            'ce que vous changez dans la fenêtre Réglages de Noctalia l\'emporte et reste')}

    def find(self):
        found = detect()
        state = verdict(found)
        if state['hyprland'] == 'missing' or corsu.PLATFORM != 'linux':
            return []
        where = paths()
        why = None
        if state['hyprland'] == 'old':
            why = reason('hyprland_old', version=found['hyprland'])
        elif not modules():
            why = reason('templates_missing', what='Lua (src/hyprland/config/corsu)')
        result = [apps.Installation(self, self.kind('config'), where['modules'], found['hyprland'], reason=why)]
        if found.get('noctalia'):
            palettes, profile, _ = look()
            why = None
            if state['noctalia'] != 'ok':
                why = reason('noctalia_version', version=found['noctalia'])
            elif profile is None:
                why = reason('templates_missing', what='Noctalia (src/hyprland/noctalia)')
            result.append(apps.Installation(self, self.kind('look'), where['noctalia'] / NOCTALIA_PROFILE_FILE,
                                            found['noctalia'], reason=why))
        return result

    def enable(self, installer, installation, force=False):
        where, notes = paths(), []
        if self.key_of(installation) == 'config':
            for name, data in modules().items():
                own_file(installer, self.id, where['modules'] / name, data, notes)
            own_file(installer, self.id, where['modules'] / 'machine.lua', machine_lua(), notes)
            starter = template('config', LUA_STARTER)
            if starter:
                own_new_file(installer, self.id, where['starter'], starter.read_bytes(), notes, corsu.t(
                    f'your {where["starter"]} is kept: add require("corsu.init") to it to use the profile',
                    f'votre {where["starter"]} est gardé : ajoutez-y require("corsu.init") pour utiliser le profil'))
            own_file(installer, self.id, where['portals'], portals_conf(), notes)
            helper = system()
            entry = next((folder / NOCTALIA_ENTRY for folder in apps.APPLICATION_DIRS if (folder / NOCTALIA_ENTRY).exists()), None)
            if entry and helper is not None and hasattr(helper, 'hyprland_only_entry'):
                own_file(installer, self.id, corsu.HOME / '.local/share/applications' / NOCTALIA_ENTRY,
                         helper.hyprland_only_entry(entry.read_text(encoding='utf-8')), notes)
            lines = env_profile_lines()
            if lines and not own_block(installer, self.id, where['env'], 'profile', lines, notes):
                return self.blocked(installation, notes)
        else:
            palettes, profile, qt6ct = look()
            for name, data in palettes.items():
                own_file(installer, self.id, where['noctalia_palettes'] / name, data, notes, force=force)
            own_file(installer, self.id, where['noctalia'] / NOCTALIA_PROFILE_FILE, profile, notes, force=force)
            if qt6ct:
                # qt6ct does not expand variables: the person's config folder, written out.
                own_new_file(installer, self.id, where['qt6ct'], qt6ct.replace('@CONFIG_HOME@', str(corsu.CONFIG)), notes)
        installation.action = '; '.join(notes) or None
        for note in notes:
            print(f'  {note}')
        return None


def reset_look():
    """Put Corsu's look back in Noctalia: its palettes and profile layer as Corsu ships them, even edited (the edited
    copy is kept in Corsu's backups). What Noctalia's Settings window saved (~/.local/state/noctalia/settings.toml) is
    never edited: it wins over Corsu's layer, and Noctalia's own "Reset Page" takes it back page by page. Hyprland's
    files and the language stay. Only when the profile is installed and switched on."""
    state = corsu.load_state()
    if PROFILE not in state.get('components', []) or corsu.is_disabled(PROFILE, state):
        print(corsu.t('The Corsu desktop profile is not switched on: nothing to reset.',
                      'Le profil de bureau Corsu n\'est pas activé : rien à remettre.'))
        return False
    profile = Profile()
    looks = [item for item in profile.find() if profile.key_of(item) == 'look']
    if not looks or not looks[0].usable:
        print(corsu.t('Noctalia is not usable here: nothing to reset.', 'Noctalia n\'est pas utilisable ici : rien à remettre.')
              + (f' {looks[0].reason}' if looks else ''))
        return False
    installer = corsu.Installer()
    profile.enable(installer, looks[0], force=True)
    result = installer.state.setdefault('results', {}).get(PROFILE)
    if result:
        result.update(operation='reset_look', time=time.time())
    corsu.save_state(installer.state)
    print(corsu.t('Corsu\'s look files are back; your other settings stay. What you chose in Noctalia\'s Settings '
                  'window still wins: use "Reset Page" there to go back to Corsu\'s look page by page.',
                  'Les fichiers d\'apparence de Corsu sont remis ; vos autres réglages restent. Ce que vous avez choisi dans '
                  'la fenêtre Réglages de Noctalia l\'emporte toujours : « Reset Page » y revient à l\'apparence Corsu page par page.'))
    return True


PROGRAMS = (Language, Profile)
