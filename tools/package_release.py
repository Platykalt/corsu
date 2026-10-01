#!/usr/bin/env python3
"""Package an explicit allowlist of public source and runtime artifacts for each platform."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
# Stable names, so https://github.com/<owner>/corsu/releases/latest/download/<name> always works.
ARCHIVES = {'linux': 'corsu-linux.tar.gz', 'windows': 'corsu-windows.zip', 'macos': 'corsu-macos.tar.gz'}
SOURCES = ('README.md', 'README.en.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE')
SOURCE_DIRECTORIES = ('src', 'lexicon', 'docs', 'install', 'tests', 'tools')


def vencord_installer(manifest, name):
    """Fetch the pinned official installer for one platform and verify it before packaging."""
    entry = manifest['installers'][name]
    binary = ROOT / 'vendor' / entry['file']
    if not binary.exists():
        with urllib.request.urlopen(manifest['installer_base_url'] + entry['file'], timeout=120) as response:
            binary.write_bytes(response.read())
    if hashlib.sha256(binary.read_bytes()).hexdigest() != entry['sha256']:
        raise RuntimeError(f'Official installer checksum mismatch: {binary}')
    return binary


def collect(manifest):
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT / 'Vencord', text=True).strip()
    if revision != manifest['vencord_revision']:
        raise RuntimeError('Vencord checkout does not match the pinned release revision.')
    if not (ROOT / 'Vencord/dist/patcher.js').exists():
        raise RuntimeError('Build the custom Vencord plugin first.')
    # The dictionary is compiled into the bundle, so a stale build ships old Discord labels.
    build = min(path.stat().st_mtime for path in (ROOT / 'Vencord/dist').glob('*.js'))
    stale = [name for name in ('lexicon/lexicon.tsv', 'lexicon/lexicon-mozilla.tsv', 'lexicon/lexicon-upstream.tsv',
                               'src/discord-plugin/index.ts', 'src/discord-plugin/translate.ts')
             if (ROOT / name).stat().st_mtime > build]
    if stale:
        raise RuntimeError('Vencord build predates ' + ', '.join(stale) + '. Rebuild it before packaging.')
    files = [ROOT / name for name in SOURCES if (ROOT / name).exists()]
    for directory in SOURCE_DIRECTORIES:
        files.extend(path for path in sorted((ROOT / directory).rglob('*'))
                     if path.is_file() and '__pycache__' not in path.parts)
    files.append(ROOT / 'vendor/vencord-installer-source.tar.gz')
    # The French Firefox language pack (MPL-2.0) is the offline fallback; installs fetch the matching version.
    files.append(ROOT / 'vendor/firefox-fr.xpi')
    upstream = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT / 'Vencord').decode().split('\0')
    files.extend(ROOT / 'Vencord' / name for name in upstream if name and (ROOT / 'Vencord' / name).is_file())
    files.extend(sorted((ROOT / 'Vencord/src/userplugins/corsu').glob('*')))
    files.extend(sorted((ROOT / 'Vencord/dist').glob('*.*')))
    for path in files:
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f'Required release file missing or symbolic link: {path}')
    return sorted(set(files))


def archive_name(path):
    """Where a file goes in the archive: the installers sit at the top, where people double-click them."""
    relative = path.relative_to(ROOT).as_posix()
    if relative.startswith('install/Install for '):
        return relative[len('install/'):]
    return relative


def package(manifest, name, files, output):
    files = [*files, vencord_installer(manifest, name)]
    stem = 'corsu'
    executable = {'Install for Linux.sh', 'Install for macOS.command', 'get.sh', manifest['installers'][name]['file']}
    if name == 'windows':
        archive = output / ARCHIVES[name]
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for path in files:
                bundle.write(path, f'{stem}/{archive_name(path)}')
    else:
        archive = output / ARCHIVES[name]

        def normalize(info):
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            info.mode = 0o755 if Path(info.name).name in executable else 0o644
            return info

        with tarfile.open(archive, 'w:gz') as bundle:
            for path in files:
                bundle.add(path, arcname=f'{stem}/{archive_name(path)}', recursive=False,
                           filter=normalize)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / f'{archive.name}.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='utf-8')
    print(f'{archive} ({archive.stat().st_size / 1024 / 1024:.1f} MiB)\nSHA-256: {checksum}')
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platforms', nargs='+', choices=sorted(ARCHIVES), default=sorted(ARCHIVES))
    parser.add_argument('--output', type=Path, default=ROOT / 'releases')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'src/release.json').read_text(encoding='utf-8'))
    files = collect(manifest)
    args.output.mkdir(parents=True, exist_ok=True)
    for name in args.platforms:
        package(manifest, name, files, args.output)


if __name__ == '__main__':
    main()
