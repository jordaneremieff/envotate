import re
from dataclasses import dataclass
from typing import Callable, Pattern, Union

from envotate.typing import AnnotatedClass, Value, Missing


@dataclass
class Method:
    name: str

    def set_context(self, annotated_class: AnnotatedClass) -> None:
        self.context = annotated_class

    def __call__(self, source: Union[Value, Missing]) -> Value:
        return getattr(self.context, self.name)(source=source)


@dataclass
class Function:
    func: Callable

    def set_context(self, annotated_class: AnnotatedClass) -> None:
        self.context = annotated_class

    def __call__(self, source: Union[Value, Missing]) -> Value:
        return self.func(source=source, context=self.context)


@dataclass
class Default:
    default: Union[Method, Function, Value]

    def set_context(self, annotated_class: AnnotatedClass) -> None:
        if isinstance(self.default, (Method, Function)):
            self.default.set_context(annotated_class)

    def get_default(self, source: Union[Value, Missing]) -> Value:
        if isinstance(self.default, (Method, Function)):
            return self.default(source)
        return self.default


@dataclass
class Split:
    delimiter: str = ","

    def __call__(self, source: str) -> list[str]:
        return source.split(self.delimiter)


@dataclass
class Match:
    pattern: Union[str, Pattern]

    def __call__(self, source: str) -> str:
        if isinstance(self.pattern, str):
            regex = re.compile(self.pattern)
        else:
            regex = self.pattern

        if regex.match(source):
            return source

        raise ValueError(f"{source} does not match {self.pattern}")


@dataclass
class Choice:
    choices: list[str]

    def __call__(self, source: Value) -> Value:
        if source in self.choices:
            return source

        raise ValueError(f"{source} is not a valid choice ({self.choices}).")
