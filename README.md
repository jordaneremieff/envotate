# Envotate

**Work in progress**

Settings management using environment variables and type annotations. This intended to support both class-based and module-based configurations.

## Example

<img src="https://user-images.githubusercontent.com/1376648/173243159-af22ce43-c7b9-4854-9187-aec83342bce0.gif" width="50%" height="50%"/>

Define a configuration like this:

```python
# app/settings.py
from envotate.env import Env, env
from envotate.types import Choice, Default


@env
class Database:
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str


PY_39 = "py39"
PY_310 = "py310"


@env
class Settings:
    DATABASE: Database
    DEBUG: bool = False
    PY_VERSION: Env[str, Choice([PY_39, PY_310]), Default(PY_39)]

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
