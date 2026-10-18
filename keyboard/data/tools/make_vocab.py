#!/usr/bin/env python3
"""Build the keyboard vocabulary lists keyboard/data/{shared,cismuntincu,pumuntincu}.tsv.

    python3 keyboard/data/tools/make_vocab.py

Inputs:
  - the downloaded resources of tools/fetch_resources.py (Vikipedia dump, Wiktionary extract, Apertium dictionary,
    Tatoeba sentences), read from $CORSU_RESOURCES or ~/.local/share/corsu/resources and never modified;
  - the hand-checked source files in keyboard/data/sources/ (daily words, ADECEC pages, U Cunghjugarellu forms,
    northern/southern pairs);
  - the project lexicons (Corsu's own software translations), counted all alike: a word does not become more
    trustworthy because of the file it comes from;
  - the Corsican place names of sources/places.tsv (Wikidata, fetched by tools/fetch_places.py);
  - the old generated word list keyboard/platykalt.co.corsu/source/wordlist.tsv as of version 0.9.0 (read from git:
    tools/build_keyboard.py now rewrites that file from these lists), only to report what changed.

Outputs the three lists, keyboard/data/audit/removed.tsv (what the old list had and the new one drops, with the
reason) and keyboard/data/audit/stats.json (the numbers quoted in keyboard/data/REVIEW.md). Weights and statuses
are explained in REVIEW.md; sources and licences in docs/keyboard-sources.md.
"""
import bz2
from collections import Counter, defaultdict
import html
import json
import os
from pathlib import Path
import re
import subprocess
import unicodedata
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'keyboard/data'
SOURCES = DATA / 'sources'
RESOURCES = Path(os.environ.get('CORSU_RESOURCES', Path.home() / '.local/share/corsu/resources'))
OLD_WORDLIST = 'keyboard/platykalt.co.corsu/source/wordlist.tsv'
# The commit that holds the old list as version 0.9.0 generated it; later commits hold build_keyboard.py's output.
OLD_WORDLIST_COMMIT = '66e7f58'
LEXICONS = [ROOT / 'lexicon' / name for name in
            ('lexicon-fixes.tsv', 'lexicon-mozilla.tsv', 'lexicon-upstream.tsv', 'lexicon.tsv')]
HEADER = 'word\tweight\tvariant\tsource\tlicense\tstatus\n'
LICENSES = {
    'cunghjugarellu': 'attestation-only',
    'adecec': 'attestation-only',
    'cowiki-lingua-corsa': 'CC-BY-SA-4.0',
    'frwiki-corse-langue': 'CC-BY-SA-4.0',
    'wiktionary': 'CC-BY-SA-4.0',
    'tatoeba': 'CC-BY-2.0-FR',
    'vikipedia': 'CC-BY-SA-4.0',
    'apertium': 'GPL-3.0',
    'wikidata': 'CC0-1.0',
    'corsu-lexicon': 'corsu-lexicon-mixed',
    'ai': 'GPL-3.0-or-later',
}
# Same word pattern as tools/build_keyboard.py: letters, possibly joined by apostrophes (l'acqua, nant'à).
WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
# Minimum weight of the daily words by tier (sources/daily.tsv).
TIER_FLOOR = {1: 20000, 2: 5000, 3: 1000}
TATOEBA_FLOOR = 2000
# The weight of a word in the software lexicon counts for this share of a Vikipedia occurrence: interface text
# repeats "file", "settings" or "error" thousands of times and says little about everyday messages.
LEXICON_SHARE = 0.02
# Weight of a Corsican place name (sources/places.tsv): its Vikipedia frequency, at least PLACE_FLOOR so that Keyman
# knows the name and auto-correction keeps it (Zicavu was once replaced by "Cavu"), and at most PLACE_CAP, just
# below the lowest floor of the everyday words (1,000): an encyclopedia names places far more often than messages
# do, and the names must not push everyday words out of the suggestions. Names already in the list (Aiacciu,
# Bastia, Corti) keep their own weight.
PLACE_FLOOR = 50
PLACE_CAP = 900
# In a variety's preference list, the other variety's form keeps this share of the pair's weight.
OTHER_SHARE = 0.25
# About 1,380 Vikipedia articles are botanical stubs generated from one table ("spezia", "pianta", "sinonimi",
# "flora"...): a quarter of all the article text. They are left out of the counts.
BOT_STUB = '{| align="right" rules="all"'
# Programs, brands and services: names, not Corsican words, even when Corsican text mentions them.
PRODUCT_NAMES = {'google', 'windows', 'linux', 'android', 'firefox', 'chrome', 'chromium', 'mozilla', 'discord',
                 'kde', 'plasma', 'git', 'commit', 'wifi', 'bluetooth', 'ios', 'macos', 'apple', 'microsoft',
                 'youtube', 'facebook', 'vlc', 'audacity', 'thunderbird', 'ubuntu', 'gnome', 'github', 'opera',
                 'safari', 'edge', 'gmail', 'twitter', 'instagram', 'whatsapp', 'keyman', 'pontoon', 'crowdin',
                 'minecraft', 'steam', 'spotify', 'netflix', 'amazon', 'id'}
