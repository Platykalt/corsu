# Contributing to Corsu

Add or correct `English|French|Corsican` rows in `lexicon.tsv`. Keep the source spelling exactly as it
appears in the application, including apostrophes and case. Use one row per spelling variant. Avoid
duplicate sources with different meanings: this dictionary has no contextual disambiguation.
Have a Corsican speaker review draft translations and agree on consistent terminology.

A row with an empty English field (`|Effacer|Sguassà`) maps a French-only spelling. Write one row with
`%1`, `%2` placeholders to cover every argument of a label: `Restart %1|Redémarrer %1|Rilancià %1` also
translates `Redémarrer { -brand-short-name }`. Keep the same placeholders on both sides of a row; the
test suite rejects rows that drop or invent one. Keep `&` or `_` accelerator markers only if the source
has them — the engine moves the marker onto the translated letter by itself. Write Corsican punctuation
(no blank before `:`, `?`, `!`) and leave the trailing `…` or `:` off the row.

Preserve placeholders, HTML tags and Fluent expressions exactly. Do not translate identifiers, access
keys, keyboard shortcuts or CSS. Plural rows need both the singular and the plural form as separate
lexicon rows; gettext and Qt plural pairs are only written when both forms translate.

Use `python3 coverage.py --output missing-labels.json` for the remaining system UI review queue.
It reads static application resources, not profiles, messages or website text. Review queues can contain
brand names and technical values that should stay unchanged. Do not submit account data or screenshots
containing private messages. Discord labels can be added manually from its interface.

Run `python3 -m unittest -v`, regenerate the plugin, rebuild Vencord and test in an isolated browser profile.
The browser test verifies translation, live updates, restoration, and preservation of chat/name/editing areas.
The native Firefox test verifies real chrome menu labels. Installer tests must use temporary homes and
mock external applications; never patch contributors' real Discord clients during tests.

All Corsu contributions are GPL-3.0-or-later. Include the full license and upstream notices with shared builds.
