from __future__ import annotations

import ast
from anti_slop.flake8_plugin import AntiSlopFlake8Plugin


def test_flake8_plugin():
    code = "class UserShape:\n    pass\n"
    tree = ast.parse(code)
    plugin = AntiSlopFlake8Plugin(tree, filename="test.py", lines=code.splitlines())
    results = list(plugin.run())
    assert len(results) == 1
    line, col, msg, _ = results[0]
    assert line == 1
    assert "SLOP009" in msg
