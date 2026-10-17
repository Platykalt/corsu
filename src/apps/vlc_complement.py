"""VLC's Corsican complement (experimental, Linux, off unless the person asks for it).

VLC's Corsican catalogue (Patriccollu di Santa Maria è Sichè's) leaves 1,760 messages of VLC 3.0.x in English.
contrib/vlc/co.po adds AI drafts for them; review.json says which were reviewed by AI (none by a speaker yet). The
complement is the upstream translations plus the drafts whose status is in STATUSES, compiled here, offline.

How VLC is made to read it without touching any system file: VLC 3.0.x binds its messages to
config_GetDataDir() + "/../locale" (src/modules/textdomain.c), and on Linux config_GetDataDir() is $VLC_DATA_PATH
when set (src/linux/dirs.c). Corsu builds corsu.DATA/vlc/share/vlc (one link per entry of VLC's own data folder,
so Lua scripts, skins and the web interface stay VLC's) and corsu.DATA/vlc/share/locale (the complement as Corsican,
links to VLC's catalogue of every other language for the fallbacks), and VLC's menu entry starts it with
VLC_DATA_PATH pointing there. Checked with VLC 3.0.20 (Ubuntu 24.04) and 3.0.24 (Debian 13), in their help text
and their Qt interface (tests/e2e/check_vlc_experimental.py). Switching the complement off, or VLC off, gives back
the system catalogue; uninstalling Corsu removes the folder.

Not handled: Windows and macOS (VLC_DATA_PATH exists there too, but nothing was checked), the Flatpak and the Snap.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil

import corsu

FOLDER = corsu.ROOT / 'contrib' / 'vlc'
STATUSES = ('ai_reviewed', 'human')
PREFERENCE = 'vlc_complement'


def enabled():
    import update
    return bool(update.preferences().get(PREFERENCE))


def _unquote(text):
    return json.loads(text) if text.startswith('"') else ''


def entries(folder=None):
    """(upstream, added): {key: value} for the .mo, key and value as gettext writes them (context\\x04id,
    plural forms joined by \\0). `added` holds the Corsu drafts whose review status is in STATUSES."""
    folder = Path(folder or FOLDER)
    review = json.loads((folder / 'review.json').read_text(encoding='utf-8'))
    upstream, added = {}, {}
    for block in (folder / 'co.po').read_text(encoding='utf-8').split('\n\n'):
        fields, flags, corsu_entry, field = {}, [], False, None
        for line in block.split('\n'):
            if line.startswith('#,'):
                flags += [flag.strip() for flag in line[2:].split(',')]
            elif line.startswith('# Corsu: '):
                corsu_entry = True
            elif line.startswith('#') or not line:
                continue
            elif line.startswith('"') and field:
                fields[field] += _unquote(line)
            else:
                field, _, value = line.partition(' ')
                fields[field] = _unquote(value)
        if 'msgid' not in fields:
            continue
        key = fields['msgid']
        if 'msgctxt' in fields:
            key = fields['msgctxt'] + '\x04' + key
        if 'msgid_plural' in fields:
            key += '\x00' + fields['msgid_plural']
            forms = [value for name, value in sorted(fields.items()) if name.startswith('msgstr[')]
            value = '\x00'.join(forms) if all(forms) else ''
        else:
            value = fields.get('msgstr', '')
        if not value:
            continue
        if corsu_entry:
            name = hashlib.sha1(key.split('\x00')[0].encode('utf-8')).hexdigest()[:12]
            if review.get(name, {}).get('status') in STATUSES:
                added[key] = value
        elif 'fuzzy' not in flags:
            upstream[key] = value
    return upstream, added


PRI = re.compile(r'<PRI([diouxX])(64|32|16|8|MAX|PTR)>')


def system_forms(key, value):
    """The messages a .mo holds for one with <PRId64>-style macros: one per expansion, as msgfmt writes them (64-bit
    integers are %ld on 64-bit Linux, %lld elsewhere)."""
    if not PRI.search(key):
        return {key: value}
    forms = {}
    for long in ('l', 'll'):
        def expand(text):
            return PRI.sub(lambda match: match.group(1) if match.group(2) in ('32', '16', '8')
                           else long + match.group(1), text)
        forms[expand(key)] = expand(value)
    return forms


def catalog(folder=None):
    """(.mo bytes, number of upstream messages, number of Corsu messages)."""
    import engine
    upstream, added = entries(folder)
    messages = {}
    for key, value in {**upstream, **added}.items():
        messages.update(system_forms(key, value))
    return engine.make_mo(messages), len(upstream) - 1, len(added)


def data_folder(executable):
    """VLC's own data folder, <prefix>/share/vlc, as libvlccore finds it for a distribution package."""
    folder = Path(executable).resolve().parent.parent / 'share' / 'vlc'
    return folder if folder.is_dir() else None


