import importlib

import pytest

from envotate.exceptions import EnvTypeError, EnvValueError


@pytest.fixture()
def app_settings(pytester):
    def inner():
        return importlib.import_module("tests.testapp.settings")

    return inner


@pytest.fixture(autouse=True)
def default_environ_for_module(monkeypatch):
    monkeypatch.setenv("APP_ID", "12345")
    monkeypatch.setenv("APP_NAME", "envotate")
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PY_VERSION", "py39")
    monkeypatch.setenv("BASE_URL", "https://github.com/jordaneremieff/")


def test_populate_variables_for_module(app_settings):
    settings = app_settings()
    assert settings.APP_ID == 12345
    assert settings.APP_NAME == "envotate"
    assert settings.APP_ENV == "dev"
    assert settings.DEBUG is True
    assert settings.PY_VERSION == "py39"
    assert settings.BASE_URL == "https://github.com/jordaneremieff/"
    assert settings.PUBLIC_URL == f"{settings.BASE_URL}{settings.APP_NAME}"


def test_module_is_missing_a_required_value(monkeypatch, app_settings):
    monkeypatch.delenv("APP_ID", raising=False)
    with pytest.raises(EnvValueError) as excinfo:
        app_settings()
    assert excinfo.match("APP_ID")


def test_module_contains_unknown_boolean_string(monkeypatch, app_settings):
    monkeypatch.setenv("DEBUG", "unknown")
    with pytest.raises(EnvValueError) as excinfo:
        app_settings()
    assert excinfo.match("DEBUG")


def test_module_contains_invalid_value_for_type(monkeypatch, app_settings):
    monkeypatch.setenv("APP_ID", "0.4.0")
    with pytest.raises(EnvTypeError) as excinfo:
        app_settings()
    assert excinfo.match("APP_ID")
