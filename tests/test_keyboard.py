"""The Keyman prediction packages: tools/build_keyboard.py, the three model projects and their metadata.

The engine itself is exercised by tests/e2e/check_keyboard.py (Keyman for Android's web engine, headless). Set
CORSU_TEST_KMC=1 to also compile the three packages here with the pinned Keyman Developer compiler (needs npx).
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
import zipfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'tests/fixtures/keyboard/data'
spec = importlib.util.spec_from_file_location('build_keyboard', ROOT / 'tools/build_keyboard.py')
build_keyboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_keyboard)
spec = importlib.util.spec_from_file_location('check_keyboard', ROOT / 'tests/e2e/check_keyboard.py')
check_keyboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_keyboard)

# Keyman Developer's naming rule for lexical models (developer/src/common/web/utils/src/source-filename-patterns.ts,
# MODEL_ID_PATTERN_PACKAGE): author.bcp47.uniq, lowercase letters, digits and underscores (and hyphens in the tag).
MODEL_ID = re.compile(r'^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_-]*\.[a-z_][a-z0-9_]*$')
HEADER = 'word\tweight\tvariant\tsource\tlicense\tstatus\n'


def model(model_id):
    return next(model for model in build_keyboard.MODELS if model.id == model_id)


class DataTests(unittest.TestCase):
    def test_default_is_shared_and_a_preference_lays_its_file_over_it(self):
        default = build_keyboard.model_words(model('platykalt.co.corsu'), FIXTURES)
        north = build_keyboard.model_words(model('platykalt.co.corsu_cismuntincu'), FIXTURES)
        south = build_keyboard.model_words(model('platykalt.co.corsu_pumuntincu'), FIXTURES)
        self.assertEqual((default['donne'], default['donni']), (25, 25))
        self.assertEqual((north['donne'], north['donni']), (50, 12))
        self.assertEqual((south['donne'], south['donni']), (12, 50))
        # Names keep their capital; a rejected row is left out; nothing else is added or removed.
        self.assertEqual(default['Corsica'], 40)
        self.assertNotIn('corsica', default)
        self.assertNotIn('zzzrifiutu', default)
        self.assertEqual(set(default), set(north))
        self.assertEqual(set(default), set(south))

    def test_malformed_files_are_refused(self):
        cases = {
            'word\tweight\n': 'header',
            HEADER + 'eccu\t12\tnordu\tx\tCC0-1.0\tattested\n': 'unknown variant',
            HEADER + 'eccu\tdodeci\tshared\tx\tCC0-1.0\tattested\n': 'positive whole weight',
            HEADER + 'eccu\t12\tshared\tx\tCC0-1.0\n': 'columns expected',
            HEADER + 'eccu\t12\tshared\tx\tCC0-1.0\tattested\neccu\t3\tshared\tx\tCC0-1.0\tattested\n': 'twice',
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'shared.tsv'
            for content, message in cases.items():
                path.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(SystemExit, message):
                    build_keyboard.read_data(path)

    def test_typographic_apostrophe_is_normalised(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'shared.tsv'
            path.write_text(HEADER + 'l’isula\t7\tshared\tx\tCC0-1.0\tattested\n', encoding='utf-8')
            self.assertEqual(build_keyboard.read_data(path), {"l'isula": 7})

    def test_committed_word_lists_match_the_data(self):
        for entry in build_keyboard.MODELS:
            words = build_keyboard.model_words(entry, build_keyboard.DATA)
            lines = entry.wordlist().read_text(encoding='utf-8').splitlines()
            self.assertTrue(lines[0].startswith('#'))
            listed = dict(line.split('\t') for line in lines[1:])
            self.assertEqual({word: int(weight) for word, weight in listed.items()}, words,
                             f'{entry.id}: run tools/build_keyboard.py')


class ProjectTests(unittest.TestCase):
    def test_models_and_packages(self):
        self.assertEqual([entry.package for entry in build_keyboard.MODELS],
                         ['corsu-keyboard.kmp', 'corsu-keyboard-cismuntincu.kmp', 'corsu-keyboard-pumuntincu.kmp'])
        versions = set()
        for entry in build_keyboard.MODELS:
            self.assertRegex(entry.id, MODEL_ID)
            # Keyman for Android takes the package id from the file name and strips "-1" or " (1)" at its end.
            self.assertNotRegex(entry.package, r'(-\d+|\(\d+\))\.kmp$')
            project = entry.project()
            self.assertTrue((project / f'{entry.id}.kpj').exists())
            source = (project / f'source/{entry.id}.model.ts').read_text(encoding='utf-8')
            self.assertIn('languageUsesCasing: true', source)
            self.assertIn("wordBreaker: 'default'", source)
            self.assertIn("sources: ['wordlist.tsv']", source)
            package = ElementTree.parse(project / f'source/{entry.id}.model.kps').getroot()
            self.assertEqual(package.findtext('Info/Name'), entry.name)
            versions.add(package.findtext('Info/Version'))
            lexical = package.find('LexicalModels/LexicalModel')
            self.assertEqual((lexical.findtext('ID'), lexical.findtext('Name')), (entry.id, entry.name))
            self.assertEqual([language.get('ID') for language in lexical.findall('Languages/Language')], ['co'])
            for name in (file.findtext('Name') for file in package.findall('Files/File')):
                if not name.startswith('..\\build\\'):
                    self.assertTrue((project / 'source' / name.replace('\\', '/')).exists(), name)
            self.assertEqual(package.findtext('Options/LicenseFile').replace('\\', '/').split('/')[-1], 'LICENSE.md')
        self.assertEqual(len(versions), 1, versions)
        self.assertIn('(experimental)', model('platykalt.co.corsu_pumuntincu').name)

    def test_readable_model_name_is_written_into_the_package(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'corsu-keyboard.kmp'
            metadata = {'info': {'name': {'description': 'Corsu'}},
                        'lexicalModels': [{'name': 'platykalt.co.corsu', 'id': 'platykalt.co.corsu',
                                           'languages': [{'name': 'Corsican', 'id': 'co'}]}]}
            with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('platykalt.co.corsu.model.js', 'model')
                archive.writestr('kmp.json', json.dumps(metadata))
            build_keyboard.name_models(package, {'platykalt.co.corsu': 'Corsu'})
            with zipfile.ZipFile(package) as archive:
                self.assertEqual(archive.namelist(), ['platykalt.co.corsu.model.js', 'kmp.json'])
                self.assertEqual(archive.read('platykalt.co.corsu.model.js'), b'model')
                written = json.loads(archive.read('kmp.json'))
        metadata['lexicalModels'][0]['name'] = 'Corsu'
        self.assertEqual(written, metadata)


class WholeWordTests(unittest.TestCase):
    """keyboard/whole-word.js wraps the compiled model; its behaviour is checked in the engine (check_keyboard.py)."""
    CODE = ("(function() {\n'use strict';\nvar definitions = {};\n"
            "LMLayerWorker.loadModel(new models.TrieModel({\"root\":{}}, {\n  languageUsesCasing: true,\n}));\n})();")

    def test_the_trie_model_is_wrapped(self):
        code = build_keyboard.wrap_model(self.CODE, 'function corsuWholeWord(model) { return model; }')
        self.assertIn('function corsuWholeWord(model) { return model; }\n'
                      'LMLayerWorker.loadModel(corsuWholeWord(new models.TrieModel({"root":{}}, {', code)
        self.assertTrue(code.endswith('  languageUsesCasing: true,\n})));\n})();\n'))

    def test_an_unknown_compiler_output_is_refused(self):
        for code in (self.CODE.replace('new models.TrieModel', 'new models.DummyModel'), self.CODE + '\n// more',
                     build_keyboard.wrap_model(self.CODE, 'function corsuWholeWord(m) { return m; }')):
            with self.assertRaisesRegex(SystemExit, 'shape'):
                build_keyboard.wrap_model(code, 'function corsuWholeWord(m) { return m; }')

    @unittest.skipUnless(shutil.which('node'), 'needs Node.js')
    def test_suggestions_mid_word_delete_the_rest_of_the_word_on_android_only(self):
        script = (build_keyboard.WHOLE_WORD.read_text(encoding='utf-8') + r"""
