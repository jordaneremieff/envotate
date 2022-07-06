# flake8: noqa
from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

import pytest

from envotate import envotate
from envotate.errors import VariableError
from envotate.types import (
    Choice,
    Directory,
    DjangoDSN,
    File,
    Function,
    Method,
    Regex,
    Split,
)
from envotate.typing import Context


def test_annotated_type_with_no_default():
    with pytest.raises(VariableError) as excinfo:

        @envotate
        class Undefined:
            APP_ENV: Annotated[str, Regex(r"^(prod|stag|dev)$")]

    assert excinfo.match("APP_ENV")


@pytest.mark.parametrize(
    "dsn,expected",
    [
        (
            "postgres://postgres:password@localhost:5432/local_db",
            {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "local_db",
                "USER": "postgres",
                "PASSWORD": "password",
                "HOST": "localhost",
                "PORT": 5432,
            },
        ),
        # (
        #     "postgresql://postgres:password@localhost:5432/local_db",
        #     {
        #         "ENGINE": "django.db.backends.postgresql",
        #         "NAME": "local_db",
        #         "USER": "postgres",
        #         "PASSWORD": "password",
        #         "HOST": "localhost",
        #         "PORT": 5432,
        #     },
        # ),
        # (
        #     "mysql://root:password@localhost:3306/local_db",
        #     {
        #         "ENGINE": "django.db.backends.mysql",
        #         "NAME": "local_db",
        #         "USER": "root",
        #         "PASSWORD": "password",
        #         "HOST": "localhost",
        #         "PORT": 3306,
        #     },
        # ),
        # (
        #     "sqlite:///db.sqlite3",
        #     {
        #         "ENGINE": "django.db.backends.sqlite3",
        #         "NAME": "db.sqlite3",
        #         "HOST": "",
        #         "PORT": "",
        #         "USER": "",
        #         "PASSWORD": "",
        #     },
        # ),
        # (
        #     "sqlite3:///db.sqlite3",
        #     {
        #         "ENGINE": "django.db.backends.sqlite3",
        #         "NAME": "db.sqlite3",
        #         "HOST": "",
        #         "PORT": "",
        #         "USER": "",
        #         "PASSWORD": "",
        #     },
        # ),
        # (
        #     "oracle://user:password@localhost:1521/local_db",
        #     {
        #         "ENGINE": "django.db.backends.oracle",
        #         "NAME": "local_db",
        #         "USER": "user",
        #         "PASSWORD": "password",
        #         "HOST": "localhost",
        #         "PORT": 1521,
        #     },
        # ),
    ],
)
def test_annotated_django_database_type(monkeypatch, export_to_module, dsn, expected):
    export_to_module(dsn, name="dsn", module=__name__)
    monkeypatch.setenv("DATABASE", dsn)

    @envotate
    class ValidForDjangoDatabase:
        DATABASE: Annotated[dict, DjangoDSN]

    expected.update(
        {
            "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {},
        }
    )

    assert ValidForDjangoDatabase.DATABASE == expected

    monkeypatch.setenv("DATABASE", "unknown://user:pass@host:5432/db")
    with pytest.raises(VariableError) as excinfo:

        @envotate
        class InvalidForDjangoDatabase:
            DATABASE: Annotated[dict, DjangoDSN]

    assert excinfo.match("'unknown'")


@pytest.mark.parametrize(
    "choices",
    [
        ["py39", "py310"],
        {"py39", "py310"},
    ],
)
def test_annotated_choice_type(monkeypatch, choices, export_to_module):
    monkeypatch.setenv("PY_VERSION", "py39")
    export_to_module(choices, name="choices", module=__name__)

    @envotate
    class ValidChoice:
        PY_VERSION: Annotated[str, Choice(choices)]

    assert ValidChoice.PY_VERSION == "py39"

    monkeypatch.setenv("PY_VERSION", "py38")
    with pytest.raises(VariableError) as excinfo:

        @envotate
        class InvalidChoice:
            PY_VERSION: Annotated[str, Choice(choices)]

    assert excinfo.match("is not a valid choice")


