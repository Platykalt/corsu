"""Count the words a built Keyman package really ships: entries of each model, and distinct words among them.

    python3 -I tools/count_kmp.py corsu-keyboard.kmp [more.kmp ...]

The count comes from the compiled `.model.js` inside the package, not from a source word list, because a release
package is what people install.
"""
import re
import sys
import zipfile

ENTRY = re.compile(r'"content":"((?:[^"\\]|\\.)*)"')


def count(path):
    with zipfile.ZipFile(path) as package:
        for name in package.namelist():
            if name.endswith('.model.js'):
                words = ENTRY.findall(package.read(name).decode('utf-8'))
                yield name, len(words), len(set(words)), len({word.casefold() for word in words})


def main(paths):
    found = False
    for path in paths:
        for name, entries, distinct, folded in count(path):
            found = True
            print(f'{path}: {name}: {entries} entries, {distinct} distinct words ({folded} ignoring case)')
    return 0 if found else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
