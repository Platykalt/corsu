#!/usr/bin/env python3
"""Package an explicit allowlist of public source and runtime artifacts."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / 'release.json').read_text())
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT / 'Vencord', text=True).strip()
    if revision != manifest['vencord_revision']:
        raise RuntimeError('Vencord checkout does not match the pinned release revision.')
    binary = ROOT / 'vendor/VencordInstallerCli-linux'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest['installer_sha256']:
        raise RuntimeError('Official installer checksum mismatch.')
    if not (ROOT / 'Vencord/dist/patcher.js').exists():
        raise RuntimeError('Build the custom Vencord plugin first.')
    # The dictionary is compiled into the bundle, so a stale build ships old Discord labels.
    build = min(path.stat().st_mtime for path in (ROOT / 'Vencord/dist').glob('*.js'))
    stale = [name for name in ('lexicon.tsv', 'plugin/index.ts', 'plugin/translate.ts')
             if (ROOT / name).stat().st_mtime > build]
    if stale:
        print('Warning: Vencord build predates ' + ', '.join(stale)
              + '. Rebuild it so Discord receives the current translations.')
    files = [ROOT / name for name in ('corsu.py', 'engine.py', 'installer.py', 'coverage.py', 'package_release.py',
                                     'lexicon.tsv', 'README.md', 'CONTRIBUTING.md', 'LICENSE', 'release.json',
                                     'install.sh', '.gitignore', 'test_corsu.py', 'test_installer.py',
                                     'test-browser.mjs', 'test-native-firefox.py', 'test-kde.cpp')]
    files.extend(sorted((ROOT / 'plugin').glob('*.ts')))
    files.extend(ROOT / 'vendor' / name for name in ('VencordInstallerCli-linux', 'vencord-installer-source.tar.gz'))
    upstream = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT / 'Vencord').decode().split('\0')
    files.extend(ROOT / 'Vencord' / name for name in upstream if name and (ROOT / 'Vencord' / name).is_file())
    files.extend(sorted((ROOT / 'Vencord/src/userplugins/corsu').glob('*')))
    files.extend(sorted((ROOT / 'Vencord/dist').glob('*.*')))
    # The optional upstream French language pack stays local. Firefox builds are never bundled.
    output = ROOT / 'releases'
    output.mkdir(exist_ok=True)
    name = f'corsu-{manifest["version"]}-linux-x86_64'
    archive = output / f'{name}.tar.gz'
    with tarfile.open(archive, 'w:gz') as bundle:
        for path in sorted(set(files)):
            if not path.is_file() or path.is_symlink():
                raise RuntimeError(f'Required release file missing or symbolic link: {path}')
            bundle.add(path, arcname=f'{name}/{path.relative_to(ROOT)}', recursive=False)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / f'{archive.name}.sha256').write_text(f'{checksum}  {archive.name}\n')
    print(f'{archive} ({archive.stat().st_size / 1024 / 1024:.1f} MiB)\nSHA-256: {checksum}')


if __name__ == '__main__':
    main()
