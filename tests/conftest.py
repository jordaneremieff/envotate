# conftest.py
from __future__ import annotations

import builtins
import sys
from typing import Union

import pytest
import rich.traceback
from rich import print

pytest_plugins = "pytester"

# Override builtin print with rich print
builtins.print = print

rich.traceback.install()


@pytest.fixture()
def export_to_module(monkeypatch):
    """Set a variable in the test module namespace to allow testing decorated classes
    defined in a function body as nested classes using parameterized arguments for
    a particular test case. This is to avoid a 'NameError' when 'get_type_hints()'
    attempts to evaluate the annotations in the tests.
    """
    with monkeypatch.context() as m:

        sys.modules[__name__].__dict__.update({"Union": Union})

        def inner(cls_or_var, name=None, module=None):
            name = name or cls_or_var.__name__
            module = module or cls_or_var.__module__
            m.setitem(sys.modules[module].__dict__, name, cls_or_var)

        yield inner
    # return inner
