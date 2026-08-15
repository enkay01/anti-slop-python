from __future__ import annotations

from anti_slop.config import AntiSlopConfig
from anti_slop.engine import analyze_source
from anti_slop.models import Diagnostic


def check_code(source: str, rule_cls: type | None = None) -> list[Diagnostic]:
    """Helper to run checks on a snippet of Python code."""
    rules = [rule_cls] if rule_cls else None
    config = AntiSlopConfig(rules={rule_cls.rule_id: "error"}) if rule_cls else AntiSlopConfig()
    return analyze_source(source, filename="test_snippet.py", config=config, rules=rules)
