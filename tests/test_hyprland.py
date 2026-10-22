"""The optional Hyprland parts (src/apps/hyprland.py) in a throwaway home folder: detection, the language and the
desktop profile chosen apart, switching on twice, switching off and giving back only what is still Corsu's, updates
that keep the person's changes, putting Corsu's look back, and Plasma's files never touched.

Nothing here runs Hyprland or Noctalia: their versions come from an injected runner (or tiny scripts on PATH), and
Corsu's templates from the stand-ins in tests/fixtures/hyprland until src/hyprland/ has the real ones."""
import io
import json
import os
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

import corsu
import apps
from apps import hyprland, settings
import app
import installer

FIXTURES = Path(__file__).resolve().parent / 'fixtures/hyprland'
COMPATIBLE = {'Hyprland': 'Hyprland 0.56.2 built from branch v0.56.2 at commit 0000000',
              'noctalia': 'noctalia 5.3.0', 'uwsm': 'uwsm 0.27.1'}


def runner(answers):
    """A stand-in for running `Hyprland --version`, `noctalia --version`, `uwsm version`."""
    def run(command):
        return answers.get(command[0])
    return run


class Home(unittest.TestCase):
    """A home folder with Plasma's files in it, Corsu's record in it, and the templates from the stand-ins."""

    answers = COMPATIBLE

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.home = Path(self.directory.name) / 'casa'
        self.config = self.home / '.config'
        self.templates = Path(self.directory.name) / 'templates'
        shutil.copytree(FIXTURES, self.templates)
        self.assets = Path(self.directory.name) / 'noctalia-assets'
        (self.assets / 'translations').mkdir(parents=True)
        for name in ('emoji.json', 'fonts/noctalia-tabler.ttf', 'templates/builtin.toml'):
            (self.assets / name).parent.mkdir(parents=True, exist_ok=True)
            (self.assets / name).write_text('')
        (self.assets / 'translations/en.json').write_text(json.dumps(
            {'bar': {'clock': 'Clock', 'battery': 'Battery', 'volume': 'Volume'}, 'settings': {'title': 'Settings'}}))
        (self.assets / 'translations/fr.json').write_text(json.dumps(
            {'bar': {'battery': 'Batterie', 'volume': ''}, 'old': {'gone': 'Disparu'}}))
        self.portal = Path(self.directory.name) / 'hyprland.portal'
        self.portal.write_text('[portal]\n')
        self.applications = Path(self.directory.name) / 'applications'
        self.applications.mkdir()
        self.run_answers = dict(self.answers)
        self.stack = ExitStack()
        for target, name, value in ((corsu, 'HOME', self.home), (corsu, 'CONFIG', self.config),
                                    (corsu, 'DATA', self.home / '.local/share/corsu'),
                                    (corsu, 'STATE', self.home / '.local/share/corsu/installation.json'),
                                    (corsu, 'PLATFORM', 'linux'), (hyprland, 'TEMPLATES', self.templates),
                                    (hyprland, 'NOCTALIA_ASSETS', self.assets), (hyprland, 'PORTAL_FILES', (self.portal,)),
                                    (hyprland, 'RUN', runner(self.run_answers)), (hyprland, 'system', lambda: None),
                                    (apps, 'APPLICATION_DIRS', (self.applications,)),
                                    (corsu, 'running_executables', lambda: set())):
            self.stack.enter_context(patch.object(target, name, value))
        self.stack.enter_context(patch.dict(hyprland.CACHE, {'key': None, 'time': 0.0, 'value': None}))
        self.stack.enter_context(patch.dict(os.environ, {'LANGUAGE': '', 'LC_ALL': '', 'LC_MESSAGES': '',
                                                         'LANG': 'fr_FR.UTF-8', 'CORSU_LANG': 'en'}))
        self.output = io.StringIO()
        self.stack.enter_context(redirect_stdout(self.output))
        self.plasma = self.plasma_files()
        self.noctalia = self.config / 'noctalia'

    def tearDown(self):
        self.stack.close()
        self.directory.cleanup()

    def plasma_files(self):
        files = {'kdeglobals': '[General]\nColorScheme=BreezeDark\n', 'gtk-3.0/settings.ini': '[Settings]\ngtk-theme-name=Breeze\n',
                 'plasma-workspace/env/corsu.sh': '#!/bin/sh\nexport LANGUAGE=co:fr\n',
                 'mimeapps.list': '[Default Applications]\ntext/html=firefox.desktop\n',
                 'plasma-localerc': '[Translations]\nLANGUAGE=co:fr\n'}
        for name, text in files.items():
            (self.config / name).parent.mkdir(parents=True, exist_ok=True)
            (self.config / name).write_text(text)
        return {name: (self.config / name).read_bytes() for name in files}

    def assertPlasmaUntouched(self):
        for name, data in self.plasma.items():
            self.assertEqual((self.config / name).read_bytes(), data, name)

    def detect_again(self, **answers):
        self.run_answers.clear()
        self.run_answers.update(answers)
        hyprland.CACHE.update(key=None, time=0.0, value=None)

    def gui_settings(self, text='[shell]\nlang = "it"\n\n[theme]\ncustom_palette = "Gruvbox"\n\n[bar.default]\n'
                                'position = "bottom"\n\n[widget.clock]\nformat = "HH:mm"\n'):
        """What Noctalia's Settings window saved (it wins over every layer)."""
        path = self.home / '.local/state/noctalia/settings.toml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def state(self):
        return corsu.load_state()

    def files(self):
        """Every file under the home folder but Corsu's own data: {relative path: bytes}."""
        return {str(path.relative_to(self.home)): path.read_bytes() for path in sorted(self.home.rglob('*'))
                if path.is_file() and '.local/share/corsu' not in str(path)}


