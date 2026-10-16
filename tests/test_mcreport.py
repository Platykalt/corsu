"""tools/mcreport.py: Minecraft pages generated from the committed data, and the freshness of each release's check."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('mcreport', ROOT / 'tools/mcreport.py')
mcreport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcreport)
packs = mcreport.packs

DATA_FILES = ('versions.json', 'keys.tsv', 'co_fr.json', 'history.json', 'LICENSE.txt', 'VERSION', 'history-report.md',
              'other-versions.md', 'inventory.tsv', 'STATUS.md')
PAGES = ('README.md', 'docs/fr/minecraft.md', 'docs/en/minecraft.md', '.github/RELEASE_NOTES.md')


def copy_tree():
    """A repository root holding only what mcreport reads and writes."""
    root = Path(tempfile.mkdtemp())
    for name in DATA_FILES:
        target = root / mcreport.DATA / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / mcreport.DATA / name, target)
    for name in PAGES:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return root


def run(*arguments):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = mcreport.main(list(arguments))
    return code, output.getvalue()


class Report(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = mcreport.facts(ROOT)
        cls.data = packs.Data(ROOT / mcreport.DATA).load()

    def test_counts_equal_the_data(self):
        data, f = self.data, self.facts
        self.assertEqual([row['version'] for row in f['rows']], data.order)
        empty = packs.digest('')
        for row in f['rows']:
            pairs = [(key, sha) for key, sha in data.pairs(row['version']) if sha != empty]
            translated = sum(1 for key, sha in pairs if (data.resolve(key, sha) or '').strip())
            self.assertEqual((row['translated'], row['total']), (translated, len(pairs)), row['version'])
            self.assertEqual(sum(row['origin'].values()), translated, row['version'])
            # versions.json's coverage also counts the keys whose English is empty.
            coverage = data.versions[row['version']]['coverage']
            empties = sum(1 for _, sha in data.pairs(row['version']) if sha == empty)
            self.assertEqual(coverage['total'] - empties, row['total'], row['version'])
        kinds = {}
        for by_hash in data.history.values():
            for entry in by_hash.values():
                kinds[entry['kind']] = kinds.get(entry['kind'], 0) + 1
        self.assertEqual(f['kinds'], {kind: kinds.get(kind, 0) for kind in mcreport.KINDS})
        self.assertEqual(f['history'], sum(kinds.values()))
        self.assertEqual(f['base_texts'], sum(1 for key, text in data.translation.items()
                                              if text.strip() and key in data.base_hash))

    def test_pages_show_those_counts(self):
        f = self.facts
        pages, _ = mcreport.outputs(ROOT, f)
        table = [line for line in pages['minecraft/java/COMPATIBILITY.md'].splitlines()
                 if re.match(r'\| \d+\.\d', line)]
        self.assertEqual(len(table), len(f['rows']))
        for line, row in zip(table, f['rows']):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            self.assertEqual(cells[0], row['version'])
            self.assertEqual(cells[2], f'{row["translated"]:,} / {row["total"]:,}')
        ok, first, last = len(f['ok']), f['ok'][0]['version'], f['ok'][-1]['version']
        self.assertIn(f'**Minecraft Java en corse pour {ok} versions** (versions stables {first} → {last})',
                      pages['docs/fr/minecraft.md'])
        self.assertIn(f'**Minecraft: Java Edition in Corsican for {ok} versions** (releases {first} → {last})',
                      pages['docs/en/minecraft.md'])
        # The sampled second pass is never presented as a review of everything.
        self.assertIn(f'sample of {f["sample"]} entries', pages['minecraft/java/COMPATIBILITY.md'])
        self.assertNotIn('all reviewed', pages['minecraft/java/COMPATIBILITY.md'])

    def test_generation_is_deterministic_and_leaves_the_rest_alone(self):
        root = copy_tree()
        self.assertEqual(run('--root', str(root))[0], 0)
        names = list(mcreport.outputs(root, self.facts)[0])
        first = {name: (root / name).read_bytes() for name in names}
        self.assertEqual(run('--root', str(root))[0], 0)
        second = {name: (root / name).read_bytes() for name in names}
        self.assertEqual(first, second)
        self.assertEqual(run('--check', '--root', str(root))[0], 0)
        # Outside the markers, README.md is the committed one.
        outside = re.compile(re.escape(mcreport.SUMMARY[0]) + '.*?' + re.escape(mcreport.SUMMARY[1]), re.S)
        self.assertEqual(outside.sub('', (root / 'README.md').read_text(encoding='utf-8')),
                         outside.sub('', (ROOT / 'README.md').read_text(encoding='utf-8')))

    def test_check_detects_a_stale_page(self):
        root = copy_tree()
        run('--root', str(root))
        page = root / 'docs/en/minecraft.md'
        page.write_text(page.read_text(encoding='utf-8').replace('for 87 versions', 'for 88 versions'),
                        encoding='utf-8')
        code, output = run('--check', '--root', str(root))
        self.assertEqual(code, 1)
        self.assertIn('docs/en/minecraft.md: differs from the data', output)

    def test_check_detects_a_changed_fingerprint(self):
        root = copy_tree()
        run('--root', str(root))
        # A text of 26.3 changes after the check: the 26.3 pack is no longer the one verified.
        path = root / mcreport.DATA / 'co_fr.json'
        texts = json.loads(path.read_text(encoding='utf-8'))
        texts['gui.done'] += ' !'
        path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        run('--root', str(root))
        code, output = run('--check', '--root', str(root))
        self.assertEqual(code, 1)
        self.assertIn('Minecraft 26.3: check to redo', output)
        compatibility = (root / mcreport.DATA / 'COMPATIBILITY.md').read_text(encoding='utf-8')
        self.assertRegex(compatibility, r'\| 26\.3 \|[^\n]*\*\*check to redo\*\*')
        # The headline counts only releases whose check matches the data.
        self.assertNotIn('for 87 versions', compatibility)

    def test_check_detects_a_recorded_fingerprint_that_differs(self):
        root = copy_tree()
        path = root / mcreport.DATA / 'versions.json'
        versions = json.loads(path.read_text(encoding='utf-8'))
        versions['1.12.2']['verified']['fingerprint'] = 'sha256:' + '0' * 64
        path.write_text(json.dumps(versions, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        run('--root', str(root))
        code, output = run('--check', '--root', str(root))
        self.assertEqual(code, 1)
        self.assertIn('Minecraft 1.12.2: check to redo', output)
        self.assertNotIn('Minecraft 1.12.1', output)

    def test_release_notes_block_only_between_markers(self):
        root = copy_tree()
        notes = root / '.github/RELEASE_NOTES.md'
        before = notes.read_text(encoding='utf-8')
        run('--root', str(root))
        self.assertEqual(notes.read_text(encoding='utf-8'), before)  # no markers: left as is
        marked = before.replace('### Nouveautés de la 0.22.0\n', '### Nouveautés\n\n' + '\n'.join(mcreport.SUMMARY)
                                + '\n').replace('### New in 0.22.0\n', '### New\n\n' + '\n'.join(mcreport.SUMMARY)
                                                + '\n')
        notes.write_text(marked, encoding='utf-8')
        run('--root', str(root))
        text = notes.read_text(encoding='utf-8')
        self.assertIn('Cette version de Corsu contient ces packs', text)
        self.assertIn('This Corsu release contains these packs', text)
        self.assertIn('https://github.com/Platykalt/corsu/blob/main/minecraft/java/COMPATIBILITY.md', text)
        self.assertEqual(run('--check', '--root', str(root))[0], 0)

    def test_fingerprint_is_the_language_file_and_mcmeta(self):
        data = self.data
        entry = data.versions['26.3']
        payload, _ = packs.build_pack('26.3', data)
        fingerprint = mcreport.mcversions.fingerprint(payload, entry)
        self.assertEqual(fingerprint, entry['verified']['fingerprint'])
        self.assertRegex(fingerprint, r'^sha256:[0-9a-f]{64}$')
        other = dict(entry, pack_format=entry['pack_format'] + 1)
        language = zipfile.ZipFile(io.BytesIO(payload)).read(entry['lang_file'])
        changed = packs.zip_bytes([('pack.mcmeta', packs.mcmeta(other, '26.3')), (entry['lang_file'], language)])
        self.assertNotEqual(mcreport.mcversions.fingerprint(changed, entry), fingerprint)


if __name__ == '__main__':
    unittest.main()
