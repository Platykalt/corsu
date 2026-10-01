"""Corsican interface for Chromium-based browsers: Chrome, Chromium, Opera / Opera GX, Edge, Brave, Vivaldi.

Chromium keeps its interface strings in per-language data packs (`locales/fr.pak`, Opera's
`localization/fr.pak`, macOS `fr.lproj/locale.pak`). Corsu rewrites the French pack with the
Corsican lexicon, so a browser displayed in French shows Corsican wherever a translation exists.
"""
import re

import engine

# Branch bodies of ICU messages: `{COUNT, plural, =1 {1 onglet} other {# onglets}}`.
ICU_BRANCH = re.compile(r'((?:=\d+|zero|one|two|few|many|other|[A-Za-z_]+)\s*)\{([^{}]*)\}')
ICU_MESSAGE = re.compile(r'\{\s*\w+\s*,\s*(?:plural|select|selectordinal)\s*,')


def translate_text(text):
    """Translate one pack string; ICU plural/select messages are translated branch by branch."""
    if not ICU_MESSAGE.search(text):
        return engine.translate(text)
    return ICU_BRANCH.sub(lambda match: match[1] + '{' + engine.translate(match[2]) + '}', text)


def pack_texts(text):
    """The translatable units of one pack string, as the lexicon sees them."""
    if ICU_MESSAGE.search(text):
        return [match[2] for match in ICU_BRANCH.finditer(text)]
    return [text]


def translate_pak(data):
    """Return the translated pack and the number of strings changed."""
    pak = engine.read_pak(data)
    if pak['encoding'] != 1:
        # Only UTF-8 packs carry text; binary resource packs are left untouched.
        return data, 0
    changed = 0
    for resource, value in pak['resources'].items():
        try:
            text = value.decode('utf-8')
        except UnicodeDecodeError:
            continue
        result = translate_text(text)
        if result != text:
            pak['resources'][resource] = result.encode('utf-8')
            changed += 1
    return (engine.make_pak(pak), changed) if changed else (data, 0)


# --- Installed browsers ---------------------------------------------------------------------

import json
import os
from pathlib import Path
import re as _re
import shlex
import subprocess
import sys
import tempfile

import corsu

LOCALE_DIRECTORIES = {'locales', 'Locales', 'localization'}
# (id, label, Linux roots, Linux commands, desktop entry, Windows roots, Local State relative to a base)
LINUX = {
    'chrome': ('Google Chrome', ['/opt/google/chrome'], ['google-chrome-stable', 'google-chrome', '/opt/google/chrome/google-chrome'], 'google-chrome.desktop'),
    'chromium': ('Chromium', ['/usr/lib/chromium', '/usr/lib/chromium-browser'], ['chromium', 'chromium-browser', '/usr/bin/chromium'], 'chromium.desktop'),
    'opera': ('Opera', ['/usr/lib/x86_64-linux-gnu/opera', '/usr/lib/opera'], ['opera', '/usr/bin/opera'], 'opera.desktop'),
    'opera-gx': ('Opera GX', ['/usr/lib/opera-gx'], ['opera-gx', '/usr/bin/opera-gx'], 'opera-gx.desktop'),
    'brave': ('Brave', ['/opt/brave.com/brave', '/opt/brave-bin'], ['brave', 'brave-browser', 'brave-browser-stable', '/usr/bin/brave-browser-stable'], 'brave-browser.desktop'),
    'edge': ('Microsoft Edge', ['/opt/microsoft/msedge'], ['microsoft-edge-stable', 'microsoft-edge', '/usr/bin/microsoft-edge-stable'], 'microsoft-edge.desktop'),
    'vivaldi': ('Vivaldi', ['/opt/vivaldi'], ['vivaldi-stable', 'vivaldi', '/usr/bin/vivaldi-stable'], 'vivaldi-stable.desktop'),
}
WINDOWS = {
    'chrome': ('Google Chrome', [('ProgramFiles', 'Google/Chrome/Application'), ('ProgramFiles(x86)', 'Google/Chrome/Application'),
                                 ('LOCALAPPDATA', 'Google/Chrome/Application')], ('LOCALAPPDATA', 'Google/Chrome/User Data')),
    'chromium': ('Chromium', [('LOCALAPPDATA', 'Chromium/Application')], ('LOCALAPPDATA', 'Chromium/User Data')),
    'opera': ('Opera', [('LOCALAPPDATA', 'Programs/Opera')], ('APPDATA', 'Opera Software/Opera Stable')),
    'opera-gx': ('Opera GX', [('LOCALAPPDATA', 'Programs/Opera GX')], ('APPDATA', 'Opera Software/Opera GX Stable')),
    'brave': ('Brave', [('ProgramFiles', 'BraveSoftware/Brave-Browser/Application'),
                        ('LOCALAPPDATA', 'BraveSoftware/Brave-Browser/Application')], ('LOCALAPPDATA', 'BraveSoftware/Brave-Browser/User Data')),
    'edge': ('Microsoft Edge', [('ProgramFiles(x86)', 'Microsoft/Edge/Application'), ('ProgramFiles', 'Microsoft/Edge/Application')],
             ('LOCALAPPDATA', 'Microsoft/Edge/User Data')),
    'vivaldi': ('Vivaldi', [('LOCALAPPDATA', 'Vivaldi/Application')], ('LOCALAPPDATA', 'Vivaldi/User Data')),
}


