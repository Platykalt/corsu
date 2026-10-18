#!/usr/bin/env python3
"""Build the Corsican word lists and the Keyman prediction packages.

    python3 tools/build_keyboard.py            # word lists only
    python3 tools/build_keyboard.py --package  # also compile the packages into keyboard/build/ (needs Node.js)

Three lexical models are built, all for the language tag `co`, for the same keyboard (EuroLatin):

    platykalt.co.corsu              corsu-keyboard.kmp              Corsu: no preference
    platykalt.co.corsu_cismuntincu  corsu-keyboard-cismuntincu.kmp  Corsu – Cismuntincu (experimental)
    platykalt.co.corsu_pumuntincu   corsu-keyboard-pumuntincu.kmp   Corsu – Pumuntincu (experimental)

The words come from keyboard/data (see keyboard/data/REVIEW.md): UTF-8, tab-separated files with the header
`word weight variant source license status`, one word per line as it is written (a name keeps its capital).

- corsu-keyboard.kmp is shared.tsv alone, which holds both varieties' forms;
- a preference model is shared.tsv with the variety's file laid over it: a word present in both takes the
  variety's weight. The variety files also hold the other variety's forms at a lower weight, so nothing is removed.

Rows whose status is `rejected` are left out. Without keyboard/data/shared.tsv, the three models fall back to the
words of the Corsu lexicon (the interface translations, lowercased).

Words are kept in their written case: the models declare `languageUsesCasing`, so Keyman matches the case being
typed (Eccu, ECCU) and its search ignores case and accents.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
KEYBOARD = ROOT / 'keyboard'
DATA = KEYBOARD / 'data'
# The Keyman Developer compiler, pinned to the stable Keyman release the packages are tested with.
KMC = '@keymanapp/kmc@18.0.254'
WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
SHORT_WORDS = {'a', 'à', 'è', 'e', 'i', 'o', 'u'}
VARIANTS = ('cismuntincu', 'pumuntincu')
COLUMNS = ['word', 'weight', 'variant', 'source', 'license', 'status']
LEFT_OUT = {'rejected'}


class Model:
    def __init__(self, model_id, name, variant, package):
        self.id, self.name, self.variant, self.package = model_id, name, variant, package

    def project(self, keyboard=KEYBOARD):
        return keyboard / self.id

    def wordlist(self, keyboard=KEYBOARD):
        return self.project(keyboard) / 'source/wordlist.tsv'


MODELS = [
    Model('platykalt.co.corsu', 'Corsu', None, 'corsu-keyboard.kmp'),
    Model('platykalt.co.corsu_cismuntincu', 'Corsu – Cismuntincu (experimental)', 'cismuntincu',
          'corsu-keyboard-cismuntincu.kmp'),
    Model('platykalt.co.corsu_pumuntincu', 'Corsu – Pumuntincu (experimental)', 'pumuntincu',
          'corsu-keyboard-pumuntincu.kmp'),
]


def lexicon_counts(paths):
    """Words of the interface translations, lowercased: {word: count}.

    Interface labels capitalise many common words, so a capital there says nothing about a proper noun; proper
    nouns get their capital from keyboard/data.
    """
    counts, reviewed = Counter(), set()
    for path, weight in paths:
        for line in path.read_text(encoding='utf-8').splitlines():
            fields = line.split('|')
            if line.startswith('#') or len(fields) != 3:
                continue
            # Placeholders, markup and entities are not words.
            text = re.sub(r'%\w+|\{[^}]*\}|<[^>]+>|&\w+;|\$\w+', ' ', fields[2])
            for word in WORD.findall(text):
                word = word.replace('’', "'")
                if word.isupper() and len(word) > 1:
                    continue
                word = word.lower()
                if len(word) < 2 and word not in SHORT_WORDS:
                    continue
                counts[word] += weight
                if weight > 1:
                    reviewed.add(word)
    return {word: count for word, count in counts.items() if count >= 2 or word in reviewed}


def project_lexicons():
    sys.path.insert(0, str(ROOT / 'src'))
    import engine  # noqa: E402
    # The project's lexicons only: the word list ships to everyone, not one person's corrections.
    return [(path, 1 if path == engine.LEXICON else 3)
            for path in engine.LEXICONS if path != engine.USER and path.exists()]


def read_data(path):
    """The rows of one keyboard/data file, checked: {word: weight}, in file order."""
    rows = {}
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.reader(handle, delimiter='\t', quoting=csv.QUOTE_NONE)
        header = next(reader, None)
        if header != COLUMNS:
            raise SystemExit(f'{path}: the header must be {chr(9).join(COLUMNS)!r}, not {header!r}')
        for number, row in enumerate(reader, start=2):
            if not row or row[0].startswith('#'):
                continue
            if len(row) != len(COLUMNS):
                raise SystemExit(f'{path}:{number}: {len(COLUMNS)} tab-separated columns expected')
            word, weight, variant, _source, _license, status = (field.strip() for field in row)
            if variant not in ('shared', *VARIANTS):
                raise SystemExit(f'{path}:{number}: unknown variant {variant!r}')
            if not word or not weight.isdigit() or int(weight) < 1:
                raise SystemExit(f'{path}:{number}: a word and a positive whole weight are needed')
            if status.lower() in LEFT_OUT:
                continue
            word = word.replace('’', "'")
            if word in rows:
                raise SystemExit(f'{path}:{number}: {word!r} is listed twice')
            rows[word] = int(weight)
    return rows


def model_words(model, data):
    """{word: weight} for one model: shared.tsv, with the preferred variety's file laid over it."""
    words = dict(read_data(data / 'shared.tsv'))
    if model.variant:
        words.update(read_data(data / f'{model.variant}.tsv'))
    return words


