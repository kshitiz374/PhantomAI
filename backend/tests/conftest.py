import os
import uuid
from pathlib import Path

import pytest

# Unique DB directory per test run invocation; each test gets its own file.
os.environ.setdefault("PHANTOM_DATA_DIR", str(Path(__file__).parent / "tmp_data"))

from app.config import settings  # noqa: E402
from app.database import init_db  # noqa: E402


@pytest.fixture
async def db_session(monkeypatch):
    test_dir = settings.data_dir
    test_dir.mkdir(parents=True, exist_ok=True)
    db_path = test_dir / f"test_{uuid.uuid4().hex}.db"
    monkeypatch.setattr(settings, "db_filename", db_path.name)
    monkeypatch.setattr(settings, "data_dir", test_dir)

    await init_db()
    yield
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass
