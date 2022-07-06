from __future__ import annotations

import logging
import os
import sys
from typing import (
    Annotated,
    Callable,
    Generator,
    Literal,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

__all__ = ["envotate"]


from envotate.errors import VariableError
from envotate.typing import (
    AnnotatedArg,
    Class,
    Value,
    get_root_arg,
    get_type_hints_with_extras,
    unpack_args,
)

FALSEY = {"false", "no", "n", "0"}
TRUTHY = {"true", "yes", "y", "1"}


logger = logging.getLogger(__name__)


def cast_or_raise(
    cls: type,
    name: str,
    value: Value,
    allowed_args: list[Union[Value, type]],
) -> Value:

    for annotation in allowed_args:
        if not isinstance(annotation, (type(None), type)):
            if value not in allowed_args:
                raise VariableError(
                    f"{cls.__name__}.{name} contains an invalid literal '{value}'.",
                    hint=f"One of {allowed_args} was expected.",
                )
            break
        if isinstance(annotation, type):
            try:
                value = annotation(value)
            except (TypeError, ValueError) as exc:
                if annotation == allowed_args[-1]:
                    raise VariableError(
                        f"{cls.__name__}.{name} could not be cast to "
                        f"{annotation.__name__}.",
                        hint=str(exc),
                    )
            else:
                break

    return value


def get_or_default(cls: type, name: str, *, required: bool) -> Value:
    if name in os.environ:
        value = os.environ[name]
    else:
        try:
            value = getattr(cls, name)
        except AttributeError:
            if required:
                raise VariableError(
                    f"{cls.__name__}.{name} is required but unset in the environment "
                    "and does not have a default."
                )
            value = None

        else:
            if callable(value):
                value = value()

    return value


def apply_metadata(
    cls: type, name: str, value: Value, annotation: type
) -> tuple[Value, type]:
    annotated_args = list(get_args(annotation))
    annotation = get_root_arg(annotated_args.pop(0))

    for arg in annotated_args:

        # Ignore arguments that do not conform to the supported interface.
        if not isinstance(arg, AnnotatedArg):
            logger.debug("Ignoring unrecognized annotated argument '%s'.", arg)
            continue

        # Allow uninstantiated arguments in the class definition.
        if isinstance(arg, type):
            arg = arg()

        # Apply the argument to the value.
        try:
            params = get_type_hints(arg.apply)
            if "value" not in params and "context" not in params:
                value = arg.apply()
            elif "value" in params and "context" in params:
                value = arg.apply(value, cls)
            elif "value" in params:
                value = arg.apply(value)
            else:
                value = arg.apply(cls)

        except (TypeError, ValueError) as exc:
            raise VariableError(
                f"{cls.__name__}.{name} could not be evaluated for "
                f"{arg.__class__.__module__}.{arg.__class__.__name__}.",
                hint=str(exc),
            )

    return value, annotation


def get_lookup_name(name: str, prefix: str, aliases: Optional[dict[str, str]]) -> str:
    if aliases and name in aliases:
        name = aliases[name]
    if prefix:
        name = f"{prefix}_{name}"

    return name


def load(
    cls: type,
    *,
    prefix: str,
    aliases: Optional[dict[str, str]],
) -> Generator[tuple[str, Union[Value, type]], None, None]:
    """Load the variables for the annotations in a class and its bases."""
    seen = set()
    for (name, annotation, nested) in get_type_hints_with_extras(cls):

        # Do not overwrite attributes set by a child class.
        if name in seen:
            continue
        seen.add(name)

        # Ignore any subscripted annotations except for context-specific metadata.
        origin = get_origin(annotation)
        if origin and origin not in (Literal, Annotated, Union):
            logger.debug(
                "%s.%s subscripts '%s' and will be ignored. "
                "The only special generic supported is 'typing.Annotated[...]'.",
                cls.__name__,
                name,
                origin,
            )
            continue

        if nested:
            if not hasattr(annotation, "__envotations__"):
                for _name, _value in load(annotation, prefix="", aliases=None):
                    setattr(annotation, _name, _value)
            yield name, annotation

        else:
            lookup_name = get_lookup_name(name, prefix, aliases)
            # unpacked = unpack_annotation(annotation)
            unpacked = unpack_args(annotation)
            value = get_or_default(
                cls, lookup_name, required=type(None) not in unpacked
            )

            # Annotated metadata types
            if origin is Annotated:
                value, annotation = apply_metadata(cls, name, value, annotation)

            # Boolean strings
            elif annotation is bool and not isinstance(value, bool):
                value = str(value).strip().lower()
                if value not in TRUTHY and value not in FALSEY:
                    raise VariableError(
                        f"{cls.__name__}.{name} contains an invalid boolean string.",
                        hint=(
                            f"Set one of {TRUTHY} to represent `True` or one of "
                            f"{FALSEY} to represent `False`."
                        ),
                    )
                value = bool(value in TRUTHY)

            # Optional value is missing
            if value is None:
                yield name, None

            else:
                # Literal value
                if value in unpacked:
                    yield name, value

                else:
                    value = cast_or_raise(cls, name, value, unpacked)
                    yield name, value


def configure(
    cls: type,
    /,
    *,
    prefix: str,
    aliases: Optional[dict[str, str]],
    export: Optional[set[str]],
) -> None:
    """Update the class attributes with the result of the load operation."""
    exported = {}
    cls.__envotations__ = set()  # type: ignore[attr-defined]
    for name, value in load(cls, prefix=prefix, aliases=aliases):
        setattr(cls, name, value)
        cls.__envotations__.add(name)  # type: ignore[attr-defined]
        if export and ("__all__" in export or name in export):
            exported[name] = value

    # Expose any configured class attributes in the module namespace.
    if exported:
        sys.modules[cls.__module__].__dict__.update(exported)


@overload
def envotate(__cls: type[Class], /) -> type[Class]:
    ...  # pragma: no cover


@overload
def envotate(
    *,
    prefix: str = ...,
    export: Optional[set[str]] = ...,
    aliases: Optional[dict[str, str]] = ...,
) -> Callable[[type[Class]], type[Class]]:
    ...  # pragma: no cover


def envotate(
    cls: Optional[type[Class]] = None,
    /,
    *,
    prefix: str = "",
    aliases: Optional[dict[str, str]] = None,
    export: Optional[set[str]] = None,
) -> Union[type[Class], Callable[[type[Class]], type[Class]]]:
    """Decorate a class to be configured from environment variables according to the
    type annotations of the class.

    **Options:**

    * **prefix** - A string prefix used to form the environment lookup key for each
    annotation discovered in the root class or any of its bases.
    * **aliases** - A mapping of class attributes and variable names to represent the
    specific environment lookup key to use instead of the attribute name.
    * **export** - A set of one or more class attributes to export as variables in the
    module namespace for the class. If the set consists of a single string '__all__'
    then all of the attributes will be exported.
    """

    def wrap(cls: type[Class]) -> type[Class]:
        configure(cls, prefix=prefix, aliases=aliases, export=export)

        return cls

    # Called as @envotate(...).
    if cls is None:
        return wrap

    # Called as @envotate.
    return wrap(cls)
