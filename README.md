# Envotate

**Work in progress**: Things may change/break at this point.

Settings management using environment variables and type annotations.

**Requirements**: Python 3.9+

## Installation

```shell
pip install envotate
```

## Example

Set the following variables in the environment:

```shell
DEBUG=true
PY_VERSION=py39
DB_USER=admin
DB_PASSWORD=password
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=postgres
```

Define a configuration like this:

```python
# app/settings.py
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

```

Then access it in an application:

```python
# app/main.py
from app.settings import Settings


def main():
    print(Settings.__dict__)


if __name__ == "__main__":
    main()

```

Output:

```python
mappingproxy(
    {
        '__module__': 'app.settings',
        '__annotations__': {
            'DEBUG': 'bool', 
            'DATABASE': 'Database', 
            'PY_VERSION': "Annotated[str, Choice(['py39', 'py310'])]"
        },
        '__dict__': <attribute '__dict__' of 'Settings' objects>,
        '__weakref__': <attribute '__weakref__' of 'Settings' objects>,
        '__doc__': None,
        '__envotations__': {'PY_VERSION', 'DEBUG', 'DATABASE'},
        'DEBUG': True,
        'DATABASE': <class 'app.settings.Database'>,
        'PY_VERSION': 'py39'
    }
)
```
