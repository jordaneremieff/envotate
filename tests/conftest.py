# conftest.py
from __future__ import annotations

import builtins

import rich.traceback
from rich import print

pytest_plugins = "pytester"

# Override builtin print with rich print
builtins.print = print

rich.traceback.install()
print(" ")
