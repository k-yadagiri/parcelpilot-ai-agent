import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.build_db import build_database


@pytest.fixture(scope="session", autouse=True)
def _ensure_db():
    build_database(force=True)
    yield
    build_database(force=True)  # leave a clean DB behind for manual app use
