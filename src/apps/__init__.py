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

    def __init__(self, app, kind, location, version=None, catalog=None, coverage=None, reason=None):
        self.app, self.kind, self.location, self.version = app, kind, Path(location), version
        self.catalog = Path(catalog) if catalog else None
        self.coverage, self.reason = coverage, reason

    @property
    def usable(self):
        return self.reason is None

    def describe(self):
        parts = [self.kind]
        if self.version:
            parts.append(self.version)
        if self.coverage:
            parts.append(corsu.t(f'Corsican {self.coverage}', f'corse {self.coverage}'))
        return f'{self.app.name} ({", ".join(parts)})'


class App:
    id = name = ''
    description = {'co': '', 'fr': '', 'en': ''}

    def find(self):
        """Installations on this computer; [] when the program is not there."""
        return []

    def enable(self, installer, installation):
        """Switch one installation to Corsican. Returns None when done, else why it was left alone."""
        raise NotImplementedError


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
EXEC = re.compile(r'^(Exec=)(?:env LANGUAGE=\S+ )?(.*)$', re.M)


def desktop_override(installer, component, desktop_id, language):
    """A user menu entry that starts the program with Corsican first. It has the system entry's name, so the menu,
    pinned launchers and file associations open it; it is rebuilt from the system entry each time Corsu runs.
    Returns None when written, else why not."""
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
    text = EXEC.sub(lambda match: f'{match.group(1)}env LANGUAGE={language} {match.group(2)}', text)
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
    from apps import programs, vlc
    return {app.id: app for app in (vlc.VLC(), *(program() for program in programs.PROGRAMS))}


def detected():
    """Programs found here with at least one installation Corsu can switch."""
    return [app_id for app_id, app in registry().items() if any(item.usable for item in app.find())]


def found():
    """Programs found here at all, usable or not (the plan says why not)."""
    return [app_id for app_id, app in registry().items() if app.find()]


def install(installer, app_id):
    """Switch every usable installation of one program. Returns a report and prints one line per installation."""
    app = registry()[app_id]
    done, skipped = [], []
    for installation in app.find():
        reason = installation.reason
        if reason is None:
            try:
                reason = app.enable(installer, installation)
            except (OSError, ValueError, ImportError) as error:
                reason = corsu.t(f'could not write ({error})', f'écriture impossible ({error})')
        entry = {'kind': installation.kind, 'location': str(installation.location), 'version': installation.version,
                 'coverage': installation.coverage}
        if reason:
            skipped.append({**entry, 'reason': reason})
            print(corsu.t(f'{installation.describe()}: left alone: {reason}',
                          f'{installation.describe()} : laissé tel quel : {reason}'))
        else:
            done.append(entry)
            print(corsu.t(f'{installation.describe()}: in Corsican. Restart it if it is open.',
                          f'{installation.describe()} : en corse. Relancez-le s\'il est ouvert.'))
    return {'installed': done, 'skipped': skipped}


def which(*names):
    return next((shutil.which(name) for name in names if shutil.which(name)), None)
