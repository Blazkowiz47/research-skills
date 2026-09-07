#!/usr/bin/env python3
"""Safely scaffold an evidence-driven course project from bundled templates."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
from datetime import date, datetime
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Iterable
from course_layout import starter_files


CONCRETE_PROFILES = (
    "knowledge-exam",
    "technical-experimental",
    "creative-portfolio",
)
PROFILES = (
    *CONCRETE_PROFILES,
    "mixed",
)
DEPTHS = ("starter", "standard", "deep")
APPROVED_STATUSES = (
    "Not started",
    "Learning",
    "Reproduced",
    "Explained",
    "Modified",
    "Debugged independently",
    "Capstone ready",
)
PLACEHOLDER_RE = re.compile(r"{{\s*([A-Za-z][A-Za-z0-9_]*)\s*}}")
IGNORED_TEMPLATE_NAMES = {".DS_Store"}
COURSE_SPEC_PATH = ".course/COURSE_SPEC.json"


def profile_template_sets(
    profile: str,
    primary_profile: str,
    secondary_profiles: tuple[str, ...],
) -> tuple[str, ...]:
    if profile == "mixed":
        return (primary_profile, *secondary_profiles)
    return (profile,)


def selected_template_sets(
    profile: str,
    primary_profile: str,
    secondary_profiles: tuple[str, ...],
    depth: str,
) -> tuple[str, ...]:
    if depth == "starter":
        return ("core",)
    selected = [
        "core",
        *profile_template_sets(profile, primary_profile, secondary_profiles),
    ]
    if depth in {"standard", "deep"}:
        selected.append("depth-standard")
    if depth == "deep":
        selected.append("depth-deep")
    return tuple(selected)


class ScaffoldError(RuntimeError):
    """A user-actionable scaffolding error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a new course project from the create-course templates. "
            "The target must be absolute and absent or empty, its parent must already "
            "exist, and overwriting is never allowed. Depth composes progressively: "
            "starter selects the minimal core; standard uses core and profile templates plus "
            "depth-standard; deep also uses depth-deep."
        )
    )
    parser.add_argument("--target", required=True, help="Absolute destination directory")
    parser.add_argument("--topic", required=True, help="Topic or desired capability")
    parser.add_argument(
        "--profile",
        required=True,
        choices=PROFILES,
        help=(
            "Course profile. 'mixed' is selective and additionally requires one "
            "--primary-profile and at least one --secondary-profile."
        ),
    )
    parser.add_argument(
        "--primary-profile",
        choices=CONCRETE_PROFILES,
        help="Primary concrete profile; required only when --profile=mixed",
    )
    parser.add_argument(
        "--secondary-profile",
        action="append",
        choices=CONCRETE_PROFILES,
        default=[],
        help=(
            "Secondary concrete profile for --profile=mixed; repeat for each selected "
            "secondary (at least one, all distinct from the primary)"
        ),
    )
    parser.add_argument(
        "--depth",
        required=True,
        choices=DEPTHS,
        help="Template depth: starter (minimal core), standard (core, profile, and depth-standard), or deep (both depth sets)",
    )
    parser.add_argument("--title", help="Human-readable course title (defaults to topic)")
    parser.add_argument(
        "--weekly-hours",
        type=float,
        help="Available study hours per week; omit to make week one a calibration week",
    )
    parser.add_argument(
        "--deadline",
        help="Optional target date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and templates and print the manifest without writing",
    )
    return parser.parse_args(argv)


