"""PDFsam Basic, whose Corsican translation (Messages_co.properties) is Patriccollu di Santa Maria è Sichè's.

The translation is inside pdfsam-i18n-<version>.jar (org/pdfsam/i18n/Messages_co.properties), the same jar on every
platform, since 3.0.0 (Locale "co" and po/co.po added in commit 6d075b1b, Aug 2015; first tag v3.0.0.M2).

The setting is PDFsam's own language preference: Java Preferences node /org/pdfsam/user/conf
(https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-core/src/main/java/org/pdfsam/core/context/ApplicationContext.java#L56),
key "locale", the enum name lower-cased since 5.0.0
(https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-core/src/main/java/org/pdfsam/core/context/StringPersistentProperty.java#L40
and #L64-L66; 4.x used the key "LOCALE"), value a language tag, "co"
(https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-model/src/main/java/org/pdfsam/model/ui/ComboItem.java#L70-L72;
read back with Locale.forLanguageTag and kept only if supported,
https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-i18n/src/main/java/org/pdfsam/i18n/I18nContext.java#L47-L66).
It is read once, at start (https://github.com/torakiki/pdfsam/blob/v6.0.6/pdfsam-gui/src/main/java/org/pdfsam/gui/PdfsamApp.java#L106-L107),
and PDFsam writes it back at every start with the language it shows (its settings page sets its language list,
whose listener saves the value: PreferenceAppearencePane.java#L55-L57, PreferenceComboBox.java#L46-L49). So the node
exists after the first start (seen with 6.0.6: locale="en").

Where Java keeps that node:
  - Linux: ~/.java/.userPrefs/org/pdfsam/user/conf/prefs.xml (FileSystemPreferences; the node names need no escaping).
    A running PDFsam keeps the node in memory and writes it back whole when it syncs or quits, without reading a
    change made by another program (only another Java program touching .userRootModFile makes it reload), so PDFsam
    must be closed, to switch on and to switch off.
  - Windows: HKCU\\Software\\JavaSoft\\Prefs\\org\\pdfsam\\user\\conf, value "locale" (REG_SZ) = "co". Java escapes
    capital letters with "/" in names and values (WindowsPreferences.toWindowsName / toWindowsValueString); "locale"
    and "co" have none. The registry is read and written directly, so an open PDFsam only needs a restart.
  - macOS: not switched by Corsu. Java keeps nodes of three or more levels in the CFPreferences domain of their first
    three names (MacOSXPreferences.cfFileForNode: org.pdfsam.user, ~/Library/Preferences/org.pdfsam.user.plist), as
    one nested dictionary {"/org/pdfsam/user/": {"conf/": {"locale": …}, "news/": …}}
    (MacOSXPreferencesFile.m copyTreeForPath); changing one value inside it means rewriting that whole tree. Corsu
    says where to choose Corsican in PDFsam instead.

Installations: the official .deb (/opt/pdfsam-basic, also the AUR pdfsam-bin), the AUR pdfsam package
(/usr/share/java/pdfsam), a Linux tar.gz reached through `pdfsam`/`pdfsam-basic` in PATH, the Windows MSI
(<Program Files>\\PDFsam Basic\\pdfsam.exe, jars in app\\mods), the macOS app (/Applications/PDFsam Basic.app). A
portable zip unpacked anywhere is not found, but every installation of one account shares the same preference, so
switching one switches them all. PDFsam Basic is neither on Flathub nor in the Snap Store (checked 2026-10-17).
"""
import json
from pathlib import Path
import re

import corsu
import apps
from apps import programs, settings

NODE = 'org/pdfsam/user/conf'
KEY = 'locale'
REGISTRY_KEY = r'Software\JavaSoft\Prefs\org\pdfsam\user\conf'
CATALOG = 'org/pdfsam/i18n/Messages_co.properties'
JAR = re.compile(r'pdfsam-i18n-(\d+(?:\.\d+)*)\b.*\.jar$')
LINUX_FOLDERS = (Path('/opt/pdfsam-basic'), Path('/usr/share/java/pdfsam'))
APPLICATIONS = (Path('/Applications'),)
MAIN_MODULE = b'org.pdfsam.basic'


