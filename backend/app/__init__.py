# app package
import sys
from pathlib import Path

# The ML, RAG and safety packages live at the repository root (ml/, rag/, safety/)
# and never import the backend. Make them importable when the backend runs from
# backend/ (uvicorn, pytest, alembic). In Docker, PYTHONPATH already covers this.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))