class Browser:
    def __init__(self, identifier, label, root, commands=(), desktop=None, local_state=None):
        self.id, self.label, self.root = identifier, label, Path(root)
        self.commands, self.desktop, self.local_state = list(commands), desktop, local_state

    def packs(self):
        """Every French interface pack, including leftover version folders on Windows."""
        return sorted(path for path in self.root.rglob('fr*.pak')
                      if path.parent.name in LOCALE_DIRECTORIES and _re.fullmatch(r'fr(?:_[A-Z]+)?\.pak', path.name))

    def executable(self):
        for command in self.commands:
            found = shutil_which(command)
            if found:
                return found
        return None


def shutil_which(command):
    import shutil
    return shutil.which(command) if not os.path.isabs(command) else (command if os.access(command, os.X_OK) else None)


def browsers():
    """Chromium-based browsers installed here. CORSU_CHROMIUM=<dir> replaces them with one test
    browser, so tests and CI never touch a real installation."""
    found = []
    if os.environ.get('CORSU_CHROMIUM'):
        root = Path(os.environ['CORSU_CHROMIUM'])
        binary = next((root / name for name in ('chrome', 'chrome.exe', 'chromium') if (root / name).exists()), None)
        return [Browser('test', 'Chromium (test)', root, [str(binary)] if binary else [])]
    if corsu.PLATFORM == 'linux':
        for identifier, (label, roots, commands, desktop) in LINUX.items():
            root = next((Path(root) for root in roots if Path(root).is_dir()), None)
            if root:
                browser = Browser(identifier, label, root, commands, desktop)
                if browser.packs():
                    found.append(browser)
    elif corsu.PLATFORM == 'windows':
        for identifier, (label, roots, state) in WINDOWS.items():
            for variable, relative in roots:
                base = os.environ.get(variable)
                if base and (Path(base) / relative).is_dir():
                    local_state = Path(os.environ.get(state[0], '')) / state[1] / 'Local State'
                    browser = Browser(identifier, label, Path(base) / relative, local_state=local_state)
                    if browser.packs():
                        found.append(browser)
                    break
    return found


# --- Writing packs, with administrator rights when the browser is system-wide ---------------

def elevated_copy(pairs):
    """Copy staged files over browser files that this account cannot write."""
    if not pairs:
        return
    if corsu.PLATFORM == 'windows':
        script = Path(tempfile.mkdtemp(prefix='corsu-')) / 'copy.ps1'
        script.write_text(''.join(f"Copy-Item -LiteralPath '{str(source).replace(chr(39), chr(39) * 2)}' "
                                  f"-Destination '{str(target).replace(chr(39), chr(39) * 2)}' -Force\r\n"
                                  for source, target in pairs), encoding='utf-8-sig')
        command = (f"Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList "
                   f"'-NoProfile','-ExecutionPolicy','Bypass','-File','\"{script}\"'")
        subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', command], check=True)
    else:
        loop = 'set -e; while [ "$#" -gt 1 ]; do cp -f -- "$1" "$2"; shift 2; done'
        subprocess.run(['pkexec', 'sh', '-c', loop, 'corsu', *[str(path) for pair in pairs for path in pair]], check=True)


def write_files(pairs):
    """Copy (source, target) pairs; ask for administrator rights once for read-only targets."""
    protected = []
    for source, target in pairs:
        try:
            temporary = target.with_name(target.name + '.corsu-tmp')
            temporary.write_bytes(source.read_bytes())
            os.replace(temporary, target)
        except PermissionError:
            temporary.unlink(missing_ok=True) if os.access(target.parent, os.W_OK) else None
            protected.append((source, target))
    elevated_copy(protected)
    for source, target in pairs:
        if corsu.digest(target.read_bytes()) != corsu.digest(source.read_bytes()):
            raise RuntimeError(f'Could not write {target}. Close the browser and run Corsu Setup again.')


