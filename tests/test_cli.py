from __future__ import annotations

import json
from pathlib import Path
from anti_slop.cli import main


def test_cli_clean_code(tmp_path: Path, monkeypatch):
    test_file = tmp_path / "clean.py"
    test_file.write_text("x: int = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check", str(test_file)])
    assert exit_code == 0


def test_cli_violations(tmp_path: Path, monkeypatch, capsys):
    test_file = tmp_path / "violations.py"
    test_file.write_text("if x.__class__ is int:\n    pass\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check", str(test_file), "--format", "json"])
    assert exit_code == 1

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["code"] == "SLOP008"


def test_cli_init(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exit_code = main(["init"])
    assert exit_code == 0
    pyproject = tmp_path / "pyproject.toml"
    assert pyproject.exists()
    assert "[tool.anti-slop]" in pyproject.read_text(encoding="utf-8")
