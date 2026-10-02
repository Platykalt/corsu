"""Install Mozilla's French Firefox for people who do not have Firefox yet, so Corsu can translate it.

The latest version number comes from Mozilla's product details; the file for this system is downloaded from
archive.mozilla.org and checked against the SHA-512 checksums Mozilla publishes for that release. Nothing runs if
the checksum differs.

Linux: unpacked into Corsu's data folder. macOS: Firefox.app copied into ~/Applications. Windows: Mozilla's
installer runs silently into %LOCALAPPDATA%\\Mozilla Firefox, which needs no administrator rights.
"""
import hashlib
import json
import os
import platform
import subprocess
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import corsu
from corsu import t

VERSIONS = 'https://product-details.mozilla.org/1.0/firefox_versions.json'
RELEASES = 'https://archive.mozilla.org/pub/firefox/releases/{version}/'


def target():
    """Where a Firefox downloaded by Corsu lives; firefox_candidates() looks there too."""
    if corsu.PLATFORM == 'windows':
        return Path(os.environ.get('LOCALAPPDATA', corsu.HOME / 'AppData/Local')) / 'Mozilla Firefox'
    if corsu.PLATFORM == 'macos':
        return corsu.HOME / 'Applications/Firefox.app'
    return corsu.DATA / 'firefox-mozilla'


def release_file(version):
    if corsu.PLATFORM == 'windows':
        return f'win64/fr/Firefox Setup {version}.exe'
    if corsu.PLATFORM == 'macos':
        return f'mac/fr/Firefox {version}.dmg'
    machine = 'linux-aarch64' if platform.machine().lower() in ('arm64', 'aarch64') else 'linux-x86_64'
    return f'{machine}/fr/firefox-{version}.tar.xz'


def fetch(url, timeout=60):
    request = urllib.request.Request(url, headers={'User-Agent': 'corsu'})
    return urllib.request.urlopen(request, timeout=timeout)


def download(url, path, expected):
    checksum, done, shown = hashlib.sha512(), 0, -1
    with fetch(url, timeout=120) as response, path.open('wb') as output:
        total = int(response.headers.get('Content-Length') or 0)
        while chunk := response.read(1 << 20):
            output.write(chunk)
            checksum.update(chunk)
            done += len(chunk)
            percent = 6 + int(9 * done / total) if total else 10
            if percent != shown:
                shown = percent
                corsu.progress(percent, f'Downloading Firefox ({done >> 20} MB)', f'Téléchargement de Firefox ({done >> 20} Mo)')
    if checksum.hexdigest() != expected:
        raise RuntimeError(t('The Firefox download does not match Mozilla\'s published checksum; nothing was installed.',
                             'Le téléchargement de Firefox ne correspond pas à la somme publiée par Mozilla ; rien n\'a été installé.'))


def install():
    with fetch(VERSIONS) as response:
        version = json.load(response)['LATEST_FIREFOX_VERSION']
    name = release_file(version)
    base = RELEASES.format(version=version)
    with fetch(base + 'SHA512SUMS') as response:
        sums = dict(reversed(line.split(None, 1)) for line in response.read().decode().splitlines() if line.strip())
    expected = sums.get(name)
    if not expected:
        raise RuntimeError(t(f'Mozilla publishes no checksum for {name}.', f'Mozilla ne publie pas de somme pour {name}.'))
    print(t(f'Installing Firefox {version} (French) from Mozilla…', f'Installation de Firefox {version} (français) depuis Mozilla…'), flush=True)
    installer = corsu.Installer()
    with tempfile.TemporaryDirectory(prefix='corsu-firefox-') as directory:
        folder = Path(directory)
        archive = folder / Path(name).name
        download(base + urllib.parse.quote(name), archive, expected)
        print(t('Checksum verified.', 'Somme de contrôle vérifiée.'), flush=True)
        if corsu.PLATFORM == 'windows':
            # /S: silent; the user's own folder needs no administrator rights.
            subprocess.run([str(archive), '/S', f'/InstallDirectoryPath={target()}'], check=True)
            installer.state['files'][str(target())] = {'backup': None, 'mode': None, 'tree': True, 'toggle': False}
            corsu.STATE.write_text(json.dumps(installer.state, indent=2), encoding='utf-8')
        elif corsu.PLATFORM == 'macos':
            mount = folder / 'mount'
            mount.mkdir()
            subprocess.run(['hdiutil', 'attach', '-nobrowse', '-readonly', '-mountpoint', str(mount), str(archive)],
                           check=True, stdout=subprocess.DEVNULL)
            try:
                installer.tree(target(), mount / 'Firefox.app')
            finally:
                subprocess.run(['hdiutil', 'detach', str(mount)], check=False, stdout=subprocess.DEVNULL)
        else:
            unpacked = folder / 'unpacked'
            unpacked.mkdir()
            with tarfile.open(archive) as bundle:
                if hasattr(tarfile, 'data_filter'):
                    bundle.extractall(unpacked, filter='data')
                else:
                    bundle.extractall(unpacked)
            installer.tree(target(), unpacked / 'firefox')
    return target()


def downloaded():
    return str(target()) in corsu.load_state().get('files', {})

