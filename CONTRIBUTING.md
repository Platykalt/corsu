# Contributing

The most useful help is checking translations. Most of the 77,000 phrases have not been read by a Corsican
speaker yet.

To report a mistake, [open an issue](https://github.com/Platykalt/corsu/issues/new?template=translation.yml).
Give the text you saw, the program and the place where you saw it, and the Corsican you would use.

## Editing the translations

The translations are plain text files in `lexicon/`, one phrase per line, written `English|French|Corsican`.
Either the English or the French part can be empty:

```
Restart %1|Redémarrer %1|Rilancià %1
|Effacer|Squassà
```

Corrections go in `lexicon/lexicon.tsv`. The two other files are copied from other projects by
`tools/import_translations.py`, so a mistake there is better fixed in the original project (Mozilla's Pontoon,
Weblate, or the project's own repository), where every user of that program benefits.

A few rules keep the files working:

1. Copy the source text exactly as the program shows it, apostrophes and capitals included.
2. Keep placeholders like `%1`, `%s`, `$1` or `{ $name }`, and HTML tags, exactly as they are. You can move them
   around in the sentence. The tests reject a line where one is missing or added.
3. Write `%1`, `%2` for any placeholder: `Restart %1` also matches `Redémarrer { -brand-short-name }` in Firefox.
4. Keep a `&` or `_` before a letter only if the source has one.
5. Put a space before `:`, `?`, `!` and `;`, as the Mozilla and Weblate translations do, and leave a final `…` or
   `:` out of the line: Corsu adds it back.

Use the vocabulary of the existing translations: *unghjetta* for a browser tab, *schedariu* for a file,
*cartulare* for a folder, *parolla d'intesa* for a password.

`python3 tools/coverage.py --output missing-labels.json` lists the text on your computer that is still
untranslated. It only reads program files, not your documents or messages.

## Code

Run the tests with `python3 -m unittest discover -s tests -t .`. [docs/developers.md](docs/developers.md)
explains the layout, the end-to-end checks and how releases are made. Tests must never change a real
installation: use a temporary home folder, and `CORSU_FIREFOX` or `CORSU_CHROMIUM` to point at a test copy of a
browser.

Contributions are published under the GPL, version 3 or later.
