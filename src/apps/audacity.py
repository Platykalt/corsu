"""Audacity and Tenacity, whose Corsican translations are Patriccollu di Santa Maria è Sichè's. Corsu checks that the
installed program has its Corsican catalogue, then sets the program's own language setting, the one its Preferences
→ Interface → Language writes. Each case below was read in the program's source at the tag named, and the paths
checked in the official release files; "Run" marks the cases also started for real (Linux AppImages, with a
throwaway home folder, the setting written by Corsu's own code, Corsican seen on screen).

Audacity 3.x (wxWidgets; distro packages, Flathub org.audacityteam.Audacity, Windows and macOS 3.x):
  `[Locale] Language=co` in audacity.cfg, read at start-up as /Locale/Language
  (https://github.com/audacity/audacity/blob/Audacity-3.7.9/src/AudacityApp.cpp#L208).
  The file is FileNames::ConfigDir()/audacity.cfg
  (https://github.com/audacity/audacity/blob/Audacity-3.7.9/libraries/lib-files/FileNames.cpp#L383-L386):
  - Linux: ~/.audacity-data/ whenever that folder exists, else $XDG_CONFIG_HOME/audacity/ (when set and not empty),
    else ~/.config/audacity/ (FileNames.cpp#L258-L278; AUDACITY_NAME is "audacity" on Linux,
    https://github.com/audacity/audacity/blob/Audacity-3.7.9/CMakeLists.txt#L588-L593). Run with 3.7.7: wrote
    ~/.config/audacity/audacity.cfg, and Language=co gave a Corsican window and kept the value.
  - Flatpak: the same rule. The legacy folder is the real ~/.audacity-data (the Flatpak has --filesystem=host),
    otherwise XDG_CONFIG_HOME is the Flatpak's ~/.var/app/org.audacityteam.Audacity/config
    (https://github.com/flathub/org.audacityteam.Audacity/blob/master/org.audacityteam.Audacity.yaml#L12-L24).
  - Windows: %APPDATA%\\audacity\\ and macOS: ~/Library/Application Support/audacity/, the wx user data folder with
    "Audacity" lower-cased (FileNames.cpp#L214-L223, #L305-L315). A "Portable Settings" folder next to the program
    takes over (FileNames.cpp#L287-L303): left alone.
  - Catalogue: <prefix>/share/locale/co/LC_MESSAGES/audacity.mo on Linux; Languages\\co\\audacity.mo next to
    Audacity.exe (audacity-win-3.7.7-64bit.zip); Audacity.app/Contents/Resources/co.lproj/audacity.mo
    (audacity-macOS-3.7.7-arm64.dmg). Search rule: libraries/lib-strings/Languages.cpp#L66-L73.
  - The Windows installer leaves a FirstTime.ini whose language replaces the setting at the next start
    (AudacityApp.cpp#L212-L265): Corsu waits until Audacity has been started once.

Audacity 4.x (MuseScore's "muse" framework; Windows .msi/.7z, macOS dmg, Linux AppImage):
  The setting is Settings::Key("languages", "language"), but muse writes only the second part to QSettings
  (https://github.com/musescore/muse_framework/blob/3ba3cd6886433b41759d2d7adef8aef9bbbd546b/framework/global/settings.cpp#L233-L240,
  "TODO: implement writing/reading first part of key"; languagesconfiguration.cpp#L36), so it is `language=co` in
  the [General] group. QSettings: organisation "Audacity", application "Audacity4", INI format except on macOS
  (https://github.com/audacity/audacity/blob/Audacity-4.0.1/src/app/main.cpp#L93-L114, settings.cpp#L49-L61; the
  `muse` submodule of Audacity-4.0.1 is that commit). Run with the 4.0.1 AppImage: ~/.config/Audacity/Audacity4.ini
  with [General] language=co loads locale/audacity_co.qm and shows Corsican; the value is kept.
  - Windows: %APPDATA%\\Audacity\\Audacity4.ini (Qt's documented INI location; not run on Windows). Program:
    <Program Files>\\Audacity 4\\bin\\Audacity4.exe (CPACK_PACKAGE_INSTALL_DIRECTORY = "Audacity 4",
    buildscripts/packaging/Windows/SetupWindowsPackaging.cmake#L42, version.cmake#L21), catalogue
    ..\\locale\\audacity_co.qm (audacity-win-4.0.1-x86_64.7z).
  - macOS: preferences domain org.audacityteam.Audacity4, key "language" (Qt's native format with the organisation
    domain audacityteam.org; not run on macOS). Program: "Audacity 4.app", catalogue
    Contents/Resources/locale/audacity_co.qm (audacity-macOS-4.0.1-arm64.dmg).
  - Linux: a system install puts its files in <prefix>/share/audacity-4.<minor>/ (SetupConfigure.cmake#L96).
    AppImages can be anywhere and Corsu cannot look inside one for the catalogue: not handled.
  3.x and 4.x are told apart by their files (Audacity.exe and Languages\\ versus bin\\Audacity4.exe and locale\\;
  Audacity.app versus "Audacity 4.app"; share/locale versus share/audacity-4.x), and they keep separate settings.

Tenacity 1.3.x (Audacity 3 code): `[Locale] Language=co` in tenacity.cfg
(https://codeberg.org/tenacityteam/tenacity/src/tag/v1.3.5/src/TenacityApp.cpp#L150, #L1013).
  - Linux: $XDG_CONFIG_HOME/tenacity/, else ~/.config/tenacity/
    (https://codeberg.org/tenacityteam/tenacity/src/tag/v1.3.5/libraries/lib-files/FileNames.cpp#L253-L267).
    Run with the 1.3.5 AppImage: wrote ~/.config/tenacity/tenacity.cfg; Language=co gave a Corsican window.
  - Flatpak org.tenacityaudio.Tenacity: XDG_CONFIG_HOME is ~/.var/app/org.tenacityaudio.Tenacity/config.
  - Windows %APPDATA%\\tenacity\\ and macOS ~/Library/Application Support/tenacity/: the wx user data folder of the
    app name "Tenacity" (libraries/lib-utility/ModuleConstants.cpp#L14-L20), lower-cased (FileNames.cpp#L216-L225).
  - Catalogue: share/locale/co/LC_MESSAGES/tenacity.mo (Linux, AppImage checked); {app}\\Languages\\co\\tenacity.mo
    with {app} = {autopf}\\Tenacity and tenacity.exe (locale/CMakeLists.txt#L30-L51,
    win/Inno_Setup_Wizard/tenacity.iss.in#L41, #L97; the Inno Setup installer itself was not unpacked);
    Tenacity.app/Contents/Resources/co.lproj/tenacity.mo (tenacity-macos-1.3.5 dmg).

All of these programs write their settings back when they quit: Corsu waits until they are closed.
"""
import glob
import os
from pathlib import Path