class Detection(Home):
    def test_absent_hyprland_is_not_offered_and_says_why(self):
        self.detect_again()
        self.assertEqual(hyprland.Language().find(), [])
        self.assertEqual(hyprland.Profile().find(), [])
        self.assertNotIn('hyprland', apps.found())
        why = hyprland.unavailable()
        self.assertIn('does not install desktops', why['en'])
        self.assertIn('n\'installe pas de bureau', why['fr'])
        self.assertIn('ùn stalla micca', why['co'])
        self.portal.unlink()
        self.detect_again()
        self.assertEqual(hyprland.summary(), 'Hyprland — not installed: Hyprland, Noctalia, uwsm, '
                                             'xdg-desktop-portal-hyprland. Not offered: Corsu does not install desktops.')

    def test_too_old_hyprland_is_found_but_left_alone(self):
        self.detect_again(Hyprland='Hyprland 0.54.3', noctalia='noctalia 5.3.0', uwsm='uwsm 0.27.1')
        [session, noctalia] = hyprland.Language().find()
        self.assertFalse(session.usable)
        self.assertIn('0.54.3 is too old', session.reason)
        self.assertTrue(noctalia.usable)  # Noctalia's own language does not depend on Hyprland's version
        [config, look] = hyprland.Profile().find()
        self.assertFalse(config.usable)
        self.assertIn('0.55', hyprland.unavailable()['en'])

    def test_compatible_versions(self):
        found = hyprland.detect()
        self.assertEqual(found, {'hyprland': '0.56.2', 'noctalia': '5.3.0', 'uwsm': '0.27.1', 'portal': True})
        self.assertEqual(hyprland.verdict(found), {'hyprland': 'ok', 'noctalia': 'ok', 'uwsm': 'ok', 'portal': 'ok'})
        self.assertIsNone(hyprland.unavailable())
        self.assertTrue(all(item.usable for item in hyprland.Language().find() + hyprland.Profile().find()))
        self.assertEqual(hyprland.Language().find()[1].coverage, '2/4')
        self.assertEqual(sorted(name for name in apps.found() if name.startswith('hyprland')), ['hyprland', 'hyprland-profile'])
        self.assertEqual(hyprland.summary(), 'Hyprland — Hyprland 0.56.2, Noctalia 5.3.0, uwsm 0.27.1, '
                                             'xdg-desktop-portal-hyprland. Compatible with Corsu.')

    def test_other_noctalia_and_missing_uwsm(self):
        self.detect_again(Hyprland='Hyprland 0.56.2', noctalia='noctalia 6.0.1')
        [session, noctalia] = hyprland.Language().find()
        self.assertIn('uwsm is not installed', session.reason)
        self.assertIn('only knows Noctalia 5', noctalia.reason)

    def test_real_commands_on_path(self):
        """The default runner, with tiny scripts standing for the programs."""
        folder = Path(self.directory.name) / 'bin'
        folder.mkdir()
        for name, text in (('Hyprland', 'Hyprland 0.55.0 built from branch main'), ('noctalia', 'noctalia v5.3.0')):
            (folder / name).write_text(f'#!/bin/sh\necho "{text}"\n')
            (folder / name).chmod(0o755)
        with patch.dict(os.environ, {'PATH': str(folder)}):
            found = hyprland.detect(hyprland.default_run)
        self.assertEqual((found['hyprland'], found['noctalia'], found['uwsm']), ('0.55.0', '5.3.0', None))

    def test_versions_from_hyprland_system(self):
        """src/hyprland_system.py's versions() (merged from branch hypr-a) with the same injected runner."""
        import hyprland_system
        with patch.object(hyprland, 'system', lambda: hyprland_system):
            found = hyprland.detect()
        self.assertEqual((found['hyprland'], found['noctalia']), ('0.56.2', '5.3.0'))

    def test_windows_and_macos_never_see_it(self):
        with patch.object(corsu, 'PLATFORM', 'windows'):
            self.assertEqual(hyprland.Language().find(), [])
            self.assertIsNone(hyprland.unavailable())
            self.assertEqual(installer.unavailable_lines([]), [])


