import os

from typing import (
    Annotated,
    Any,
    Generator,
    Optional,
    Union,
    get_origin,
)

from envotate.typing import (
    AnnotatedClass,
    Value,
    Missing,
    is_annotated_class,
    get_annotations,
    unpack_annotations,
    update_args,
)
from envotate.exceptions import EnvTypeError, EnvValueError


__all__ = ["env", "Env"]


Env = Annotated


def get_value(
    name: str, *, annotation: type, annotated_class: type, origin: Optional[type]
) -> tuple[str, Value]:
    value = (
        os.environ[name]
        if name in os.environ
        else getattr(annotated_class, name, Missing())
    )

    # If the value is missing it still may be set by a default in an annotated type arg,
    # so unpack the annotation in this case and then proceed to handle any errors.
    if origin is Annotated:
        value, annotation = unpack_annotations(value, annotation=annotation)
    elif origin is not None:
        raise EnvTypeError(
            f"'{name}' is configured with an unsupported annotation '{origin}'."
        )
    if isinstance(value, Missing):
        raise EnvValueError(
            f"'{name}' was not found in the environment and does not set a default."
        )

    # Finalize the value by casting it to the expected type.
    if annotation is bool and origin is None:
        value = (
            str(value).strip().lower() in ("true", "yes", "y", "1") if value else False
        )
    elif not isinstance(value, annotation):
        try:
            value = annotation(value)
        except TypeError as exc:
            raise EnvTypeError(
                f"'{name}' received an supported value '{value}'.",
                hint=f"Can the value be cast to {annotation.__name__}?",
            ) from exc

    return name, value


def populate_class(
    annotated_class: AnnotatedClass,
) -> Generator[tuple[str, Value], None, None]:
    seen = set()
    for (name, annotation, is_nested) in get_annotations(annotated_class):

        # Do not overwrite attributes set by a child class.
        if name in seen:
            continue
        seen.add(name)

        # Only annotated metadata types are supported.
        origin = get_origin(annotation)
        if origin is Annotated:
            update_args(annotation, annotated_class)
        elif origin is not None:
            continue

        # Recursively populate a nested annotated class.
        if is_nested:
            yield from populate_class(annotation)

        # Retrieve and validate the value from the environment.
        yield get_value(
            name=name,
            annotation=annotation,
            annotated_class=annotated_class,
            origin=origin,
        )


def env(cls_or_var: Union[AnnotatedClass, str]) -> Union[AnnotatedClass, Any]:
    if is_annotated_class(cls_or_var):
        for name, value in populate_class(cls_or_var):
            setattr(cls_or_var, name, value)

    return cls_or_var


# TODO: Handle module level variables.
# class config:
#     def __init__(self) -> None:
#         pass


# def configure() -> Any:
#     pass
