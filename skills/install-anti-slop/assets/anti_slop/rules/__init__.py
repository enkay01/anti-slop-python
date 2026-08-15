from __future__ import annotations

from typing import Type

from anti_slop.rules.base import BaseRule
from anti_slop.rules.no_chained_type_assertions import NoChainedTypeAssertionsRule
from anti_slop.rules.no_conditional_empty_dict_spread import NoConditionalEmptyDictSpreadRule
from anti_slop.rules.no_known_value_widening import NoKnownValueWideningRule
from anti_slop.rules.no_module_mocking import NoModuleMockingRule
from anti_slop.rules.no_object_parameters import NoObjectParametersRule
from anti_slop.rules.no_reflect_apply import NoReflectApplyRule
from anti_slop.rules.no_reflect_get import NoReflectGetRule
from anti_slop.rules.no_runtime_typeof import NoRuntimeTypeofRule
from anti_slop.rules.no_shape_in_symbol_names import NoShapeInSymbolNamesRule
from anti_slop.rules.no_unknown_parameters import NoUnknownParametersRule
from anti_slop.rules.no_unknown_returns import NoUnknownReturnsRule
from anti_slop.rules.no_unknown_type_aliases import NoUnknownTypeAliasesRule
from anti_slop.rules.no_unsafe_dictionary_type import NoUnsafeDictionaryTypeRule
from anti_slop.rules.no_widen_then_assert import NoWidenThenAssertRule
from anti_slop.rules.require_safety_comment_for_cast import RequireSafetyCommentForCastRule

ALL_RULES: list[Type[BaseRule]] = [
    NoChainedTypeAssertionsRule,
    NoConditionalEmptyDictSpreadRule,
    NoKnownValueWideningRule,
    NoModuleMockingRule,
    NoObjectParametersRule,
    NoReflectApplyRule,
    NoReflectGetRule,
    NoRuntimeTypeofRule,
    NoShapeInSymbolNamesRule,
    NoUnknownParametersRule,
    NoUnknownReturnsRule,
    NoUnknownTypeAliasesRule,
    NoUnsafeDictionaryTypeRule,
    NoWidenThenAssertRule,
    RequireSafetyCommentForCastRule,
]

RULE_REGISTRY: dict[str, Type[BaseRule]] = {}
for rule_cls in ALL_RULES:
    RULE_REGISTRY[rule_cls.rule_id] = rule_cls
    RULE_REGISTRY[rule_cls.code] = rule_cls

__all__ = [
    "ALL_RULES",
    "RULE_REGISTRY",
    "BaseRule",
    "NoChainedTypeAssertionsRule",
    "NoConditionalEmptyDictSpreadRule",
    "NoKnownValueWideningRule",
    "NoModuleMockingRule",
    "NoObjectParametersRule",
    "NoReflectApplyRule",
    "NoReflectGetRule",
    "NoRuntimeTypeofRule",
    "NoShapeInSymbolNamesRule",
    "NoUnknownParametersRule",
    "NoUnknownReturnsRule",
    "NoUnknownTypeAliasesRule",
    "NoUnsafeDictionaryTypeRule",
    "NoWidenThenAssertRule",
    "RequireSafetyCommentForCastRule",
]
