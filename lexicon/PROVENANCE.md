# Where the lexicon rows come from

State on 18 October 2026, measured from the files and the Git history. This is a bounded check (file headers, import
script, commits that created the large sections), not a row-by-row reconstruction.

## Three classes

| Class | Files | Rows | What is known |
| --- | --- | --- | --- |
| Identified imports | `lexicon-upstream.tsv`, `lexicon-mozilla.tsv` | 15,033 + 3,740 | Written by `tools/import_translations.py` from published Corsican translations of other free software (Patriccollu di Santa Maria è Sichè and other translators; Mozilla's Corsican team). Each section names its source and licence. Texts are kept as published; Corsu's changes are in `lexicon-fixes.tsv` and `corrections.tsv`. |
| Created or adapted with an AI assistant, documented | `lexicon.tsv`, rows added or changed after the first commit | about 118,500 | Every commit that touched `lexicon.tsv` is co-signed by Claude (Opus 5, then Opus 5.5). Several section headers say so directly ("new proposals written by an AI", "an AI second pass"); others say "draft translations, review welcomed". The co-signature records that the commit was made with an AI assistant; it does not record, row by row, who chose each word. |
| Initial provenance undetermined | `lexicon.tsv`, rows already present in the first commit (`5e55e92`, 30 September 2026) and unchanged since | 872 (of 971 distinct rows in that commit) | The file existed before the Git history began. That first commit is itself co-signed by Claude Opus 5 and says "250 reviewed rows added"; which rows those are, and where the others came from, is not recorded. They are not presented as human translations by default. |

Other files: `lexicon-fixes.tsv` (Corsu's corrections of imported rows), `corrections.tsv` (their list),
`review-discord-2026-10.tsv` (an AI review of Discord labels, each row with its source), `ambiguous-sources.tsv` and
`imported-french-audit.tsv` (audits). All were written in commits co-signed by an AI assistant.

## What this means

- No row of `lexicon.tsv` is counted as validated by a Corsican speaker. Reviews by a speaker, when there are some,
  are recorded apart ([REVIEWS.md](REVIEWS.md)).
- An AI review is not a validation; a translation repeated in Corsu's own lexicon is not an independent attestation
  ([AGENTS.md](../AGENTS.md)).
- Fixing a row does not wait for its origin to be known.

## How the figures were measured

```sh
git log --follow --format='%h %(trailers:key=Co-Authored-By,valueonly)' -- lexicon/lexicon.tsv  # all co-signed
git show 5e55e92:lexicon.tsv | grep -v '^#' | grep . | sort -u > root.txt                          # 971 rows
grep -v '^# ' lexicon/lexicon.tsv | grep . | sort -u > now.txt
comm -12 root.txt now.txt | wc -l                                                                  # 872
```
