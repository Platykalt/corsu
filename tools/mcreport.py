#!/usr/bin/env python3
"""Minecraft Java pages and counters, generated from the committed data only.

    python3 tools/mcreport.py           rewrite the generated pages and blocks
    python3 tools/mcreport.py --check   exit 1 when a generated page or block differs from the data, or when a
                                        release's check must be redone (CI)

Sources: minecraft/java/versions.json (formats, coverage, the `verified` fingerprint of what `mcversions.py verify`
checked), keys.tsv, co_fr.json, history.json, inventory.tsv, history-report.md (size of the sampled second AI pass)
and other-versions.md (what is not claimed). The current fingerprint of each release is computed from the pack
src/minecraft_packs.build_pack makes today: when it differs from the recorded one, the release shows "check to redo".

Written:
- minecraft/java/COMPATIBILITY.md, minecraft/README.md, minecraft/java/README.md: whole files;
- README.md (French block, then English block), docs/fr/minecraft.md, docs/en/minecraft.md, and
  .github/RELEASE_NOTES.md when the lead has placed them: between <!-- corsu:minecraft-summary:start --> and
  <!-- corsu:minecraft-summary:end -->;
- minecraft/java/STATUS.md: between <!-- corsu:minecraft-status:start --> and <!-- corsu:minecraft-status:end -->.
Nothing outside the markers of those files is changed.
"""
import argparse
import collections
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
DATA = 'minecraft/java'
GITHUB = 'https://github.com/Platykalt/corsu/blob/main/'

_spec = importlib.util.spec_from_file_location('mcversions', Path(__file__).resolve().parent / 'mcversions.py')
mcversions = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mcversions)
packs = mcversions.packs

EMPTY = packs.digest('')

# Runs in a real game, as recorded by the maintainer (not derivable from the data). "log": the game's log shows the
# pack loaded and its own messages in Corsican; no per-key visual check is recorded (inventory.tsv `in_game`).
IN_GAME = {'26.3': {'date': '2026-10-16', 'evidence': 'log'}}
# The first published Corsu release that ships the packs of every listed version; None until it is published. The
# last published release and the only Minecraft version its pack is for.
PUBLISHED_IN = '0.23.0'
LAST_PUBLISHED = ('0.22.0', '26.3')

SUMMARY = ('<!-- corsu:minecraft-summary:start -->', '<!-- corsu:minecraft-summary:end -->')
STATUS = ('<!-- corsu:minecraft-status:start -->', '<!-- corsu:minecraft-status:end -->')
# File: (kind, languages of its blocks in order, required).
BLOCKS = {
    'README.md': ('readme', ['fr', 'en'], True),
    'docs/fr/minecraft.md': ('docs', ['fr'], True),
    'docs/en/minecraft.md': ('docs', ['en'], True),
    '.github/RELEASE_NOTES.md': ('release', ['fr', 'en'], False),
}
WHOLE = ('minecraft/java/COMPATIBILITY.md', 'minecraft/README.md', 'minecraft/java/README.md')
STATUS_FILE = 'minecraft/java/STATUS.md'

KINDS = ('reused', 'renamed', 'adapted', 'new')


# ------------------------------------------------------------------------------------------------------- facts

def major(version):
    return int(version.split('.')[0])


def exceptions(version, order):
    """What the game's own code did not check for one release (MULTIVERSION.md, "Not covered by game code"),
    besides drawing and the resource pack screen, never checked for any release."""
    found = []
    if major(version) < 26:
        found.append('components')
    if version == '1.21.1':
        found.append('pack')
    if '1.20' in order and order.index(version) >= order.index('1.20'):
        found.append('code')
    return found


