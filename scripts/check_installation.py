#!/usr/bin/env python3
"""Check installed research skills without loading agent configuration or secrets."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import uuid


REPO = Path(__file__).resolve().parent.parent


def skill_name(path: Path) -> str | None:
    text = (path / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    match = re.search(r"^name:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", text.split("---", 2)[1], re.M)
    return match.group(1) if match else None


def fingerprint(path: Path) -> dict[str, str]:
    return {
        p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in path.rglob("*")
        if p.is_file() and not any(part in {".git", "__pycache__", ".DS_Store"} for part in p.relative_to(path).parts)
    }


def check(agent_home: Path, move_backups: bool = False) -> list[str]:
    root = agent_home / "skills"
    problems: list[str] = []
    expected = {p.name: p for p in REPO.iterdir() if (p / "SKILL.md").is_file()}
    names: dict[str, list[Path]] = {}
    for path in sorted(root.iterdir()) if root.is_dir() else []:
        if path.is_symlink() and not path.exists():
            problems.append(f"Broken link: {path}")
            continue
        if not (path / "SKILL.md").is_file():
            continue
        try:
            name = skill_name(path)
            legacy = re.fullmatch(r"(.+)\.backup-\d+", path.name)
            if legacy and legacy.group(1) in expected and name == legacy.group(1):
                if move_backups:
                    backup_root = agent_home / "skill-backups"
                    backup_root.mkdir(parents=True, exist_ok=True)
                    destination = backup_root / f"{path.name}-{uuid.uuid4().hex}"
                    shutil.move(str(path), str(destination))
                    print(f"Moved legacy backup: {path} -> {destination}")
                    continue
                problems.append(f"Discoverable legacy backup: {path}")
            if name:
                names.setdefault(name, []).append(path)
        except (OSError, UnicodeError) as exc:
            problems.append(f"Cannot inspect {path}: {exc}")
    for name, paths in names.items():
        if len(paths) > 1:
            problems.append(f"Duplicate {name}: " + ", ".join(map(str, paths)))
    for name, source in expected.items():
        destination = root / name
        if not (destination / "SKILL.md").is_file():
            problems.append(f"Missing research skill: {destination}")
        elif destination.resolve() != source.resolve():
            try:
                if fingerprint(destination) != fingerprint(source):
                    problems.append(f"Outdated or customized copy: {destination}")
            except OSError as exc:
                problems.append(f"Cannot compare {destination}: {exc}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["codex", "claude", "both"], default="both")
    parser.add_argument("--agent-home", type=Path, help="Check one explicit agent home, including test installations.")
    parser.add_argument("--move-legacy-backups", action="store_true", help="Move this repository's old installer backups outside skills/.")
    args = parser.parse_args()
    homes = [args.agent_home] if args.agent_home else [
        Path(os.environ.get(f"{name.upper()}_HOME", str(Path.home() / f".{name}")))
        for name in ("codex", "claude") if args.target in {name, "both"}
    ]
    problems = []
    for agent_home in homes:
        problems.extend(check(agent_home.expanduser().resolve(), args.move_legacy_backups))
    for problem in problems:
        print(problem)
    print(f"Installation check: {len(problems)} issue(s)")
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
