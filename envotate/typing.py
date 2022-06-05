from __future__ import annotations

from typing import (
    Generator,
    Literal,
    Optional,
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
        return False


Value: TypeAlias = Union[set, str, list, dict, float, int, bool, None]
Source: TypeAlias = Union[str, Missing]
AnnotatedClass: TypeAlias = Type


@runtime_checkable
class MissingValue(Protocol):
    def __repr__(self) -> Literal["envotate.typing.Missing"]:
        ...

    def __bool__(self) -> Literal[False]:
        return False


@runtime_checkable
class AnnotatedArg(Protocol):
    def __call__(self, source: Value) -> Value:
        ...


@runtime_checkable
class SupportsContext(Protocol):
    def set_context(self, annotated_class: AnnotatedClass) -> None:
        ...


@runtime_checkable
class SupportsDefault(Protocol):
    def get_default(self, source: Union[Value, Missing]) -> Value:
        ...


def is_annotated_class(
    obj: object,
) -> bool:
    return bool(obj and obj is not object and hasattr(obj, "__annotations__"))


def get_annotated_class(
    obj: object, *, name: str, base: AnnotatedClass
) -> Optional[AnnotatedClass]:
    if is_annotated_class(obj):
        return obj

    value = getattr(base, name, None)
    if is_annotated_class(value):
        return value

    return None


def get_annotations(
    annotated_class: AnnotatedClass,
) -> Generator[tuple[str, type, bool], None, None]:
    for base in reversed(annotated_class.__mro__):
        for name, annotation in get_type_hints(base, include_extras=True).items():
            if nested_class := get_annotated_class(annotation, name=name, base=base):
                yield name, nested_class, True
            yield name, annotation, False


def update_args(annotation: type, annotated_class: AnnotatedClass) -> None:
    for arg in get_args(annotation):
        if isinstance(arg, SupportsContext):
            arg.set_context(annotated_class)


def get_root_annotation(annotation: type) -> type:
    if origin := get_origin(annotation):
        return get_root_annotation(origin)
    return annotation


def unpack_annotations(
    value: Union[Value, Missing],
    *,
    annotation: type,
) -> tuple[object, type]:
    type_args = get_args(annotation)
    annotation = get_root_annotation(type_args[0])
    type_args = type_args[1:]

    if isinstance(value, Missing):
        for arg in type_args:
            if isinstance(arg, SupportsDefault):
                value = arg.get_default(value)

    if not isinstance(value, Missing):
        for arg in type_args:
            if isinstance(arg, AnnotatedArg):
                value = arg(value)

    return value, annotation
