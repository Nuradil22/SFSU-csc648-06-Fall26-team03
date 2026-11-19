"""Production startup validation for SECRET_KEY (app.config)."""
import pytest

from app.config import DEV_SECRET_KEY, Settings, ensure_production_secret


def _settings(environment="development", secret_key=DEV_SECRET_KEY):
    return Settings(environment=environment, secret_key=secret_key)


def test_development_allows_default_secret():
    ensure_production_secret(_settings())


def test_production_rejects_default_secret():
    with pytest.raises(RuntimeError):
        ensure_production_secret(_settings("production"))


def test_production_rejects_empty_secret():
    with pytest.raises(RuntimeError):
        ensure_production_secret(_settings("production", "  "))


def test_production_accepts_real_secret():
    ensure_production_secret(_settings("production", "some-long-random-value"))


def test_nonproduction_envs_allow_default_secret():
    for env in ("development", "test", "staging", "local"):
        ensure_production_secret(_settings(env))
