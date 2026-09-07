#!/usr/bin/env python3
"""Validate this package's local links, entrypoint and distributable file types.

This is a package check, not a general YAML parser or a behavioral evaluation.
"""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "dbdbschool"


def validate():
    errors = []
    entry = SKILL / "SKILL.md"
    if not entry.is_file():
        return ["Missing SKILL.md"]
    body = entry.read_text(encoding="utf-8")
    parts = body.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        errors.append("Missing YAML frontmatter delimiters")
    elif not re.search(r"^name: dbdbschool$", parts[1], re.M) or not re.search(
        r"^description: \S.+$", parts[1], re.M
    ):
        errors.append("Invalid name or missing single-line description")
    if not (SKILL / "agents" / "openai.yaml").is_file():
        errors.append("Missing UI metadata")
    for path in SKILL.rglob("*"):
        if path.is_symlink():
            errors.append(f"Symlink in skill: {path.relative_to(ROOT)}")
        elif path.is_file() and path.suffix not in {".md", ".yaml"}:
            errors.append(f"Unexpected distributable file: {path.relative_to(ROOT)}")
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f"Broken/outside link in {path.relative_to(ROOT)}: {link}")
    # Ensure references can be discovered starting from the skill entrypoint.
    seen = set()
    pending = [entry.resolve()]
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if target.is_relative_to(SKILL) and target.is_file() and target.suffix == ".md":
                pending.append(target)
    for path in (SKILL / "references").glob("*.md"):
        if path.resolve() not in seen:
            errors.append(f"Unreachable reference: {path.name}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("Package structure, local links and reference discovery: OK")