def facts(root=ROOT):
    """Every number the pages show, computed from the committed data."""
    root = Path(root)
    folder = root / DATA
    data = packs.Data(folder).load()
    history_kinds, history_review = collections.Counter(), collections.Counter()
    for by_hash in data.history.values():
        for entry in by_hash.values():
            history_kinds[entry.get('kind')] += 1
            history_review[entry.get('review')] += 1
    # Each (key, English) pair once: where its Corsican comes from (None: no Corsican), then per release.
    sources = []
    for key, sha, positions in data.rows:
        if sha == EMPTY:
            continue
        text = data.resolve(key, sha)
        in_history = data.history.get(key, {}).get(sha)
        source = None if text is None or not text.strip() else (
            in_history.get('kind') if isinstance(in_history, dict) else 'base')
        sources.append((source, positions))
    rows = []
    for position, version in enumerate(data.order):
        entry = data.versions[version]
        origin, total = collections.Counter(), 0
        for source, positions in sources:
            if position in positions:
                total += 1
                if source:
                    origin[source] += 1
        translated = sum(origin.values())
        payload, _ = packs.build_pack(version, data)
        current = mcversions.fingerprint(payload, entry)
        verified = entry.get('verified') or {}
        if not entry.get('supported') or not verified:
            check = 'none'
        elif verified.get('fingerprint') != current or not verified.get('engine'):
            check = 'redo'
        else:
            check = 'ok'
        skipped = re.search(r'\((\d+) skipped', entry.get('note', ''))
        rows.append({
            'version': version, 'lang_format': entry['lang_format'], 'lang_file': entry['lang_file'],
            'language_code': entry['language_code'], 'pack_format': entry['pack_format'], 'mcmeta': entry['mcmeta'],
            'translated': translated, 'total': total, 'origin': dict(origin), 'check': check,
            'date': verified.get('date'), 'fingerprint': current, 'recorded': verified.get('fingerprint'),
            'skipped': int(skipped.group(1)) if skipped else None, 'exceptions': exceptions(version, data.order),
            'in_game': IN_GAME.get(version)})
    ok = [row for row in rows if row['check'] == 'ok' and row['translated'] == row['total']]
    base_texts = sum(1 for key, text in data.translation.items()
                     if isinstance(text, str) and text.strip() and data.base_hash.get(key) not in (None, EMPTY))
    sample = None
    report = folder / 'history-report.md'
    if report.exists():
        found = re.search(r'random sample of (\d+) entries', report.read_text(encoding='utf-8'))
        sample = int(found.group(1)) if found else None
    others = None
    listing = folder / 'other-versions.md'
    if listing.exists():
        counts = re.findall(r'^\| [^|]+ \| (\d+) \|', listing.read_text(encoding='utf-8'), re.M)
        others = sum(int(n) for n in counts) if counts else None
    marks = collections.Counter()
    inventory = folder / 'inventory.tsv'
    if inventory.exists():
        lines = inventory.read_text(encoding='utf-8').splitlines()
        header = lines[0].split('\t')
        for line in lines[1:]:
            cells = dict(zip(header, line.split('\t')))
            for column in ('human_review', 'in_game'):
                if cells.get(column, '').strip() in ('ok', 'done'):
                    marks[column] += 1
    return {
        'rows': rows, 'ok': ok, 'order': data.order, 'base': data.base, 'base_texts': base_texts,
        'pairs': sum(1 for _, sha, _ in data.rows if sha != EMPTY), 'history': sum(history_kinds.values()),
        'kinds': {kind: history_kinds.get(kind, 0) for kind in KINDS},
        'human': history_review.get('human', 0) + marks['human_review'], 'seen_keys': marks['in_game'],
        'sample': sample, 'others': others,
        'dates': sorted({row['date'] for row in rows if row['date']}),
        'skipped': sum(row['skipped'] or 0 for row in rows),
        'skipped_range': sorted({row['skipped'] for row in rows if row['skipped'] is not None}),
        'first_26': next((v for v in data.order if major(v) >= 26), None),
    }


# ------------------------------------------------------------------------------------------------------- words

def capital(text):
    return text[:1].upper() + text[1:]


def number(n, lang):
    text = f'{n:,}'
    return text.replace(',', ' ') if lang == 'fr' else text


def link(target, page, absolute=False):
    """A link from one generated page to a repository file."""
    if absolute:
        return GITHUB + target
    return os.path.relpath(ROOT / target, (ROOT / page).parent).replace(os.sep, '/')


def span(f):
    ok = f['ok']
    return (ok[0]['version'], ok[-1]['version']) if ok else (None, None)


def dates(f, lang):
    d = f['dates']
    if not d:
        return '—'
    return d[0] if len(d) == 1 else (f'{d[0]} à {d[-1]}' if lang == 'fr' else f'{d[0]} to {d[-1]}')


def exception_words(f, lang):
    first_26 = f['first_26']
    if lang == 'fr':
        return {'components': f'composants de texte (chat, progrès) avant {first_26} : règle Python seulement',
                'pack': 'section `pack` de pack.mcmeta en 1.21.1 : non lue par le code du jeu',
                'code': 'code de langue de la section `language` à partir de 1.20 : vérifié en Python'}
    return {'components': f'text components (chat, advancements) before {first_26}: Python rule only',
            'pack': 'the `pack` section of pack.mcmeta in 1.21.1: not read by the game\'s code',
            'code': 'the code in the `language` section from 1.20: checked in Python'}


