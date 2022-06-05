from __future__ import annotations

import os
from unittest import mock

from envotate.env import env, Env
from envotate.types import Match, Choice, Split, Method, Default  # , Function


class RegexConf:
    ALLOWED_HOSTS: Env[
        list[str],
        Match(pattern=r"^(localhost|127\.0\.0\.1|local\.host)$"),
        Split(delimiter="|"),
    ]


def test_value_field():
    @env
    class URLConf:
        APP_ENV: str = "prod"
        DOMAIN: str = "mysite.com"
        PUBLIC_URL: Env[
            str,
            Default(Method("set_public_url")),
        ]

        @classmethod
        def set_public_url(cls, **kwargs) -> str:
            if cls.APP_ENV == "prod":
                url = f"https://www.{cls.DOMAIN}/"
            elif cls.APP_ENV == "staging":
                url = f"http://staging.{cls.DOMAIN}/"
            else:
                url = "http://localhost:8000/"

            return url

    assert URLConf.PUBLIC_URL == "https://www.mysite.com/"


def test_regex_field():
    valid_hosts = ["localhost", "127.0.0.1", "local.host"]
    for host in valid_hosts:
        with mock.patch.dict(os.environ, {"ALLOWED_HOSTS": host}):

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


# def test_invalid_annotated_type_rule():
#     # with pytest.raises(TypeError):

#     class InvalidClass:
#         pass

#     @env
#     class Conf:
#         DEBUG: Env[str, InvalidClass] = "debug"
