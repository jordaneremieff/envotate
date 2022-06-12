from __future__ import annotations
import re

import pytest

from envotate.env import env, Env
from envotate.types import Match, Choice, Split, Method, Default
from envotate.exceptions import EnvValueError  # , Function


def test_arg_with_no_default():
    with pytest.raises(EnvValueError) as excinfo:

        @env
        class Conf:
            APP_ENV: Env[
                str,
                Match(pattern=r"^(prod|stag|dev)$"),
            ]

    assert excinfo.match("APP_ENV")


def test_method_arg():
    @env
    class URLConf:
        APP_ENV: str = "prod"
        DOMAIN: str = "mysite.com"
        PUBLIC_URL: Env[
            str,
            Default(Method("set_public_url")),
        ]

        @classmethod
        def set_public_url(cls) -> str:
            if cls.APP_ENV == "prod":
                url = f"https://www.{cls.DOMAIN}/"
            elif cls.APP_ENV == "staging":
                url = f"http://staging.{cls.DOMAIN}/"
            else:
                url = "http://localhost:8000/"

            return url

    assert URLConf.PUBLIC_URL == "https://www.mysite.com/"


def test_regex_arg(monkeypatch):
    class RegexConf:
        ALLOWED_HOSTS: Env[
            list[str],
            Match(pattern=r"^(localhost|127\.0\.0\.1|local\.host)$"),
            Split(delimiter="|"),
        ]

        ALLOWED_HOSTS_COMPILED: Env[
            list[str],
            Match(pattern=re.compile(r"^(localhost|127\.0\.0\.1|local\.host)$")),
            Split(delimiter="|"),
        ]

    valid_hosts = ["localhost", "127.0.0.1", "local.host"]
    for host in valid_hosts:
        monkeypatch.setenv("ALLOWED_HOSTS", host)
        monkeypatch.setenv("ALLOWED_HOSTS_COMPILED", host)

        @env
        class Conf(RegexConf):
            APP_ENV: Env[
                str,
                Match(pattern=r"^(prod|stag|dev)$"),
                Default("dev"),
            ]
            VERSION: Env[
                str,
                Match(pattern=r"^(py39|py310)$"),
                Choice(["py39"]),
                Default("py39"),
            ]

        assert Conf.APP_ENV == "dev"
        assert Conf.VERSION == "py39"
        assert Conf.ALLOWED_HOSTS == [host]
        assert Conf.ALLOWED_HOSTS_COMPILED == [host]


def test_value_does_not_match_regex_pattern(monkeypatch):

    monkeypatch.setenv("ALLOWED_HOSTS", "invalid.host|other.host")

    with pytest.raises(EnvValueError) as excinfo:

        @env
        class RegexConf:
            ALLOWED_HOSTS: Env[
                list[str],
                Match(pattern=r"^(localhost|127\.0\.0\.1|local\.host)$"),
                Split(delimiter="|"),
            ]

    assert excinfo.match("does not match")


def test_value_is_not_supported_for_choice(monkeypatch):
    monkeypatch.setenv("PY_VERSION", "py38")
    with pytest.raises(EnvValueError) as excinfo:

        @env
        class Conf:
            PY_VERSION: Env[
                str,
                Choice(["py39", "py310"]),
            ]

    assert excinfo.match("is not a valid choice")
