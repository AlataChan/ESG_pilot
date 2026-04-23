import sys

import anyio
import httpx
import pytest


class SyncASGITestClient:
    """Synchronous test client backed by httpx ASGITransport."""

    def __init__(self, app, base_url: str = "http://testserver"):
        self.app = app
        self.base_url = base_url
        self._portal_cm = None
        self._portal = None
        self._lifespan = None
        self._client = None

    def __enter__(self):
        self._portal_cm = anyio.from_thread.start_blocking_portal()
        self._portal = self._portal_cm.__enter__()
        self._lifespan = self.app.router.lifespan_context(self.app)
        self._portal.call(self._lifespan.__aenter__)

        transport = httpx.ASGITransport(app=self.app)
        self._client = httpx.AsyncClient(transport=transport, base_url=self.base_url)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._client is not None:
                self._portal.call(self._client.aclose)
            if self._lifespan is not None:
                self._portal.call(self._lifespan.__aexit__, exc_type, exc, tb)
        finally:
            if self._portal_cm is not None:
                self._portal_cm.__exit__(exc_type, exc, tb)

    def request(self, method: str, url: str, **kwargs):
        return self._portal.call(lambda: self._client.request(method, url, **kwargs))

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)


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

    with SyncASGITestClient(app) as test_client:
        yield test_client

    _clear_app_modules()
