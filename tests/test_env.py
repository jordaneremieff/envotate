import os
from unittest import mock

import pytest

from envotate.env import env, Env
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


def test_populate_annotated_class():
    with mock.patch.dict(os.environ, {}):

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


def test_replace_base_and_nested_annotations():

    env_user = "admin"
    env_port = "5433"
    default_host = "127.0.0.1"

    with mock.patch.dict(os.environ, {"USER": env_user, "PORT": env_port}):

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
    "env_value,expected",
    [
        ("true", True),
        ("yes", True),
        ("y", True),
        ("1", True),
        ("1    ", True),
        ("TrUe", True),
        ("TRUE", True),
        ("", False),
        ("0", False),
        ("2", False),
        ("Yeah", False),
        ("truth", False),
    ],
)
def test_cast_strings_to_boolean(env_value, expected):
    with mock.patch.dict(os.environ, {"DEBUG": env_value}):

        @env
        class Conf:
            DEBUG: bool

        assert Conf.DEBUG == expected


# def test_env_without_class():
#     APP_ENV: str = env("APP_ENV")