class Choices(Home):
    def test_profile_is_never_ticked_by_default(self):
        self.assertTrue(apps.opt_in('hyprland-profile'))
        self.assertFalse(apps.opt_in('hyprland'))
        answers = iter([''])
        with patch.object(corsu, 'STATE', self.home / 'none.json'), patch('builtins.input', lambda prompt: next(answers)):
            chosen = installer.choose(['firefox', 'hyprland', 'hyprland-profile'])
        self.assertEqual(chosen, ['firefox', 'hyprland'])
        self.assertIn('[ ] 3.', self.output.getvalue())

    def test_first_installation_without_a_list_leaves_the_profile_out(self):
        seen = {}
        with patch.object(installer, 'available_components', lambda: ['hyprland', 'hyprland-profile']), \
                patch.object(installer, 'discord_location', lambda: None), \
                patch.object(installer, 'show_plan', lambda components, location: seen.setdefault('plan', components)):
            self.assertEqual(installer.main(['--dry-run']), 0)
        self.assertEqual(seen['plan'], ['hyprland'])

    def test_missing_hyprland_is_explained_not_offered(self):
        self.detect_again()
        self.assertEqual(installer.unavailable_lines([]), [f'Hyprland: {hyprland.unavailable()["en"]}'])
        with patch.object(installer, 'available_components', lambda: []), \
                patch.object(installer, 'discord_location', lambda: None), \
                patch('sys.stderr', io.StringIO()) as error, self.assertRaises(SystemExit):
            installer.main(['--dry-run', '--components', 'hyprland-profile'])
        self.assertIn('Corsu does not install desktops', error.getvalue())

    def test_plan_names_the_files(self):
        installer.show_plan(['hyprland', 'hyprland-profile'], None)
        plan = self.output.getvalue()
        self.assertIn('env-hyprland', plan)
        self.assertIn('user.lua stays yours', plan)
        self.assertIn('hyprland-portals.conf', plan)
        self.assertIn('00-corsu-language.toml', plan)


