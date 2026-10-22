"""What the optional Hyprland + Noctalia component needs to know about this computer, and the session files it writes.

Everything here is read-only detection and text generation: it never writes a file, starts a compositor or changes a
setting. Inputs are injectable (`root` for /sys, /dev, /etc and /usr; `home`; `env`; `run` for commands) so the tests
build fake machines in throwaway folders. Installer state and writing belong to `apps/hyprland.py`.
Why each choice is made is explained in docs/hyprland-system.md.
"""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

import corsu

# Lua configuration arrived with Hyprland 0.55; Corsu's configuration is written and checked against 0.56.
HYPRLAND_MINIMUM, HYPRLAND_TESTED = (0, 55), (0, 56)
# Noctalia 5 is the native C++ shell (TOML settings, JSON translations); 4.x was a different (Quickshell) program.
NOCTALIA_MAJOR = 5
BEGIN, END = '# corsu:begin', '# corsu:end'
# DRM connector types aquamarine counts as built-in panels (gpuNumBuiltinPanels in aquamarine's DRM.cpp).
INTERNAL = ('eDP', 'LVDS', 'DSI')
ICON_DIRS = ('.local/share/icons', '.icons')
SYSTEM_ICON_DIRS = ('usr/share/icons', 'usr/local/share/icons')
QT6CT_PLUGIN = 'usr/lib/qt6/plugins/platformthemes/libqt6ct.so'
PORTALS = 'usr/share/xdg-desktop-portal/portals'


def run_command(argv, timeout=10):
    """Standard output of a command that succeeded, else None (missing, failed, too slow). English output so the
    parsers below read the same words on every computer."""
    if shutil.which(argv[0]) is None:
        return None
    env = dict(os.environ, LC_ALL='C', LANGUAGE='')
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


# ---- versions ----

def version_tuple(text):
    match = re.match(r'v?(\d+)\.(\d+)(?:\.(\d+))?', text or '')
    return tuple(int(part) for part in match.groups() if part is not None) if match else None


def hyprland_version_from(text):
    """Version in the output of `Hyprland --version-json`, `Hyprland --version` or `hyprctl version`."""
    if not text:
        return None
    try:
        data = json.loads(text)
        value = data.get('version') or data.get('tag')
        if value:
            return value.lstrip('v')
    except (ValueError, AttributeError):
        pass
    match = re.search(r'Hyprland v?(\d+\.\d+(?:\.\d+)?)', text) or re.search(r'Tag: v?(\d+\.\d+(?:\.\d+)?)', text)
    return match.group(1) if match else None


def plain_version_from(text):
    match = re.search(r'(\d+\.\d+(?:\.\d+)?)', text or '')
    return match.group(1) if match else None


def pacman_version(package, run):
    """Upstream version of an installed Arch package ('hyprland 0.56.2-4.1' gives '0.56.2'), else None."""
    output = run(['pacman', '-Q', package])
    match = re.match(rf'{re.escape(package)} (?:\d+:)?([^-\s]+)', output or '')
    return match.group(1) if match else None


def versions(run=run_command):
    """{'hyprland', 'noctalia', 'uwsm', 'xdph'}: installed version or None. The program's own answer first (it is
    the one that runs), the package database for programs without a version option."""
    hyprland = (hyprland_version_from(run(['Hyprland', '--version-json']))
                or hyprland_version_from(run(['Hyprland', '--version'])) or pacman_version('hyprland', run))
    noctalia = plain_version_from(run(['noctalia', '--version'])) or pacman_version('noctalia', run)
    return {'hyprland': hyprland, 'noctalia': noctalia, 'uwsm': pacman_version('uwsm', run),
            'xdph': pacman_version('xdg-desktop-portal-hyprland', run)}


