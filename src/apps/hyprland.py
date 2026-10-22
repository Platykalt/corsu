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
# Noctalia's own catalogues, the reference for the coverage of Corsu's.
NOCTALIA_ASSETS = Path('/usr/share/noctalia/assets')
PORTAL_FILES = (Path('/usr/share/xdg-desktop-portal/portals/hyprland.portal'),)
# The Noctalia setting holding the interface language: [table, key] in its TOML settings.
NOCTALIA_LANGUAGE_KEY = ['general', 'language']
LUA_STARTER = 'hyprland.lua'


def paths():
    """Where each file goes, from the person's folders (read again each time: tests change them)."""
    config, data = corsu.CONFIG, corsu.HOME / '.local/share'
    return {'env': config / 'uwsm/env-hyprland',
            'portals': config / 'xdg-desktop-portal/hyprland-portals.conf',
            'hypr': config / 'hypr',
            'modules': config / 'hypr/corsu',
            'starter': config / 'hypr' / LUA_STARTER,
            'user': config / 'hypr/user.lua',
            'noctalia_settings': config / 'noctalia/settings.toml',
            'noctalia_palettes': config / 'noctalia/colorschemes',
            'noctalia_translations': data / 'noctalia/translations'}


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
        try:
            found = dict(helper.versions(run=run))
        except TypeError:
            found = dict(helper.versions())
    if found is None:
        hyprland = run(['Hyprland', '--version']) or run(['hyprland', '--version'])
        noctalia = run(['noctalia', '--version'])
        uwsm = run(['uwsm', 'version'])
        if uwsm is None and shutil.which('uwsm'):
            uwsm = 'uwsm'
        found = {'hyprland': version_text(hyprland), 'noctalia': version_text(noctalia),
                 'uwsm': version_text(uwsm) or ('yes' if uwsm else None),
                 'portal': any(path.exists() for path in PORTAL_FILES)}
    found = {'hyprland': found.get('hyprland'), 'noctalia': found.get('noctalia'), 'uwsm': found.get('uwsm'),
             'portal': bool(found.get('portal') or found.get('xdph') or found.get('xdg-desktop-portal-hyprland'))}
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
    return {'found': found, 'verdict': verdict(found), 'summary': summary(found), 'parts': parts}


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


def machine_lua():
    """~/.config/hypr/corsu/machine.lua: the values found on this computer (keyboard, scale, graphics card). Never a
    template: connector names and card paths differ from one computer to the next."""
    helper = system()
    if helper is not None and hasattr(helper, 'machine_lua'):
        return helper.machine_lua()
    return ('-- Corsu: values found on this computer when the profile was switched on. Corsu rewrites this file;\n'
            '-- put your own settings in ~/.config/hypr/user.lua instead.\n'
            'return {}\n')


def env_profile_lines():
    """The profile's lines for uwsm's env-hyprland (graphics card, toolkit hints), from src/hyprland_system.py:
    its block without its own markers. Empty when this copy has none."""
    helper = system()
    if helper is None or not hasattr(helper, 'env_block'):
        return ''
    lines = [line for line in helper.env_block().splitlines() if not line.strip().startswith('# corsu:')]
    return '\n'.join(lines).strip('\n') + '\n' if any(line.strip() for line in lines) else ''


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


def language_value():
    """Corsican first, then the person's languages, then English: what programs fall back to, said explicitly."""
    languages = apps.corsican_first().split(':')
    if 'en' not in languages:
        languages.append('en')
    return ':'.join(dict.fromkeys(languages))


def language_lines():
    value = language_value()
    fallback = value.split(':', 1)[1].replace(':', ', ')
    return ('# Corsu: Corsican first in the Hyprland session, then ' + fallback + ' for texts not translated yet.\n'
            f'export LANGUAGE={value}\n')


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
    """Corsu's look for Noctalia: ({file name: bytes} of the palettes, [([section, key], value)] of the visual
    settings), from src/hyprland/noctalia/."""
    palettes = template('noctalia', 'palettes')
    files = {path.name: path.read_bytes() for path in sorted(palettes.iterdir()) if path.is_file()} if palettes else {}
    profile = template('noctalia', 'profile.toml')
    values = toml_entries(profile.read_text(encoding='utf-8')) if profile else []
    return files, values


