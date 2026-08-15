from __future__ import annotations

from pathlib import Path
from anti_slop.config import AntiSlopConfig


def test_is_ignored():
    config = AntiSlopConfig(ignore_patterns=[".venv/**", "tools/anti-slop/**"])
    assert config.is_ignored(Path(".venv/lib/python3.13/site-packages/foo.py"))
    assert config.is_ignored(Path("tools/anti-slop/rules/base.py"))
    assert not config.is_ignored(Path("src/myapp/main.py"))


def test_rule_enabled():
    config = AntiSlopConfig(rules={"no-chained-type-assertions": "error", "SLOP002": "off"})
    assert config.is_rule_enabled("no-chained-type-assertions", "SLOP001")
    assert not config.is_rule_enabled("no-conditional-empty-object-spread", "SLOP002")
