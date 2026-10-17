r"""VLC media player. Its Corsican catalogue is Patriccollu di Santa Maria è Sichè's (po/co.po in videolan/vlc).

Windows: VLC's own language setting (HKCU\Software\VideoLAN\VLC, Lang). macOS: its preference "language" in the
org.videolan.vlc domain. Both are what VLC's Preferences write since 3.0.9.
Linux: VLC has no language setting of its own and follows the session language (LANGUAGE/LANG). gettext ignores
LANGUAGE when the session locale is "C" (no locale configured), as on bare servers; desktop sessions have one. When the Corsican
catalogue is installed with VLC (/usr/share/locale/co/LC_MESSAGES/vlc.mo), Corsu starts VLC's menu entry with
LANGUAGE=co:<your languages>; for the Flatpak, the same variable goes in its user override. When the catalogue is
missing, Corsu says so and changes nothing. Snap: left alone (no per-user environment override).
Corsican complement (experimental, Linux system package, only when the person switches it on with
--vlc-complement on): the upstream catalogue plus the drafts reviewed by AI, read by VLC through VLC_DATA_PATH; see
apps/vlc_complement.py.
"""
from pathlib import Path
import re
import subprocess

import corsu
import apps
from apps import vlc_complement

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
    # Real VLC: Ubuntu's in CI (help shown in Corsican) and the Windows registry setting on a real runner. Window looked
    # at: Debian's 3.0.24 in a container (menus and preferences, with and without the complement), Linux only.
    validation = {'simulated': True, 'real_app': ['linux', 'windows'], 'visual': True, 'linguistic_review': False}
    restart_processes = ('vlc', 'vlc.exe')
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
            french = LOCALE / 'fr/LC_MESSAGES/vlc.mo'
            coverage = apps.coverage_against(catalog, french)
            installed_version = version(executable)
            kind = corsu.t('system package', 'paquet du système')
            reason = None
            complement = vlc_complement.enabled()
            if complement:
                why = vlc_complement.unsupported(executable, installed_version)
                if why:
                    complement = False
                    kind = corsu.t(f'system package; complement not used: {why}',
                                   f'paquet du système ; complément non utilisé : {why}')
            if complement:
                _, upstream, added = vlc_complement.catalog()
                total = apps.mo_entries(french)
                coverage = f'{upstream + added}/{total}' if total else f'{upstream + added}'
                kind = corsu.t(f'system package, with Corsu\'s experimental complement ({added} AI translations, '
                               'not reviewed by a speaker)',
                               f'paquet du système, avec le complément expérimental de Corsu ({added} traductions IA, '
                               'non relues par un locuteur)')
            elif not catalog.exists():
                reason = corsu.t('this VLC package has no Corsican catalogue (vlc.mo); nothing changed',
                                 'ce paquet VLC n\'a pas de catalogue corse (vlc.mo) ; rien n\'est changé')
            if reason is None and apps.session_is_corsican() and not complement:
                reason = corsu.t('already in Corsican: your session language is Corsican',
                                 'déjà en corse : la langue de votre session est le corse')
            installation = apps.Installation(self, kind, executable, installed_version,
                                             catalog if catalog.exists() else None, coverage, reason)
            installation.complement = complement
            found.append(installation)
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

    def leave(self, installer, installation):
        """The complement switched off where VLC has no Corsican of its own: its folder and the menu entry that
        pointed VLC to it go."""
        if not hasattr(installation, 'complement'):
            return
        vlc_complement.remove(installer)
        entry = corsu.HOME / '.local/share/applications/vlc.desktop'
        record = installer.state['files'].get(str(entry))
        if record and entry.exists() and 'VLC_DATA_PATH=' in entry.read_text(encoding='utf-8') \
                and corsu.restore(entry, record):
            installer.state['files'].pop(str(entry))
            corsu.save_state(installer.state)

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
        if getattr(installation, 'complement', False):
            path, _, _ = vlc_complement.prepare(installer, installation.location)
            return apps.desktop_override(installer, self.id, 'vlc.desktop', apps.corsican_first(),
                                         {'VLC_DATA_PATH': path})
        vlc_complement.remove(installer)
        return apps.desktop_override(installer, self.id, 'vlc.desktop', apps.corsican_first())
