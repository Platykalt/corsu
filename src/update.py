#!/usr/bin/env python3
"""Find and install a newer Corsu release (docs/update-architecture.md).

`check()` asks GitHub for the newest stable release. Its answer is kept in corsu.DATA/update.json for an hour at most,
with the time GitHub gave it; a failed check is never read as "up to date" (docs/update-diagnosis.md).
`python3 update.py --install [--version X.Y.Z]` downloads the archive of that exact release for this system, checks it
against its published SHA-256 and that it is the version asked for, extracts it safely and runs its installer for the
parts already installed (parts switched off stay off). Nothing is installed when any check fails. It prints
`@progress <percent> <text>` lines, then one `@result {json}` line.
`preferences()` / `set_preference()`: corsu.DATA/preferences.json (auto_update, default off).
"""
import argparse
import errno
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

import corsu
from corsu import t
import installer

REPOSITORY = 'https://github.com/Platykalt/corsu'
API = 'https://api.github.com/repos/Platykalt/corsu/releases?per_page=30'
ARCHIVES = {'linux': 'corsu-linux.tar.gz', 'macos': 'corsu-macos.tar.gz', 'windows': 'corsu-windows.zip'}
CACHE = 'update.json'
PREFERENCES = 'preferences.json'
# vlc_complement: VLC's experimental Corsican complement (apps/vlc_complement.py), only when asked for.
DEFAULTS = {'auto_update': False, 'vlc_complement': False}
# How long GitHub's answer is used again without asking. Until 0.25.1 it was 6 hours, so a window opened hours after a
# release could still say "up to date" (docs/update-diagnosis.md).
CHECK_EVERY = 3600
# After a failed check (offline, GitHub's rate limit), wait this long before asking again, unless GitHub said when.
RETRY_AFTER = 15 * 60
VERSION = re.compile(r'v?(\d+)\.(\d+)\.(\d+)')

version_tuple = installer.version_tuple
installed_release = installer.installed_release


def current():
    """The version of this copy of Corsu."""
    return json.loads((corsu.SRC / 'release.json').read_text(encoding='utf-8'))['version']


def download_base():
    """CORSU_DOWNLOAD_BASE, as in install/get.sh: a development override pointing at the same archives in another
    folder (a test build, file:// works). SHA-256 then only proves the download matches the .sha256 fetched from
    that same base (the transfer was not corrupted), not where the files come from; the authenticity of the
    official release rests on HTTPS to github.com. install() announces a non-default base."""
    return os.environ.get('CORSU_DOWNLOAD_BASE', '').rstrip('/')


def download_url(name, version):
    base = download_base()
    if base:
        return f'{base}/{name}'
    # The exact release asked for, never "latest": what was checked is what gets installed.
    return f'{REPOSITORY}/releases/download/v{version}/{name}'


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.corsu-tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temp, path)


# Preferences -------------------------------------------------------------------------------------------------------

def preferences():
    """{'auto_update': bool, ...}: the defaults, overridden by what the person chose."""
    saved = read_json(corsu.DATA / PREFERENCES)
    return {**DEFAULTS, **{name: value for name, value in saved.items() if name in DEFAULTS}}


def set_preference(name, value):
    if name not in DEFAULTS:
        raise ValueError(f'Unknown preference: {name}')
    if type(value) is not type(DEFAULTS[name]):
        raise ValueError(f'{name} must be {type(DEFAULTS[name]).__name__}')
    saved = read_json(corsu.DATA / PREFERENCES)
    saved[name] = value
    write_json(corsu.DATA / PREFERENCES, saved)
    return preferences()


# Checking ----------------------------------------------------------------------------------------------------------

