# Licensing options for Corsu's own texts

Checked on 2026-10-16. Not legal advice. Nothing here has been applied; the repository is still GPL-3.0-or-later.

## Verified facts

**Minecraft EULA** (<https://www.minecraft.net/en-us/eula>):

- Mods: "By "Mods," we mean something original that you or someone else created that doesn't contain a substantial
  part of our copyrightable code or content." "We have the final say on what constitutes a Mod and what doesn't."
  "Basically, Mods are okay to distribute". "You only own what you created; you do not own our code or content."
- Content section: "We don't own the original stuff that you create. We will however own things that are copies (or
  substantial copies) or derivatives of our property and creations - but if you create original things, they aren't
  ours." The Realms section adds that Mojang retains "our Minecraft intellectual property, which includes the game
  itself … and derivatives of each."

**Usage Guidelines** (<https://www.minecraft.net/en-us/usage-guidelines>):

- "All rights (including copyright, trademark rights, and related rights) in the name, brand, assets, and any
  derivatives are and will remain owned by Mojang and Microsoft". "Assets" means "the code, software, graphics,
  textures, images, models, sounds and other audio from any of our games and any videos or screenshots". Text is not
  listed by name.
- "commercial use means any uses of our name, brand, or assets that you use and share with others (regardless of
  whether you receive payment or provide it for free)".
- "Prominently include the disclaimer similar to the following: "NOT AN OFFICIAL MINECRAFT [PRODUCT/SERVICE/EVENT/etc.].
  NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT""; "Do not redistribute our games or any alterations of our
  games or game files".
- `/en-us/commercial-usage` now returns 404; the Usage Guidelines cover commercial use.

