from __future__ import annotations

import logging
import os
import sys
from typing import (
    Annotated,
    Callable,
    Generator,
    Optional,
    Union,
    get_args,
    get_origin,
    overload,
)

from envotate.exceptions import EnvTypeError, EnvValueError
from envotate.typing import (
    Arg,
    ArgWithCls,
    Value,
    Class,
    get_root_arg,
    get_type_hints_with_extras,
)

logger = logging.getLogger(__name__)


TRUTHY_VARS = {"true", "yes", "y", "1"}
FALSEY_VARS = {"false", "no", "n", "0"}


def validate(
    name: str,
    source: Value,
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


def get_or_default(cls: type, name: str) -> Value:
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


class Loader:
    def __init__(
        self, cls: type, /, *, prefix: str, export: Optional[set[str]] = None
    ) -> None:
        """Initialize the configuration options for a wrapped class and set a special
        attribute to ensure that it is not reconfigured if nested elsewhere.
        """
        setattr(cls, "__envotations__", set())
        self.cls = cls
        self.prefix = prefix
        self.export = export if export is not None else set()

    def __call__(self) -> None:
        """Update the class attributes with the result of the load operation."""
        exported = {}
        for name, value in self.load(self.cls, prefix=self.prefix):
            setattr(self.cls, name, value)
            self.cls.__dict__["__envotations__"].add(name)
            if "__all__" in self.export or name in self.export:
                exported[name] = value

        # Expose the exported class attributes in module scope.
        if exported:
            sys.modules[self.cls.__module__].__dict__.update(exported)

    def load(
        self, cls: type, *, prefix: str
    ) -> Generator[tuple[str, Union[type, Value]], None, None]:
        """Load and validate the corresponding environment variable or default value for
        all of the annotations in the provided root (or nested) class and its bases.
        """
        seen = set()
        for (name, annotation, nested) in get_type_hints_with_extras(cls):

            # Do not overwrite attributes set by a child class.
            if name in seen:
                continue
            seen.add(name)

            # Skip any subscripted annotations other than 'Annotated'.
            origin = get_origin(annotation)
            if origin is Annotated:
                for arg in get_args(annotation):
                    if isinstance(arg, ArgWithCls):
                        arg.set_cls(cls)
            elif origin is not None:
                logger.warning(
                    f"{name} is a subscripted annotation for '{origin}', but "
                    "only 'typing.Annotated[...]' is supported."
                )
                continue

            # Set the nested class on the immediate parent. If the nested class uses
            # the decorator then it will handle its own loading, otherwise recurse into
            # the nested class to populate the values.
            if nested:
                if not hasattr(annotation, "__envotations__"):
                    for nested_name, nested_value in self.load(annotation, prefix=""):
                        setattr(annotation, nested_name, nested_value)

                yield name, annotation

            # Retrieve the value from the environment.
            else:
                value = get_or_default(cls, f"{prefix}{name}")

                # Unpack the subscripted annotation to apply the context-specific
                # metadata and identify the root type.
                if origin:
                    annotated_args = list(get_args(annotation))
                    annotation = get_root_arg(annotated_args.pop(0))
                    for arg in annotated_args:
                        if isinstance(arg, Arg):
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


@overload
def envotate(__cls: type[Class], /) -> type[Class]:
    ...  # pragma: no cover


@overload
def envotate(
    *,
    prefix: str = ...,
    export: Optional[set[str]] = ...,
) -> Callable[[type[Class]], type[Class]]:
    ...  # pragma: no cover


def envotate(
    cls: Optional[type[Class]] = None,
    /,
    *,
    prefix: str = "",
    export: Optional[set[str]] = None,
) -> Union[type[Class], Callable[[type[Class]], type[Class]]]:
    """Decorate a class to be configured from the environment.

    **Parameters:**

    * **cls** - A class with annotations that will be used to validate and populate its
    attributes from either the environment or the class defaults. An attribute must
    be annot
    * **prefix** - A string prefix used to form the environment lookup key for each
    annotation (except nested classes) discovered in the root class or any of its
    bases. Default is `""`.
    * **export** - An optional set that contains one or more strings that identify the
    attributes that should be exported from the clas to the module namespace. If the set
    includes the special string `__all__` as the sole member then all attributes will be
    exported. Default is `None`.
    """

    def wrap(cls: type[Class]) -> type[Class]:
        loader = Loader(cls, prefix=prefix, export=export)
        loader()
        return cls

    # Called as @envotate(...).
    if cls is None:
        return wrap

    # Called as @envotate.
    return wrap(cls)
