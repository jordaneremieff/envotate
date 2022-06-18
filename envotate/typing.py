from __future__ import annotations

from typing import (
    Generator,
    Protocol,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    runtime_checkable,
)

from typing_extensions import TypeAlias

Value: TypeAlias = Union[set, str, list, dict, float, int, bool, None]


@runtime_checkable
class AnnotatedArg(Protocol):
    def __call__(self, value: Value) -> Value:
        ...  # pragma: no cover


@runtime_checkable
class SupportsContext(Protocol):
    def set_context(self, cls: Type) -> None:
        ...  # pragma: no cover


def is_cls(
    obj: object,
) -> bool:
    return bool(obj and obj is not object and hasattr(obj, "__annotations__"))


def iter_annotations(
    cls: Type,
) -> Generator[tuple[str, Union[type, Type], bool], None, None]:
    for base in cls.__mro__:
        for name, annotation in get_type_hints(base, include_extras=True).items():
            yield name, annotation, is_cls(annotation)


def update_args(annotation: type, cls: Type) -> None:
    for arg in get_args(annotation):
        if isinstance(arg, SupportsContext):
            arg.set_context(cls)


def get_root_arg(annotation: type) -> type:
    if origin := get_origin(annotation):
        return get_root_arg(origin)

    return annotation