class Language(Home):
    def test_language_only_writes_no_profile_file(self):
        corsu.install(['hyprland'])
        env = (self.config / 'uwsm/env-hyprland').read_text()
        assets = corsu.DATA / 'noctalia/assets'
        self.assertIn('# corsu:begin language\n', env)
        # The person's languages from Plasma's settings (co:fr), then English.
        self.assertIn('export LANGUAGE=co:fr:en\n', env)
        self.assertIn('then fr, en for texts not translated yet', env)
        self.assertIn(f'export NOCTALIA_ASSETS_DIR={assets}\n', env)
        self.assertNotIn('# corsu:begin profile', env)
        # Corsican where the English is unchanged, French for a text whose English changed, nothing empty or obsolete.
        self.assertEqual(json.loads((assets / 'translations/co.json').read_text()),
                         {'bar': {'clock': 'Ora', 'battery': 'Batterie'}, 'settings': {'title': 'Parametri'}})
        self.assertEqual((assets / 'translations/fr.json').resolve(), self.assets / 'translations/fr.json')
        self.assertEqual((assets / 'fonts').resolve(), self.assets / 'fonts')
        self.assertTrue(all((assets / name).exists() for name in hyprland.ASSET_ROOT))
        self.assertEqual((self.noctalia / '00-corsu-language.toml').read_bytes(),
                         (FIXTURES / 'noctalia/00-corsu-language.toml').read_bytes())
        self.assertFalse((self.noctalia / '00-corsu-profile.toml').exists())
        self.assertFalse((self.config / 'hypr').exists())
        self.assertFalse((self.config / 'xdg-desktop-portal').exists())
        result = self.state()['results']['hyprland']
        self.assertEqual(result['activation'], 'active')
        self.assertEqual(self.state()['components'], ['hyprland'])
        self.assertPlasmaUntouched()

    def test_session_languages_without_plasma(self):
        (self.config / 'plasma-localerc').unlink()
        self.assertEqual(hyprland.language_value(), 'co:fr_FR:en')

    def test_switching_on_twice_changes_nothing(self):
        corsu.install(['hyprland'])
        before, records = self.files(), self.state()['files']
        corsu.install(['hyprland'])
        corsu.enable(['hyprland'])
        self.assertEqual(self.files(), before)
        self.assertEqual(self.state()['files'], records)
        self.assertEqual((self.config / 'uwsm/env-hyprland').read_text().count('LANGUAGE='), 1)

    def test_switching_off_gives_back_existing_files_byte_for_byte(self):
        env = self.config / 'uwsm/env-hyprland'
        env.parent.mkdir(parents=True)
        env.write_text('# mine\nexport XCURSOR_SIZE=24\n')
        original_env = env.read_bytes()
        gui = self.gui_settings()
        original_gui = gui.read_bytes()
        corsu.install(['hyprland'])
        corsu.disable(['hyprland'])
        self.assertEqual(env.read_bytes(), original_env)
        self.assertEqual(gui.read_bytes(), original_gui)
        self.assertFalse((self.noctalia / '00-corsu-language.toml').exists())
        self.assertEqual(self.state()['results']['hyprland']['activation'], 'inactive')
        corsu.enable(['hyprland'])
        self.assertIn('export LANGUAGE=co', env.read_text())
        corsu.uninstall()
        self.assertEqual(env.read_bytes(), original_env)
        self.assertEqual(gui.read_bytes(), original_gui)
        self.assertPlasmaUntouched()

    def test_a_file_corsu_created_goes_when_switched_off(self):
        corsu.install(['hyprland'])
        self.assertTrue((self.config / 'uwsm/env-hyprland').exists())
        corsu.disable(['hyprland'])
        self.assertFalse((self.config / 'uwsm/env-hyprland').exists())

    def test_no_assets_variable_without_noctalia(self):
        self.detect_again(Hyprland='Hyprland 0.56.2', uwsm='uwsm 0.27.1')
        corsu.install(['hyprland'])
        env = (self.config / 'uwsm/env-hyprland').read_text()
        self.assertIn('export LANGUAGE=', env)
        self.assertNotIn('NOCTALIA_ASSETS_DIR', env)
        self.assertFalse((corsu.DATA / 'noctalia').exists())

    def test_incomplete_noctalia_assets_never_named(self):
        (self.assets / 'emoji.json').unlink()
        corsu.install(['hyprland'])
        self.assertNotIn('NOCTALIA_ASSETS_DIR', (self.config / 'uwsm/env-hyprland').read_text())
        self.assertIn('stays in English', self.output.getvalue())

    def test_the_bundle_stays_when_switched_off(self):
        """A running Noctalia's lock screen reloads the language from it (LOADING.md)."""
        corsu.install(['hyprland'])
        corsu.disable(['hyprland'])
        self.assertTrue((corsu.DATA / 'noctalia/assets/translations/co.json').exists())

    def test_switching_off_keeps_the_persons_later_changes(self):
        corsu.install(['hyprland'])
        env = self.config / 'uwsm/env-hyprland'
        env.write_text(env.read_text() + 'export MOZ_ENABLE_WAYLAND=1\n')  # outside Corsu's block
        layer = self.noctalia / '00-corsu-language.toml'
        layer.write_text('[shell]\nlang = "it"\n')
        corsu.disable(['hyprland'])
        self.assertEqual(env.read_text(), 'export MOZ_ENABLE_WAYLAND=1\n')
        self.assertEqual(layer.read_text(), '[shell]\nlang = "it"\n')

    def test_a_block_edited_inside_is_left_and_said(self):
        corsu.install(['hyprland'])
        env = self.config / 'uwsm/env-hyprland'
        env.write_text(env.read_text().replace('export LANGUAGE=co:fr:en', 'export LANGUAGE=co:it'))
        corsu.install(['hyprland'])
        self.assertIn('export LANGUAGE=co:it', env.read_text())
        self.assertIn('block changed since, left as it is', self.output.getvalue())
        corsu.disable(['hyprland'])
        self.assertIn('export LANGUAGE=co:it', env.read_text())


