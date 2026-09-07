#!/usr/bin/env python3
"""Install this repository's skill without replacing an existing installation."""

import argparse
import os
from pathlib import Path
import shutil
import sys

SKILL_NAME = "dbdbschool"
SOURCE = Path(__file__).resolve().parents[1] / "skills" / SKILL_NAME


def default_skills_dir():
    codex_dir = os.environ.get("CODEX_HOME")
    return (Path(codex_dir).expanduser() if codex_dir else Path.home() / ".codex") / "skills"


def install(skills_dir, source=SOURCE):
    source = Path(source)
    if not (source / "SKILL.md").is_file():
        raise ValueError("설치 원본에 SKILL.md가 없습니다.")
    if source.is_symlink() or any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("설치 원본에 심볼릭 링크가 포함되어 있습니다.")
    skills_dir = Path(skills_dir).expanduser()
    target = skills_dir / SKILL_NAME
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"기존 설치를 덮어쓰지 않습니다: {target}")
    # Prevent copying the source recursively into itself.
    if target.resolve().is_relative_to(source.resolve()):
        raise ValueError("설치 대상은 원본 스킬 내부에 둘 수 없습니다.")
    skills_dir.mkdir(parents=True, exist_ok=True)
    target.mkdir()  # Exclusive creation also refuses concurrent installs.
    try:
        shutil.copytree(source, target, dirs_exist_ok=True)
    except BaseException:
        shutil.rmtree(target)
        raise
    return target.resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, default=default_skills_dir())
    args = parser.parse_args(argv)
    try:
        target = install(args.skills_dir)
    except (OSError, ValueError) as exc:
        print(f"설치 실패: {exc}", file=sys.stderr)
        return 1
    print(f"설치 완료: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
