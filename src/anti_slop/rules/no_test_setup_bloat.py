from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import (
    enclosing_class,
    enclosing_function,
    get_annotation_name,
    get_dotted_name,
    is_any_or_object_annotation,
    is_test_file,
)

DEFAULT_MAX_TEST_KWARGS = 5
TEST_LIFECYCLE_METHODS = {"setup", "set_up", "setup_method", "setup_class", "teardown", "teardown_method", "teardown_class"}
TEST_HELPER_PREFIXES = ("make_", "build_", "create_test_", "fake_", "stub_")


def is_pascal_case_constructor(name: str | None) -> bool:
    """Check if the target callee name looks like a PascalCase class constructor."""
    if not name:
        return False
    base = name.split(".")[-1]
    return bool(base and base[0].isupper() and not base.isupper())


def is_test_function_or_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if the function is a test function or test lifecycle method."""
    name_lower = node.name.lower()
    if name_lower.startswith("test_") or name_lower in TEST_LIFECYCLE_METHODS:
        return True

    parent_cls = enclosing_class(node)
    if parent_cls and parent_cls.name.startswith("Test"):
        if name_lower.startswith("test") or name_lower in TEST_LIFECYCLE_METHODS:
            return True

    return False


def is_test_helper_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if a function definition appears to be a test builder/helper."""
    name_lower = node.name.lower()
    return name_lower.startswith(TEST_HELPER_PREFIXES)


class NoTestSetupBloatRule(BaseRule):
    rule_id = "no-test-setup-bloat"
    code = "SLOP023"
    description = (
        "Disallow excessive inline model instantiation in test functions (>5 kwargs); "
        "extract localized typed helper functions with baseline defaults."
    )

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if not is_test_file(context.filename):
            return

        max_kwargs = context.options.get("max_kwargs", DEFAULT_MAX_TEST_KWARGS)

        for node in ast.walk(context.tree):
            # 1. Check for excessive inline constructor kwargs inside test functions
            if isinstance(node, ast.Call):
                func_name = get_dotted_name(node.func)
                if is_pascal_case_constructor(func_name):
                    enclosing_fn = enclosing_function(node)
                    if enclosing_fn and is_test_function_or_method(enclosing_fn):
                        kwarg_count = len(node.keywords)
                        if kwarg_count > max_kwargs:
                            base_name = func_name.split(".")[-1] if func_name else "Model"
                            suggested_helper = f"make_{base_name.lower()}"
                            yield context.make_diagnostic(
                                node=node,
                                code=self.code,
                                rule_id=self.rule_id,
                                message=(
                                    f"Direct instantiation of `{func_name}` in test function `{enclosing_fn.name}` "
                                    f"has {kwarg_count} keyword arguments (max allowed: {max_kwargs}). "
                                    f"Extract a localized typed helper function (e.g. `{suggested_helper}(...)`) "
                                    "with baseline defaults to improve test signal-to-noise."
                                ),
                            )

            # 2. Check for untyped test helper definitions (missing return type or untyped **kwargs)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_test_helper_function(node):
                    # Check return type annotation
                    if node.returns is None:
                        yield context.make_diagnostic(
                            node=node,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=(
                                f"Test helper `{node.name}` is missing a return type annotation. "
                                "Provide a concrete domain return type."
                            ),
                        )
                    elif is_any_or_object_annotation(node.returns):
                        ret_name = get_annotation_name(node.returns)
                        yield context.make_diagnostic(
                            node=node.returns,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=(
                                f"Test helper `{node.name}` returns untyped `{ret_name}`. "
                                "Provide a concrete domain return type."
                            ),
                        )

                    # Check for untyped **kwargs
                    if node.args.kwarg is not None:
                        kwarg_node = node.args.kwarg
                        if kwarg_node.annotation is None or is_any_or_object_annotation(kwarg_node.annotation):
                            yield context.make_diagnostic(
                                node=kwarg_node,
                                code=self.code,
                                rule_id=self.rule_id,
                                message=(
                                    f"Test helper `{node.name}` uses untyped `**{kwarg_node.arg}`. "
                                    "Use typed keyword parameters or `typing.Unpack[TypedDict]` to preserve static type safety."
                                ),
                            )
