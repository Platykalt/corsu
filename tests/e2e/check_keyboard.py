#!/usr/bin/env python3
"""Run Corsu's Keyman packages in the real Keyman for Android web engine, headless, and check what a user sees.

Usage: check_keyboard.py [--keyman 18.0.254] [--chrome CHROME] [--log LOG.txt] PACKAGE.kmp [PACKAGE.kmp ...]
       check_keyboard.py --cases CASES.tsv ...  # data cases (default: tests/e2e/keyboard_data_cases.tsv)
       check_keyboard.py --observe PACKAGE.kmp   # only print the log (for an old package: no checks)

The official Keyman for Android APK of that version is downloaded from downloads.keyman.com (its MD5 checked
against the Keyman API), and its engine (assets/keyboard.html, keymanweb-webview.js, android-host.js) runs in
headless Chrome with the EuroLatin (SIL) keyboard the APK ships. tests/e2e/keyman/harness.mjs plays
tests/e2e/keyman/scenarios.json: real touch taps on the on-screen keys, suggestion taps through the banner, caret
moves sent the way the Android app sends them. Needs Node.js, npm (puppeteer-core is installed in the cache folder)
and a Chrome or chrome-headless-shell binary (--chrome or $CHROME).

What this shows and what it does not: the engine, the keyboard and the model are the ones a phone runs; the Android
app around them (its Java side, the text field, the system keyboard service) is a stand-in, so this is not a test
on a phone. The engine's suggestion settings are set the way the app's settings menu sets them (setting 2,
"Predictions with corrections", is Keyman 18's default and highest choice; setting 3 is auto-correction, offered
from Keyman 19).

Two kinds of expectations are checked. The behaviour of the models (case, sentence start, caret moves) is written
in checks() below against scenarios.json. What depends on the word data (a word offered first, a name kept by
auto-correction) is listed in tests/e2e/keyboard_data_cases.tsv, kept with the data; see DATA_CASES_HELP.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get('CORSU_KEYMAN_CACHE', Path.home() / '.cache/corsu-keyman-e2e'))
API = 'https://downloads.keyman.com/api/version/2.0'


def open_url(url, timeout):
    # downloads.keyman.com refuses Python's default user agent.
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'corsu-tests'}), timeout=timeout)


def fetch_engine(version):
    """The assets of the official Keyman for Android APK, and EuroLatin's compiled keyboard."""
    folder = CACHE / f'keyman-{version}'
    assets = folder / 'assets'
    if (assets / 'keyboard.html').exists():
        return assets, folder / 'sil_euro_latin.js'
    folder.mkdir(parents=True, exist_ok=True)
    with open_url(API, 60) as response:
        releases = json.load(response)['android']
    entry = next((files[f'keyman-{version}.apk'] for tier in releases.values()
                  if isinstance(tier, dict) and (files := tier.get('files', {})).get(f'keyman-{version}.apk')), None)
    tier = next((name for name, tier in releases.items() if isinstance(tier, dict) and tier.get('version') == version), None)
    if not entry or not tier:
        raise SystemExit(f'Keyman for Android {version} is not offered by {API}')
    apk = folder / f'keyman-{version}.apk'
    url = f'https://downloads.keyman.com/android/{tier}/{version}/keyman-{version}.apk'
    print(f'Downloading {url}', flush=True)
    with open_url(url, 300) as response, apk.open('wb') as target:
        shutil.copyfileobj(response, target)
    if hashlib.md5(apk.read_bytes()).hexdigest() != entry['md5'].lower():
        apk.unlink()
        raise SystemExit(f'{url}: MD5 does not match the Keyman API')
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if name.startswith('assets/') and not name.startswith(('assets/info/', 'assets/dexopt/')):
                archive.extract(name, folder)
    with zipfile.ZipFile(assets / 'sil_euro_latin.kmp') as package:
        (folder / 'sil_euro_latin.js').write_bytes(package.read('sil_euro_latin.js'))
    return assets, folder / 'sil_euro_latin.js'


