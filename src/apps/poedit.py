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

Linux: no setting (NEED_CHOOSELANG_UI is 0, src/uilang.h#L35-L39 in 3.6.3 and 3.10): Poedit follows the session
language, but through wxWidgets 3.2, not gettext. PoeditApp::SetupLanguage (edapp.cpp#L543-L590 in 3.6.3) asks
wxUILocale::GetPreferredUILanguages, which puts the language of LC_ALL, else LC_MESSAGES, else LANG first and
LANGUAGE's list only after it, a "C"/"POSIX" value (the part before "." and "@") counting as none
(https://github.com/wxWidgets/wxWidgets/blob/v3.2.8/src/unix/uilocale.cpp#L56-L99, #L886-L956; the same in 3.2.12,
Flathub's build); ICU's uloc_acceptLanguage then takes the first of these Poedit has a catalogue for. So LANGUAGE=co:fr
alone, enough for VLC, still gives French in a French session (seen for real). Then wxLocale::Init(wxLANGUAGE_DEFAULT)
does setlocale(LC_ALL, "") (src/common/intl.cpp#L486), and GTK (the file chooser, its buttons) translates with
glibc's gettext from that locale. Corsu 0.25's first way, LANG=C.UTF-8 and LC_MESSAGES=C.UTF-8 with the formats given
back, made wxWidgets read LANGUAGE first, but glibc ignores LANGUAGE when LC_MESSAGES is "C" or "C.<codeset>"
(intl/dcigettext.c, guess_category_value, release/2.41 lines 1527-1543): GTK's dialogs came out in English (seen for
real, in the Debian package and the Flatpak). A Corsican locale name (LC_MESSAGES=co_FR.UTF-8) does not exist in
glibc: setlocale(LC_ALL, "") then fails as a whole and Poedit shows "locale::facet::_S_create_c_locale name not
valid" in its suggestions panel (seen for real).

What Corsu does: LANGUAGE=co:<your languages> and LC_MESSAGES=/C.UTF-8, LANG and the format categories left as they
are. The two readers disagree on that one value. wxWidgets keeps "/C" (before the "."): not "C", not a language it
knows, so nothing goes before LANGUAGE's list and Poedit takes Corsican. glibc accepts a locale name starting with "/"
(locale/findlocale.c, valid_locale_name) and looks it up under its own locale folder: /usr/lib/locale//C.UTF-8, the
C.UTF-8 locale that glibc 2.35+ ships as a folder (Debian, Ubuntu, Fedora, Arch; the Flatpak runtimes too). Only
LC_MESSAGES comes from it (yes/no answers in English, unused by Poedit), and its name is not "C", so gettext follows
LANGUAGE: GTK, which has no Corsican, takes the next language, yours. Seen for real (2026-10-17) with Debian 13's
package (Poedit 3.6.3, wxWidgets 3.2.8, glibc 2.41) and Flathub's Poedit 3.10 (GNOME 51 runtime, glibc 2.44), in
containers under Xvfb, sessions fr_FR, de_DE and it_IT: Poedit's windows in Corsican, the GTK file chooser and its
buttons in French, German, Italian, dates in the file list and "50 %" in the status bar in the session's format, a
.po file in a folder with accents opened, no locale error. This relies on how glibc resolves locale names, which is
not a documented interface: before writing the menu entry Corsu checks it with `locale` (LC_ALL=/C.UTF-8 must load
without "Cannot set"). Where it fails (another C library, a glibc without the C.UTF-8 folder), Corsu falls back to the
first way and says what it costs: Poedit in Corsican, GTK's dialogs in English (with "C" instead of "C.UTF-8" where
that locale does not load either: LC_MESSAGES=C.UTF-8 would make setlocale(LC_ALL, "") fail as a whole and take the
session's formats away, seen in a Debian 13 container without C.UTF-8). When the session sets LC_ALL (which
beats LC_MESSAGES everywhere), Corsu empties it and gives its value to LANG and to the categories the session sets.
For the Flatpak, the same variables go in its user override (no check there: the runtime's glibc is the one seen).
Debian's package (3.6.3, Debian 13; wxWidgets 3.2.8) installs /usr/bin/poeditor, the entries
net.poedit.Poedit.desktop and net.poedit.PoeditURI.desktop (both "Exec=poeditor …"), and poedit-common's
/usr/share/locale/co/LC_MESSAGES/poedit.mo; Poedit reads its catalogues in <prefix of the executable>/share/locale
(edapp.cpp#L386-L395, #L549-L551). ~/.config/poedit/config (rewritten by Poedit when it quits) is never touched by
Corsu. Flathub's net.poedit.Poedit keeps its catalogues in its .Locale extension (co present: 736 messages), so
Corsican is there only when Flatpak's languages include it. Snap: left alone (no per-user environment override).

macOS: no setting of Poedit's own (NEED_CHOOSELANG_UI is 0; the 3.10 binary has no ui_language string);
Poedit.app/Contents/Resources/co.lproj has the catalogue. wxUILocale::GetPreferredUILanguages is
[NSLocale preferredLanguages] there (https://github.com/wxWidgets/wxWidgets/blob/v3.2.8/src/osx/core/uilocale.mm#L314-L325),
which reads AppleLanguages from the application's own domain before the global one: the per-application language of
System Settings → General → Language & Region → Applications, an array. Corsu writes that array in Poedit's domain
only (net.poedit.Poedit, not sandboxed: PRODUCT_BUNDLE_IDENTIFIER in Poedit.xcodeproj, no entitlements for the app):
Corsican, then your own list (read from the global AppleLanguages, never written), so AppKit's own panels, which have
no Corsican, take your language. The earlier value (or its absence) is recorded with its type and given back; a list
changed since (in System Settings) is yours and stays. Experimental: Poedit itself was not run on a Mac. Seen on a
GitHub Actions macOS 26 runner (tests/test_apps_settings.py, RealMacTests, 2026-10-17): Corsu's `defaults` helper
writes the array and gives back an absent key, an array, a string, a number, a boolean and a dictionary exactly, and a
small tool with its own bundle identifier gets [NSLocale preferredLanguages] = co,fr-FR from that per-application
list (en-US without it). Not seen: Poedit's window, and AppKit's panels taking the second language. A string written
in AppleLanguages reads back as absent on macOS (seen on that runner): Foundation only takes an array there.
"""
import os
from pathlib import Path
import subprocess

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
MAC_DOMAIN = 'net.poedit.Poedit'
# LC_MESSAGES for Poedit: "/C" to wxWidgets, glibc's C.UTF-8 messages under another name to gettext (module docstring).
MESSAGES = '/C.UTF-8'
# Categories that keep the session's locale while LANG and LC_MESSAGES are C.UTF-8 (the fallback, module docstring).
FORMATS = ('LC_CTYPE', 'LC_NUMERIC', 'LC_TIME', 'LC_COLLATE', 'LC_MONETARY', 'LC_PAPER', 'LC_MEASUREMENT')
CATEGORIES = (*FORMATS, 'LC_NAME', 'LC_ADDRESS', 'LC_TELEPHONE', 'LC_IDENTIFICATION')


def is_c(locale):
    return locale.split('.')[0].split('@')[0] in ('', 'C', 'POSIX')


def locale_loads(name):
    """Whether this computer's C library loads the locale `name` (`locale` with LC_ALL=name says nothing wrong)."""
    try:
        result = subprocess.run(['locale'], env={'LC_ALL': name, 'PATH': os.environ.get('PATH') or '/usr/bin:/bin'},
                                capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and not result.stderr.strip() and name in result.stdout


def messages_name_works():
    """Whether this computer's C library loads LC_MESSAGES=/C.UTF-8 (glibc 2.35+ with its C.UTF-8 folder)."""
    return locale_loads(MESSAGES)


def c_utf8_works():
    """Whether C.UTF-8 loads at all (the fallback's LANG and LC_MESSAGES; plain "C" otherwise)."""
    return locale_loads('C.UTF-8')


def environment(separate=True):
    """The variables besides LANGUAGE that make Poedit (wxWidgets) take LANGUAGE's list first: {name: value}, an empty
    value clearing the variable. separate: GTK keeps the session's language (LC_MESSAGES=/C.UTF-8); otherwise the
    fallback, LANG and LC_MESSAGES C.UTF-8 with the session's formats given back (GTK then in English)."""
    everything = os.environ.get('LC_ALL', '')
    if separate:
        result = {'LC_MESSAGES': MESSAGES}
        if everything:  # LC_ALL beats LC_MESSAGES: its value goes where it applied
            result['LC_ALL'] = ''
            result['LANG'] = everything
            for name in CATEGORIES:
                if os.environ.get(name):
                    result[name] = everything
        return result
    neutral = 'C.UTF-8' if c_utf8_works() else 'C'  # a locale that does not load would lose every category
    result = {'LANG': neutral, 'LC_MESSAGES': neutral}
    if everything:
        result['LC_ALL'] = ''
    for name in FORMATS:
        if os.environ.get(name) and not everything:
            continue  # set by the session itself: Poedit inherits it
        value = everything or os.environ.get(name) or os.environ.get('LANG', '')
        if not is_c(value):
            result[name] = value
    return result


def mac_languages():
    """Corsican, then the person's own list for the rest (the global AppleLanguages, read only)."""
    try:
        system = settings.defaults_value('NSGlobalDomain', 'AppleLanguages')
    except (OSError, ValueError):
        system = None
    if not isinstance(system, list) or not all(isinstance(item, str) for item in system):
        system = [language.replace('_', '-') for language in apps.session_languages()]
    return ['co', *dict.fromkeys(item for item in system if item and not item.lower().startswith('co'))]


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
    # Real: Debian 13's package (3.6.3) and Flathub's 3.10 in containers, started under Xvfb with the variables Corsu
    # writes, the window and the GTK file chooser seen (fr, de, it sessions), switched off, run again, uninstalled
    # (2026-10-17). Windows and macOS: fixtures only (macOS experimental).
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
            separate = reason is None and messages_name_works()
            kind = corsu.t('system package', 'paquet du système')
            if reason is None and not separate:
                kind = corsu.t('system package; its file dialogs will be in English: this system\'s C library has no '
                               'C.UTF-8 locale folder to keep them in your language',
                               'paquet du système ; ses fenêtres de fichiers seront en anglais : la bibliothèque C de ce '
                               'système n\'a pas le dossier de locale C.UTF-8 qui les garderait dans votre langue')
            item = apps.Installation(self, kind, executable, None,
                                     catalog if catalog.exists() else None,
                                     apps.coverage_against(catalog, locale / 'fr/LC_MESSAGES/poedit.mo')
                                     if catalog.exists() else None, reason, action)
            item.setting = 'menu'
            item.separate = separate
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
            reason = action = None
            if not catalog.exists():
                reason, action = self.missing(catalog)
            # Experimental: the per-application language list was not tried on a Mac yet (module docstring).
            kind = corsu.t('Poedit.app, experimental: not checked on a Mac yet',
                           'Poedit.app, expérimental : pas encore vérifié sur un Mac')
            item = apps.Installation(self, kind, bundle, None, catalog if catalog.exists() else None,
                                     apps.coverage_against(catalog, resources / 'fr.lproj/poedit.mo')
                                     if catalog.exists() else None, reason, action)
            item.setting = 'defaults'
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
        if installation.setting == 'defaults':
            name = f'defaults:{MAC_DOMAIN}:AppleLanguages'
            current = settings.defaults_value(MAC_DOMAIN, 'AppleLanguages')  # ValueError: reported as a failure
            if current is None and installer.state['files'].get(name):
                # Corsu's list is gone while still recorded (switching off drops the record): the person chose
                # "System default" for Poedit in System Settings, which deletes the key. Keep that choice, and forget
                # the original so uninstalling does not bring back a list from before it.
                installer.state['files'].pop(name)
                corsu.save_state(installer.state)
                return changed_message()
            if changed_since(installer, name, None if current is None else settings.plist_fragment(current)):
                return changed_message()
            # What System Settings → Language & Region → Applications writes: an array in Poedit's own domain.
            settings.set_defaults_value(installer, self.id, MAC_DOMAIN, 'AppleLanguages', mac_languages())
            return None
        if installation.setting == 'flatpak':
            override = flatpak_override()
            text, _, _ = settings.read_body(override)  # ValueError (not UTF-8): left alone, reported as a failure
            if changed_since(installer, f'{override}#[Environment]LANGUAGE',
                             settings.ini_get(text, 'Environment', 'LANGUAGE')):
                return changed_message()
            values = {'LANGUAGE': apps.corsican_first(), **environment(separate=True)}
            # A variable Corsu set at an earlier run and no longer needs (the session changed) goes back first.
            self.take_back(installer, keep=set(values))
            for key, value in values.items():
                settings.set_ini(installer, self.id, override, 'Environment', key, value)
            return None
        language = apps.corsican_first()
        variables = environment(separate=getattr(installation, 'separate', True))
        reason = apps.desktop_override(installer, self.id, DESKTOP, language, variables)
        if reason is None and any((folder / DESKTOP_URI).exists() for folder in apps.APPLICATION_DIRS):
            # Secondary: a menu entry of the person's own for links is simply left as it is.
            apps.desktop_override(installer, self.id, DESKTOP_URI, language, variables)
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
        if setting == 'defaults':
            name = f'defaults:{MAC_DOMAIN}:AppleLanguages'
            record = installer.state['files'].get(name)
            if record and record.get('component') == self.id and settings.revert(record):
                installer.state['files'].pop(name)
                corsu.save_state(installer.state)
        if setting != 'menu':
            return
        for desktop_id in (DESKTOP, DESKTOP_URI):
            entry = corsu.HOME / '.local/share/applications' / desktop_id
            record = installer.state['files'].get(str(entry))
            if record and record.get('component') == self.id and entry.exists() and corsu.restore(entry, record):
                installer.state['files'].pop(str(entry))
                corsu.save_state(installer.state)


PROGRAMS = (Poedit,)
