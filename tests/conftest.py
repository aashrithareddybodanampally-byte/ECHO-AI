import sys
from pathlib import Path

# Make ml/, rag/ and safety/ importable when running `pytest tests` from the repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
