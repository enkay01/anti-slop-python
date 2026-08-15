from __future__ import annotations

__version__ = "0.1.0"

from .config import AntiSlopConfig, load_config
from .engine import analyze_paths, analyze_source
from .models import Diagnostic, Location, Severity
from .rules import ALL_RULES, BaseRule

__all__ = [
    "__version__",
    "AntiSlopConfig",
    "Diagnostic",
    "Location",
    "Severity",
    "BaseRule",
    "ALL_RULES",
    "analyze_source",
    "analyze_paths",
    "load_config",
]
