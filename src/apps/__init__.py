"""Programs that already have a Corsican translation of their own, switched to Corsican by Corsu.

Each program is an adapter: it finds the installations on this computer (system package, Flatpak, Snap, portable…),
says whether each one has its Corsican catalogue and how much of the program it covers, and switches it on with the
least change possible: the program's own language setting, or, when it only follows the session language, its menu
entry started with Corsican first. Corsu never installs the programs themselves.

The order of preference: switch on a Corsican translation the program already ships; install an official catalogue
when it is missing (not done yet for any program); add a Corsu complement only when needed, named as such.
"""
import os
from pathlib import Path
import re
import shutil

import corsu
from apps import settings


class Installation:
    """One installation of a program, and either what Corsu would do there or why it leaves it alone."""

    def __init__(self, app, kind, location, version=None, catalog=None, coverage=None, reason=None, action=None):
        self.app, self.kind, self.location, self.version = app, kind, Path(location), version
        self.catalog = Path(catalog) if catalog else None
        self.coverage, self.reason = coverage, reason
        # The next useful step for the person when Corsu leaves this installation alone.
        self.action = action

    @property
    def usable(self):
        return self.reason is None

    def describe(self):
        parts = [self.kind]
        if self.version:
            parts.append(self.version)
        if self.coverage and self.coverage[0].isdigit():
            parts.append(corsu.t(f'Corsican {self.coverage}', f'corse {self.coverage}'))
        elif self.coverage:
            parts.append(self.coverage)
        return f'{self.app.name} ({", ".join(parts)})'


class App:
    id = name = ''
    description = {'co': '', 'fr': '', 'en': ''}
    # How this switch was checked: fixtures (simulated folders, files, registry), the real program on these platforms
    # (its files and settings, read by the program at start), its window looked at, its Corsican reviewed by a speaker.
    validation = {'simulated': True, 'real_app': [], 'visual': False, 'linguistic_review': False}
    # Executable names that, when running, need a restart to show Corsican (programs that do not rewrite the setting).
    restart_processes = ()

    def find(self):
        """Installations on this computer; [] when the program is not there."""
        return []

    def enable(self, installer, installation):
        """Switch one installation to Corsican. Returns None when done, else why it was left alone."""
        raise NotImplementedError

    def leave(self, installer, installation):
        """Called instead of enable() when an installation is left alone: take back what an earlier run did there
        and no longer applies (nothing by default)."""


def session_languages():
    """The language list programs read on Linux (LANGUAGE, else LANG), without Corsican."""
    value = (os.environ.get('LANGUAGE') or os.environ.get('LC_ALL') or os.environ.get('LC_MESSAGES')
             or os.environ.get('LANG') or 'fr')
    languages = []
    for item in value.split(':'):
        language = item.split('.')[0].split('@')[0]
        if language and language not in ('C', 'POSIX') and not language.startswith('co'):
            languages.append(language)
    return languages or ['fr']


def corsican_first():
    """LANGUAGE value putting Corsican first, then the person's own languages for what is not translated."""
    return ':'.join(['co', *session_languages()])


def session_is_corsican():
    return (os.environ.get('LANGUAGE') or os.environ.get('LANG') or '').startswith('co')


APPLICATION_DIRS = (Path('/usr/share/applications'), Path('/usr/local/share/applications'),
                    Path('/var/lib/flatpak/exports/share/applications'))
# What Corsu puts in front of a command; taken away before it writes it again.
EXEC = re.compile(r'^(Exec=)(?:env (?:(?:LANGUAGE|VLC_DATA_PATH)=\S+ |"(?:LANGUAGE|VLC_DATA_PATH)=(?:[^"\\]|\\.)*" )+)?(.*)$',
                  re.M)


def exec_value(name, value):
    """NAME=value as one argument of a menu entry's Exec line, quoted when it holds spaces. Characters that need a
    double escape there (" ` $ \\) are refused rather than risked."""
    value = str(value).replace('%', '%%')
    if re.search(r'["`$\\]', value):
        raise ValueError(f'{value!r} cannot go in a menu entry')
    return f'{name}={value}' if re.fullmatch(r'[\w@%+=:,./-]+', value) else f'"{name}={value}"'


