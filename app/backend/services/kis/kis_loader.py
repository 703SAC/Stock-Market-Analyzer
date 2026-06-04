"""Load open-trading-api domestic_stock functions without modifying upstream."""

from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from types import ModuleType

from config import EXAMPLES_USER_ROOT, DOMESTIC_STOCK_ROOT


def _ensure_paths() -> None:
    for path in (str(EXAMPLES_USER_ROOT), str(DOMESTIC_STOCK_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)


@lru_cache
def get_domestic_stock_module() -> ModuleType | None:
    """Import domestic_stock_functions from open-trading-api."""
    _ensure_paths()
    module_path = DOMESTIC_STOCK_ROOT / "domestic_stock_functions.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        "domestic_stock_functions",
        module_path,
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["domestic_stock_functions"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module