class Profile(Home):
    def test_profile_only_writes_no_translation(self):
        corsu.install(['hyprland-profile'])
        modules = self.config / 'hypr/corsu'
        self.assertEqual(sorted(path.name for path in modules.iterdir()), ['init.lua', 'keys.lua', 'machine.lua'])
        self.assertEqual((self.config / 'hypr/hyprland.lua').read_bytes(), (FIXTURES / 'config/hyprland.lua').read_bytes())
        self.assertFalse((self.config / 'hypr/user.lua').exists())
        self.assertEqual((self.config / 'xdg-desktop-portal/hyprland-portals.conf').read_bytes(),
                         (FIXTURES / 'session/hyprland-portals.conf').read_bytes())
        self.assertTrue((self.noctalia / 'palettes/Corsu.json').exists())
        self.assertEqual((self.noctalia / '00-corsu-profile.toml').read_bytes(),
                         (FIXTURES / 'noctalia/00-corsu-profile.toml').read_bytes())
        self.assertIn(f'color_scheme_path={self.config}/qt6ct/colors/noctalia.conf',
                      (self.config / 'qt6ct/qt6ct.conf').read_text())
        self.assertFalse((self.noctalia / '00-corsu-language.toml').exists())
        self.assertFalse((corsu.DATA / 'noctalia').exists())
        self.assertFalse((self.config / 'uwsm/env-hyprland').exists())  # no profile lines without hyprland_system
        self.assertPlasmaUntouched()

    def test_existing_files_of_the_person_stay(self):
        hypr = self.config / 'hypr'
        hypr.mkdir(parents=True)
        (hypr / 'hyprland.lua').write_text('-- mine\n')
        (hypr / 'user.lua').write_text('-- my settings\n')
        portals = self.config / 'xdg-desktop-portal/hyprland-portals.conf'
        portals.parent.mkdir(parents=True)
        portals.write_text('[preferred]\ndefault=gtk\n')
        qt6ct = self.config / 'qt6ct/qt6ct.conf'
        qt6ct.parent.mkdir(parents=True)
        qt6ct.write_text('[Appearance]\nstyle=Fusion\n')
        corsu.install(['hyprland-profile'])
        self.assertEqual((hypr / 'hyprland.lua').read_text(), '-- mine\n')
        self.assertEqual(portals.read_text(), '[preferred]\ndefault=gtk\n')
        self.assertEqual(qt6ct.read_text(), '[Appearance]\nstyle=Fusion\n')
        action = self.state()['results']['hyprland-profile']['instances'][0]['action']
        self.assertIn('add require("corsu.init")', action)
        self.assertIn('yours, left as it is', action)
        corsu.disable(['hyprland-profile'])
        self.assertEqual((hypr / 'hyprland.lua').read_text(), '-- mine\n')
        self.assertEqual((hypr / 'user.lua').read_text(), '-- my settings\n')
        self.assertEqual(portals.read_text(), '[preferred]\ndefault=gtk\n')
        self.assertEqual(qt6ct.read_text(), '[Appearance]\nstyle=Fusion\n')
        self.assertFalse((hypr / 'corsu/init.lua').exists())

    def test_switching_on_twice_and_off(self):
        gui = self.gui_settings()
        original = gui.read_bytes()
        corsu.install(['hyprland-profile'])
        before, records = self.files(), self.state()['files']
        corsu.install(['hyprland-profile'])
        self.assertEqual(self.files(), before)
        self.assertEqual(self.state()['files'], records)
        (self.config / 'hypr/user.lua').write_text('-- mine\n')
        corsu.disable(['hyprland-profile'])
        self.assertEqual(gui.read_bytes(), original)  # Noctalia's Settings window choices stay
        for name in ('hypr/hyprland.lua', 'hypr/corsu/keys.lua', 'xdg-desktop-portal/hyprland-portals.conf',
                     'noctalia/00-corsu-profile.toml', 'noctalia/palettes/Corsu.json', 'qt6ct/qt6ct.conf'):
            self.assertFalse((self.config / name).exists(), name)
        self.assertEqual((self.config / 'hypr/user.lua').read_text(), '-- mine\n')
        self.assertPlasmaUntouched()

    def test_update_refreshes_unchanged_files_and_leaves_edited_ones(self):
        corsu.install(['hyprland-profile'])
        modules = self.config / 'hypr/corsu'
        (modules / 'init.lua').write_text('-- my own init\n')
        # The next release's templates.
        (self.templates / 'config/corsu/keys.lua').write_text('-- Corsu keys, next version.\nreturn {}\n')
        (self.templates / 'config/corsu/init.lua').write_text('-- Corsu init, next version.\n')
        (self.templates / 'config/corsu/rules.lua').write_text('-- new module\n')
        (self.templates / 'config/hyprland.lua').write_text('-- starter, next version\n')
        (self.templates / 'noctalia/00-corsu-profile.toml').write_text('[theme]\nmode = "light"\n')
        corsu.install(['hyprland-profile'])
        self.assertEqual((modules / 'keys.lua').read_text(), '-- Corsu keys, next version.\nreturn {}\n')
        self.assertEqual((modules / 'rules.lua').read_text(), '-- new module\n')
        self.assertEqual((modules / 'init.lua').read_text(), '-- my own init\n')
        self.assertEqual((self.noctalia / '00-corsu-profile.toml').read_text(), '[theme]\nmode = "light"\n')
        # The starter is written once and never rewritten.
        self.assertEqual((self.config / 'hypr/hyprland.lua').read_bytes(), (FIXTURES / 'config/hyprland.lua').read_bytes())
        self.assertIn(f'changed since, left as it is: {modules / "init.lua"}', self.output.getvalue())
        result = self.state()['results']['hyprland-profile']
        self.assertEqual(result['activation'], 'active')
        self.assertIn('init.lua', result['instances'][0]['action'])
        corsu.uninstall()
        self.assertEqual((modules / 'init.lua').read_text(), '-- my own init\n')
        self.assertFalse((modules / 'rules.lua').exists())

    def test_reset_look_keeps_other_settings(self):
        gui = self.gui_settings()
        original_gui = gui.read_bytes()
        corsu.install(['hyprland', 'hyprland-profile'])
        palette = self.noctalia / 'palettes/Corsu.json'
        palette.write_text('{"name": "Corsu", "primary": "#000000"}')
        layer = self.noctalia / '00-corsu-profile.toml'
        layer.write_text('[theme]\nmode = "light"\n')
        (self.config / 'hypr/user.lua').write_text('-- mine\n')
        (self.config / 'hypr/corsu/keys.lua').write_text('-- my keys\n')
        env = (self.config / 'uwsm/env-hyprland').read_bytes()
        language = (self.noctalia / '00-corsu-language.toml').read_bytes()
        with patch.object(corsu, 'lock', lambda action: ExitStack()):
            self.assertEqual(installer.main(['--hyprland-reset-look']), 0)
        self.assertEqual(palette.read_bytes(), (FIXTURES / 'noctalia/palettes/Corsu.json').read_bytes())
        self.assertEqual(layer.read_bytes(), (FIXTURES / 'noctalia/00-corsu-profile.toml').read_bytes())
        kept = {path.name: path.read_text() for path in (corsu.DATA / 'backups/hyprland-reset').rglob('*') if path.is_file()}
        self.assertEqual(kept, {'Corsu.json': '{"name": "Corsu", "primary": "#000000"}',
                                '00-corsu-profile.toml': '[theme]\nmode = "light"\n'})
        # Never edited: Noctalia's Settings window choices, Hyprland's files, the language.
        self.assertEqual(gui.read_bytes(), original_gui)
        self.assertEqual((self.config / 'hypr/user.lua').read_text(), '-- mine\n')
        self.assertEqual((self.config / 'hypr/corsu/keys.lua').read_text(), '-- my keys\n')
        self.assertEqual((self.config / 'uwsm/env-hyprland').read_bytes(), env)
        self.assertEqual((self.noctalia / '00-corsu-language.toml').read_bytes(), language)
        corsu.disable(['hyprland-profile'])
        self.assertFalse(palette.exists())
        self.assertTrue((self.noctalia / '00-corsu-language.toml').exists())
        self.assertPlasmaUntouched()

    def test_reset_needs_the_profile(self):
        self.assertFalse(hyprland.reset_look())
        self.assertIn('not switched on', self.output.getvalue())

    def test_session_values_from_hyprland_system(self):
        (self.applications / hyprland.NOCTALIA_ENTRY).write_text('[Desktop Entry]\nName=Noctalia\nExec=noctalia\n')

        class System:
            @staticmethod
            def env_block(env, root='/', home=None, cards=None):
                return ('# corsu:begin\n# Written by Corsu for the Hyprland session only; Plasma does not read this file.\n'
                        f'export LANGUAGE=co:{env["LANG"][:2]}\nexport QT_QPA_PLATFORMTHEME=qt6ct\n# corsu:end\n')

            @staticmethod
            def gpus(root='/'):
                return []

            @staticmethod
            def keyboard(root='/', home=None):
                return {'layout': 'fr', 'variant': 'oss', 'model': '', 'options': '', 'source': 'localectl'}

            @staticmethod
            def outputs(cards, home=None):
                return [{'name': 'OUT-1', 'plasma': 1.5, 'suggested': 1.25}]

            @staticmethod
            def portals_conf(root='/'):
                return '[preferred]\ndefault=hyprland;gtk\n'

            @staticmethod
            def hyprland_only_entry(text):
                return text + 'OnlyShowIn=Hyprland;\n'

        with patch.object(hyprland, 'system', lambda: System):
            corsu.install(['hyprland', 'hyprland-profile'])
        env = (self.config / 'uwsm/env-hyprland').read_text()
        self.assertEqual(env.count('# corsu:begin'), 2)
        self.assertEqual(env.count('LANGUAGE='), 1)  # only the language part's
        self.assertIn('# corsu:begin profile\nexport QT_QPA_PLATFORMTHEME=qt6ct\n# corsu:end profile\n', env)
        machine = (self.config / 'hypr/corsu/machine.lua').read_text()
        self.assertIn('keyboard = { layout = "fr", variant = "oss", model = "", options = "" },', machine)
        self.assertIn('monitors = { { output = "OUT-1", mode = "preferred", position = "auto", scale = 1.5 } },', machine)
        entry = self.home / '.local/share/applications' / hyprland.NOCTALIA_ENTRY
        self.assertTrue(entry.read_text().endswith('OnlyShowIn=Hyprland;\n'))
        corsu.disable(['hyprland-profile'])
        env = (self.config / 'uwsm/env-hyprland').read_text()
        self.assertNotIn('QT_QPA_PLATFORMTHEME', env)
        self.assertIn('export LANGUAGE=', env)
        self.assertFalse(entry.exists())
        corsu.disable(['hyprland'])
        self.assertFalse((self.config / 'uwsm/env-hyprland').exists())


