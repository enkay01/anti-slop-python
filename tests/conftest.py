from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.models import Diagnostic


def check_code(source: str, rule_cls: type | None = None) -> list[Diagnostic]:
    """Helper to run checks on a snippet of Python code."""
    rules = [rule_cls] if rule_cls else None
    return analyze_source(source, filename="test_snippet.py", rules=rules)
