r"""Poedit, whose Corsican translation (locales/co.po) is Patriccollu di Santa Maria è Sichè's.

Only the Windows build has a language setting of its own: NEED_CHOOSELANG_UI is 1 on __WXMSW__ only
(https://github.com/vslavik/poedit/blob/v3.10-oss/src/uilang.h#L34-L38, the same since at least 3.4.2 in
src/chooselang.h). Elsewhere Poedit picks the best of its catalogues for the language list the system gives it
(wxUILocale::GetPreferredUILanguages, then ICU's uloc_acceptLanguage,
https://github.com/vslavik/poedit/blob/v3.10-oss/src/uilang.cpp#L88-L169).

Windows: the wxConfig value ui_language, written by Preferences → "Change UI language" as a language tag ("co") or
"default" (uilang.cpp#L198-L204), read once at start-up (uilang.cpp#L207-L222, edapp.cpp#L562-L571). Poedit's
wxConfig has no file there (edapp.cpp#L405-L411, configuration.cpp#L42-L45), so it is wxRegConfig under
HKCU\Software\<vendor>\<app> with vendor "Vaclav Slavik" and app "Poedit" (edapp.cpp#L344-L345): the REG_SZ value
HKCU\Software\Vaclav Slavik\Poedit\ui_language = co. wxRegConfig writes a value only when the program writes it, and
only that dialog writes this one, so Poedit open does not undo Corsu's value: it shows Corsican at its next start.
The value can be written before Poedit's first start (nothing to create first). Poedit 3.10's installer
(Poedit-3.10-setup.exe, unpacked in a container) puts the program in Program Files\Poedit with
Translations\co\poedit.mo (1089 messages, as many as Translations\fr\poedit.mo). Poedit.exe itself could not be
started under Wine (it needs Windows' own icu.dll), so the registry value is checked against the source only.

Linux: no setting; Poedit follows the session language, but through wxWidgets 3.2, not gettext: the language of
LC_ALL, else LC_MESSAGES, else LANG comes first, and LANGUAGE's list only after it; a "C" locale counts as none
(https://github.com/wxWidgets/wxWidgets/blob/v3.2.8/src/unix/uilocale.cpp#L886-L956, #L56-L99). So LANGUAGE=co:fr
alone, enough for VLC, still gives French in a French session (seen for real). Corsu starts Poedit's menu entry with
LANGUAGE=co:<your languages>, LANG=C.UTF-8 and LC_MESSAGES=C.UTF-8 (and LC_ALL emptied when the session sets it),
and gives back the session's own locale for the format categories (LC_CTYPE, LC_NUMERIC, LC_TIME, LC_COLLATE,
LC_MONETARY, LC_PAPER, LC_MEASUREMENT), so numbers, dates and sorting stay as they were. A Corsican locale name
instead (LC_MESSAGES=co_FR.UTF-8) does not exist in glibc: the whole C library locale then fails and Poedit shows
"locale::facet::_S_create_c_locale name not valid" in its suggestions panel (seen for real), so it is not used. The cost:
GTK's own dialogs (the file chooser) show English instead of French, GTK having no Corsican; Poedit's own windows,
menus and messages are Corsican. For the Flatpak, the same variables go in its user override.
Debian's package (3.6.3, Debian 13; wxWidgets 3.2.8) installs /usr/bin/poeditor, the entries
net.poedit.Poedit.desktop and net.poedit.PoeditURI.desktop (both "Exec=poeditor …"), and poedit-common's
/usr/share/locale/co/LC_MESSAGES/poedit.mo; Poedit reads its catalogues in <prefix of the executable>/share/locale
(edapp.cpp#L386-L395, #L549-L551). Run for real in a container: the window showed Corsican, a file in a folder with
accents opened, and ~/.config/poedit/config (rewritten by Poedit when it quits) is never touched by Corsu.
Flathub's net.poedit.Poedit keeps its catalogues in its .Locale extension (co present: 736 messages), so Corsican is
there only when Flatpak's languages include it; the Flatpak was not run (fixtures only). Snap: left alone (no
per-user environment override).

macOS: no setting either (the 3.10 binary has no ui_language string); Poedit.app/Contents/Resources/co.lproj has the
catalogue, and Poedit follows the system's language list for the application. Corsu would need the per-application
AppleLanguages array, which its preference helper cannot write yet: left alone, with the system's own way to do it.
"""
import os
from pathlib import Path

import corsu
import apps
from apps import settings

LOCALE = Path('/usr/share/locale')
APPLICATIONS = (Path('/Applications'),)
SNAP = Path('/snap/poedit')
FLATPAK = 'net.poedit.Poedit'
DESKTOP = 'net.poedit.Poedit.desktop'
# Opens poedit:// links (Poedit's cloud accounts); started with Corsican too when it is there.
DESKTOP_URI = 'net.poedit.PoeditURI.desktop'
REGISTRY_KEY = r'Software\Vaclav Slavik\Poedit'
REGISTRY_VALUE = 'ui_language'
# Categories that keep the session's locale while LANG and LC_MESSAGES are C.UTF-8 (see the module docstring).
FORMATS = ('LC_CTYPE', 'LC_NUMERIC', 'LC_TIME', 'LC_COLLATE', 'LC_MONETARY', 'LC_PAPER', 'LC_MEASUREMENT')