def compatibility(found):
    """(verdict, reasons): 'supported', 'untested' (newer than what Corsu was checked with), 'unsupported' or
    'missing'. Hyprland before 0.55 has no Lua configuration, which Corsu's profile is written in; Noctalia other
    than 5.x has other settings and translation files."""
    reasons, verdict = [], 'supported'
    hyprland, noctalia = version_tuple(found.get('hyprland')), version_tuple(found.get('noctalia'))
    if hyprland is None or noctalia is None:
        missing = [name for name, value in (('Hyprland', hyprland), ('Noctalia', noctalia)) if value is None]
        return 'missing', [corsu.t(f'not installed: {", ".join(missing)}', f'non installé : {", ".join(missing)}')]
    if hyprland[:2] < HYPRLAND_MINIMUM:
        verdict = 'unsupported'
        reasons.append(corsu.t(f'Hyprland {found["hyprland"]} predates the Lua configuration (0.55)',
                               f'Hyprland {found["hyprland"]} précède la configuration Lua (0.55)'))
    elif hyprland[:2] > HYPRLAND_TESTED:
        verdict = 'untested'
        reasons.append(corsu.t(f'Hyprland {found["hyprland"]} is newer than the version checked (0.56)',
                               f'Hyprland {found["hyprland"]} est plus récent que la version vérifiée (0.56)'))
    if noctalia[0] != NOCTALIA_MAJOR:
        verdict = 'unsupported'
        reasons.append(corsu.t(f'Noctalia {found["noctalia"]}: only 5.x is supported',
                               f'Noctalia {found["noctalia"]} : seule la 5.x est prise en charge'))
    return verdict, reasons


# ---- graphics cards and outputs ----

def read(path, default=None):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace').strip()
    except OSError:
        return default


def edid_size_mm(edid):
    """(width, height) in millimetres from an EDID: the first detailed timing (millimetres), else the basic
    block (centimetres). None when the EDID says nothing (projectors, some televisions)."""
    if not edid or len(edid) < 128:
        return None
    timing = edid[54:72]
    if timing[0] or timing[1]:
        width, height = timing[12] | (timing[14] & 0xF0) << 4, timing[13] | (timing[14] & 0x0F) << 8
        if width and height:
            return width, height
    if edid[21] and edid[22]:
        return edid[21] * 10, edid[22] * 10
    return None


def connectors(root, card):
    found = []
    for path in sorted((Path(root) / 'sys/class/drm').glob(f'{card}-*')):
        name = path.name[len(card) + 1:]
        try:
            edid = (path / 'edid').read_bytes()
        except OSError:
            edid = b''
        modes = (read(path / 'modes', '') or '').split()
        mode = re.fullmatch(r'(\d+)x(\d+)\w*', modes[0]) if modes else None
        found.append({'name': name, 'status': read(path / 'status', 'unknown'),
                      'internal': name.split('-')[0] in INTERNAL,
                      'size_mm': edid_size_mm(edid), 'mode': (int(mode[1]), int(mode[2])) if mode else None})
    return found


def gpus(root='/'):
    """Graphics cards with a display engine: [{card, driver, slot, by_path, boot_vga, connectors}]. `by_path` is
    the stable /dev/dri/by-path name (cardN numbers change between boots), None when udev made none."""
    root = Path(root)
    by_path = {}
    for link in (root / 'dev/dri/by-path').glob('*-card'):
        try:
            by_path[Path(os.readlink(link)).name] = '/' + str(link.relative_to(root))
        except OSError:
            continue
    found = []
    for card in sorted((root / 'sys/class/drm').glob('card*'), key=lambda path: int(re.sub(r'\D', '', path.name) or 0)):
        if not re.fullmatch(r'card\d+', card.name):
            continue
        device = card / 'device'
        try:
            driver = Path(os.readlink(device / 'driver')).name
        except OSError:
            driver = None
        slot = device.resolve().name
        found.append({'card': card.name, 'driver': driver,
                      'slot': slot if re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.\d', slot) else None,
                      'by_path': by_path.get(card.name), 'boot_vga': read(device / 'boot_vga') == '1',
                      'connectors': connectors(root, card.name)})
    return found


def panel_gpu(cards):
    """The card driving a connected built-in panel (eDP, LVDS, DSI), else None (desktop, or lid closed and off)."""
    return next((gpu for gpu in cards if any(item['internal'] and item['status'] == 'connected'
                                             for item in gpu['connectors'])), None)


def aquamarine_order(cards):
    """The order aquamarine (Hyprland's backend, 0.8 and later) chooses by itself: boot VGA card first, then the card
    with the most connected built-in panels moved in front. All cards are kept, so outputs on any of them work."""
    order = sorted(cards, key=lambda gpu: not gpu['boot_vga'])
    panels = lambda gpu: sum(item['internal'] and item['status'] == 'connected' for item in gpu['connectors'])
    best = max(order, key=panels, default=None)
    if best is not None and panels(best) and order[0] is not best:
        order.remove(best)
        order.insert(0, best)
    return order


