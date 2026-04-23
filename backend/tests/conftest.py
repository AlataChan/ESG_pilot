import sys

import pytest
from fastapi.testclient import TestClient


def _clear_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("ENV_STATE", "test")
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_path))

    # The app caches settings and SessionLocal at import time, so clear app modules
    # before importing to force the test SQLite file into the module globals.
    _clear_app_modules()

    from app.main import app
    from app.db.session import create_tables

    create_tables()

    with TestClient(app) as test_client:
        yield test_client

    _clear_app_modules()

