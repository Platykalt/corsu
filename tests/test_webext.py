"""Checks of the Corsu web extension (src/webext): manifest, glossaries, adapters, and its Node tests."""
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

WEBEXT = Path(__file__).resolve().parent.parent / 'src/webext'
PLACEHOLDER = re.compile(r'\{([A-Za-z_]\w*)\}')
STATUSES = {'reviewed', 'draft', 'proposal'}


def glossaries():
    return {path.name: json.loads(path.read_text(encoding='utf-8')) for path in sorted(WEBEXT.glob('glossary/*.json'))}


def adapters():
    return {path.stem: path.read_text(encoding='utf-8') for path in sorted(WEBEXT.glob('adapters/*.js'))}


def selector_list(source, key):
    """The quoted strings of a multi-line `key: [ ... ],` list in an adapter file."""
    found = re.search(rf'^ *{key}: \[\n(.*?)^ *\],', source, re.S | re.M)
    if not found:
        return []
    return [text.replace('\\"', '"') for text in re.findall(r'"((?:[^"\\]|\\.)*)"', found.group(1))]


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((WEBEXT / 'manifest.json').read_text(encoding='utf-8'))

    def test_manifest_v3_with_minimal_permissions(self):
        manifest = self.manifest
        self.assertEqual(manifest['manifest_version'], 3)
        self.assertEqual(manifest['permissions'], ['storage'])
        for pattern in manifest['host_permissions']:
            self.assertRegex(pattern, r'^https://[a-z0-9.-]+/\*$', 'one exact host per pattern, https only')
        self.assertNotIn('optional_host_permissions', manifest)
        self.assertNotIn('web_accessible_resources', manifest, 'no extension file is exposed to pages')
        gecko = manifest['browser_specific_settings']['gecko']
        self.assertTrue(gecko['id'])
        self.assertEqual(gecko['data_collection_permissions'], {'required': ['none']})

    def test_referenced_files_exist(self):
        manifest = self.manifest
        files = [manifest['background']['service_worker'], *manifest['background']['scripts'],
                 manifest['options_ui']['page']]
        for script in manifest['content_scripts']:
            files += script['js']
            self.assertTrue(set(script['matches']) <= set(manifest['host_permissions']))
        for name in files:
            self.assertTrue((WEBEXT / name).is_file(), name)

    def test_every_adapter_host_is_in_the_manifest(self):
        matches = {pattern for script in self.manifest['content_scripts'] for pattern in script['matches']}
        for name, source in adapters().items():
            hosts = re.findall(r'"([^"]+)"', re.search(r'hosts: \[([^\]]*)\]', source).group(1))
            self.assertTrue(hosts, name)
            for host in hosts:
                self.assertIn(f'https://{host}/*', matches, name)


class GlossaryTests(unittest.TestCase):
    def test_entries_keep_their_placeholders(self):
        for name, glossary in glossaries().items():
            for entry in glossary['entries'] + glossary.get('exceptions', []):
                if entry.get('skip'):
                    continue
                with self.subTest(glossary=name, source=entry['source']):
                    self.assertEqual(sorted(PLACEHOLDER.findall(entry['source'])),
                                     sorted(PLACEHOLDER.findall(entry['co'])))
                    self.assertNotRegex(entry['co'], r'%[sd]|\$\{', 'only {name} placeholders')

    def test_entries_are_well_formed(self):
        for name, glossary in glossaries().items():
            seen = set()
            for entry in glossary['entries']:
                with self.subTest(glossary=name, source=entry['source']):
                    self.assertIn(entry['status'], STATUSES)
                    self.assertTrue(entry['co'].strip())
                    self.assertTrue(entry.get('origin'), 'say where the translation comes from')
                    self.assertLessEqual(len(entry['source']), 120)
                    key = (entry['source'], entry.get('within'))
                    self.assertNotIn(key, seen, 'duplicate entry')
                    seen.add(key)

    def test_site_glossary_size(self):
        self.assertTrue(60 <= len(glossaries()['github.json']['entries']) <= 120)

    def test_shared_glossary_is_generated_from_the_lexicon(self):
        result = subprocess.run([sys.executable, str(WEBEXT / 'tools/build_shared.py'), '--check'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class AdapterTests(unittest.TestCase):
    def test_adapters_declare_interface_and_excluded_zones(self):
        sources = adapters()
        self.assertTrue(sources)
        for name, source in sources.items():
            with self.subTest(adapter=name):
                ui, never = selector_list(source, 'ui'), selector_list(source, 'never')
                self.assertTrue(ui, 'interface zones')
                self.assertGreaterEqual(len(never), 5, 'user-content zones')
                self.assertNotIn('*', ui, 'no catch-all interface zone outside its own adapter rules')
                self.assertNotIn('body', ui)
                self.assertNotIn('html', ui)
                self.assertTrue((WEBEXT / re.search(r'glossary: "([^"]+)"', source).group(1)).is_file())

    def test_placeholder_attribute_only_on_search_fields(self):
        for name, source in adapters().items():
            attributes = re.search(r'attributes: \[([^\]]*)\]', source)
            self.assertTrue(attributes, name)
            self.assertNotIn('placeholder', attributes.group(1), name)


class NodeTests(unittest.TestCase):
    def test_engine_tests_pass_under_node(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('node is not installed')
        result = subprocess.run([node, '--test', str(WEBEXT / 'test/engine.test.js')], capture_output=True, text=True,
                                timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout[-4000:] + result.stderr[-2000:])


if __name__ == '__main__':
    unittest.main()
