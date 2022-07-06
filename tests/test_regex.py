from __future__ import annotations

import re
from typing import Annotated

import pytest

from envotate import envotate
from envotate.errors import VariableError
from envotate.types import Regex