const words = text => [...text.matchAll(/[\p{L}']+/gu)].map(m => ({start: m.index, end: m.index + m[0].length, text: m[0]}));
const model = () => ({ wordbreaker: words, predict: (transform, context) =>
  [{ sample: { transform: { insert: 'casa', deleteLeft: 2 }, displayAs: 'casa' }, p: 1 }] });
const run = (agent, left, right, transform) => {
  Object.defineProperty(globalThis, 'navigator', { value: { userAgent: agent }, configurable: true });
  return corsuWholeWord(model()).predict(transform || { insert: '', deleteLeft: 0 }, { left, right })[0].sample.transform;
};
console.log(JSON.stringify([
  run('Linux; Android 14', 'Eccu a ca', 'sa di Petru.'),
  run('Linux; Android 14', 'Eccu a ca', 'sa'),
  run('Linux; Android 14', 'Eccu a ca', 'sa.'),
  run('Linux; Android 14', 'Eccu a ca', ' di Petru.'),
  run('Linux; Android 14', 'Eccu a c', 'sa di', { insert: 'a', deleteLeft: 0 }),
  run('Linux; Android 14', 'Eccu a ', 'casa'),
  run('iPhone; CPU iPhone OS 17_6', 'Eccu a ca', 'sa di Petru.'),
]));
""")
        output = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout
        deletions = [change.get('deleteRight') for change in json.loads(output)]
        # rest of the word and its space; at the end of the text; before punctuation; caret at the end of a word;
        # a letter just typed mid-word; caret before a word (not inside it); Keyman for iPhone (ignores it).
        self.assertEqual(deletions, [3, 2, 2, None, 3, None, None])


class DataCaseTests(unittest.TestCase):
    """tests/e2e/keyboard_data_cases.tsv: the data-dependent expectations of the engine check."""
    HEAD = '\t'.join(check_keyboard.DATA_CASE_COLUMNS) + '\n'

    def load(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cases.tsv'
            path.write_text(content, encoding='utf-8')
            return check_keyboard.load_data_cases(path)

    def test_committed_file_loads(self):
        cases = check_keyboard.load_data_cases(ROOT / 'tests/e2e/keyboard_data_cases.tsv')
        models = {entry.id for entry in build_keyboard.MODELS}
        for case in cases:
            self.assertTrue(case['model'] == '*' or case['model'] in models, case)

    def test_rows_become_scenarios(self):
        cases = self.load('# comment\n' + self.HEAD
                          + '*\t3\tin\\s\tBastelicaccia\tspace\tin Bastelicaccia\\s\ttext\tfail\tname kept\n'
                          + 'platykalt.co.corsu_pumuntincu\t2\t\tzite\tnone\tziteddu\tfirst\twarn\tsouth\n')
        self.assertEqual((cases[0]['context'], cases[0]['expected']), ('in ', 'in Bastelicaccia '))
        models = ['platykalt.co.corsu', 'platykalt.co.corsu_pumuntincu']
        scenarios = check_keyboard.data_scenarios(cases, models)
        self.assertEqual([s['model'] for s in scenarios], models + ['platykalt.co.corsu_pumuntincu'])
        self.assertEqual(scenarios[0]['steps'], [{'setText': 'in '}, {'type': 'Bastelicaccia'}, {'key': 'K_SPACE'}])
        self.assertEqual(scenarios[2]['steps'], [{'type': 'zite'}])
        snap = lambda text, banner, tags: {'text': text, 'suggestions': banner, 'tags': tags}  # noqa: E731
        results = [
            {'name': scenarios[0]['name'], 'model': models[0], 'errors': [],
             'steps': [snap('', [], []), snap('in ', [], []), snap('in Bastelicaccia', [], []),
                       snap('in Bastilicaccia ', [], [])]},
            {'name': scenarios[1]['name'], 'model': models[1], 'errors': [],
             'steps': [snap('', [], []), snap('in ', [], []), snap('in Bastelicaccia', [], []),
                       snap('in Bastelicaccia ', [], [])]},
            {'name': scenarios[2]['name'], 'model': models[1], 'errors': [],
             'steps': [snap('', [], []), snap('zite', ['“zite”', 'zitellu', 'ziteddu'], ['keep', '', ''])]},
        ]
        failures, warnings = check_keyboard.data_checks(results, scenarios)
        self.assertEqual(len(failures), 1)
        self.assertIn("'in Bastilicaccia '", failures[0])
        self.assertEqual(len(warnings), 1)
        self.assertIn('zitellu', warnings[0])

    def test_malformed_rows_are_refused(self):
        for content, message in {
            'model\tsetting\n': 'header',
            self.HEAD + '*\t4\t\ta\tnone\ta\tfirst\tfail\tx\n': 'not allowed',
            self.HEAD + '*\t2\t\ta\tspace\ta\tfirst\tfail\tx\n': 'action must be none',
            self.HEAD + '*\t2\t\\q\ta\tnone\ta\tfirst\tfail\tx\n': 'escape',
            self.HEAD + '*\t2\t\ta\tnone\n': 'columns',
        }.items():
            with self.assertRaisesRegex(SystemExit, message):
                self.load(content)


@unittest.skipUnless(os.environ.get('CORSU_TEST_KMC') and shutil.which('npx'), 'set CORSU_TEST_KMC=1 (needs npx)')
class CompiledPackageTests(unittest.TestCase):
    def test_compiled_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            keyboard = Path(directory)
            for entry in build_keyboard.MODELS:
                shutil.copytree(entry.project(), keyboard / entry.id, ignore=shutil.ignore_patterns('build'))
            subprocess.run([sys.executable, str(ROOT / 'tools/build_keyboard.py'), '--package',
                            '--keyboard', str(keyboard)], check=True, capture_output=True)
            for entry in build_keyboard.MODELS:
                with zipfile.ZipFile(keyboard / 'build' / entry.package) as archive:
                    metadata = json.loads(archive.read('kmp.json'))
                    code = archive.read(f'{entry.id}.model.js').decode('utf-8')
                self.assertEqual(metadata['lexicalModels'],
                                 [{'name': entry.name, 'id': entry.id, 'languages': [{'name': 'Corsican', 'id': 'co'}]}])
                self.assertEqual(metadata['info']['name']['description'], entry.name)
                self.assertIn('languageUsesCasing: true', code)
                self.assertIn('applyCasing: function', code)
                self.assertIn('LMLayerWorker.loadModel(corsuWholeWord(new models.TrieModel(', code)
                self.assertTrue(code.endswith('})));\n})();\n'))


if __name__ == '__main__':
    unittest.main()