class RealTemplates(Home):
    """The same round trip with the real src/hyprland/ (branch hyprland) instead of the stand-ins."""

    def setUp(self):
        super().setUp()
        self.stack.enter_context(patch.object(hyprland, 'TEMPLATES', corsu.SRC / 'hyprland'))

    def test_enable_twice_and_disable(self):
        if not (corsu.SRC / 'hyprland/config/corsu').is_dir():
            self.skipTest('src/hyprland has no templates in this copy')
        gui = self.gui_settings()
        original = gui.read_bytes()
        corsu.install(['hyprland', 'hyprland-profile'])
        before, records = self.files(), self.state()['files']
        corsu.install(['hyprland', 'hyprland-profile'])
        self.assertEqual(self.files(), before)
        self.assertEqual(self.state()['files'], records)
        self.assertTrue((self.config / 'hypr/corsu/init.lua').exists())
        self.assertTrue((self.config / 'hypr/corsu/machine.lua').exists())
        self.assertTrue((self.noctalia / 'palettes/Corsu-Maquis.json').exists())
        self.assertNotIn('@CONFIG_HOME@', (self.config / 'qt6ct/qt6ct.conf').read_text())
        self.assertIn('lang = "co"', (self.noctalia / '00-corsu-language.toml').read_text())
        self.assertTrue((corsu.DATA / 'noctalia/assets/translations/co.json').exists())
        self.assertEqual({result['activation'] for result in self.state()['results'].values()}, {'active'})
        corsu.disable(['hyprland', 'hyprland-profile'])
        self.assertEqual(gui.read_bytes(), original)
        self.assertEqual([path for path in self.config.rglob('*') if path.is_file() and 'hypr' in path.parts
                          or path.name.startswith('00-corsu')], [])
        self.assertFalse((self.config / 'uwsm/env-hyprland').exists())
        self.assertPlasmaUntouched()