def describe_error(error):
    """A short sentence for the window, in the person's language."""
    if isinstance(error, urllib.error.HTTPError):
        if error.code in (403, 429):
            return t('GitHub limits how often it can be asked; try again later.',
                     'GitHub limite le nombre de demandes ; réessayez plus tard.')
        if error.code == 404:
            return t('Not found on GitHub (HTTP 404).', 'Introuvable sur GitHub (HTTP 404).')
        return t(f'GitHub answered HTTP {error.code}.', f'GitHub a répondu HTTP {error.code}.')
    if isinstance(error, (json.JSONDecodeError, http.client.HTTPException)):
        return t('GitHub\'s answer was incomplete or unreadable.', 'La réponse de GitHub était incomplète ou illisible.')
    if isinstance(error, urllib.error.URLError):
        return t(f'GitHub could not be reached ({error.reason}). Check the connection.',
                 f'GitHub est injoignable ({error.reason}). Vérifiez la connexion.')
    if isinstance(error, OSError):
        if error.errno == errno.ENOSPC:
            return t('Not enough disk space.', 'Pas assez d\'espace disque.')
        if isinstance(error, PermissionError):
            where = f' ({error.filename})' if error.filename else ''
            return t(f'Access refused or file in use{where}. Close Corsu\'s programs and try again.',
                     f'Accès refusé ou fichier utilisé{where}. Fermez les logiciels traduits et réessayez.')
        if isinstance(error, TimeoutError):
            return t('The connection timed out.', 'La connexion a expiré.')
    return str(error)


def error_kind(error):
    """Why a check failed: 'rate_limit', 'http' (GitHub answered with an error), 'network' (no answer) or
    'bad_response' (an answer that is not a list of releases, or one cut short)."""
    if isinstance(error, urllib.error.HTTPError):
        return 'rate_limit' if error.code in (403, 429) else 'http'
    if isinstance(error, (ValueError, KeyError, TypeError, http.client.HTTPException)):
        return 'bad_response'
    return 'network'


def retry_time(error, now):
    """When to ask GitHub again after `error` without being asked to: its Retry-After or rate-limit reset when it
    gave one (6 hours at most), else RETRY_AFTER."""
    headers = getattr(error, 'headers', None) or {}
    try:
        if headers.get('Retry-After'):
            return now + min(max(int(headers['Retry-After']), 0), 6 * 3600)
        if headers.get('X-RateLimit-Remaining') == '0' and headers.get('X-RateLimit-Reset'):
            return min(max(float(headers['X-RateLimit-Reset']), now), now + 6 * 3600)
    except (TypeError, ValueError):
        pass
    return now + RETRY_AFTER


