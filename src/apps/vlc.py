"""VLC media player. Its Corsican catalogue is Patriccollu di Santa Maria è Sichè's (po/co.po in videolan/vlc).

Windows: VLC's own language setting (HKCU\Software\VideoLAN\VLC, Lang). macOS: its preference "language" in the
org.videolan.vlc domain. Both are what VLC's Preferences write since 3.0.9.
Linux: VLC has no language setting of its own and follows the session language (LANGUAGE/LANG). gettext ignores
LANGUAGE when the session locale is "C" (no locale configured), as on bare servers; desktop sessions have one. When the Corsican
catalogue is installed with VLC (/usr/share/locale/co/LC_MESSAGES/vlc.mo), Corsu starts VLC's menu entry with
LANGUAGE=co:<your languages>; for the Flatpak, the same variable goes in its user override. When the catalogue is
missing, Corsu says so and changes nothing. Snap: left alone (no per-user environment override).
"""
from pathlib import Path
import re
import subprocess

import corsu
import apps

FLATPAK = 'org.videolan.VLC'
LOCALE = Path('/usr/share/locale')
SNAP = Path('/snap/vlc')


def version(executable):
    try:
        output = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r'VLC (?:media player |version )?(\d+\.\d+[\w.-]*)', output)
    return match.group(1) if match else None


class VLC(apps.App):
    id = 'vlc'
    name = 'VLC'
    description = {
        'co': ('VLC', "L'interfaccia di VLC, cù a so traduzzione corsa (Patriccollu di Santa Maria è Sichè)."),
        'fr': ('VLC', "L'interface de VLC, avec sa traduction corse (Patriccollu di Santa Maria è Sichè)."),
        'en': ('VLC', "VLC's interface, with its own Corsican translation (Patriccollu di Santa Maria è Sichè)."),
    }

    def find(self):
        if corsu.PLATFORM == 'windows':
            return self.find_windows()
        if corsu.PLATFORM == 'macos':
            return self.find_macos()
        found = []
        executable = apps.which('vlc')
        if executable and not executable.startswith('/snap/'):
            catalog = LOCALE / 'co/LC_MESSAGES/vlc.mo'
            coverage = apps.coverage_against(catalog, LOCALE / 'fr/LC_MESSAGES/vlc.mo')
            reason = None
            if not catalog.exists():
                reason = corsu.t('this VLC package has no Corsican catalogue (vlc.mo); nothing changed',
                                 'ce paquet VLC n\'a pas de catalogue corse (vlc.mo) ; rien n\'est changé')
            elif apps.session_is_corsican():
                reason = corsu.t('already in Corsican: your session language is Corsican',
                                 'déjà en corse : la langue de votre session est le corse')
            found.append(apps.Installation(self, corsu.t('system package', 'paquet du système'), executable,
                                           version(executable), catalog if catalog.exists() else None, coverage, reason))
        base = apps.flatpak_installed(FLATPAK)
        if base:
            catalog = apps.flatpak_catalog(base, FLATPAK, 'vlc')
            reason = None if catalog else corsu.t(
                'the Flatpak\'s languages do not include Corsican (flatpak config --set extra-languages co, then update)',
                'les langues du Flatpak n\'incluent pas le corse (flatpak config --set extra-languages co, puis mise à jour)')
            found.append(apps.Installation(self, 'Flatpak', base / 'app' / FLATPAK, None, catalog,
                                           apps.coverage_against(catalog, None) if catalog else None, reason))
        if SNAP.exists():
            found.append(apps.Installation(self, 'Snap', SNAP, reason=corsu.t(
                'Snap packages cannot be given a language per user; nothing changed',
                'un paquet Snap ne peut pas recevoir de langue par utilisateur ; rien n\'est changé')))
        return found

    def find_windows(self):
        from apps import programs
        found = []
        for base in programs.program_dirs():
            executable = base / 'VideoLAN/VLC/vlc.exe'
            if executable.exists():
                catalog = executable.parent / 'locale/co/LC_MESSAGES/vlc.mo'
                coverage = apps.coverage_against(catalog, executable.parent / 'locale/fr/LC_MESSAGES/vlc.mo')
                reason = None if catalog.exists() else corsu.t('no Corsican catalogue in this VLC',
                                                               'pas de catalogue corse dans ce VLC')
                found.append(apps.Installation(self, corsu.t('installed', 'installé'), executable, None,
                                               catalog if catalog.exists() else None, coverage, reason))
        return found

    def find_macos(self):
        bundle = Path('/Applications/VLC.app')
        if not bundle.exists():
            return []
        catalog = bundle / 'Contents/MacOS/share/locale/co/LC_MESSAGES/vlc.mo'
        coverage = apps.coverage_against(catalog, bundle / 'Contents/MacOS/share/locale/fr/LC_MESSAGES/vlc.mo')
        reason = None if catalog.exists() else corsu.t('no Corsican catalogue in this VLC', 'pas de catalogue corse dans ce VLC')
        return [apps.Installation(self, 'VLC.app', bundle, None, catalog if catalog.exists() else None, coverage, reason)]

    def enable(self, installer, installation):
        from apps import settings
        if corsu.PLATFORM == 'windows':
            # VLC's own Preferences → Interface → Language writes this value.
            settings.set_registry(installer, self.id, r'Software\VideoLAN\VLC', 'Lang', 'co', 1)
            return None
        if corsu.PLATFORM == 'macos':
            settings.set_defaults(installer, self.id, 'org.videolan.vlc', 'language', 'co')
            return None
        if installation.kind == 'Flatpak':
            apps.flatpak_language(installer, self.id, FLATPAK, apps.corsican_first())
            return None
        return apps.desktop_override(installer, self.id, 'vlc.desktop', apps.corsican_first())
