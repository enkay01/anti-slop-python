from __future__ import annotations

import ast
from dataclasses import dataclass

from anti_slop.shared.ast_utils import get_annotation_name

DICT_CONTAINER_NAMES = {
    "dict",
    "Dict",
    "typing.Dict",
    "Mapping",
    "typing.Mapping",
    "MutableMapping",
    "typing.MutableMapping",
    "OrderedDict",
    "typing.OrderedDict",
    "collections.OrderedDict",
    "defaultdict",
    "typing.DefaultDict",
    "collections.defaultdict",
}

UNSAFE_VALUE_NAMES = {
    "Any": "any",
    "typing.Any": "any",
    "object": "object",
    "builtins.object": "object",
    "dict": "empty-dict",
    "Dict": "empty-dict",
    "typing.Dict": "empty-dict",
}


@dataclass(frozen=True)
class UnsafeDictClassification:
    container: str
    unsafe_value: str


def is_unsafe_value_annotation(node: ast.AST | None, aliases: dict[str, ast.AST] | None = None) -> str | None:
    """Check if an annotation node represents an unsafe dictionary value like Any, object, or union with Any/object."""
    if node is None:
        return None

    name = get_annotation_name(node)
    if name and name in UNSAFE_VALUE_NAMES:
        return UNSAFE_VALUE_NAMES[name]

    # Python 3.10+ union: A | B
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left_unsafe = is_unsafe_value_annotation(node.left, aliases)
        right_unsafe = is_unsafe_value_annotation(node.right, aliases)
        if left_unsafe or right_unsafe:
            return "union"

    # Union[...]
    if isinstance(node, ast.Subscript):
        val_name = get_annotation_name(node.value)
        if val_name in {"Union", "typing.Union"}:
            if isinstance(node.slice, ast.Tuple):
                for elt in node.slice.elts:
                    if is_unsafe_value_annotation(elt, aliases):
                        return "union"
            elif is_unsafe_value_annotation(node.slice, aliases):
                return "union"

    # Check aliases
    if aliases and isinstance(node, ast.Name) and node.id in aliases:
        target = aliases[node.id]
        if target is not node:
            return is_unsafe_value_annotation(target, {k: v for k, v in aliases.items() if k != node.id})

    return None


def classify_unsafe_dict_annotation(
    node: ast.AST | None,
    aliases: dict[str, ast.AST] | None = None,
) -> UnsafeDictClassification | None:
    """Check if a type annotation is an unsafe dictionary like dict[str, Any] or Mapping[str, object]."""
    if node is None:
        return None

    if isinstance(node, ast.Subscript):
        container_name = get_annotation_name(node.value)
        if container_name in DICT_CONTAINER_NAMES:
            # Check slice arguments: dict[Key, Value]
            if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) >= 2:
                val_node = node.slice.elts[1]
                unsafe_val = is_unsafe_value_annotation(val_node, aliases)
                if unsafe_val is not None:
                    return UnsafeDictClassification(container=container_name, unsafe_value=unsafe_val)
            elif not isinstance(node.slice, ast.Tuple):
                # e.g. single arg or generic subscript
                unsafe_val = is_unsafe_value_annotation(node.slice, aliases)
                if unsafe_val is not None:
                    return UnsafeDictClassification(container=container_name, unsafe_value=unsafe_val)

    # Check if this is a type alias resolving to an unsafe dict
    if aliases and isinstance(node, ast.Name) and node.id in aliases:
        target = aliases[node.id]
        if target is not node:
            return classify_unsafe_dict_annotation(target, {k: v for k, v in aliases.items() if k != node.id})

    return None


def is_known_evidence_value(node: ast.AST) -> bool:
    """Check if an AST node is a syntactically established value (dict literal, list literal, constant, call, etc.)."""
    if isinstance(node, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
        return True
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Call, ast.JoinedStr, ast.Lambda)):
        return True
    if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
        return True
    return False
