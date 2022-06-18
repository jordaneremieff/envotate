from __future__ import annotations

import re

import pytest

from envotate import Env, envotate
from envotate.exceptions import EnvValueError
from envotate.types import Choice, Match, Split


def test_arg_with_no_default():
    with pytest.raises(EnvValueError) as excinfo:

        @envotate
        class Settings:
            APP_ENV: Env[
                str,
                Match(pattern=r"^(prod|stag|dev)$"),
            ]

    assert excinfo.match("APP_ENV")


def test_regex_arg(monkeypatch):
    class RegexSettings:
        ALLOWED_HOSTS: Env[
            list[str],
            Match(pattern=r"^(localhost|127.0.0.1|local.host)$"),
            Split(delimiter="|"),
        ]

        ALLOWED_HOSTS_COMPILED: Env[
            list[str],
            Match(pattern=re.compile(r"^(localhost|127.0.0.1|local.host)$")),
            Split(delimiter="|"),
        ]

    valid_hosts = ["localhost", "127.0.0.1", "local.host"]
    for host in valid_hosts:
        monkeypatch.setenv("ALLOWED_HOSTS", host)
        monkeypatch.setenv("ALLOWED_HOSTS_COMPILED", host)

        @envotate
        class Settings(RegexSettings):
            APP_ENV: Env[
                str,
                Match(pattern=r"^(prod|stag|dev)$"),
            ] = "dev"
            VERSION: Env[
                str,
                Match(pattern=r"^(py39|py310)$"),
                Choice(["py39"]),
            ] = "py39"

        assert Settings.APP_ENV == "dev"
        assert Settings.VERSION == "py39"
        assert Settings.ALLOWED_HOSTS == [host]
        assert Settings.ALLOWED_HOSTS_COMPILED == [host]


def test_value_does_not_match_regex_pattern(monkeypatch):

    monkeypatch.setenv("ALLOWED_HOSTS", "invalid.host|other.host")

    with pytest.raises(EnvValueError) as excinfo:

        @envotate
        class RegexSettings:
            ALLOWED_HOSTS: Env[
                list[str],
                Match(pattern=r"^(localhost|127.0.0.1|local.host)$"),
                Split(delimiter="|"),
            ]

    assert excinfo.match("does not match")


def test_value_is_not_supported_for_choice(monkeypatch):
    monkeypatch.setenv("PY_VERSION", "py38")
    with pytest.raises(EnvValueError) as excinfo:

        @envotate
        class Settings:
            PY_VERSION: Env[
                str,
                Choice(["py39", "py310"]),
            ]

    assert excinfo.match("is not a valid choice")


# def test_method_arg():
#     @envotate
#     class URLSettings:
#         APP_ENV: str = "prod"
#         DOMAIN: str = "mysite.com"
#         PUBLIC_URL: Env[str, Method("make_public_url")]

#         @classmethod
#         def make_public_url(cls) -> str:
#             if cls.APP_ENV == "prod":
#                 url = f"https://www.{cls.DOMAIN\}/"
#             elif cls.APP_ENV == "staging":
#                 url = f"http://staging.{cls.DOMAIN\}/"
#             else:
#                 url = "http://localhost:8000/"

#             return url

#     assert URLSettings.PUBLIC_URL == "https://www.mysite.com/"
