"""The Review page of the Corsu app: go through translations written for Corsu, confirm or correct them.

Corrections are kept with Corsu's data (lexicon-user.tsv, loaded before every other lexicon) and copied into the
Discord plugin's settings, so they apply without rebuilding anything. Nothing is sent anywhere: the person can
choose to open a GitHub issue with their corrections.
"""
from functools import lru_cache
import json
import urllib.parse

import corsu
import engine

SECTIONS = ('Discord', 'Google')
STATE_FILE = 'review.json'
ISSUE_URL = 'https://github.com/Platykalt/corsu/issues/new'
VENCORD_SETTINGS = ('Vencord/settings/settings.json', 'vesktop/settings/settings.json')


@lru_cache(maxsize=None)
def rows(section):
    """(English, French, Corsican) rows of a section of lexicon.tsv, shortest first: those are seen most."""
    found, inside = [], False
    for line in engine.LEXICON.read_text(encoding='utf-8').splitlines():
        if line.startswith('# '):
            inside = line.startswith(f'# {section}:')
            continue
        fields = line.split('|')
        if inside and len(fields) == 3 and fields[2].strip():
            found.append(tuple(field.strip() for field in fields))
    return tuple(sorted(found, key=lambda row: (len(row[1] or row[0]), row[1] or row[0])))


def load_state():
    path = corsu.DATA / STATE_FILE
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'verdicts': {}, 'fixes': {}, 'options': {}}


def save_state(state):
    corsu.DATA.mkdir(parents=True, exist_ok=True)
    (corsu.DATA / STATE_FILE).write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')


def key(row):
    return row[1] or row[0]


def progress(section):
    state = load_state()
    all_rows = rows(section)
    done = sum(1 for row in all_rows if key(row) in state['verdicts'])
    return {'total': len(all_rows), 'done': done, 'fixed': len(state['fixes'])}


def next_item(section):
    state = load_state()
    for row in rows(section):
        if key(row) not in state['verdicts']:
            english, french, corsican = row
            return {'english': english, 'french': french, 'corsican': state['fixes'].get(key(row), corsican)}
    return None


def write_user_lexicon(fixes):
    path = engine.USER
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ['# Corrections made in the Corsu app. English|French|Corsican']
    lines += [f"{fix['english']}|{fix['french']}|{fix['corsican']}" for fix in fixes.values()]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def plugin_settings(fields):
    """Write fields into the Corsu plugin settings of each installed Vencord (Discord, Vesktop)."""
    installer = corsu.Installer()
    for relative in VENCORD_SETTINGS:
        path = corsu.CONFIG / relative
        if path.exists():
            installer.json_settings(path, {f'plugins/Corsu/{name}': value for name, value in fields.items()})


def record(french, english, verdict, corsican=None):
    """verdict is 'ok', 'skip' or 'fix'; a fix needs the corrected Corsican."""
    if verdict not in ('ok', 'skip', 'fix'):
        raise ValueError(verdict)
    state = load_state()
    item = french or english
    state['verdicts'][item] = verdict
    if verdict == 'fix':
        corsican = (corsican or '').strip()
        if not corsican or '|' in corsican or '\n' in corsican:
            raise ValueError('The correction must be one line, without |.')
        for source in (english, french):
            if source and engine.signature(source) != engine.signature(corsican):
                raise ValueError('Keep the placeholders of the original text (%1, {name}…).')
        state['fixes'][item] = {'english': english, 'french': french, 'corsican': corsican}
        write_user_lexicon(state['fixes'])
        corrections = {}
        for fix in state['fixes'].values():
            for source in (fix['english'], fix['french']):
                if source:
                    corrections[engine.normalize(source)] = fix['corsican']
        plugin_settings({'corrections': json.dumps(corrections, ensure_ascii=False)})
    save_state(state)
    return progress_all()


def progress_all():
    return {section: progress(section) for section in SECTIONS}


def issue_link():
    """A GitHub issue prefilled with the corrections, for the person to send if they want to."""
    fixes = load_state()['fixes'].values()
    body = '\n'.join(f"{fix['english']}|{fix['french']}|{fix['corsican']}" for fix in fixes)
    text = 'Corrections made in the Corsu app (English|French|Corsican):\n\n```\n' + body + '\n```\n'
    url = ISSUE_URL + '?' + urllib.parse.urlencode({'title': 'Translation corrections', 'body': text})
    # Browsers and GitHub refuse very long addresses; past that the page offers to copy the list instead.
    return {'url': url if len(url) < 7500 else ISSUE_URL, 'text': body, 'count': len(load_state()['fixes'])}


def set_option(name, value):
    """Options shared by the Corsu parts; only showOriginal exists for now."""
    if name != 'showOriginal':
        raise ValueError(name)
    state = load_state()
    state.setdefault('options', {})[name] = bool(value)
    save_state(state)
    plugin_settings({'showOriginal': bool(value)})
    return state['options']


def options():
    return load_state().get('options', {})
