# Usage

The decorator function `envotate` must be used as the entrypoint to configure the environment variables for a class.


## Using the decorator

The most basic usage only requires decorating the class (without parentheses):

```python
from envotate import envotate

@envotate
class Settings:
    DEBUG: bool
```

It may also be provided one or more optional parameters for more detailed configuration:

```python
@envotate(prefix="DB")
class Settings:
    NAME: str
    HOST: str
    PORT: int = 5432
```

### Optional parameters

* `prefix` - A string prefix used to form the environment lookup key for each annotation
discovered in the root class or any of its bases.

* `aliases` - A mapping of class attributes and variable names to represent the specific
environment lookup key to use instead of the attribute name.

* `export` - A set of one or more class attributes to export as variables in the module
namespace for the class. If the set consists of a single string `'__all__'` then all
of the attributes will be exported.

## Annotated types

The creation of special types for handling more granular configurations and validation at runtime is made possible by the [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) type from the Python standard library. These types may be provided as context-specific metadata to `Annotated` to be evaulated for a configuration variable.

### Example

```shell
PY_VERSION=py39
```

```python
from envotate import envotate

@envotate
class Settings:
    PY_VERSION: Annotated[str, Choice(["py39", "py310"])]

```

Annotated metadata types are composable and will be evaluated in order with each type receiving the result of the previous evaluation.

```python
from envotate import envotate


@envotate
class Settings:
    PY_VERSION: Annotated[
        str,
        Regex(r"^(py39|py310)$"),
        Choice(
            ["py39", "py310"],
        ),
    ]
```

All of the supported types in `envotate.types` may be provided as context-specific metadata as well as custom types that conform to the same interface.


### Interface

```python
from envotate import Value


class Arg:
    def evaluate(self, value: Value) -> Value:
        ...
```

### With context

Additionally, the context of the class containing the annotated type can be made available to the type by including the `contextualize` method:

```python
from envotate import Value


class Arg:
    def contextualize(self, cls: type) -> None:
        ...

    def evaluate(self, value: Value) -> Value:
        ...
```



### Supported types

#### Split




#### Match

### Choice

#### Method

`Method` may be used to reference the name of any `@classmethod` on the configuration class to inform the value for a configuration.


```python
from envotate import envotate
from envotate.types import Method

@envotate
class Settings:
    APP_ENV: str
    DOMAIN: str = "example.com"
    URL: Annotated[str, Method("configure_url")] = "http://localhost:8000/"

    @classmethod
    def configure_url(cls, value: str) -> str:
        if cls.APP_ENV == "prod":
            return f"https://www.{cls.DOMAIN}/"
        if cls.APP_ENV == "staging":
            return f"http://staging.{cls.DOMAIN}/"

        return value

```

#### Function

The `Function` type works similarly to the `Method` type except it is used for functions defined outside of the class.

```python
def configure_url(cls, value: str) -> str:
    if cls.APP_ENV == "prod":
        return f"https://www.{cls.DOMAIN}/"
    if cls.APP_ENV == "staging":
        return f"http://staging.{cls.DOMAIN}/"

    return value

@envotate
class Settings:
    APP_ENV: str
    DOMAIN: str = "example.com"
    PUBLIC_URL: Annotated[str, Function(configure_url)] = "http://localhost:8000/"

```




