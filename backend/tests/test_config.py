import pytest


def test_prod_default_secret_raises():
    from app.core.config import DEFAULT_SECRET_KEY, Settings

    with pytest.raises(ValueError):
        Settings(ENV_STATE="docker", SECRET_KEY=DEFAULT_SECRET_KEY)


def test_local_default_secret_ok():
    from app.core.config import DEFAULT_SECRET_KEY, Settings

    settings = Settings(ENV_STATE="local", SECRET_KEY=DEFAULT_SECRET_KEY)

    assert settings.ENV_STATE == "local"


def test_prod_custom_secret_ok():
    from app.core.config import Settings

    settings = Settings(ENV_STATE="docker", SECRET_KEY="x" * 32)

    assert settings.SECRET_KEY == "x" * 32

