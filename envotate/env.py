import os
import sys
import importlib
import logging
from typing import (
    Annotated,
    Any,
    Generator,
    Optional,
    Union,
    get_args,
    get_origin,
)

from envotate.typing import (
    AnnotatedArg,
    AnnotatedClass,
    SupportsDefault,
    Value,
    Missing,
    get_root_arg,
    iter_annotations,
    update_args,
)
from envotate.exceptions import EnvTypeError, EnvValueError


__all__ = ["env", "Env"]

logger = logging.getLogger(__name__)


Env = Annotated


BOOLEAN_TRUE_VALUES = {"true", "yes", "y", "1"}
BOOLEAN_FALSE_VALUES = {"false", "no", "n", "0"}


def cast_variable(
    name: str,
    source: Any,
    annotation: type,
) -> Value:
    try:
        value = annotation(source)
    except (ValueError, TypeError) as exc:
        raise EnvTypeError(
            f"'{name}' does not support the provided source value.",
            hint=f"Can the value be cast to {annotation.__name__}?",
        ) from exc

    return value


def load_variable(
    name: str,
    annotation: type,
    annotated_class: AnnotatedClass,
    origin: Optional[type],
) -> tuple[str, Value]:
    source: Any = os.environ.get(name, getattr(annotated_class, name, Missing()))
    if not origin and isinstance(source, Missing):
        raise EnvValueError(
            f"'{name}' is missing from the environment but does not assign a default."
        )

    if origin:
        annotated_args = list(get_args(annotation))
        annotation = get_root_arg(annotated_args.pop(0))
        if isinstance(annotated_args[-1], SupportsDefault):
            default_arg = annotated_args.pop()
            if isinstance(source, Missing):
                source = default_arg.get_default()
        elif isinstance(source, Missing):
            raise EnvValueError(
                f"{name} is missing from the environment but does not include a "
                "'Default' metadata argument."
            )
        for arg in annotated_args:
            if isinstance(arg, AnnotatedArg):
                source = arg(source)

    elif annotation is bool:
        source = str(source).strip().lower()
        if source not in BOOLEAN_TRUE_VALUES and source not in BOOLEAN_FALSE_VALUES:
            raise EnvValueError(
                f"{name} expectes a boolean value, but '{source}' is not in "
                f"{BOOLEAN_TRUE_VALUES} or {BOOLEAN_FALSE_VALUES}."
            )
        source = bool(source in BOOLEAN_TRUE_VALUES)

    return name, cast_variable(name, source, annotation)


def iter_variables(
    annotated_class: AnnotatedClass,
) -> Generator[tuple[str, Union[type, Value]], None, None]:
    seen = set()
    for (name, annotation, is_nested) in iter_annotations(annotated_class):

        # Do not overwrite attributes set by a child class.
        if name in seen:
            continue
        seen.add(name)

        # Skip any subscripted annotations other than 'Annotated'.
        origin = get_origin(annotation)
        if origin is Annotated:
            update_args(annotation, annotated_class)
        elif origin is not None:
            logger.warning(
                f"{name} is a subscripted annotation for '{origin}', but "
                "only 'typing.Annotated[...]' is supported."
            )
            continue

        # Recursively populate a nested annotated class, or retrieve the validated value
        # for the current annotation.
        if is_nested:
            populate_class(annotation)
            yield name, annotation
        else:
            yield load_variable(name, annotation, annotated_class, origin)


def populate_class(annotated_class: AnnotatedClass) -> AnnotatedClass:
    for name, value in iter_variables(annotated_class):
        setattr(annotated_class, name, value)

    return annotated_class


def populate_module(module_name: str) -> AnnotatedClass:
    annotated_module = importlib.import_module(module_name)
    annotated_class = type(
        module_name,
        (),
        {
            **{"__annotations__": annotated_module.__annotations__},
            **{
                k: v
                for k, v in annotated_module.__dict__.items()
                if not k.startswith("_") and not callable(v)
            },
        },
    )
    populate_class(annotated_class)
    sys.modules[module_name].__dict__.update(**annotated_class.__dict__)

    return annotated_class


def env(configuration: Union[AnnotatedClass, str]) -> AnnotatedClass:
    if isinstance(configuration, str):
        annotated_class = populate_module(configuration)
    else:
        annotated_class = populate_class(configuration)

    return annotated_class
