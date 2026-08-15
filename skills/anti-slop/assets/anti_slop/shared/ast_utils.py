from __future__ import annotations

import ast


def add_parent_pointers(tree: ast.AST) -> None:
    """Attach parent references to all AST nodes."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "parent", parent)


def get_dotted_name(node: ast.AST | None) -> str | None:
    """Extract a full dotted name from ast.Name, ast.Attribute, etc."""
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        value_name = get_dotted_name(node.value)
        if value_name is not None:
            return f"{value_name}.{node.attr}"
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def is_call_to(node: ast.Call, target_names: set[str] | list[str]) -> bool:
    """Check if a Call node calls any of the specified target names."""
    targets = set(target_names)
    name = get_dotted_name(node.func)
    if name in targets:
        return True
    if isinstance(node.func, ast.Name) and node.func.id in targets:
        return True
    if isinstance(node.func, ast.Attribute) and node.func.attr in targets:
        return True
    return False


def is_cast_call(node: ast.Call) -> bool:
    """Check if a Call node is a typing.cast call."""
    return is_call_to(node, {"cast", "typing.cast"})


def get_annotation_name(node: ast.AST | None) -> str | None:
    """Return a normalized string representation of an annotation node."""
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        val = get_annotation_name(node.value)
        return f"{val}.{node.attr}" if val else node.attr
    if isinstance(node, ast.Subscript):
        val = get_annotation_name(node.value)
        slice_repr = get_annotation_name(node.slice)
        return f"{val}[{slice_repr}]" if (val and slice_repr) else val
    if isinstance(node, ast.Tuple):
        elts = [get_annotation_name(elt) or "_" for elt in node.elts]
        return ", ".join(elts)
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = get_annotation_name(node.left)
        right = get_annotation_name(node.right)
        return f"{left} | {right}"
    return None


def is_any_or_object_annotation(node: ast.AST | None) -> str | None:
    """Check if an annotation is Any or object, returning the matched kind."""
    if node is None:
        return None
    name = get_annotation_name(node)
    if name in {"Any", "typing.Any"}:
        return "Any"
    if name in {"object", "builtins.object"}:
        return "object"
    return None


def enclosing_function(node: ast.AST) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Find the nearest enclosing function for a node."""
    current = getattr(node, "parent", None)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
        current = getattr(current, "parent", None)
    return None


def enclosing_class(node: ast.AST) -> ast.ClassDef | None:
    """Find the nearest enclosing class for a node."""
    current = getattr(node, "parent", None)
    while current is not None:
        if isinstance(current, ast.ClassDef):
            return current
        current = getattr(current, "parent", None)
    return None


def is_typeguard_function(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if a function return annotation is TypeGuard[...] or TypeIs[...]."""
    if func.returns is None:
        return False
    ret_name = get_annotation_name(func.returns)
    if ret_name is None:
        return False
    return (
        ret_name.startswith("TypeGuard[")
        or ret_name.startswith("typing.TypeGuard[")
        or ret_name.startswith("typing_extensions.TypeGuard[")
        or ret_name.startswith("TypeIs[")
        or ret_name.startswith("typing.TypeIs[")
        or ret_name.startswith("typing_extensions.TypeIs[")
    )


def is_test_file(filename: str) -> bool:
    """Check if a filename is part of a test suite."""
    clean = filename.replace("\\", "/")
    if (
        "test_" in clean
        or "_test.py" in clean
        or "/tests/" in clean
        or clean.startswith("tests/")
        or "conftest.py" in clean
    ):
        return True
    return False


def is_public_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    filename: str,
) -> bool:
    """Determine if a function or method is public and subject to signature typing contracts."""
    if is_test_file(filename):
        return False
    # Private functions and methods start with '_'
    if node.name.startswith("_"):
        return False
    # Exclude @overload functions
    for dec in node.decorator_list:
        dec_name = get_dotted_name(dec)
        if dec_name in {"overload", "typing.overload"}:
            return False
    return True


def is_exact_type_check_expr(node: ast.AST) -> bool:
    """Check if an expression is an exact type identity comparison (type(x) is / __class__ is)."""
    if isinstance(node, ast.Compare):
        # 1. Left is type(x) call
        if isinstance(node.left, ast.Call):
            name = get_dotted_name(node.left.func)
            if name in {"type", "builtins.type"}:
                return True
        # 2. Left is x.__class__ attribute
        if isinstance(node.left, ast.Attribute) and node.left.attr == "__class__":
            return True
        # 3. Any comparator is type(x) or x.__class__
        for comp in node.comparators:
            if isinstance(comp, ast.Call) and get_dotted_name(comp.func) in {"type", "builtins.type"}:
                return True
            if isinstance(comp, ast.Attribute) and comp.attr == "__class__":
                return True
    return False


def is_single_statement_exact_type_helper(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Check if a function body structurally consists only of returning an exact type check."""
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if len(body) == 1 and isinstance(body[0], ast.Return) and body[0].value is not None:
        return is_exact_type_check_expr(body[0].value)
    return False
