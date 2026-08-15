from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name

SPARSE_CLASS_NAME_SUFFIXES = {
    "patch",
    "update",
    "filter",
    "filters",
    "query",
    "options",
    "partial",
    "delta",
}


def is_sparse_class_name(name: str) -> bool:
    lower = name.lower()
    return any(lower.endswith(suffix) or f"{suffix}_" in lower for suffix in SPARSE_CLASS_NAME_SUFFIXES)


def is_optional_annotation(annotation: ast.AST | None) -> bool:
    if annotation is None:
        return False

    # 1. `T | None` or `None | T`
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        left_name = get_annotation_name(annotation.left)
        right_name = get_annotation_name(annotation.right)
        if left_name == "None" or right_name == "None":
            return True
        return is_optional_annotation(annotation.left) or is_optional_annotation(annotation.right)

    # 2. `Optional[T]` or `Union[T, None]`
    if isinstance(annotation, ast.Subscript):
        base_name = get_annotation_name(annotation.value)
        if base_name in {"Optional", "typing.Optional"}:
            return True
        if base_name in {"Union", "typing.Union"}:
            if isinstance(annotation.slice, ast.Tuple):
                for elt in annotation.slice.elts:
                    if get_annotation_name(elt) == "None":
                        return True
            elif get_annotation_name(annotation.slice) == "None":
                return True

    return False


def count_null_check_clauses(node: ast.AST) -> int:
    """Count 'x is None' or 'x is not None' comparisons in a BoolOp expression."""
    count = 0
    if isinstance(node, ast.BoolOp):
        for value in node.values:
            if isinstance(value, ast.Compare):
                for op, comp in zip(value.ops, value.comparators):
                    if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(comp, ast.Constant) and comp.value is None:
                        count += 1
            elif isinstance(value, ast.BoolOp):
                count += count_null_check_clauses(value)
    return count


class NoExcessiveOptionalFieldsRule(BaseRule):
    rule_id = "no-excessive-optional-fields"
    code = "SLOP022"
    description = (
        "Disallow classes with excessive optional fields (>50% and >=3 fields) and massive null-check chains; "
        "parse raw inputs directly into complete domain entities at the boundary."
    )

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            # 1. Check Class Definitions (dataclasses, models, records)
            if isinstance(node, ast.ClassDef):
                if is_sparse_class_name(node.name):
                    continue

                total_fields = 0
                optional_fields = 0

                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        # Exclude ClassVar or private fields
                        if item.target.id.startswith("__"):
                            continue
                        total_fields += 1
                        if is_optional_annotation(item.annotation):
                            optional_fields += 1

                if total_fields >= 3 and optional_fields >= 3:
                    ratio = optional_fields / total_fields
                    if ratio >= 0.5:
                        pct = int(ratio * 100)
                        yield context.make_diagnostic(
                            node=node,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=(
                                f"Class `{node.name}` has {optional_fields}/{total_fields} optional fields ({pct}%). "
                                "Avoid anemic partial models where most fields are nullable. "
                                "Parse raw boundary data directly into complete domain entities."
                            ),
                        )

            # 2. Check for massive compound null-check chains (>=4 clauses)
            elif isinstance(node, ast.If):
                null_checks = count_null_check_clauses(node.test)
                if null_checks >= 4:
                    yield context.make_diagnostic(
                        node=node.test,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=(
                            f"Compound condition contains {null_checks} null checks. "
                            "Massive null-check chains indicate unparsed partial data. "
                            "Parse and validate records at the I/O boundary before passing to domain logic."
                        ),
                    )
