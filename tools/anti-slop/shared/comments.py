from __future__ import annotations

import io
import re
import tokenize
from dataclasses import dataclass

SAFETY_COMMENT_PATTERN = re.compile(r"#\s*SAFETY\s*:\s*\S+", re.IGNORECASE)


@dataclass(frozen=True)
class Comment:
    text: str
    lineno: int
    col_offset: int


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
    except Exception:
        # Fallback line-by-line scanning if tokenize encounters an encoding error
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


def has_safety_comment_for_node(
    comments: list[Comment],
    node_lineno: int,
    lookback_lines: int = 2,
) -> bool:
    """Check if there is a '# SAFETY:' comment on the same line or immediately preceding lines."""
    for c in comments:
        if (node_lineno - lookback_lines) <= c.lineno <= node_lineno:
            if SAFETY_COMMENT_PATTERN.search(c.text):
                return True
    return False
