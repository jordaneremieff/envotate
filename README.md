# Envotate

**Work in progress**: Things may change/break at this point.

Settings management using environment variables and type annotations.

**Requirements**: Python 3.9+

## Installation

```shell
pip install envotate
```

## Example

Define a configuration like this:

```python
# app/settings.py
from envotate import envotate
from envotate.types import Choice, Default


@envotate
class Database:
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str


PY_39 = "py39"
PY_310 = "py310"


@envotate
class Settings:
    DATABASE: Database
    DEBUG: bool = False
    PY_VERSION: Env[str, Choice([PY_39, PY_310])]

```

Then access it in an application:

```python
# app/main.py
from app.settings import Settings


def main():
    print(Settings.DATABASE.DB_NAME)


if __name__ == "__main__":
    main()

```