def apply(installer, browser):
    """Translate the browser's French packs in place. Browser updates bring fresh French packs:
    those become the new originals and are translated again."""
    pairs, changed = [], 0
    stage = corsu.DATA / 'chromium' / browser.id
    stage.mkdir(parents=True, exist_ok=True)
    for pack in browser.packs():
        data = pack.read_bytes()
        record = installer.state['files'].get(str(pack))
        if record and corsu.digest(data) == record['installed_sha256']:
            continue
        translated, count = translate_pak(data)
        if not count:
            continue
        backup = corsu.DATA / 'backups' / corsu.digest(str(pack).encode())
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(data)
        staged = stage / (corsu.digest(translated)[:16] + '.pak')
        staged.write_bytes(translated)
        pairs.append((staged, pack))
        installer.state['files'][str(pack)] = {
            'backup': str(backup), 'mode': None, 'toggle': True, 'chromium': browser.id,
            'installed_sha256': corsu.digest(translated)}
        changed += count
    write_files(pairs)
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    return {'browser': browser.label, 'packs': len(browser.packs()), 'updated_packs': len(pairs), 'translated_strings': changed}


def restore(records):
    """Put the original French packs back; packs from removed browser versions are forgotten."""
    pairs = []
    for name, record in records.items():
        path = Path(name)
        if path.exists() and corsu.digest(path.read_bytes()) == record['installed_sha256'] and record.get('backup'):
            pairs.append((Path(record['backup']), path))
    write_files(pairs)


def refresh():
    """Re-translate packs replaced by browser updates. Run at login and by the launchers."""
    if corsu.disabled_marker().exists() or not corsu.STATE.exists():
        return []
    installer = corsu.Installer()
    wanted = set(installer.state.get('chromium', []))
    # Forget packs of browser versions the updater deleted.
    for name, record in list(installer.state['files'].items()):
        if record.get('chromium') and not Path(name).exists():
            installer.state['files'].pop(name)
    return [apply(installer, browser) for browser in browsers() if browser.id in wanted]


# --- Launch integration ----------------------------------------------------------------------

def linux_entry(installer, browser):
    """Route the browser's menu entry through Corsu, which re-translates after updates and
    asks Chromium for French (`co` has no pack, so `LANGUAGE=co:fr` resolves to the Corsican-filled `fr`)."""
    launcher = corsu.HOME / f'.local/bin/{browser.id}-corsu'
    installer.write(launcher, f'#!/bin/sh\nexec python3 {shlex.quote(str(corsu.SRC / "corsu.py"))} '
                              f'launch-chromium {browser.id} "$@"\n', 0o755)
    existing = corsu.HOME / '.local/share/applications' / browser.desktop
    original = existing if existing.exists() else Path('/usr/share/applications') / browser.desktop
    if not original.exists():
        return
    names = {Path(command).name for command in browser.commands}
    text = _re.sub(r'^Exec=(\S+)', lambda match: f'Exec={launcher}' if Path(match[1]).name in names else match[0],
                   original.read_text(encoding='utf-8'), flags=_re.M)
    installer.write(existing, text, toggle=True)


def launch(identifier, arguments):
    """Start a browser from its Corsu menu entry."""
    browser = next((browser for browser in browsers() if browser.id == identifier), None)
    if browser is None:
        raise SystemExit(f'{identifier} is not installed.')
    if not corsu.disabled_marker().exists():
        try:
            installer = corsu.Installer()
            apply(installer, browser)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
            print(f'Corsu could not update the translation: {error}', file=sys.stderr)
    environment = dict(os.environ)
    if not corsu.disabled_marker().exists():
        environment['LANGUAGE'] = 'co:fr'
    executable = browser.executable()
    extra = ['--lang=fr'] if browser.id.startswith('opera') and not corsu.disabled_marker().exists() else []
    os.execve(executable, [executable, *extra, *arguments], environment)


def install(installer):
    found = browsers()
    if not found:
        return []
    installer.state['chromium'] = sorted(set(installer.state.get('chromium', [])) | {browser.id for browser in found})
    reports = [apply(installer, browser) for browser in found]
    for browser in found:
        if corsu.PLATFORM == 'linux' and browser.desktop:
            linux_entry(installer, browser)
        if corsu.PLATFORM == 'windows' and browser.local_state and browser.local_state.exists():
            # Chromium on Windows shows the language chosen in its settings; choose French.
            installer.json_settings(browser.local_state, {'intl/app_locale': 'fr'}, toggle=True)
    if corsu.PLATFORM == 'windows':
        # Browser updates bring back French packs: re-translate them at every login.
        corsu.windows_link(installer, corsu.CONFIG / 'Microsoft/Windows/Start Menu/Programs/Startup/Corsu.lnk',
                           corsu.python_launcher(), f'"{corsu.SRC / "corsu.py"}" chromium-refresh')
    corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
    return reports
