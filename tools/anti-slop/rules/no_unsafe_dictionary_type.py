from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.dictionary_types import classify_unsafe_dict_annotation


class NoUnsafeDictionaryTypeRule(BaseRule):
    rule_id = "no-unsafe-dictionary-type"
    code = "SLOP013"
    description = "Disallow dictionary contracts whose value type is Any, object, or union containing escape hatches."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            # Check AnnAssign, Function annotations, TypeAlias, etc.
            classification = classify_unsafe_dict_annotation(node, context.aliases)
            if classification is not None:
                # Avoid reporting child Subscript if parent is already a Subscript that was reported
                parent = getattr(node, "parent", None)
                if parent is not None and classify_unsafe_dict_annotation(parent, context.aliases) is not None:
                    continue

                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=f"This dictionary's `{classification.unsafe_value}` value type gives callers no concrete value contract. Use an owner/schema-derived value type; parse external payloads before insertion.",
                )
