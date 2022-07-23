from __future__ import annotations

from typing import (
    Generator,
    Protocol,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
    runtime_checkable,
)

from typing_extensions import TypeAlias

Class = TypeVar("Class")
Context: TypeAlias = type[Class]
Value: TypeAlias = Union[set, str, list, dict, float, int, bool, None]


T = TypeVar("T")


@runtime_checkable
class AnnotatedArg(Protocol):
    @overload
    def apply(self, __value: Value) -> Value:
        ...  # pragma: nocover

    @overload
    def apply(self, __context: Context[T]) -> Value:
        ...  # pragma: nocover

    @overload
    def apply(self, __value: Value, __context: Context[T]) -> Value:
        ...  # pragma: nocover

    @overload
    def apply(self) -> Value:
        ...  # pragma: nocover


def get_root_arg(annotation: type) -> type:
    if origin := get_origin(annotation):
        return get_root_arg(origin)

    return annotation


VALUE_TYPES = (int, float, str, bool, bytes, list, dict, set, tuple, type(None))


def unpack_args(annotation: type) -> list[Union[Value, type]]:
    unpacked: list[Union[Value, type]] = []
    args = get_args(annotation)
    if not args:
        unpacked.append(annotation)
        return unpacked

    for arg in args:
        if isinstance(arg, AnnotatedArg):
            continue
        root = get_root_arg(arg)
        if root in VALUE_TYPES:
            if not unpacked or unpacked[-1] != root:
                unpacked.append(root)

        for _arg in unpack_args(arg):
            if not unpacked or unpacked[-1] != _arg:
                unpacked.append(_arg)

    return unpacked