def puppeteer():
    modules = CACHE / 'node/node_modules'
    if not (modules / 'puppeteer-core').exists():
        (CACHE / 'node').mkdir(parents=True, exist_ok=True)
        subprocess.run(['npm', 'install', '--prefix', str(CACHE / 'node'), '--no-save', '--silent',
                        'puppeteer-core@24.43.1'], check=True)
    return modules


def find_chrome(given):
    candidates = [given, os.environ.get('CHROME'), shutil.which('chrome-headless-shell'),
                  shutil.which('google-chrome'), shutil.which('chromium')]
    candidates += sorted(map(str, Path.home().glob('.cache/*/chrome*/**/chrome-headless-shell')), reverse=True)
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise SystemExit('No Chrome found: give --chrome or $CHROME.')


# The model each package must hold (tools/build_keyboard.py).
PACKAGE_MODELS = {'corsu-keyboard.kmp': 'platykalt.co.corsu',
                  'corsu-keyboard-cismuntincu.kmp': 'platykalt.co.corsu_cismuntincu',
                  'corsu-keyboard-pumuntincu.kmp': 'platykalt.co.corsu_pumuntincu'}


def models_of(packages, folder):
    """{model id: path of its .model.js} for every lexical model of the packages."""
    models = {}
    for package in packages:
        with zipfile.ZipFile(package) as archive:
            metadata = json.loads(archive.read('kmp.json'))
            for model in metadata['lexicalModels']:
                target = folder / f'{model["id"]}.model.js'
                target.write_bytes(archive.read(f'{model["id"]}.model.js'))
                models[model['id']] = target
    return models


def package_checks(packages, models, results):
    """Each package holds the one model its name says, wrapped by whole-word.js, and the engine loaded it."""
    failures = []
    for package in packages:
        with zipfile.ZipFile(package) as archive:
            ids = [model['id'] for model in json.loads(archive.read('kmp.json'))['lexicalModels']]
        expected = PACKAGE_MODELS.get(package.name)
        if expected and ids != [expected]:
            failures.append(f'{package.name} holds {ids}, expected [{expected!r}]')
    for model, path in models.items():
        if 'corsuWholeWord(new models.TrieModel(' not in path.read_text(encoding='utf-8'):
            failures.append(f'{model}: the model is not wrapped by keyboard/whole-word.js')
    for result in results:
        if result['model'] and result['setup'].get('state') != 'configured':
            failures.append(f'{result["model"]}: not loaded by the engine in {result["name"]!r} ({result["setup"]})')
    return failures


def log_lines(results):
    for result in results:
        yield (f'== {result["name"]} | model {result["model"]} | setting {result["setting"]} | '
               f'keyboard {result["setup"].get("keyboard")} | page errors {len(result["errors"])}')
        for error in result['errors']:
            yield f'   page error: {error}'
        for step in result['steps']:
            label = json.dumps(step['step'], ensure_ascii=False)
            if 'error' in step:
                yield f'   {label:34} ERROR {step["error"]}'
            else:
                yield (f'   {label:34} -> {step["text"]!r} caret={step["caret"]} layer={step["layer"]} '
                       f'auto={step["selected"]!r} banner={step["suggestions"][:6]}')