def test_annotated_split_type(monkeypatch, export_to_module):
    for delimiter in [",", ";", "|"]:
        ALLOWED_HOSTS = delimiter.join(
            ["localhost", "local.host", "0.0.0.0", "127.0.0.1"]
        )

        monkeypatch.setenv("ALLOWED_HOSTS", ALLOWED_HOSTS)
        export_to_module(ALLOWED_HOSTS, name="ALLOWED_HOSTS", module=__name__)
        export_to_module(delimiter, name="delimiter", module=__name__)

        @envotate
        class ValidForDelimiter:
            ALLOWED_HOSTS: Annotated[list[str], Split(delimiter)]

        assert ValidForDelimiter.ALLOWED_HOSTS == ALLOWED_HOSTS.split(delimiter)

    ALLOWED_HOSTS = ["localhost"]
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost")
    export_to_module(ALLOWED_HOSTS, name="ALLOWED_HOSTS", module=__name__)

    @envotate
    class ValidForDefault:
        ALLOWED_HOSTS: Annotated[list[str], Split()]

    assert ValidForDefault.ALLOWED_HOSTS == ALLOWED_HOSTS

    monkeypatch.setenv("ALLOWED_HOSTS", "localhost|local.host|127.0.0.1")
    with pytest.raises(VariableError) as excinfo:

        @envotate
        class InvalidSplit:
            ALLOWED_HOSTS: Annotated[list[str], Method("make_bad_input"), Split("|")]

            @classmethod
            def make_bad_input(cls, value):
                return 1

    assert excinfo.match("ALLOWED_HOSTS")


def test_annotated_directory_and_file_type(monkeypatch, export_to_module):
    BASE_DIR = Path(__file__).parent.absolute()
    APP_DIR = BASE_DIR / "testapp"
    DATA_DIR = APP_DIR / "data"
    FILES_DIR = DATA_DIR / "files"
    FILE_NAME = "file.txt"
    FILE_PATH = FILES_DIR / FILE_NAME

    export_to_module(BASE_DIR, name="BASE_DIR", module=__name__)
    export_to_module(APP_DIR, name="APP_DIR", module=__name__)
    export_to_module(DATA_DIR, name="DATA_DIR", module=__name__)
    export_to_module(FILES_DIR, name="FILES_DIR", module=__name__)
    export_to_module(FILE_NAME, name="FILE_NAME", module=__name__)
    export_to_module(FILE_PATH, name="FILE_PATH", module=__name__)

    monkeypatch.setenv("BASE", str(BASE_DIR))
    monkeypatch.setenv("APP", str(APP_DIR))
    monkeypatch.setenv("DATA", str(DATA_DIR))
    monkeypatch.setenv("DATA2", str(DATA_DIR))
    monkeypatch.setenv("FILES", str(FILES_DIR))
    monkeypatch.setenv("FILE", str(FILE_PATH))
    monkeypatch.setenv("FILE2", str(FILE_PATH))
    monkeypatch.setenv("FILE3", str(FILE_PATH))

    @envotate
    class PathConfig:
        BASE: Annotated[Path, Directory]
        APP: Annotated[Path, Directory(BASE_DIR)]
        DATA: Annotated[Path, Directory(base=str(APP_DIR))]
        FILES: Annotated[Path, Directory()]
        FILE: Annotated[Path, File]
        FILE2: Annotated[Path, File(base=FILES_DIR.parent)]
        FILE3: Annotated[Path, File(str(FILES_DIR.parent))]

    assert PathConfig.BASE == BASE_DIR
    assert PathConfig.APP == APP_DIR
    assert PathConfig.DATA == DATA_DIR
    assert PathConfig.FILES == FILES_DIR
    assert PathConfig.FILE == FILE_PATH

    with pytest.raises(VariableError) as excinfo:

        @envotate
        class InvalidDirBase:
            APP: Annotated[Path, Directory("unknown/base")]

    assert excinfo.match("InvalidDirBase.APP")
    assert excinfo.match("unknown/base")

    with pytest.raises(VariableError) as excinfo:

        @envotate
        class InvalidFileBase:
            APP: Annotated[Path, File("unknown/base")]

    assert excinfo.match("InvalidFileBase.APP")
    assert excinfo.match("unknown/base")


