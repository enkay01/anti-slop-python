from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    OFF = "off"


@dataclass(frozen=True)
class Location:
    lineno: int
    col_offset: int
    end_lineno: int | None = None
    end_col_offset: int | None = None


@dataclass(frozen=True)
class Diagnostic:
    code: str
    rule_id: str
    message: str
    filename: str
    location: Location
    severity: Severity = Severity.ERROR
    context_line: str = ""

    def format_cli(self) -> str:
        loc = f"{self.filename}:{self.location.lineno}:{self.location.col_offset + 1}"
        header = f"{loc}: {self.code} [{self.rule_id}] {self.message}"
        if self.context_line:
            pointer = " " * self.location.col_offset + "^"
            return f"{header}\n    {self.context_line}\n    {pointer}"
        return header

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "rule_id": self.rule_id,
            "message": self.message,
            "filename": self.filename,
            "lineno": self.location.lineno,
            "col_offset": self.location.col_offset,
            "end_lineno": self.location.end_lineno,
            "end_col_offset": self.location.end_col_offset,
            "severity": self.severity.value,
        }