DATA_CASE_COLUMNS = ['model', 'setting', 'context', 'typed', 'action', 'expected', 'kind', 'severity', 'note']
DATA_CASES_HELP = """One case per line, tab-separated, UTF-8, header line first; lines starting with # are comments.

model     a model id (platykalt.co.corsu, platykalt.co.corsu_cismuntincu, platykalt.co.corsu_pumuntincu), or * for
          each model checked; a case for a model that is not checked is skipped
setting   2 (predictions with corrections, Keyman 18's highest) or 3 (auto-correction: Keyman 19; the 18.0 engine
          also applies it when asked, though the 18.0 app does not offer it)
context   text already in the field, the caret at its end (empty: an empty field, the start of a sentence)
typed     what is typed after it, key by key on EuroLatin (a space is a tap on the space bar)
action    space (tap the space bar: auto-correction acts here), accept=WORD (tap that suggestion in the banner), or
          none
expected  for kind text: the whole field after the action; for first, offers and absent: one word
kind      text: the field after the action is exactly expected;
          first: after typing, the banner's first suggestion (the quoted "keep what I typed" entry aside) is expected;
          offers: after typing, the banner holds expected; absent: after typing, the banner does not hold expected
severity  fail (the check fails) or warn (reported only)
note      why the case exists (free text)

In context, typed and expected, \\s is a space (so a trailing space survives editors), \\n a new line, \\t a tab and
\\\\ a backslash."""


def unescape(text):
    out, chars = [], iter(text)
    for char in chars:
        if char == '\\':
            char = {'s': ' ', 'n': '\n', 't': '\t', '\\': '\\'}.get(next(chars, ''), None)
            if char is None:
                raise ValueError('unknown escape')
        out.append(char)
    return ''.join(out)


def load_data_cases(path):
    """The rows of keyboard_data_cases.tsv, checked: a list of dicts (with their line number)."""
    if not path.exists():
        return []
    lines = path.read_text(encoding='utf-8').splitlines()
    rows = [(number, line) for number, line in enumerate(lines, start=1) if line.strip() and not line.startswith('#')]
    if not rows or rows[0][1].split('\t') != DATA_CASE_COLUMNS:
        raise SystemExit(f'{path}: the first line must be the header {chr(9).join(DATA_CASE_COLUMNS)!r}\n{DATA_CASES_HELP}')
    cases = []
    for number, line in rows[1:]:
        fields = line.split('\t')
        if len(fields) != len(DATA_CASE_COLUMNS):
            raise SystemExit(f'{path}:{number}: {len(DATA_CASE_COLUMNS)} tab-separated columns expected')
        case = dict(zip(DATA_CASE_COLUMNS, fields), line=number)
        try:
            for key in ('context', 'typed', 'expected'):
                case[key] = unescape(case[key])
        except ValueError:
            raise SystemExit(f'{path}:{number}: unknown backslash escape') from None
        action = case['action']
        if case['setting'] not in ('2', '3') or case['kind'] not in ('text', 'first', 'offers', 'absent') \
                or case['severity'] not in ('fail', 'warn') \
                or not (action in ('space', 'none') or action.startswith('accept=') and len(action) > 7) \
                or not case['expected'] or not (case['model'] == '*' or case['model'].startswith('platykalt.co.')):
            raise SystemExit(f'{path}:{number}: a value is not allowed here\n{DATA_CASES_HELP}')
        if case['kind'] != 'text' and action != 'none':
            raise SystemExit(f'{path}:{number}: kinds first, offers and absent read the banner: action must be none')
        cases.append(case)
    return cases


def data_scenarios(cases, models):
    """One harness scenario per case and model."""
    scenarios = []
    for case in cases:
        for model in (models if case['model'] == '*' else [m for m in models if m == case['model']]):
            steps = [{'setText': case['context']}] if case['context'] else []
            if case['typed']:
                steps.append({'type': case['typed']})
            if case['action'] == 'space':
                steps.append({'key': 'K_SPACE'})
            elif case['action'] != 'none':
                steps.append({'accept': case['action'][len('accept='):]})
            scenarios.append({'name': f'data case line {case["line"]}: {case["note"]}', 'setting': int(case['setting']),
                              'model': model, 'steps': steps, 'case': case})
    return scenarios


