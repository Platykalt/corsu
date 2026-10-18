# Instructions for agents working on Corsu

These rules apply to every person or program (AI assistants included) that changes Corsu. They complement
[CONTRIBUTING.md](CONTRIBUTING.md), [lexicon/REVIEWS.md](lexicon/REVIEWS.md) and [docs/continuite.md](docs/continuite.md).

## Translating

1. **Translate the full meaning before the abbreviation.** When a label contains an abbreviation, first find the
   full expression it stands for and its function in the interface (title, button, field, unit…), then translate
   that expression in its context. In a Discord profile, "Bio" means "Biographie", not "biologique".
   - Prefer full words when they are natural and fit the interface. Shorten the translation only when the display
     requires it, with a form that stays understandable and consistent.
   - Keep usual technical acronyms, identifiers and proper names when translating them would be wrong.
   - One abbreviation can stand for several things ("Min": minimum or minutes; "Mod": moderator or modification):
     never deduce its translation from its form alone, nor from its use in another program.
   - A sense collision that is fixed gets a regression test (see `tests/test_discord_words.py`).
2. **Context before reuse.** A label imported from another program is reused only when its sense is the same in
   both. A polysemous term is never replaced globally: correct it in the application's own section or in
   `lexicon/lexicon-fixes.tsv`.
3. **Say where each translation comes from.** For every linguistic correction, record which of these it rests on:
   an external source consulted (named), a usage already present in Corsu (cited, and not counted as an independent
   validation: repeating a word in our own lexicon proves nothing), or an AI proposal. An AI review is never
   presented as a human validation; review proposals are kept apart from corrections actually applied.
4. **User content stays as written**: names, nicknames, statuses, server, channel and role names, messages. Only
   the interface part of a mixed label is translated.

## Testing and publishing

- Tests never touch a real installation: run them with `HOME=$(mktemp -d)` and throwaway profiles or containers.
  Unit tests: `HOME=$(mktemp -d) python3 -m unittest discover -s tests -t .`.
- Keep exit codes; never filter logs in a way that hides a failure.
- Do not publish a release, create or move a tag, merge into `main`, or contact anyone (upstream projects,
  translators, Crowdin) without an explicit instruction from the maintainer.
- Say what was really observed and on which platform; a simulated page or one engine does not validate another.