def headline(f, lang):
    """The maintainer's headline, only as far as the data confirms it."""
    n, (first, last) = len(f['ok']), span(f)
    if lang == 'fr':
        if not n:
            return '**Minecraft: Java Edition en corse** : aucune version n\'a aujourd\'hui une vérification à jour.'
        return (f'**Minecraft Java en corse pour {n} versions** (versions stables {first} → {last}). Traduction '
                'complète des fichiers de langue pour les versions listées ; vérifications techniques avec le code '
                'de chaque version.')
    if not n:
        return '**Minecraft: Java Edition in Corsican**: no version has an up-to-date check today.'
    return (f'**Minecraft: Java Edition in Corsican for {n} versions** (releases {first} → {last}). Complete '
            'translation of the language files for the listed versions; technical checks with each version\'s own '
            'code.')


def others_line(f, lang):
    rest = [row for row in f['rows'] if row not in f['ok']]
    if not rest:
        return ''
    redo = [row['version'] for row in rest if row['check'] == 'redo']
    other = [row['version'] for row in rest if row['check'] != 'redo']
    parts = []
    if lang == 'fr':
        if redo:
            parts.append(f'vérification à refaire (données changées depuis) : {", ".join(redo)}')
        if other:
            parts.append(f'non vérifiées ou incomplètes : {", ".join(other)}')
        return ' Autres versions de la liste — ' + ' ; '.join(parts) + '.'
    if redo:
        parts.append(f'check to redo (data changed since): {", ".join(redo)}')
    if other:
        parts.append(f'not checked or incomplete: {", ".join(other)}')
    return ' Other listed versions — ' + '; '.join(parts) + '.'


def availability(f, lang):
    released, only = LAST_PUBLISHED
    if PUBLISHED_IN:
        return (f'dans les versions publiées de Corsu à partir de {PUBLISHED_IN}' if lang == 'fr'
                else f'in published Corsu releases from {PUBLISHED_IN}')
    if lang == 'fr':
        return (f'sur la branche main (développement) aujourd\'hui ; dans une version publiée de Corsu seulement '
                f'quand une version qui contient ces packs sera publiée (la dernière publiée, {released}, ne contient '
                f'que le pack {only})')
    return (f'on the main branch (development) today; in a published Corsu release only once a release containing '
            f'these packs is published (the last published one, {released}, has only the {only} pack)')


def kinds_text(f, lang):
    k = f['kinds']
    if lang == 'fr':
        return (f'{number(k["reused"], lang)} repris, {number(k["renamed"], lang)} clés renommées, '
                f'{number(k["adapted"], lang)} adaptés, {number(k["new"], lang)} nouveaux')
    return (f'{number(k["reused"], lang)} reused, {number(k["renamed"], lang)} renamed keys, '
            f'{number(k["adapted"], lang)} adapted, {number(k["new"], lang)} new')


def in_game_text(f, lang, page, absolute=False):
    seen = sorted(f['rows'], key=lambda row: f['order'].index(row['version']))
    seen = [row for row in seen if row['in_game']]
    status = link(f'{DATA}/STATUS.md', page, absolute)
    counter_fr = 'le compteur par clé de STATUS.md' if page == STATUS_FILE else f'[STATUS.md]({status}) compte'
    counter_en = 'the per-key counter below shows' if page == STATUS_FILE else f'[STATUS.md]({status}) counts'
    versions = ', '.join(row['version'] for row in seen)
    when = ', '.join(sorted({row['in_game']['date'] for row in seen}))
    if lang == 'fr':
        if not seen:
            return 'aucune version n\'a été lancée avec le pack.'
        return (f'seule la {versions} a été lancée avec le pack, sur l\'instance Prism Launcher du mainteneur '
                f'({when}) : le journal du jeu montre le pack chargé et des messages en corse. Aucune vérification '
                f'visuelle clé par clé n\'est enregistrée : c\'est pourquoi {counter_fr} « vu en jeu : '
                f'{number(f["seen_keys"], lang)} ». Les autres versions n\'ont pas été lancées.')
    if not seen:
        return 'no version has been started with the pack.'
    return (f'only {versions} has been started with the pack, on the maintainer\'s Prism Launcher instance ({when}): '
            f'the game\'s log shows the pack loaded and messages in Corsican. No per-key visual check has been '
            f'recorded, which is why {counter_en} "seen in game: {number(f["seen_keys"], lang)}". '
            'The other versions have not been started.')


