#!/usr/bin/env python3
"""Preview or synchronize derived course markers and manifests without changing learner data."""

from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import os
from pathlib import Path
import re
import tempfile

import validate_course as validation


def marker(text: str, name: str, value: str) -> str:
    pattern = re.compile(r"<!--\s*course:" + re.escape(name) + r"\s*=[^<>\r\n]*-->")
    if len(pattern.findall(text)) > 1:
        raise ValueError(f"duplicate course:{name} markers; resolve the ambiguity first")
    replacement = f"<!-- course:{name}={value} -->"
    if pattern.search(text):
        return pattern.sub(lambda _match: replacement, text)
    lines = text.splitlines(keepends=True)
    lines.insert(1 if lines and lines[0].startswith("#") else 0, "\n" + replacement + "\n")
    return "".join(lines)


def plan_updates(target: Path, adopt_existing: bool = False) -> dict[Path, str]:
    reporter = validation.Reporter(initial_state=False)
    validation.validate_layout_and_symlinks(target, reporter)
    spec = validation.load_spec(target, reporter)
    if spec is None or reporter.errors:
        raise ValueError("course layout/spec is invalid: " + "; ".join(f.message for f in reporter.errors))
    validation.validate_spec(spec, target, reporter)
    if reporter.errors:
        raise ValueError("invalid course specification: " + "; ".join(f.message for f in reporter.errors))
    def path_for(relative: str) -> Path:
        safe = validation.safe_relative(relative)
        if safe is None:
            raise ValueError(f"unsafe course path: {relative!r}")
        path = target / safe
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing regular course file: {relative}")
        return path
    tracker = path_for("curriculum/skill-tracker.csv")
    rows = list(csv.DictReader(io.StringIO(tracker.read_text(encoding="utf-8"))))
    if not rows or not all({"skill_id", "depends_on"} <= row.keys() for row in rows):
        raise ValueError("tracker requires skill_id and depends_on columns")
    dependencies = {row["skill_id"]: validation.dependencies(row["depends_on"]) for row in rows}
    if len(dependencies) != len(rows) or any(not key for key in dependencies):
        raise ValueError("tracker skill IDs must be non-empty and unique")
    if any(dep not in dependencies for deps in dependencies.values() for dep in deps):
        raise ValueError("tracker contains an unknown prerequisite")
    # Detect dependency cycles before deriving any files.
    remaining = set(dependencies)
    while remaining:
        ready = {key for key in remaining if not remaining.intersection(dependencies[key])}
        if not ready:
            raise ValueError("tracker contains a dependency cycle")
        remaining -= ready
    if adopt_existing and ("modules" not in spec or "skill_references" not in spec):
        adopted = []
        for path in sorted((target / "curriculum/modules").glob("*.md")):
            if path.name.startswith("_"):
                continue
            text = path.read_text(encoding="utf-8")
            def read(pattern):
                matches = list(pattern.finditer(text))
                if len(matches) != 1:
                    raise ValueError(f"cannot adopt ambiguous markers in {path}")
                return matches[0].group(1)
            adopted.append((int(read(validation.MODULE_ORDER_RE)), {
                "path": path.relative_to(target).as_posix(),
                "skills": validation.marker_ids(read(validation.MODULE_SKILLS_RE)),
                "prerequisites": validation.marker_ids(read(validation.MODULE_PREREQUISITES_RE)),
            }))
        if len({order for order, _ in adopted}) != len(adopted):
            raise ValueError("cannot adopt duplicate module orders")
        spec.setdefault("modules", [module for _, module in sorted(adopted, key=lambda item: item[0])])
        references = {}
        for path in validation.walk_files(target):
            if path.suffix != ".md":
                continue
            matches = list(validation.SKILL_REFS_RE.finditer(path.read_text(encoding="utf-8")))
            if len(matches) > 1:
                raise ValueError(f"cannot adopt duplicate skill references in {path}")
            if matches:
                references[path.relative_to(target).as_posix()] = validation.marker_ids(matches[0].group(1))
        spec.setdefault("skill_references", references)
    modules = spec.get("modules")
    references = spec.get("skill_references")
    if not isinstance(modules, list) or not modules or not isinstance(references, dict):
        raise ValueError("spec requires modules and skill_references; use --adopt-existing to adopt unambiguous legacy markers")
    updates: dict[Path, str] = {}
    owners: dict[str, int] = {}
    seen_paths = set()
    for order, module in enumerate(modules):
        if not isinstance(module, dict):
            raise ValueError("each module must be an object")
        path = path_for(module.get("path"))
        if path.parent != target / "curriculum/modules" or path.name.startswith("_") or path.suffix != ".md" or path in seen_paths:
            raise ValueError("module paths must be distinct concrete curriculum/modules/*.md files")
        seen_paths.add(path)
        skills = module.get("skills")
        if not isinstance(skills, list) or not skills:
            raise ValueError(f"module {path.name} requires owned skills")
        for skill in skills:
            if not isinstance(skill, str) or skill not in dependencies or skill in owners:
                raise ValueError(f"unknown or multiply owned skill: {skill!r}")
            owners[skill] = order
    if set(owners) != set(dependencies):
        raise ValueError("every tracker skill must belong to one module")
    actual_modules = {p for p in (target / "curriculum/modules").glob("*.md") if not p.name.startswith("_")}
    if actual_modules != seen_paths:
        raise ValueError("spec modules must exactly match concrete module files")
    for order, module in enumerate(modules):
        skills = module["skills"]
        extra = module.get("prerequisites", [])
        if not isinstance(extra, list) or any(not isinstance(s, str) for s in extra):
            raise ValueError("module prerequisites must be a list of skill IDs")
        required = set(extra) | {dep for skill in skills for dep in dependencies[skill] if dep not in skills}
        if any(dep not in owners or owners[dep] >= order for dep in required):
            raise ValueError(f"module {module['path']} requires a skill from the same or later module")
        path = path_for(module["path"])
        text = path.read_text(encoding="utf-8")
        for name, value in (("module-order", str(order)), ("module-skills", ",".join(skills)), ("module-prerequisites", ",".join(sorted(required)))):
            text = marker(text, name, value)
        updates[path] = text
    if "tracking/ROADMAP.md" not in references:
        raise ValueError("skill_references must declare the roadmap's skill scope")
    for relative, ids in references.items():
        if not isinstance(ids, list) or any(not isinstance(s, str) or s not in dependencies for s in ids) or len(set(ids)) != len(ids):
            raise ValueError(f"invalid skill references in {relative}")
        path = path_for(relative)
        updates[path] = marker(updates.get(path, path.read_text(encoding="utf-8")), "skill-refs", ",".join(ids))
    week_id = spec["week_id"]
    # strptime validates the week identifier through the ISO calendar separately.
    from datetime import date
    year, week = week_id.split("-W")
    date.fromisocalendar(int(year), int(week), 1)
    week_path = path_for(f"tracking/{week_id}.md")
    updates[week_path] = marker(week_path.read_text(encoding="utf-8"), "week-id", week_id)
    today = path_for("TODAY.md")
    text = marker(today.read_text(encoding="utf-8"), "active-week", f"tracking/{week_id}.md")
    navigation = f"Week: [[tracking/{week_id}|{week_id}]]  "
    if re.search(r"^Week:.*$", text, re.M):
        text = re.sub(r"^Week:.*$", lambda _m: navigation, text, flags=re.M)
    else:
        text += "\n" + navigation + "\n"
    updates[today] = text
    actual = validation.final_artifact_files(target, reporter)
    if reporter.errors:
        raise ValueError("cannot read complete course manifest")
    spec["generated_files"] = sorted(actual)
    for key in ("core_files", "profile_files", "depth_files", "initially_empty_csvs"):
        spec[key] = [p for p in spec[key] if p in actual]
    spec["csv_schemas"] = {
        relative: next(csv.reader(io.StringIO((target / relative).read_text(encoding="utf-8"))))
        for relative in sorted(actual) if relative.endswith(".csv")
    }
    updates[target / validation.SPEC_RELATIVE] = json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    return {path: text for path, text in updates.items() if path.read_text(encoding="utf-8") != text}


