from __future__ import annotations

import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from pprint import pformat
from typing import (
    Annotated,
    Callable,
    Generator,
    Literal,
    Optional,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

__all__ = ["envotate"]


from envotate.errors import AnnotationError, VariableError
from envotate.typing import AnnotatedArg, Class, Value, unpack_args

FALSEY = {"false", "no", "n", "0"}
TRUTHY = {"true", "yes", "y", "1"}


logger = logging.getLogger(__name__)


@dataclass
class Envotation:
    type: type
    path: str
    origin: Optional[type] = field(init=False)  # type: ignore[valid-type]
    args: list[type] = field(init=False, default_factory=list)  # type: ignore[valid-type]
    metadata: list[AnnotatedArg] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.origin = get_origin(self.type)
        if self.origin is Annotated:
            self.args = unpack_args(self.type)
            args = list(get_args(self.type))
            self.type = args.pop(0)
            # self.origin = get_origin(self.type)
            for arg in args:
                if not isinstance(arg, AnnotatedArg):
                    logger.debug("Ignoring unrecognized annotated argument '%s'.", arg)
                    continue
                if isinstance(arg, type):
                    arg = cast(AnnotatedArg, arg())
                self.metadata.append(arg)

        if self.origin in (Literal, Union, Annotated):
            self.args = unpack_args(self.type)
        elif self.origin is not None:
            raise AnnotationError(
                f"'{self.origin}' is not a supported type form.",
                hint=(
                    "An origin may only be one of Literal, Union, Optional, "
                    "or Annotated."
                ),
            )

    # def __repr__(self) -> str:
    #     return pformat(self.dump())

    @property
    def is_literal(self) -> bool:
        return self.origin is Literal

    @property
    def is_union(self) -> bool:
        return self.origin is Union

    @property
    def is_optional(self) -> bool:
        if self.is_union and type(None) in self.args:
            return True
        return False

    @property
    def is_bool(self) -> bool:
        return self.type is bool

    def cast(self, value: Value) -> Value:
        try:
            value = self.type(value)
        except (TypeError, ValueError) as exc:
            if self.args and self.type != self.args[-1]:
                value = None
            else:
                raise AnnotationError(
                    f"'{self.path} could not be cast to " f"{self.type.__qualname__}.",
                    hint=str(exc),
                )

        return value

    def dump(self) -> dict[str, Union[Value, type]]:  # type: ignore[valid-type]
        return asdict(self)


@dataclass
class Resolver:
    prefix: Optional[str]
    aliases: Optional[dict[str, str]]
    export: Optional[set[str]]

    def resolve(
        self,
        cls: type[Class],
        path: Optional[str] = None,
    ) -> Generator[tuple[str, Union[Value, type]], None, None]:
        seen = set()
        for base in cls.__mro__:
            if not base or base is object:
                continue
            for attribute, annotation in get_type_hints(
                base,
                include_extras=True,
            ).items():
                if attribute in seen:
                    continue
                seen.add(attribute)

                if hasattr(annotation, "__envotations__"):
                    yield attribute, annotation
                elif getattr(annotation, "__annotations__", None):
                    annotation.__envotations__ = set()
                    for _attr, _val in self.resolve(annotation, path=base.__qualname__):
                        setattr(annotation, _attr, _val)
                        annotation.__envotations__.add(_attr)
                    yield attribute, annotation

                else:
                    yield attribute, self.get(
                        cls=base,
                        path=path,
                        attribute=attribute,
                        annotation=annotation,
                    )

    def get(
        self,
        *,
        cls: type[Class],
        attribute: str,
        annotation: type,
        path: Optional[str] = None,
    ) -> Value:
        name = attribute
        path = f"{path}.{name}" if path is not None else attribute
        envotation = Envotation(annotation, path)

        if self.aliases and path in self.aliases:
            name = self.aliases[path]
        if self.prefix:
            name = f"{self.prefix}_{name}"

        # FIXME: Optional type vs. check for default vs. needs to exist in env, etc.
        value = os.environ.get(name, getattr(cls, attribute, None))
        if value is None:
            if not envotation.is_optional:
                raise VariableError(
                    f"'{path}' is required but missing from the environment and has "
                    "not set a default."
                )
            return value

        if callable(value):
            value = value()

        if envotation.metadata:
            for arg in envotation.metadata:
                try:
                    params = get_type_hints(arg.apply)
                    if "value" not in params and "context" not in params:
                        value = arg.apply()  # type: ignore[assignment]
                    elif "value" in params and "context" in params:
                        value = arg.apply(value, cls)  # type: ignore[assignment]
                    elif "value" in params:
                        value = arg.apply(value)  # type: ignore[assignment]
                    else:
                        value = arg.apply(cls)  # type: ignore[assignment]
                except (TypeError, ValueError) as exc:
                    arg_path = arg.__class__.__qualname__
                    raise VariableError(
                        f"'{path}' could not be evaluated for '{arg_path}'.",
                        hint=str(exc),
                    )

        if envotation.is_bool and not isinstance(value, bool):
            if str(value).strip().lower() not in TRUTHY | FALSEY:
                raise VariableError(
                    f"{path} is an invalid boolean.",
                    hint=(
                        f"Set one of {TRUTHY} to represent `True` or one of "
                        f"{FALSEY} to represent `False`."
                    ),
                )
            return bool(value in TRUTHY)

        if envotation.is_literal and value in envotation.args:
            return value

        if envotation.args:
            for arg in envotation.args:
                if not isinstance(arg, (type(None), type)):
                    if value not in envotation.args:
                        raise VariableError(
                            f"'{path}' contains an invalid literal '{value}'.",
                            hint=f"One of {envotation.args} was expected.",
                        )
                    break
                if isinstance(envotation.type, type):
                    if value := envotation.cast(value):  # type: ignore[assignment]
                        break

            return value

        return envotation.cast(value)


def configure(
    cls: type,
    /,
    *,
    prefix: Optional[str],
    aliases: Optional[dict[str, str]],
    export: Optional[set[str]],
) -> None:
    """Update the class attributes with the result of the load operation."""

    cls.__envotations__ = set()  # type: ignore[attr-defined]
    exportable = {}
    resolver = Resolver(
        prefix=prefix,
        aliases=aliases,
        export=export,
    )
    for attribute, value in resolver.resolve(cls):
        setattr(cls, attribute, value)
        cls.__envotations__.add(attribute)  # type: ignore[attr-defined]
        if export and attribute in export or export == {"__all__"}:
            exportable[attribute] = value

    if exportable:
        sys.modules[cls.__module__].__dict__.update(exportable)


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
    prefix: Optional[str] = None,
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
        configure(
            cls,
            prefix=prefix,
            aliases=aliases,
            export=export,
        )

        return cls

    # Called as @envotate(...).
    if cls is None:
        return wrap

    # Called as @envotate.
    return wrap(cls)
