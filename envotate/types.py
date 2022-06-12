import re
from dataclasses import dataclass
from typing import Callable, Pattern, Union

from envotate.exceptions import EnvValueError
from envotate.typing import AnnotatedClass, Value


@dataclass
class Method:
    name: str

    def set_context(self, annotated_class: AnnotatedClass) -> None:
        self.context = annotated_class

    def __call__(self) -> Value:
        method = getattr(self.context, self.name)

        return method()


@dataclass
class Function:
    func: Callable

    def set_context(self, annotated_class: AnnotatedClass) -> None:
        self.context = annotated_class

    def __call__(self) -> Value:
        return self.func(context=self.context)


@dataclass
class Default:
    default: Union[Method, Function, Value]

    def set_context(self, annotated_class: AnnotatedClass) -> None:
        if isinstance(self.default, (Method, Function)):
            self.default.set_context(annotated_class)

    def get_default(self) -> Value:
        if isinstance(self.default, (Method, Function)):
            return self.default()
        return self.default


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
