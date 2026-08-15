from __future__ import annotations

from anti_slop.rules.no_excessive_parameters import NoExcessiveParametersRule
from tests.conftest import check_code


def test_excessive_parameters_flagged():
    code = """
def export_dataset(
    dataset_id: str,
    output_format: str,
    start_date: str,
    end_date: str,
    include_deleted: bool = False,
) -> None:
    pass
"""
    diags = check_code(code, NoExcessiveParametersRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP016"
    assert diags[0].rule_id == "no-excessive-parameters"


def test_options_model_allowed():
    code = """
from dataclasses import dataclass

@dataclass(frozen=True)
class ExportOptions:
    output_format: str
    start_date: str
    end_date: str
    include_deleted: bool = False

def export_dataset(dataset_id: str, options: ExportOptions) -> None:
    pass
"""
    diags = check_code(code, NoExcessiveParametersRule)
    assert len(diags) == 0