def translation():
    path = template('translations', 'co.json')
    return path.read_bytes() if path else None


def leaves(document):
    if isinstance(document, dict):
        return sum(leaves(value) for value in document.values())
    return 1 if isinstance(document, str) and document else 0


def coverage(data):
    """'N/M' texts of Corsu's Noctalia catalogue against Noctalia's English one, when both can be read."""
    try:
        have = leaves(json.loads(data))
    except (ValueError, TypeError):
        return None
    try:
        total = leaves(json.loads((NOCTALIA_ASSETS / 'translations/en.json').read_text(encoding='utf-8')))
    except (OSError, ValueError):
        total = 0
    return f'{have}/{total}' if total else (f'{have}' if have else None)


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
        if corsu.digest(current) != record['installed_sha256']:
            if not force:
                notes.append(corsu.t(f'changed since, left as it is: {path}', f'modifié depuis, laissé tel quel : {path}'))
                return False
            kept = corsu.DATA / 'backups/hyprland-reset' / time.strftime('%Y%m%d-%H%M%S') / path.name
            kept.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, kept)
            record['installed_sha256'] = corsu.digest(current)
            notes.append(corsu.t(f'your version kept in {kept}', f'votre version gardée dans {kept}'))
        elif current == data and record.get('component') == component and record.get('toggle'):
            return True
    installer.write(path, data, toggle=True)
    installer.state['files'][key]['component'] = component
    corsu.save_state(installer.state)
    return True


def own_block(installer, component, path, name, value, notes):
    """One marked block in a file the person shares with Corsu (uwsm's env-hyprland)."""
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


def own_value(installer, component, path, spec, value, notes, force=False):
    """One TOML value in Noctalia's settings. A value the person changed since in Noctalia stays, unless `force`.
    Noctalia writes its settings at its first start: before that there is nothing to change."""
    key = f'{path}#{json.dumps(list(spec))}'
    record = installer.state['files'].get(key)
    if record and Path(path).exists() and not force:
        current = settings._toml_get(settings.read_body(path)[0], list(spec))
        if current != record['setting']['installed']:
            notes.append(corsu.t(f'{spec[1]} changed in Noctalia, kept', f'{spec[1]} modifié dans Noctalia, gardé'))
            return False
    settings.set_file_value(installer, component, path, 'toml', list(spec), value)
    return True


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

    def leave(self, installer, installation):
        """Left alone now (Hyprland gone or too old): what an earlier run wrote stays until switched off."""