def apply_updates(updates: dict[Path, str]) -> None:
    originals = {path: path.read_bytes() for path in updates}
    written = []
    try:
        for path, content in updates.items():
            if path.read_bytes() != originals[path]:
                raise ValueError(f"file changed during sync: {path}")
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(content.encode("utf-8"))
                temporary.chmod(path.stat().st_mode)
                os.replace(temporary, path)
                written.append(path)
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
    except BaseException:
        for path in reversed(written):
            if path.read_bytes() == updates[path].encode("utf-8"):
                path.write_bytes(originals[path])
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--write", action="store_true", help="Apply the previewed marker/manifest changes.")
    parser.add_argument("--adopt-existing", action="store_true", help="Adopt unambiguous legacy module/reference markers as the initial canonical mapping.")
    args = parser.parse_args()
    if not args.target.is_absolute() or args.target.is_symlink():
        parser.error("target must be an absolute real course directory")
    try:
        updates = plan_updates(args.target.resolve(), args.adopt_existing)
        for path, text in updates.items():
            print("".join(difflib.unified_diff(path.read_text(encoding="utf-8").splitlines(True), text.splitlines(True), fromfile=str(path), tofile=str(path))), end="")
        if args.write:
            apply_updates(updates)
        print(f"{'Updated' if args.write else 'Would update'} {len(updates)} file(s). Learner content and actuals are unchanged.")
        return 0 if args.write or not updates else 1
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as exc:
        print(f"sync error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
