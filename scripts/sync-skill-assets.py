#!/usr/bin/env python3
"""Sync src/anti_slop and scripts to skills/anti-slop and skills/install-anti-slop."""

import shutil
from pathlib import Path


def sync_skill(repo_root: Path, skill_name: str, src_dir: Path) -> None:
    skill_dir = repo_root / "skills" / skill_name
    assets_dest = skill_dir / "assets" / "anti_slop"
    scripts_dest = skill_dir / "scripts"

    if assets_dest.exists():
        shutil.rmtree(assets_dest)
    assets_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_dir, assets_dest)

    scripts_src = repo_root / "skills" / "install-anti-slop" / "scripts"
    if scripts_src.exists() and skill_name != "install-anti-slop":
        if scripts_dest.exists():
            shutil.rmtree(scripts_dest)
        shutil.copytree(scripts_src, scripts_dest)

    print(f"Synced {src_dir} -> {skill_dir}")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = repo_root / "src" / "anti_slop"

    sync_skill(repo_root, "anti-slop", src_dir)
    sync_skill(repo_root, "install-anti-slop", src_dir)
    return 0


if __name__ == "__main__":
    main()
