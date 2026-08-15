#!/usr/bin/env python3
"""Sync src/anti_slop to skills/install-anti-slop/assets/anti_slop."""

import shutil
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = repo_root / "src" / "anti_slop"
    assets_dest = repo_root / "skills" / "install-anti-slop" / "assets" / "anti_slop"

    if assets_dest.exists():
        shutil.rmtree(assets_dest)

    assets_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_dir, assets_dest)
    print(f"Synced {src_dir} -> {assets_dest}")
    return 0


if __name__ == "__main__":
    main()
