"""Programs that ship their Corsican translation and have a language setting of their own, all by Patriccollu di
Santa Maria è Sichè. Corsu checks that the Corsican file is in the installed program, then sets that one setting.
Sources for every path and value: docs/apps-research.md.

Not done here: portable installs that keep their settings next to the program (Notepad++ with doLocalConf.xml is
handled; others are left alone), Flatpak/Snap variants other than VLC's, and Mp3tag / Paint.NET (proprietary, setting
undocumented).
"""
import os
from pathlib import Path

import corsu
import apps
from apps import settings


def program_dirs():
    """Folders where Windows programs are installed, for everyone or for this user."""
    found = []
    for variable in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432'):
        if os.environ.get(variable):
            found.append(Path(os.environ[variable]))
    local = Path(os.environ.get('LOCALAPPDATA', corsu.HOME / 'AppData/Local'))
    found += [local / 'Programs', local]
    return list(dict.fromkeys(found))


def appdata():
    return Path(os.environ.get('APPDATA', corsu.HOME / 'AppData/Roaming'))


def config_home():
    return Path(os.environ.get('XDG_CONFIG_HOME', corsu.HOME / '.config'))


def running(*names):
    """True when a process with one of these executable names runs (None from the system counts as not known)."""
    processes = corsu.running_executables() or set()
    wanted = {name.lower() for name in names}
    return any(Path(process.replace('\\', '/')).name.lower() in wanted for process in processes)


def writable(path):
    """Whether a file could be created at path: the nearest existing folder above it must be writable."""
    folder = Path(path).parent
    while not folder.exists() and folder != folder.parent:
        folder = folder.parent
    return os.access(folder, os.W_OK)


def close_first(name):
    return corsu.t(f'{name} is open: close it, then run Corsu again (it rewrites its settings when it quits)',
                   f'{name} est ouvert : fermez-le, puis relancez Corsu (il réécrit ses réglages en quittant)')


class SettingApp(apps.App):
    """A program found by its executable and its Corsican file, switched by one value in its settings."""
    executables = ()     # (platform, path relative to a program folder or absolute)
    corsican = ''        # the Corsican file, relative to the program's folder (or absolute on Linux)
    processes = ()       # executable names to check before writing, when the program rewrites its settings
    coverage_note = None

    def installs(self):
        """(executable path, program folder) found on this platform."""
        found = []
        for platform, path in self.executables:
            if platform != corsu.PLATFORM:
                continue
            candidates = [Path(path)] if Path(path).is_absolute() else [base / path for base in program_dirs()]
            for candidate in candidates:
                if candidate.exists():
                    found.append((candidate, candidate.parent))
        return list(dict.fromkeys(found))

    def corsican_file(self, folder):
        path = Path(self.corsican)
        return path if path.is_absolute() else folder / path

    def find(self):
        result = []
        for executable, folder in self.installs():
            catalog = self.corsican_file(folder)
            reason = action = None
            if not catalog.exists():
                reason = corsu.t(f'its Corsican file is missing ({catalog})', f'son fichier corse manque ({catalog})')
                action = corsu.t(f'Reinstall {self.name} with its translations, then run Corsu again',
                                 f'Réinstallez {self.name} avec ses traductions, puis relancez Corsu')
            else:
                reason = self.check(folder)
                if reason:
                    action = self.check_action(folder)
            if reason is None and self.processes and running(*self.processes):
                reason = close_first(self.name)
                action = corsu.t(f'Close {self.name}, then switch it on in Corsu', f'Fermez {self.name}, puis activez-le dans Corsu')
            result.append(apps.Installation(self, corsu.t('installed', 'installé'), executable, None,
                                            catalog if catalog.exists() else None, self.coverage_note, reason, action))
        return result

    def check_action(self, folder):
        """What to do about check()'s reason: start the program once when its settings file is not created yet."""
        settings_file = getattr(self, 'settings_file', None)
        if settings_file and not settings_file().exists():
            return corsu.t(f'Start {self.name} once, close it, then run Corsu again',
                           f'Lancez {self.name} une fois, fermez-le, puis relancez Corsu')
        return None

    def check(self, folder):
        """Why this installation cannot be switched (settings file missing…), or None."""
        return None