def fetch_latest():
    """The newest stable release on GitHub: (version, tag, url). Drafts and pre-releases are never offered, nor a tag
    without a release (GitHub's list holds releases only). An answer that is not a list is an error, never "nothing
    newer"."""
    request = urllib.request.Request(API, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'corsu-update',
                                                   'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=8) as response:
        releases = json.load(response)
    if not isinstance(releases, list):
        raise ValueError(t('GitHub gave an unexpected answer.', 'GitHub a donné une réponse inattendue.'))
    best = None
    for release in releases:
        if not isinstance(release, dict) or release.get('draft') or release.get('prerelease'):
            continue
        match = VERSION.fullmatch(str(release.get('tag_name', '')))
        if not match:
            continue
        version = '.'.join(match.groups())
        if best is None or version_tuple(version) > version_tuple(best[0]):
            best = (version, release['tag_name'], release.get('html_url') or f'{REPOSITORY}/releases/tag/{release["tag_name"]}')
    if best is None:
        raise ValueError(t('No stable release found on GitHub.', 'Aucune version stable trouvée sur GitHub.'))
    return best


def status_of(running, latest, installed=None):
    """Compared with the newest of this copy and the installed one: an installed copy newer than this window is
    reached by restarting, never by installing it again; a development copy newer than every release is 'ahead'."""
    if not latest:
        return 'unknown'
    base = max((version for version in (running, installed) if version), key=version_tuple)
    if version_tuple(latest) > version_tuple(base):
        return 'available'
    if version_tuple(latest) < version_tuple(base):
        return 'ahead'
    return 'up_to_date'


def installed_version():
    """The installed copy's version, or None (not installed, or installation.json unreadable)."""
    try:
        return (installed_release() or {}).get('version')
    except (RuntimeError, OSError, ValueError):
        return None


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def check(force=False, max_age=CHECK_EVERY):
    """{'current', 'installed', 'latest', 'tag', 'url', 'status', 'checked', 'fresh', 'error', 'error_kind'}.

    status: 'available', 'up_to_date', 'ahead' (this copy is newer than the latest release: a development version)
    or 'unknown' (the check failed: see error and error_kind; never read as up to date). 'latest' and 'checked' are
    GitHub's last good answer and its time, kept after a failure so they can be shown with their date. 'fresh': GitHub
    answered during this call; otherwise the answer is the one saved at 'checked'. GitHub is asked when the saved
    answer is older than `max_age` seconds or `force`; after a failure, not again before its retry time unless
    `force`."""
    path = corsu.DATA / CACHE
    saved = read_json(path)
    now = time.time()
    checked = number(saved.get('checked'))
    good = saved.get('format') == 2 and isinstance(saved.get('latest'), str) and VERSION.fullmatch(saved['latest'])
    running, installed = current(), installed_version()
    # A time in the future (clock changed) is not taken as fresh, nor a saved "latest" older than this copy or the
    # installed one: it was saved before they were installed (an update by the one-line install, or a restart into
    # the new copy), so it says nothing about what is published now.
    fresh_enough = (good and 0 <= now - checked < max_age
                    and status_of(running, saved['latest'], installed) != 'ahead')
    failed_after = number(saved.get('failed')) > checked
    retry = force or now >= number(saved.get('retry_at')) or now < number(saved.get('failed'))
    error = kind = None
    fresh = False
    if force or not fresh_enough:
        if retry:
            try:
                version, tag, url = fetch_latest()
                saved = {'format': 2, 'checked': now, 'latest': version, 'tag': tag, 'url': url}
                fresh = True
            except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as problem:
                error, kind = describe_error(problem), error_kind(problem)
                saved = {**saved, 'failed': now, 'retry_at': retry_time(problem, now), 'error': error, 'error_kind': kind}
            try:
                write_json(path, saved)
            except OSError:
                pass
        else:
            # A recent failure, and the saved answer is too old to stand for a check.
            error = saved.get('error') if failed_after else None
            error = error or t('Not checked yet.', 'Pas encore vérifié.')
            kind = saved.get('error_kind') if failed_after else 'network'
    good = saved.get('format') == 2 and isinstance(saved.get('latest'), str) and VERSION.fullmatch(saved['latest'])
    latest = saved['latest'] if good else None
    return {'current': running, 'installed': installed, 'latest': latest,
            'tag': saved.get('tag') if latest else None, 'url': saved.get('url') if latest else None,
            'status': 'unknown' if error else status_of(running, latest, installed),
            'checked': number(saved.get('checked')) or None if latest else None, 'fresh': fresh, 'error': error,
            'error_kind': kind}


def latest(force=False):
    """Earlier interface, kept for the window until it uses check(): {'version', 'newer', 'url'} or None."""
    info = check(force)
    if not info['latest']:
        return None
    return {'version': info['latest'], 'url': info['url'], 'newer': info['status'] == 'available'}


# Installing --------------------------------------------------------------------------------------------------------

def progress(percent, english, francais):
    print(f'@progress {int(percent)} {t(english, francais)}', flush=True)


def download(url, target, start=10, end=40):
    """Stream `url` to `target`. A download cut short is an error, never a smaller file taken as complete."""
    request = urllib.request.Request(url, headers={'User-Agent': 'corsu-update'})
    with urllib.request.urlopen(request, timeout=60) as response, open(target, 'wb') as output:
        size = int(response.headers.get('Content-Length') or 0) if hasattr(response, 'headers') and response.headers else 0
        done, shown = 0, -1
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            output.write(chunk)
            done += len(chunk)
            if size:
                percent = start + (end - start) * done // size
                if percent != shown:
                    shown = percent
                    progress(percent, f'Downloading {target.name}… {done >> 20} / {size >> 20} MB',
                             f'Téléchargement de {target.name}… {done >> 20} / {size >> 20} Mo')
    if size and done != size:
        raise OSError(t(f'The download of {target.name} was cut short ({done} of {size} bytes); nothing was installed.',
                        f'Le téléchargement de {target.name} a été interrompu ({done} sur {size} octets) ; rien n\'a été installé.'))


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


class UnsafeArchive(ValueError):
    pass


def member_path(name):
    """A member name as a safe relative path, or UnsafeArchive: no absolute path, drive, '..' or empty name."""
    text = name.replace('\\', '/')
    if text.startswith('/') or re.match(r'^[A-Za-z]:', text) or '\0' in text:
        raise UnsafeArchive(f'absolute path in the archive: {name}')
    parts = [part for part in text.split('/') if part not in ('', '.')]
    if any(part == '..' for part in parts):
        raise UnsafeArchive(f'path leaving the folder in the archive: {name}')
    if not parts:
        return None
    return PurePosixPath(*parts)


def inside(path, root):
    try:
        Path(os.path.realpath(path)).relative_to(os.path.realpath(root))
        return True
    except ValueError:
        return False


def write_member(target, stream, mode):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        raise UnsafeArchive(f'the archive writes {target.name} twice')
    with open(target, 'wb') as output:
        shutil.copyfileobj(stream, output)
    os.chmod(target, (mode & 0o755) | 0o600 if mode else 0o644)


def extract_tar(archive, root):
    """Every Python from 3.10 on: files and folders first, checked one by one; links last, and only to a place
    inside the folder. Nothing is written after a link exists, so no file can be written through one."""
    links = []
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            relative = member_path(member.name)
            if relative is None:
                continue
            target = root.joinpath(*relative.parts)
            if not inside(target.parent, root) and target.parent.exists():
                raise UnsafeArchive(f'path leaving the folder in the archive: {member.name}')
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                write_member(target, bundle.extractfile(member), member.mode)
            elif member.issym() or member.islnk():
                links.append((member, relative, target))
            else:
                raise UnsafeArchive(f'special file in the archive: {member.name}')
        for member, relative, target in links:
            if member.islnk():
                source = member_path(member.linkname)
                if source is None or not root.joinpath(*source.parts).is_file():
                    raise UnsafeArchive(f'hard link to a missing file in the archive: {member.name}')
                source = root.joinpath(*source.parts)
                if not inside(source, root):
                    raise UnsafeArchive(f'hard link leaving the folder in the archive: {member.name}')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                continue
            link = member.linkname
            if not link or link.startswith(('/', '\\')) or re.match(r'^[A-Za-z]:', link):
                raise UnsafeArchive(f'link to an absolute path in the archive: {member.name} -> {link}')
            if not inside(target.parent, root):
                raise UnsafeArchive(f'link leaving the folder in the archive: {member.name}')
            # A rule that does not depend on how the system resolves links (Windows does not follow a chain the same
            # way): relative, no "..", and not reached through another link of the archive. Corsu's own archives
            # only link a file to its neighbour (python3 -> python3.13).
            if '..' in re.split(r'[\\/]', link) or any(other is not member and (
                    relative.as_posix() + '/').startswith(member_path(other.name).as_posix() + '/') for other, _, _ in links
                    if other.issym() and member_path(other.name)):
                raise UnsafeArchive(f'link leaving the folder in the archive: {member.name} -> {link}')
            destination = posixpath.normpath(posixpath.join(relative.parent.as_posix(), link))
            if destination.startswith('..') or not inside(target.parent / link, root):
                raise UnsafeArchive(f'link leaving the folder in the archive: {member.name} -> {link}')
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(link, target)


def extract_zip(archive, root):
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        for member in members:
            relative = member_path(member.filename)
            kind = (member.external_attr >> 16) & 0o170000
            if kind == stat.S_IFLNK:
                raise UnsafeArchive(f'link in the archive: {member.filename}')
            if relative is None:
                continue
            target = root.joinpath(*relative.parts)
            if not inside(target.parent, root) and target.parent.exists():
                raise UnsafeArchive(f'path leaving the folder in the archive: {member.filename}')
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            with bundle.open(member) as stream:
                write_member(target, stream, (member.external_attr >> 16) & 0o777)


def safe_extract(archive, root):
    """Extract a release archive into the empty folder `root`; UnsafeArchive (nothing used) for anything that could
    land outside it."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if str(archive).endswith('.zip'):
        extract_zip(archive, root)
    else:
        extract_tar(archive, root)


def installed_components(state=None):
    """The parts recorded as installed (switched off ones too: the installer keeps them off)."""
    state = corsu.load_state() if state is None else state
    components = [name for name in state.get('components', []) if name != 'terminal']
    if state.get('qt_system'):
        components.append('qt')
    return components


def clean_downloads(folder):
    """Downloads that an interrupted update left, older than a day."""
    if folder.is_dir():
        for path in folder.iterdir():
            try:
                if time.time() - path.stat().st_mtime > installer.DAY:
                    shutil.rmtree(path, ignore_errors=True) if path.is_dir() else path.unlink()
            except OSError:
                continue


def python_for(extracted):
    """The new release's own Python when Corsu runs on a copy of the bundled one (so the new copy is used from then
    on), else this Python."""
    current_python = Path(sys.executable).resolve()
    bundled = installer.runtime_python(extracted / 'runtime' / installer.machine())
    runtimes = (corsu.DATA / 'runtime').resolve()
    if bundled.exists() and current_python.is_relative_to(runtimes):
        return bundled
    return Path(sys.executable)


def run_installer(command):
    """Run the new installer, passing its progress on (scaled to 50–98 %) and its output. Returns (code, last line)."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                               errors='replace', env={**os.environ, 'PYTHONUNBUFFERED': '1', 'PYTHONIOENCODING': 'utf-8'})
    last = ''
    for line in process.stdout:
        line = line.rstrip('\n')
        match = re.match(r'@progress (\d+) (.*)', line)
        if match:
            print(f'@progress {50 + int(match[1]) * 48 // 100} {match[2]}', flush=True)
            continue
        print(line, flush=True)
        if line.strip():
            last = line.strip()
    return process.wait(), last