# Tokens of web addresses, markup and file names, never words.
NOT_WORDS = {'http', 'https', 'www', 'html', 'htm', 'jpg', 'jpeg', 'png', 'svg', 'gif', 'pdf', 'php', 'com', 'org',
             'net', 'commons', 'wikimedia', 'wikipedia', 'wiki', 'url', 'isbn', 'px', 'thumb', 'ref', 'nbsp'}


ACUTE = re.compile('[áéíóú]')
# Corsican spelling uses the Latin letters a-z without k, w, x, y, j only in chj/ghj, and grave accents on vowels.
CORSICAN_LETTERS = re.compile(r"[a-zàèìòù']+")
FOREIGN_LETTERS = re.compile(r'[kwxy]|(?<![gc]h)j')
CONSONANT_RUN = re.compile(r"[^aeiouàèìòù']{5,}")
TRIPLE = re.compile(r'(.)\1\1')


def shape_problem(low):
    """Why a token cannot be a Corsican word as spelled (None when it can): other scripts (ディスコード),
    letters Corsican spelling does not use (ycbcr, yyyy, json), no vowel (ctrl), runs of five consonants, triple letters."""
    if not CORSICAN_LETTERS.fullmatch(low):
        if ACUTE.search(low) and CORSICAN_LETTERS.fullmatch(ACUTE.sub('a', low)):
            return 'non-corsican-spelling'
        return 'non-corsican-letters'
    if FOREIGN_LETTERS.search(low):
        return 'non-corsican-letters'
    # ghj and chj write one consonant (aghjunghje, inghjò, cerchju).
    if not has_vowel(low) or CONSONANT_RUN.search(re.sub('[gc]hj', 'G', low)) or TRIPLE.search(low):
        return 'fragment'
    return None


def nfc(text):
    return unicodedata.normalize('NFC', text.replace('’', "'"))


def read_tsv(path):
    rows = []
    lines = [line for line in path.read_text(encoding='utf-8').splitlines() if line and not line.startswith('#')]
    header = lines[0].split('\t')
    for line in lines[1:]:
        rows.append(dict(zip(header, line.split('\t'))))
    return rows


def wiki_counts():
    """Word counts in the prose of Vikipedia articles, with how often each word is capitalised mid-sentence."""
    counts, caps, mid = Counter(), Counter(), Counter()

    def clean(t):
        t = re.sub(r'<!--.*?-->', ' ', t, flags=re.S)
        t = re.sub(r'<ref[^>]*/>', ' ', t)
        t = re.sub(r'<ref.*?</ref>', ' ', t, flags=re.S)
        for _ in range(4):
            t = re.sub(r'\{\{[^{}]*\}\}', ' ', t)
        t = re.sub(r'\{\|.*?\|\}', ' ', t, flags=re.S)
        t = re.sub(r'\[\[(?:[^\]|:]*):[^\]]*\]\]', ' ', t)
        t = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', t)
        t = re.sub(r'\[https?://\S+\s*([^\]]*)\]', r'\1', t)
        t = re.sub(r'https?://\S+', ' ', t)
        t = re.sub(r'<[^>]+>', ' ', t)
        t = html.unescape(re.sub(r"'{2,}", '', t))
        return '\n'.join(line for line in t.splitlines() if line and not line.startswith(('|', '!', '{', '}', '=')))

    with bz2.open(RESOURCES / 'wikimedia/cowiki-latest-pages-articles.xml.bz2', 'rb') as stream:
        ns = None
        for _, element in ET.iterparse(stream):
            tag = element.tag.rsplit('}', 1)[-1]
            if tag == 'ns':
                ns = element.text
            elif (tag == 'text' and ns == '0' and element.text and not element.text.lstrip().startswith('#')
                  and not element.text.lstrip().startswith(BOT_STUB)):
                for sentence in re.split(r'(?<=[.!?])\s+|\n', clean(element.text)):
                    for index, match in enumerate(WORD.finditer(sentence)):
                        word = nfc(match.group())
                        low = word.lower()
                        counts[low] += 1
                        if index:
                            mid[low] += 1
                            if word[0].isupper():
                                caps[low] += 1
            elif tag == 'page':
                element.clear()
    return counts, caps, mid