class SevenZip(SettingApp):
    id, name = '7zip', '7-Zip'
    description = {'co': ('7-Zip', "A finestra è u listinu di 7-Zip in corsu (Patriccollu)."),
                   'fr': ('7-Zip', "La fenêtre et le menu de 7-Zip en corse (Patriccollu)."),
                   'en': ('7-Zip', "7-Zip's window and menu in Corsican (Patriccollu).")}
    validation = {'simulated': True, 'real_app': ['windows'], 'visual': False, 'linguistic_review': False}
    restart_processes = ('7zFM.exe',)
    executables = (('windows', '7-Zip/7zFM.exe'),)
    corsican = 'Lang/co.txt'

    def enable(self, installer, installation):
        settings.set_registry(installer, self.id, r'Software\7-Zip', 'Lang', 'co', 1)


class NotepadPlusPlus(SettingApp):
    """Notepad++'s installer copies only the language picked during setup, so localization/corsican.xml is often not
    there. Then Corsu fetches the official file of the installed version from the Notepad++ repository and checks it
    against the repository's own blob hash before using it."""
    id, name = 'notepadpp', 'Notepad++'
    description = {'co': ('Notepad++', "L'interfaccia di Notepad++ in corsu (Patriccollu)."),
                   'fr': ('Notepad++', "L'interface de Notepad++ en corse (Patriccollu)."),
                   'en': ('Notepad++', "Notepad++'s interface in Corsican (Patriccollu).")}
    validation = {'simulated': True, 'real_app': ['windows'], 'visual': False, 'linguistic_review': False}
    restart_processes = ('notepad++.exe',)
    executables = (('windows', 'Notepad++/notepad++.exe'),)
    corsican = 'localization/corsican.xml'
    REPOSITORY = 'notepad-plus-plus/notepad-plus-plus'
    PATH = 'PowerEditor/installer/nativeLang/corsican.xml'

    def target(self, folder):
        # Portable mode (doLocalConf.xml next to the program) keeps its settings in the program's folder.
        return folder / 'nativeLang.xml' if (folder / 'doLocalConf.xml').exists() else appdata() / 'Notepad++/nativeLang.xml'

    def find(self):
        result = []
        for executable, folder in self.installs():
            catalog = self.corsican_file(folder)
            target = self.target(folder)
            reason = None
            if not writable(target):
                reason = corsu.t(f'{target.parent} cannot be written', f'{target.parent} n\'est pas modifiable')
            note = None if catalog.exists() else corsu.t('official Corsican file fetched from Notepad++',
                                                         'fichier corse officiel téléchargé depuis Notepad++')
            result.append(apps.Installation(self, corsu.t('installed', 'installé'), executable, None,
                                            catalog if catalog.exists() else None, note, reason))
        return result

    def version(self, executable):
        import subprocess
        try:
            output = subprocess.run(['powershell', '-NoProfile', '-Command',
                                     f"(Get-Item -LiteralPath '{executable}').VersionInfo.ProductVersion"],
                                    **corsu.hidden(capture_output=True, text=True, timeout=30)).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
        return output.split()[0] if output else None

    def official_file(self, executable):
        """corsican.xml of the installed version (tag v<version>), checked against the git blob hash GitHub gives."""
        import hashlib
        import json as _json
        import urllib.request
        version = self.version(executable)
        if not version:
            raise ValueError(corsu.t('version of Notepad++ unknown', 'version de Notepad++ inconnue'))
        tag = 'v' + '.'.join(part for part in version.replace(',', '.').split('.') if part)
        while tag.endswith('.0') and tag.count('.') > 1:
            tag = tag[:-2]
        api = f'https://api.github.com/repos/{self.REPOSITORY}/contents/{self.PATH}?ref={tag}'
        headers = {'User-Agent': 'Corsu', 'Accept': 'application/vnd.github+json'}
        if os.environ.get('GITHUB_TOKEN'):
            # CI runners share an address and GitHub's limit of 60 anonymous API requests an hour.
            headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
        request = urllib.request.Request(api, headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            meta = _json.loads(response.read())
        with urllib.request.urlopen(meta['download_url'], timeout=60) as response:
            data = response.read()
        blob = hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
        if blob != meta['sha']:
            raise ValueError(corsu.t('downloaded file does not match the repository', 'fichier téléchargé non conforme au dépôt'))
        return data, tag

    def enable(self, installer, installation):
        # What Notepad++'s own language menu does: copy the language file to nativeLang.xml. A nativeLang.xml of
        # another language is kept as the backup and comes back when Corsu is switched off.
        folder = installation.location.parent
        if installation.catalog:
            data = installation.catalog.read_bytes()
        else:
            try:
                data, tag = self.official_file(installation.location)
            except (OSError, ValueError, KeyError) as error:
                raise RuntimeError(corsu.t(f'could not fetch the Corsican file ({error}); check the connection and retry',
                                           f'téléchargement du fichier corse impossible ({error}) ; vérifiez la connexion '
                                           'et réessayez')) from None
            print(corsu.t(f'Notepad++: Corsican file of {tag} fetched from github.com/{self.REPOSITORY}',
                          f'Notepad++ : fichier corse de {tag} téléchargé depuis github.com/{self.REPOSITORY}'))
        target = self.target(folder)
        record = installer.state['files'].get(str(target))
        if record and target.exists() and corsu.digest(target.read_bytes()) != record['installed_sha256']:
            # Notepad++'s own language menu rewrites nativeLang.xml: that choice is the person's.
            return corsu.t('language changed in Notepad++ since; left alone', 'langue changée dans Notepad++ depuis ; laissé tel quel')
        installer.write(target, data, toggle=True)
        installer.state['files'][str(target)]['component'] = self.id


class WinMerge(SettingApp):
    id, name = 'winmerge', 'WinMerge'
    description = {'co': ('WinMerge', "L'interfaccia di WinMerge in corsu (Patriccollu)."),
                   'fr': ('WinMerge', "L'interface de WinMerge en corse (Patriccollu)."),
                   'en': ('WinMerge', "WinMerge's interface in Corsican (Patriccollu).")}
    executables = (('windows', 'WinMerge/WinMergeU.exe'),)
    corsican = 'Languages/Corsican.po'
    processes = ('WinMergeU.exe',)

    def check(self, folder):
        if (folder / 'winmerge.ini').exists():
            return corsu.t('portable WinMerge (winmerge.ini): left alone', 'WinMerge portable (winmerge.ini) : laissé tel quel')
        return None

    def enable(self, installer, installation):
        # 1155 = 0x0483, the Windows language id of Corsican.
        settings.set_registry(installer, self.id, r'Software\Thingamahoochie\WinMerge\Locale', 'LanguageId', 1155, 4)


class SumatraPDF(SettingApp):
    id, name = 'sumatrapdf', 'SumatraPDF'
    description = {'co': ('SumatraPDF', "L'interfaccia di SumatraPDF in corsu (Patriccollu)."),
                   'fr': ('SumatraPDF', "L'interface de SumatraPDF en corse (Patriccollu)."),
                   'en': ('SumatraPDF', "SumatraPDF's interface in Corsican (Patriccollu).")}
    executables = (('windows', 'SumatraPDF/SumatraPDF.exe'),)
    corsican = 'SumatraPDF.exe'  # its translations are built into the program
    processes = ('SumatraPDF.exe',)

    def settings_file(self):
        return Path(os.environ.get('LOCALAPPDATA', corsu.HOME / 'AppData/Local')) / 'SumatraPDF/SumatraPDF-settings.txt'

    def check(self, folder):
        if not self.settings_file().exists():
            return corsu.t('start SumatraPDF once first (no settings file yet)',
                           'lancez SumatraPDF une fois d\'abord (pas encore de fichier de réglages)')
        return None

    def enable(self, installer, installation):
        settings.set_file_value(installer, self.id, self.settings_file(), 'line', 'UiLanguage', 'co')


class FileZilla(SettingApp):
    id, name = 'filezilla', 'FileZilla'
    description = {'co': ('FileZilla', "L'interfaccia di FileZilla in corsu (Patriccollu)."),
                   'fr': ('FileZilla', "L'interface de FileZilla en corse (Patriccollu)."),
                   'en': ('FileZilla', "FileZilla's interface in Corsican (Patriccollu).")}
    executables = (('windows', 'FileZilla FTP Client/filezilla.exe'), ('linux', '/usr/bin/filezilla'))
    processes = ('filezilla.exe', 'filezilla')
    KEY = ('Setting', 'name', 'Language Code', 'Settings')

    def corsican_file(self, folder):
        if corsu.PLATFORM == 'linux':
            return Path('/usr/share/locale/co/LC_MESSAGES/filezilla.mo')
        return folder / 'locales/co/filezilla.mo'

    def settings_file(self):
        return appdata() / 'FileZilla/filezilla.xml' if corsu.PLATFORM == 'windows' else config_home() / 'filezilla/filezilla.xml'

    def check(self, folder):
        if not self.settings_file().exists():
            return corsu.t('start FileZilla once first (no filezilla.xml yet)',
                           'lancez FileZilla une fois d\'abord (pas encore de filezilla.xml)')
        return None

    def enable(self, installer, installation):
        settings.set_file_value(installer, self.id, self.settings_file(), 'xml', list(self.KEY), 'co')


class HandBrake(SettingApp):
    id, name = 'handbrake', 'HandBrake'
    description = {'co': ('HandBrake', "L'interfaccia di HandBrake in corsu (Patriccollu)."),
                   'fr': ('HandBrake', "L'interface de HandBrake en corse (Patriccollu)."),
                   'en': ('HandBrake', "HandBrake's interface in Corsican (Patriccollu).")}
    executables = (('windows', 'HandBrake/HandBrake.exe'), ('linux', '/usr/bin/ghb'))
    processes = ('HandBrake.exe', 'ghb')

    def corsican_file(self, folder):
        if corsu.PLATFORM == 'linux':
            return Path('/usr/share/locale/co/LC_MESSAGES/ghb.mo')
        # HandBrake.exe is a single file with its translations built in (1.11.2).
        return folder / 'HandBrake.exe'

    def settings_file(self):
        return appdata() / 'HandBrake/settings.json' if corsu.PLATFORM == 'windows' else config_home() / 'ghb/preferences.json'

    def check(self, folder):
        if corsu.PLATFORM == 'windows' and (folder / 'portable.ini').exists():
            return corsu.t('portable HandBrake: left alone', 'HandBrake portable : laissé tel quel')
        if not self.settings_file().exists():
            return corsu.t('start HandBrake once first (no settings file yet)',
                           'lancez HandBrake une fois d\'abord (pas encore de fichier de réglages)')
        return None

    def corsican_present(self, folder):
        return self.corsican_file(folder).exists()

    def enable(self, installer, installation):
        key = 'UiLanguage' if corsu.PLATFORM == 'windows' else 'Preferences/UiLanguage'
        settings.set_file_value(installer, self.id, self.settings_file(), 'json', key, 'co')


class VeraCrypt(SettingApp):
    id, name = 'veracrypt', 'VeraCrypt'
    description = {'co': ('VeraCrypt', "L'interfaccia di VeraCrypt in corsu (Patriccollu)."),
                   'fr': ('VeraCrypt', "L'interface de VeraCrypt en corse (Patriccollu)."),
                   'en': ('VeraCrypt', "VeraCrypt's interface in Corsican (Patriccollu).")}
    executables = (('windows', 'VeraCrypt/VeraCrypt.exe'), ('linux', '/usr/bin/veracrypt'))
    processes = ('VeraCrypt.exe', 'veracrypt')
    KEY = ('config', 'key', 'Language', 'configuration')

    def corsican_file(self, folder):
        if corsu.PLATFORM == 'linux':
            return Path('/usr/share/veracrypt/languages/Language.co.xml')
        return folder / 'Languages/Language.co.xml'

    def settings_file(self):
        return appdata() / 'VeraCrypt/Configuration.xml' if corsu.PLATFORM == 'windows' else config_home() / 'VeraCrypt/Configuration.xml'

    def check(self, folder):
        if not self.settings_file().exists():
            return corsu.t('start VeraCrypt once first (no Configuration.xml yet)',
                           'lancez VeraCrypt une fois d\'abord (pas encore de Configuration.xml)')
        return None

    def enable(self, installer, installation):
        settings.set_file_value(installer, self.id, self.settings_file(), 'xml', list(self.KEY), 'co')


PROGRAMS = (SevenZip, NotepadPlusPlus, WinMerge, SumatraPDF, FileZilla, HandBrake, VeraCrypt)
