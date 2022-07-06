from __future__ import annotations

from typing import Annotated

from envotate import envotate
from envotate.errors import VariableError
from envotate.types import Choice, Function, Method, Regex, Split


def test_usage_example_of_annotated_types(monkeypatch):
    monkeypatch.setenv("PY_VERSION", "py39")

    @envotate
    class Settings:
        PY_VERSION: Annotated[
            str,
            Regex(r"^(py39|py310)$"),
            Choice(
                ["py39", "py310"],
            ),
        ]

    assert Settings.PY_VERSION == "py39"


# def test_usage_example_of_method_type(monkeypatch):
#     monkeypatch.setenv("APP_ENV", "staging")

#     @envotate
#     class Settings:
#         APP_ENV: str
#         DOMAIN: str = "example.com"
#         URL: Annotated[str, Method("configure_url")] = "http://localhost:8000/"

#         @classmethod
#         def configure_url(cls, value: str) -> str:
#             if cls.APP_ENV == "prod":
#                 return f"https://www.{cls.DOMAIN}/"
#             if cls.APP_ENV == "staging":
#                 return f"http://staging.{cls.DOMAIN}/"

#             return value

#     assert Settings.URL == f"http://staging.{Settings.DOMAIN}/"


# def configure_url(cls, value: str) -> str:
#     if cls.APP_ENV == "prod":
#         return f"https://www.{cls.DOMAIN}/"
#     if cls.APP_ENV == "staging":
#         return f"http://staging.{cls.DOMAIN}/"

#     return value


# def test_usage_example_of_function_type(monkeypatch):
#     monkeypatch.setenv("APP_ENV", "staging")

#     @envotate
#     class Settings:
#         APP_ENV: str
#         DOMAIN: str = "example.com"
#         PUBLIC_URL: Annotated[str, Function(configure_url)] = "http://localhost:8000/"

#     assert Settings.PUBLIC_URL == f"http://staging.{Settings.DOMAIN}/"
