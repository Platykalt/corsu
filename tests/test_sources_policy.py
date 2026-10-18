"""Source policy: no program in Corsu queries INFCOR.

INFCOR (ADECEC's Corsican dictionary) is an interactive application with no stated licence and no per-entry address;
it is consulted by hand, one entry at a time (docs/keyboard-sources.md). On 2026-10-18 an AI agent sent 219 scripted
requests to it during the Minecraft review (minecraft/java/review-2026-10/ROUND3.md); this test keeps any such code
out of the repository. It does not replace the rule: agents are told not to script queries in a scratch folder either.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
CODE = ('.py', '.js', '.mjs', '.ts', '.sh', '.ps1', '.java', '.cmd', '.bat')
ENDPOINT = re.compile(r'(infcor\.adecec\.net|adecec\.net/infcor)', re.I)


class SourcesPolicyTests(unittest.TestCase):
    def test_no_code_queries_infcor(self):
        offenders = []
        for path in ROOT.rglob('*'):
            if '.git' in path.parts or 'node_modules' in path.parts or path.suffix not in CODE or not path.is_file():
                continue
            if path == Path(__file__).resolve():
                continue
            if ENDPOINT.search(path.read_text(encoding='utf-8', errors='replace')):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [], 'INFCOR is consulted by hand only, never from code')


if __name__ == '__main__':
    unittest.main()