def is_c(locale):
    return locale.split('.')[0].split('@')[0] in ('', 'C', 'POSIX')


def environment():
    """The variables besides LANGUAGE that make Poedit (wxWidgets) take LANGUAGE's list first, keeping the session's
    formats: {name: value}, an empty value clearing the variable."""
    everything = os.environ.get('LC_ALL', '')
    result = {'LANG': 'C.UTF-8', 'LC_MESSAGES': 'C.UTF-8'}
    if everything:
        result['LC_ALL'] = ''
    for name in FORMATS:
        if os.environ.get(name) and not everything:
            continue  # set by the session itself: Poedit inherits it
        value = everything or os.environ.get(name) or os.environ.get('LANG', '')
        if not is_c(value):
            result[name] = value
    return result


def flatpak_override():
    return corsu.HOME / '.local/share/flatpak/overrides' / FLATPAK


def changed_since(installer, name, current):
    """True when Corsu set this setting before and it now holds something else: the person's choice."""
    record = installer.state['files'].get(name)
    return bool(record and current is not None and current != record['setting']['installed'])


def changed_message():
    return corsu.t('language changed since Corsu set it; your choice is kept',
                   'langue changée depuis que Corsu l\'a réglée ; votre choix est gardé')


class Poedit(apps.App):
    id, name = 'poedit', 'Poedit'
    description = {'co': ('Poedit', "L'interfaccia di Poedit in corsu (Patriccollu)."),
                   'fr': ('Poedit', "L'interface de Poedit en corse (Patriccollu)."),
                   'en': ('Poedit', "Poedit's interface in Corsican (Patriccollu).")}
    # Real: Debian 13's package (3.6.3) in a container, the menu entry's command started under Xvfb and the window
    # seen in Corsican, switched off, run again, uninstalled (2026-10-17). Windows and macOS: fixtures only.
    validation = {'simulated': True, 'real_app': ['linux'], 'visual': True, 'linguistic_review': False}
    # Poedit reads its language at start only and keeps one instance: an open Poedit shows Corsican once restarted.
    restart_processes = ('poedit', 'poeditor', 'Poedit.exe', 'Poedit')

    def find(self):
        if corsu.PLATFORM == 'windows':
            return self.find_windows()
        if corsu.PLATFORM == 'macos':
            return self.find_macos()
        return self.find_linux()

    def missing(self, catalog):
        return (corsu.t(f'its Corsican catalogue is missing ({catalog})', f'son catalogue corse manque ({catalog})'),
                corsu.t('Reinstall Poedit with its translations, then run Corsu again',
                        'Réinstallez Poedit avec ses traductions, puis relancez Corsu'))

    def find_linux(self):
        found = []
        executable = apps.which('poeditor', 'poedit')
        if executable and not executable.startswith('/snap/'):
            locale = Path(executable).resolve().parent.parent / 'share/locale'
            if not locale.is_dir():
                locale = LOCALE
            catalog = locale / 'co/LC_MESSAGES/poedit.mo'
            reason = action = None
            if not catalog.exists():
                reason = self.missing(catalog)[0]
                action = corsu.t('Install Poedit\'s translations (Debian, Ubuntu: poedit-common), then run Corsu again',
                                 'Installez les traductions de Poedit (Debian, Ubuntu : poedit-common), puis relancez Corsu')
            elif apps.session_is_corsican():
                reason = corsu.t('already in Corsican: your session language is Corsican',
                                 'déjà en corse : la langue de votre session est le corse')
            item = apps.Installation(self, corsu.t('system package', 'paquet du système'), executable, None,
                                     catalog if catalog.exists() else None,
                                     apps.coverage_against(catalog, locale / 'fr/LC_MESSAGES/poedit.mo')
                                     if catalog.exists() else None, reason, action)
            item.setting = 'menu'
            found.append(item)
        base = apps.flatpak_installed(FLATPAK)
        if base:
            catalog = apps.flatpak_catalog(base, FLATPAK, 'poedit')
            reason = action = None
            if catalog is None:
                reason = corsu.t(
                    'the Flatpak\'s languages do not include Corsican (flatpak config --set extra-languages co, then update)',
                    'les langues du Flatpak n\'incluent pas le corse (flatpak config --set extra-languages co, puis mise à jour)')
                action = corsu.t('Run: flatpak config --user --set extra-languages co && flatpak update, then run Corsu again',
                                 'Lancez : flatpak config --user --set extra-languages co && flatpak update, puis relancez Corsu')
            item = apps.Installation(self, 'Flatpak', base / 'app' / FLATPAK, None, catalog,
                                     apps.coverage_against(catalog, None) if catalog else None, reason, action)
            item.setting = 'flatpak'
            found.append(item)
        if SNAP.exists():
            item = apps.Installation(self, 'Snap', SNAP, reason=corsu.t(
                'Snap packages cannot be given a language per user; nothing changed',
                'un paquet Snap ne peut pas recevoir de langue par utilisateur ; rien n\'est changé'))
            item.setting = None
            found.append(item)
        return found

    def find_windows(self):
        from apps import programs
        found = []
        for base in programs.program_dirs():
            executable = base / 'Poedit/Poedit.exe'
            if not executable.exists():
                continue
            translations = executable.parent / 'Translations'
            catalog = translations / 'co/poedit.mo'
            reason = action = None
            if not catalog.exists():
                reason, action = self.missing(catalog)
            item = apps.Installation(self, corsu.t('installed', 'installé'), executable, None,
                                     catalog if catalog.exists() else None,
                                     apps.coverage_against(catalog, translations / 'fr/poedit.mo')
                                     if catalog.exists() else None, reason, action)
            item.setting = 'registry'
            found.append(item)
        return found

    def find_macos(self):
        found = []
        for folder in dict.fromkeys((*APPLICATIONS, corsu.HOME / 'Applications')):
            bundle = folder / 'Poedit.app'
            if not bundle.exists():
                continue
            resources = bundle / 'Contents/Resources'
            catalog = resources / 'co.lproj/poedit.mo'
            if catalog.exists():
                reason = corsu.t('Poedit on macOS has no language setting of its own; Corsu does not change the '
                                 'system\'s language list for it yet',
                                 'Poedit sur macOS n\'a pas de réglage de langue à lui ; Corsu ne change pas encore la '
                                 'liste de langues du système pour lui')
                action = corsu.t('In System Settings → General → Language & Region → Applications, add Poedit and '
                                 'choose Corsican if it is offered (not checked by Corsu)',
                                 'Dans Réglages Système → Général → Langue et région → Applications, ajoutez Poedit et '
                                 'choisissez le corse s\'il est proposé (non vérifié par Corsu)')
            else:
                reason, action = self.missing(catalog)
            item = apps.Installation(self, 'Poedit.app', bundle, None, catalog if catalog.exists() else None,
                                     apps.coverage_against(catalog, resources / 'fr.lproj/poedit.mo')
                                     if catalog.exists() else None, reason, action)
            item.setting = None
            found.append(item)
        return found

    def enable(self, installer, installation):
        if installation.setting == 'registry':
            name = f'HKCU\\{REGISTRY_KEY}\\{REGISTRY_VALUE}'
            current = settings.registry_get(REGISTRY_KEY, REGISTRY_VALUE)
            if changed_since(installer, name, list(current) if current else None):
                return changed_message()
            # What Poedit's "Change UI language" writes (REG_SZ).
            settings.set_registry(installer, self.id, REGISTRY_KEY, REGISTRY_VALUE, 'co', 1)
            return None
        if installation.setting == 'flatpak':
            override = flatpak_override()
            text, _, _ = settings.read_body(override)  # ValueError (not UTF-8): left alone, reported as a failure
            if changed_since(installer, f'{override}#[Environment]LANGUAGE',
                             settings.ini_get(text, 'Environment', 'LANGUAGE')):
                return changed_message()
            values = {'LANGUAGE': apps.corsican_first(), **environment()}
            # A variable Corsu set at an earlier run and no longer needs (the session changed) goes back first.
            self.take_back(installer, keep=set(values))
            for key, value in values.items():
                settings.set_ini(installer, self.id, override, 'Environment', key, value)
            return None
        language = apps.corsican_first()
        reason = apps.desktop_override(installer, self.id, DESKTOP, language, environment())
        if reason is None and any((folder / DESKTOP_URI).exists() for folder in apps.APPLICATION_DIRS):
            # Secondary: a menu entry of the person's own for links is simply left as it is.
            apps.desktop_override(installer, self.id, DESKTOP_URI, language, environment())
        return reason

    def take_back(self, installer, keep=()):
        """Put back the Flatpak override's variables Corsu set (those still holding Corsu's value), except keep."""
        override = str(flatpak_override())
        for name, record in list(installer.state['files'].items()):
            setting = record.get('setting') or {}
            if record.get('component') == self.id and setting.get('file') == override \
                    and setting.get('key') not in keep and settings.revert(record):
                installer.state['files'].pop(name)
                corsu.save_state(installer.state)

    def leave(self, installer, installation):
        """Corsican no longer usable there (catalogue gone, session already Corsican): what Corsu wrote for that
        installation goes back, unless the person changed it since."""
        setting = getattr(installation, 'setting', None)
        if setting == 'flatpak':
            self.take_back(installer)
        if setting != 'menu':
            return
        for desktop_id in (DESKTOP, DESKTOP_URI):
            entry = corsu.HOME / '.local/share/applications' / desktop_id
            record = installer.state['files'].get(str(entry))
            if record and record.get('component') == self.id and entry.exists() and corsu.restore(entry, record):
                installer.state['files'].pop(str(entry))
                corsu.save_state(installer.state)


PROGRAMS = (Poedit,)
