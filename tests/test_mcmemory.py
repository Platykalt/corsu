"""The Minecraft review decisions in the contextual memory (tools/mcmemory.py, lexicon/memory/minecraft-java.jsonl)."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
import engine  # noqa: E402

_spec = importlib.util.spec_from_file_location('mcmemory', ROOT / 'tools/mcmemory.py')
mcmemory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mcmemory)
MEMORY = ROOT / 'lexicon/memory/minecraft-java.jsonl'


class MinecraftMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = list(engine.read_memory(MEMORY))
        cls.co = json.loads((ROOT / 'minecraft/java/co_fr.json').read_text(encoding='utf-8'))
        cls.history = json.loads((ROOT / 'minecraft/java/history.json').read_text(encoding='utf-8'))

    def test_committed_file_is_up_to_date(self):
        text, _ = mcmemory.render()
        self.assertEqual(MEMORY.read_text(encoding='utf-8'), text, 'run python3 tools/mcmemory.py')

    def test_entries_follow_the_pack_and_keep_validation_levels_apart(self):
        for entry in self.entries:
            key = entry['key']
            if '@' in key:
                name, digest = key.split('@', 1)
                current = self.history[name][digest]['co']
            else:
                current = self.co[key]
            self.assertEqual(entry['target'], current, key)
            self.assertEqual(entry['reuse'], 'same-app', key)
            self.assertEqual(entry['validation']['human'], 'none', key)
            self.assertTrue(entry['validation']['ai_proposal'] and entry['validation']['ai_review'], key)
            # Mojang's English is not stored: only its hash.
            self.assertEqual(entry['source'], '', key)
            self.assertRegex(entry['source_hash'] or '', r'^[0-9a-f]{12}$', key)

    def test_rail_decision_records_its_sources(self):
        rail = next(entry for entry in self.entries if entry['key'] == 'block.minecraft.rail')
        self.assertEqual(rail['target'], 'Ragliu')
        references = rail['decision']['round3']['references']
        self.assertIn('chaudronnerie', references)
        self.assertIn('printed page 101', references)

    def test_minecraft_decisions_never_answer_for_another_program(self):
        for text in ('Rail', 'Sign', 'Cake', 'Dandelion', 'Thunder roars'):
            self.assertNotIn(engine.lookup(text), ('Ragliu', 'Cartella', 'Pastadolce', 'Radichju', 'Tonu rimbomba'))


if __name__ == '__main__':
    unittest.main()
