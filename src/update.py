#!/usr/bin/env python3
"""Find and install a newer Corsu release.

`latest()` asks GitHub for the latest release (at most once an hour, only while the Corsu app is open).
`python3 update.py --install` downloads the archive for this system, checks its SHA-256 against the published
checksum, and runs its installer for the parts already installed. Nothing runs if the checksum differs.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

import corsu
from corsu import t

API = 'https://api.github.com/repos/Platykalt/corsu/releases/latest'
DOWNLOAD = 'https://github.com/Platykalt/corsu/releases/latest/download/'
ARCHIVES = {'linux': 'corsu-linux.tar.gz', 'macos': 'corsu-macos.tar.gz', 'windows': 'corsu-windows.zip'}
CACHE = 'update.json'


def version_tuple(text):
    return tuple(int(part) for part in text.lstrip('v').split('.') if part.isdigit())


def current():
    return json.loads((corsu.SRC / 'release.json').read_text(encoding='utf-8'))['version']


def latest(force=False):
    """{'version', 'newer', 'url'} or None when GitHub cannot be reached."""
    cache = corsu.DATA / CACHE
    try:
        saved = json.loads(cache.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        saved = None
    if not saved or force or time.time() - saved.get('checked', 0) > 3600:
        try:
            request = urllib.request.Request(API, headers={'Accept': 'application/vnd.github+json',
                                                           'User-Agent': 'corsu-update'})
            with urllib.request.urlopen(request, timeout=8) as response:
                release = json.load(response)
            saved = {'checked': time.time(), 'version': release['tag_name'].lstrip('v'), 'url': release['html_url']}
            corsu.DATA.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(saved), encoding='utf-8')
        except (OSError, ValueError, KeyError):
            if not saved:
                return None
    return {'version': saved['version'], 'url': saved['url'],
            'newer': version_tuple(saved['version']) > version_tuple(current())}


def download(name, target):
    request = urllib.request.Request(DOWNLOAD + name, headers={'User-Agent': 'corsu-update'})
    with urllib.request.urlopen(request, timeout=120) as response:
        target.write_bytes(response.read())


def installed_components():
    state = corsu.load_state()
    components = [name for name in state.get('components', []) if name != 'terminal']
    if state.get('qt_system'):
        components.append('qt')
    return components


def install():
    name = ARCHIVES[corsu.PLATFORM]
    components = installed_components()
    if not components:
        raise RuntimeError(t('Nothing is installed yet.', 'Rien n\'est encore installé.'))
    with tempfile.TemporaryDirectory(prefix='corsu-update-') as directory:
        folder = Path(directory)
        print(t(f'Downloading {name}…', f'Téléchargement de {name}…'), flush=True)
        download(name, folder / name)
        download(name + '.sha256', folder / 'expected.sha256')
        expected = (folder / 'expected.sha256').read_text(encoding='utf-8').split()[0].lower()
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(t('The download does not match its published checksum; nothing was installed.',
                                 'Le téléchargement ne correspond pas à sa somme de contrôle publiée ; rien n\'a été installé.'))
        print(t('Checksum verified.', 'Somme de contrôle vérifiée.'), flush=True)
        if name.endswith('.zip'):
            with zipfile.ZipFile(folder / name) as archive:
                archive.extractall(folder)
        else:
            with tarfile.open(folder / name) as archive:
                # The 'data' filter refuses links and paths that leave the folder (Python 3.12 and later).
                if hasattr(tarfile, 'data_filter'):
                    archive.extractall(folder, filter='data')
                else:
                    archive.extractall(folder)
        installer = folder / 'corsu/src/installer.py'
        command = [sys.executable, str(installer), '--yes', '--components', *components]
        if 'discord' in components:
            record = next((record for record in corsu.load_state()['files'].values() if record.get('discord_location')), None)
            if record:
                command += ['--discord-path', record['discord_location']]
        result = subprocess.run(command)
        if result.returncode:
            raise RuntimeError(t('The new version could not be installed.', 'La nouvelle version n\'a pas pu être installée.'))


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    import logbook
    logbook.start('update')
    if '--install' in sys.argv:
        try:
            install()
        except (RuntimeError, OSError) as error:
            logbook.failure(error)
            print(error, file=sys.stderr)
            return 1
        except Exception as error:
            print(logbook.failure(error), file=sys.stderr)
            return 1
        return 0
    print(json.dumps(latest(force=True)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