class Window(Home):
    def setUp(self):
        super().setUp()
        for item in (patch.object(app, 'detected', lambda: set(installer.available_components())),
                     patch.object(installer, 'available_components', lambda: apps.found())):
            self.stack.enter_context(item)

    def items(self):
        return {item['name']: item for item in app.snapshot()['items']}

    def test_missing_hyprland_is_shown_unavailable(self):
        self.detect_again()
        items = self.items()
        self.assertIn('ùn stalla micca', items['hyprland']['unavailable']['co'])
        self.assertFalse(items['hyprland-profile']['installed'])
        self.assertTrue(items['hyprland-profile']['opt_in'])
        with patch.object(corsu, 'PLATFORM', 'windows'):
            self.assertNotIn('hyprland', self.items())

    def test_found_installed_and_reset(self):
        items = self.items()
        self.assertNotIn('unavailable', items['hyprland'])
        self.assertIn('Hyprland 0.56.2, Noctalia 5.3.0', items['hyprland']['text']['fr'][1])
        corsu.install(['hyprland-profile'])
        items = self.items()
        profile = items['hyprland-profile']
        self.assertTrue(profile['on'])
        self.assertTrue(profile['reset'])
        self.assertEqual(profile['activation'], 'active')
        self.assertFalse(items['hyprland']['installed'])

    def test_status_command(self):
        corsu.install(['hyprland'])
        with patch.object(corsu, 'firefox_profile', lambda: None):
            corsu.status()
        report = json.loads(self.output.getvalue()[self.output.getvalue().index('{\n'):])
        self.assertEqual(report['hyprland']['found']['hyprland'], '0.56.2')
        self.assertTrue(report['hyprland']['parts']['hyprland']['on'])
        self.assertFalse(report['hyprland']['parts']['hyprland-profile']['installed'])

    def test_status_carries_the_checks(self):
        class System:
            @staticmethod
            def checks(home=None):
                return [('warning', 'only the "Hyprland" login entry')]

        with patch.object(hyprland, 'system', lambda: System):
            report = hyprland.status()
        self.assertEqual(report['checks'], [{'level': 'warning', 'text': 'only the "Hyprland" login entry'}])

    def test_page_texts(self):
        texts = (corsu.SRC / 'app/texts.js').read_text(encoding='utf-8')
        self.assertEqual(texts.count('hyprland_reset_look:'), 3)
        self.assertEqual(texts.count('opt_in_hint:'), 3)
        script = (corsu.SRC / 'app/app.js').read_text(encoding='utf-8')
        self.assertIn('/api/hyprland-reset', script)
        self.assertIn('!item.opt_in && !item.unavailable', script)