def desktop_override(installer, component, desktop_id, language, environment=None):
    """A user menu entry that starts the program with Corsican first. It has the system entry's name, so the menu,
    pinned launchers and file associations open it; it is rebuilt from the system entry each time Corsu runs.
    `environment`: more variables for the program ({name: value}). Returns None when written, else why not."""
    system = next((folder / desktop_id for folder in APPLICATION_DIRS if (folder / desktop_id).exists()), None)
    if system is None:
        return corsu.t(f'no menu entry {desktop_id}', f'pas d\'entrée de menu {desktop_id}')
    user = corsu.HOME / '.local/share/applications' / desktop_id
    record = installer.state['files'].get(str(user))
    if user.exists() and record is None:
        return corsu.t(f'you have your own menu entry {user}; left alone',
                       f'vous avez votre propre entrée de menu {user} ; laissée telle quelle')
    if user.exists() and record and corsu.digest(user.read_bytes()) != record['installed_sha256']:
        return corsu.t(f'menu entry changed since; left alone: {user}', f'entrée de menu modifiée depuis ; laissée : {user}')
    text = system.read_text(encoding='utf-8')
    if re.search(r'^DBusActivatable=true', text, re.M):
        return corsu.t('started through D-Bus: the menu entry cannot set its language',
                       'lancé par D-Bus : l\'entrée de menu ne peut pas choisir sa langue')
    variables = ' '.join(exec_value(name, value) for name, value in {'LANGUAGE': language, **(environment or {})}.items())
    text = EXEC.sub(lambda match: f'{match.group(1)}env {variables} {match.group(2)}', text)
    installer.write(user, text, toggle=True)
    installer.state['files'][str(user)]['component'] = component
    return None


FLATPAK_SYSTEM = Path('/var/lib/flatpak')


def flatpak_installed(app_id):
    for base in (corsu.HOME / '.local/share/flatpak', FLATPAK_SYSTEM):
        if (base / 'app' / app_id).is_dir():
            return base
    return None


def flatpak_catalog(base, app_id, domain):
    """The Corsican catalogue in a Flatpak's locale extension, if the extension holds Corsican."""
    for path in (base / 'runtime' / f'{app_id}.Locale').glob(f'*/*/*/files/co/share/co/LC_MESSAGES/{domain}.mo'):
        return path
    return None


def flatpak_language(installer, component, app_id, language):
    """Corsican first for one Flatpak, in its user override file (what `flatpak override --user --env` writes)."""
    path = corsu.HOME / '.local/share/flatpak/overrides' / app_id
    settings.set_ini(installer, component, path, 'Environment', 'LANGUAGE', language)


def mo_entries(path):
    import engine
    try:
        return len(engine.read_mo(Path(path).read_bytes())) - 1
    except (OSError, ValueError):
        return 0


def coverage_against(corsican, reference):
    """'N/M' messages, the Corsican catalogue against the French one of the same installation, when both exist."""
    have = mo_entries(corsican)
    total = mo_entries(reference) if reference and Path(reference).exists() else 0
    return f'{have}/{total}' if total else (f'{have}' if have else None)


def registry():
    from apps import audacity, freac, hyprland, pdfsam, poedit, programs, vlc
    return {app.id: app for app in (vlc.VLC(), *(program() for program in
                                                 (*programs.PROGRAMS, *audacity.PROGRAMS, *freac.PROGRAMS,
                                                  *poedit.PROGRAMS, *pdfsam.PROGRAMS, *hyprland.PROGRAMS)))}


def opt_in(app_id):
    """A part offered but never ticked unless the person asks for it (the Hyprland desktop profile)."""
    return bool(getattr(registry().get(app_id), 'opt_in', False))


def detected():
    """Programs found here with at least one installation Corsu can switch."""
    return [app_id for app_id, app in registry().items() if any(item.usable for item in app.find())]


def found():
    """Programs found here at all, usable or not (the plan says why not)."""
    return [app_id for app_id, app in registry().items() if app.find()]


# The status of one program, kept in Corsu's state as state['results'][app_id] and read by the window and the
# installation summary alike, so they cannot disagree. Activation and translation coverage are separate: a program
# switched on whose Corsican catalogue covers 72 % of its texts is "active" with a "partial" coverage.
#   activation: active | partial (some installations switched, others not) | inactive | blocked (a known condition:
#               catalogue missing, program open, settings not created yet, changed by the person) | failed (an error)
#               | restart_required (switched while the program was open)
#   instances:  [{kind, location, version, activation, reason, action, coverage}]
#   coverage:   {state: complete | partial | unknown, translated, total, note}
ACTIVE = ('active', 'partial', 'restart_required')


