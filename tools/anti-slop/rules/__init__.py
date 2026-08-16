from __future__ import annotations

from typing import Type

from anti_slop.rules.base import BaseRule
from anti_slop.rules.no_assert_validation import NoAssertValidationRule
from anti_slop.rules.no_assertionless_test import NoAssertionlessTestRule
from anti_slop.rules.no_chained_type_assertions import NoChainedTypeAssertionsRule
from anti_slop.rules.no_conditional_empty_dict_spread import NoConditionalEmptyDictSpreadRule
from anti_slop.rules.no_excessive_optional_fields import NoExcessiveOptionalFieldsRule
from anti_slop.rules.no_excessive_parameters import NoExcessiveParametersRule
from anti_slop.rules.no_known_value_widening import NoKnownValueWideningRule
from anti_slop.rules.no_module_mocking import NoModuleMockingRule
from anti_slop.rules.no_mutable_default_arguments import NoMutableDefaultArgumentsRule
from anti_slop.rules.no_object_parameters import NoObjectParametersRule
from anti_slop.rules.no_opaque_test_names import NoOpaqueTestNamesRule
from anti_slop.rules.no_private_member_test_access import NoPrivateMemberTestAccessRule
from anti_slop.rules.no_reflect_apply import NoReflectApplyRule
from anti_slop.rules.no_reflect_get import NoReflectGetRule
from anti_slop.rules.no_runtime_typeof import NoRuntimeTypeofRule
from anti_slop.rules.no_shape_in_symbol_names import NoShapeInSymbolNamesRule
from anti_slop.rules.no_silent_exception_swallow import NoSilentExceptionSwallowRule
from anti_slop.rules.no_silent_test_except import NoSilentTestExceptRule
from anti_slop.rules.no_tautological_assert import NoTautologicalAssertRule
from anti_slop.rules.no_test_print import NoTestPrintRule
from anti_slop.rules.no_test_setup_bloat import NoTestSetupBloatRule
from anti_slop.rules.no_test_sleep import NoTestSleepRule
from anti_slop.rules.no_unknown_parameters import NoUnknownParametersRule
from anti_slop.rules.no_unknown_returns import NoUnknownReturnsRule
from anti_slop.rules.no_unknown_type_aliases import NoUnknownTypeAliasesRule
from anti_slop.rules.no_unnamed_tuple_returns import NoUnnamedTupleReturnsRule
from anti_slop.rules.no_unsafe_dictionary_type import NoUnsafeDictionaryTypeRule
from anti_slop.rules.no_widen_then_assert import NoWidenThenAssertRule
from anti_slop.rules.require_keyword_only_booleans import RequireKeywordOnlyBooleansRule
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
    NoExcessiveParametersRule,
    RequireKeywordOnlyBooleansRule,
    NoSilentExceptionSwallowRule,
    NoUnnamedTupleReturnsRule,
    NoAssertValidationRule,
    NoMutableDefaultArgumentsRule,
    NoExcessiveOptionalFieldsRule,
    NoTestSetupBloatRule,
    NoTautologicalAssertRule,
    NoAssertionlessTestRule,
    NoSilentTestExceptRule,
    NoOpaqueTestNamesRule,
    NoTestSleepRule,
    NoTestPrintRule,
    NoPrivateMemberTestAccessRule,
]

RULE_REGISTRY: dict[str, Type[BaseRule]] = {}
for rule_cls in ALL_RULES:
    RULE_REGISTRY[rule_cls.rule_id] = rule_cls
    RULE_REGISTRY[rule_cls.code] = rule_cls

__all__ = [
    "ALL_RULES",
    "RULE_REGISTRY",
    "BaseRule",
    "NoAssertValidationRule",
    "NoAssertionlessTestRule",
    "NoChainedTypeAssertionsRule",
    "NoConditionalEmptyDictSpreadRule",
    "NoExcessiveOptionalFieldsRule",
    "NoExcessiveParametersRule",
    "NoKnownValueWideningRule",
    "NoModuleMockingRule",
    "NoMutableDefaultArgumentsRule",
    "NoObjectParametersRule",
    "NoOpaqueTestNamesRule",
    "NoPrivateMemberTestAccessRule",
    "NoReflectApplyRule",
    "NoReflectGetRule",
    "NoRuntimeTypeofRule",
    "NoShapeInSymbolNamesRule",
    "NoSilentExceptionSwallowRule",
    "NoSilentTestExceptRule",
    "NoTautologicalAssertRule",
    "NoTestPrintRule",
    "NoTestSetupBloatRule",
    "NoTestSleepRule",
    "NoUnknownParametersRule",
    "NoUnknownReturnsRule",
    "NoUnknownTypeAliasesRule",
    "NoUnnamedTupleReturnsRule",
    "NoUnsafeDictionaryTypeRule",
    "NoWidenThenAssertRule",
    "RequireKeywordOnlyBooleansRule",
    "RequireSafetyCommentForCastRule",
]
