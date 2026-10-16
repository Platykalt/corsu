"""fre:ac, whose Corsican translation (lang/freac_co.xml) is Patriccollu di Santa Maria è Sichè's.

The setting is the value Language of the section Settings, in the configuration "default" of freac.xml:
<ConfigFile><configuration name="default"><section name="Settings"><value name="Language">freac_co.xml</value>.
It holds the language file's name, not a code
(https://github.com/enzo1982/freac/blob/v1.1.7/src/config.cpp#L60-L61; read and written back at every start,
https://github.com/enzo1982/freac/blob/v1.1.7/src/freac.cpp#L114-L121; the name is file.GetFileName(),
https://github.com/enzo1982/smooth/blob/0da5d2788a45b3b5fffda078377a51f633381bfd/classes/i18n/translator.cpp#L402-L420;
element names: https://github.com/enzo1982/smooth/blob/0da5d2788a45b3b5fffda078377a51f633381bfd/classes/misc/config.cpp#L14-L22).

Where freac.xml is (https://github.com/enzo1982/BoCA/blob/8ffdb685e31fc85e8f8cb3cfff5dbc38acb85ca2/runtime/common/config.cpp#L279-L350):
next to the program when the program is outside the Program Files folder and either freac.xml is already there or
the folder can be written; otherwise in the user's settings folder:
  - Windows: %APPDATA%\\freac\\freac.xml (CSIDL_APPDATA,
    https://github.com/enzo1982/smooth/blob/0da5d2788a45b3b5fffda078377a51f633381bfd/classes/system/system.cpp#L316-L372).
    Installed in Program Files: there. Elsewhere (portable zip, per-user folder): <program folder>\\freac.xml.
  - Linux: $XDG_CONFIG_HOME, else the account's home folder + /.config; then "freac/" when that folder ends in
    "/.config/", ".freac/" otherwise. So ~/.config/freac/freac.xml normally. A real run of the 1.1.7 AppImage from
    a read-only folder created ~/.config/freac/ (and ~/.cache/freac/) in the account's home folder, as read here.
    Catalogue of a system install: <prefix>/share/freac/lang/freac_co.xml
    (https://github.com/enzo1982/freac/blob/v1.1.7/Makefile#L170-L178).
Checked in the release files: freac-1.1.7-windows-x64.zip has freac.exe and lang/freac_co.xml (1104 entries, as
many as the English template lang/freac.xml); the AppImage and the macOS dmg have it too.

Not handled: the Flatpak (org.freac.freac: by the rule above its file would be
~/.var/app/org.freac.freac/config/.freac/freac.xml, not checked), AppImages (Corsu cannot look inside one), macOS
(whether the settings go next to the program depends on whether the .app folder can be written; not checked), and
portable copies outside the program folders, which Corsu does not search for.
fre:ac writes its settings back when it quits: Corsu waits until it is closed.
"""
import os
from pathlib import Path
import re

import corsu
import apps
from apps import settings

SHARE = Path('/usr/share')
APPLICATIONS = (Path('/Applications'),)
KEY = (('configuration', 'name', 'default'), ('section', 'name', 'Settings'), ('value', 'name', 'Language'))
VALUE = 'freac_co.xml'
ENTRY = re.compile(r'<entry\b[^>]*>([^<]*\S[^<]*)</entry>')


def entries(path):
    try:
        return len(ENTRY.findall(Path(path).read_text(encoding='utf-8')))
    except (OSError, ValueError):
        return 0


def coverage(folder):
    """'N/M': translated entries of freac_co.xml against the English template freac.xml next to it."""
    have, total = entries(folder / 'freac_co.xml'), entries(folder / 'freac.xml')
    return f'{have}/{total}' if total else (f'{have}' if have else None)


def linux_settings():
    xdg = os.environ.get('XDG_CONFIG_HOME')
    folder = (xdg.rstrip('/') + '/') if xdg else str(corsu.HOME / '.config') + '/'
    return Path(folder + ('freac' if folder.endswith('/.config/') else '.freac')) / 'freac.xml'


