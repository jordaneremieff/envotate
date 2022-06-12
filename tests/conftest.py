# conftest.py
import builtins
from rich import print
import rich.traceback

pytest_plugins = "pytester"

# Override builtin print with rich print
builtins.print = print

rich.traceback.install()
print("")
