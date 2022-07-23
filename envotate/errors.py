from __future__ import annotations


class Error(Exception):
    """Base exception class to provide message hints."""

    def __init__(self, message: str, hint: str = "") -> None:
        if hint:
            message = f"{message} ({hint})"
        super().__init__(message)


class VariableError(Error):
    """A variable is missing, invalid, or not supported for its expected type."""


class AnnotationError(Error):
    """An annotation is unsupported or invalid."""
