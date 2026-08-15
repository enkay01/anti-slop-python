#!/usr/bin/env python3
"""Install script to vendor anti-slop into a target repository."""

import argparse
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Vendor anti-slop into target repository.")
    parser.add_argument(
        "destination",
        nargs="?",
        default="tools/anti-slop",
        help="Destination directory (default: tools/anti-slop)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing destination directory.",
    )
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    assets_src = skill_root / "assets" / "anti_slop"

    # Fallback to repo src if assets not synced
    if not assets_src.exists():
        repo_root = skill_root.parent.parent
        assets_src = repo_root / "src" / "anti_slop"

    if not assets_src.exists():
        print(f"Error: Source files not found at {assets_src}", file=sys.stderr)
        return 1

    dest_path = Path.cwd() / args.destination
    if dest_path.exists() and not args.force:
        print(
            f"Error: Destination {dest_path} already exists. Pass --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    if dest_path.exists() and args.force:
        shutil.rmtree(dest_path)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(assets_src, dest_path)
    print(f"Successfully vendored anti-slop to {dest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