def ai_text(f, lang):
    sample = f['sample']
    if lang == 'fr':
        second = (f'deuxième passe IA sur un échantillon de {sample} entrées des {number(f["history"], lang)} textes '
                  'anciens (pas sur tous)') if sample else 'pas de deuxième passe IA enregistrée sur les textes anciens'
        return f'textes écrits par IA ; {second}'
    second = (f'second AI pass on a sample of {sample} entries of the {number(f["history"], lang)} older texts (not '
              'on all of them)') if sample else 'no second AI pass recorded on the older texts'
    return f'texts written by AI; {second}'


def review_text(f, lang):
    if lang == 'fr':
        return f'{ai_text(f, lang)} ; relecture par un locuteur : {number(f["human"], lang)}.'
    return f'{ai_text(f, lang)}; review by a Corsican speaker: {number(f["human"], lang)}.'


def check_text(f, lang, page, absolute=False):
    words = exception_words(f, lang)
    multiversion = link(f'{DATA}/MULTIVERSION.md', page, absolute)
    compatibility = link(f'{DATA}/COMPATIBILITY.md', page, absolute)
    skipped = (' ou ' if lang == 'fr' else ' or ').join(str(n) for n in f['skipped_range']) or '0'
    if lang == 'fr':
        return (f'le {dates(f, lang)}, pour chaque version : règles Python sur chaque texte (arguments, codes `§`, '
                'formats du fichier et de pack.mcmeta), puis le code du jeu de cette version (son propre fichier '
                'client, SHA-1 vérifié) a chargé le fichier de langue et affiché chaque texte : 0 problème '
                f'({skipped} textes par version non affichés car leur anglais lui-même ne se formate pas). '
                'Exceptions : '
                + ' ; '.join(words.values()) + ' ; l\'affichage à l\'écran et l\'écran des packs ne sont pas vérifiés '
                f'([détail]({multiversion}), [par version]({compatibility})). Ce n\'est ni une relecture par un '
                'locuteur ni une vérification visuelle de chaque écran.')
    return (f'on {dates(f, lang)}, for each version: Python rules on every text (arguments, `§` codes, language file '
            'and pack.mcmeta formats), then that version\'s own game code (its client jar, SHA-1 checked) loaded the '
            f'language file and rendered every text: 0 problems ({skipped} texts per version not rendered because '
            'their English itself does not format). Exceptions: ' + '; '.join(words.values()) + '; drawing on '
            f'screen and the resource pack screen are not checked ([details]({multiversion}), [per version]'
            f'({compatibility})). This is neither a speaker\'s review nor a visual check of every screen.')


def scope_text(lang):
    if lang == 'fr':
        return ('les fichiers de langue du jeu seulement : pas les mods, les serveurs ni le lanceur ; phrases '
                'd\'accueil et poème de fin : pack facultatif séparé. Pas les snapshots, pré-versions ni release '
                'candidates, pas Bedrock, rien avant 1.6.1 (pas de packs de ressources).')
    return ('the game\'s language files only: not mods, servers or the launcher; splash texts and the End Poem: a '
            'separate optional pack. No snapshots, pre-releases or release candidates, no Bedrock, nothing before '
            '1.6.1 (no resource packs).')


def steps(lang):
    if lang == 'fr':
        return '\n'.join([
            '**Obtenir et activer le bon pack**',
            '',
            '1. Fermez Minecraft.',
            '2. Dans l\'application Corsu (une version qui contient ces packs), cochez **Minecraft** et installez. '
            'Corsu lit la version jouée par chaque dossier de jeu (lanceur officiel, Prism Launcher, MultiMC, y '
            'compris sous Fabric, Forge, Quilt ou NeoForge), y copie le pack de cette version et choisit le corse.',
            '3. Lancez le jeu : **Options… → Langue…** montre **Corsu (Corsica)**, déjà choisie.',
            '',
            'Développeurs, depuis une copie de main : `python3 tools/mcversions.py build <version>` écrit '
            '`dist/corsu-minecraft-java-<version>.zip` ; déposez-le dans le dossier `resourcepacks` de cette version, '
            'activez-le dans **Packs de ressources…**, puis choisissez **Corsu (Corsica)** dans **Langue…**.'])
    return '\n'.join([
        '**Getting and switching on the right pack**',
        '',
        '1. Close Minecraft.',
        '2. In the Corsu app (a release that contains these packs), tick **Minecraft** and install. Corsu reads the '
        'version each game folder plays (official launcher, Prism Launcher, MultiMC, also under Fabric, Forge, Quilt '
        'or NeoForge), copies that version\'s pack there and picks Corsican.',
        '3. Start the game: **Options… → Language…** shows **Corsu (Corsica)**, already chosen.',
        '',
        'Developers, from a copy of main: `python3 tools/mcversions.py build <version>` writes '
        '`dist/corsu-minecraft-java-<version>.zip`; drop it in that version\'s `resourcepacks` folder, switch it on '
        'in **Resource Packs…**, then pick **Corsu (Corsica)** in **Language…**.'])


