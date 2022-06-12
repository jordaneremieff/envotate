from envotate.env import Env, env
from envotate.types import Choice, Default, Match, Function, Split


APP_ID: int

APP_NAME: str

APP_ENV: Env[
    str,
    Match(pattern=r"^(prod|stag|dev)$"),
    Default("dev"),
]


ALLOWED_HOSTS: Env[list[str], Split(delimiter=","), Default("localhost,")]

DEBUG: bool = False

PY_VERSION: Env[
    str,
    Match(pattern=r"^(py39|py310)$"),
    Choice(["py39"]),
    Default("py39"),
]


BASE_URL: str


def make_public_url(context) -> str:
    return f"{context.BASE_URL}{context.APP_NAME}"


PUBLIC_URL: Env[
    str,
    Default(Function(make_public_url)),
]


env(__name__)