def test_method_arg():
    @envotate
    class URLSettings:
        APP_ENV: str = "prod"
        DOMAIN: str = "mysite.com"
        PUBLIC_URL: Annotated[Union[bytes, str, None], Method("make_public_url")]

        @classmethod
        def make_public_url(cls) -> str:
            if cls.APP_ENV == "prod":
                url = f"https://www.{cls.DOMAIN}/"
            elif cls.APP_ENV == "staging":
                url = f"http://staging.{cls.DOMAIN}/"
            else:
                url = "http://localhost:8000/"

            return url

    assert URLSettings.PUBLIC_URL == "https://www.mysite.com/"


def make_public_url(context: Context[FunctionConfig]) -> str:
    if context.APP_ENV == "prod":
        url = f"https://www.{context.DOMAIN}/"
    elif context.APP_ENV == "staging":
        url = f"http://staging.{context.DOMAIN}/"
    else:
        url = "http://localhost:8000/"

    return url


class FunctionConfig:
    APP_ENV: str = "prod"
    DOMAIN: str = "mysite.com"
    PUBLIC_URL: Annotated[str, Function(make_public_url)] = ""


def test_function_arg(export_to_module):
    @envotate
    class ValidFunctionConfig(FunctionConfig):
        pass

    export_to_module(ValidFunctionConfig)

    assert ValidFunctionConfig.PUBLIC_URL == "https://www.mysite.com/"


STRING_PATTERN = r"^(prod|staging|dev)$"
COMPILED_STRING_PATTERN = re.compile(STRING_PATTERN)


class StringPattern:
    APP_ENV: Annotated[str, Regex(STRING_PATTERN)]


class CompiledStringPattern:
    APP_ENV: Annotated[str, Regex(COMPILED_STRING_PATTERN)]


def test_annotated_regex_type(monkeypatch, export_to_module):
    matches = ["prod", "staging", "dev"]
    for match in matches:
        monkeypatch.setenv("APP_ENV", match)

        @envotate
        class ValidString(StringPattern):
            pass

        @envotate
        class ValidCompiledString(CompiledStringPattern):
            pass

        assert ValidString.APP_ENV == match
        assert ValidCompiledString.APP_ENV == match

    # monkeypatch.setenv("APP_ENV", "local")
    # with pytest.raises(VariableError) as excinfo:

    #     @envotate
    #     class InvalidForStringPattern:
    #         APP_ENV: Annotated[str, Regex(PATTERN)]

    # assert excinfo.match("does not match")

    # with pytest.raises(VariableError) as excinfo:

    #     @envotate
    #     class InvalidForCompiledPattern:
    #         APP_ENV: Annotated[str, Regex(re.compile(PATTERN))]

    # assert excinfo.match("does not match")


class UnknownType:
    def run(self):
        pass


def test_ignore_unknown_annotated_type(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")

    @envotate
    class InvalidAnnotatedType:
        APP_ENV: Annotated[str, UnknownType]

    assert InvalidAnnotatedType.APP_ENV == "prod"


class LiteralConfig:
    APP_ENV: Union[bytes, Literal["prod", "staging", "dev"]]


def test_literal_types(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")

    @envotate
    class ValidLiteralConfig(LiteralConfig):
        pass

    assert ValidLiteralConfig.APP_ENV == "prod"

    with pytest.raises(VariableError) as excinfo:
        monkeypatch.setenv("APP_ENV", "local")

        @envotate
        class InvalidLiteralConfig(LiteralConfig):
            pass

    assert excinfo.match("InvalidLiteralConfig.APP_ENV")
