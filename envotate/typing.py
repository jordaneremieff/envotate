from __future__ import annotations

from typing import (
    Any,
    Generator,
    Literal,
    Protocol,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    runtime_checkable,
)
from typing_extensions import TypeAlias


class Missing:
    def __bool__(self):
        return False  # pragma: no cover


Value: TypeAlias = Union[set, str, list, dict, float, int, bool, None]
AnnotatedClass: TypeAlias = Type


@runtime_checkable
class MissingValue(Protocol):
    def __repr__(self) -> Literal["envotate.typing.Missing"]:
        ...  # pragma: no cover

    def __bool__(self) -> Literal[False]:
        ...  # pragma: no cover


@runtime_checkable
class AnnotatedArg(Protocol):
    def __call__(self, value: Any) -> Any:
        ...  # pragma: no cover


@runtime_checkable
class SupportsContext(Protocol):
    def set_context(self, annotated_class: AnnotatedClass) -> None:
        ...  # pragma: no cover


@runtime_checkable
class SupportsDefault(Protocol):
    def get_default(self) -> Value:
        ...  # pragma: no cover


def is_annotated_class(
    obj: object,
) -> bool:
    return bool(obj and obj is not object and hasattr(obj, "__annotations__"))


def iter_annotations(
    annotated_class: AnnotatedClass,
) -> Generator[tuple[str, Union[type, AnnotatedClass], bool], None, None]:
    for base in reversed(annotated_class.__mro__):
        for name, annotation in get_type_hints(base, include_extras=True).items():
            yield name, annotation, is_annotated_class(annotation)


def update_args(annotation: type, annotated_class: AnnotatedClass) -> None:
    for arg in get_args(annotation):
        if isinstance(arg, SupportsContext):
            arg.set_context(annotated_class)


def get_root_arg(annotation: type) -> type:
    if origin := get_origin(annotation):
        return get_root_arg(origin)

    return annotation