def aq_drm_devices(cards):
    """by-path names in the order Hyprland should use the cards: the one driving the built-in panel first (it
    renders and scans out the panel without a copy), then the others so their outputs keep working.
    None with a single card: nothing to choose."""
    usable = [gpu for gpu in cards if gpu['by_path']]
    if len(usable) < 2:
        return None
    first = panel_gpu(usable) or next((gpu for gpu in usable if gpu['boot_vga']), usable[0])
    return [first['by_path']] + [gpu['by_path'] for gpu in usable if gpu is not first]


def gpu_lines(cards):
    """Shell lines for env-hyprland setting AQ_DRM_DEVICES, or [] when aquamarine already picks that order.
    by-path names hold ':' which AQ_DRM_DEVICES uses as separator, so they are turned into /dev/dri/cardN at each
    login; a card missing that day is skipped instead of leaving Hyprland without a GPU."""
    wanted = aq_drm_devices(cards)
    if wanted is None or [gpu['by_path'] for gpu in aquamarine_order(cards) if gpu['by_path']] == wanted:
        return []
    paths = ' '.join(shlex.quote(path) for path in wanted)
    return ['# Graphics cards for Hyprland, in order (stable PCI names resolved at each login).',
            'AQ_DRM_DEVICES=',
            f'for corsu_card in {paths}; do',
            '    [ -e "$corsu_card" ] && AQ_DRM_DEVICES="${AQ_DRM_DEVICES:+$AQ_DRM_DEVICES:}$(readlink -f "$corsu_card")"',
            'done',
            'unset corsu_card',
            'if [ -n "$AQ_DRM_DEVICES" ]; then export AQ_DRM_DEVICES; else unset AQ_DRM_DEVICES; fi']


# ---- scale ----

CLEAN_SCALES = (1, 1.2, 1.25, 1.5, 1.6, 1.75, 2, 2.4, 2.5, 3)


def suggested_scale(width, height, width_mm, height_mm, internal=True):
    """A scale giving about 110 logical pixels per inch on a laptop panel (held closer) and 96 on a monitor, among
    the scales that divide the resolution into whole logical pixels (Hyprland refuses the others). 1 when the
    physical size is unknown, implausible or large (televisions)."""
    if not (width and height and width_mm and height_mm) or width_mm < 100 or height_mm < 60:
        return 1
    target = width / (width_mm / 25.4) / (110 if internal else 96)
    clean = [scale for scale in CLEAN_SCALES
             if abs(width / scale - round(width / scale)) < 1e-6 and abs(height / scale - round(height / scale)) < 1e-6]
    # The largest that does not overshoot by more than a tenth: a slightly small interface beats a cramped one.
    return max((scale for scale in clean if scale <= target + 0.1), default=1)


