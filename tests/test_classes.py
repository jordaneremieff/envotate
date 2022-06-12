from typing import Literal, Optional, Union

import pytest

from envotate.env import BOOLEAN_FALSE_VALUES, BOOLEAN_TRUE_VALUES, env, Env
from envotate.exceptions import EnvValueError
from envotate.types import Default


class Database:
    USER: str = "postgres"
    PASSWORD: str = "password"
    HOST: str = "localhost"
    PORT: int = 5432
    NAME: str = "local_db"


class Base:
    APP_VERSION: Env[str, Default("0.0.1")]
    DEBUG: Env[bool, Default(False)]
    DATABASE = Database


def test_populate_class_from_default_values():
    @env
    class Conf(Base):
        APP_ENV: str = "local"

    assert Conf.APP_ENV == "local"
    assert Conf.DEBUG is False
    assert Conf.DATABASE is Database
    assert Conf.DATABASE.USER == "postgres"
    assert Conf.DATABASE.PASSWORD == "password"
    assert Conf.DATABASE.HOST == "localhost"
    assert Conf.DATABASE.PORT == 5432
    assert Conf.DATABASE.NAME == "local_db"


def test_populate_class_with_nested_env_class(monkeypatch):
    monkeypatch.setenv("DB_USER", "admin")
    monkeypatch.setenv("DB_PASSWORD", "password123")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "mydb")

    @env
    class DB:
        DB_USER: str
        DB_PASSWORD: str
        DB_HOST: str
        DB_PORT: int
        DB_NAME: str

    @env
    class Conf:
        APP_ENV: str = "local"
        DATABASE: DB

    assert Conf.APP_ENV == "local"
    assert Conf.DATABASE is DB
    assert Conf.DATABASE.DB_USER == "admin"
    assert Conf.DATABASE.DB_PASSWORD == "password123"
    assert Conf.DATABASE.DB_HOST == "127.0.0.1"
    assert Conf.DATABASE.DB_PORT == 5433
    assert Conf.DATABASE.DB_NAME == "mydb"


def test_replace_base_and_nested_annotations(monkeypatch):

    env_user = "admin"
    env_port = "5433"
    default_host = "127.0.0.1"
    monkeypatch.setenv("USER", env_user)
    monkeypatch.setenv("PORT", env_port)

    @env
    class ModifyDB(Database):
        HOST: str = default_host
        USER: str

    @env
    class Modify(Base):
        DEBUG: bool = True
        APP_VERSION: str = "0.0.1"
        DATABASE = ModifyDB

    assert Modify.DEBUG is True
    assert Modify.DATABASE is ModifyDB
    assert Modify.DATABASE.USER == ModifyDB.USER == env_user
    assert Modify.DATABASE.HOST == ModifyDB.HOST == default_host
    assert Modify.DATABASE.PASSWORD == Database.PASSWORD == "password"
    assert Modify.DATABASE.PORT == int(env_port)
    assert Modify.DATABASE.NAME == Database.NAME == "local_db"


@pytest.mark.parametrize(
    "known_string, expected_value",
    [(i, True) for i in BOOLEAN_TRUE_VALUES]  # type: ignore
    + [(i, False) for i in BOOLEAN_FALSE_VALUES],
)
def test_cast_to_bool_for_known_boolean_strings(
    monkeypatch, known_string, expected_value
):
    monkeypatch.setenv("DEBUG", known_string)

    @env
    class Conf:
        DEBUG: bool

    assert Conf.DEBUG is expected_value


@pytest.mark.parametrize(
    "unknown_string",
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
def test_raise_value_error_for_unknown_boolean_strings(monkeypatch, unknown_string):
    monkeypatch.setenv("DEBUG", unknown_string)

    with pytest.raises(EnvValueError) as excinfo:

        @env
        class Conf:
            DEBUG: bool

    assert excinfo.match("DEBUG")


def test_unsupported_origin_types(caplog):
    @env
    class Conf:
        APP_NAME: Optional[str]
        APP_VERSION: Literal["0.1.0"]
        PY_VERSION: Union[Literal["3.10"], Literal["3.9"]]

    with pytest.raises(AttributeError) as excinfo:
        Conf.APP_NAME
    assert excinfo.match("APP_NAME")

    with pytest.raises(AttributeError) as excinfo:
        Conf.APP_VERSION
    assert excinfo.match("APP_VERSION")

    with pytest.raises(AttributeError) as excinfo:
        Conf.PY_VERSION
    assert excinfo.match("PY_VERSION")
