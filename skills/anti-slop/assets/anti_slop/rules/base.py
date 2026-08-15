from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator

from ..models import Diagnostic, Location, Severity
from ..shared.comments import Comment


@dataclass
class RuleContext:
    filename: str
    source_code: str
    tree: ast.AST
    lines: list[str]
    comments: list[Comment]
    aliases: dict[str, ast.AST] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)

    def get_line(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1]
        return ""

    def make_diagnostic(
        self,
        node: ast.AST,
        code: str,
        rule_id: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
    ) -> Diagnostic:
        lineno = getattr(node, "lineno", 1)
        col_offset = getattr(node, "col_offset", 0)
        end_lineno = getattr(node, "end_lineno", lineno)
        end_col_offset = getattr(node, "end_col_offset", None)
        context_line = self.get_line(lineno)

        return Diagnostic(
            code=code,
            rule_id=rule_id,
            message=message,
            filename=self.filename,
            location=Location(
                lineno=lineno,
                col_offset=col_offset,
                end_lineno=end_lineno,
                end_col_offset=end_col_offset,
            ),
            severity=severity,
            context_line=context_line,
        )


class BaseRule(ABC):
    rule_id: str
    code: str
    description: str

    @abstractmethod
    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        """Execute the rule against the parsed AST and context."""
        raise NotImplementedError
