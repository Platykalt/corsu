# Contribuer · Contributing

[Français](#français) · [English](#english)

## Français

Le plus utile est de corriger les traductions. Pour signaler une erreur, [ouvrez un ticket](https://github.com/Platykalt/corsu/issues/new?template=translation.yml)
avec le texte vu, le logiciel et l'endroit où il apparaît, et le corse que vous utiliseriez.

Pour corriger vous-même : les traductions sont des fichiers texte dans `lexicon/`, une phrase par ligne, écrite
`anglais|français|corse`. L'anglais ou le français peut être vide :

```
Restart %1|Redémarrer %1|Rilancià %1
|Effacer|Squassà
```

Les corrections vont dans `lexicon/lexicon.tsv`. Si une traduction importée est fausse dans un logiciel précis, la
correction va dans `lexicon/lexicon-fixes.tsv`, lu en premier. Les deux autres fichiers sont copiés depuis d'autres projets par
`tools/import_translations.py` : une erreur s'y corrige plutôt dans le projet d'origine (Pontoon de Mozilla,
Weblate, ou le dépôt du projet), pour que tous ses utilisateurs en profitent.

Quelques règles :

1. Recopiez le texte source exactement comme le logiciel l'affiche, apostrophes et majuscules comprises.
2. Gardez les variables (`%1`, `%s`, `$1`, `{ $name }`) et les balises HTML telles quelles ; on peut les déplacer
   dans la phrase.
3. Écrivez `%1`, `%2` pour une variable : `Restart %1` couvre aussi `Redémarrer { -brand-short-name }` dans Firefox.
4. Ne gardez un `&` ou un `_` devant une lettre que si la source en a un.
5. Mettez une espace avant `:`, `?`, `!` et `;`, et laissez le `…` ou le `:` final hors de la ligne.

Suivez le vocabulaire existant : *unghjetta* pour un onglet, *schedariu* pour un fichier, *cartulare* pour un
dossier, *parolla d'intesa* pour un mot de passe.

Pour le code : `python3 -m unittest discover -s tests -t .` lance les tests, et [docs/fr/developpeurs.md](docs/fr/developpeurs.md)
explique le reste. Un test ne doit jamais modifier une vraie installation. Les contributions sont publiées sous GPL,
version 3 ou ultérieure.

## English

The most useful help is correcting translations. To report a mistake, [open an issue](https://github.com/Platykalt/corsu/issues/new?template=translation.yml)
with the text you saw, the program and the place where it appears, and the Corsican you would use.

To correct it yourself: the translations are text files in `lexicon/`, one phrase per line, written
`English|French|Corsican`. Either the English or the French part can be empty:

```
Restart %1|Redémarrer %1|Rilancià %1
|Effacer|Squassà
```

Corrections go in `lexicon/lexicon.tsv`. When an imported translation is wrong for a given program, the correction
goes in `lexicon/lexicon-fixes.tsv`, which is read first. The two other files are copied from other projects by
`tools/import_translations.py`, so a mistake there is better fixed in the original project (Mozilla's Pontoon,
Weblate, or the project's repository), where every user of that program benefits.

A few rules:

1. Copy the source text exactly as the program shows it, apostrophes and capitals included.
2. Keep placeholders (`%1`, `%s`, `$1`, `{ $name }`) and HTML tags as they are; you can move them in the sentence.
3. Write `%1`, `%2` for a placeholder: `Restart %1` also covers `Redémarrer { -brand-short-name }` in Firefox.
4. Keep a `&` or `_` before a letter only if the source has one.
5. Put a space before `:`, `?`, `!` and `;`, and leave a final `…` or `:` out of the line.

Use the existing vocabulary: *unghjetta* for a browser tab, *schedariu* for a file, *cartulare* for a folder,
*parolla d'intesa* for a password.

For code: `python3 -m unittest discover -s tests -t .` runs the tests, and [docs/en/developers.md](docs/en/developers.md)
explains the rest. Tests must never change a real installation. Contributions are published under the GPL, version 3
or later.