def prefs_file():
    """Linux: the node's prefs.xml (Java uses the account's home folder, which Corsu's is)."""
    return corsu.HOME / '.java/.userPrefs' / NODE / 'prefs.xml'


def registry_node_exists():
    import winreg
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY).Close()
        return True
    except OSError:
        return False


def linux_running():
    """True when a PDFsam Basic runs (its Java command line names its main module), whatever Java runs it."""
    proc = Path('/proc')
    if not proc.is_dir():
        return False
    for process in proc.iterdir():
        try:
            if MAIN_MODULE in (process / 'cmdline').read_bytes():
                return True
        except OSError:
            continue
    return False


def is_running():
    if corsu.PLATFORM == 'linux':
        return linux_running()
    if corsu.PLATFORM == 'windows':
        return programs.running('pdfsam.exe')
    return False


def version_of(jar):
    match = JAR.search(jar.name)
    return match.group(1) if match else None


def properties_count(data):
    """Entries of a .properties file (logical lines that are neither blank nor comments)."""
    count, continued = 0, False
    for line in data.decode('latin-1').splitlines():
        stripped = line.strip()
        comment = not continued and stripped[:1] in ('#', '!')
        if not continued and stripped and not comment:
            count += 1
        # An odd number of backslashes at the end continues the line (not in a comment).
        continued = not comment and bool(re.search(r'(?<!\\)(?:\\\\)*\\$', line))
    return count


def coverage(jar):
    """'N/M': Corsican entries against the fullest catalogue in the same jar; None when the jar has no Corsican."""
    import zipfile
    try:
        with zipfile.ZipFile(jar) as archive:
            names = [name for name in archive.namelist()
                     if re.fullmatch(r'org/pdfsam/i18n/Messages_\w+\.properties', name)]
            if CATALOG not in names:
                return None
            counts = {name: properties_count(archive.read(name)) for name in names}
    except (OSError, zipfile.BadZipFile):
        return None
    return f'{counts[CATALOG]}/{max(counts.values())}'


