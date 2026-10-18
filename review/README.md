# Relecture par des locuteurs · Review by speakers

[Français](#français) · [English](#english)

## Français

Les textes corses de Corsu ont été écrits puis revus par une IA. Ce dossier sert à les faire relire par des
personnes qui parlent corse, par petits lots, sans Git ni compte.

### Les lots

[`sets/`](sets/README.md) contient 71 lots d'environ dix questions (au plus 12 textes), tirés des lots Minecraft
de [`minecraft/java/review-batches/`](../minecraft/java/review-batches/). Chaque question montre, pour chaque texte :
la clé, l'anglais, le français officiel du jeu, le corse actuellement dans le pack (pris dans `co_fr.json`), l'endroit
où il apparaît et une question précise. Si la question a été écrite pour un corse qui a changé depuis, le lot le dit.

Chaque lot existe en deux formes :

- **HTML** (`mcNN-N.html`) : un seul fichier, sans réseau. On le télécharge (« Download raw file » sur GitHub), on
  l'ouvre dans un navigateur, on choisit pour chaque question « OK », « J'écrirais autrement » (avec sa forme) ou
  « Passer », avec une remarque si on veut. La page fabrique une **réponse** à relire, puis à copier, enregistrer
  en fichier, ou envoyer dans un ticket GitHub prérempli (ouvert seulement par un clic ; il faut un compte GitHub).
  Aucun nom n'est demandé ; les brouillons restent dans le navigateur.
- **Markdown** (`mcNN-N.md`) : lisible sur GitHub ; on peut aussi écrire « OK » ou sa forme sous chaque « Réponse ».

### Ce que devient une réponse

1. `python3 tools/review_sets.py import FICHIER… --via "ticket #12"` lit les réponses (texte de la page HTML, corps
   d'un ticket collé dans un fichier, ou lot Markdown rempli) et les ajoute à `answers.jsonl` comme
   **propositions**. Rien ne change dans le pack. Les noms des personnes ne sont pas enregistrés.
2. Chaque réponse garde, pour chaque texte, l'empreinte de l'anglais (`source_hash`, la même que `keys.tsv`), la
   version du jeu et l'empreinte du corse montré. Une réponse porte donc sur un texte exact.
3. `python3 tools/review_sets.py status` compare chaque réponse aux textes actuels : si l'anglais d'un de ses
   textes a changé (autre empreinte), ou si le corse approuvé par un « OK » a changé, elle redevient
   **à réexaminer**, quel que soit son état précédent.
4. `python3 tools/review_sets.py examine LOT QUESTION accepted|rejected --note …` enregistre l'examen du mainteneur.
   Seule une réponse **acceptée** dont les textes n'ont pas changé compte comme validation humaine :
   `tools/mcmemory.py` l'écrit dans `lexicon/memory/minecraft-java.jsonl` (`validation.human`), à part des niveaux IA.
   Une forme proposée et acceptée s'applique ensuite dans `co_fr.json` comme toute correction, avec sa provenance.

Une relecture par IA n'est jamais enregistrée ici comme une réponse de locuteur.

Les lots se régénèrent avec `python3 tools/review_sets.py build` (les tests vérifient qu'ils sont à jour).

## English

Corsu's Corsican texts were written and revised by an AI. This folder is for having them reviewed by people who
speak Corsican, in small sets, without Git or an account.

### The sets

[`sets/`](sets/README.md) holds 71 sets of about ten questions (at most 12 texts), cut from the Minecraft batches
in [`minecraft/java/review-batches/`](../minecraft/java/review-batches/). Each question shows, for each text: the
key, the English, the game's official French, the Corsican now in the pack (from `co_fr.json`), where it appears and
a precise question. When the question was written about a Corsican that changed since, the set says so.

Each set comes in two forms:

- **HTML** (`mcNN-N.html`): one file, no network. Download it ("Download raw file" on GitHub), open it in a browser,
  choose for each question "OK", "I would write it otherwise" (with your form) or "Skip", with a comment if you
  like. The page makes a **reply** to read, then copy, save as a file, or send as a prefilled GitHub issue (opened
  only on a click; needs a GitHub account). No name is asked; drafts stay in the browser.
- **Markdown** (`mcNN-N.md`): readable on GitHub; you can also write "OK" or your form under each "Answer".

### What happens to an answer

1. `python3 tools/review_sets.py import FILE… --via "issue #12"` reads the answers (the HTML page's reply, an issue
   body pasted into a file, or a filled-in Markdown set) and adds them to `answers.jsonl` as **proposals**. Nothing
   changes in the pack. People's names are not recorded.
2. Each answer keeps, for each text, the hash of the English (`source_hash`, the same as `keys.tsv`), the game
   version and the hash of the Corsican shown. An answer is about one exact text.
3. `python3 tools/review_sets.py status` compares each answer with the current texts: when the English of one of its
   texts changed (another hash), or the Corsican an "OK" approved changed, it goes back to **to re-examine**, whatever
   its earlier state.
4. `python3 tools/review_sets.py examine SET QUESTION accepted|rejected --note …` records the maintainer's decision.
   Only an **accepted** answer whose texts did not change counts as a human validation: `tools/mcmemory.py` writes
   it into `lexicon/memory/minecraft-java.jsonl` (`validation.human`), apart from the AI levels. An accepted form is
   then applied in `co_fr.json` like any correction, with its provenance.

An AI review is never recorded here as a speaker's answer.

Rebuild the sets with `python3 tools/review_sets.py build` (the tests check that they are up to date).
