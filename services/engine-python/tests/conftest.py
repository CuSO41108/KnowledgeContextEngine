from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[1]
service_root_str = str(SERVICE_ROOT)
if service_root_str not in sys.path:
    sys.path.insert(0, service_root_str)

TEST_DB_PATH = SERVICE_ROOT / ".pytest_cache" / "runtime-test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("KCE_RUNTIME_DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.db import Base, engine


@pytest.fixture(autouse=True)
def reset_runtime_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
