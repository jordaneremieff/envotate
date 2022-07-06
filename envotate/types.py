from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from re import Pattern
from typing import Callable, Sequence, TypedDict, Union, get_type_hints
from urllib.parse import urlparse

from envotate.typing import Value


def make_path(value: str, *, base: Union[str, Path]) -> Path:
    if not base:
        return Path(value)
    if isinstance(base, str):
        base = Path(base)
    if base.is_file():
        raise ValueError(f"Base path '{base}' is a file, not a directory.")
    if not base.is_dir():
        raise ValueError(f"Base path '{base}' could not be resolved.")

    return base / value


@dataclass
class Directory:
    base: Union[Path, str] = ""

    def apply(self, value: str) -> Path:
        path = make_path(value, base=self.base)
        if path.is_file():
            raise ValueError(f"'{path}' is a file, not a directory.")
        if not path.is_dir():
            raise ValueError(f"'{path}' could not be resolved.")

        return path


@dataclass
class File:
    base: Union[Path, str] = ""

    def apply(self, value: str) -> Path:
        path = make_path(value, base=self.base)
        if path.is_dir():
            raise ValueError(f"'{value}' is a valid directory, not a file.")
        if not path.is_file():
            raise ValueError(f"'{value}' could not be resolved.")

        return path


@dataclass
class Split:
    delimiter: str = ","

    def apply(self, value: str) -> list[str]:
        try:
            value_list = value.split(self.delimiter)
        except AttributeError as exc:
            raise ValueError(f"'{value}' could not be converted into a list: {exc}")

        return value_list


@dataclass
class Regex:
    pattern: Union[str, Pattern[str]]

    def apply(self, value: str) -> str:
        if isinstance(self.pattern, str):
            pattern = re.compile(self.pattern)
        else:
            pattern = self.pattern

        match = pattern.match(value)
        if not match:
            raise ValueError(f"'{value}' did not match '{pattern}'")

        return value


@dataclass
class Choice:
    choices: Sequence[Value]

    def apply(self, value: Value) -> Value:
        if isinstance(value, (list, tuple)):
            if not value:
                raise ValueError("Empty sequence cannot be used for choice validation.")

            for choice in value:
                if choice not in self.choices:
                    raise ValueError(
                        f"'{choice}' is not a valid choice for {self.choices}."
                    )

        elif value not in self.choices:
            raise ValueError(f"'{value}' is not a valid choice for {self.choices}.")

        return value


@dataclass
class Method:
    name: str

    def apply(self, value: Value, context: type) -> Value:
        method = getattr(context, self.name)
        params = get_type_hints(method)
        if "value" not in params:
            value = method()
        elif "value" in params:
            value = method(value)
        else:
            value = method(context)

        return value


@dataclass
class Function:

    function: Callable[..., Value]

    def __post_init__(self) -> None:
        if not callable(self.function):
            raise ValueError(f"{self.function} is not callable.")
        self.apply = self.function


class DjangoDB(TypedDict):
    # ENGINE: Literal[
    #     "django.db.backends.postgresql",
    #     "django.db.backends.mysql",
    #     "django.db.backends.sqlite3",
    #     "django.db.backends.oracle",
    # ]
    ENGINE: str
    NAME: str
    USER: str
    PASSWORD: str
    HOST: str
    PORT: Union[str, int]
    OPTIONS: dict[str, str]
    CONN_MAX_AGE: int
    AUTOCOMMIT: bool
    ATOMIC_REQUESTS: bool


@dataclass
class DjangoDSN:
    conn_max_age: int = 0
    atomic_requests: bool = False
    autocommit: bool = True

    def apply(self, value: str) -> DjangoDB:
        dsn = urlparse(value)

        if dsn.scheme == "":
            raise ValueError("DSN must have a scheme.")
        if dsn.scheme in ("postgresql", "postgres"):
            engine = "django.db.backends.postgresql"
        elif dsn.scheme == "mysql":
            engine = "django.db.backends.mysql"
        elif dsn.scheme in ("sqlite", "sqlite3"):
            engine = "django.db.backends.sqlite3"
        elif dsn.scheme == "oracle":
            engine = "django.db.backends.oracle"
        else:
            raise ValueError(f"'{dsn.scheme}' is not a valid Django database scheme.")

        name = dsn.path[1:] or ""
        hostname = dsn.hostname or ""
        port = dsn.port or ""
        username = dsn.username or ""
        password = dsn.password or ""
        if not dsn.query:
            options = {}
        else:
            options = {
                k: v for k, v in (option.split("=") for option in dsn.query.split("&"))
            }

        return {
            "ENGINE": engine,
            "NAME": name,
            "USER": username,
            "PASSWORD": password,
            "HOST": hostname,
            "PORT": port,
            "OPTIONS": options,
            "CONN_MAX_AGE": self.conn_max_age,
            "AUTOCOMMIT": self.autocommit,
            "ATOMIC_REQUESTS": self.atomic_requests,
        }


# f"postgresql://postgres:mangum@{hostname}:{host_port}/postgres"


# dialect[+driver]://user:password@host/dbname[?key=value..]

# @dataclass
# class PostgresDSN:
#     schemes: set[str] = {"postgresql", "postgres"}
#     drivers: Optional[set[str]] = None


#     def apply(self, value: str) -> Value:
#         parsed_dsn = urlparse(value)
#         if parsed_dsn.scheme not in self.scheme:


#         return value


#      "postgresql://[userspec@][hostspec][/dbname][?paramspec]"

# #     """[scheme]://[userspec@][hostspec][/dbname][?paramspec]"""
