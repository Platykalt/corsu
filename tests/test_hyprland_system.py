"""Detection and session files for the Hyprland component (src/hyprland_system.py).

SIMULATED: every machine here is a fake /sys, /dev and /etc tree in a throwaway folder, and commands are answered by
a fake runner; nothing reads or changes the computer running the tests. The laptop case copies what was read on the
maintainer's Acer Predator PHN18-72 on 22 October 2026 (internal panel on the NVIDIA card).
"""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import hyprland_system as hs


def edid(width_mm, height_mm):
    """A 128-byte EDID with one detailed timing carrying the image size in millimetres."""
    data = bytearray(128)
    data[0:8] = b'\x00\xff\xff\xff\xff\xff\xff\x00'
    data[21], data[22] = width_mm // 10, height_mm // 10
    data[54], data[55] = 0x01, 0x1d
    data[66], data[67] = width_mm & 0xFF, height_mm & 0xFF
    data[68] = (width_mm >> 8) << 4 | (height_mm >> 8)
    return bytes(data)


class Machine:
    """A fake root: add_gpu() makes /sys/devices/.../<slot>, /sys/class/drm/cardN and /dev/dri/by-path links."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp())
        self.home = self.root / 'home'
        self.home.mkdir()

    def add_gpu(self, card, slot, driver, connectors=(), boot_vga=False, by_path=True):
        if sys.platform == 'win32':
            raise unittest.SkipTest('a fake /sys needs symbolic links, which Windows restricts')
        device = self.root / 'sys/devices/pci0000:00' / slot
        (device / 'drm' / card).mkdir(parents=True)
        drivers = self.root / 'sys/bus/pci/drivers' / driver
        drivers.mkdir(parents=True, exist_ok=True)
        os.symlink(drivers, device / 'driver')
        (device / 'boot_vga').write_text('1\n' if boot_vga else '0\n')
        drm = self.root / 'sys/class/drm'
        drm.mkdir(parents=True, exist_ok=True)
        os.symlink(device / 'drm' / card, drm / card)
        os.symlink(device, device / 'drm' / card / 'device')
        for name, status, size, mode in connectors:
            folder = device / 'drm' / card / f'{card}-{name}'
            folder.mkdir()
            (folder / 'status').write_text(status + '\n')
            (folder / 'edid').write_bytes(edid(*size) if size else b'')
            (folder / 'modes').write_text(f'{mode}\n' if mode else '')
            os.symlink(folder, drm / f'{card}-{name}')
        if by_path:
            links = self.root / 'dev/dri/by-path'
            links.mkdir(parents=True, exist_ok=True)
            os.symlink(f'../{card}', links / f'pci-{slot}-card')

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


def runner(answers):
    """A fake command runner: {'program arg': output}; anything else is a missing program."""
    return lambda argv: answers.get(' '.join(argv))


INSTALLED = {
    'Hyprland --version-json': '{"branch": "v0.56.2", "version": "0.56.2", "tag": "v0.56.2", "commits": "7661"}',
    'noctalia --version': 'noctalia 5.3.0\n',
    'pacman -Q uwsm': 'uwsm 0.27.1-1\n',
    'pacman -Q xdg-desktop-portal-hyprland': 'xdg-desktop-portal-hyprland 1.4.1-2.1\n',
    'localectl status': 'System Locale: LANG=en_US.UTF-8\n    VC Keymap: fr\n   X11 Layout: fr\n',
}


def predator(machine):
    """The maintainer's laptop: Intel Arrow Lake (no screen) and NVIDIA with the 18-inch 2560x1600 panel."""
    machine.add_gpu('card1', '0000:00:02.0', 'i915', [('DP-1', 'disconnected', None, None),
                                                      ('DP-2', 'disconnected', None, None)])
    machine.add_gpu('card2', '0000:01:00.0', 'nvidia', [('DP-3', 'disconnected', None, None),
                                                        ('HDMI-A-1', 'disconnected', None, None),
                                                        ('eDP-1', 'connected', (387, 242), '2560x1600')], boot_vga=True)


class Case(unittest.TestCase):
    def setUp(self):
        self.machine = Machine()
        self.addCleanup(self.machine.cleanup)