def unsupported(executable, version):
    """Why the complement cannot be used with this VLC, or None."""
    if corsu.PLATFORM != 'linux':
        return corsu.t('the Corsican complement is only checked on Linux', 'le complément corse n\'est vérifié que sous Linux')
    if not (FOLDER / 'co.po').exists() or not (FOLDER / 'review.json').exists():
        return corsu.t('this copy of Corsu has no VLC complement', 'cette copie de Corsu n\'a pas de complément VLC')
    if not version or not re.match(r'3\.0\.', version):
        return corsu.t(f'the complement is made for VLC 3.0.x, not {version or "an unknown version"}',
                       f'le complément est fait pour VLC 3.0.x, pas {version or "une version inconnue"}')
    if data_folder(executable) is None:
        return corsu.t('VLC\'s data folder was not found', 'dossier de données de VLC introuvable')
    return None


def prepare(installer, executable):
    """Build corsu.DATA/vlc for this VLC; returns (VLC_DATA_PATH value, upstream count, Corsu count)."""
    source = data_folder(executable)
    locale = source.parent / 'locale'
    data, upstream, added = catalog()
    staging = corsu.DATA / 'vlc.corsu-build'
    shutil.rmtree(staging, ignore_errors=True)
    share = staging / 'share'
    (share / 'vlc').mkdir(parents=True)
    for entry in sorted(source.iterdir()):
        (share / 'vlc' / entry.name).symlink_to(entry)
    target = share / 'locale' / 'co' / 'LC_MESSAGES'
    target.mkdir(parents=True)
    (target / 'vlc.mo').write_bytes(data)
    for other in sorted(locale.glob('*/LC_MESSAGES/vlc.mo')):
        language = other.parent.parent.name
        if language != 'co':
            (share / 'locale' / language / 'LC_MESSAGES').mkdir(parents=True)
            (share / 'locale' / language / 'LC_MESSAGES' / 'vlc.mo').symlink_to(other)
    installer.tree(corsu.DATA / 'vlc', staging)
    installer.state['files'][str(corsu.DATA / 'vlc')]['component'] = 'vlc'
    corsu.save_state(installer.state)
    shutil.rmtree(staging, ignore_errors=True)
    return corsu.DATA / 'vlc' / 'share' / 'vlc', upstream, added


def remove(installer):
    """Take the complement away (switched off in the preferences)."""
    path = corsu.DATA / 'vlc'
    if installer.state['files'].pop(str(path), None) is not None:
        shutil.rmtree(path, ignore_errors=True)
        corsu.save_state(installer.state)


def drafts_included():
    """How many Corsu translations the complement holds (review statuses in STATUSES), without compiling it."""
    try:
        review = json.loads((FOLDER / 'review.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return 0
    return sum(1 for record in review.values() if record.get('status') in STATUSES)


def status():
    """What the window and the command line show: {'enabled': the person's choice, 'available': whether this
    computer has a VLC the complement works with, 'reason': why not, 'translations': how many it adds}. The choice is
    the preference 'vlc_complement' (update.preferences), the same one --vlc-complement on|off writes."""
    import apps
    from apps import vlc
    reason = None
    if corsu.PLATFORM != 'linux':
        reason = unsupported(None, None)
    else:
        executable = apps.which('vlc')
        if not executable:
            reason = corsu.t('only for VLC installed from the system\'s packages; none found',
                             'seulement pour le VLC installé par les paquets du système ; aucun trouvé')
        elif executable.startswith('/snap/'):
            reason = corsu.t('not for the Snap of VLC', 'pas pour le Snap de VLC')
        else:
            reason = unsupported(executable, vlc.version(executable))
    return {'enabled': enabled(), 'available': reason is None, 'reason': reason, 'translations': drafts_included()}