class Language(Hyprland):
    id, name = LANGUAGE, 'Hyprland'
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
            f'Corsu\'s Corsican catalogue in {paths()["noctalia_translations"]} and Noctalia\'s language set to Corsican',
            f'le catalogue corse de Corsu dans {paths()["noctalia_translations"]} et la langue de Noctalia en corse')}

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
            elif data is None:
                why = reason('templates_missing', what='Noctalia (co.json)')
            result.append(apps.Installation(self, self.kind('noctalia'), where['noctalia_translations'] / 'co.json',
                                            found['noctalia'], coverage=coverage(data) if data else None, reason=why))
        return result

    def enable(self, installer, installation):
        where, notes = paths(), []
        if self.key_of(installation) == 'session':
            own_block(installer, self.id, where['env'], 'language', language_lines(), notes)
        else:
            own_file(installer, self.id, where['noctalia_translations'] / 'co.json', translation(), notes)
            if where['noctalia_settings'].exists():
                own_value(installer, self.id, where['noctalia_settings'], NOCTALIA_LANGUAGE_KEY, '"co"', notes)
            else:
                notes.append(corsu.t('Start Noctalia once, then switch Hyprland on again here to choose Corsican in it',
                                     'Démarrez Noctalia une fois, puis réactivez Hyprland ici pour y choisir le corse'))
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
        'co': ('Prufilu di scagnu Corsu per Hyprland', "Facultativu. Una cunfigurazione Hyprland pronta (tasti, finestre, portali) è l'aspettu di Corsu per Noctalia. U vostru user.lua ùn hè mai toccu."),
        'fr': ('Profil de bureau Corsu pour Hyprland', 'Facultatif. Une configuration Hyprland prête (touches, fenêtres, portails) et l\'apparence Corsu pour Noctalia. Votre user.lua n\'est jamais touché.'),
        'en': ('Corsu desktop profile for Hyprland', 'Optional. A ready Hyprland configuration (keys, windows, portals) and Corsu\'s look for Noctalia. Your user.lua is never touched.')}
    kinds = {'config': ('Hyprland configuration', 'configuration Hyprland'), 'look': ('Noctalia look', 'apparence de Noctalia')}
    plans = {
        'config': lambda: corsu.t(
            f'Corsu\'s Lua modules in {paths()["modules"]}, {paths()["starter"]} only if you have none, the Hyprland '
            f'session\'s portals in {paths()["portals"]}; {paths()["user"]} stays yours',
            f'les modules Lua de Corsu dans {paths()["modules"]}, {paths()["starter"]} seulement si vous n\'en avez pas, '
            f'les portails de la session Hyprland dans {paths()["portals"]} ; {paths()["user"]} reste à vous'),
        'look': lambda: corsu.t(
            f'Corsu\'s palette in {paths()["noctalia_palettes"]} and its look in {paths()["noctalia_settings"]}; '
            'what you change later in Noctalia stays',
            f'la palette Corsu dans {paths()["noctalia_palettes"]} et son apparence dans {paths()["noctalia_settings"]} ; '
            'ce que vous changez ensuite dans Noctalia reste')}

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
            palettes, values = look()
            why = None
            if state['noctalia'] != 'ok':
                why = reason('noctalia_version', version=found['noctalia'])
            elif not (palettes or values):
                why = reason('templates_missing', what='Noctalia (src/hyprland/noctalia)')
            result.append(apps.Installation(self, self.kind('look'), where['noctalia_settings'], found['noctalia'], reason=why))
        return result

    def enable(self, installer, installation, force=False):
        where, notes = paths(), []
        if self.key_of(installation) == 'config':
            for name, data in modules().items():
                own_file(installer, self.id, where['modules'] / name, data, notes)
            own_file(installer, self.id, where['modules'] / 'machine.lua', machine_lua(), notes)
            starter = template('config', LUA_STARTER)
            if starter and (not where['starter'].exists() or str(where['starter']) in installer.state['files']):
                own_file(installer, self.id, where['starter'], starter.read_bytes(), notes)
            elif starter:
                notes.append(corsu.t(f'your {where["starter"]} is kept: load ~/.config/hypr/corsu/init.lua from it to use the profile',
                                     f'votre {where["starter"]} est gardé : chargez-y ~/.config/hypr/corsu/init.lua pour utiliser le profil'))
            own_file(installer, self.id, where['portals'], portals_conf(), notes)
            lines = env_profile_lines()
            if lines:
                own_block(installer, self.id, where['env'], 'profile', lines, notes)
        else:
            palettes, values = look()
            for name, data in palettes.items():
                own_file(installer, self.id, where['noctalia_palettes'] / name, data, notes, force=force)
            if values and where['noctalia_settings'].exists():
                for spec, value in values:
                    own_value(installer, self.id, where['noctalia_settings'], spec, value, notes, force=force)
            elif values:
                notes.append(corsu.t('Start Noctalia once, then switch the profile on again here for Corsu\'s look',
                                     'Démarrez Noctalia une fois, puis réactivez le profil ici pour l\'apparence Corsu'))
        installation.action = '; '.join(notes) or None
        for note in notes:
            print(f'  {note}')
        return None


def reset_look():
    """Put Corsu's look back in Noctalia (palettes and the visual settings of the profile), keeping every other
    setting, Hyprland's files and the language. Only when the profile is installed and switched on."""
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
    print(corsu.t('Corsu\'s look is back in Noctalia; your other settings stay. Noctalia applies it when it reloads.',
                  'L\'apparence Corsu est remise dans Noctalia ; vos autres réglages restent. Noctalia l\'applique en se rechargeant.'))
    return True


PROGRAMS = (Language, Profile)