def write_wordlist(model, words, keyboard=KEYBOARD):
    lines = [f'{word}\t{count}' for word, count in sorted(words.items(), key=lambda item: (-item[1], item[0]))]
    header = f'# {model.name}: Corsican words and their weight, built by tools/build_keyboard.py\n'
    model.wordlist(keyboard).write_text(header + '\n'.join(lines) + '\n', encoding='utf-8')


def name_models(package, names):
    """Give each lexical model of a compiled package its readable name in kmp.json.

    kmc (18.0 and 19.0) writes the model id as the name, and Keyman for Android and iOS show that name in the
    dictionary settings. Only that field changes; every other member is copied as it is.
    """
    with zipfile.ZipFile(package) as source:
        members = [(info, source.read(info)) for info in source.infolist()]
    temporary = package.with_suffix('.tmp')
    with zipfile.ZipFile(temporary, 'w') as target:
        for info, data in members:
            if info.filename == 'kmp.json':
                metadata = json.loads(data)
                for model in metadata.get('lexicalModels', []):
                    model['name'] = names.get(model['id'], model['name'])
                data = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')
            target.writestr(info, data, compress_type=info.compress_type)
    temporary.replace(package)


def compile_packages(keyboard=KEYBOARD):
    npx = shutil.which('npx')
    if not npx:
        raise SystemExit('Compiling the Keyman packages needs Node.js (npx).')
    build = keyboard / 'build'
    build.mkdir(parents=True, exist_ok=True)
    for model in MODELS:
        project = model.project(keyboard)
        subprocess.run([npx, '-y', KMC, 'build', '--no-error-reporting', str(project / f'{model.id}.kpj')], check=True)
        target = build / model.package
        shutil.copy2(project / f'build/{model.id}.model.kmp', target)
        name_models(target, {model.id: model.name})
        print(f'{target} ({target.stat().st_size // 1024} KiB)')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--package', action='store_true', help='compile the Keyman packages with kmc (needs Node.js)')
    parser.add_argument('--data', type=Path, default=DATA, help='the word data folder (default: keyboard/data)')
    parser.add_argument('--keyboard', type=Path, default=KEYBOARD,
                        help='the folder holding the model projects, for a test copy (default: keyboard)')
    args = parser.parse_args()
    lexicon = None if (args.data / 'shared.tsv').exists() else lexicon_counts(project_lexicons())
    for model in MODELS:
        words = lexicon if lexicon is not None else model_words(model, args.data)
        write_wordlist(model, words, args.keyboard)
        print(f'{model.wordlist(args.keyboard)}: {len(words)} words')
    if args.package:
        compile_packages(args.keyboard)


if __name__ == '__main__':
    main()