class VersionTests(Case):
    def test_installed_versions_come_from_the_programs(self):
        self.assertEqual(hs.versions(runner(INSTALLED)),
                         {'hyprland': '0.56.2', 'noctalia': '5.3.0', 'uwsm': '0.27.1', 'xdph': '1.4.1'})

    def test_text_outputs_of_hyprland_and_hyprctl(self):
        text = 'Hyprland 0.56.2 built from branch v0.56.2 at commit efb5099 clean (nix).\nTag: v0.56.2, commits: 7661\n'
        self.assertEqual(hs.hyprland_version_from(text), '0.56.2')
        self.assertEqual(hs.hyprland_version_from('Hyprland, built from branch main\nTag: v0.55.0-12-gabc'), '0.55.0')
        self.assertIsNone(hs.hyprland_version_from(''))

    def test_package_database_when_the_program_does_not_answer(self):
        answers = {'pacman -Q hyprland': 'hyprland 0.56.2-4.1\n', 'pacman -Q noctalia': 'noctalia 1:5.3.0-1\n'}
        found = hs.versions(runner(answers))
        self.assertEqual((found['hyprland'], found['noctalia']), ('0.56.2', '5.3.0'))

    def test_missing_packages(self):
        found = hs.versions(runner({}))
        self.assertEqual(found, {'hyprland': None, 'noctalia': None, 'uwsm': None, 'xdph': None})
        verdict, reasons = hs.compatibility(found)
        self.assertEqual(verdict, 'missing')
        self.assertIn('Hyprland', reasons[0])

    def test_compatibility_range(self):
        self.assertEqual(hs.compatibility({'hyprland': '0.56.2', 'noctalia': '5.3.0'})[0], 'supported')
        self.assertEqual(hs.compatibility({'hyprland': '0.55.0', 'noctalia': '5.0.1'})[0], 'supported')
        self.assertEqual(hs.compatibility({'hyprland': '0.54.3', 'noctalia': '5.3.0'})[0], 'unsupported')
        self.assertEqual(hs.compatibility({'hyprland': '0.57.0', 'noctalia': '5.3.0'})[0], 'untested')
        self.assertEqual(hs.compatibility({'hyprland': '0.56.2', 'noctalia': '4.1.0'})[0], 'unsupported')


class GpuTests(Case):
    def test_this_laptop_panel_on_nvidia(self):
        predator(self.machine)
        cards = hs.gpus(self.machine.root)
        self.assertEqual([(gpu['card'], gpu['driver'], gpu['slot']) for gpu in cards],
                         [('card1', 'i915', '0000:00:02.0'), ('card2', 'nvidia', '0000:01:00.0')])
        self.assertEqual(cards[1]['by_path'], '/dev/dri/by-path/pci-0000:01:00.0-card')
        self.assertEqual(hs.panel_gpu(cards)['driver'], 'nvidia')
        self.assertEqual(hs.aq_drm_devices(cards), ['/dev/dri/by-path/pci-0000:01:00.0-card',
                                                    '/dev/dri/by-path/pci-0000:00:02.0-card'])
        # aquamarine already puts the panel's card first and keeps the other: no line to write.
        self.assertEqual(hs.gpu_lines(cards), [])
        [panel] = hs.outputs(cards)
        self.assertEqual((panel['name'], panel['mode'], panel['size_mm'], panel['suggested']),
                         ('eDP-1', (2560, 1600), (387, 242), 1.6))

    def test_panel_on_intel_external_on_nvidia(self):
        self.machine.add_gpu('card0', '0000:00:02.0', 'i915', [('eDP-1', 'connected', (344, 194), '1920x1080')],
                             boot_vga=True)
        self.machine.add_gpu('card1', '0000:01:00.0', 'nvidia', [('HDMI-A-1', 'connected', (600, 340), '2560x1440')])
        cards = hs.gpus(self.machine.root)
        self.assertEqual(hs.aq_drm_devices(cards)[0], '/dev/dri/by-path/pci-0000:00:02.0-card')
        self.assertEqual(len(hs.aq_drm_devices(cards)), 2, 'the external screen needs the NVIDIA card kept')
        self.assertEqual(hs.gpu_lines(cards), [])
        self.assertEqual([(item['name'], item['driver'], item['suggested']) for item in hs.outputs(cards)],
                         [('eDP-1', 'i915', 1.25), ('HDMI-A-1', 'nvidia', 1)])

    def test_boot_vga_on_nvidia_but_panel_on_intel(self):
        # aquamarine moves the card with the connected panel in front of the boot VGA card itself: nothing to write.
        self.machine.add_gpu('card0', '0000:00:02.0', 'i915', [('eDP-1', 'connected', (344, 194), '1920x1080')])
        self.machine.add_gpu('card1', '0000:01:00.0', 'nvidia', [('DP-1', 'disconnected', None, None)], boot_vga=True)
        cards = hs.gpus(self.machine.root)
        self.assertEqual(hs.aquamarine_order(cards)[0]['driver'], 'i915')
        self.assertEqual(hs.gpu_lines(cards), [])

    def test_card_without_by_path_name(self):
        predator(self.machine)
        self.machine.add_gpu('card3', '0000:05:00.0', 'amdgpu', by_path=False)
        cards = hs.gpus(self.machine.root)
        self.assertEqual(len(cards), 3)
        self.assertEqual(len(hs.aq_drm_devices(cards)), 2, 'only cards with a stable name are listed')

    def test_single_gpu(self):
        self.machine.add_gpu('card0', '0000:00:02.0', 'i915', [('eDP-1', 'connected', (300, 190), '2880x1800')],
                             boot_vga=True)
        cards = hs.gpus(self.machine.root)
        self.assertIsNone(hs.aq_drm_devices(cards))
        self.assertEqual(hs.gpu_lines(cards), [])
        self.assertEqual(hs.outputs(cards)[0]['suggested'], 2)

    def test_no_drm_at_all(self):
        self.assertEqual(hs.gpus(self.machine.root), [])
        self.assertIsNone(hs.aq_drm_devices([]))
        self.assertIsNone(hs.panel_gpu([]))