def wiktionary_words():
    words = set()
    for line in (RESOURCES / 'kaikki/kaikki.org-dictionary-Corsican.jsonl').read_text(encoding='utf-8').splitlines():
        entry = json.loads(line)
        words.add(nfc(entry['word']).lower())
        for form in entry.get('forms', []):
            if 'table-tags' not in form.get('tags', []) and ' ' not in form.get('form', ''):
                words.add(nfc(form['form']).lower())
    return words


def apertium_words():
    text = (RESOURCES / 'apertium/apertium-cos.cos.dix').read_text(encoding='utf-8')
    return {nfc(m).lower() for m in re.findall(r'<e[^>]*lm="([^"]+)"', text)}


def tatoeba_words():
    words = Counter()
    with bz2.open(RESOURCES / 'tatoeba/cos_sentences.tsv.bz2', 'rt', encoding='utf-8') as stream:
        for line in stream:
            for word in WORD.findall(line.split('\t')[-1]):
                words[nfc(word).lower()] += 1
    return words


def lexicon_counts():
    """Word counts in the Corsican column of the project lexicons, and in their English column."""
    corsican, english, caps, mid = Counter(), Counter(), Counter(), Counter()
    for path in LEXICONS:
        for line in path.read_text(encoding='utf-8').splitlines():
            fields = line.split('|')
            if line.startswith('#') or len(fields) != 3:
                continue
            for column, counter in ((fields[2], corsican), (fields[0], english)):
                text = re.sub(r'%\w+|\{[^}]*\}|<[^>]+>|&\w+;|\$\w+', ' ', column)
                for index, word in enumerate(WORD.findall(text)):
                    if word.isupper() and len(word) > 1:
                        continue
                    low = nfc(word).lower()
                    counter[low] += 1
                    if counter is corsican and index:
                        mid[low] += 1
                        caps[low] += word[0].isupper()
    return corsican, english, caps, mid


def old_wordlist():
    text = subprocess.run(['git', 'show', f'{OLD_WORDLIST_COMMIT}:{OLD_WORDLIST}'], cwd=ROOT, check=True,
                          capture_output=True, text=True, encoding='utf-8').stdout
    words = {}
    for line in text.splitlines():
        if line.startswith('#') or '\t' not in line:
            continue
        word, count = line.split('\t')
        words[word] = int(count)
    return words


def fold(word):
    """Keyman's default search key: lowercase, accents removed (Bastìa and Bastia are one key)."""
    decomposed = unicodedata.normalize('NFD', word.lower())
    return ''.join(c for c in decomposed if not unicodedata.combining(c))


def place_names():
    """{word: Wikidata item} for the words of the Corsican place labels of sources/places.tsv.

    A label of several words gives its capitalised words of three letters or more (Sari è Sulinzara: Sari,
    Sulinzara); an elided word gives its name (d'Orezza: Orezza); a disambiguation in brackets is dropped
    (Luri (pieve)). The first item, in file order, names the word's source.
    """
    words = {}
    for row in read_tsv(SOURCES / 'places.tsv'):
        label = re.sub(r'\s*\([^)]*\)', '', nfc(row['label']))
        for token in re.split(r'[\s-]+', label):
            token = token.rsplit("'", 1)[-1]
            if len(token) >= 3 and token[0].isupper() and token == token[0] + token[1:].lower():
                words.setdefault(token, row['qid'])
    return words


def has_vowel(word):
    return re.search(r'[aeiouàèìòùáéíóúâêîôûäëïöü]', word) is not None


