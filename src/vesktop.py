"""Install Vesktop (a Discord app that includes Vencord) for people who have neither Discord nor Vesktop.

The latest release is read from GitHub; the archive for this system is downloaded, checked against the SHA-256
digest GitHub publishes for it, and unpacked into Corsu's data folder (Linux, Windows) or ~/Applications (macOS).
A menu entry or shortcut is added. Uninstalling Corsu removes all of it. Corsu then points Vesktop at the Vencord
build that contains the Corsu plugin, like for a Vesktop installed by hand.
"""
import hashlib
import json
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import corsu
from corsu import t

API = 'https://api.github.com/repos/Vencord/Vesktop/releases/latest'


def asset_pattern():
    arm = platform.machine().lower() in ('arm64', 'aarch64')
    if corsu.PLATFORM == 'windows':
        return r'Vesktop-[\d.]+-arm64-win\.zip' if arm else r'Vesktop-[\d.]+-win\.zip'
    if corsu.PLATFORM == 'macos':
        return r'Vesktop-[\d.]+-universal-mac\.zip'
    return r'vesktop-[\d.]+-arm64\.tar\.gz' if arm else r'vesktop-[\d.]+\.tar\.gz'


def latest_asset():
    request = urllib.request.Request(API, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'corsu'})
    with urllib.request.urlopen(request, timeout=20) as response:
        release = json.load(response)
    pattern = re.compile(asset_pattern() + '$')
    for asset in release.get('assets', []):
        if pattern.match(asset['name']) and str(asset.get('digest', '')).startswith('sha256:'):
            return release['tag_name'], asset
    raise RuntimeError(t('No Vesktop download with a published checksum was found for this system.',
                         'Aucun téléchargement de Vesktop avec somme de contrôle publiée pour ce système.'))


def download(asset, target):
    """Download with progress lines from 10 to 50 percent, then check the SHA-256 digest."""
    request = urllib.request.Request(asset['browser_download_url'], headers={'User-Agent': 'corsu'})
    total, done, checksum = asset.get('size') or 0, 0, hashlib.sha256()
    shown = -1
    with urllib.request.urlopen(request, timeout=60) as response, target.open('wb') as output:
        while chunk := response.read(1 << 20):
            output.write(chunk)
            checksum.update(chunk)
            done += len(chunk)
            percent = 10 + int(40 * done / total) if total else 30
            if percent != shown:
                shown = percent
                corsu.progress(percent, f'Downloading Vesktop ({done >> 20} MB)', f'Téléchargement de Vesktop ({done >> 20} Mo)')
    if checksum.hexdigest() != asset['digest'].split(':', 1)[1]:
        raise RuntimeError(t('The Vesktop download does not match its published checksum; nothing was installed.',
                             'Le téléchargement de Vesktop ne correspond pas à sa somme de contrôle ; rien n\'a été installé.'))


def unpack(archive, folder):
    if corsu.PLATFORM == 'macos':
        # ditto keeps the links and permissions an application bundle needs.
        subprocess.run(['ditto', '-x', '-k', str(archive), str(folder)], check=True)
    elif archive.name.endswith('.zip'):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(folder)
    else:
        with tarfile.open(archive) as bundle:
            if hasattr(tarfile, 'data_filter'):
                bundle.extractall(folder, filter='data')
            else:
                bundle.extractall(folder)


def install():
    """Download and install Vesktop; returns where it went."""
    installer = corsu.Installer()
    corsu.progress(8, 'Looking for Vesktop', 'Recherche de Vesktop')
    version, asset = latest_asset()
    print(t(f'Installing Vesktop {version}…', f'Installation de Vesktop {version}…'), flush=True)
    with tempfile.TemporaryDirectory(prefix='corsu-vesktop-') as directory:
        folder = Path(directory)
        archive = folder / asset['name']
        download(asset, archive)
        print(t('Checksum verified.', 'Somme de contrôle vérifiée.'), flush=True)
        corsu.progress(52, 'Unpacking Vesktop', 'Décompression de Vesktop')
        unpacked = folder / 'unpacked'
        unpacked.mkdir()
        unpack(archive, unpacked)
        if corsu.PLATFORM == 'macos':
            app = next(unpacked.glob('*.app'))
            target = corsu.HOME / 'Applications/Vesktop.app'
            installer.tree(target, app)
            return target
        entries = list(unpacked.iterdir())
        root = entries[0] if len(entries) == 1 and entries[0].is_dir() else unpacked
        target = corsu.DATA / 'vesktop'
        installer.tree(target, root)
    if corsu.PLATFORM == 'windows':
        corsu.windows_link(installer, corsu.START_MENU / 'Vesktop.lnk', target / 'Vesktop.exe', '')
    else:
        executable = target / 'vesktop'
        executable.chmod(0o755)
        icon = next((path for path in sorted(target.rglob('*.png')) if 'icon' in path.name.lower()), None)
        installer.write(corsu.HOME / '.local/share/applications/vesktop.desktop',
                        '[Desktop Entry]\nType=Application\nName=Vesktop\nGenericName=Discord\n'
                        'Comment=Discord with Vencord, installed by Corsu\n'
                        f'Exec={executable} %U\nIcon={icon or "discord"}\nTerminal=false\n'
                        'Categories=Network;InstantMessaging;Chat;\nStartupWMClass=vesktop\n')
    return target


def installed_by_corsu():
    return str(corsu.DATA / 'vesktop') in corsu.load_state().get('files', {}) or \
        str(corsu.HOME / 'Applications/Vesktop.app') in corsu.load_state().get('files', {})
