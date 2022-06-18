from __future__ import annotations


class NestedSettings:
    NESTED_INT: int = 2
    NESTED_STR: str = "nested"
    NESTED_BOOL: bool = False

    @classmethod
    def method(cls) -> int:
        return 123


class Settings:
    SETTINGS_INT: int = 1
    SETTINGS_STR: str = "settings"
    SETTINGS_BOOL: bool = True
    NESTED_SETTINGS: NestedSettings
