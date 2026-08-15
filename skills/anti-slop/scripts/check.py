#!/usr/bin/env python3
"""Run anti-slop checks directly from the skill without modifying the target repository."""

import sys
from pathlib import Path

# Add bundled assets/anti_slop (or src/anti_slop if running in repo) to sys.path
_script_dir = Path(__file__).resolve().parent
_skill_root = _script_dir.parent
_assets_dir = _skill_root / "assets"
_repo_src = _skill_root.parent.parent / "src"

if _assets_dir.exists():
    if str(_assets_dir) not in sys.path:
        sys.path.insert(0, str(_assets_dir))
elif _repo_src.exists():
    if str(_repo_src) not in sys.path:
        sys.path.insert(0, str(_repo_src))

try:
    from anti_slop.cli import main
except ImportError as e:
    print(f"Error: Unable to import anti_slop engine from skill assets: {e}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    argv = sys.argv[1:]
    # Default to check subcommand if user passes path directly
    if not argv or (argv[0] not in {"check", "init", "--help", "-h", "--version"} and not argv[0].startswith("-")):
        argv = ["check"] + argv
    sys.exit(main(argv))