class ExplicitOrderTests(unittest.TestCase):
    """gpu_lines() with hand-made cards, where aquamarine's own choice differs from the one wanted."""

    def card(self, name, slot, panel=False, boot_vga=False):
        return {'card': name, 'driver': 'x', 'slot': slot, 'by_path': f'/dev/dri/by-path/pci-{slot}-card',
                'boot_vga': boot_vga,
                'connectors': [{'name': 'eDP-1', 'status': 'connected' if panel else 'disconnected', 'internal': True,
                                'size_mm': None, 'mode': None}]}

    def test_lines_when_needed(self):
        # Two panels counted the same: aquamarine keeps the boot VGA card, Corsu wants the first card with a panel.
        first, second = self.card('card0', '0000:00:02.0', panel=True), self.card('card1', '0000:01:00.0', panel=True,
                                                                                  boot_vga=True)
        lines = hs.gpu_lines([first, second])
        self.assertTrue(lines)
        text = '\n'.join(lines)
        self.assertIn('/dev/dri/by-path/pci-0000:00:02.0-card /dev/dri/by-path/pci-0000:01:00.0-card', text)
        self.assertIn('readlink -f', text)
        self.assertNotIn('/dev/dri/card', text)
        self.assertIn('unset AQ_DRM_DEVICES', text)


class ScaleTests(unittest.TestCase):
    def test_scales_divide_the_resolution(self):
        for width, height, mm in ((2560, 1600, (387, 242)), (1920, 1080, (344, 194)), (3840, 2160, (344, 194)),
                                  (2880, 1800, (300, 190))):
            scale = hs.suggested_scale(width, height, *mm)
            self.assertEqual(width / scale, round(width / scale))
            self.assertEqual(height / scale, round(height / scale))

    def test_unknown_size(self):
        self.assertEqual(hs.suggested_scale(1920, 1080, 0, 0), 1)
        self.assertEqual(hs.suggested_scale(1920, 1080, 1600, 900, internal=False), 1)   # a television
        self.assertEqual(hs.suggested_scale(2560, 1440, 600, 340, internal=False), 1)   # 27-inch monitor
        self.assertEqual(hs.suggested_scale(3840, 2160, 344, 194), 2.5)

    def test_edid(self):
        self.assertEqual(hs.edid_size_mm(edid(387, 242)), (387, 242))
        self.assertIsNone(hs.edid_size_mm(b''))

    def test_plasma_scale_is_read(self):
        machine = Machine()
        self.addCleanup(machine.cleanup)
        machine.write('home/.config/kwinoutputconfig.json',
                      '[{"name": "outputs", "data": [{"connectorName": "eDP-1", "scale": 1.25}]}, {"name": "setups"}]')
        self.assertEqual(hs.plasma_scales(machine.home), {'eDP-1': 1.25})
        self.assertEqual(hs.plasma_scales(machine.root), {})