def install(version=None, allow_downgrade=False):
    """Download, check and install a release. Returns the @result dictionary."""
    before = installed_release()
    if not before:
        raise RuntimeError(t('Corsu is not installed yet: run its installer first.',
                             'Corsu n\'est pas encore installé : lancez d\'abord son installeur.'))
    result = {'corsu': 'failed', 'from': before['version'], 'to': version, 'restart_app': False, 'error': None}
    state = corsu.load_state()
    components = installed_components(state)
    if not components:
        raise RuntimeError(t('Nothing is installed yet.', 'Rien n\'est encore installé.'))
    progress(2, 'Looking for the latest version', 'Recherche de la dernière version')
    if version is None and not download_base():
        info = check(force=True)
        if info['status'] == 'unknown' and not info['latest']:
            raise RuntimeError(info['error'] or t('The latest version is unknown.', 'La dernière version est inconnue.'))
        if info['error']:
            raise RuntimeError(info['error'])
        version = info['latest']
        result['to'] = version
        if version_tuple(version) <= version_tuple(before['version']):
            result['corsu'] = 'unchanged'
            return result
    if version and version_tuple(version) < version_tuple(before['version']) and not allow_downgrade:
        raise RuntimeError(t(f'Corsu {before["version"]} is installed; {version} is older. Add --allow-downgrade to go back.',
                             f'Corsu {before["version"]} est installé ; {version} est plus ancien. '
                             'Ajoutez --allow-downgrade pour y revenir.'))
    name = ARCHIVES[corsu.PLATFORM]
    downloads = corsu.DATA / 'tmp'
    clean_downloads(downloads)
    downloads.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='update-', dir=downloads))
    try:
        if download_base():
            progress(9, f'Downloading from {download_base()}, not the official releases (SHA-256 checks the transfer, not the source)',
                     f'Téléchargement depuis {download_base()}, pas les versions officielles (SHA-256 vérifie le transfert, pas la source)')
        progress(10, f'Downloading {name}', f'Téléchargement de {name}')
        download(download_url(name, version), folder / name)
        download(download_url(name + '.sha256', version), folder / 'expected.sha256', 40, 41)
        try:
            expected = (folder / 'expected.sha256').read_text(encoding='utf-8').split()[0].lower()
        except (IndexError, UnicodeDecodeError):
            expected = ''
        if sha256(folder / name) != expected:
            raise RuntimeError(t('The download does not match its published checksum; nothing was installed.',
                                 'Le téléchargement ne correspond pas à sa somme de contrôle publiée ; rien n\'a été installé.'))
        progress(42, 'Checksum verified', 'Somme de contrôle vérifiée')
        extracted = folder / 'extracted'
        try:
            safe_extract(folder / name, extracted)
        except (UnsafeArchive, tarfile.TarError, zipfile.BadZipFile, EOFError) as error:
            raise RuntimeError(t(f'The archive is damaged or unsafe ({error}); nothing was installed.',
                                 f'L\'archive est endommagée ou dangereuse ({error}) ; rien n\'a été installé.')) from None
        root = extracted / 'corsu'
        found = installer.release_version(root)
        if not found or not (root / 'src/installer.py').is_file():
            raise RuntimeError(t('The archive holds no Corsu release; nothing was installed.',
                                 'L\'archive ne contient pas de version de Corsu ; rien n\'a été installé.'))
        if version and found != version:
            raise RuntimeError(t(f'The archive says it is Corsu {found}, not {version}; nothing was installed.',
                                 f'L\'archive dit être Corsu {found}, pas {version} ; rien n\'a été installé.'))
        result['to'] = found
        if version_tuple(found) < version_tuple(before['version']) and not allow_downgrade:
            raise RuntimeError(t(f'Corsu {before["version"]} is installed; the archive is the older {found}. Nothing was installed.',
                                 f'Corsu {before["version"]} est installé ; l\'archive est la version antérieure {found}. '
                                 'Rien n\'a été installé.'))
        progress(48, f'Installing Corsu {found}', f'Installation de Corsu {found}')
        if version_tuple(found) < version_tuple(before['version']):
            # An older installer may not know that parts switched off stay off: give it only the parts switched on.
            components = [name for name in components if not corsu.is_disabled('desktop' if name == 'qt' else name, state)]
            if not components:
                raise RuntimeError(t('Every part is switched off; switch one on before going back.',
                                     'Toutes les parties sont désactivées ; activez-en une avant de revenir en arrière.'))
        command = [str(python_for(root)), str(root / 'src/installer.py'), '--yes', '--components', *components]
        if allow_downgrade:
            command.append('--allow-downgrade')
        code, last = run_installer(command)
        if code:
            raise RuntimeError(t(f'The new version could not be installed; Corsu {before["version"]} is still in place. ({last})',
                                 f'La nouvelle version n\'a pas pu être installée ; Corsu {before["version"]} reste en place. ({last})'))
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    after = installed_release() or {}
    result['to'] = after.get('version', found)
    result['corsu'] = 'repaired' if version_tuple(result['to']) == version_tuple(before['version']) else 'updated'
    app_root = os.environ.get('CORSU_APP_ROOT') or str(corsu.ROOT)
    result['restart_app'] = bool(after) and installer.folder_name(after['folder']) != installer.folder_name(app_root)
    progress(100, 'Done', 'Terminé')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', help='Install the latest stable release (or --version)')
    parser.add_argument('--version', help='With --install: this exact release, X.Y.Z')
    parser.add_argument('--allow-downgrade', action='store_true', help='With --install: allow an older release')
    parser.add_argument('--check', action='store_true', help='Print what check() finds (the default)')
    args = parser.parse_args(argv)
    if args.version and not VERSION.fullmatch(args.version):
        parser.error('--version takes X.Y.Z')
    import logbook
    if not args.install:
        print(json.dumps(check(force=True), ensure_ascii=False))
        return 0
    version = args.version.lstrip('v') if args.version else None
    try:
        with corsu.lock('update'):
            result = install(version, args.allow_downgrade)
    except corsu.Busy as error:
        result = {'corsu': 'failed', 'busy': True, 'error': str(error)}
    except (RuntimeError, OSError, ValueError) as error:
        logbook.failure(error)
        result = {'corsu': 'failed', 'error': describe_error(error) if isinstance(error, OSError) else str(error)}
    except Exception as error:
        result = {'corsu': 'failed', 'error': logbook.failure(error)}
    result = {'corsu': 'failed', 'from': None, 'to': version, 'restart_app': False, 'error': None, **result}
    if result['corsu'] == 'failed':
        try:
            result['from'] = result['from'] or (installed_release() or {}).get('version')
        except RuntimeError:
            pass
        print(result['error'], file=sys.stderr, flush=True)
    print('@result ' + json.dumps(result, ensure_ascii=False), flush=True)
    return 1 if result['corsu'] == 'failed' else 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    import logbook
    logbook.start('update')
    raise SystemExit(main())