class PDFsam(apps.App):
    id, name = 'pdfsam', 'PDFsam Basic'
    description = {'co': ('PDFsam Basic', "L'interfaccia di PDFsam Basic in corsu (Patriccollu)."),
                   'fr': ('PDFsam Basic', "L'interface de PDFsam Basic en corse (Patriccollu)."),
                   'en': ('PDFsam Basic', "PDFsam Basic's interface in Corsican (Patriccollu).")}
    validation = {'simulated': True, 'real_app': ['linux'], 'visual': True, 'linguistic_review': False}

    @property
    def restart_processes(self):
        # Windows: the setting can change while PDFsam is open; it shows Corsican at its next start.
        return ('pdfsam.exe',) if corsu.PLATFORM == 'windows' else ()

    @property
    def processes(self):
        # Linux: an open PDFsam would write its old value back over a switch-off (apps.busy() reads this). Its
        # process is a "java"; the command line says which.
        return ('java',) if corsu.PLATFORM == 'linux' and linux_running() else ()

    def folders(self):
        """(program folder, jar holding the translations or None) of each installation found on this platform."""
        found = []
        if corsu.PLATFORM == 'linux':
            candidates = list(LINUX_FOLDERS)
            launcher = apps.which('pdfsam-basic', 'pdfsam')
            if launcher:
                # bin/pdfsam-basic of the .deb or tar.gz (through /usr/bin/pdfsam); a script elsewhere (AUR) is
                # only counted when its folder holds PDFsam's jars.
                candidates.append(Path(launcher).resolve().parent.parent)
            for folder in dict.fromkeys(candidates):
                if folder.is_dir():
                    jars = sorted(folder.glob('lib/pdfsam-i18n-*.jar')) + sorted(folder.glob('pdfsam-i18n-*.jar'))
                    if jars or folder in LINUX_FOLDERS and (folder / 'bin').is_dir():
                        found.append((folder, jars[-1] if jars else None))
        elif corsu.PLATFORM == 'windows':
            for base in programs.program_dirs():
                folder = base / 'PDFsam Basic'
                if (folder / 'pdfsam.exe').exists():
                    jars = sorted(folder.glob('app/mods/pdfsam-i18n-*.jar')) + sorted(folder.glob('lib/pdfsam-i18n-*.jar'))
                    found.append((folder, jars[-1] if jars else None))
        elif corsu.PLATFORM == 'macos':
            for base in (*APPLICATIONS, corsu.HOME / 'Applications'):
                bundle = base / 'PDFsam Basic.app'
                if bundle.is_dir():
                    jars = sorted(bundle.glob('Contents/**/pdfsam-i18n-*.jar'))
                    found.append((bundle, jars[-1] if jars else None))
        return list(dict.fromkeys(found))

    def find(self):
        result = []
        for folder, jar in self.folders():
            version = version_of(jar) if jar else None
            covered = coverage(jar) if jar else None
            reason = action = None
            if covered is None:
                reason = corsu.t('its Corsican translation is missing (pdfsam-i18n jar without Messages_co)',
                                 'sa traduction corse manque (jar pdfsam-i18n sans Messages_co)')
                action = corsu.t('Update or reinstall PDFsam Basic, then run Corsu again',
                                 'Mettez à jour ou réinstallez PDFsam Basic, puis relancez Corsu')
            elif version and int(version.split('.')[0]) < 5:
                reason = corsu.t(f'PDFsam {version} keeps its language under another name than 5.0 and later',
                                 f'PDFsam {version} garde sa langue sous un autre nom que la 5.0 et suivantes')
                action = corsu.t('Update PDFsam Basic, then run Corsu again',
                                 'Mettez à jour PDFsam Basic, puis relancez Corsu')
            elif corsu.PLATFORM == 'macos':
                reason = corsu.t('on macOS, Corsu does not change Java\'s shared preferences file',
                                 'sur macOS, Corsu ne modifie pas le fichier de préférences partagé de Java')
                action = corsu.t('In PDFsam: Settings, Language, choose Corsican, then restart PDFsam',
                                 'Dans PDFsam : Paramètres, Langue, choisissez le corse, puis relancez PDFsam')
            elif not self.settings_exist():
                reason = corsu.t('PDFsam has not been started yet (no preferences yet)',
                                 'PDFsam n\'a pas encore été lancé (pas encore de préférences)')
                action = corsu.t('Start PDFsam Basic once, close it, then run Corsu again',
                                 'Lancez PDFsam Basic une fois, fermez-le, puis relancez Corsu')
            elif corsu.PLATFORM == 'linux' and linux_running():
                reason = programs.close_first(self.name)
                action = corsu.t(f'Close {self.name}, then switch it on in Corsu',
                                 f'Fermez {self.name}, puis activez-le dans Corsu')
            location = folder / 'pdfsam.exe' if corsu.PLATFORM == 'windows' else folder
            result.append(apps.Installation(self, corsu.t('installed', 'installé'), location, version, jar if covered else None,
                                            covered, reason, action))
        return result

    def settings_exist(self):
        if corsu.PLATFORM == 'windows':
            return registry_node_exists()
        return prefs_file().exists()

    def record(self, installer):
        """Corsu's record of this setting, when an earlier run switched it on."""
        if corsu.PLATFORM == 'windows':
            return installer.state['files'].get(f'HKCU\\{REGISTRY_KEY}\\{KEY}')
        return installer.state['files'].get(f'{prefs_file()}#{json.dumps(KEY)}')

    def current(self):
        if corsu.PLATFORM == 'windows':
            value = settings.registry_get(REGISTRY_KEY, KEY)
            return value[0] if value else None
        text = settings.read_body(prefs_file())[0]
        return settings.FILE_KINDS['java-prefs'][0](text, KEY)

    def enable(self, installer, installation):
        # Every installation of the account shares the one preference: a second installation finds it done.
        if self.record(installer):
            try:
                current = self.current()
            except Exception:  # unreadable: set_file_value below refuses it with the reason
                current = 'co'
            if current != 'co':
                return corsu.t(f'language changed in PDFsam since ({current or "automatic"}); left alone',
                               f'langue changée dans PDFsam depuis ({current or "automatique"}) ; laissé tel quel')
        if corsu.PLATFORM == 'windows':
            settings.set_registry(installer, self.id, REGISTRY_KEY, KEY, 'co', 1)
        else:
            settings.set_file_value(installer, self.id, prefs_file(), 'java-prefs', KEY, 'co')
        return None


PROGRAMS = (PDFsam,)
