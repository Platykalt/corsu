"""Unit tests. The modules under test live in src/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
import os
os.environ.setdefault('CORSU_LANG', 'en')