def data_checks(results, scenarios):
    """Failures and warnings of the data cases, from their runs."""
    failures, warnings = [], []
    cases = {(s['name'], s['model']): s['case'] for s in scenarios if 'case' in s}
    for result in results:
        case = cases.get((result['name'], result['model']))
        if not case:
            continue
        steps = result['steps']
        last = steps[-1]
        typed = steps[-2] if case['action'] != 'none' else last
        label = (f'{result["model"]}: data case line {case["line"]} ({case["note"]}): '
                 f'{case["context"] + case["typed"]!r} {case["action"]}')
        if any('error' in s for s in steps) or result['errors']:
            problem = '; '.join([s['error'] for s in steps if 'error' in s] + result['errors'])
            message = f'{label}: {problem}'
        elif case['kind'] == 'text':
            message = None if last['text'] == case['expected'] else \
                f'{label}: field {last["text"]!r}, expected {case["expected"]!r}'
        else:
            banner = [s for s, tag in zip(typed['suggestions'], typed.get('tags', [])) if tag != 'keep'] \
                if typed.get('tags') else typed['suggestions']
            ok = {'first': banner[:1] == [case['expected']], 'offers': case['expected'] in typed['suggestions'],
                  'absent': case['expected'] not in banner}[case['kind']]
            message = None if ok else f'{label}: banner {typed["suggestions"]}, expected {case["kind"]} {case["expected"]!r}'
        if message:
            (failures if case['severity'] == 'fail' else warnings).append(message)
    return failures, warnings


def step(results, scenario, model, index):
    result = next(r for r in results if r['name'].startswith(scenario) and r['model'] == model)
    return result['steps'][index]


