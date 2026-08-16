from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import enclosing_class, get_dotted_name, is_test_file

ASSERTION_CONTEXT_MANAGERS = {
    "pytest.raises",
    "pytest.warns",
    "pytest.deprecated_call",
    "self.assertRaises",
    "self.assertRaisesRegex",
    "self.assertWarns",
    "self.assertWarnsRegex",
    "self.assertLogs",
}

ASSERTION_CALL_PREFIXES = (
    "assert_",
    "self.assert",
)

ASSERTION_EXACT_CALLS = {
    "pytest.fail",
    "pytest.skip",
    "self.fail",
    "self.skipTest",
    "assert_that",
    "assert_frame_equal",
    "assert_series_equal",
    "assert_array_equal",
    "assert_allclose",
}


def is_test_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if node is a test function or method."""
    if node.name.startswith("test"):
        return True

    parent_cls = enclosing_class(node)
    if parent_cls and parent_cls.name.startswith("Test"):
        return True

    return False


def is_abstract_or_empty_stub(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function is an abstract method or pure stub (... or pass)."""
    for dec in node.decorator_list:
        dec_name = get_dotted_name(dec)
        if dec_name in {"abstractmethod", "abc.abstractmethod"}:
            return True

    body = node.body
    # Strip leading docstring if present
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]

    if not body:
        return True

    if len(body) == 1:
        stmt = body[0]
        if isinstance(stmt, ast.Pass):
            return True
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
            return True
        if isinstance(stmt, ast.Raise):
            exc = stmt.exc
            if exc is not None:
                exc_name = get_dotted_name(exc if not isinstance(exc, ast.Call) else exc.func)
                if exc_name in {"NotImplementedError", "builtins.NotImplementedError"}:
                    return True

    return False


def has_assertions_or_expectations(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function body contains any assert statements, context managers, or assertion calls."""
    for child in ast.walk(node):
        # 1. Direct assert statement
        if isinstance(child, ast.Assert):
            return True

        # 2. Context manager: with pytest.raises(...):
        if isinstance(child, (ast.With, ast.AsyncWith)):
            for item in child.items:
                ctx_expr = item.context_expr
                func_node = ctx_expr.func if isinstance(ctx_expr, ast.Call) else ctx_expr
                name = get_dotted_name(func_node)
                if name:
                    if name in ASSERTION_CONTEXT_MANAGERS:
                        return True
                    if any(name.endswith(f".{cm}") for cm in ("raises", "warns", "assertRaises", "assertRaisesRegex")):
                        return True

        # 3. Method / function calls: mock.assert_called_once(), self.assertEqual(), pytest.fail()
        if isinstance(child, ast.Call):
            call_name = get_dotted_name(child.func)
            if call_name:
                if call_name in ASSERTION_EXACT_CALLS:
                    return True
                if any(call_name.startswith(pfx) for pfx in ASSERTION_CALL_PREFIXES):
                    return True
                # Method call ending in assert methods: e.g. mock.assert_called() or checker.assert_valid()
                func_attr = getattr(child.func, "attr", None)
                if func_attr and func_attr.startswith("assert_"):
                    return True

    return False


class NoAssertionlessTestRule(BaseRule):
    rule_id = "no-assertionless-test"
    code = "SLOP025"
    description = "Disallow test functions that perform no assertions or exception checks (line hitter anti-pattern)."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if not is_test_file(context.filename):
            return

        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            if not is_test_function(node):
                continue

            if is_abstract_or_empty_stub(node):
                continue

            if not has_assertions_or_expectations(node):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        f"Test function `{node.name}` contains no assertions, `pytest.raises`, or verification calls. "
                        "Add explicit domain assertions to verify observable behavior."
                    ),
                )