def coverage_record(value):
    """The coverage of a catalogue from 'N/M', 'N' or a descriptive note."""
    record = {'state': 'unknown', 'translated': None, 'total': None, 'note': None}
    match = re.fullmatch(r'(\d+)(?:/(\d+))?', value or '')
    if match:
        record['translated'] = int(match[1])
        if match[2]:
            record['total'] = int(match[2])
            record['state'] = 'complete' if record['translated'] >= record['total'] else 'partial'
    elif value:
        record['note'] = value
    return record


def aggregate(instances):
    states = [instance['activation'] for instance in instances]
    if not states:
        return 'inactive'
    switched = [state for state in states if state in ('active', 'restart_required')]
    if switched and len(switched) < len(states):
        return 'partial'
    if switched:
        return 'restart_required' if 'restart_required' in switched else 'active'
    return 'failed' if 'failed' in states else 'blocked'


def total_coverage(instances):
    """The lowest measured coverage among switched installations (what the person may see), else unknown."""
    measured = [instance['coverage'] for instance in instances
                if instance['activation'] in ('active', 'restart_required') and instance['coverage']['total']]
    if not measured:
        return next((instance['coverage'] for instance in instances if instance['coverage']['note']),
                    coverage_record(None))
    return min(measured, key=lambda record: record['translated'] / record['total'])


def install(installer, app_id):
    """Switch every usable installation of one program, print one line per installation and return its status
    (see above), also kept in installer.state['results']."""
    app = registry()[app_id]
    instances = []
    for installation in app.find():
        reason, action, activation = installation.reason, installation.action, 'blocked'
        if reason is not None:
            app.leave(installer, installation)
        if reason is None:
            try:
                reason = app.enable(installer, installation)
            except RuntimeError as error:
                # Raised with a message for the person; also a file Corsu wrote and the person changed since.
                reason, activation = str(error), 'failed'
            except (OSError, ValueError, ImportError) as error:
                reason, activation = corsu.t(f'could not write ({error})', f'écriture impossible ({error})'), 'failed'
            if reason is None:
                # What enable() noted for the person (a file of theirs left as it is) stays next to the status.
                action = installation.action
                running = app.restart_processes and _running(app.restart_processes)
                activation = 'restart_required' if running else 'active'
                if running:
                    action = corsu.t(f'Restart {app.name} to see it in Corsican', f'Relancez {app.name} pour le voir en corse')
        instances.append({'kind': installation.kind, 'location': str(installation.location),
                          'version': installation.version, 'activation': activation, 'reason': reason,
                          'action': action, 'coverage': coverage_record(installation.coverage)})
        if activation in ('blocked', 'failed'):
            print(corsu.t(f'{installation.describe()}: left alone: {reason}',
                          f'{installation.describe()} : laissé tel quel : {reason}'))
        else:
            print(corsu.t(f'{installation.describe()}: in Corsican. Restart it if it is open.',
                          f'{installation.describe()} : en corse. Relancez-le s\'il est ouvert.'))
    result = {'activation': aggregate(instances), 'operation': 'install', 'time': __import__('time').time(),
              'instances': instances, 'coverage': total_coverage(instances)}
    installer.state.setdefault('results', {})[app_id] = result
    # 'installed' and 'skipped': the earlier report's lists, still read by report.json readers.
    return {**result, 'installed': [instance for instance in instances if instance['activation'] in ('active', 'restart_required')],
            'skipped': [instance for instance in instances if instance['activation'] in ('blocked', 'failed')]}


def _running(names):
    from apps import programs
    return programs.running(*names)


def summary(results):
    """(installed, partly, left alone) program ids from their statuses: the installation summary's three lines."""
    installed = sorted(app_id for app_id, result in results.items() if result['activation'] in ('active', 'restart_required'))
    partly = sorted(app_id for app_id, result in results.items() if result['activation'] == 'partial')
    left = sorted(app_id for app_id, result in results.items() if result['activation'] in ('blocked', 'failed'))
    return installed, partly, left


def busy(component):
    """Why a program's setting cannot be put back now (it is open and rewrites its settings when it quits), or None."""
    app = registry().get(component)
    processes = getattr(app, 'processes', ())
    if processes:
        from apps import programs
        if programs.running(*processes):
            return programs.close_first(app.name)
    return None


def which(*names):
    return next((shutil.which(name) for name in names if shutil.which(name)), None)
