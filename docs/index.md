<h1 align="center">
    Envotate
</h1>
<p align="center">
    <em>Settings management using environment variables and type annotations.</em>
</p>
<p align="center">
    <a href="https://github.com/jordaneremieff/envotate/actions/workflows/test.yml">
    <img src="https://img.shields.io/github/workflow/status/jordaneremieff/envotate/Test/main" alt="GitHub workflow status (Test)" >
    </a>
    <a href="https://pypi.org/project/envotate" target="_blank">
        <img src="https://img.shields.io/pypi/v/envotate" alt="PyPi package">
    </a>
    <a href="https://pypi.org/project/envotate" target="_blank">
        <img src="https://img.shields.io/pypi/pyversions/envotate" alt="Supported Python versions">
    </a>
</p>

**Work in progress**

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


@envotate(prefix="DB")
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
