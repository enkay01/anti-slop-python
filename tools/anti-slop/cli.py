from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Bootstrap sys.path for direct vendored execution (e.g. python3 tools/anti-slop/cli.py)
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from anti_slop import __version__  # noqa: E402
from anti_slop.config import load_config  # noqa: E402
from anti_slop.engine import analyze_paths  # noqa: E402
from anti_slop.models import Diagnostic  # noqa: E402


def init_command(target_dir: Path) -> int:
    """Initialize or update pyproject.toml with default anti-slop configuration."""
    pyproject = target_dir / "pyproject.toml"
    config_snippet = """
[tool.anti-slop]
ignore_patterns = [
    ".agent/**",
    ".agents/**",
    ".claude/**",
    ".codex/**",
    ".continue/**",
    ".cursor/**",
    ".gemini/**",
    ".git/**",
    ".opencode/**",
    ".pi/**",
    ".roo/**",
    ".venv/**",
    ".windsurf/**",
    "tools/anti-slop/**",
]

[tool.anti-slop.rules]
"no-chained-type-assertions" = "error"
"no-conditional-empty-object-spread" = "error"
"no-known-value-widening" = "error"
"no-module-mocking" = "error"
"no-object-parameters" = "error"
"no-reflect-apply" = "error"
"no-reflect-get" = "error"
"no-runtime-typeof" = "error"
"no-shape-in-symbol-names" = "error"
"no-unknown-parameters" = "error"
"no-unknown-returns" = "error"
"no-unknown-type-aliases" = "error"
"no-unsafe-dictionary-type" = "error"
"no-widen-then-assert" = "error"
"require-safety-comment-for-type-assertion" = "error"
"no-excessive-parameters" = "error"
"require-keyword-only-booleans" = "error"
"no-silent-exception-swallow" = "error"
"no-unnamed-tuple-returns" = "error"
"no-assert-validation" = "error"
"no-mutable-default-arguments" = "error"
"no-excessive-optional-fields" = "error"
"""
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        if "[tool.anti-slop]" in content:
            print(f"Anti-slop configuration already present in {pyproject}")
            return 0
        with open(pyproject, "a", encoding="utf-8") as f:
            f.write(config_snippet)
        print(f"Appended anti-slop configuration to {pyproject}")
    else:
        with open(pyproject, "w", encoding="utf-8") as f:
            f.write(config_snippet.lstrip())
        print(f"Created {pyproject} with anti-slop configuration")
    return 0


def format_text(diagnostics: list[Diagnostic]) -> str:
    """Format diagnostics into human-readable text."""
    if not diagnostics:
        return ""
    lines = [d.format_cli() for d in diagnostics]
    summary = f"\nFound {len(diagnostics)} violation{'s' if len(diagnostics) != 1 else ''}."
    return "\n\n".join(lines) + summary


def format_json(diagnostics: list[Diagnostic]) -> str:
    """Format diagnostics as JSON."""
    return json.dumps([d.to_dict() for d in diagnostics], indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anti-slop",
        description="Opinionated Python rules that reject low-evidence and low-signal patterns.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # check subcommand
    check_parser = subparsers.add_parser("check", help="Check python files for anti-slop violations.")
    check_parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to check (default: current directory).",
    )
    check_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    check_parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to custom pyproject.toml configuration.",
    )

    # init subcommand
    init_parser = subparsers.add_parser("init", help="Initialize pyproject.toml with anti-slop configuration.")
    init_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Target directory (default: current directory).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # If no subcommand provided, default to check on '.'
    command = args.command or "check"

    if command == "init":
        target = Path(getattr(args, "directory", ".")).resolve()
        return init_command(target)

    # Check command
    raw_paths = getattr(args, "paths", ["."])
    paths = [Path(p).resolve() for p in raw_paths]
    output_format = getattr(args, "format", "text")
    config_path = getattr(args, "config", None)

    if config_path and config_path.exists():
        target_base = config_path.parent
        config = load_config(target_base)
    elif paths:
        first_path = paths[0]
        target_base = first_path if first_path.is_dir() else first_path.parent
        config = load_config(target_base)
    else:
        target_base = Path.cwd()
        config = load_config(target_base)

    diagnostics = analyze_paths(paths, config, base_dir=target_base)

    if output_format == "json":
        print(format_json(diagnostics))
    else:
        formatted = format_text(diagnostics)
        if formatted:
            print(formatted)
        else:
            print("No anti-slop violations found. Code evidence is sound!")

    return 1 if diagnostics else 0


if __name__ == "__main__":
    sys.exit(main())
