from __future__ import annotations

import ast
from typing import Any, Generator

from .engine import analyze_source


class AntiSlopFlake8Plugin:
    name = "anti-slop"
    version = "0.1.0"

    def __init__(self, tree: ast.AST, filename: str = "(none)", lines: list[str] | None = None) -> None:
        self.tree = tree
        self.filename = filename
        self.lines = lines or []

    def run(self) -> Generator[tuple[int, int, str, type[Any]], None, None]:
        source = "\n".join(self.lines)
        diagnostics = analyze_source(source, filename=self.filename)
        for diag in diagnostics:
            msg = f"{diag.code} [{diag.rule_id}] {diag.message}"
            yield (diag.location.lineno, diag.location.col_offset, msg, type(self))