def translation_text(f, lang):
    ok = f['ok']
    smallest = min(ok, key=lambda row: row['total']) if ok else None
    largest = max(ok, key=lambda row: row['total']) if ok else None
    if lang == 'fr':
        size = (f' : de {number(smallest["total"], lang)} textes ({smallest["version"]}) à '
                f'{number(largest["total"], lang)} ({largest["version"]})') if ok else ''
        return (f'chaque texte non vide des fichiers de langue de chaque version listée a son texte corse{size}. Une '
                f'seule traduction : celle de {f["base"]} ({number(f["base_texts"], lang)} textes) sert partout où la '
                f'clé et son anglais sont les mêmes ; {number(f["history"], lang)} textes anciens différents ont leur '
                f'propre entrée ({kinds_text(f, lang)}).')
    size = (f': from {number(smallest["total"], lang)} texts ({smallest["version"]}) to '
            f'{number(largest["total"], lang)} ({largest["version"]})') if ok else ''
    return (f'every non-empty text of each listed version\'s language files has its Corsican text{size}. One '
            f'translation: {f["base"]}\'s ({number(f["base_texts"], lang)} texts) serves wherever the key and its '
            f'English are the same; {number(f["history"], lang)} differing older texts have their own entry '
            f'({kinds_text(f, lang)}).')


def summary(f, lang, kind, page):
    absolute = kind == 'release'
    compatibility = link(f'{DATA}/COMPATIBILITY.md', page, absolute)
    docs = link(f'docs/{lang}/minecraft.md', page, absolute)
    released, only = LAST_PUBLISHED
    if kind == 'readme':
        if lang == 'fr':
            return (headline(f, lang) + others_line(f, lang) + ' L\'application Corsu trouve la version de chaque '
                    'dossier de jeu, y ajoute le pack de cette version et choisit le corse. Textes écrits par IA, '
                    'sans relecture par un locuteur ; vérifications automatiques, pas visuelles ; seule la '
                    f'{only} a été lancée avec le pack. Disponibilité : {availability(f, lang)}. Détails et limites : '
                    f'[Minecraft en corse]({docs}), [versions et vérifications]({compatibility}).')
        return (headline(f, lang) + others_line(f, lang) + ' The Corsu app finds the version of each game folder, adds '
                'that version\'s pack and picks Corsican. AI-written texts, not reviewed by a speaker; automated '
                f'checks, not visual ones; only {only} has been started with the pack. Availability: '
                f'{availability(f, lang)}. Details and limits: [Minecraft in Corsican]({docs}), '
                f'[versions and checks]({compatibility}).')
    if kind == 'release':
        if lang == 'fr':
            return (f'- {headline(f, lang)} ([versions et vérifications]({compatibility})) Cette version de Corsu '
                    'contient ces packs : fermez Minecraft, puis l\'application trouve la version de chaque dossier '
                    'de jeu (lanceur officiel, Prism Launcher, MultiMC), y ajoute le pack de cette version et choisit '
                    f'le corse. Limites : {review_text(f, lang)[:-1]} ; {in_game_text(f, lang, page, True)} '
                    'Les vérifications automatiques ne sont ni une relecture par un locuteur ni un contrôle visuel '
                    'de chaque écran. Pas les snapshots, pré-versions, Bedrock ni les versions avant 1.6.1.')
        return (f'- {headline(f, lang)} ([versions and checks]({compatibility})) This Corsu release contains these '
                'packs: close Minecraft, then the app finds the version of each game folder (official launcher, Prism '
                'Launcher, MultiMC), adds that version\'s pack and picks Corsican. Limits: '
                f'{review_text(f, lang)[:-1]}; {in_game_text(f, lang, page, True)} The automated checks are neither a '
                'speaker\'s review nor a visual check of every screen. No snapshots, pre-releases, '
                'Bedrock or versions before 1.6.1.')
    rows = (['Versions', 'Traduction', 'Vérifications techniques', 'Relecture', 'En jeu', 'Disponibilité',
             'Hors champ'] if lang == 'fr' else
            ['Versions', 'Translation', 'Technical checks', 'Review', 'In the game', 'Availability', 'Out of scope'])
    first, last = span(f)
    listed = (f'les {len(f["ok"])} versions stables de Java Edition de {first} à {last} ([liste et résultat par '
              f'version]({compatibility})).' if lang == 'fr' else
              f'the {len(f["ok"])} Java Edition releases from {first} to {last} ([list and result per version]'
              f'({compatibility})).') + others_line(f, lang)
    cells = [listed, translation_text(f, lang), check_text(f, lang, page), review_text(f, lang),
             in_game_text(f, lang, page), availability(f, lang) + '.', scope_text(lang)]
    lines = [headline(f, lang), '', '| | |', '| --- | --- |']
    lines += [f'| {name} | {cell} |' for name, cell in zip(rows, cells)]
    return '\n'.join(lines + ['', steps(lang)])


