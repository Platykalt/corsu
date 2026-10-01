#!/usr/bin/env python3
"""Build the Corsican word list and the Keyman prediction package from the Corsu lexicon.

    python3 tools/build_keyboard.py            # wordlist only
    python3 tools/build_keyboard.py --package  # also compile keyboard/build/corsu-keyboard.kmp (needs Node.js)

Reviewed translations count three times as much as the others. A word is kept when it appears at least twice,
or once in a reviewed translation.
"""
import argparse
from collections import Counter
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
import engine  # noqa: E402

PROJECT = ROOT / 'keyboard/platykalt.co.corsu'
WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
SHORT_WORDS = {'a', 'à', 'è', 'e', 'i', 'o', 'u'}


def word_counts():
    counts, reviewed = Counter(), set()
    # The project's lexicons only: the word list ships to everyone, not one person's corrections.
    for path in (path for path in engine.LEXICONS if path != engine.USER and path.exists()):
        weight = 1 if path == engine.LEXICON else 3
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', action='store_true', help='compile the Keyman package with kmc (needs Node.js)')
    args = parser.parse_args()
    words = word_counts()
    wordlist = PROJECT / 'source/wordlist.tsv'
    lines = [f'{word}\t{count}' for word, count in sorted(words.items(), key=lambda item: (-item[1], item[0]))]
    wordlist.write_text('# Corsican words and their frequency in the Corsu lexicon\n' + '\n'.join(lines) + '\n',
                        encoding='utf-8')
    print(f'{wordlist.relative_to(ROOT)}: {len(words)} words')
    if not args.package:
        return
    npx = shutil.which('npx')
    if not npx:
        raise SystemExit('Compiling the Keyman package needs Node.js (npx).')
    subprocess.run([npx, '-y', '@keymanapp/kmc@18', 'build', '--no-error-reporting', str(PROJECT / 'platykalt.co.corsu.kpj')],
                   check=True)
    package = PROJECT / 'build/platykalt.co.corsu.model.kmp'
    target = ROOT / 'keyboard/build/corsu-keyboard.kmp'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(package, target)
    print(f'{target.relative_to(ROOT)} ({target.stat().st_size // 1024} KiB)')


if __name__ == '__main__':
    main()
