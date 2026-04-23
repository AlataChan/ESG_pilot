import importlib
import sys

import pytest


@pytest.fixture
def fresh_config(monkeypatch):
    for var in ("ENV_STATE", "SECRET_KEY"):
        monkeypatch.delenv(var, raising=False)

    # Import the module under a safe local env so the module-level settings
    # singleton can be created without depending on ambient CI variables.
    monkeypatch.setenv("ENV_STATE", "local")
    sys.modules.pop("app.core.config", None)
    core_pkg = importlib.import_module("app.core")
    if hasattr(core_pkg, "config"):
        delattr(core_pkg, "config")
    return importlib.import_module("app.core.config")


def test_prod_default_secret_raises(fresh_config, monkeypatch):
    monkeypatch.delenv("ENV_STATE", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValueError):
        fresh_config.Settings(
            ENV_STATE="docker",
            SECRET_KEY=fresh_config.DEFAULT_SECRET_KEY,
        )


def test_local_default_secret_ok(fresh_config, monkeypatch):
    monkeypatch.delenv("ENV_STATE", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    settings = fresh_config.Settings(
        ENV_STATE="local",
        SECRET_KEY=fresh_config.DEFAULT_SECRET_KEY,
    )

    assert settings.ENV_STATE == "local"


def test_prod_custom_secret_ok(fresh_config, monkeypatch):
    monkeypatch.delenv("ENV_STATE", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    settings = fresh_config.Settings(ENV_STATE="docker", SECRET_KEY="x" * 32)

    assert settings.SECRET_KEY == "x" * 32


def test_unknown_env_state_fails_closed(fresh_config, monkeypatch):
    monkeypatch.delenv("ENV_STATE", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValueError):
        fresh_config.Settings(
            ENV_STATE="staging",
            SECRET_KEY=fresh_config.DEFAULT_SECRET_KEY,
        )


def test_unset_env_state_fails_closed(fresh_config, monkeypatch):
    monkeypatch.delenv("ENV_STATE", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValueError):
        fresh_config.Settings(
            _env_file=None,
            SECRET_KEY=fresh_config.DEFAULT_SECRET_KEY,
        )