# ------------------------------------------------------------------------------------------------------- pages

def check_cell(row, words):
    if row['check'] == 'none':
        return 'not checked'
    if row['check'] == 'redo':
        return f'**check to redo** (pack differs from the one checked on {row["date"]})'
    rendered = (f'every text rendered except {row["skipped"]} whose English itself does not format'
                if row['skipped'] else 'every text rendered')
    return f'partial: language file loaded, {rendered}, 0 problems'


def compatibility(f):
    page = f'{DATA}/COMPATIBILITY.md'
    words = exception_words(f, 'en')
    short = {'components': 'text components', 'pack': '`pack` section', 'code': 'language code'}
    k, rows = f['kinds'], f['rows']
    base_pairs = sum(row['origin'].get('base', 0) for row in rows)
    lines = [
        '# Minecraft: Java Edition in Corsican — versions and checks', '',
        'Generated by `python3 tools/mcreport.py` from `versions.json`, `keys.tsv`, `co_fr.json`, `history.json`, '
        '`inventory.tsv`, `history-report.md` and `other-versions.md`; do not edit by hand. Status by state: '
        '[STATUS.md](STATUS.md); contract: [MULTIVERSION.md](MULTIVERSION.md).', '',
        headline(f, 'en') + others_line(f, 'en'), '',
        f'Availability: {availability(f, "en")}.', '',
        '## One translation for every version', '',
        f'- The {len(rows)} releases show {number(f["pairs"], "en")} different (key, English text) pairs with '
        'non-empty English (`keys.tsv`).',
        f'- The {f["base"]} translation (`co_fr.json`, {number(f["base_texts"], "en")} texts) serves every release '
        f'wherever the key and its English are exactly {f["base"]}\'s: {number(base_pairs, "en")} texts summed over '
        'the releases.',
        f'- `history.json` holds {number(f["history"], "en")} pairs whose English differs from {f["base"]}\'s: '
        f'{number(k["reused"], "en")} *reused* ({f["base"]}\'s Corsican still says the older English), '
        f'{number(k["renamed"], "en")} *renamed* (same English under a key renamed since: the Corsican of the new '
        f'key), {number(k["adapted"], "en")} *adapted* ({f["base"]}\'s Corsican adapted to the older English), '
        f'{number(k["new"], "en")} *new* (English found nowhere in {f["base"]}: translated).',
        '- A correction to a shared text is made once and reaches every release showing that exact English; a '
        'different English is a different pair, so a historical difference stays.', '',
        '## Limits', '',
        '- ' + capital(review_text(f, 'en')),
        '- Technical check: ' + check_text(f, 'en', page),
        '- In the game: ' + in_game_text(f, 'en', page),
        '- Scope: ' + scope_text('en') + (f' The {number(f["others"], "en")} other entries of Mojang\'s version '
                                          'manifest are listed in [other-versions.md](other-versions.md) and not '
                                          'claimed.' if f['others'] else ''),
        f'- Freshness: `tools/mcversions.py verify` records the SHA-256 of the exact `pack.mcmeta` and language file '
        'it checked (`versions.json` → `verified`). This page computes them again from today\'s data: a release whose '
        'pack differs shows "check to redo", and `python3 tools/mcreport.py --check` fails until `verify` runs again.',
        '', '## Every release', '',
        'Texts: Corsican texts / texts with non-empty English in that release. Origin: texts from '
        f'{f["base"]}\'s translation / texts from `history.json`. Python only: what that release\'s game code did '
        'not check, with the Python rule standing in (see "Technical check" above). Drawing and the resource pack '
        'screen are not checked for any release.', '',
        '| Version | Language file (pack format) | Texts | Origin | Game code check | Python only | Checked on | '
        'In the game |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in rows:
        origin = row['origin']
        own = sum(origin.get(kind, 0) for kind in KINDS)
        game = (f'log shows the pack loaded ({row["in_game"]["date"]}); no per-key visual check'
                if row['in_game'] else 'not tried')
        lines.append(
            f'| {row["version"]} | `{row["lang_file"].rsplit("/", 1)[1]}` ({row["pack_format"]}, {row["mcmeta"]}) | '
            f'{number(row["translated"], "en")} / {number(row["total"], "en")} | '
            f'{number(origin.get("base", 0), "en")} / {number(own, "en")} | {check_cell(row, words)} | '
            f'{", ".join(short[key] for key in row["exceptions"]) or "—"} | {row["date"] or "—"} | {game} |')
    return '\n'.join(lines) + '\n'


def folder_readme(f):
    page = 'minecraft/README.md'
    return '\n'.join([
        '# Minecraft en corse · Minecraft in Corsican', '',
        'Généré par `python3 tools/mcreport.py` · Generated by `python3 tools/mcreport.py`.', '',
        '## Français', '',
        summary(f, 'fr', 'docs', page), '',
        f'Guide : [docs/fr/minecraft.md]({link("docs/fr/minecraft.md", page)}). Dossiers : [java/](java/) (cette '
        'traduction), [bedrock/](bedrock/) (prototype, jamais chargé dans le jeu : '
        '[STATUS.md](bedrock/STATUS.md)).', '',
        '## English', '',
        summary(f, 'en', 'docs', page), '',
        f'Guide: [docs/en/minecraft.md]({link("docs/en/minecraft.md", page)}). Folders: [java/](java/) (this '
        'translation), [bedrock/](bedrock/) (prototype, never loaded in the game: [STATUS.md](bedrock/STATUS.md)).',
        '', 'NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.', ''])


def java_readme(f):
    page = 'minecraft/java/README.md'
    files = [
        ('COMPATIBILITY.md', 'every release: language file, texts, check result and date, in-game status'),
        ('STATUS.md', 'the four states kept apart: translation, AI review, human review, seen in the game'),
        ('MULTIVERSION.md', 'the contract: data, resolution, formats, what the checks cover and do not'),
        ('co_fr.json', f'the {f["base"]} translation, the base'),
        ('history.json', 'Corsican for older English that differs from the base (one entry per key and English)'),
        ('keys.tsv', 'every (key, English hash) of every release and the releases showing it'),
        ('versions.json', 'per release: formats, coverage, the check\'s note and fingerprint (`verified`)'),
        ('history-report.md', 'how the older texts were handled, and the sampled second AI pass'),
        ('other-versions.md', 'snapshots, pre-releases and older versions: inventoried, not claimed'),
        ('TESTING.md', 'how to test in the game and report (French: docs/fr/minecraft-tester.md)'),
        ('STYLE.md', 'conventions; [glossary.tsv](glossary.tsv): terms'),
        ('LICENSING.md', 'licence of the texts'),
    ]
    return '\n'.join([
        '# Minecraft: Java Edition in Corsican — data', '',
        'Generated by `python3 tools/mcreport.py`. Français : '
        f'[docs/fr/minecraft.md]({link("docs/fr/minecraft.md", page)}).', '',
        summary(f, 'en', 'docs', page), '',
        '## Files', '',
        '| File | What |', '| --- | --- |'] + [f'| [{name}]({name}) | {what} |' for name, what in files] + [
        '',
        'Tools: `tools/mcversions.py` (fetch Mojang\'s English, index, formats, build, verify), `tools/mchistory.py` '
        '(older texts), `tools/minecraft.py` (the base: check, build, game-code check of 26.3, splash texts), '
        '`tools/mcreport.py` (these pages).', '',
        'NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.', ''])


def status_block(f):
    rows, ok = f['rows'], f['ok']
    complete = [row for row in rows if row['translated'] == row['total']]
    smallest = min(rows, key=lambda row: row['total'])
    redo = [row['version'] for row in rows if row['check'] == 'redo']
    none = [row['version'] for row in rows if row['check'] == 'none']
    words = exception_words(f, 'en')
    first, last = rows[0]['version'], rows[-1]['version']
    check = (f'{len(ok)} / {len(rows)} with a check matching today\'s data ({dates(f, "en")}, '
             '`tools/mcversions.py verify`; fingerprints in `versions.json`): Python rules for placeholders, `§` '
             'codes, file and mcmeta formats; then each release\'s own client jar (SHA-1 checked) loads the language '
             'file and renders every text with its own formatter (0 problems, 0 unknown keys; '
             f'{" or ".join(map(str, f["skipped_range"]))} texts per release not rendered because their English itself '
             'does not format). Exceptions: ' + '; '.join(words.values()) + '; drawing and the resource pack screen '
             'not checked ([COMPATIBILITY.md](COMPATIBILITY.md), [MULTIVERSION.md](MULTIVERSION.md))')
    if redo:
        check += f'. **Check to redo** (data changed since): {", ".join(redo)}'
    if none:
        check += f'. Not checked: {", ".join(none)}'
    return '\n'.join([
        f'## Every release from {first} to {last} ({len(rows)} releases)', '',
        'Generated by `python3 tools/mcreport.py`; per release: [COMPATIBILITY.md](COMPATIBILITY.md).', '',
        '| State | Result |', '| --- | --- |',
        f'| Translation present | {len(complete)} / {len(rows)} releases with every non-empty text translated (from '
        f'{number(smallest["total"], "en")} texts in {smallest["version"]} to {number(rows[-1]["total"], "en")} in '
        f'{last}): the {f["base"]} base ({number(f["base_texts"], "en")} texts) plus `history.json` '
        f'({number(f["history"], "en")} pairs for older English: {kinds_text(f, "en")}) |',
        f'| Technical check | {check} |',
        f'| AI review | {capital(ai_text(f, "en"))}. The {f["base"]} base also got a '
        'harmonising and a reviewing AI pass (section 3 below), then in October 2026 a review of the concrete names '
        'and of the language with sources, checked by a separate AI verification before part of it was applied '
        '([review-2026-10/TRACKING.md](review-2026-10/TRACKING.md)). An AI pass finds mistakes; it is not a '
        'validation. |',
        f'| Human review | {number(f["human"], "en")} |',
        f'| Seen in the game | {capital(in_game_text(f, "en", STATUS_FILE))} |',
        '', 'Snapshots, pre-releases, release candidates and versions before 1.6.1 (no resource packs): not claimed '
        '([other-versions.md](other-versions.md)).'])


# ------------------------------------------------------------------------------------------------------- files

def replace_blocks(text, markers, blocks, name):
    start, end = markers
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    found = pattern.findall(text)
    if len(found) != len(blocks):
        raise ValueError(f'{name}: {len(found)} marked blocks, expected {len(blocks)}')
    replacements = iter(blocks)
    return pattern.sub(lambda _: f'{start}\n{next(replacements)}\n{end}', text)


def outputs(root=ROOT, f=None):
    """{relative path: expected content} of every generated file, and the notes for files left as they are."""
    root = Path(root)
    f = f or facts(root)
    result, notes = {}, []
    result['minecraft/java/COMPATIBILITY.md'] = compatibility(f)
    result['minecraft/README.md'] = folder_readme(f)
    result['minecraft/java/README.md'] = java_readme(f)
    for name, (kind, languages, required) in BLOCKS.items():
        path = root / name
        text = path.read_text(encoding='utf-8') if path.exists() else ''
        if SUMMARY[0] not in text and not required:
            notes.append(f'{name}: no {SUMMARY[0]} markers, left as is')
            continue
        result[name] = replace_blocks(text, SUMMARY, [summary(f, lang, kind, name) for lang in languages], name)
    status = (root / STATUS_FILE).read_text(encoding='utf-8')
    result[STATUS_FILE] = replace_blocks(status, STATUS, [status_block(f)], STATUS_FILE)
    return result, notes


def problems(root=ROOT, f=None):
    """What --check reports: generated files that differ, releases whose check must be redone or is missing."""
    root = Path(root)
    f = f or facts(root)
    found = [f'Minecraft {row["version"]}: check to redo (pack fingerprint {row["fingerprint"][:19]}…, checked '
             f'{(row["recorded"] or "")[:19]}… on {row["date"]}): run `python3 tools/mcversions.py verify '
             f'{row["version"]}`' for row in f['rows'] if row['check'] == 'redo']
    found += [f'Minecraft {row["version"]}: listed but not checked' for row in f['rows'] if row['check'] == 'none']
    expected, _ = outputs(root, f)
    for name, content in expected.items():
        path = root / name
        if not path.exists() or path.read_text(encoding='utf-8') != content:
            found.append(f'{name}: differs from the data (run `python3 tools/mcreport.py`)')
    return found


def write(root=ROOT, f=None):
    root = Path(root)
    f = f or facts(root)
    expected, notes = outputs(root, f)
    for name, content in expected.items():
        path = root / name
        if not path.exists() or path.read_text(encoding='utf-8') != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            print(f'{name}: written')
    for line in notes:
        print(line)
    return f


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--check', action='store_true', help='exit 1 if anything generated differs or is stale')
    parser.add_argument('--root', default=str(ROOT), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.check:
        found = problems(args.root)
        for line in found:
            print(line)
        if not found:
            print('Minecraft pages and checks are up to date with the data.')
        return 1 if found else 0
    f = write(args.root)
    for line in problems(args.root, f):
        print('warning:', line)
    return 0


if __name__ == '__main__':
    sys.exit(main())