**Crowdin Terms** (<https://support.crowdin.com/terms/>, revised 24 September 2026), platform terms that every
translator accepts:

- "Client Data" includes "translations"; 12.3: the contributor warrants that it "either owns its Client Data or has the
  necessary licenses" and that its use does not "infringe … any third-party right".
- 12.6 Public Projects: "Client or User hereby grants Supplier and other Clients a perpetual, irrevocable, nonexclusive,
  royalty free license under all rights necessary to … reproduce, distribute, modify, adapt, prepare derivative works
  of … and use such Client Data". This goes to Crowdin and to other Crowdin users, the project owner (Mojang) included.

**Minecraft project terms**: the *Minecraft Crowdin Localization FAQ*
(<https://docs.google.com/document/d/1qSYgCGvqbgKUVd_7B53Li4fo_Ksq43L-D7RpJdbeaJs/>, linked from
<https://minecraft.wiki/w/Crowdin>) contains no licence or CLA. It says languages are added "when there is evidence that
there are enough dedicated users", and machine translations "should be avoided". No Mojang CLA was found.

**Other targets**: Pontoon: "Translations are governed by the Mozilla Public License 2.0, or another license or set
of licenses acceptable to the Mozilla Foundation" (<https://pontoon.mozilla.org/terms/>). Weblate projects set their own
"Translation license" and optional "Contributor license agreement"
(<https://docs.weblate.org/en/latest/admin/projects.html>).

**Compatibility**: Creative Commons: "compatibility with the GPLv3 is one-way only, which means you may license your
contributions to adaptations of BY-SA 4.0 materials under GPLv3, but you may not license your contributions to
adaptations of GPLv3 projects under BY-SA 4.0" (<https://creativecommons.org/compatible-licenses/>). FSF: GPLv3 only,
not "or later", unless CC is named as proxy; CC0: "Both public domain works and the lax license provided by CC0 are
compatible with the GNU GPL. If you want to release your non-software work to the public domain, we recommend you use
CC0" (<https://www.gnu.org/licenses/license-list.en.html>).

**AI output**: US Copyright Office, Part 2 (January 2025,
<https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf>): "Copyright
does not extend to purely AI-generated material, or material where there is insufficient human control over the
expressive elements"; "prompts do not alone provide sufficient control". Creative human modifications can be
protected. The EU test is the "author's own intellectual creation" (CJEU, C-5/08 *Infopaq*); French and EU law on AI
output is unsettled.

## Uncertain

1. **What the derivative sentence covers.** It sits in the *Content* section, about "the original stuff that you
   create", and attaches to "derivatives of our property and creations". The game's English text is Mojang's, so a
   translation can fall under it, but the EULA never names translations and courts have not tested it. The Mod
   clauses do not resolve this: Mojang has "the final say" on what is a Mod.
2. **Whether Corsu has copyright to license.** The texts were written by an AI model under the maintainer's direction.
   Where human review, choices and edits are enough, the maintainer is the author; otherwise there may be nothing to
   license.
3. **Whether Mojang would add Corsican to Crowdin.** It is not a game language; not checked.

For Crowdin the question is **who can grant the 12.6 licence**. The maintainer, sole human author (per git history),
can grant it whatever Corsu's public licence is. A **third party** can submit Corsu's texts only if Corsu's licence
lets them grant 12.6 without conditions: GPL and CC BY-SA do not (12.6 carries no attribution or share-alike), CC0
does. CC0 is not *necessary* for the maintainer and not *sufficient* by itself: it cannot clear Mojang's possible
rights (moot when submitting to Mojang's own project), and the FAQ's stance on machine translation remains.

## Comparison for Corsu's original translation texts

| | GPL-3.0-or-later | CC BY-SA 4.0 | CC0 1.0 |
| --- | --- | --- | --- |
| Reuse by others | yes, under GPL | yes, with credit | anything |
| Attribution required | keep notices | yes | no (credit requested, not required) |
| Share-alike of adaptations | yes | yes | no |
| Into Pontoon (MPL-2.0) by a third party | no | no | yes |
| Into a GPL Weblate project | GPLv3+ projects only | GPLv3 only, one-way | any |
| Into Crowdin Minecraft by a third party | no | no | yes (Mojang's rights aside) |
| Weak if copyright is doubtful | claims copyleft it may not have | same | nothing to enforce |

## Recommendation

**CC0 1.0 for Corsu's own Corsican texts; code stays GPL-3.0-or-later.** The likely reusers are localisation
projects (Pontoon, Weblate, Crowdin) that GPL and CC BY-SA would block. CC0 also fits the uncertainty: it claims
nothing that the AI-authorship or Mojang-derivative questions might deny. The cost: no legal duty to credit Corsu, and
proprietary reuse is allowed. Choose CC BY-SA 4.0 instead if credit and share-alike matter more than upstream reuse.

## Proposed changes (not applied)

**If CC0** (or CC BY-SA: same files, other licence):

- `minecraft/java/LICENSE.txt`, `texts/LICENSE.txt`: replace the GPL sentence with "Corsu's own Corsican text is
  dedicated to the public domain under CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/". Keep the Mojang and
  Gough notices and the disclaimer.
- `co_fr.json` (covered by the pack's LICENSE.txt), `glossary.tsv`, `STYLE.md`, `decisions.md`, `review.md`,
  `changes-review.tsv`, `inventory.tsv`, `pack.png`: one notice in `LICENSING.md`.
- `lexicon/lexicon.tsv`: header "Corsican column, where written for Corsu: CC0 1.0. English and French columns come from
  the programs named in each section and keep their licences (Firefox MPL-2.0, KDE/GNU GPL or LGPL, Discord, Google,
  Opera: proprietary)." Corsican rows translating proprietary strings are in the same position as `co_fr.json`.
  Same for the other review files in `lexicon/`.
- **Unchanged**: `lexicon-mozilla.tsv` (MPL-2.0), `lexicon-upstream.tsv` (per section), `keyboard/` (GPL; its word list
  counts words from all lexicons, including imported ones), `vendor/`, all code.
- `README.md`: "Code: GPL-3.0-or-later. Corsican texts written for Corsu: CC0 1.0. Imported translations keep their
  licence (lexicon/)." Add `LICENSES/CC0-1.0.txt`; add a `CREDITS.md` listing Patriccollu di Santa Maria è Sichè and
  each imported project with its licence, Julian Gough (End Poem, CC0), Mojang (source text, EULA).

**If GPL is kept**: only the `LICENSING.md` corrections (done) and `CREDITS.md`.

## Other finding

`tools/import_translations.py` says "every source below is compatible with Corsu's GPL-3.0-or-later", but imports
HandBrake rows under **GPL-2.0-only**, which is not GPLv3-compatible.