import corsu
import apps
from apps import settings

LOCALE = Path('/usr/share/locale')
SHARE = Path('/usr/share')
APPLICATIONS = (Path('/Applications'),)
# Linux: the official AppImages (Audacity 3.7.7 and 4.0.1, Tenacity 1.3.5) were started for real with a throwaway
# home folder after Corsu's own code had written the setting where it computes it; they showed Corsican, and Corsu's
# revert then gave back the original after the programs had rewritten their files. Windows and macOS: fixtures only.
CHECKED = {'simulated': True, 'real_app': ['linux'], 'visual': True, 'linguistic_review': False}


def config_home():
    """$XDG_CONFIG_HOME when set and not empty, else ~/.config (what both programs do)."""
    return Path(os.environ.get('XDG_CONFIG_HOME') or corsu.HOME / '.config')


def application_bundles(name):
    folders = dict.fromkeys((*APPLICATIONS, corsu.HOME / 'Applications'))
    return [folder / name for folder in folders if (folder / name).exists()]


class WxAudioApp(apps.App):
    """A program on Audacity 3's code: [Locale] Language in <name>.cfg."""
    domain = ''          # catalogue and settings file name: audacity / tenacity
    executable = ''      # Windows: folder/executable under a program folder
    bundle = ''          # macOS: the .app name
    flatpak = ''
    processes = ()

    def start_once(self):
        return corsu.t(f'start {self.name} once first (no settings file yet)',
                       f'lancez {self.name} une fois d\'abord (pas encore de fichier de réglages)')

    def linux_settings(self):
        return config_home() / self.domain / f'{self.domain}.cfg'

    def flatpak_settings(self):
        return corsu.HOME / '.var/app' / self.flatpak / 'config' / self.domain / f'{self.domain}.cfg'

    def windows_settings(self):
        from apps import programs
        return programs.appdata() / self.domain / f'{self.domain}.cfg'

    def macos_settings(self):
        return corsu.HOME / 'Library/Application Support' / self.domain / f'{self.domain}.cfg'

    def installation(self, kind, location, version, catalog, coverage, setting, extra=None):
        """One installation. setting: ('ini', file, section, key) or ('defaults', domain, None, key)."""
        reason = action = None
        if not catalog or not Path(catalog).exists():
            reason = corsu.t(f'its Corsican catalogue is missing ({catalog})' if catalog else 'its Corsican catalogue is missing',
                             f'son catalogue corse manque ({catalog})' if catalog else 'son catalogue corse manque')
            action = corsu.t(f'Reinstall {self.name} with its translations, then run Corsu again',
                             f'Réinstallez {self.name} avec ses traductions, puis relancez Corsu')
        elif extra:
            reason = extra
        elif setting[0] == 'ini' and not Path(setting[1]).exists():
            reason = self.start_once()
            action = corsu.t(f'Start {self.name} once, close it, then run Corsu again',
                             f'Lancez {self.name} une fois, fermez-le, puis relancez Corsu')
        elif self.processes:
            from apps import programs
            if programs.running(*self.processes):
                reason = programs.close_first(self.name)
                action = corsu.t(f'Close {self.name}, then switch it on in Corsu', f'Fermez {self.name}, puis activez-le dans Corsu')
        present = bool(catalog) and Path(catalog).exists()
        item = apps.Installation(self, kind, location, version, catalog if present else None,
                                 coverage if present else None, reason, action)
        item.setting = setting
        return item

    def find(self):
        if corsu.PLATFORM == 'windows':
            return self.find_windows()
        if corsu.PLATFORM == 'macos':
            return self.find_macos()
        return self.find_linux()

    def find_linux(self):
        found = []
        executable = apps.which(self.domain)
        if executable and not executable.startswith('/snap/'):
            found += self.linux_system(executable)
        base = apps.flatpak_installed(self.flatpak) if self.flatpak else None
        if base:
            found.append(self.linux_flatpak(base))
        return found

    def linux_system(self, executable):
        catalog = LOCALE / 'co/LC_MESSAGES' / f'{self.domain}.mo'
        return [self.installation(corsu.t('system package', 'paquet du système'), executable, self.major, catalog,
                                  apps.coverage_against(catalog, LOCALE / 'fr/LC_MESSAGES' / f'{self.domain}.mo'),
                                  ('ini', self.linux_settings(), 'Locale', 'Language'))]

    def linux_flatpak(self, base):
        catalog = apps.flatpak_catalog(base, self.flatpak, self.domain)
        item = self.installation('Flatpak', base / 'app' / self.flatpak, self.major, catalog,
                                 apps.coverage_against(catalog, None) if catalog else None,
                                 ('ini', self.flatpak_settings(), 'Locale', 'Language'))
        if catalog is None:
            item.reason = corsu.t(
                'the Flatpak\'s languages do not include Corsican (flatpak config --set extra-languages co, then update)',
                'les langues du Flatpak n\'incluent pas le corse (flatpak config --set extra-languages co, puis mise à jour)')
        return item

    def find_windows(self):
        from apps import programs
        found = []
        for base in programs.program_dirs():
            executable = base / self.executable
            if not executable.exists():
                continue
            folder = executable.parent
            catalog = folder / 'Languages/co' / f'{self.domain}.mo'
            extra = None
            if (folder / 'Portable Settings').is_dir():
                extra = corsu.t(f'portable {self.name} ("Portable Settings" folder): left alone',
                                f'{self.name} portable (dossier « Portable Settings ») : laissé tel quel')
            elif (folder / 'FirstTime.ini').exists():
                extra = corsu.t(f'{self.name} was just installed or updated: start it once first',
                                f'{self.name} vient d\'être installé ou mis à jour : lancez-le une fois d\'abord')
            found.append(self.installation(corsu.t('installed', 'installé'), executable, self.major, catalog,
                                           apps.coverage_against(catalog, folder / 'Languages/fr' / f'{self.domain}.mo'),
                                           ('ini', self.windows_settings(), 'Locale', 'Language'), extra))
        return found

    def find_macos(self):
        found = []
        for bundle in application_bundles(self.bundle):
            resources = bundle / 'Contents/Resources'
            catalog = resources / 'co.lproj' / f'{self.domain}.mo'
            extra = None
            if (bundle / 'Contents/Portable Settings').is_dir():
                extra = corsu.t(f'portable {self.name}: left alone', f'{self.name} portable : laissé tel quel')
            found.append(self.installation(self.bundle, bundle, self.major, catalog,
                                           apps.coverage_against(catalog, resources / 'fr.lproj' / f'{self.domain}.mo'),
                                           ('ini', self.macos_settings(), 'Locale', 'Language'), extra))
        return found

    def enable(self, installer, installation):
        kind, target, section, key = installation.setting
        if kind == 'defaults':
            settings.set_defaults(installer, self.id, target, key, 'co')
        else:
            settings.set_ini(installer, self.id, target, section, key, 'co')
        return None


