from __future__ import annotations

from typing import (
    Generator,
    Protocol,
    TypeVar,
    Union,
    get_origin,
    get_type_hints,
    runtime_checkable,
)

from typing_extensions import TypeAlias


@runtime_checkable
class Arg(Protocol):
    def __call__(self, value: Value) -> Value:
        ...  # pragma: no cover


@runtime_checkable
class ArgWithCls(Protocol):
    def set_cls(self, cls: type) -> None:
        ...  # pragma: no cover


Class = TypeVar("Class")


Value: TypeAlias = Union[set, str, list, dict, float, int, bool, None]


def get_type_hints_with_extras(
    cls: type,
) -> Generator[tuple[str, type, bool], None, None]:
    for base in cls.__mro__:
        if not base or base is object:
            continue
        for name, annotation in get_type_hints(base, include_extras=True).items():
            nested = bool(
                annotation
                and annotation is not object
                and hasattr(annotation, "__annotations__")
            )
            yield name, annotation, nested


def get_root_arg(annotation: type) -> type:
    if origin := get_origin(annotation):
        return get_root_arg(origin)

    return annotation
