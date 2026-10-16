"""Write src/webext/glossary/shared.json from the curated list glossary/shared-labels.txt.

Each label is looked up by its English text in Corsu's lexicon, in the order Corsu's engine uses (first row wins):
lexicon-fixes.tsv, the reviewed imports (lexicon-mozilla.tsv, lexicon-upstream.tsv), then the drafts of
lexicon.tsv. Only the curated labels go to the extension, never the whole lexicon.

    python3 src/webext/tools/build_shared.py          # rewrite shared.json
    python3 src/webext/tools/build_shared.py --check  # exit 1 if shared.json is out of date
"""
import json
import sys
from pathlib import Path

WEBEXT = Path(__file__).resolve().parent.parent
ROOT = WEBEXT.parent.parent
LEXICONS = [('lexicon-fixes.tsv', 'reviewed'), ('lexicon-mozilla.tsv', 'reviewed'),
            ('lexicon-upstream.tsv', 'reviewed'), ('lexicon.tsv', 'draft')]
LIST = WEBEXT / 'glossary/shared-labels.txt'
OUTPUT = WEBEXT / 'glossary/shared.json'


def index():
    found = {}
    for name, status in LEXICONS:
        for line in (ROOT / 'lexicon' / name).read_text(encoding='utf-8').splitlines():
            if line.startswith('#'):
                continue
            fields = [field.strip() for field in line.split('|')]
            if len(fields) == 3 and fields[0] and fields[2]:
                found.setdefault(fields[0], (fields[2], status, name))
    return found


def build():
    rows = index()
    entries, missing = [], []
    for label in LIST.read_text(encoding='utf-8').splitlines():
        label = label.strip()
        if not label or label.startswith('#'):
            continue
        if label not in rows:
            missing.append(label)
            continue
        corsican, status, origin = rows[label]
        entries.append({'source': label, 'co': corsican, 'status': status, 'origin': origin})
    if missing:
        raise SystemExit('Not in the lexicon (add a row there first): ' + ', '.join(missing))
    data = {'site': 'shared', 'source_language': 'en',
            'generated_by': 'src/webext/tools/build_shared.py from glossary/shared-labels.txt',
            'entries': entries}
    return json.dumps(data, ensure_ascii=False, indent=1) + '\n'


if __name__ == '__main__':
    text = build()
    if '--check' in sys.argv[1:]:
        current = OUTPUT.read_text(encoding='utf-8') if OUTPUT.exists() else ''
        sys.exit(0 if current == text else 'shared.json is out of date: run src/webext/tools/build_shared.py')
    OUTPUT.write_text(text, encoding='utf-8')
    print(f'{OUTPUT}: {text.count("source")} entries')