def plasma_scales(home):
    """{connector: scale} chosen in Plasma's display settings (kwinoutputconfig.json), so both sessions can look the
    same; {} when Plasma has none."""
    try:
        data = json.loads((Path(home) / '.config/kwinoutputconfig.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    scales = {}
    for section in data if isinstance(data, list) else []:
        if isinstance(section, dict) and section.get('name') == 'outputs':
            for output in section.get('data') or []:
                if isinstance(output, dict) and output.get('connectorName') and output.get('scale'):
                    scales.setdefault(output['connectorName'], output['scale'])
    return scales


def plasma_modes(home):
    """{connector: 'WIDTHxHEIGHT@RATE'} chosen in Plasma's display settings, so Hyprland starts at the same refresh rate
    (a panel's preferred mode is often its lowest rate: 60 Hz on a 240 Hz laptop); {} when Plasma has none."""
    try:
        data = json.loads((Path(home) / '.config/kwinoutputconfig.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    modes = {}
    for section in data if isinstance(data, list) else []:
        if not (isinstance(section, dict) and section.get('name') == 'outputs'):
            continue
        for output in section.get('data') or []:
            mode = output.get('mode') if isinstance(output, dict) else None
            if not (isinstance(mode, dict) and output.get('connectorName')):
                continue
            cvt = mode.get('cvt')
            try:
                if isinstance(cvt, dict):
                    width, height = int(cvt['hdisplay']), int(cvt['vdisplay'])
                    rate = int(cvt['clock']) * 1000 / (int(cvt['htotal']) * int(cvt['vtotal']))
                else:
                    width, height, rate = int(mode['width']), int(mode['height']), int(mode['refreshRate']) / 1000
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                continue
            if width > 0 and height > 0 and rate > 0:
                modes.setdefault(output['connectorName'], f'{width}x{height}@{rate:.2f}')
    return modes


def outputs(cards, home=None):
    """Connected outputs: [{name, card, driver, internal, mode, size_mm, suggested, plasma}]; `plasma` is the scale
    the person uses in Plasma (None if unknown), `plasma_mode` its mode there, `suggested` the one computed from the physical size."""
    plasma = plasma_scales(home) if home else {}
    plasma_mode = plasma_modes(home) if home else {}
    found = []
    for gpu in cards:
        for item in gpu['connectors']:
            if item['status'] != 'connected':
                continue
            size, mode = item['size_mm'] or (None, None), item['mode'] or (None, None)
            found.append({'name': item['name'], 'card': gpu['card'], 'driver': gpu['driver'],
                          'internal': item['internal'], 'mode': item['mode'], 'size_mm': item['size_mm'],
                          'suggested': suggested_scale(*mode, *size, internal=item['internal']),
                          'plasma': plasma.get(item['name']), 'plasma_mode': plasma_mode.get(item['name'])})
    return found


# ---- keyboard ----

def keyboard(root='/', home=None, run=run_command):
    """{'layout', 'variant', 'model', 'options', 'source'} in Hyprland's comma-separated form. Plasma's own choice
    first (kxkbrc, used when its Use=true), then the system one (localectl, else the file localed writes)."""
    from apps import settings
    if home:
        text = read(Path(home) / '.config/kxkbrc', '')
        if text and (settings.ini_get(text, 'Layout', 'Use') or '').lower() == 'true' \
                and settings.ini_get(text, 'Layout', 'LayoutList'):
            return {'layout': settings.ini_get(text, 'Layout', 'LayoutList'),
                    'variant': settings.ini_get(text, 'Layout', 'VariantList') or '',
                    'model': settings.ini_get(text, 'Layout', 'Model') or '',
                    'options': settings.ini_get(text, 'Layout', 'Options') or '', 'source': 'kxkbrc'}
    names = {'layout': 'Layout', 'variant': 'Variant', 'model': 'Model', 'options': 'Options'}
    output = run(['localectl', 'status'])
    if output:
        found = {key: (re.search(rf'X11 {word}:\s*(\S*)', output) or [None, ''])[1] for key, word in names.items()}
        if found['layout']:
            return dict(found, source='localectl')
    text = read(Path(root) / 'etc/X11/xorg.conf.d/00-keyboard.conf', '')
    found = {key: (re.search(rf'Option\s+"Xkb{word}"\s+"([^"]*)"', text) or [None, ''])[1] for key, word in names.items()}
    if found['layout']:
        return dict(found, source='00-keyboard.conf')
    return None


# ---- session environment ----

def session_languages(env):
    """Same rule as apps.session_languages, on a given environment: the person's languages without Corsican."""
    value = env.get('LANGUAGE') or env.get('LC_ALL') or env.get('LC_MESSAGES') or env.get('LANG') or 'fr'
    languages = []
    for item in value.split(':'):
        language = item.split('.')[0].split('@')[0]
        if language and language not in ('C', 'POSIX') and not language.startswith('co') and language not in languages:
            languages.append(language)
    return languages or ['fr']


def language_value(env):
    """LANGUAGE for the Hyprland session, built like apps.corsican_first(): Corsican, then the person's languages."""
    return ':'.join(['co', *session_languages(env)])


def cursor(root='/', home=None):
    """(theme, size, hyprcursor) from Plasma's mouse settings when that theme is installed; hyprcursor tells whether
    it also comes in Hyprland's own format. None when Plasma has no choice saved or the theme is gone."""
    from apps import settings
    if not home:
        return None
    text = read(Path(home) / '.config/kcminputrc', '')
    theme, size = settings.ini_get(text, 'Mouse', 'cursorTheme'), settings.ini_get(text, 'Mouse', 'cursorSize')
    if not theme or '/' in theme:
        return None
    folders = [Path(home) / folder / theme for folder in ICON_DIRS] + \
              [Path(root) / folder / theme for folder in SYSTEM_ICON_DIRS]
    folder = next((folder for folder in folders if (folder / 'cursors').is_dir() or (folder / 'manifest.hl').exists()
                   or (folder / 'manifest.toml').exists()), None)
    if folder is None:
        return None
    hyprcursor = (folder / 'manifest.hl').exists() or (folder / 'manifest.toml').exists()
    return theme, size if size and size.isdigit() else None, hyprcursor


def environment(env, root='/', home=None):
    """[(name, value)] Corsu sets for the Hyprland session only."""
    root = Path(root)
    pairs = [('LANGUAGE', language_value(env))]
    if (root / QT6CT_PLUGIN).exists():
        pairs.append(('QT_QPA_PLATFORMTHEME', 'qt6ct'))
    # KDE programs (Dolphin's "Open with", the KDE file dialog) read $XDG_MENU_PREFIX applications.menu; only
    # Plasma's menu file is installed and Plasma alone sets the prefix.
    if (root / 'etc/xdg/menus/plasma-applications.menu').exists() and not (root / 'etc/xdg/menus/applications.menu').exists():
        pairs.append(('XDG_MENU_PREFIX', 'plasma-'))
    found = cursor(root, home)
    if found:
        theme, size, hyprcursor = found
        pairs.append(('XCURSOR_THEME', theme))
        if size:
            pairs.append(('XCURSOR_SIZE', size))
        if hyprcursor:
            pairs.append(('HYPRCURSOR_THEME', theme))
            if size:
                pairs.append(('HYPRCURSOR_SIZE', size))
    return pairs


def env_block(env, root='/', home=None, cards=None):
    """Corsu's block for ~/.config/uwsm/env-hyprland (uwsm sources it, as shell, for the Hyprland session only)."""
    lines = [BEGIN,
             '# Written by Corsu for the Hyprland session only; Plasma does not read this file.',
             '# Corsu rewrites the lines between the markers; put your own lines outside them.']
    lines += [f'export {name}={shlex.quote(str(value))}' for name, value in environment(env, root, home)]
    lines += gpu_lines(cards or [])
    lines.append(END)
    return '\n'.join(lines) + '\n'


def replace_block(text, block):
    """The file with Corsu's block replaced (or added at the end), the person's lines left as they are."""
    pattern = re.compile(rf'^{re.escape(BEGIN)}\n.*?^{re.escape(END)}\n?', re.M | re.S)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1)
    return text + ('' if not text or text.endswith('\n') else '\n') + block


def remove_block(text):
    pattern = re.compile(rf'^{re.escape(BEGIN)}\n.*?^{re.escape(END)}\n?', re.M | re.S)
    return pattern.sub('', text)


# ---- portals ----

def portal_backends(root='/'):
    """Names of the installed portal backends (file names in /usr/share/xdg-desktop-portal/portals)."""
    return sorted(path.stem for path in (Path(root) / PORTALS).glob('*.portal'))


def portals_conf(root='/'):
    """~/.config/xdg-desktop-portal/hyprland-portals.conf, read only when XDG_CURRENT_DESKTOP is Hyprland. It replaces
    the packaged hyprland-portals.conf as a whole, so it repeats its default. Screen sharing, screenshots and global
    shortcuts stay with Hyprland's backend; the file dialog comes from KDE's backend when installed (the same dialog
    as in Plasma); light/dark and accent come from Plasma's settings first; secrets from KWallet."""
    backends = portal_backends(root)
    lines = ['# Written by Corsu for the Hyprland session; Plasma uses kde-portals.conf.', '[preferred]',
             'default=hyprland;gtk']
    if 'kde' in backends:
        lines.append('org.freedesktop.impl.portal.FileChooser=kde;gtk')
        lines.append('org.freedesktop.impl.portal.Settings=kde;gtk')
    if 'kwallet' in backends:
        lines.append('org.freedesktop.impl.portal.Secret=kwallet')
    return '\n'.join(lines) + '\n'


# ---- menu entry ----

def hyprland_only_entry(text):
    """A copy of Noctalia's menu entry shown only in Hyprland: started from Plasma's menu it would put a second shell
    over Plasma. Built from the system entry so its command stays current."""
    lines, in_main, done = [], False, False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('['):
            if in_main and not done:
                lines.append('OnlyShowIn=Hyprland;')
                done = True
            in_main = stripped == '[Desktop Entry]'
        elif in_main and re.match(r'(OnlyShowIn|NotShowIn)\s*=', stripped):
            continue
        lines.append(line)
    if in_main and not done:
        lines.append('OnlyShowIn=Hyprland;')
    return '\n'.join(lines) + '\n'


# ---- everything together ----

def detect(root='/', home=None, env=None, run=run_command):
    """All of the above for the component and the window; nothing is cached."""
    env = os.environ if env is None else env
    cards = gpus(root)
    found = versions(run)
    return {'versions': found, 'compatibility': compatibility(found), 'gpus': cards,
            'aq_drm_devices': aq_drm_devices(cards), 'outputs': outputs(cards, home),
            'keyboard': keyboard(root, home, run), 'portal_backends': portal_backends(root),
            'env_block': env_block(env, root, home, cards), 'portals_conf': portals_conf(root)}


def checks(root='/', home=None, env=None, run=run_command, detected=None):
    """[(level, text)] for the window and the command line; level is 'ok', 'info', 'warning' or 'missing'."""
    if sys.platform != 'linux' and root == '/':
        return [('info', corsu.t('Hyprland runs on Linux only', 'Hyprland ne fonctionne que sous Linux'))]
    root = Path(root)
    found = detected or detect(root, home, env, run)
    names = {'hyprland': 'Hyprland', 'noctalia': 'Noctalia', 'uwsm': 'uwsm', 'xdph': 'xdg-desktop-portal-hyprland'}
    results = []
    for key, name in names.items():
        version = found['versions'].get(key)
        results.append(('ok', f'{name} {version}') if version else
                       ('missing', corsu.t(f'{name} is not installed', f'{name} n\'est pas installé')))
    verdict, reasons = found['compatibility']
    if verdict != 'missing':
        results.append(('ok' if verdict == 'supported' else 'warning',
                        '; '.join(reasons) or corsu.t('versions supported', 'versions prises en charge')))
    sessions = root / 'usr/share/wayland-sessions'
    if (sessions / 'hyprland-uwsm.desktop').exists():
        results.append(('ok', corsu.t('login entry "Hyprland (uwsm-managed)" present',
                                      'entrée de connexion « Hyprland (uwsm-managed) » présente')))
    elif (sessions / 'hyprland.desktop').exists():
        results.append(('warning', corsu.t('only the "Hyprland" login entry: install uwsm so Corsu\'s session settings apply',
                                           'seulement l\'entrée « Hyprland » : installez uwsm pour que les réglages de session de Corsu s\'appliquent')))
    backends = found['portal_backends']
    if 'hyprland' not in backends:
        results.append(('missing', corsu.t('no Hyprland portal: screen sharing will not work',
                                           'pas de portail Hyprland : le partage d\'écran ne marchera pas')))
    if 'kde' not in backends and 'gtk' not in backends:
        results.append(('warning', corsu.t('no portal with a file dialog (kde or gtk)',
                                           'aucun portail avec une fenêtre de fichiers (kde ou gtk)')))
    if not (root / QT6CT_PLUGIN).exists():
        results.append(('info', corsu.t('qt6ct is not installed: Qt programs keep their default look in Hyprland',
                                        'qt6ct n\'est pas installé : les programmes Qt gardent leur aspect par défaut dans Hyprland')))
    results.extend(gpu_findings(found['gpus'], root))
    if (root / 'usr/lib/pam_kwallet_init').exists():
        results.append(('info', corsu.t('KWallet opens at login only if the Hyprland session runs /usr/lib/pam_kwallet_init',
                                        'KWallet ne s\'ouvre à la connexion que si la session Hyprland lance /usr/lib/pam_kwallet_init')))
    if home and not re.search(r'^\s*polkit_agent\s*=\s*true', read(Path(home) / '.config/noctalia/config.toml', '') or '', re.M):
        results.append(('info', corsu.t('Noctalia\'s administrator password prompt (polkit_agent) is off',
                                        'la demande de mot de passe administrateur de Noctalia (polkit_agent) est désactivée')))
    return results


def gpu_findings(cards, root):
    if not cards:
        return [('info', corsu.t('no graphics card found', 'aucune carte graphique trouvée'))]
    describe = ', '.join(f'{gpu["slot"] or gpu["card"]} {gpu["driver"] or "?"}' for gpu in cards)
    results = [('info', corsu.t(f'graphics cards: {describe}', f'cartes graphiques : {describe}'))]
    panel = panel_gpu(cards)
    if panel and len(cards) > 1:
        results.append(('info', corsu.t(f'built-in screen on {panel["driver"]} ({panel["slot"]}); Hyprland uses it first',
                                        f'écran intégré sur {panel["driver"]} ({panel["slot"]}) ; Hyprland l\'utilise en premier')))
        if panel['driver'] == 'nvidia':
            results.append(('info', corsu.t('the NVIDIA card drives the built-in screen: it cannot sleep while the screen '
                                            'is on (the laptop\'s graphics switch decides this, not Hyprland)',
                                            'la carte NVIDIA pilote l\'écran intégré : elle ne peut pas se mettre en veille '
                                            'tant que l\'écran est allumé (c\'est le commutateur graphique du portable qui '
                                            'en décide, pas Hyprland)')))
    return results
