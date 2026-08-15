from __future__ import annotations

import fnmatch
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        import tomllib  # type: ignore

DEFAULT_IGNORE_PATTERNS = [
    ".agent/**",
    ".agents/**",
    ".claude/**",
    ".codex/**",
    ".continue/**",
    ".cursor/**",
    ".gemini/**",
    ".git/**",
    ".hg/**",
    ".mypy_cache/**",
    ".opencode/**",
    ".pi/**",
    ".pytest_cache/**",
    ".roo/**",
    ".ruff_cache/**",
    ".tox/**",
    ".venv/**",
    ".windsurf/**",
    "__pycache__/**",
    "build/**",
    "dist/**",
    "env/**",
    "node_modules/**",
    "skills/**",
    "tools/anti-slop/**",
    "venv/**",
]


@dataclass
class AntiSlopConfig:
    ignore_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_PATTERNS))
    rules: dict[str, str | dict[str, Any]] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)

    def is_ignored(self, path: Path, base_dir: Path | None = None) -> bool:
        """Check whether a given path matches any ignore pattern."""
        if base_dir:
            try:
                rel_path = str(path.relative_to(base_dir)).replace(os.sep, "/")
            except ValueError:
                rel_path = str(path).replace(os.sep, "/")
        else:
            rel_path = str(path).replace(os.sep, "/")

        # Match path components and relative patterns
        for pattern in self.ignore_patterns:
            clean_pattern = pattern.rstrip("/")
            if fnmatch.fnmatch(rel_path, clean_pattern) or fnmatch.fnmatch(rel_path, pattern):
                return True
            if fnmatch.fnmatch(path.name, clean_pattern):
                return True
            # Match directory prefixes
            if "**" in pattern:
                prefix = pattern.split("/**")[0]
                if rel_path.startswith(prefix + "/") or rel_path == prefix:
                    return True
        return False

    def is_rule_enabled(self, rule_id: str, code: str) -> bool:
        """Check if a rule is enabled."""
        val = self.rules.get(rule_id) or self.rules.get(f"anti-slop/{rule_id}") or self.rules.get(code)
        if val is None:
            # Enabled by default unless explicitly turned off
            return True
        if isinstance(val, str):
            return val.lower() not in {"off", "false", "0", "disable"}
        if isinstance(val, dict):
            severity = val.get("severity", "error")
            return severity.lower() not in {"off", "false", "0", "disable"}
        return True

    def get_rule_options(self, rule_id: str, code: str) -> dict[str, Any]:
        """Get options configured for a specific rule."""
        val = self.rules.get(rule_id) or self.rules.get(f"anti-slop/{rule_id}") or self.rules.get(code)
        if isinstance(val, dict):
            return val.get("options", {})
        return self.options.get(rule_id, {}) or self.options.get(code, {})


def load_config(root_dir: Path | None = None) -> AntiSlopConfig:
    """Load configuration from pyproject.toml in root_dir or parent directories."""
    current = (root_dir or Path.cwd()).resolve()
    while current != current.parent:
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                tool_config = data.get("tool", {}).get("anti-slop", {})
                if tool_config:
                    ignores = tool_config.get("ignore_patterns", list(DEFAULT_IGNORE_PATTERNS))
                    rules = tool_config.get("rules", {})
                    options = tool_config.get("options", {})
                    return AntiSlopConfig(ignore_patterns=ignores, rules=rules, options=options)
            except Exception:
                pass
        current = current.parent
    return AntiSlopConfig()
