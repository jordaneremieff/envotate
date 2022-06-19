# type: ignore
# flake8: noqa
from __future__ import annotations

import sys
from typing import Literal, Optional, Union

import pytest

from envotate import FALSEY_VARS, TRUTHY_VARS, envotate
from envotate.exceptions import EnvTypeError, EnvValueError


class Database:
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "local_db"


class Settings:
    APP_ID: int
    APP_ENV: str = "local"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    DATABASE: Database


@pytest.fixture(autouse=True)
def default_test_settings_environ(monkeypatch):
    monkeypatch.setenv("APP_ID", "2")
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "local_db")


@pytest.fixture()
def patch_module_for_class(monkeypatch):
    """Patch the module namespace to include any nested annotated classes defined in the
    body of a test function for the duration of a particular test.

    This is to avoid a 'NameError' when 'get_type_hints()' attempts to evaluate these
    annotations in tests, but not intended to represent a recommended pattern.
    """

    def inner(cls):
        monkeypatch.setitem(sys.modules[cls.__module__].__dict__, cls.__name__, cls)

    return inner


def test_populate_from_environment():
    @envotate
    class TestSettings(Settings):
        APP_VERSION: str = "0.2.0"
        CALLABLE: str = lambda: "callable"
        DATABASE: Database

    assert TestSettings.APP_ENV == "dev"
    assert TestSettings.CALLABLE == "callable"
    assert TestSettings.DEBUG is True
    assert TestSettings.DATABASE is Database
    assert TestSettings.DATABASE.DB_USER == "postgres"
    assert TestSettings.DATABASE.DB_PASSWORD == "password"
    assert TestSettings.DATABASE.DB_HOST == "localhost"
    assert TestSettings.DATABASE.DB_PORT == 5432
    assert TestSettings.DATABASE.DB_NAME == "local_db"


def test_populate_with_nested_configuration(patch_module_for_class):
    @envotate
    class DatabaseExtra(Database):
        DB_EXTRA: str = "extra"

    patch_module_for_class(DatabaseExtra)

    @envotate
    class TestSettings(Settings):
        APP_VERSION: str = "0.2.0"
        DATABASE: DatabaseExtra

    assert TestSettings.DATABASE is DatabaseExtra
    assert TestSettings.DATABASE.DB_USER == "postgres"
    assert TestSettings.DATABASE.DB_PASSWORD == "password"
    assert TestSettings.DATABASE.DB_HOST == "localhost"
    assert TestSettings.DATABASE.DB_PORT == 5432
    assert TestSettings.DATABASE.DB_NAME == "local_db"
    assert TestSettings.DATABASE.DB_EXTRA == "extra"


@pytest.mark.parametrize(
    "support_boolean_string, expected_boolean_constant",
    [(i, True) for i in TRUTHY_VARS] + [(i, False) for i in FALSEY_VARS],
)
def test_cast_to_bool_for_known_boolean_strings(
    monkeypatch, support_boolean_string, expected_boolean_constant
):
    monkeypatch.setenv("DEBUG", support_boolean_string)

    @envotate
    class TestSettings(Settings):
        DEBUG: bool

    assert TestSettings.DEBUG is expected_boolean_constant


@pytest.mark.parametrize(
    "unknown_boolean_string",
    [
        "tru",
        "ya",
        "yep",
        "-1",
        "falsed",
        "",
        "2",
    ],
)
def test_raise_value_error_for_unknown_boolean_strings(
    monkeypatch, unknown_boolean_string
):
    monkeypatch.setenv("DEBUG", unknown_boolean_string)

    with pytest.raises(EnvValueError) as excinfo:

        @envotate
        class TestSettings(Settings):
            DEBUG: bool

    assert excinfo.match("DEBUG")


def test_raise_type_error_for_invalid_value(monkeypatch):
    monkeypatch.setenv("INT", "1.1")
    monkeypatch.setenv("FLOAT", "string")
    with pytest.raises(EnvTypeError) as excinfo:

        @envotate
        class TestSettings(Settings):
            INT: int

    assert excinfo.match("INT")

    with pytest.raises(EnvTypeError) as excinfo:

        @envotate
        class TestSettings(Settings):
            FLOAT: float

    assert excinfo.match("FLOAT")

    # TODO: Test this using the special types.


def test_unsupported_origin_types():
    @envotate
    class TestSettings:
        APP_NAME: Optional[str]
        APP_VERSION: Literal["0.1.0"]
        PY_VERSION: Union[Literal["3.10"], Literal["3.9"]]

    with pytest.raises(AttributeError) as excinfo:
        TestSettings.APP_NAME
    assert excinfo.match("APP_NAME")

    with pytest.raises(AttributeError) as excinfo:
        TestSettings.APP_VERSION
    assert excinfo.match("APP_VERSION")

    with pytest.raises(AttributeError) as excinfo:
        TestSettings.PY_VERSION
    assert excinfo.match("PY_VERSION")


def test_export_all_attributes_to_module():
    from tests.testapp import settings

    ExportAll = envotate(export={"__all__"})(settings.Settings)

    from tests.testapp.settings import (
        NESTED_SETTINGS,
        SETTINGS_BOOL,
        SETTINGS_INT,
        SETTINGS_STR,
    )

    assert SETTINGS_INT == 1
    assert SETTINGS_STR == "settings"
    assert SETTINGS_BOOL is True
    assert NESTED_SETTINGS is settings.NestedSettings

    assert ExportAll.SETTINGS_INT == SETTINGS_INT
    assert ExportAll.SETTINGS_STR == SETTINGS_STR
    assert ExportAll.SETTINGS_BOOL is SETTINGS_BOOL
    assert ExportAll.NESTED_SETTINGS is NESTED_SETTINGS

    with pytest.raises(ImportError) as excinfo:
        from tests.testapp.settings import NESTED_INT
    assert excinfo.match("NESTED_INT")

    with pytest.raises(ImportError) as excinfo:
        from tests.testapp.settings import NESTED_STR
    assert excinfo.match("NESTED_STR")

    with pytest.raises(ImportError) as excinfo:
        from tests.testapp.settings import NESTED_BOOL
    assert excinfo.match("NESTED_BOOL")

    assert ExportAll.NESTED_SETTINGS.NESTED_INT == 2
    assert ExportAll.NESTED_SETTINGS.NESTED_STR == "nested"
    assert ExportAll.NESTED_SETTINGS.NESTED_BOOL is False
    assert ExportAll.NESTED_SETTINGS.method() == 123


def test_prefix_for_environment_variables(patch_module_for_class):
    @envotate(prefix="DB_")
    class DB:
        USER: str
        PASSWORD: str
        HOST: str
        PORT: int
        NAME: str

    patch_module_for_class(DB)

    @envotate
    class Settings:
        DEBUG: bool
        DATABASE: DB

    assert Settings.DEBUG is True
    assert Settings.DATABASE.USER == "postgres"
    assert Settings.DATABASE.PASSWORD == "password"
    assert Settings.DATABASE.HOST == "localhost"
    assert Settings.DATABASE.PORT == 5432
    assert Settings.DATABASE.NAME == "local_db"
