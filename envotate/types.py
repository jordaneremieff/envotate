from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable, Pattern, Union

from envotate.exceptions import EnvValueError
from envotate.typing import Value


@dataclass
class Method:
    name: str

    def set_cls(self, cls: type) -> None:
        self.cls = cls

    def __call__(self, value: Value) -> Value:
        method = getattr(self.cls, self.name)

        return method(value=value)


@dataclass
class Function:
    func: Callable

    def set_cls(self, cls: type) -> None:
        self.cls = cls

    def __call__(self, value: Value) -> Value:
        return self.func(cls=self.cls, value=value)


@dataclass
class Split:
    delimiter: str = ","

    def __call__(self, value: str) -> list[str]:
        return value.split(self.delimiter)


@dataclass
class Match:
    pattern: Union[str, Pattern]

    def __call__(self, value: str) -> str:
        if isinstance(self.pattern, str):
            regex = re.compile(self.pattern)
        else:
            regex = self.pattern

        if regex.match(value):
            return value

        raise EnvValueError(f"{value} does not match {self.pattern}")


@dataclass
class Choice:
    choices: list[str]

    def __call__(self, value: Value) -> Value:
        if value in self.choices:
            return value

        raise EnvValueError(f"{value} is not a valid choice ({self.choices}).")
