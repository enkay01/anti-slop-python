from __future__ import annotations

import io
import tokenize
from dataclasses import dataclass


@dataclass(frozen=True)
class Comment:
    text: str
    lineno: int
    col_offset: int


def _fallback_scan_comments(source_code: str) -> list[Comment]:
    comments: list[Comment] = []
    for i, line in enumerate(source_code.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            comments.append(
                Comment(
                    text=stripped,
                    lineno=i,
                    col_offset=line.find("#"),
                )
            )
    return comments


def extract_comments(source_code: str) -> list[Comment]:
    """Extract all comments from Python source code using tokenize."""
    comments: list[Comment] = []
    try:
        tokens = tokenize.tokenize(io.BytesIO(source_code.encode("utf-8")).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comments.append(
                    Comment(
                        text=tok.string,
                        lineno=tok.start[0],
                        col_offset=tok.start[1],
                    )
                )
        return comments
    except (tokenize.TokenError, UnicodeDecodeError, Exception):
        return _fallback_scan_comments(source_code)