class KeyboardTests(Case):
    def test_azerty_from_localectl(self):
        found = hs.keyboard(self.machine.root, self.machine.home, runner(INSTALLED))
        self.assertEqual(found, {'layout': 'fr', 'variant': '', 'model': '', 'options': '', 'source': 'localectl'})

    def test_layout_with_variant_from_plasma(self):
        self.machine.write('home/.config/kxkbrc', '[Layout]\nLayoutList=fr,us\nVariantList=oss,intl\nModel=pc105\n'
                                                  'Options=grp:alt_shift_toggle\nUse=true\n')
        found = hs.keyboard(self.machine.root, self.machine.home, runner(INSTALLED))
        self.assertEqual(found, {'layout': 'fr,us', 'variant': 'oss,intl', 'model': 'pc105',
                                 'options': 'grp:alt_shift_toggle', 'source': 'kxkbrc'})

    def test_plasma_layouts_not_in_use_are_ignored(self):
        self.machine.write('home/.config/kxkbrc', '[Layout]\nLayoutList=us\nUse=false\n')
        self.assertEqual(hs.keyboard(self.machine.root, self.machine.home, runner(INSTALLED))['layout'], 'fr')

    def test_variant_from_the_localed_file(self):
        self.machine.write('etc/X11/xorg.conf.d/00-keyboard.conf',
                           'Section "InputClass"\n        Identifier "system-keyboard"\n'
                           '        Option "XkbLayout" "fr"\n        Option "XkbVariant" "bepo"\nEndSection\n')
        found = hs.keyboard(self.machine.root, None, runner({}))
        self.assertEqual((found['layout'], found['variant'], found['source']), ('fr', 'bepo', '00-keyboard.conf'))

    def test_nothing_known(self):
        self.assertIsNone(hs.keyboard(self.machine.root, None, runner({})))


class EnvironmentTests(Case):
    def test_language_like_corsican_first(self):
        self.assertEqual(hs.language_value({'LANGUAGE': 'co:fr'}), 'co:fr')
        self.assertEqual(hs.language_value({'LANG': 'fr_FR.UTF-8'}), 'co:fr_FR')
        self.assertEqual(hs.language_value({'LANGUAGE': 'it:fr:en'}), 'co:it:fr:en')

    def test_empty_env(self):
        self.assertEqual(hs.language_value({}), 'co:fr')
        block = hs.env_block({}, self.machine.root, self.machine.home, [])
        self.assertEqual(block.splitlines()[0], hs.BEGIN)
        self.assertEqual(block.splitlines()[-1], hs.END)
        self.assertIn("export LANGUAGE=co:fr\n", block)
        self.assertNotIn('QT_QPA_PLATFORMTHEME', block)
        self.assertNotIn('AQ_DRM_DEVICES', block)
        self.assertNotIn('CURSOR', block)

    def test_this_laptop_block(self):
        predator(self.machine)
        self.machine.write(hs.QT6CT_PLUGIN, '')
        self.machine.write('etc/xdg/menus/plasma-applications.menu', '<Menu/>')
        self.machine.write('usr/share/icons/miku-cursor-linux/cursors/left_ptr', '')
        self.machine.write('home/.config/kcminputrc', '[Mouse]\ncursorSize=48\ncursorTheme=miku-cursor-linux\n')
        block = hs.env_block({'LANGUAGE': 'co:fr', 'LANG': 'en_US.UTF-8'}, self.machine.root, self.machine.home,
                             hs.gpus(self.machine.root))
        self.assertEqual(block.splitlines()[3:-1], [
            'export LANGUAGE=co:fr', 'export QT_QPA_PLATFORMTHEME=qt6ct', 'export XDG_MENU_PREFIX=plasma-',
            'export XCURSOR_THEME=miku-cursor-linux', 'export XCURSOR_SIZE=48'])

    def test_hyprcursor_theme_and_missing_theme(self):
        self.machine.write('home/.config/kcminputrc', '[Mouse]\ncursorTheme=Bibata\ncursorSize=24\n')
        self.assertIsNone(hs.cursor(self.machine.root, self.machine.home))
        self.machine.write('home/.local/share/icons/Bibata/manifest.hl', 'name = Bibata\n')
        self.machine.write('home/.local/share/icons/Bibata/cursors/left_ptr', '')
        names = dict(hs.environment({}, self.machine.root, self.machine.home))
        self.assertEqual((names['HYPRCURSOR_THEME'], names['HYPRCURSOR_SIZE'], names['XCURSOR_THEME']),
                         ('Bibata', '24', 'Bibata'))

    def test_values_are_quoted_for_the_shell(self):
        self.machine.write('home/.config/kcminputrc', '[Mouse]\ncursorTheme=My Cursors\n')
        self.machine.write('usr/share/icons/My Cursors/cursors/left_ptr', '')
        block = hs.env_block({}, self.machine.root, self.machine.home, [])
        self.assertIn("export XCURSOR_THEME='My Cursors'", block)

    def test_block_replaced_and_removed_leaving_the_persons_lines(self):
        mine = 'export MY_VAR=1\n'
        first = hs.replace_block(mine, hs.env_block({}, self.machine.root))
        second = hs.replace_block(first, hs.env_block({'LANGUAGE': 'it'}, self.machine.root))
        self.assertEqual(second.count(hs.BEGIN), 1)
        self.assertIn('co:it', second)
        self.assertTrue(second.startswith(mine))
        self.assertEqual(hs.remove_block(second), mine)


