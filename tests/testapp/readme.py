from __future__ import annotations

from envotate import envotate, Annotated
from envotate.types import Choice


@envotate(prefix="DB_")
class Database:
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    NAME: str


@envotate
class Settings:
    DEBUG: bool
    DATABASE: Database
    PY_VERSION: Annotated[str, Choice(["py39", "py310"])]