def main():
    wiki, wiki_caps, wiki_mid = wiki_counts()
    wiki_total = sum(wiki.values())
    wiktionary, apertium, tatoeba = wiktionary_words(), apertium_words(), tatoeba_words()
    lexicon, english, lexicon_caps, lexicon_mid = lexicon_counts()
    lexicon_total = sum(lexicon.values())
    daily = {nfc(row['word']): int(row['tier']) for row in read_tsv(SOURCES / 'daily.tsv')}
    adecec = {nfc(row['word']).lower() for row in read_tsv(SOURCES / 'adecec.tsv')}
    conjugations = read_tsv(SOURCES / 'cunghjugarellu.tsv')
    pairs = read_tsv(SOURCES / 'variant-pairs.tsv')

    def frequency_weight(low):
        return wiki[low] * 1e7 / wiki_total + LEXICON_SHARE * lexicon[low] * 1e7 / lexicon_total

    def attestation(low):
        """The strongest external source that has the word, or None."""
        if low in conjugation_forms:
            return 'cunghjugarellu'
        if low in adecec:
            return 'adecec'
        if low in wiktionary:
            return 'wiktionary'
        if low in tatoeba:
            return 'tatoeba'
        if wiki[low] >= 5:
            return 'vikipedia'
        if low in apertium:
            return 'apertium'
        return None

    def natural_case(low):
        """Proper nouns keep their capital: Vikipedia writes them capitalised almost every time mid-sentence."""
        if wiki_mid[low] >= 5 and wiki_caps[low] >= 0.9 * wiki_mid[low]:
            return low[0].upper() + low[1:]
        return low

    def foreign(low):
        """A name or English word left untranslated in software strings (Firefox, Google, the, of...)."""
        if low in NOT_WORDS or low in PRODUCT_NAMES:
            return True
        if low in wiktionary or low in apertium or low in tatoeba or low in adecec or low in daily_low:
            return False
        return english[low] >= 0.5 * max(lexicon[low], 1)

    conjugation_forms = {nfc(row['form']).lower() for row in conjugations}
    daily_low = {word.lower() for word in daily}

    # 1. Audit of the old list.
    old = old_wordlist()
    removed, kept = {}, {}
    for word, count in old.items():
        low = nfc(word).lower()
        source = attestation(low)
        if low != word and low in old:
            removed[word] = (count, 'duplicate', f'same word as "{low}" once normalised')
        elif foreign(low):
            removed[word] = (count, 'foreign-or-name', 'also written so in the English source strings; '
                             'not found in a Corsican dictionary')
        elif shape_problem(low) and source != 'wiktionary' and low not in daily_low:
            reason = shape_problem(low)
            removed[word] = (count, reason, {
                'non-corsican-spelling': 'acute accent (entrée, moiré, periféricu); Corsican spelling writes grave '
                                         'accents',
                'non-corsican-letters': 'another script, or k, w, x, y, a lone j: letters Corsican spelling does '
                                        'not use',
                'fragment': 'no vowel, a run of five consonants or a letter written three times'}[reason])
        elif len(low) <= 2 and source is None:
            removed[word] = (count, 'fragment', 'no vowel or one-two letters found in no Corsican source')
        elif lexicon[low] == 0 and source is None:
            removed[word] = (count, 'gone-from-lexicon', 'no longer in the lexicon (corrected since the list was '
                             'built) and found in no external source')
        elif source is None and lexicon[low] < 3:
            removed[word] = (count, 'unattested-rare', f'{lexicon[low]} occurrence(s) in the lexicon, found in no '
                             'external source')
        else:
            kept[low] = source

    # 2. Candidates: the kept words, the attested daily words, conjugations, ADECEC words, frequent Vikipedia words
    #    that a dictionary or the lexicon also has.
    candidates = dict(kept)
    for word in daily:
        low = word.lower()
        # A daily word found nowhere else stays, marked as an AI proposal (REVIEW.md lists them for checking).
        candidates[low] = attestation(low) or ('ai' if low not in kept else None)
    for low in conjugation_forms | adecec:
        candidates[low] = attestation(low)
    for low, count in wiki.items():
        if count < 30 or low in candidates or foreign(low) or not has_vowel(low) or len(low) < 2:
            continue
        if (low in wiktionary or low in apertium or lexicon[low] >= 3) and not shape_problem(low):
            candidates[low] = attestation(low)

    entries, dropped_names = {}, []
    for low, source in candidates.items():
        weight = frequency_weight(low)
        tier = daily.get(low) or daily.get(low[0].upper() + low[1:])
        if tier:
            weight = max(weight, TIER_FLOOR[tier])
        if low in tatoeba:
            weight = max(weight, TATOEBA_FLOOR)
        if source is None:
            source, status = 'corsu-lexicon', 'corsu-lexicon'
        elif source == 'ai':
            status = 'ai-proposal'
        else:
            status = 'attested'
        word = natural_case(low)
        if word != low and lexicon[low] >= 3 and lexicon_caps[low] < 0.9 * max(lexicon_mid[low], 1):
            word = low  # the lexicon writes it in lowercase (secondi, uniti, omessa): a common word
        corsican_name = lexicon[low] >= 3 and wiki[low] >= 30 and english[low] == 0  # Germania, Svizzera
        if word != low and source in ('vikipedia', 'apertium', 'tatoeba') and not tier and not corsican_name:
            # A capitalised name known only from a corpus (León in Vikipedia, Tom in Tatoeba): not a word to
            # suggest. Names that Wiktionary has as Corsican words (Spagna, Genuva) stay.
            dropped_names.append(low)
            if low in old:
                removed[low] = (old[low], 'corpus-name', 'capitalised name known only from Vikipedia or Tatoeba')
            continue
        if tier and low not in daily and low[0].upper() + low[1:] in daily:
            word = low[0].upper() + low[1:]
        entries[low] = dict(word=word, weight=max(1, round(weight)), source=source, status=status)

    # 3. Northern and southern forms: conjugations paired by verb, tense and person, plus the listed pairs.
    northern, southern, pair_rows = defaultdict(set), defaultdict(set), []
    slots = defaultdict(lambda: {'supranacciu': set(), 'suttanacciu': set()})
    for row in conjugations:
        slots[(row['table'], row['tense'], row['person'])][row['version']].add(nfc(row['form']).lower())
    for (table, tense, person), forms in slots.items():
        north, south = forms['supranacciu'], forms['suttanacciu']
        for form in north:
            northern[form].add(f'cunghjugarellu:{table}')
        for form in south:
            southern[form].add(f'cunghjugarellu:{table}')
        # A slot where one version only has a form with a final apostrophe (sta', va', po') is left unpaired:
        # the other version's form is not the odd one out.
        if north and south and north != south:
            pair_rows.append((north, south, 'cunghjugarellu', True, 0))
    for row in pairs:
        north = {nfc(form).lower() for form in row['cismuntincu'].split('/')}
        south = {nfc(form).lower() for form in row['pumuntincu'].split('/')}
        for form in north:
            northern[form].add(row['source'])
        for form in south:
            southern[form].add(row['source'])
        floor = TIER_FLOOR[int(row['tier'])] if row.get('tier') else 0
        pair_rows.append((north, south, row['source'], row['lower_other'] == 'yes', floor))
    north_only = set(northern) - set(southern)
    south_only = set(southern) - set(northern)
    # Forms that are also ordinary words in both areas: eri (yesterday), sete (thirst), mane (morning), sani
    # (healthy), vani (vain), pari (equal), novi (new), sì (yes / if), sò (I know).
    homographs = {'eri', 'sete', 'mane', 'sani', 'vani', 'pari', 'novi', 'nove', 'sì', 'sò', 'site', 'deti', 'feti'}

    variant_weight = {'cismuntincu': {}, 'pumuntincu': {}}
    variant_source = {}
    for north, south, source, lower_other, floor in pair_rows:
        north_specific, south_specific = north & north_only, south & south_only
        if not north_specific and not south_specific:
            continue
        base = max([entries[f]['weight'] for f in north | south if f in entries] + [1000, floor])
        for variety, own, other in (('cismuntincu', north_specific, south_specific),
                                    ('pumuntincu', south_specific, north_specific)):
            for form in own:
                variant_weight[variety][form] = max(variant_weight[variety].get(form, 0), base)
                variant_source[form] = source
            if lower_other:
                for form in other - homographs:
                    # When several pairs lower the same form, the strongest pair sets its weight.
                    lowered = max(1, round(base * OTHER_SHARE))
                    variant_weight[variety][form] = max(variant_weight[variety].get(form, 0), lowered)
                    variant_source[form] = source
    # Every variety-specific form is also in the shared list, at half its pair's weight (daily words keep their
    # own weight), so that a keyboard that only loads shared.tsv still knows both.
    for form in sorted(north_only | south_only):
        own = variant_weight['cismuntincu' if form in north_only else 'pumuntincu'].get(form)
        if own is None:
            continue
        source = variant_source[form].split(':')[0]
        half = max(1, own // 2)
        entry = entries.get(form)
        if entry is None:
            entries[form] = dict(word=natural_case(form), weight=half, source=source, status='attested')
            continue
        entry['weight'] = max(entry['weight'], half) if form in daily_low else half
        if entry['status'] != 'attested' or entry['source'] in ('vikipedia', 'apertium'):
            entry.update(source=source, status='attested')

    # 4. Corsican place names (Wikidata). A name whose search key is already a word of the list is left to that word:
    #    Bastia (written so by Tatoeba and 25 times more often than Bastìa in Vikipedia), Corti, Sartè, or common
    #    words such as piana, lama, felce. A word that Vikipedia mostly writes in lowercase mid-sentence is also a
    #    common word (vescuvatu, stazzona, valle): it is added in lowercase, and Keyman keeps the capital when
    #    one is typed. The Vikipedia dump is used only for these checks and for the weight.
    known = {fold(low) for low in entries}
    place_stats = Counter()
    for word, qid in place_names().items():
        low = word.lower()
        if shape_problem(low):
            place_stats['not_corsican_spelling'] += 1
        elif fold(low) in known:
            place_stats['already_a_word'] += 1
        else:
            common = wiki_mid[low] >= 5 and wiki_caps[low] < 0.5 * wiki_mid[low]
            place_stats['added_in_lowercase' if common else 'added'] += 1
            place_stats['seen_in_vikipedia'] += wiki[low] > 0
            known.add(fold(low))
            weight = min(max(frequency_weight(low), PLACE_FLOOR), PLACE_CAP)
            entries[low] = dict(word=low if common else word, weight=round(weight), source=f'wikidata:{qid}',
                                status='attested')
            removed.pop(low, None)

    def license_of(source):
        return LICENSES[source.split(':')[0]]

    def write(path, rows):
        lines = [HEADER] + [f"{r['word']}\t{r['weight']}\t{r['variant']}\t{r['source']}\t{license_of(r['source'])}"
                            f"\t{r['status']}\n" for r in sorted(rows, key=lambda r: (-r['weight'], r['word']))]
        path.write_text(''.join(lines), encoding='utf-8')

    write(DATA / 'shared.tsv', [dict(e, variant='shared') for e in entries.values()])
    for variety, weights in variant_weight.items():
        rows = []
        for form, weight in weights.items():
            belongs = 'cismuntincu' if form in north_only else 'pumuntincu'
            rows.append(dict(word=natural_case(form), weight=weight, variant=belongs,
                             source=variant_source[form], status='attested'))
        write(DATA / f'{variety}.tsv', rows)

    (DATA / 'audit').mkdir(exist_ok=True)
    with (DATA / 'audit/removed.tsv').open('w', encoding='utf-8') as out:
        out.write('# Words of the old generated list (keyboard/platykalt.co.corsu/source/wordlist.tsv) that the new\n'
                  '# lists drop, with the reason found by keyboard/data/tools/make_vocab.py.\n')
        out.write('word\told_weight\treason\tdetail\n')
        for word, (count, reason, detail) in sorted(removed.items(), key=lambda item: (item[1][1], -item[1][0])):
            out.write(f'{word}\t{count}\t{reason}\t{detail}\n')
    statuses = Counter(e['status'] for e in entries.values())
    sources = Counter(e['source'].split(':')[0] for e in entries.values())
    merged = {v: {low: variant_weight[v].get(low, e['weight']) for low, e in entries.items()} for v in variant_weight}
    differing = sorted(low for low in entries if merged['cismuntincu'][low] != merged['pumuntincu'][low])
    stats = dict(
        old_entries=len(old), removed=len(removed), removed_by_reason=Counter(r[1] for r in removed.values()),
        shared_entries=len(entries), shared_by_status=statuses, shared_by_source=sources,
        new_from_outside_old_list=len([low for low in entries if low not in old]),
        cismuntincu_entries=len(variant_weight['cismuntincu']), pumuntincu_entries=len(variant_weight['pumuntincu']),
        northern_only_forms=len(north_only), southern_only_forms=len(south_only),
        words_ranked_differently=len(differing), wiki_tokens=wiki_total, lexicon_tokens=lexicon_total,
        place_words=place_stats,
    )
    (DATA / 'audit/stats.json').write_text(json.dumps(stats, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