@unittest.skipUnless(shutil.which('node'), 'node is not installed')
class Page(unittest.TestCase):
    """The page's own code (app.js) on the small DOM of tests/test_app_ui.py: the Add page shows Hyprland unavailable
    with why and leaves the profile unticked; the installed profile's row has its reset button."""

    def test_rows(self):
        import copy
        import subprocess
        from tests import test_app_ui as ui
        fixture = copy.deepcopy(ui.FIXTURE)
        fixture['platform'] = 'linux'
        why = {'co': 'Hyprland ùn hè micca stallatu.', 'fr': "Hyprland n'est pas installé.", 'en': 'Hyprland is not installed.'}
        common = {'switchable': False, 'on': False, 'activation': None, 'instances': [], 'coverage': None,
                  'validation': None, 'updated': None}
        fixture['items'] += [
            {'name': 'hyprland', 'text': {lang: ['Hyprland', 'detail'] for lang in why}, 'installed': False,
             'unavailable': why, **common},
            {'name': 'optional', 'text': {lang: ['Optional', 'detail'] for lang in why}, 'installed': False, 'opt_in': True,
             **common},
            {'name': 'hyprland-profile', 'text': {lang: ['Profile', 'detail'] for lang in why}, 'installed': True,
             **{**common, 'switchable': True, 'on': True, 'activation': 'active'}, 'opt_in': True, 'reset': True}]
        with tempfile.TemporaryDirectory() as folder:
            harness, data = Path(folder) / 'harness.js', Path(folder) / 'fixture.json'
            harness.write_text(ui.HARNESS, encoding='utf-8')
            data.write_text(json.dumps(fixture), encoding='utf-8')
            done = subprocess.run(['node', str(harness), str(ui.PAGE), str(data)], capture_output=True, text=True,
                                  encoding='utf-8', timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        result = json.loads(done.stdout)
        add = {row['name']: row for row in result['add']}
        self.assertFalse(add['hyprland']['checked'])
        self.assertIn('Not available here: Hyprland is not installed', add['hyprland']['text'])
        self.assertIn('off', add['hyprland']['class'])
        self.assertFalse(add['optional']['checked'])
        self.assertIn('Optional: tick it only if you want it.', add['optional']['text'])
        self.assertTrue(add['discord']['checked'])  # an ordinary program found stays ticked
        profile = next(row for row in result['programs'] if row['name'] == 'hyprland-profile')
        self.assertTrue(profile['checked'])
        self.assertIn("Put Corsu's look back", profile['text'])


class Settings(unittest.TestCase):
    """The two kinds of value apps/settings.py gained for Hyprland."""

    def test_block(self):
        text = 'export A=1\n'
        added = settings._block_put(text, 'language', 'export LANGUAGE=co\n')
        self.assertEqual(added, 'export A=1\n# corsu:begin language\nexport LANGUAGE=co\n# corsu:end language\n')
        self.assertEqual(settings._block_get(added, 'language'), 'export LANGUAGE=co\n')
        self.assertIsNone(settings._block_get(added, 'profile'))
        self.assertEqual(settings._block_put(added, 'language', None), text)
        self.assertEqual(settings._block_put(added + 'export B=2\n', 'language', None), 'export A=1\nexport B=2\n')
        self.assertEqual(settings._block_put(settings._block_put(added, 'language', 'x'), 'language', None), text)

    def test_toml(self):
        text = 'top = 1\n\n[general]\nlanguage = "fr"   \nother=2\n\n[bar]\nheight = 3\n'
        spec = ['general', 'language']
        self.assertEqual(settings._toml_get(text, spec), '"fr"')
        changed = settings._toml_put(text, spec, '"co"')
        self.assertIn('language = "co"\n', changed)
        self.assertEqual(settings._toml_put(changed, spec, '"fr"').replace('"fr"\n', '"fr"   \n'), text)
        added = settings._toml_put(text, ['colors', 'scheme'], '"Corsu"')
        self.assertTrue(added.endswith('height = 3\n\n[colors]\nscheme = "Corsu"\n'))
        self.assertEqual(settings._toml_put(added, ['colors', 'scheme'], None), text)
        inserted = settings._toml_put(text, ['general', 'dark'], 'true')
        self.assertIn('other=2\ndark = true\n\n[bar]', inserted)
        self.assertEqual(settings._toml_put(inserted, ['general', 'dark'], None), text)
        self.assertIsNone(settings._toml_get(text, ['bar', 'language']))
        self.assertEqual(settings._toml_put('', ['', 'x'], '1'), 'x = 1\n')
        listed = '[bar]\nend = ["a",\n       "b]"]\nheight = 3\n'
        self.assertEqual(settings._toml_put(listed, ['bar', 'end'], None), '[bar]\nheight = 3\n')


class Templates(unittest.TestCase):
    """Corsu's Hyprland templates and the stand-ins carry no personal path, name or identifier: machine values come
    from detection when the profile is switched on."""

    PERSONAL = re.compile(r'/home/[a-z]|/Users/|(?<![a-z])kalt\b|coldaslava|@gmail|\b(?:DP|HDMI|eDP)-\d|/dev/dri/card\d|'
                          r'pci-0000|by-path|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}', re.I)

    def test_no_personal_values(self):
        folders = [FIXTURES, corsu.SRC / 'hyprland']
        files = [path for folder in folders if folder.exists() for path in folder.rglob('*') if path.is_file()]
        files.append(corsu.SRC / 'apps/hyprland.py')
        for path in files:
            text = path.read_text(encoding='utf-8', errors='replace')
            if path.name == 'README.md':
                text = re.sub(r'`[^`]*`', '', text)  # the contract may name places in code spans
            self.assertIsNone(self.PERSONAL.search(text), f'{path}: {self.PERSONAL.search(text)}')


if __name__ == '__main__':
    unittest.main()
