"""Desktop entries KDE reads names from (applications menu, Shortcuts components): Corsican where Corsu has it, the
French text where it has not, never English for a Corsican session (LANGUAGE=co:fr)."""
import configparser
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import corsu

# Shortened copies of Plasma 6.7's files (kscreen): the entry of the display settings module and its Shortcuts
# component, whose English names were what KDE showed.
KCM = """[Desktop Entry]
Exec=systemsettings kcm_kscreen
Icon=preferences-desktop-display-randr
Type=Application
NoDisplay=true
Name=Display Configuration
Name[de]=Anzeige-Einrichtung
Name[fr]=Configuration de l'affichage
Comment=Manage and configure monitors and displays
Comment[fr]=Gérer et configurer les moniteurs et les affichages
X-KDE-Keywords=display,monitor
"""
KGLOBALACCEL = """[Desktop Entry]
Type=Application
Name=Display Configuration
Name[fr]=Configuration de l'affichage
X-KDE-Shortcuts=Meta+P

[Desktop Action ShowOSD]
Name=Switch Display
Name[fr]=Basculer l'affichage
X-KDE-Shortcuts=Display,Meta+P

[Desktop Action Other]
Name=Toggle Something Untranslated
Name[fr]=Basculer une chose inconnue
"""
# Nothing here that Corsu translates: the system's file stays the one KDE reads.
UNKNOWN = """[Desktop Entry]
Type=Application
Name=Zzyzx Tool
Name[fr]=Outil Zzyzx
Exec=zzyzx
"""


def entries(path):
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(path, encoding='utf-8')
    return config


class DesktopEntryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.home = root / 'home'
        self.system = root / 'usr/share'
        for folder, name, text in (('applications', 'kcm_kscreen.desktop', KCM),
                                   ('applications', 'zzyzx.desktop', UNKNOWN),
                                   ('kglobalaccel', 'org.kde.kscreen.desktop', KGLOBALACCEL)):
            (self.system / folder).mkdir(parents=True, exist_ok=True)
            (self.system / folder / name).write_text(text, encoding='utf-8')
        self.folders = (('applications', self.system / 'applications'), ('kglobalaccel', self.system / 'kglobalaccel'))
        data = self.home / '.local/share/corsu'
        for patcher in (patch.object(corsu, 'HOME', self.home), patch.object(corsu, 'DATA', data),
                        patch.object(corsu, 'STATE', data / 'installation.json'),
                        patch.object(corsu, 'DESKTOP_ENTRY_FOLDERS', self.folders)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_entries(self):
        stats = {'desktop_entries': 0}
        corsu.desktop_entries(corsu.Installer(), stats)
        return stats

    def test_display_configuration_is_corsican_in_both_places(self):
        stats = self.run_entries()
        self.assertEqual(stats['desktop_entries'], 2)
        kcm = entries(self.home / '.local/share/applications/kcm_kscreen.desktop')['Desktop Entry']
        self.assertEqual(kcm['Name[co]'], "Cunfigurazione di l'affissere")
        # Everything else of the entry stays as the system wrote it.
        for key in ('Exec', 'Icon', 'NoDisplay', 'Name', 'Name[de]', 'Name[fr]', 'X-KDE-Keywords'):
            self.assertEqual(kcm[key], entries(self.system / 'applications/kcm_kscreen.desktop')['Desktop Entry'][key])
        shortcuts = entries(self.home / '.local/share/kglobalaccel/org.kde.kscreen.desktop')
        self.assertEqual(shortcuts['Desktop Entry']['Name[co]'], "Cunfigurazione di l'affissere")
        self.assertEqual(shortcuts['Desktop Action ShowOSD']['Name[co]'], "Cambià l'affissaghju")
        self.assertEqual(shortcuts['Desktop Action ShowOSD']['X-KDE-Shortcuts'], 'Display,Meta+P')

    def test_untranslated_text_falls_back_to_french_not_english(self):
        self.run_entries()
        kcm = entries(self.home / '.local/share/applications/kcm_kscreen.desktop')['Desktop Entry']
        self.assertEqual(kcm['Comment[co]'], kcm['Comment[fr]'])
        other = entries(self.home / '.local/share/kglobalaccel/org.kde.kscreen.desktop')['Desktop Action Other']
        self.assertEqual(other['Name[co]'], 'Basculer une chose inconnue')

    def test_file_without_corsican_is_left_to_the_system(self):
        self.run_entries()
        self.assertFalse((self.home / '.local/share/applications/zzyzx.desktop').exists())

    def test_rerun_is_stable_and_keeps_a_programs_own_corsican(self):
        self.run_entries()
        first = (self.home / '.local/share/kglobalaccel/org.kde.kscreen.desktop').read_text(encoding='utf-8')
        self.run_entries()
        self.assertEqual((self.home / '.local/share/kglobalaccel/org.kde.kscreen.desktop').read_text(encoding='utf-8'),
                         first)
        # A Corsican text shipped by the program itself is not replaced by the French fallback.
        (self.system / 'applications/kcm_kscreen.desktop').write_text(
            KCM.replace('Comment=Manage', 'Comment[co]=Testu di u prugramma\nComment=Manage'), encoding='utf-8')
        shutil.rmtree(self.home)
        self.run_entries()
        kcm = entries(self.home / '.local/share/applications/kcm_kscreen.desktop')['Desktop Entry']
        self.assertEqual(kcm['Comment[co]'], 'Testu di u prugramma')

    def test_uninstall_gives_kde_its_files_back(self):
        self.run_entries()
        with patch.object(corsu, 'PLATFORM', 'linux'), redirect_stdout(io.StringIO()):
            corsu.uninstall()
        self.assertFalse((self.home / '.local/share/kglobalaccel/org.kde.kscreen.desktop').exists())
        self.assertFalse((self.home / '.local/share/applications/kcm_kscreen.desktop').exists())

    @unittest.skipUnless(shutil.which('kreadconfig6'), 'KDE Frameworks 6 (kreadconfig6) not installed')
    def test_kde_reads_corsican_then_french(self):
        # KConfig, as KDE reads these files with LANGUAGE=co:fr: [co] when present, otherwise the untranslated
        # (English) text, never [fr]. Hence the French fallback written as [co].
        self.run_entries()
        environment = {**os.environ, 'HOME': str(self.home), 'LANG': 'en_US.UTF-8', 'LANGUAGE': 'co:fr'}

        def read(path, group):
            return subprocess.run(['kreadconfig6', '--file', str(path), '--group', group, '--key', 'Name'],
                                  capture_output=True, text=True, check=True, env=environment).stdout.strip()
        shortcuts = self.home / '.local/share/kglobalaccel/org.kde.kscreen.desktop'
        self.assertEqual(read(shortcuts, 'Desktop Action ShowOSD'), "Cambià l'affissaghju")
        self.assertEqual(read(shortcuts, 'Desktop Action Other'), 'Basculer une chose inconnue')
        self.assertEqual(read(self.system / 'kglobalaccel/org.kde.kscreen.desktop', 'Desktop Action ShowOSD'),
                         'Switch Display')


if __name__ == '__main__':
    unittest.main()
