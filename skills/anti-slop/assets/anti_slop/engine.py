from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator

from .config import AntiSlopConfig
from .models import Diagnostic, Location
from .rules import ALL_RULES
from .rules.base import BaseRule, RuleContext
from .shared.ast_utils import add_parent_pointers
from .shared.comments import extract_comments


def collect_type_aliases(tree: ast.AST) -> dict[str, ast.AST]:
    """Collect type aliases defined in the module."""
    aliases: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        # Python 3.12+ `type X = Y`
        if hasattr(ast, "TypeAlias") and isinstance(node, getattr(ast, "TypeAlias")):
            name = getattr(node.name, "id", None) if isinstance(getattr(node, "name", None), ast.Name) else str(getattr(node, "name", ""))
            if name and getattr(node, "value", None):
                aliases[name] = node.value

        # `X: TypeAlias = Y`
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            aliases[node.target.id] = node.value

        # `X = Y` (if capitalized)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id[0].isupper():
                aliases[node.targets[0].id] = node.value

    return aliases


def analyze_source(
    source_code: str,
    filename: str = "<stdin>",
    config: AntiSlopConfig | None = None,
    rules: list[type[BaseRule]] | None = None,
) -> list[Diagnostic]:
    """Analyze a single Python source string and return all rule diagnostics."""
    cfg = config or AntiSlopConfig()
    active_rule_classes = rules or ALL_RULES

    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as e:
        # Return a diagnostic for syntax errors
        return [
            Diagnostic(
                code="SYNTAX",
                rule_id="syntax-error",
                message=f"Syntax error: {e.msg}",
                filename=filename,
                location=Location(lineno=e.lineno or 1, col_offset=e.offset or 0),
            )
        ]

    add_parent_pointers(tree)
    lines = source_code.splitlines()
    comments = extract_comments(source_code)
    aliases = collect_type_aliases(tree)

    diagnostics: list[Diagnostic] = []

    for rule_cls in active_rule_classes:
        rule_instance = rule_cls()
        if not cfg.is_rule_enabled(rule_instance.rule_id, rule_instance.code):
            continue

        rule_options = cfg.get_rule_options(rule_instance.rule_id, rule_instance.code)
        context = RuleContext(
            filename=filename,
            source_code=source_code,
            tree=tree,
            lines=lines,
            comments=comments,
            aliases=aliases,
            options=rule_options,
        )

        for diag in rule_instance.run(context):
            diagnostics.append(diag)

    diagnostics.sort(key=lambda d: (d.filename, d.location.lineno, d.location.col_offset))
    return diagnostics


def find_python_files(paths: list[Path], config: AntiSlopConfig, base_dir: Path) -> Iterator[Path]:
    """Find all .py files in paths that are not ignored."""
    for path in paths:
        if path.is_file():
            if path.suffix == ".py" and not config.is_ignored(path, base_dir):
                yield path
        elif path.is_dir():
            if config.is_ignored(path, base_dir):
                continue
            for child in path.rglob("*.py"):
                if not config.is_ignored(child, base_dir):
                    yield child


def analyze_paths(
    paths: list[Path],
    config: AntiSlopConfig,
    base_dir: Path | None = None,
) -> list[Diagnostic]:
    """Analyze multiple file paths or directories."""
    root = base_dir or Path.cwd()
    all_diagnostics: list[Diagnostic] = []

    for py_file in find_python_files(paths, config, root):
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception as e:
            all_diagnostics.append(
                Diagnostic(
                    code="IO",
                    rule_id="io-error",
                    message=f"Failed to read file: {e}",
                    filename=str(py_file),
                    location=Location(lineno=1, col_offset=0),
                )
            )
            continue

        file_diags = analyze_source(source, filename=str(py_file), config=config)
        all_diagnostics.extend(file_diags)

    all_diagnostics.sort(key=lambda d: (d.filename, d.location.lineno, d.location.col_offset))
    return all_diagnostics