def checks(results, models):
    """What the fixed packages must do; each check names the defect it guards."""
    failures, warnings = [], []

    def expect(condition, message, record=failures):
        if not condition:
            record.append(message)

    for model in models:
        s = lambda scenario, index: step(results, scenario, model, index)  # noqa: E731
        expect(all(not r['errors'] for r in results if r['model'] == model), f'{model}: page errors')
        expect(s('casing: suggestion taps', 2)['text'] == 'Eccu ', f'{model}: "Ecc" + tap on "Eccu" must keep the capital')
        expect(s('casing: suggestion taps', 4)['text'] == 'Eccu ECCU ', f'{model}: "ECC" + tap must give ECCU')
        expect(s('casing: lower, initial', 4)['text'] == 'eccu Eccu ', f'{model}: auto-correction lowered "Eccu"')
        expect(s('casing: lower, initial', 6)['text'] == 'eccu Eccu ECCU ', f'{model}: auto-correction lowered "ECCU"')
        expect(s('casing: a typo corrected', 2)['text'] == 'Lingua ', f'{model}: "Lingau" must become "Lingua"')
        expect(s('casing: a typo corrected', 6)['text'] == 'Lingua lingua LINGUA ', f'{model}: corrected case')
        expect(s('casing: proper nouns', 1)['suggestions'][:1] == ['Corsica'], f'{model}: "corsic" must offer "Corsica"')
        expect(s('casing: proper nouns', 4)['text'] == 'in Corsica Aiacciu ', f'{model}: a name tapped keeps its capital')
        expect(s('casing: proper nouns', 6)['text'] == 'in Corsica Aiacciu corsicaa ',
               f'{model}: without auto-correction, an unknown word stays as typed')
        # The text after each tap: the typed case is kept (initial, upper), a name keeps its capital mid-sentence,
        # a common word is not capitalised mid-sentence, and a tap before any letter follows the OSK's layer.
        taps = {3: 'Eccu. Perchè ', 6: 'Eccu. Lingua ', 9: "Eccu. L'isula ", 12: "Eccu. D'altri ", 15: 'Eccu. Ùn ',
                18: 'Disse: Aiacciu ', 21: 'Eccu a casa ', 23: 'Eccu, di ', 26: 'ECCU LINGUA ', 28: 'Eccu. Di ',
                30: 'Eccu?\nDi '}
        for index, text in taps.items():
            got = s('casing: taps at a sentence start', index)
            expect(got.get('text') == text, f'{model}: tap gave {got.get("text", got.get("error"))!r}, expected {text!r}')
        expect(s('sentence start: suggestion before', 0)['suggestions'][:1] == ['Di'],
               f'{model}: the first suggestion of a sentence must be capitalised')
        expect(s('sentence start: suggestion before', 1)['text'] == 'Di ', f'{model}: sentence-start suggestion tap')
        places = next(r for r in results if r['name'].startswith('places: Corsican') and r['model'] == model)
        expect(places['steps'][-1]['text'].startswith('in Zicavu Aiacciu Bastia Portivechju Corti Calvi Bunifaziu Sartè Bastilicaccia '),
               f'{model}: auto-correction changed a place name: {places["steps"][-1]["text"]!r}')
        for index, name in zip(range(2, 20, 2), ('Zicavu', 'Aiacciu', 'Bastia', 'Portivechju', 'Corti', 'Calvi', 'Bunifaziu', 'Sartè', 'Bastilicaccia')):
            expect(s('places: a lowercase prefix', index)['suggestions'][:1] == [name], f'{model}: prefix must offer {name}')
        if model != 'platykalt.co.corsu_pumuntincu':
            expect(s('ranking: parlle', 1)['suggestions'][:1] == ['parolle'], f'{model}: "parlle" must rank parolle first')
        expect(s('sentence start: field start', 2)['layer'] == 'shift', f'{model}: shift after ". "')
        expect(s('auto-correct off', 2)['text'] == 'lingau ', f'{model}: without auto-correction a typo must stay')
        # Auto-correction (setting 3) is the engine's: it may replace a word it does not know when the model offers
        # a single close candidate. Reported, not failed: the dictionary does not control it.
        for index in (8, 10, 12, 14, 18, 20, 22):
            typed = s('auto-correct on', index - 1)['text'].split(' ')[-1]
            expect(s('auto-correct on', index)['text'].endswith(typed + ' '),
                   f'{model}: auto-correction replaced the unknown word {typed!r}: '
                   f'{s("auto-correct on", index)["text"]!r}', warnings)
        sentence = 'Eccu a casa di Petru.'
        expect(s('return to a word: caret inside', 3)['text'] == sentence,
               f'{model}: moving the caret alone must not change the text')
        # A suggestion chosen with the caret inside a word replaces the whole word (keyboard/whole-word.js), and at
        # the end of a word replaces that word; no piece of the old word stays right of the caret.
        expect(s('return to a word: caret inside', 2)['text'] == sentence,
               f'{model}: "ca|sa" + "casa" gave {s("return to a word: caret inside", 2)["text"]!r}')
        expect(s('return to a word: caret inside', 4)['text'] == 'Eccu a casata di Petru.',
               f'{model}: "casa|" + "casata" gave {s("return to a word: caret inside", 4)["text"]!r}')
        for scenario, index in (('return to a word: selection replaced', 4), ('return to a word: delete the last', 4)):
            got = s(scenario, index).get('text')
            expect(got == sentence, f'{model}: {scenario!r} gave {got!r}')
        after = s('return to a word: after a full stop', 4).get('text')
        expect(after == 'Eccu a casa. Dopu ghjunghje', f'{model}: "Dop|u" + "Dopu" after a full stop gave {after!r}')
        guide = s("return to a word: the guide's example", 2)['text']
        expect(guide == 'Dopu ellu vene', f'{model}: "Dopu ell|a vene" + "ellu" gave {guide!r}')
        # Keyman for iPhone ignores deleteRight, so the model leaves suggestions as they are there: the engine's
        # own result, the end of the old word right of the caret.
        iphone = s('return to a word: iPhone user agent', 2)['text']
        expect(iphone == 'Dopu ellu a vene', f'{model}: with an iPhone user agent, {iphone!r}')
        # Known limits of the engine, reported when they change: a space is added before punctuation that follows
        # the word; undoing a mid-word choice does not bring back the end of the old word; a selected word gets the
        # suggestions of a sentence start, with a capital.
        limits = {2: 'Eccu Aiacciu .', 6: 'Eccu a cadi Petru.', 9: 'Eccu a Di di Petru.'}
        for index, text in limits.items():
            got = s('return to a word: known limits', index)
            expect(got.get('text') == text, f'{model}: known limit changed: {got.get("text", got.get("error"))!r} '
                   f'instead of {text!r} (step {index})', warnings)
    if {'platykalt.co.corsu_cismuntincu', 'platykalt.co.corsu_pumuntincu'} <= set(models):
        north = step(results, 'variants', 'platykalt.co.corsu_cismuntincu', 1)['suggestions']
        south = step(results, 'variants', 'platykalt.co.corsu_pumuntincu', 1)['suggestions']
        # Each preference ranks its own form first and still offers the other one.
        rank = lambda banner, word: banner.index(word) if word in banner else 99  # noqa: E731
        expect(rank(north, 'zitellu') < rank(north, 'ziteddu') < 99, f'Cismuntincu "zite": {north}')
        expect(rank(south, 'ziteddu') < rank(south, 'zitellu') < 99, f'Pumuntincu "zite": {south}')
    return failures, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('packages', nargs='+', type=Path)
    parser.add_argument('--keyman', default='18.0.254', help='Keyman for Android version (default: 18.0.254, stable)')
    parser.add_argument('--chrome')
    parser.add_argument('--scenarios', type=Path, default=HERE / 'keyman/scenarios.json')
    parser.add_argument('--log', type=Path, help='also write the readable log here')
    parser.add_argument('--cases', type=Path, default=HERE / 'keyboard_data_cases.tsv',
                        help='data-dependent cases (default: tests/e2e/keyboard_data_cases.tsv)')
    parser.add_argument('--observe', action='store_true', help='print what happens without checking it')
    args = parser.parse_args()
    assets, keyboard = fetch_engine(args.keyman)
    work = CACHE / 'run'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    models = models_of(args.packages, work)
    cases = load_data_cases(args.cases)
    scenarios = json.loads(args.scenarios.read_text(encoding='utf-8')) + data_scenarios(cases, list(models))
    (work / 'scenarios.json').write_text(json.dumps(scenarios, ensure_ascii=False), encoding='utf-8')
    command = ['node', str(HERE / 'keyman/harness.mjs'), '--assets', str(assets), '--keyboard', str(keyboard),
               '--chrome', find_chrome(args.chrome), '--scenarios', str(work / 'scenarios.json'),
               '--out', str(work / 'log.json')]
    for model, path in models.items():
        command += ['--model', f'{model}={path}']
    subprocess.run(command, check=True, env={**os.environ, 'NODE_PATH': str(puppeteer())})
    results = json.loads((work / 'log.json').read_text(encoding='utf-8'))
    lines = [f'Keyman for Android {args.keyman} engine, EuroLatin (SIL) from its APK; packages: '
             + ', '.join(f'{p.name} (sha256 {hashlib.sha256(p.read_bytes()).hexdigest()[:16]})' for p in args.packages),
             *log_lines(results)]
    print('\n'.join(lines))
    if args.log:
        args.log.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    if args.observe:
        return
    failures, warnings = checks(results, list(models))
    failures += package_checks(args.packages, models, results)
    for found, record in zip(data_checks(results, scenarios), (failures, warnings)):
        record.extend(found)
    for warning in warnings:
        print('WARNING:', warning)
    for failure in failures:
        print('FAIL:', failure)
    if failures:
        raise SystemExit(f'{len(failures)} keyboard check(s) failed')
    print(f'All keyboard checks passed for {", ".join(models)}.')


if __name__ == '__main__':
    main()
