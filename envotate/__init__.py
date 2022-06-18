from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Annotated, Any, Generator, Type, Union, get_args, get_origin

from envotate.exceptions import EnvTypeError, EnvValueError
from envotate.typing import (
    AnnotatedArg,
    Value,
    get_root_arg,
    iter_annotations,
    update_args,
)

logger = logging.getLogger(__name__)


Env = Annotated


TRUTHY_VARS = {"true", "yes", "y", "1"}
FALSEY_VARS = {"false", "no", "n", "0"}


def validate(
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


def get_or_default(cls: Type, name: str) -> Value:
    if name in os.environ:
        value = os.environ[name]
    else:
        try:
            value = getattr(cls, name)
        except AttributeError:
            raise EnvValueError(
                f"'{name}' is missing from the environment and does not have a default."
            )
        else:
            if callable(value):
                value = value()

    return value


@dataclass
class Envotation:
    prefix: str
    export: set[str]

    def __call__(self, cls: Type) -> Type:
        cls.__envotated__ = True

        # Retrieve, validate, and assign the values from the environment for each
        # annotation on the class.
        export_data = {}
        for name, value in self.load(cls):
            setattr(cls, name, value)

            # Collect the values to be exported from the class to the module namespace.
            if "__all__" in self.export or name in self.export:
                export_data[name] = value

        if export_data:
            sys.modules[cls.__module__].__dict__.update(export_data)

        return cls

    def load(self, cls: Type) -> Generator[tuple[str, Union[type, Value]], None, None]:
        seen = set()
        for (name, annotation, is_nested) in iter_annotations(cls):

            # Do not overwrite attributes set by a child class.
            if name in seen:
                continue
            seen.add(name)

            # Skip any subscripted annotations other than 'Annotated'.
            origin = get_origin(annotation)
            if origin is Annotated:
                update_args(annotation, cls)
            elif origin is not None:
                logger.warning(
                    f"{name} is a subscripted annotation for '{origin}', but "
                    "only 'typing.Annotated[...]' is supported."
                )
                continue

            # Retrieve the value from the environment.
            if not is_nested:

                value = get_or_default(cls, f"{self.prefix}{name}")

                # Unpack the subscripted annotation to apply the context-specific
                # metadata and identify the root type.
                if origin:
                    annotated_args = list(get_args(annotation))
                    annotation = get_root_arg(annotated_args.pop(0))
                    for arg in annotated_args:
                        if isinstance(arg, AnnotatedArg):
                            value = arg(value)

                # Convert a supported boolean string variable to the appropriate boolean
                # type value.
                elif annotation is bool and not isinstance(value, bool):
                    value = str(value).strip().lower()
                    if value not in TRUTHY_VARS and value not in FALSEY_VARS:
                        raise EnvValueError(
                            f"{name} expectes a boolean value, but '{value}' is not in "
                            f"{TRUTHY_VARS} or {FALSEY_VARS}."
                        )
                    value = bool(value in TRUTHY_VARS)

                yield name, validate(name, value, annotation)

            # Recurse into annotations for nested classes that have not been envotated.
            elif not hasattr(annotation, "__envotated__"):
                for nested_name, nested_value in self.load(annotation):
                    setattr(annotation, nested_name, nested_value)
                yield name, annotation

            # Nested envotations will handle their own loading.
            else:
                yield name, annotation


def envotate(
    cls: Type = None,
    /,
    *,
    prefix: str = "",
    export: Union[set[str], None] = None,
) -> Union[Type, Envotation]:
    if export is None:
        export = set()

    # Create a new envotation instance for the class.
    envotation = Envotation(prefix=prefix, export=export)

    # Called as @envotate(...)
    if cls is None:
        return envotation

    # Called as @envotate
    return envotation(cls)