def clean_required_text(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ScaffoldError(f"{label} must not be blank")
    if "\x00" in cleaned:
        raise ScaffoldError(f"{label} must not contain a NUL character")
    return cleaned


def normalize_weekly_hours(value: float | None) -> int | float | None:
    if value is None:
        return None
    if not math.isfinite(value) or value <= 0 or value > 168:
        raise ScaffoldError("--weekly-hours must be greater than 0 and no more than 168")
    return int(value) if value.is_integer() else value


def normalize_deadline(value: str | None, start_date: date) -> str | None:
    if value is None:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ScaffoldError("--deadline must use YYYY-MM-DD and be a real date") from exc
    if parsed < start_date:
        raise ScaffoldError("--deadline must not be earlier than the course start date")
    return parsed.isoformat()


def normalize_profile_selection(
    profile: str,
    primary_profile: str | None,
    secondary_profiles: list[str],
) -> tuple[str, tuple[str, ...]]:
    if profile != "mixed":
        if primary_profile is not None or secondary_profiles:
            raise ScaffoldError(
                "--primary-profile and --secondary-profile are valid only with --profile=mixed"
            )
        return profile, ()

    if primary_profile is None:
        raise ScaffoldError("--profile=mixed requires --primary-profile")
    if not secondary_profiles:
        raise ScaffoldError(
            "--profile=mixed requires at least one --secondary-profile"
        )
    if len(set(secondary_profiles)) != len(secondary_profiles):
        raise ScaffoldError("--secondary-profile values must be distinct")
    if primary_profile in secondary_profiles:
        raise ScaffoldError(
            "--secondary-profile values must be distinct from --primary-profile"
        )
    return primary_profile, tuple(secondary_profiles)


def validate_target(raw_target: str) -> Path:
    raw_path = Path(raw_target)
    if not raw_path.is_absolute():
        raise ScaffoldError("--target must be an absolute path")
    if raw_path.name in {"", ".", ".."}:
        raise ScaffoldError("--target must name a directory below an existing parent")
    if os.path.lexists(raw_path) and raw_path.is_symlink():
        raise ScaffoldError(f"target must not be a symlink: {raw_path}")

    try:
        parent = raw_path.parent.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as exc:
        raise ScaffoldError(
            f"target parent must already exist and resolve without a symlink loop: {raw_path.parent}"
        ) from exc
    if not parent.is_dir():
        raise ScaffoldError(f"target parent is not a directory: {parent}")

    # Resolve only the existing parent. The final target component must never be
    # followed, either here or by the descriptor-relative writer.
    target = parent / raw_path.name
    if os.path.lexists(target):
        if target.is_symlink():
            raise ScaffoldError(f"target must not be a symlink: {target}")
        if not target.is_dir():
            raise ScaffoldError(f"target exists and is not a directory: {target}")
        try:
            first_entry = next(target.iterdir(), None)
        except OSError as exc:
            raise ScaffoldError(f"cannot inspect target directory {target}: {exc}") from exc
        if first_entry is not None:
            raise ScaffoldError(
                f"target directory is not empty; refusing to merge or overwrite: {target}"
            )
    return target


def render(value: str, replacements: dict[str, str], source: str) -> str:
    rendered = value
    for name, replacement in replacements.items():
        rendered = re.sub(
            r"{{\s*" + re.escape(name) + r"\s*}}",
            lambda _match, text=replacement: text,
            rendered,
        )
    unresolved = sorted(set(PLACEHOLDER_RE.findall(rendered)))
    if unresolved:
        raise ScaffoldError(
            f"unknown or unresolved placeholder(s) in {source}: " + ", ".join(unresolved)
        )
    return rendered


def safe_output_path(rendered_relative: str, source: Path) -> PurePosixPath:
    if rendered_relative.endswith(".tmpl"):
        rendered_relative = rendered_relative[:-5]
    output = PurePosixPath(rendered_relative)
    if (
        not rendered_relative
        or output.is_absolute()
        or any(part in {"", ".", ".."} for part in output.parts)
    ):
        raise ScaffoldError(f"template produces an unsafe output path: {source}")
    if output.as_posix() in {"COURSE_SPEC.json", COURSE_SPEC_PATH}:
        raise ScaffoldError(
            f"{COURSE_SPEC_PATH} is generated by the scaffold and cannot be a template"
        )
    return output


def iter_template_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.name in IGNORED_TEMPLATE_NAMES or "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            raise ScaffoldError(f"template symlinks are not supported: {path}")
        if path.is_file():
            yield path


def load_templates(
    template_root: Path,
    selected_sets: tuple[str, ...],
    replacements: dict[str, str],
) -> tuple[dict[str, str], dict[str, str], dict[str, list[str]]]:
    roots = tuple((group, template_root / group) for group in selected_sets)
    rendered_files: dict[str, str] = {}
    sources: dict[str, str] = {}
    groups: dict[str, list[str]] = {group: [] for group in selected_sets}

    if not template_root.is_dir():
        raise ScaffoldError(f"template directory is missing: {template_root}")

    for group, root in roots:
        if not root.is_dir():
            raise ScaffoldError(f"required template set is missing: {root}")
        template_files = list(iter_template_files(root))
        if not template_files:
            raise ScaffoldError(f"template set contains no files: {root}")
        for template_path in template_files:
            relative_template = template_path.relative_to(root).as_posix()
            rendered_relative = render(
                relative_template,
                replacements,
                f"template path {template_path}",
            )
            output = safe_output_path(rendered_relative, template_path).as_posix()
            if output in rendered_files:
                raise ScaffoldError(
                    f"template output collision for {output}: "
                    f"{sources[output]} and {template_path}"
                )
            try:
                template_text = template_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise ScaffoldError(
                    f"templates must be UTF-8 text files; cannot decode {template_path}"
                ) from exc
            rendered_files[output] = render(
                template_text,
                replacements,
                f"template content {template_path}",
            )
            sources[output] = str(template_path)
            groups[group].append(output)

    return rendered_files, sources, groups


def csv_schemas(rendered_files: dict[str, str]) -> dict[str, list[str]]:
    schemas: dict[str, list[str]] = {}
    for relative, content in rendered_files.items():
        if not relative.lower().endswith(".csv"):
            continue
        try:
            rows = csv.reader(io.StringIO(content))
            header = next(rows)
        except (StopIteration, csv.Error) as exc:
            raise ScaffoldError(f"CSV template has no valid header: {relative}") from exc
        normalized = [column.strip() for column in header]
        if not normalized or any(not column for column in normalized):
            raise ScaffoldError(f"CSV template has a blank header field: {relative}")
        if len(set(normalized)) != len(normalized):
            raise ScaffoldError(f"CSV template has duplicate header fields: {relative}")
        schemas[relative] = normalized
    return schemas


def initially_empty_csvs(rendered_files: dict[str, str]) -> list[str]:
    empty_logs: list[str] = []
    for relative in rendered_files:
        if not relative.lower().endswith(".csv"):
            continue
        stem = PurePosixPath(relative).stem.lower()
        if stem == "log" or stem.endswith("-log") or stem.endswith("_log"):
            empty_logs.append(relative)
    return sorted(empty_logs)


def build_spec(
    *,
    target: Path,
    topic: str,
    title: str,
    profile: str,
    primary_profile: str,
    secondary_profiles: tuple[str, ...],
    depth: str,
    weekly_hours: int | float | None,
    deadline: str | None,
    start_date: str,
    week_id: str,
    selected_sets: tuple[str, ...],
    groups: dict[str, list[str]],
    files: dict[str, str],
) -> dict[str, object]:
    generated_files = sorted([COURSE_SPEC_PATH, *files.keys()])
    assumptions: list[dict[str, str]] = [
        {
            "field": "baseline",
            "value": "unknown",
            "reason": "No verified learner evidence was supplied to the scaffold.",
            "review_trigger": "Complete the baseline diagnostic.",
        }
    ]
    if weekly_hours is None:
        assumptions.append(
            {
                "field": "capacity_hours_per_week",
                "value": "provisional calibration",
                "reason": "Weekly capacity was not supplied.",
                "review_trigger": "Review actual sustainable time after Week 1.",
            }
        )
    profile_sets = profile_template_sets(
        profile,
        primary_profile,
        secondary_profiles,
    )
    profile_files = sorted(
        relative
        for group in profile_sets
        for relative in groups.get(group, [])
    )
    depth_files = sorted(
        relative
        for group in selected_sets
        if group.startswith("depth-")
        for relative in groups[group]
    )
    return {
        "schema_version": "1.1",
        "generator": "create-course/scaffold_course.py",
        "target_dir": str(target),
        "title": title,
        "topic": topic,
        "objective": None,
        "learner_background": None,
        "existing_knowledge": [],
        "target_outcome": None,
        "profile": profile,
        "primary_profile": primary_profile,
        "secondary_profiles": list(secondary_profiles),
        "profile_rationale": None,
        "depth": depth,
        "capacity_hours_per_week": weekly_hours,
        "deadline": deadline,
        "start_date": start_date,
        "week_id": week_id,
        "available_resources": [],
        "constraints": [],
        "safety_constraints": [],
        "learning_preferences": [],
        "reference_projects": [],
        "assumptions": assumptions,
        "approved_statuses": list(APPROVED_STATUSES),
        "initial_status": "Not started",
        "selected_template_sets": list(selected_sets),
        "generated_files": generated_files,
        "core_files": sorted(groups["core"]),
        "profile_files": profile_files,
        "depth_files": depth_files,
        "csv_schemas": csv_schemas(files),
        "initially_empty_csvs": initially_empty_csvs(files),
        "modules": [{"path": "curriculum/modules/M00-calibration.md", "skills": [f"S{i:02d}" for i in range(1, 9)]}],
        "skill_references": {
            path: re.search(r"course:skill-refs=([^<>\r\n]*?)\s*-->", files[path]).group(1).split(",")
            for path in ("tracking/ROADMAP.md", "curriculum/DEPENDENCY_MAP.md", "practice/CAPSTONE.md")
            if path in files
        },
    }


def require_secure_filesystem_primitives() -> None:
    required_dir_fd_functions = (os.open, os.mkdir, os.stat, os.unlink, os.rmdir)
    missing = [
        function.__name__
        for function in required_dir_fd_functions
        if function not in os.supports_dir_fd
    ]
    if missing:
        raise ScaffoldError(
            "secure scaffolding is unsupported on this platform; missing dir_fd support for: "
            + ", ".join(missing)
        )
    if os.stat not in os.supports_follow_symlinks:
        raise ScaffoldError(
            "secure scaffolding is unsupported on this platform; os.stat cannot reject symlinks"
        )
    if os.listdir not in os.supports_fd:
        raise ScaffoldError(
            "secure scaffolding is unsupported on this platform; os.listdir cannot inspect a directory descriptor"
        )
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise ScaffoldError(
            "secure scaffolding is unsupported on this platform; O_DIRECTORY and O_NOFOLLOW are required"
        )


def directory_open_flags() -> int:
    return (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )


def open_absolute_directory(path: Path) -> int:
    """Open an absolute directory without following any path-component symlink."""
    if not path.is_absolute():
        raise ScaffoldError(f"internal error: directory path is not absolute: {path}")
    parts = path.parts
    if not parts:
        raise ScaffoldError(f"internal error: directory path has no components: {path}")

    flags = directory_open_flags()
    current_fd = os.open(parts[0], flags)
    try:
        for part in parts[1:]:
            next_fd = os.open(part, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        os.close(current_fd)
        raise


def inode_identity(stat_result: os.stat_result) -> tuple[int, int]:
    return stat_result.st_dev, stat_result.st_ino


def entry_matches(
    parent_fd: int,
    name: str,
    expected: tuple[int, int],
) -> bool:
    try:
        actual = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return inode_identity(actual) == expected


def write_files(target: Path, files: dict[str, str]) -> None:
    """Write through pinned directory descriptors, never through descendant paths."""
    require_secure_filesystem_primitives()
    parent_fd = open_absolute_directory(target.parent)
    target_fd: int | None = None
    target_created_by_us = False
    target_identity: tuple[int, int] | None = None
    directory_fds: dict[tuple[str, ...], int] = {}
    written: list[tuple[tuple[str, ...], str, tuple[int, int]]] = []
    created_directories: list[
        tuple[tuple[str, ...], str, tuple[int, int], tuple[str, ...]]
    ] = []

    try:
        try:
            target_fd = os.open(target.name, directory_open_flags(), dir_fd=parent_fd)
        except FileNotFoundError:
            try:
                os.mkdir(target.name, mode=0o700, dir_fd=parent_fd)
            except FileExistsError as exc:
                raise ScaffoldError(
                    f"target changed while scaffolding; refusing to continue: {target}"
                ) from exc
            target_created_by_us = True
            target_fd = os.open(target.name, directory_open_flags(), dir_fd=parent_fd)
        except OSError as exc:
            raise ScaffoldError(
                f"target cannot be securely opened as a non-symlink directory: {target}: {exc}"
            ) from exc

        target_identity = inode_identity(os.fstat(target_fd))
        if not entry_matches(parent_fd, target.name, target_identity):
            raise ScaffoldError(
                f"target changed while it was being opened; refusing to continue: {target}"
            )
        if os.listdir(target_fd):
            raise ScaffoldError(
                f"target directory is not empty; refusing to merge or overwrite: {target}"
            )

        directory_fds[()] = target_fd
        target_fd = None
        file_flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )

        for relative in sorted(files):
            output = PurePosixPath(relative)
            parent_key: tuple[str, ...] = ()
            for part in output.parts[:-1]:
                child_key = (*parent_key, part)
                if child_key not in directory_fds:
                    current_parent_fd = directory_fds[parent_key]
                    try:
                        os.mkdir(part, mode=0o755, dir_fd=current_parent_fd)
                    except FileExistsError as exc:
                        raise ScaffoldError(
                            f"destination changed while scaffolding; refusing existing directory: "
                            f"{PurePosixPath(*child_key)}"
                        ) from exc
                    child_fd = os.open(
                        part,
                        directory_open_flags(),
                        dir_fd=current_parent_fd,
                    )
                    child_identity = inode_identity(os.fstat(child_fd))
                    if not entry_matches(current_parent_fd, part, child_identity):
                        os.close(child_fd)
                        raise ScaffoldError(
                            f"destination directory changed while it was being opened: "
                            f"{PurePosixPath(*child_key)}"
                        )
                    directory_fds[child_key] = child_fd
                    created_directories.append(
                        (parent_key, part, child_identity, child_key)
                    )
                parent_key = child_key

            destination_parent_fd = directory_fds[parent_key]
            filename = output.name
            descriptor = os.open(
                filename,
                file_flags,
                0o644,
                dir_fd=destination_parent_fd,
            )
            file_identity = inode_identity(os.fstat(descriptor))
            written.append((parent_key, filename, file_identity))
            data = files[relative].encode("utf-8")
            try:
                offset = 0
                while offset < len(data):
                    count = os.write(descriptor, data[offset:])
                    if count == 0:
                        raise OSError("zero-byte write while scaffolding")
                    offset += count
            finally:
                os.close(descriptor)

        if not entry_matches(parent_fd, target.name, target_identity):
            raise ScaffoldError(
                f"target changed during scaffolding; generated files were rolled back: {target}"
            )
    except Exception:
        # Roll back only entries created by this invocation and still bound to
        # the same inode. A replaced name is never removed.
        for parent_key, name, identity in reversed(written):
            directory_fd = directory_fds.get(parent_key)
            if directory_fd is None:
                continue
            if entry_matches(directory_fd, name, identity):
                try:
                    os.unlink(name, dir_fd=directory_fd)
                except OSError:
                    pass

        for parent_key, name, identity, child_key in reversed(created_directories):
            child_fd = directory_fds.pop(child_key, None)
            if child_fd is not None:
                try:
                    os.close(child_fd)
                except OSError:
                    pass
            directory_fd = directory_fds.get(parent_key)
            if directory_fd is None:
                continue
            if entry_matches(directory_fd, name, identity):
                try:
                    os.rmdir(name, dir_fd=directory_fd)
                except OSError:
                    pass

        root_fd = directory_fds.pop((), None)
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
        if (
            target_created_by_us
            and target_identity is not None
            and entry_matches(parent_fd, target.name, target_identity)
        ):
            try:
                os.rmdir(target.name, dir_fd=parent_fd)
            except OSError:
                pass
        raise
    finally:
        if target_fd is not None:
            try:
                os.close(target_fd)
            except OSError:
                pass
        for descriptor in directory_fds.values():
            try:
                os.close(descriptor)
            except OSError:
                pass
        os.close(parent_fd)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        target = validate_target(args.target)
        topic = clean_required_text(args.topic, "--topic")
        title = clean_required_text(args.title if args.title is not None else topic, "--title")
        primary_profile, secondary_profiles = normalize_profile_selection(
            args.profile,
            args.primary_profile,
            args.secondary_profile,
        )
        weekly_hours = normalize_weekly_hours(args.weekly_hours)
        today = date.today()
        deadline = normalize_deadline(args.deadline, today)
        iso = today.isocalendar()
        week_id = f"{iso.year}-W{iso.week:02d}"

        replacements = {
            "TITLE": title,
            "TOPIC": topic,
            "PROFILE": args.profile,
            "DEPTH": args.depth,
            "WEEKLY_HOURS": (
                "Unknown — calibrate in Week 1"
                if weekly_hours is None
                else f"{weekly_hours} hours"
            ),
            "DEADLINE": deadline if deadline is not None else "No fixed deadline",
            "START_DATE": today.isoformat(),
            "WEEK_ID": week_id,
        }
        template_root = Path(__file__).resolve().parent.parent / "assets" / "templates"
        template_sets = selected_template_sets(
            args.profile,
            primary_profile,
            secondary_profiles,
            args.depth,
        )
        rendered_files, sources, groups = load_templates(
            template_root,
            template_sets,
            replacements,
        )
        if args.depth == "starter":
            keep = starter_files(week_id)
            rendered_files = {path: content for path, content in rendered_files.items() if path in keep}
            sources = {path: source for path, source in sources.items() if path in keep}
            groups = {group: [path for path in paths if path in keep] for group, paths in groups.items()}
            rendered_files["README.md"] = rendered_files["README.md"].replace(
                "[[notes/INDEX\\|Notes index]]", "Create notes when the first attempt needs one"
            )
        spec = build_spec(
            target=target,
            topic=topic,
            title=title,
            profile=args.profile,
            primary_profile=primary_profile,
            secondary_profiles=secondary_profiles,
            depth=args.depth,
            weekly_hours=weekly_hours,
            deadline=deadline,
            start_date=today.isoformat(),
            week_id=week_id,
            selected_sets=template_sets,
            groups=groups,
            files=rendered_files,
        )
        rendered_files[COURSE_SPEC_PATH] = json.dumps(
            spec,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ) + "\n"
        sources[COURSE_SPEC_PATH] = "generated"

        if not args.dry_run:
            write_files(target, rendered_files)

        manifest = {
            "status": "dry-run" if args.dry_run else "created",
            "target": str(target),
            "profile": args.profile,
            "primary_profile": primary_profile,
            "secondary_profiles": list(secondary_profiles),
            "depth": args.depth,
            "selected_template_sets": list(template_sets),
            "template_root": str(template_root),
            "files": [
                {"path": relative, "source": sources[relative]}
                for relative in sorted(rendered_files)
            ],
        }
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0
    except ScaffoldError as exc:
        print(f"scaffold error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"scaffold error: filesystem operation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
