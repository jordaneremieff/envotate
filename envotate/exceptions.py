class EnvError(Exception):
    """Base error type for environment type or value errors."""

    context: dict

    def __init__(self, message: str, hint: str = "", **context: object) -> None:
        if hint:
            message = f"{message} ({hint})"
        self.context = context
        super().__init__(message)


class EnvValueError(EnvError, ValueError):
    """A value from either the configuration or the environment is invalid."""


class EnvTypeError(EnvError, TypeError):
    """A type from the configuration is invalid."""