class Audacity(WxAudioApp):
    id, name = 'audacity', 'Audacity'
    description = {'co': ('Audacity', "L'interfaccia d'Audacity in corsu (Patriccollu)."),
                   'fr': ('Audacity', "L'interface d'Audacity en corse (Patriccollu)."),
                   'en': ('Audacity', "Audacity's interface in Corsican (Patriccollu).")}
    domain, executable, bundle, flatpak, major = 'audacity', 'Audacity/Audacity.exe', 'Audacity.app', \
        'org.audacityteam.Audacity', '3.x'
    processes = ('audacity', 'Audacity.exe', 'Audacity4.exe', 'audacity4portable')
    validation = dict(CHECKED)
    # Audacity 4 keeps its settings with Qt, under these names (see the module docstring).
    QT_ORGANISATION, QT_APPLICATION, MAC_DOMAIN = 'Audacity', 'Audacity4', 'org.audacityteam.Audacity4'
    WINDOWS_4 = 'Audacity 4/bin/Audacity4.exe'
    BUNDLE_4 = 'Audacity 4.app'

    def linux_settings(self):
        # Audacity 3 keeps using the folder of Audacity 2 when it is there.
        legacy = corsu.HOME / '.audacity-data'
        return legacy / 'audacity.cfg' if legacy.is_dir() else super().linux_settings()

    def flatpak_settings(self):
        legacy = corsu.HOME / '.audacity-data'
        return legacy / 'audacity.cfg' if legacy.is_dir() else super().flatpak_settings()

    def qt_ini(self, root):
        return root / self.QT_ORGANISATION / f'{self.QT_APPLICATION}.ini'

    def linux_system(self, executable):
        prefix = SHARE
        fours = sorted(glob.glob(str(prefix / 'audacity*-4.*')))
        if not fours:
            return super().linux_system(executable)
        catalog = Path(fours[-1]) / 'locale/audacity_co.qm'
        return [self.installation(corsu.t('system package', 'paquet du système'), executable, '4.x', catalog, None,
                                  ('ini', self.qt_ini(config_home()), 'General', 'language'))]

    def linux_flatpak(self, base):
        if glob.glob(str(base / 'app' / self.flatpak / '*/*/active/files/share/audacity*-4.*')):
            return apps.Installation(self, 'Flatpak', base / 'app' / self.flatpak, '4.x', reason=corsu.t(
                'Audacity 4 Flatpak: its settings location is not verified yet; nothing changed',
                'Flatpak d\'Audacity 4 : l\'emplacement de ses réglages n\'est pas encore vérifié ; rien n\'est changé'))
        return super().linux_flatpak(base)

    def find_windows(self):
        from apps import programs
        found = super().find_windows()
        for base in programs.program_dirs():
            executable = base / self.WINDOWS_4
            if executable.exists():
                catalog = executable.parent.parent / 'locale/audacity_co.qm'
                found.append(self.installation(corsu.t('installed', 'installé'), executable, '4.x', catalog, None,
                                               ('ini', self.qt_ini(programs.appdata()), 'General', 'language')))
        return found

    def find_macos(self):
        found = super().find_macos()
        for bundle in application_bundles(self.BUNDLE_4):
            catalog = bundle / 'Contents/Resources/locale/audacity_co.qm'
            plist = corsu.HOME / 'Library/Preferences' / f'{self.MAC_DOMAIN}.plist'
            item = self.installation(self.BUNDLE_4, bundle, '4.x', catalog, None,
                                     ('defaults', self.MAC_DOMAIN, None, 'language'))
            if item.reason is None and not plist.exists():
                item.reason = self.start_once()
            found.append(item)
        return found


class Tenacity(WxAudioApp):
    id, name = 'tenacity', 'Tenacity'
    description = {'co': ('Tenacity', "L'interfaccia di Tenacity in corsu (Patriccollu)."),
                   'fr': ('Tenacity', "L'interface de Tenacity en corse (Patriccollu)."),
                   'en': ('Tenacity', "Tenacity's interface in Corsican (Patriccollu).")}
    domain, executable, bundle, flatpak, major = 'tenacity', 'Tenacity/tenacity.exe', 'Tenacity.app', \
        'org.tenacityaudio.Tenacity', None
    processes = ('tenacity', 'tenacity.exe', 'Tenacity')
    validation = dict(CHECKED)


PROGRAMS = (Audacity, Tenacity)