class PortalTests(Case):
    def test_with_kde_and_kwallet(self):
        for name in ('hyprland', 'gtk', 'kde', 'kwallet', 'plasmanotify'):
            self.machine.write(f'{hs.PORTALS}/{name}.portal', '[portal]\n')
        text = hs.portals_conf(self.machine.root)
        self.assertEqual(text.splitlines()[1:], [
            '[preferred]', 'default=hyprland;gtk', 'org.freedesktop.impl.portal.FileChooser=kde;gtk',
            'org.freedesktop.impl.portal.Settings=kde;gtk', 'org.freedesktop.impl.portal.Secret=kwallet'])
        self.assertNotIn('plasmanotify', text, 'Plasma\'s notification backend needs plasmashell')
        self.assertNotIn('ScreenCast', text, 'screen sharing stays with Hyprland\'s backend')

    def test_without_kde(self):
        self.machine.write(f'{hs.PORTALS}/hyprland.portal', '[portal]\n')
        self.assertEqual(hs.portals_conf(self.machine.root).splitlines()[1:], ['[preferred]', 'default=hyprland;gtk'])


class MenuEntryTests(unittest.TestCase):
    NOCTALIA = ('[Desktop Entry]\nType=Application\nName=Noctalia\nExec=noctalia --daemon\nNotShowIn=GNOME;\n\n'
                '[Desktop Action Settings]\nName=Open Settings\nExec=sh -c "noctalia msg settings-open"\n')

    def test_only_in_hyprland(self):
        text = hs.hyprland_only_entry(self.NOCTALIA)
        main, action = text.split('[Desktop Action Settings]')
        self.assertIn('OnlyShowIn=Hyprland;', main)
        self.assertNotIn('NotShowIn', text)
        self.assertNotIn('OnlyShowIn', action)
        self.assertIn('Exec=noctalia --daemon', main)
        self.assertEqual(hs.hyprland_only_entry(text), text, 'applying it twice changes nothing')


class CheckTests(Case):
    def test_everything_installed_on_this_laptop(self):
        predator(self.machine)
        for name in ('hyprland', 'gtk', 'kde'):
            self.machine.write(f'{hs.PORTALS}/{name}.portal', '[portal]\n')
        self.machine.write('usr/share/wayland-sessions/hyprland-uwsm.desktop', '[Desktop Entry]\n')
        self.machine.write('home/.config/noctalia/config.toml', '[shell]\npolkit_agent = true\n')
        results = hs.checks(self.machine.root, self.machine.home, {}, runner(INSTALLED))
        levels = [level for level, _ in results]
        self.assertNotIn('missing', levels)
        text = '\n'.join(message for _, message in results)
        self.assertIn('Hyprland 0.56.2', text)
        self.assertIn('nvidia', text)
        self.assertNotIn('polkit', text)

    def test_nothing_installed(self):
        results = hs.checks(self.machine.root, self.machine.home, {}, runner({}))
        self.assertEqual([level for level, _ in results][:4], ['missing'] * 4)
        self.assertIn('polkit_agent', '\n'.join(message for _, message in results))


if __name__ == '__main__':
    unittest.main()