def under_program_files(folder):
    roots = [os.environ.get(name) for name in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432')]
    text = str(folder).replace('/', '\\').lower().rstrip('\\') + '\\'
    return any(root and text.startswith(root.replace('/', '\\').lower().rstrip('\\') + '\\') for root in roots)


class Freac(apps.App):
    id, name = 'freac', 'fre:ac'
    description = {'co': ('fre:ac', "L'interfaccia di fre:ac in corsu (Patriccollu)."),
                   'fr': ('fre:ac', "L'interface de fre:ac en corse (Patriccollu)."),
                   'en': ('fre:ac', "fre:ac's interface in Corsican (Patriccollu).")}
    processes = ('freac', 'freac.exe')
    validation = {'simulated': True, 'real_app': [], 'visual': False, 'linguistic_review': False}
    FLATPAK = 'org.freac.freac'

    def windows_settings(self, folder):
        from apps import programs
        if not under_program_files(folder):
            beside = folder / 'freac.xml'
            if beside.exists() or programs.writable(beside):
                return beside
        return programs.appdata() / 'freac/freac.xml'

    def installation(self, kind, location, lang, target):
        from apps import programs
        catalog = lang / VALUE
        reason = None
        if not catalog.exists():
            reason = corsu.t(f'its Corsican file is missing ({catalog})', f'son fichier corse manque ({catalog})')
        elif not target.exists():
            reason = corsu.t('start fre:ac once first (no freac.xml yet)',
                             'lancez fre:ac une fois d\'abord (pas encore de freac.xml)')
        elif programs.running(*self.processes):
            reason = programs.close_first(self.name)
        item = apps.Installation(self, kind, location, None, catalog if catalog.exists() else None,
                                 coverage(lang) if catalog.exists() else None, reason)
        item.target = target
        return item

    def find(self):
        if corsu.PLATFORM == 'windows':
            from apps import programs
            found = []
            for base in programs.program_dirs():
                try:
                    folders = sorted(path for path in base.iterdir() if (path / 'freac.exe').is_file())
                except OSError:
                    continue
                for folder in folders:
                    found.append(self.installation(corsu.t('installed', 'installé'), folder / 'freac.exe',
                                                   folder / 'lang', self.windows_settings(folder)))
            return found
        if corsu.PLATFORM == 'macos':
            bundles = [folder / 'freac.app' for folder in dict.fromkeys((*APPLICATIONS, corsu.HOME / 'Applications'))]
            return [apps.Installation(self, 'freac.app', bundle, reason=corsu.t(
                'fre:ac on macOS: where it keeps its settings is not verified yet; nothing changed',
                'fre:ac sur macOS : l\'emplacement de ses réglages n\'est pas encore vérifié ; rien n\'est changé'))
                for bundle in bundles if bundle.exists()]
        found = []
        executable = apps.which('freac')
        if executable and not executable.startswith('/snap/'):
            lang = Path(executable).resolve().parent.parent / 'share/freac/lang'
            if not lang.exists():
                lang = SHARE / 'freac/lang'
            found.append(self.installation(corsu.t('system package', 'paquet du système'), executable, lang,
                                           linux_settings()))
        base = apps.flatpak_installed(self.FLATPAK)
        if base:
            found.append(apps.Installation(self, 'Flatpak', base / 'app' / self.FLATPAK, reason=corsu.t(
                'fre:ac Flatpak: where it keeps its settings is not verified yet; nothing changed',
                'Flatpak de fre:ac : l\'emplacement de ses réglages n\'est pas encore vérifié ; rien n\'est changé')))
        return found

    def enable(self, installer, installation):
        text, _, _ = settings.read_body(installation.target)
        get = settings.FILE_KINDS['xml-path'][0]
        # Another configuration than "default" with its own language would hide Corsu's value.
        for name in re.findall(r'<configuration\s[^>]*?name\s*=\s*"([^"]*)"', text):
            try:
                own = name != 'default' and get(text, [['configuration', 'name', name], *[list(step) for step in KEY[1:]]])
            except Exception as error:  # a malformed file: never rewritten
                raise ValueError(f'{installation.target}: {error}') from None
            if own:
                return corsu.t(f'the fre:ac configuration "{name}" has its own language; left alone',
                               f'la configuration fre:ac « {name} » a sa propre langue ; laissée telle quelle')
        settings.set_file_value(installer, self.id, installation.target, 'xml-path', [list(step) for step in KEY], VALUE)
        return None


PROGRAMS = (Freac,)
