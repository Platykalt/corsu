#!/usr/bin/env python3
"""Build the keyboard vocabulary lists keyboard/data/{shared,cismuntincu,pumuntincu}.tsv.

    python3 keyboard/data/tools/make_vocab.py

Inputs:
  - the downloaded resources of tools/fetch_resources.py (Vikipedia dump, Wiktionary extract, Apertium dictionary,
    Tatoeba sentences), read from $CORSU_RESOURCES or ~/.local/share/corsu/resources and never modified;
  - the hand-checked source files in keyboard/data/sources/ (daily words, ADECEC pages, U Cunghjugarellu forms,
    northern/southern pairs, forms a reference writes in full);
  - the project lexicons (Corsu's own software translations), counted all alike: a word does not become more
    trustworthy because of the file it comes from;
  - the Corsican place names of sources/places.tsv (Wikidata, fetched by tools/fetch_places.py) and the official
    commune names of sources/communes-official.tsv (INSEE, fetched by tools/fetch_communes.py);
  - the old generated word list keyboard/platykalt.co.corsu/source/wordlist.tsv as of version 0.9.0 (read from git:
    tools/build_keyboard.py now rewrites that file from these lists), only to report what changed.

Outputs the three lists, keyboard/data/held-back.tsv (forms that only the whole-dump Vikipedia count supports: not
shipped, with their passages), keyboard/data/audit/removed.tsv (what the old list had and the new one drops, with the
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
    'cog': 'etalab-2.0',
    'homographs': 'GPL-3.0-or-later',
    'acronyms': 'GPL-3.0-or-later',
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
# Weight of a word of an official commune name that the Corsican names do not already give (Bastelicaccia, Zicavo,
# Ajaccio; sources/communes-official.tsv): its Vikipedia frequency, between these bounds. Low on purpose: the name
# must be known, so that auto-correction keeps it as typed, but it must not outrank a Corsican place name (at least
# PLACE_FLOOR) or an everyday word; Vikipedia counts Florent or Martino mostly as first names, so the cap is low.
# Official names are spelled as INSEE writes them, so the Corsican spelling checks do not apply.
OFFICIAL_FLOOR = 20
OFFICIAL_CAP = PLACE_FLOOR
# Weight of a curated acronym (sources/acronyms.tsv): known, so auto-correction keeps it, never among the suggestions
# of an everyday prefix.
ACRONYM_WEIGHT = 20
# In a variety's preference list, the other variety's form keeps this share of the pair's weight.
OTHER_SHARE = 0.25
# Vikipedia occurrences needed to add another form of a listed word (step 5b): the attestation threshold.
INFLECTED_MIN = 5
# ... counted in Corsican prose only (class Prose: not in titles, quotations, verse, bibliographies or Italian and
# French sentences), and in at least this many articles, so that one article quoting a text cannot add a form.
INFLECTED_ARTICLES = 3
# ... and their weight: their Vikipedia frequency, at most the weight of the listed form and at most INFLECTED_CAP.
# They are added so that a correct word typed on purpose is known (auto-correction keeps it), not to be suggested
# early: with this cap no word of weight 100 or more leaves the top 3 of a 1-4 letter prefix (REVIEW.md). Without
# it, abitanti (854 times in an encyclopedia) and rumani took the first places of short prefixes.
INFLECTED_CAP = 100
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

    prose = Prose()
    with bz2.open(RESOURCES / 'wikimedia/cowiki-latest-pages-articles.xml.bz2', 'rb') as stream:
        ns = title = None
        for _, element in ET.iterparse(stream):
            tag = element.tag.rsplit('}', 1)[-1]
            if tag == 'title':
                title = element.text
            elif tag == 'ns':
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
                prose.add(title, element.text, clean)
            elif tag == 'page':
                element.clear()
    return counts, caps, mid, prose


# Sections of a Vikipedia article that list works, references and links, or gather quotations: their titles and
# quotations are in the language of the work quoted (Italian, French, Latin...), not Corsican prose.
LIST_SECTIONS = {'riferimenti', 'rifarimenti', 'rifarenzi', 'referenze', 'riferenze', 'note', 'noti', 'ligami',
                 'liami', 'ligami esterni', 'altri prugetti', 'da vede dinò', 'da vede dinù', 'da veda dinò',
                 'da veda', 'bibliugrafia', 'bibliografia', 'fonti', 'citazioni', 'citazione', 'albumi', 'opari',
                 'opere', 'discugrafia', 'discografia', 'filmugrafia', 'filmografia', 'articuli cunnessi',
                 'publicazioni', 'pubblicazioni', 'scritti', 'libri'}
# Function words of Italian, French and Latin that Corsican does not write (Corsican: u, di u, cù, chì, cum'è, hè,
# sò; più, la, le, tra and è are left out because Corsican texts also write them). A sentence holding one is
# treated as a foreign passage: "La calligrafia corsiva insegnata nelle scuole italiane (secoli XX-XXI)".
FOREIGN_MARKERS = {
    'il', 'della', 'dello', 'delle', 'degli', 'nella', 'nelle', 'nello', 'negli', 'sono', 'gli', 'perché',
    'anche', 'questo', 'essere', 'siamo', 'hanno', 'dei', 'del', 'alla', 'alle', 'agli', 'dalla', 'dalle', 'sul',
    'sulla', 'nel', 'che', 'con', 'come',                                               # Italian
    'les', 'des', 'est', 'une', 'avec', 'pour', 'dans', 'sur', 'du', 'au', 'aux', 'et',  # French
    'sunt', 'quae', 'quod', 'cum',                                                       # Latin
}
QUOTED = re.compile(r'«[^»\n]{0,400}»|“[^”\n]{0,400}”|„[^“”\n]{0,400}[“”]|"[^"\n]{0,400}"')


class Prose:
    """Where each word of Vikipedia occurs: in Corsican prose, or in a passage that is not (step 5b, 5d).

    Counting every token of the dump let in forms that Vikipedia only quotes: titles of works in italics, quotations,
    verse, bibliographies, sentences in Italian or French inside a Corsican article (secoli, from "La calligrafia
    corsiva insegnata nelle scuole italiane (secoli XX-XXI)" and the Italian anthem). Corsican prose is what is left
    of an article once these are taken out: text outside a list section (LIST_SECTIONS), outside italics ('' '') and
    quotation marks, in a sentence with no FOREIGN_MARKERS word (a block of verse or indented lines: in a block with
    none).
    For each word: its prose count, the articles it occurs in as prose, how often it occurs in each kind of left-out
    passage, and the first passages seen (for keyboard/data/held-back.tsv)."""

    KINDS = ('list-section', 'italics', 'quotation', 'foreign-verse', 'foreign-sentence')

    def __init__(self):
        self.counts, self.articles = Counter(), defaultdict(set)
        self.left_out = defaultdict(Counter)
        self.passages = defaultdict(list)

    def note(self, low, title, kind, text):
        if len(self.passages[low]) < 3 and not any(p[0] == title for p in self.passages[low]):
            self.passages[low].append((title, kind, text))

    def words(self, title, kind, text, clean):
        snippet = ' '.join(clean(text).split())
        for match in WORD.finditer(snippet):
            low = nfc(match.group()).lower()
            if kind == 'prose':
                self.counts[low] += 1
                self.articles[low].add(title)
            else:
                self.left_out[low][kind] += 1
            start = max(0, match.start() - 60)
            self.note(low, title, kind, snippet[start:match.end() + 60])

    def add(self, title, text, clean):
        # References, comments, templates and tables first, over the whole text (they span lines); links, markup
        # and the quote marks of the wiki syntax are cleaned span by span, once italics are told apart.
        text = re.sub(r'<!--.*?-->', ' ', text, flags=re.S)
        text = re.sub(r'<ref[^>]*/>', ' ', text)
        text = re.sub(r'<ref.*?</ref>', ' ', text, flags=re.S)
        for _ in range(4):
            text = re.sub(r'\{\{[^{}]*\}\}', ' ', text)
        for _ in range(2):
            text = re.sub(r'\{\|(?:(?!\{\|).)*?\|\}', ' ', text, flags=re.S)
        text = re.sub(r'<math[^>]*>.*?</math>', ' ', text, flags=re.S | re.I)
        text = re.sub(r'<(poem|blockquote)[^>]*>.*?</\1>', lambda m: '\n' + m.group().replace('\n', '<br>\n') + '\n',
                      text, flags=re.S | re.I)
        listed_level, verse = 0, []
        for line in text.splitlines() + ['']:
            # Verse (<br> line breaks, <poem>, <blockquote>) and indented blocks (":" lines: poems, proverbs,
            # quotations) are read as one block: a poem in Italian has its markers on some lines only ("Noi siamo
            # da secoli<br /> Calpesti, derisi"). Corsican verse and proverbs count as prose.
            if not listed_level and (re.search(r'<br\s*/?>', line, re.I) or line.startswith(':')):
                verse.append(line)
                continue
            if verse:
                block = ' '.join(verse)
                if {nfc(w).lower() for w in WORD.findall(clean(block))} & FOREIGN_MARKERS:
                    self.words(title, 'foreign-verse', block, clean)
                else:
                    for verse_line in verse:
                        self.line(title, verse_line, clean)
                verse = []
            heading = re.fullmatch(r'\s*(=+)\s*(.*?)\s*=+\s*', line)
            if heading:
                level = len(heading.group(1))
                if listed_level and level <= listed_level:
                    listed_level = 0
                if not listed_level and nfc(heading.group(2)).lower() in LIST_SECTIONS:
                    listed_level = level
                continue
            if line.lstrip().startswith(('|', '!', '{', '}')):
                continue
            if listed_level:
                self.words(title, 'list-section', line, clean)
            else:
                self.line(title, line, clean)

    def line(self, title, line, clean):
        """One line of an article outside list sections: italics, quotations, then each sentence."""
        line = re.sub(r"'''''(.*?)'''''", r"''\1''", line).replace("'''", '\x01')
        for span in re.findall(r"''(?:(?!'').)+''", line):
            self.words(title, 'italics', span, clean)
        line = re.sub(r"''(?:(?!'').)+''", ' ', line).replace('\x01', "'''")
        for span in QUOTED.findall(line):
            self.words(title, 'quotation', span, clean)
        line = QUOTED.sub(' ', line)
        for sentence in re.split(r'(?<=[.!?])\s+', line):
            lows = {nfc(w).lower() for w in WORD.findall(clean(sentence))}
            self.words(title, 'foreign-sentence' if lows & FOREIGN_MARKERS else 'prose', sentence, clean)


def wiktionary_words():
    words = set()
    for line in (RESOURCES / 'kaikki/kaikki.org-dictionary-Corsican.jsonl').read_text(encoding='utf-8').splitlines():
        entry = json.loads(line)
        words.add(nfc(entry['word']).lower())
        for form in entry.get('forms', []):
            if 'table-tags' not in form.get('tags', []) and ' ' not in form.get('form', ''):
                words.add(nfc(form['form']).lower())
    return words


def wiktionary_common_words():
    """Wiktionary's Corsican words and forms of entries that are not names (orsu, argentu, mansu): common words."""
    words = set()
    for line in (RESOURCES / 'kaikki/kaikki.org-dictionary-Corsican.jsonl').read_text(encoding='utf-8').splitlines():
        entry = json.loads(line)
        if entry.get('pos') == 'name':
            continue
        words.add(nfc(entry['word']))
        for form in entry.get('forms', []):
            if 'table-tags' not in form.get('tags', []) and ' ' not in form.get('form', ''):
                words.add(nfc(form['form']))
    return words


def wiktionary_forms():
    """{form: headword} for Wiktionary's Corsican words and forms that are not names, as written (step 5c).

    Conjugation and declension forms of an entry count (manghjatu, cantendu); a form tagged as a misspelling or
    archaic, a template placeholder and a phrase of several words do not."""
    forms = {}
    for line in (RESOURCES / 'kaikki/kaikki.org-dictionary-Corsican.jsonl').read_text(encoding='utf-8').splitlines():
        entry = json.loads(line)
        if entry.get('pos') == 'name':
            continue
        head = nfc(entry['word'])
        senses = {tag for sense in entry.get('senses', []) for tag in sense.get('tags', [])}
        if not senses & {'misspelling', 'archaic'}:
            forms.setdefault(head, head)
        for form in entry.get('forms', []):
            tags = set(form.get('tags', []))
            text = nfc(form.get('form', ''))
            if tags & {'table-tags', 'inflection-template', 'misspelling', 'archaic', 'canonical'} or ' ' in text:
                continue
            forms.setdefault(text, head)
    return forms


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


def official_names():
    """{word: INSEE code} for the words of the official commune names of sources/communes-official.tsv, split as
    place_names() splits the Corsican labels (Sainte-Lucie-de-Tallano: Sainte, Lucie, Tallano)."""
    words = {}
    for row in read_tsv(SOURCES / 'communes-official.tsv'):
        for token in re.split(r'[\s-]+', nfc(row['name'])):
            token = token.rsplit("'", 1)[-1]
            if len(token) >= 3 and token[0].isupper() and token == token[0] + token[1:].lower():
                words.setdefault(token, row['code'])
    return words


def has_vowel(word):
    return re.search(r'[aeiouàèìòùáéíóúâêîôûäëïöü]', word) is not None


def main():
    wiki, wiki_caps, wiki_mid, prose = wiki_counts()
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
        """The external source cited for the word, or None. An openly licensed source that has the word is cited
        first; the reference works consulted without a reuse licence (U Cunghjugarellu, the ADECEC pages) are
        cited when they are the only ones. Every form checked in them stays listed in sources/, whatever is
        cited here; the order changes no weight."""
        if low in wiktionary:
            return 'wiktionary'
        if low in tatoeba:
            return 'tatoeba'
        if wiki[low] >= 5:
            return 'vikipedia'
        if low in apertium:
            return 'apertium'
        if low in conjugation_forms:
            return 'cunghjugarellu'
        if low in adecec:
            return 'adecec'
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

    # 5. Official commune names (INSEE): Bastelicaccia next to Bastilicaccia. A legitimate spelling typed on purpose
    #    must be known, or auto-correction replaces it with a close Corsican name. Words already known (same search
    #    key) are left as they are; the others get a low weight (OFFICIAL_FLOOR..OFFICIAL_CAP).
    for word, code in official_names().items():
        if fold(word) in known:
            place_stats['official_already_known'] += 1
            continue
        known.add(fold(word))
        place_stats['official_added'] += 1
        weight = min(max(frequency_weight(word.lower()), OFFICIAL_FLOOR), OFFICIAL_CAP)
        entries[word.lower()] = dict(word=word, weight=round(weight), source=f'cog:{code}', status='attested')
        removed.pop(word.lower(), None)

    # The list as the rules above leave it: the forms of steps 5b-5e are added to be known, and must not push any of
    # these words out of the suggestions (see "Keeping the added forms below" after step 5e).
    base_entries = set(entries)

    # 5b. Other forms of a word: the feminine and plural of a noun, adjective or participle (tradizioni next to
    #     tradizione, fundata next to fundatu, partuti next to partutu), written at least INFLECTED_MIN times in
    #     Vikipedia, mostly in lowercase, when the list has another form of the word or when Vikipedia also has its
    #     masculine singular in -u (partutu, partuti, partuta), the Corsican ending that sets these paradigms apart
    #     from Italian ones. Auto-correction (Keyman 19) replaced such words, correct but unknown, with a listed
    #     form: tradizioni became tradizione, partuti partiti. Only the final vowel may differ (-u/-a/-i/-e); no
    #     other rule is applied, and a form found in no source is not invented. Weight: see INFLECTED_CAP.
    #     Since 2026-10-19 (second pass) the occurrences are counted in Corsican prose only (class Prose), in at
    #     least INFLECTED_ARTICLES articles: counting every token let in Italian quoted by Vikipedia (secoli, from
    #     the title of an image and the Italian anthem). A form the old count would have taken and the prose count
    #     does not is held back (keyboard/data/held-back.tsv, with its passages), unless another source writes it
    #     (Wiktionary: step 5c; Apertium, Tatoeba, U Cunghjugarellu, ADECEC: here).
    def word_shape(low):
        return (len(low) >= 4 and "'" not in low and not foreign(low) and not shape_problem(low) and has_vowel(low)
                and wiki_caps[low] < 0.5 * max(wiki_mid[low], 1))

    def vikipedia_form(low, counted='prose'):
        """Whether Vikipedia writes low as a word of its own: 'raw', 5 times anywhere (the rule before the prose
        count); 'prose', 5 times in Corsican prose across 3 articles; 'partner', 5 times anywhere and at least once
        in prose (the other form of a paradigm, which only shows that the word has a paradigm in -u)."""
        if counted == 'raw':
            return wiki[low] >= INFLECTED_MIN and word_shape(low)
        if counted == 'partner':
            return wiki[low] >= INFLECTED_MIN and prose.counts[low] >= 1 and word_shape(low)
        return prose_attested(low) and word_shape(low)

    def prose_attested(low):
        return prose.counts[low] >= INFLECTED_MIN and len(prose.articles[low]) >= INFLECTED_ARTICLES

    def prose_weight(low):
        return prose.counts[low] * 1e7 / wiki_total + LEXICON_SHARE * lexicon[low] * 1e7 / lexicon_total

    def other_source(low):
        """An external source other than Vikipedia and Wiktionary that writes the word (Wiktionary: step 5c)."""
        for name, words in (('tatoeba', tatoeba), ('apertium', apertium), ('cunghjugarellu', conjugation_forms),
                            ('adecec', adecec)):
            if low in words:
                return name
        return None

    def form_of(low, counted):
        """The listed form that caps the weight of another form of a word, '' for a form of a Vikipedia paradigm
        in -u, or None when low is not another form of a word."""
        stem = low[:-1]
        siblings = [stem + end for end in 'aeiu' if end != low[-1] and stem + end in entries
                    and entries[stem + end]['word'] == stem + end]
        if siblings:
            # The listed form with the highest weight (ties: alphabetical) caps the weight.
            return max(siblings, key=lambda form: (entries[form]['weight'], [-ord(c) for c in form]))
        partner = 'partner' if counted == 'prose' else counted
        if any(end != low[-1] and vikipedia_form(stem + end, partner) for end in 'aeiu') \
                and (low[-1] == 'u' or vikipedia_form(stem + 'u', partner)):
            return ''
        return None

    inflected, held = {}, {}
    for low in sorted(wiki):
        if low[-1:] not in ('a', 'e', 'i', 'u') or low in entries or fold(low) in known \
                or not vikipedia_form(low, 'raw'):
            continue
        sibling = form_of(low, 'prose') if vikipedia_form(low) else None
        if sibling is not None:
            inflected[low] = (sibling, 'vikipedia')
        elif form_of(low, 'raw') is not None:
            source = other_source(low)
            if source:
                inflected[low] = (form_of(low, 'raw'), source)
            else:
                held[low] = ('5b', form_of(low, 'raw'))
    for low, (sibling, source) in inflected.items():
        known.add(fold(low))
        weight = min(prose_weight(low) if source == 'vikipedia' else frequency_weight(low),
                     entries[sibling]['weight'] if sibling else INFLECTED_CAP, INFLECTED_CAP)
        entries[low] = dict(word=low, weight=max(1, round(weight)), source=source, status='attested')
        removed.pop(low, None)

    # 5c. Wiktionary's Corsican words and forms (manghjatu, cantendu, parlavamu) not yet listed. Wiktionary is the
    #     first source cited for attestation, but only its words that another rule selected were listed, so a
    #     correct form it records could still be replaced by auto-correction. Added as known words, weighed like
    #     the forms of step 5b (at most INFLECTED_CAP), next to any name or word with the same search key. A
    #     regional form (Cismontane, Ultramontane) is only known: no preference list changes.
    wiktionary_added = 0
    for word, head in sorted(wiktionary_forms().items()):
        low = word.lower()
        if (low in entries or len(low) < 2 or not has_vowel(low) or shape_problem(low)
                or not re.fullmatch(r"[^\W\d_]+(?:'[^\W\d_]+)*", word)):
            continue
        weight = min(frequency_weight(low), INFLECTED_CAP)
        entries[low] = dict(word=word, weight=max(1, round(weight)), source='wiktionary', status='attested')
        known.add(fold(low))
        removed.pop(low, None)
        wiktionary_added += 1

    # 5d. Elided forms written at least INFLECTED_MIN times in Vikipedia (l'abitanti, d'Aiacciu, l'ADECEC) whose second
    #     part is a listed word and whose first part is an elision the list already uses at least 5 times (l', d',
    #     un', st', s', ch'...). Keyman's word breaker keeps an elided form as one word, and its correction search
    #     only follows words of the lexicon: auto-correction turned l'abitanti into abitanti. The second part keeps
    #     the case the list gives it. Weight: as in step 5b.
    elisions = Counter(low.split("'")[0] for low in entries if "'" in low)
    # The acronyms of step 7 count as listed words here (l'ADECEC).
    written = {low: entry['word'] for low, entry in entries.items()}
    written.update({nfc(row['word']).lower(): nfc(row['word']) for row in read_tsv(SOURCES / 'acronyms.tsv')})
    acronyms = {nfc(row['word']).lower() for row in read_tsv(SOURCES / 'acronyms.tsv')}
    elided_added = 0
    for low, count in sorted(wiki.items()):
        head, _, tail = low.partition("'")
        if count >= INFLECTED_MIN and tail in held and elisions[head] >= 5 and low not in entries:
            held[low] = ('5d', tail)  # l'equazioni: equazioni itself is held back
            continue
        if (count < INFLECTED_MIN or not tail or low in entries or tail not in written or elisions[head] < 5
                or "'" in tail):
            continue
        if not prose_attested(low) and tail not in acronyms:
            # Same prose rule as step 5b: an elided form in an Italian title or quotation is not Corsican usage. An
            # elided curated acronym keeps the old count: Vikipedia writes l'ADECEC mostly in its bibliographies
            # (the publisher's name), in Corsican.
            held[low] = ('5d', tail)
            continue
        word = head + "'" + written[tail]
        weight = min(prose_weight(low), INFLECTED_CAP)
        entries[low] = dict(word=word, weight=max(1, round(weight)), source='vikipedia', status='attested')
        known.add(fold(low))
        removed.pop(low, None)
        elided_added += 1

    # 5e. Forms a reference work writes in full that no rule above selects (sources/forms.tsv: ghjocanu, written
    #     by U Cunghjugarellu's examples; auto-correction made it ghjovanu). The openly licensed source is cited
    #     first when it has the word (attestation()); weighed like the forms of step 5b.
    for row in read_tsv(SOURCES / 'forms.tsv'):
        low = nfc(row['word']).lower()
        if low in entries:
            continue
        entries[low] = dict(word=low, weight=max(1, round(min(prose_weight(low), INFLECTED_CAP))),
                            source=attestation(low) or 'cunghjugarellu', status='attested')
        known.add(fold(low))
        held.pop(low, None)

    # Held back: forms the raw Vikipedia count would have added and Corsican prose does not attest. They are not in
    #     the lists (so not in the packages); keyboard/data/held-back.tsv gives each one's counts and passages, so a
    #     reviewer can bring one back through a source (sources/, Wiktionary) or reject it.
    held = {low: value for low, value in held.items() if low not in entries}
    with (DATA / 'held-back.tsv').open('w', encoding='utf-8', newline='\n') as out:
        out.write('# Forms that keyboard/data/tools/make_vocab.py does not list: written 5 times or more in the\n'
                  '# Vikipedia dump, but not 5 times in Corsican prose across 3 articles (titles, quotations, foreign\n'
                  '# verse, bibliographies, Italian or French sentences left out), and in no other source. Not shipped.\n'
                  '# Classes and passages: keyboard/data/REVIEW.md, "Second pass".\n')
        columns = ('word', 'step', 'form_of', 'vikipedia_all', 'vikipedia_prose', 'prose_articles', 'left_out',
                   'class', 'reason', 'passages')
        out.write('\t'.join(columns) + '\n')
        for low, (step, of) in sorted(held.items(), key=lambda item: (item[1][0], -wiki[item[0]], item[0])):
            left = prose.left_out[low]
            kinds = ', '.join(f'{kind} {left[kind]}' for kind in Prose.KINDS if left[kind])
            if step == '5d' and of in held:
                reason = f'second part held back ({of})'
            elif prose.counts[low] < INFLECTED_MIN:
                reason = f'{prose.counts[low]} prose occurrence(s) of {wiki[low]}'
            else:
                reason = f'prose in {len(prose.articles[low])} article(s) only'
            where = dict(left, prose=prose.counts[low])
            where['table or template'] = max(0, wiki[low] - sum(where.values()))
            dominant = max(where, key=lambda kind: (where[kind], kind == 'prose'))
            if prose.counts[low] >= INFLECTED_MIN:
                kind = 'corsican-prose-narrow'
            else:
                kind = {'prose': 'corsican-prose-rare', 'list-section': 'title-or-reference',
                        'table or template': 'table-or-template'}.get(dominant, dominant)
            passages = ' | '.join(f'[{title}, {kind}] {text}' for title, kind, text in prose.passages[low])
            out.write(f'{low}\t{step}\t{of or ""}\t{wiki[low]}\t{prose.counts[low]}\t{len(prose.articles[low])}\t'
                      f'{kinds}\t{kind}\t{reason}\t{passages.replace(chr(9), " ")}\n')

    # 6. Common words written like a capitalised entry (orsu / Orsu, corti / Corti): Keyman keeps a word typed exactly
    #    as the list has it, so with only the name a lowercase word typed on purpose became the name. The lowercase
    #    word is added next to it, weighed by its lowercase uses in Vikipedia: from Wiktionary's common (non-name)
    #    forms, and from sources/homographs.tsv for the others (each with its evidence).
    extra = {}
    common = wiktionary_common_words()
    listed = {nfc(row['word']) for row in read_tsv(SOURCES / 'homographs.tsv')}
    for entry in list(entries.values()):
        word = entry['word']
        low = word.lower()
        if word == low or not (low in common or low in listed):
            continue
        lowercase_uses = max(wiki_mid[low] - wiki_caps[low], 0)
        weight = lowercase_uses * 1e7 / wiki_total + LEXICON_SHARE * lexicon[low] * 1e7 / lexicon_total
        extra[low] = dict(word=low, weight=max(1, round(min(weight, int(entry['weight'])))),
                          source='wiktionary' if low in common else 'homographs', status='attested')
    place_stats['lowercase_homographs'] = len(extra)

    # 7. Corsican names of communes written otherwise than their Wikidata label (sources/place-titles.tsv: Vizzani
    #    next to Vezzani), and curated acronyms kept in capitals (sources/acronyms.tsv: ADECEC).
    for row in read_tsv(SOURCES / 'place-titles.tsv'):
        name = nfc(row['name'])
        if fold(name) not in known:
            known.add(fold(name))
            weight = min(max(frequency_weight(name.lower()), PLACE_FLOOR), PLACE_CAP)
            extra[name.lower()] = dict(word=name, weight=round(weight), source=f"wikidata:{row['qid']}",
                                       status='attested')
    for row in read_tsv(SOURCES / 'acronyms.tsv'):
        word = nfc(row['word'])
        extra[word] = dict(word=word, weight=ACRONYM_WEIGHT, source='acronyms', status='attested')
        removed.pop(word.lower(), None)
    extra_keys = set()
    for key, entry in extra.items():
        # Kept under their own key: entries are keyed by the lowercase word, which the name already uses.
        entries[f"\0{entry['word']}"] = entry
        extra_keys.add(f"\0{entry['word']}")

    # Keeping the added forms below. The forms of steps 5b-5e are there so that a correct word typed on purpose is
    #     known (Keyman keeps a typed word that the model lists, whatever its weight: the trie returns the exact
    #     match first, keyboard/data/REVIEW.md). With INFLECTED_CAP alone, a form of weight 100 still pushed listed
    #     words out of a top 3: utile (92) for utilizatu, eccezziunale (91), urigine (99). Each added form now
    #     weighs less than every other word of the list (the rules before them and steps 6-7) in the top 3 of every
    #     prefix of its search key, so it only fills the places that the list leaves empty.
    added = set(entries) - base_entries - extra_keys
    third = {}
    by_prefix = defaultdict(list)
    for low in set(entries) - added:
        key = fold(entries[low]['word'])
        for end in range(1, len(key) + 1):
            by_prefix[key[:end]].append(entries[low]['weight'])
    for prefix, weights in by_prefix.items():
        third[prefix] = min(sorted(weights, reverse=True)[:3])
    lowered = 0
    for low in added:
        key = fold(entries[low]['word'])
        limits = [third[key[:end]] - 1 for end in range(1, len(key) + 1) if key[:end] in third]
        if limits and entries[low]['weight'] > min(limits):
            entries[low]['weight'] = max(1, min(limits))
            lowered += 1

    def license_of(source):
        return LICENSES[source.split(':')[0]]

    def write(path, rows):
        lines = [HEADER] + [f"{r['word']}\t{r['weight']}\t{r['variant']}\t{r['source']}\t{license_of(r['source'])}"
                            f"\t{r['status']}\n" for r in sorted(rows, key=lambda r: (-r['weight'], r['word']))]
        path.write_text(''.join(lines), encoding='utf-8', newline='\n')

    write(DATA / 'shared.tsv', [dict(e, variant='shared') for e in entries.values()])
    for variety, weights in variant_weight.items():
        rows = []
        for form, weight in weights.items():
            belongs = 'cismuntincu' if form in north_only else 'pumuntincu'
            rows.append(dict(word=natural_case(form), weight=weight, variant=belongs,
                             source=variant_source[form], status='attested'))
        write(DATA / f'{variety}.tsv', rows)

    (DATA / 'audit').mkdir(exist_ok=True)
    with (DATA / 'audit/removed.tsv').open('w', encoding='utf-8', newline='\n') as out:
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
        place_words=place_stats, inflected_forms=len(inflected), wiktionary_forms=wiktionary_added, elided_forms=elided_added,
        held_back=Counter(step for step, _ in held.values()), added_forms_lowered=lowered,
    )
    # LF line ends on every system, so that a rebuild on Windows leaves the committed files unchanged.
    (DATA / 'audit/stats.json').write_text(json.dumps(stats, ensure_ascii=False, indent=1) + '\n', encoding='utf-8',
                                           newline='\n')
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
