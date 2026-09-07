#!/usr/bin/env python3
"""Validate the structure and pristine state of a generated course project."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Iterable
from urllib.parse import unquote, urlsplit
from course_layout import starter_files


PROFILES = {
    "knowledge-exam",
    "technical-experimental",
    "creative-portfolio",
    "mixed",
}
CONCRETE_PROFILES = {
    "knowledge-exam",
    "technical-experimental",
    "creative-portfolio",
}
DEPTHS = {"starter", "standard", "deep"}
EVIDENCE_STATUSES = (
    "Not started",
    "Learning",
    "Reproduced",
    "Explained",
    "Modified",
    "Debugged independently",
    "Capstone ready",
)
INITIAL_STATUS = "Not started"
GENERIC_STARTER_SKILL_DESCRIPTIONS = {
    "Use the essential vocabulary precisely",
    "Explain the central model or process",
    "Reproduce a representative canonical task",
    "Use the field's core method or tool safely",
    "Diagnose a representative error or weakness",
    "Adapt a known method under one changed constraint",
    "Complete an unfamiliar task independently",
    "Integrate and defend a capstone",
}
GENERIC_SENTINELS = {
    "README.md": (
        "The exact capstone and acceptance criteria are defined during Phase 0 rather than assumed here",
    ),
    "curriculum/modules/M00-calibration.md": (
        "Turn the generic starter capabilities",
        "Rewrite S01–S08",
    ),
}
SPEC_RELATIVE = ".course/COURSE_SPEC.json"
ALLOWED_ROOT_FILES = {"README.md", "TODAY.md", "AGENTS.md", "CLAUDE.md"}
ALLOWED_TOP_LEVEL_DIRECTORIES = {
    "curriculum",
    "notes",
    "practice",
    "tracking",
    "resources",
}
CORE_REQUIRED = {
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "TODAY.md",
    SPEC_RELATIVE,
    "tracking/ROADMAP.md",
    "tracking/DASHBOARD.md",
    "tracking/BACKLOG.md",
    "tracking/study-log.csv",
    "resources/SOURCES.md",
    "curriculum/BASELINE_DIAGNOSTIC.md",
    "curriculum/SKILL_MAP.md",
    "curriculum/skill-tracker.csv",
}
PLACEHOLDER_RE = re.compile(r"{{\s*[A-Za-z][A-Za-z0-9_]*\s*}}")
CHECKED_BOX_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[[xX]\]")
INLINE_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+|<[^>]+>)", re.MULTILINE)
WIKI_LINK_RE = re.compile(r"!?\[\[([^\]\n]+)\]\]")
CAPACITY_MARKER_RE = re.compile(
    r"<!--\s*course:(?:weekly-)?planned-minutes\s*=\s*(\d+)\s*-->",
    re.IGNORECASE,
)
CAPACITY_PERCENT_RE = re.compile(
    r"<!--\s*course:planned-capacity-percent\s*=\s*(\d+(?:\.\d+)?)\s*-->",
    re.IGNORECASE,
)
SESSION_CAPACITY_PERCENT_RE = re.compile(
    r"<!--\s*course:session-capacity-percent\s*=\s*(\d+(?:\.\d+)?)\s*-->",
    re.IGNORECASE,
)
PLANNED_CAPACITY_TOKEN_RE = re.compile(r"course:planned-capacity-percent", re.IGNORECASE)
SESSION_CAPACITY_TOKEN_RE = re.compile(r"course:session-capacity-percent", re.IGNORECASE)
MODULE_ORDER_RE = re.compile(
    r"<!--\s*course:module-order\s*=\s*(\d+)\s*-->", re.IGNORECASE
)
MODULE_SKILLS_RE = re.compile(
    r"<!--\s*course:module-skills\s*=\s*([^<>\r\n]*)\s*-->", re.IGNORECASE
)
MODULE_PREREQUISITES_RE = re.compile(
    r"<!--\s*course:module-prerequisites\s*=\s*([^<>\r\n]*)\s*-->",
    re.IGNORECASE,
)
SKILL_REFS_RE = re.compile(
    r"<!--\s*course:skill-refs\s*=\s*([^<>\r\n]*)\s*-->", re.IGNORECASE
)
ACTIVE_WEEK_RE = re.compile(
    r"<!--\s*course:active-week\s*=\s*([^<>\r\n]+?)\s*-->", re.IGNORECASE
)
WEEK_ID_MARKER_RE = re.compile(
    r"<!--\s*course:week-id\s*=\s*(\d{4}-W\d{2})\s*-->", re.IGNORECASE
)
TEXT_SUFFIXES = {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".py", ".sh"}
SKIP_DIRECTORIES = {".git", ".hg", ".svn", "__pycache__"}


def selected_template_sets(spec: dict[str, object]) -> tuple[str, ...]:
    """Return the deterministic template-set selection for a well-formed spec.

    Invalid profile-selection fields are reported by ``validate_spec``. This
    helper deliberately falls back to only the sets it can prove safe so a
    malformed list never crashes validation or broadens the expected manifest.
    """

    profile = spec.get("profile")
    if spec.get("schema_version") == "1.1" and spec.get("depth") == "starter":
        return ("core",)
    selected_profiles: list[str] = []
    if profile == "mixed":
        primary = spec.get("primary_profile")
        if isinstance(primary, str) and primary in CONCRETE_PROFILES:
            selected_profiles.append(primary)
        secondary = spec.get("secondary_profiles")
        if isinstance(secondary, list):
            for value in secondary:
                if (
                    isinstance(value, str)
                    and value in CONCRETE_PROFILES
                    and value not in selected_profiles
                ):
                    selected_profiles.append(value)
    elif isinstance(profile, str) and profile in CONCRETE_PROFILES:
        selected_profiles.append(profile)

    sets = ["core", *selected_profiles]
    depth = spec.get("depth")
    if depth in {"standard", "deep"}:
        sets.append("depth-standard")
    if depth == "deep":
        sets.append("depth-deep")
    return tuple(sets)


@dataclass(order=True, frozen=True)
class Finding:
    code: str
    location: str
    message: str


@dataclass
class Reporter:
    initial_state: bool = True
    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)

    def error(self, code: str, location: str | Path, message: str) -> None:
        self.errors.append(Finding(code, str(location), message))

    def warning(self, code: str, location: str | Path, message: str) -> None:
        self.warnings.append(Finding(code, str(location), message))

    def emit(self) -> None:
        for finding in sorted(self.errors):
            print(f"ERROR [{finding.code}] {finding.location}: {finding.message}")
        for finding in sorted(self.warnings):
            print(f"WARNING [{finding.code}] {finding.location}: {finding.message}")
        result = "FAILED" if self.errors else "PASSED"
        print(
            f"Validation {result}: {len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s)"
        )


@dataclass(frozen=True)
class SkillTrackerData:
    dependencies: dict[str, list[str]]
    id_lines: dict[str, int]

    @property
    def ids(self) -> set[str]:
        return set(self.dependencies)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a customized create-course project. By default the topic-specific "
            "objective, outcome, skills, and planning sentinels must be finalized."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--scaffold",
        action="store_true",
        help=(
            "validate an untouched intermediate scaffold; structural and zero-state checks "
            "still run, and files are compared with the currently installed template bundle"
        ),
    )
    mode.add_argument("--in-progress", action="store_true", help="Validate a used course without requiring empty logs or zero learner progress.")
    parser.add_argument("target", help="Absolute course project directory")
    return parser.parse_args(argv)


def safe_relative(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def read_text(path: Path, reporter: Reporter, code: str = "TEXT_READ") -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        reporter.error(code, path, f"cannot read as UTF-8 text: {exc}")
        return None


def has_symlink_component(target: Path, relative: PurePosixPath) -> bool:
    current = target
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def load_spec(target: Path, reporter: Reporter) -> dict[str, object] | None:
    spec_path = target / SPEC_RELATIVE
    if has_symlink_component(target, PurePosixPath(SPEC_RELATIVE)):
        return None  # The tree-level validator reports the exact symlink.
    if not spec_path.is_file():
        reporter.error("SPEC_MISSING", spec_path, "required course specification is missing")
        return None
    text = read_text(spec_path, reporter, "SPEC_READ")
    if text is None:
        return None
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as exc:
        reporter.error("SPEC_JSON", spec_path, f"invalid JSON: {exc}")
        return None
    if not isinstance(spec, dict):
        reporter.error("SPEC_TYPE", spec_path, "top-level JSON value must be an object")
        return None
    return spec


def validate_spec(spec: dict[str, object], target: Path, reporter: Reporter) -> None:
    spec_path = target / SPEC_RELATIVE
    if spec.get("schema_version") not in {"1.0", "1.1"}:
        reporter.error("SPEC_VERSION", spec_path, "schema_version must be '1.0' or '1.1'")
    for key in ("title", "topic"):
        value = spec.get(key)
        if not isinstance(value, str) or not value.strip():
            reporter.error("SPEC_FIELD", spec_path, f"{key} must be a non-empty string")
    target_dir = spec.get("target_dir")
    if not isinstance(target_dir, str) or not Path(target_dir).is_absolute():
        reporter.error("SPEC_TARGET", spec_path, "target_dir must be an absolute path")
    else:
        try:
            recorded_target = Path(target_dir).resolve(strict=False)
        except (OSError, RuntimeError, ValueError) as exc:
            reporter.error("SPEC_TARGET", spec_path, f"cannot normalize target_dir: {exc}")
        else:
            if recorded_target != target:
                reporter.warning(
                    "SPEC_TARGET_MOVED",
                    spec_path,
                    f"course is being validated at {target}, not its generated target_dir {target_dir}",
                )
    if spec.get("profile") not in PROFILES:
        reporter.error("SPEC_PROFILE", spec_path, f"profile must be one of {sorted(PROFILES)}")
    if spec.get("depth") not in DEPTHS:
        reporter.error("SPEC_DEPTH", spec_path, f"depth must be one of {sorted(DEPTHS)}")

    weekly_hours = spec.get("capacity_hours_per_week")
    if weekly_hours is not None:
        if (
            not isinstance(weekly_hours, (int, float))
            or isinstance(weekly_hours, bool)
            or not math.isfinite(weekly_hours)
            or weekly_hours <= 0
            or weekly_hours > 168
        ):
            reporter.error(
                "SPEC_CAPACITY",
                spec_path,
                "capacity_hours_per_week must be null or a number greater than 0 and no more than 168",
            )

    for key in ("start_date", "deadline"):
        value = spec.get(key)
        if value is None and key == "deadline":
            continue
        if not isinstance(value, str):
            reporter.error("SPEC_DATE", spec_path, f"{key} must be YYYY-MM-DD")
            continue
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            reporter.error("SPEC_DATE", spec_path, f"{key} must be a real YYYY-MM-DD date")

    start_value = spec.get("start_date")
    deadline_value = spec.get("deadline")
    if isinstance(start_value, str) and isinstance(deadline_value, str):
        try:
            if datetime.strptime(deadline_value, "%Y-%m-%d") < datetime.strptime(
                start_value, "%Y-%m-%d"
            ):
                reporter.error("SPEC_DEADLINE", spec_path, "deadline must not precede start_date")
        except ValueError:
            pass  # Individual date errors are reported above.

    week_id = spec.get("week_id")
    if not isinstance(week_id, str) or not re.fullmatch(r"\d{4}-W\d{2}", week_id):
        reporter.error("SPEC_WEEK", spec_path, "week_id must use YYYY-Www")

    for key in (
        "existing_knowledge",
        "available_resources",
        "constraints",
        "safety_constraints",
        "learning_preferences",
        "reference_projects",
        "assumptions",
    ):
        if not isinstance(spec.get(key), list):
            reporter.error("SPEC_LIST", spec_path, f"{key} must be a list")

    statuses = spec.get("approved_statuses")
    statuses_well_formed = (
        isinstance(statuses, list)
        and bool(statuses)
        and all(isinstance(item, str) and bool(item) for item in statuses)
    )
    if not statuses_well_formed:
        reporter.error(
            "SPEC_STATUSES",
            spec_path,
            "approved_statuses must be a non-empty list of strings",
        )
    else:
        assert isinstance(statuses, list)
        typed_statuses = [item for item in statuses if isinstance(item, str)]
        indices = [EVIDENCE_STATUSES.index(item) for item in typed_statuses if item in EVIDENCE_STATUSES]
        if (
            typed_statuses[0] != INITIAL_STATUS
            or len(set(typed_statuses)) != len(typed_statuses)
            or any(item not in EVIDENCE_STATUSES for item in typed_statuses)
            or len(indices) != len(typed_statuses)
            or indices != sorted(indices)
        ):
            reporter.error(
                "SPEC_STATUSES",
                spec_path,
                "approved_statuses must be an ordered subset of the fixed evidence vocabulary, with 'Not started' first",
            )

    if spec.get("initial_status") != INITIAL_STATUS:
        reporter.error(
            "SPEC_INITIAL_STATUS",
            spec_path,
            "initial_status must be exactly 'Not started'",
        )

    profile = spec.get("profile")
    primary = spec.get("primary_profile")
    secondary = spec.get("secondary_profiles")
    if profile == "mixed":
        if not isinstance(primary, str) or primary not in CONCRETE_PROFILES:
            reporter.error(
                "SPEC_PRIMARY_PROFILE",
                spec_path,
                f"mixed courses require primary_profile to be one of {sorted(CONCRETE_PROFILES)}",
            )
        if (
            not isinstance(secondary, list)
            or not secondary
            or any(not isinstance(item, str) for item in secondary)
        ):
            reporter.error(
                "SPEC_SECONDARY_PROFILES",
                spec_path,
                "mixed courses require a non-empty list of secondary_profiles",
            )
        else:
            typed_secondary = [item for item in secondary if isinstance(item, str)]
            if (
                any(item not in CONCRETE_PROFILES for item in typed_secondary)
                or len(set(typed_secondary)) != len(typed_secondary)
                or primary in typed_secondary
            ):
                reporter.error(
                    "SPEC_SECONDARY_PROFILES",
                    spec_path,
                    "secondary_profiles must be unique concrete profiles distinct from primary_profile",
                )
    elif profile in CONCRETE_PROFILES:
        if primary != profile:
            reporter.error(
                "SPEC_PRIMARY_PROFILE",
                spec_path,
                "a concrete course must record its profile as primary_profile",
            )
        if secondary != []:
            reporter.error(
                "SPEC_SECONDARY_PROFILES",
                spec_path,
                "a non-mixed course must use an empty secondary_profiles list",
            )

    declared_sets = spec.get("selected_template_sets")
    expected_sets = list(selected_template_sets(spec))
    if not isinstance(declared_sets, list) or any(
        not isinstance(item, str) for item in declared_sets
    ):
        reporter.error(
            "SPEC_TEMPLATE_SETS",
            spec_path,
            "selected_template_sets must be a list of template-set names",
        )
    elif declared_sets != expected_sets:
        reporter.error(
            "SPEC_TEMPLATE_SETS",
            spec_path,
            f"selected_template_sets must equal {expected_sets!r} for this profile and depth",
        )


def template_expected_paths(
    spec: dict[str, object], reporter: Reporter
) -> tuple[set[str], set[str]]:
    template_root = Path(__file__).resolve().parent.parent / "assets" / "templates"
    profile = spec.get("profile")
    if not isinstance(profile, str) or profile not in PROFILES:
        return set(), set()
    replacements = {
        "TITLE": str(spec.get("title", "")),
        "TOPIC": str(spec.get("topic", "")),
        "PROFILE": profile,
        "DEPTH": str(spec.get("depth", "")),
        "WEEKLY_HOURS": (
            "Unknown — calibrate in Week 1"
            if spec.get("capacity_hours_per_week") is None
            else f"{spec.get('capacity_hours_per_week')} hours"
        ),
        "DEADLINE": (
            "No fixed deadline" if spec.get("deadline") is None else str(spec.get("deadline"))
        ),
        "START_DATE": str(spec.get("start_date", "")),
        "WEEK_ID": str(spec.get("week_id", "")),
    }

    groups: dict[str, set[str]] = {}
    selected_sets = selected_template_sets(spec)
    for group in selected_sets:
        root = template_root / group
        if not root.is_dir():
            reporter.warning(
                "TEMPLATES_UNAVAILABLE",
                root,
                "cannot recompute required files; using COURSE_SPEC manifest",
            )
            groups[group] = set()
            continue
        outputs: set[str] = set()
        for path in sorted(root.rglob("*")):
            if path.name == ".DS_Store" or "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                reporter.error("TEMPLATE_SYMLINK", path, "template symlinks are unsupported")
                continue
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            for name, value in replacements.items():
                relative = re.sub(
                    r"{{\s*" + re.escape(name) + r"\s*}}",
                    lambda _match, text=value: text,
                    relative,
                )
            if relative.endswith(".tmpl"):
                relative = relative[:-5]
            safe = safe_relative(relative)
            if safe is None:
                reporter.error("TEMPLATE_PATH", path, "template renders to an unsafe path")
            else:
                if spec.get("schema_version") == "1.1" and spec.get("depth") == "starter" and safe not in starter_files(str(spec.get("week_id"))):
                    continue
                outputs.add(safe)
        groups[group] = outputs
    noncore_groups = [groups[group] for group in selected_sets if group != "core"]
    profile_outputs = set().union(*noncore_groups) if noncore_groups else set()
    return groups.get("core", set()), profile_outputs


def validate_required_files(
    target: Path,
    spec: dict[str, object],
    reporter: Reporter,
    *,
    compare_current_templates: bool,
) -> set[str]:
    expected: set[str] = set(CORE_REQUIRED)
    if compare_current_templates:
        core_from_templates, profile_from_templates = template_expected_paths(spec, reporter)
        expected.update(core_from_templates)
        expected.update(profile_from_templates)

    for key in ("generated_files", "core_files", "profile_files", "depth_files"):
        values = spec.get(key)
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            reporter.error("SPEC_MANIFEST", target / SPEC_RELATIVE, f"{key} must be a list of paths")
            continue
        for value in values:
            safe = safe_relative(value)
            if safe is None:
                reporter.error("SPEC_PATH", target / SPEC_RELATIVE, f"unsafe path in {key}: {value!r}")
            else:
                expected.add(safe)

    for relative in sorted(expected):
        path = target / PurePosixPath(relative)
        if not path.is_file():
            reporter.error("REQUIRED_FILE", relative, "required generated file is missing")
        elif path.is_symlink():
            reporter.error("GENERATED_SYMLINK", relative, "generated files must not be symlinks")
    return expected


def final_artifact_files(target: Path, reporter: Reporter) -> set[str]:
    artifacts: set[str] = set()
    walk_errors: list[OSError] = []

    def remember_walk_error(exc: OSError) -> None:
        walk_errors.append(exc)

    for root, directories, files in os.walk(
        target,
        topdown=True,
        followlinks=False,
        onerror=remember_walk_error,
    ):
        root_path = Path(root)
        if root_path == target:
            directories[:] = sorted(
                name
                for name in directories
                if not name.startswith(".") or name == ".course"
            )
        else:
            directories[:] = sorted(directories)
        for name in sorted(files):
            if root_path == target and name.startswith("."):
                continue
            path = root_path / name
            if path.is_symlink() or not path.is_file():
                continue
            artifacts.add(path.relative_to(target).as_posix())
    for exc in sorted(walk_errors, key=lambda item: str(item)):
        reporter.error("MANIFEST_TREE_READ", ".", f"cannot enumerate course artifacts: {exc}")
    return artifacts


def validate_final_manifest_sync(
    target: Path,
    spec: dict[str, object],
    reporter: Reporter,
) -> None:
    spec_path = target / SPEC_RELATIVE
    manifest_sets: dict[str, set[str]] = {}
    for key in ("generated_files", "core_files", "profile_files", "depth_files"):
        value = spec.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            return  # validate_required_files reports the malformed manifest.
        safe_values: list[str] = []
        for item in value:
            safe = safe_relative(item)
            if safe is None:
                return  # validate_required_files reports unsafe paths.
            safe_values.append(safe)
        if len(set(safe_values)) != len(safe_values):
            reporter.error(
                "MANIFEST_DUPLICATE",
                spec_path,
                f"{key} must not contain duplicate paths",
            )
        manifest_sets[key] = set(safe_values)

    declared = manifest_sets["generated_files"]
    actual = final_artifact_files(target, reporter)
    for relative in sorted(actual - declared):
        reporter.error(
            "MANIFEST_UNDECLARED_FILE",
            relative,
            "regular course artifact is absent from generated_files",
        )
    for relative in sorted(declared - actual):
        reporter.error(
            "MANIFEST_STALE_FILE",
            relative,
            "generated_files declares a path that is not a regular course artifact",
        )

def validate_layout_and_symlinks(target: Path, reporter: Reporter) -> None:
    """Enforce the compact root layout and reject every descendant symlink."""

    try:
        root_entries = sorted(target.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        reporter.error("ROOT_READ", ".", f"cannot inspect course root: {exc}")
        return

    reported_symlinks: set[Path] = set()
    for entry in root_entries:
        if entry.is_symlink():
            reporter.error("GENERATED_SYMLINK", entry.name, "course trees must not contain symlinks")
            reported_symlinks.add(entry)
            continue
        if entry.name.startswith("."):
            continue
        if entry.is_dir() and entry.name not in ALLOWED_TOP_LEVEL_DIRECTORIES:
            reporter.error(
                "ROOT_DIRECTORY",
                entry.name,
                "unexpected top-level directory; allowed directories are "
                + ", ".join(sorted(ALLOWED_TOP_LEVEL_DIRECTORIES)),
            )
        elif entry.is_file() and entry.name not in ALLOWED_ROOT_FILES:
            reporter.error(
                "ROOT_FILE",
                entry.name,
                "visible root files are limited to README.md, TODAY.md, AGENTS.md, and CLAUDE.md",
            )
        elif not entry.is_dir() and not entry.is_file():
            reporter.error(
                "ROOT_ENTRY",
                entry.name,
                "visible root entries must be one of the allowed regular files or directories",
            )

    walk_errors: list[OSError] = []

    def remember_walk_error(exc: OSError) -> None:
        walk_errors.append(exc)

    for root, directories, files in os.walk(target, topdown=True, followlinks=False, onerror=remember_walk_error):
        root_path = Path(root)
        kept_directories: list[str] = []
        for name in sorted(directories):
            path = root_path / name
            if path.is_symlink():
                if path not in reported_symlinks:
                    reporter.error(
                        "GENERATED_SYMLINK",
                        path.relative_to(target),
                        "course trees must not contain symlinked directories",
                    )
                    reported_symlinks.add(path)
            else:
                kept_directories.append(name)
        directories[:] = kept_directories
        for name in sorted(files):
            path = root_path / name
            if path.is_symlink():
                if path not in reported_symlinks:
                    reporter.error(
                        "GENERATED_SYMLINK",
                        path.relative_to(target),
                        "course trees must not contain symlinked files",
                    )
                    reported_symlinks.add(path)
    for exc in sorted(walk_errors, key=lambda item: str(item)):
        reporter.error("TREE_READ", ".", f"cannot inspect descendant entry: {exc}")


def walk_files(target: Path) -> Iterable[Path]:
    for root, directories, files in os.walk(target, followlinks=False):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in SKIP_DIRECTORIES
            and not (Path(root) / directory).is_symlink()
        )
        for filename in sorted(files):
            path = Path(root) / filename
            if path.is_symlink() or not path.is_file():
                continue
            yield path


def unfenced_lines(text: str) -> Iterable[tuple[int, str]]:
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        match = re.match(r"(`{3,}|~{3,})", stripped)
        if match:
            marker = match.group(1)
            marker_char = marker[0]
            if fence is None:
                fence = marker_char
            elif fence == marker_char:
                fence = None
            continue
        if fence is None:
            yield number, line


def validate_placeholders_and_checkboxes(target: Path, reporter: Reporter) -> None:
    for path in walk_files(target):
        if path.is_symlink() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = read_text(path, reporter)
        if text is None:
            continue
        relative = path.relative_to(target)
        for match in PLACEHOLDER_RE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            reporter.error(
                "UNRESOLVED_PLACEHOLDER",
                f"{relative}:{line}",
                f"unresolved placeholder {match.group(0)}",
            )
        if reporter.initial_state and path.suffix.lower() == ".md":
            for line_number, line in unfenced_lines(text):
                if CHECKED_BOX_RE.match(line):
                    reporter.error(
                        "INITIAL_CHECKBOX",
                        f"{relative}:{line_number}",
                        "newly scaffolded courses must not contain checked tasks",
                    )


def extract_link_target(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("<") and ">" in raw:
        return raw[1 : raw.index(">")]
    # CommonMark destinations containing spaces must be angle-bracketed. The first
    # whitespace-delimited token is therefore the destination, not the optional title.
    return raw.split(maxsplit=1)[0] if raw else ""


def validate_one_link(
    raw: str,
    markdown_path: Path,
    target: Path,
    line_number: int,
    reporter: Reporter,
) -> None:
    destination = extract_link_target(raw)
    if not destination or destination.startswith("#"):
        return
    try:
        parsed = urlsplit(destination)
    except ValueError as exc:
        reporter.error(
            "MALFORMED_LINK",
            f"{markdown_path.relative_to(target)}:{line_number}",
            f"cannot parse link destination {destination!r}: {exc}",
        )
        return
    if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
        return
    relative_path = unquote(parsed.path)
    if not relative_path:
        return
    try:
        candidate = (markdown_path.parent / relative_path).resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        reporter.error(
            "MALFORMED_LINK",
            f"{markdown_path.relative_to(target)}:{line_number}",
            f"cannot resolve link destination {destination!r}: {exc}",
        )
        return
    try:
        candidate.relative_to(target)
    except ValueError:
        reporter.error(
            "LINK_ESCAPE",
            f"{markdown_path.relative_to(target)}:{line_number}",
            f"relative link escapes the course directory: {destination}",
        )
        return
    if not candidate.exists():
        reporter.error(
            "BROKEN_LINK",
            f"{markdown_path.relative_to(target)}:{line_number}",
            f"relative link target does not exist: {destination}",
        )


def validate_wiki_link(
    raw: str,
    markdown_path: Path,
    target: Path,
    line_number: int,
    reporter: Reporter,
) -> None:
    destination = re.split(r"\\?\|", raw, maxsplit=1)[0].strip()
    file_part = destination.split("#", 1)[0].strip()
    if not file_part:
        return
    if "\x00" in file_part:
        reporter.error(
            "MALFORMED_LINK",
            f"{markdown_path.relative_to(target)}:{line_number}",
            "Obsidian link contains a NUL character",
        )
        return
    wiki_path = PurePosixPath(file_part)
    if wiki_path.is_absolute() or any(part in {"", ".", ".."} for part in wiki_path.parts):
        reporter.error(
            "LINK_ESCAPE",
            f"{markdown_path.relative_to(target)}:{line_number}",
            f"unsafe Obsidian link destination: {destination}",
        )
        return

    rendered = wiki_path if wiki_path.suffix else PurePosixPath(f"{wiki_path.as_posix()}.md")
    candidates: list[Path] = []
    if len(rendered.parts) > 1:
        candidates.append(target / rendered)
    else:
        candidates.extend((markdown_path.parent / rendered, target / rendered))
        candidates.extend(path for path in walk_files(target) if path.name == rendered.name)

    unique_matches: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            normalized = candidate.resolve(strict=False)
            normalized.relative_to(target)
        except (OSError, RuntimeError, ValueError):
            continue
        try:
            is_regular_file = normalized.exists() and normalized.is_file()
        except OSError:
            is_regular_file = False
        if is_regular_file and normalized not in seen:
            seen.add(normalized)
            unique_matches.append(normalized)
    if not unique_matches:
        reporter.error(
            "BROKEN_LINK",
            f"{markdown_path.relative_to(target)}:{line_number}",
            f"Obsidian link target does not exist: {destination}",
        )
    elif len(rendered.parts) == 1 and len(unique_matches) > 1:
        reporter.error(
            "AMBIGUOUS_WIKI_LINK",
            f"{markdown_path.relative_to(target)}:{line_number}",
            f"Obsidian link {destination!r} matches multiple files; include its path",
        )


def validate_markdown_links(target: Path, reporter: Reporter) -> None:
    for path in walk_files(target):
        if path.is_symlink() or path.suffix.lower() != ".md":
            continue
        text = read_text(path, reporter)
        if text is None:
            continue
        for line_number, line in unfenced_lines(text):
            for match in INLINE_LINK_RE.finditer(line):
                validate_one_link(match.group(1), path, target, line_number, reporter)
            for match in REFERENCE_LINK_RE.finditer(line):
                validate_one_link(match.group(1), path, target, line_number, reporter)
            for match in WIKI_LINK_RE.finditer(line):
                validate_wiki_link(match.group(1), path, target, line_number, reporter)


def normalized_header(header: list[str]) -> list[str]:
    return [column.strip().lstrip("\ufeff") for column in header]


def read_csv_rows(path: Path, reporter: Reporter) -> list[list[str]] | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        reporter.error("CSV_READ", path, f"cannot parse CSV: {exc}")
        return None


def validate_csvs(
    target: Path, spec: dict[str, object], reporter: Reporter
) -> dict[str, tuple[list[str], list[list[str]]]]:
    parsed_csvs: dict[str, tuple[list[str], list[list[str]]]] = {}
    schema_value = spec.get("csv_schemas")
    schemas = schema_value if isinstance(schema_value, dict) else {}
    if not isinstance(schema_value, dict):
        reporter.error("SPEC_CSV_SCHEMAS", target / SPEC_RELATIVE, "csv_schemas must be an object")

    empty_value = spec.get("initially_empty_csvs")
    if not isinstance(empty_value, list) or any(not isinstance(item, str) for item in empty_value):
        reporter.error(
            "SPEC_EMPTY_LOGS",
            target / SPEC_RELATIVE,
            "initially_empty_csvs must be a list of paths",
        )
        initially_empty = set()
    else:
        initially_empty = set(empty_value)

    for path in walk_files(target):
        if path.is_symlink() or path.suffix.lower() != ".csv":
            continue
        relative = path.relative_to(target).as_posix()
        rows = read_csv_rows(path, reporter)
        if rows is None:
            continue
        if not rows:
            reporter.error("CSV_HEADER", relative, "CSV must contain a header row")
            continue
        header = normalized_header(rows[0])
        if not header or any(not column for column in header):
            reporter.error("CSV_HEADER", relative, "CSV header contains a blank field")
        if len(set(header)) != len(header):
            reporter.error("CSV_HEADER", relative, "CSV header fields must be unique")
        width = len(header)
        data_rows: list[list[str]] = []
        for line_number, row in enumerate(rows[1:], start=2):
            if not row or all(not cell.strip() for cell in row):
                continue
            if len(row) != width:
                reporter.error(
                    "CSV_WIDTH",
                    f"{relative}:{line_number}",
                    f"expected {width} columns, found {len(row)}",
                )
            data_rows.append(row)

        expected_schema = schemas.get(relative)
        if expected_schema is None:
            reporter.warning("CSV_SCHEMA_UNDECLARED", relative, "CSV schema is not recorded in COURSE_SPEC")
        elif not isinstance(expected_schema, list) or any(
            not isinstance(column, str) for column in expected_schema
        ):
            reporter.error("CSV_SCHEMA_SPEC", relative, "declared CSV schema must be a list of strings")
        elif header != expected_schema:
            reporter.error(
                "CSV_SCHEMA",
                relative,
                f"header {header!r} does not match declared schema {expected_schema!r}",
            )

        stem = path.stem.lower()
        is_log = stem == "log" or stem.endswith("-log") or stem.endswith("_log")
        if reporter.initial_state and (relative in initially_empty or is_log) and data_rows:
            reporter.error(
                "INITIAL_LOG_DATA",
                relative,
                "newly scaffolded evidence/study logs must contain only their header",
            )
        parsed_csvs[relative] = (header, data_rows)
    return parsed_csvs


def header_index(header: list[str], aliases: set[str]) -> int | None:
    normalized = [re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_") for column in header]
    for index, value in enumerate(normalized):
        if value in aliases:
            return index
    return None


def header_indices(header: list[str], aliases: set[str]) -> list[int]:
    normalized = [re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_") for column in header]
    return [index for index, value in enumerate(normalized) if value in aliases]


def validate_source_locks(
    parsed_csvs: dict[str, tuple[list[str], list[list[str]]]],
    reporter: Reporter,
) -> None:
    locator_aliases = {
        "url",
        "path",
        "uri",
        "url_or_path",
        "source_url",
        "source_path",
        "repository_path",
        "url_or_repository_path",
        "location",
    }
    version_aliases = {
        "version",
        "edition",
        "branch",
        "tag",
        "commit",
        "version_or_commit",
        "version_edition_branch_tag_or_commit",
        "syllabus_year",
    }
    retrieval_aliases = {
        "retrieval",
        "retrieved",
        "retrieval_date",
        "accessed",
        "accessed_date",
        "retrieved_date",
        "retrieved_at",
        "retrieval_timestamp",
        "access_date",
        "last_verified",
        "verified_date",
    }
    authority_aliases = {
        "authority",
        "publisher",
        "maintainer",
        "publisher_or_maintainer",
        "owner",
    }
    status_aliases = {"status", "source_status"}
    valid_statuses = {"current", "provisional", "superseded", "unavailable"}

    for relative in sorted(parsed_csvs):
        normalized_name = re.sub(r"[^a-z0-9]+", "_", Path(relative).stem.lower()).strip("_")
        if normalized_name not in {"source_lock", "sources_lock"}:
            continue
        header, rows = parsed_csvs[relative]
        groups = {
            "URL or repository path": header_indices(header, locator_aliases),
            "version or retrieval date": header_indices(
                header, version_aliases | retrieval_aliases
            ),
            "authority": header_indices(header, authority_aliases),
            "status": header_indices(header, status_aliases),
        }
        for label, indices in groups.items():
            if not indices:
                reporter.error(
                    "SOURCE_LOCK_SCHEMA",
                    relative,
                    f"source lock is missing a recognized {label} column",
                )

        for line_number, row in enumerate(rows, start=2):
            for label, indices in groups.items():
                if indices and not any(
                    index < len(row) and bool(row[index].strip()) for index in indices
                ):
                    reporter.error(
                        "SOURCE_LOCK_INCOMPLETE",
                        f"{relative}:{line_number}",
                        f"non-empty source-lock rows require {label}",
                    )

            locator_indices = groups["URL or repository path"]
            for index in locator_indices:
                if index >= len(row):
                    continue
                locator = row[index].strip()
                if not locator:
                    continue
                try:
                    urlsplit(locator)
                except ValueError as exc:
                    reporter.error(
                        "SOURCE_LOCK_URL",
                        f"{relative}:{line_number}",
                        f"malformed source URL/path {locator!r}: {exc}",
                    )

            status_indices = groups["status"]
            for index in status_indices:
                if index >= len(row) or not row[index].strip():
                    continue
                value = row[index].strip().lower()
                if value not in valid_statuses:
                    reporter.error(
                        "SOURCE_LOCK_STATUS",
                        f"{relative}:{line_number}",
                        f"status must be one of {sorted(valid_statuses)}, not {row[index].strip()!r}",
                    )


def dependencies(value: str) -> list[str]:
    value = value.strip()
    if not value or value.lower() in {"none", "n/a", "na", "-"}:
        return []
    return [part.strip() for part in re.split(r"[;,|]", value) if part.strip()]


def validate_skill_tracker(
    target: Path,
    spec: dict[str, object],
    parsed_csvs: dict[str, tuple[list[str], list[list[str]]]],
    reporter: Reporter,
) -> SkillTrackerData:
    relative = "curriculum/skill-tracker.csv"
    parsed = parsed_csvs.get(relative)
    if parsed is None:
        return SkillTrackerData({}, {})
    header, rows = parsed
    id_index = header_index(header, {"id", "skill_id"})
    dependency_index = header_index(
        header,
        {"depends_on", "dependencies", "prerequisites", "prerequisite_ids"},
    )
    status_index = header_index(header, {"status"})
    for name, index in (("skill ID", id_index), ("dependencies", dependency_index), ("status", status_index)):
        if index is None:
            reporter.error("SKILL_SCHEMA", relative, f"missing required {name} column")
    if id_index is None or dependency_index is None or status_index is None:
        return SkillTrackerData({}, {})

    allowed_value = spec.get("approved_statuses")
    if isinstance(allowed_value, list) and all(
        isinstance(item, str) for item in allowed_value
    ):
        allowed = {
            item for item in allowed_value if isinstance(item, str) and item in EVIDENCE_STATUSES
        }
    else:
        allowed = set(EVIDENCE_STATUSES)
    graph: dict[str, list[str]] = {}
    id_lines: dict[str, int] = {}
    if not rows:
        reporter.error(
            "SKILL_EMPTY",
            relative,
            "skill tracker must contain at least one skill row",
        )
    for line_number, row in enumerate(rows, start=2):
        if max(id_index, dependency_index, status_index) >= len(row):
            continue
        skill_id = row[id_index].strip()
        if not skill_id:
            reporter.error("SKILL_ID", f"{relative}:{line_number}", "skill ID must not be blank")
            continue
        if skill_id in graph:
            reporter.error(
                "SKILL_DUPLICATE",
                f"{relative}:{line_number}",
                f"duplicate skill ID {skill_id!r}; first seen on line {id_lines[skill_id]}",
            )
            continue
        graph[skill_id] = dependencies(row[dependency_index])
        id_lines[skill_id] = line_number
        status = row[status_index].strip()
        if status not in EVIDENCE_STATUSES:
            reporter.error(
                "SKILL_STATUS",
                f"{relative}:{line_number}",
                f"status {status!r} is outside the fixed evidence vocabulary",
            )
        elif allowed and status not in allowed:
            reporter.error(
                "SKILL_STATUS",
                f"{relative}:{line_number}",
                f"status {status!r} is not enabled by approved_statuses",
            )
        elif status != INITIAL_STATUS and reporter.initial_state:
            reporter.error(
                "INITIAL_SKILL_STATUS",
                f"{relative}:{line_number}",
                f"new courses must begin at status {INITIAL_STATUS!r}, not {status!r}",
            )
        elif status != INITIAL_STATUS:
            evidence_index = header_index(header, {"evidence_link", "evidence", "evidence_links"})
            evidence = row[evidence_index].strip() if evidence_index is not None and evidence_index < len(row) else ""
            if not evidence:
                reporter.error("SKILL_EVIDENCE", f"{relative}:{line_number}", "progressed skills require an evidence link")
            else:
                for entry in evidence.split(";"):
                    raw = entry.strip()
                    wiki = WIKI_LINK_RE.fullmatch(raw)
                    markdown = INLINE_LINK_RE.fullmatch(raw)
                    if wiki:
                        validate_wiki_link(wiki.group(1), target / relative, target, line_number, reporter)
                    else:
                        validate_one_link(markdown.group(1) if markdown else raw, target / relative, target, line_number, reporter)

    if rows and not graph:
        reporter.error(
            "SKILL_EMPTY",
            relative,
            "skill tracker must contain at least one valid, non-blank skill ID",
        )

    for skill_id, required in graph.items():
        for dependency in required:
            if dependency not in graph:
                reporter.error(
                    "SKILL_DEPENDENCY",
                    f"{relative}:{id_lines[skill_id]}",
                    f"{skill_id!r} depends on missing skill {dependency!r}",
                )

    state: dict[str, int] = {}
    reported_cycles: set[tuple[str, ...]] = set()

    for start_skill in graph:
        if state.get(start_skill, 0) != 0:
            continue
        state[start_skill] = 1
        path = [start_skill]
        stack: list[tuple[str, Iterable[str]]] = [
            (start_skill, iter(graph.get(start_skill, [])))
        ]
        while stack:
            skill_id, iterator = stack[-1]
            try:
                dependency = next(iterator)
            except StopIteration:
                stack.pop()
                finished = path.pop()
                state[finished] = 2
                continue
            if dependency not in graph:
                continue
            dependency_state = state.get(dependency, 0)
            if dependency_state == 0:
                state[dependency] = 1
                path.append(dependency)
                stack.append((dependency, iter(graph.get(dependency, []))))
            elif dependency_state == 1:
                cycle_start = path.index(dependency)
                nodes = path[cycle_start:]
                rotations = [tuple(nodes[index:] + nodes[:index]) for index in range(len(nodes))]
                canonical_nodes = min(rotations)
                cycle = (*canonical_nodes, canonical_nodes[0])
                if cycle not in reported_cycles:
                    reported_cycles.add(cycle)
                    reporter.error(
                        "SKILL_CYCLE",
                        f"{relative}:{id_lines[skill_id]}",
                        "dependency cycle: " + " -> ".join(cycle),
                    )
    return SkillTrackerData(graph, id_lines)


def normalized_generic_text(value: str) -> str:
    value = value.translate(str.maketrans({"–": "-", "—": "-", "−": "-"}))
    return re.sub(r"\s+", " ", value).strip().rstrip(".").casefold()


def validate_final_customization(
    target: Path,
    spec: dict[str, object],
    parsed_csvs: dict[str, tuple[list[str], list[list[str]]]],
    reporter: Reporter,
) -> None:
    spec_path = target / SPEC_RELATIVE
    for key in ("objective", "target_outcome"):
        value = spec.get(key)
        if not isinstance(value, str) or not value.strip():
            reporter.error(
                "FINAL_SPEC_FIELD",
                spec_path,
                f"final validation requires {key} to be a non-empty string",
            )
    if spec.get("profile") == "mixed":
        rationale = spec.get("profile_rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            reporter.error(
                "FINAL_PROFILE_RATIONALE",
                spec_path,
                "final validation of a mixed course requires a non-empty profile_rationale",
            )

    tracker_relative = "curriculum/skill-tracker.csv"
    parsed = parsed_csvs.get(tracker_relative)
    if parsed is not None:
        header, rows = parsed
        description_index = header_index(
            header,
            {"skill", "skill_description", "capability", "description"},
        )
        if description_index is None:
            reporter.error(
                "FINAL_SKILL_SCHEMA",
                tracker_relative,
                "final validation requires a skill/capability description column",
            )
        else:
            generic_descriptions = {
                normalized_generic_text(value) for value in GENERIC_STARTER_SKILL_DESCRIPTIONS
            }
            for line_number, row in enumerate(rows, start=2):
                if description_index >= len(row):
                    continue
                description = row[description_index].strip()
                if not description:
                    reporter.error(
                        "FINAL_SKILL_DESCRIPTION",
                        f"{tracker_relative}:{line_number}",
                        "final validation requires a non-empty topic-specific skill description",
                    )
                elif normalized_generic_text(description) in generic_descriptions:
                    reporter.error(
                        "GENERIC_SKILL_DESCRIPTION",
                        f"{tracker_relative}:{line_number}",
                        f"replace generic starter skill description {description!r} with a topic-specific capability",
                    )

    for relative, sentinels in GENERIC_SENTINELS.items():
        path = target / relative
        if not path.is_file() or path.is_symlink():
            continue
        text = read_text(path, reporter)
        if text is None:
            continue
        normalized = normalized_generic_text(text)
        for sentinel in sentinels:
            if normalized_generic_text(sentinel) in normalized:
                reporter.error(
                    "GENERIC_COURSE_SENTINEL",
                    relative,
                    f"replace scaffold-only language containing {sentinel!r}",
                )


def capacity_allocation_shares(text: str) -> tuple[list[float], list[float]]:
    in_section = False
    share_index: int | None = None
    non_slack: list[float] = []
    slack: list[float] = []
    for _line_number, line in unfenced_lines(text):
        heading = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            title = re.sub(r"[*_`]", "", heading.group(2)).strip().lower()
            if "capacity allocation" in title:
                in_section = True
                continue
            if in_section:
                break
        if not in_section or "|" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if share_index is None:
            for index, cell in enumerate(cells):
                normalized = normalized_table_label(cell)
                if "share" in normalized and "capacity" in normalized:
                    share_index = index
                    break
            if share_index is not None:
                continue
        if share_index is None or share_index >= len(cells):
            continue
        percentages = [
            float(value)
            for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", cells[share_index])
        ]
        if not percentages:
            continue
        destination = slack if re.search(
            r"\b(?:slack|buffer|unallocated|reserve)\b", line, re.IGNORECASE
        ) else non_slack
        destination.extend(percentages)
    return non_slack, slack


def validate_capacity(target: Path, spec: dict[str, object], reporter: Reporter) -> None:
    weekly_hours = spec.get("capacity_hours_per_week")
    for path in walk_files(target):
        if path.is_symlink() or path.suffix.lower() != ".md":
            continue
        relative = path.relative_to(target)
        if not relative.parts or relative.parts[0] != "tracking" or path.name.startswith("_"):
            continue
        text = read_text(path, reporter)
        if text is None:
            continue
        minute_markers = list(CAPACITY_MARKER_RE.finditer(text))
        percent_markers = list(CAPACITY_PERCENT_RE.finditer(text))
        if len(minute_markers) + len(percent_markers) > 1:
            reporter.error(
                "CAPACITY_MARKERS",
                relative,
                "a weekly plan must contain at most one standardized capacity marker",
            )
        for marker in minute_markers:
            try:
                minutes = int(marker.group(1))
            except (OverflowError, ValueError):
                reporter.error(
                    "CAPACITY_MARKER_VALUE",
                    relative,
                    "planned-minutes marker contains an invalid integer",
                )
                continue
            if weekly_hours is None:
                reporter.warning(
                    "CAPACITY_UNKNOWN",
                    relative,
                    f"planned {minutes} minutes but capacity_hours_per_week is unset; calibrate after week one",
                )
                continue
            if isinstance(weekly_hours, (int, float)) and not isinstance(weekly_hours, bool):
                capacity = float(weekly_hours) * 60
                if minutes > capacity:
                    reporter.error(
                        "CAPACITY_EXCEEDED",
                        relative,
                        f"planned {minutes} minutes exceeds weekly capacity of {capacity:g} minutes",
                    )
                elif minutes > capacity * 0.9:
                    reporter.warning(
                        "CAPACITY_SLACK",
                        relative,
                        f"planned {minutes} of {capacity:g} minutes leaves less than 10% slack",
                    )
        for marker in percent_markers:
            try:
                percent = float(marker.group(1))
            except (OverflowError, ValueError):
                reporter.error(
                    "CAPACITY_MARKER_VALUE",
                    relative,
                    "planned-capacity-percent marker contains an invalid number",
                )
                continue
            if not math.isfinite(percent) or percent > 100:
                reporter.error(
                    "CAPACITY_EXCEEDED",
                    relative,
                    f"planned allocation is {percent:g}% of weekly capacity; it must not exceed 100%",
                )
                continue
            non_slack, slack = capacity_allocation_shares(text)
            if not non_slack:
                reporter.error(
                    "CAPACITY_ALLOCATION",
                    relative,
                    "percent-based weekly plans require a capacity-allocation table",
                )
            else:
                allocated = sum(non_slack)
                if not math.isclose(allocated, percent, abs_tol=0.001):
                    reporter.error(
                        "CAPACITY_ALLOCATION",
                        relative,
                        f"non-slack allocation totals {allocated:g}%, but the marker declares {percent:g}%",
                    )
            expected_slack = 100.0 - percent
            if not slack:
                reporter.error(
                    "CAPACITY_SLACK_MISMATCH",
                    relative,
                    f"allocation table must explicitly retain {expected_slack:g}% slack",
                )
            else:
                recorded_slack = sum(slack)
                if not math.isclose(recorded_slack, expected_slack, abs_tol=0.001):
                    reporter.error(
                        "CAPACITY_SLACK_MISMATCH",
                        relative,
                        f"slack allocation totals {recorded_slack:g}%, expected {expected_slack:g}% from the marker",
                    )
            if weekly_hours is None:
                reporter.warning(
                    "CAPACITY_UNKNOWN",
                    relative,
                    f"planned allocation is {percent:g}%, but capacity_hours_per_week is unset",
                )
                continue
            if isinstance(weekly_hours, (int, float)) and not isinstance(weekly_hours, bool):
                capacity = float(weekly_hours) * 60
                planned = capacity * percent / 100
                if percent > 90:
                    reporter.warning(
                        "CAPACITY_SLACK",
                        relative,
                        f"planned {planned:g} of {capacity:g} minutes leaves less than 10% slack",
                    )


def validate_exact_capacity_marker(
    text: str,
    valid_pattern: re.Pattern[str],
    token_pattern: re.Pattern[str],
    relative: Path,
    code: str,
    marker_name: str,
    reporter: Reporter,
) -> float | None:
    matches = list(valid_pattern.finditer(text))
    token_count = len(token_pattern.findall(text))
    if len(matches) != 1 or token_count != 1:
        reporter.error(
            code,
            relative,
            f"file must contain exactly one valid course:{marker_name} marker; "
            f"found {len(matches)} valid marker(s) and {token_count} marker token(s)",
        )
        return None
    try:
        percent = float(matches[0].group(1))
    except (OverflowError, ValueError):
        percent = math.inf
    if not math.isfinite(percent) or percent <= 0 or percent > 100:
        reporter.error(
            code,
            relative,
            f"course:{marker_name} must be greater than 0 and no more than 100",
        )
        return None
    return percent


def validate_active_week(
    target: Path,
    spec: dict[str, object],
    reporter: Reporter,
) -> None:
    today_relative = Path("TODAY.md")
    today_path = target / today_relative
    if not today_path.is_file() or today_path.is_symlink():
        return
    text = read_text(today_path, reporter)
    if text is None:
        return
    validate_exact_capacity_marker(
        text,
        SESSION_CAPACITY_PERCENT_RE,
        SESSION_CAPACITY_TOKEN_RE,
        today_relative,
        "SESSION_CAPACITY_MARKER",
        "session-capacity-percent",
        reporter,
    )
    matches = list(ACTIVE_WEEK_RE.finditer(text))
    if len(matches) != 1:
        reporter.error(
            "ACTIVE_WEEK_MARKER",
            today_relative,
            f"TODAY.md must contain exactly one course:active-week marker; found {len(matches)}",
        )
        return
    raw_relative = matches[0].group(1).strip()
    safe = safe_relative(raw_relative)
    if safe is None:
        reporter.error(
            "ACTIVE_WEEK_PATH",
            today_relative,
            f"active-week marker contains an unsafe path: {raw_relative!r}",
        )
        return
    relative = PurePosixPath(safe)
    if not relative.parts or relative.parts[0] != "tracking" or relative.suffix != ".md":
        reporter.error(
            "ACTIVE_WEEK_PATH",
            today_relative,
            "active-week target must be a Markdown file under tracking/",
        )
        return
    if has_symlink_component(target, relative):
        reporter.error(
            "ACTIVE_WEEK_PATH",
            today_relative,
            "active-week target or one of its parent directories is a symlink",
        )
        return
    weekly_path = target / relative
    if not weekly_path.is_file() or weekly_path.is_symlink():
        reporter.error(
            "ACTIVE_WEEK_MISSING",
            today_relative,
            f"active-week target is missing or is not a regular file: {safe}",
        )
        return
    weekly_text = read_text(weekly_path, reporter)
    if weekly_text is None:
        return
    validate_exact_capacity_marker(
        weekly_text,
        CAPACITY_PERCENT_RE,
        PLANNED_CAPACITY_TOKEN_RE,
        Path(safe),
        "PLANNED_CAPACITY_MARKER",
        "planned-capacity-percent",
        reporter,
    )
    week_matches = list(WEEK_ID_MARKER_RE.finditer(weekly_text))
    if len(week_matches) != 1:
        reporter.error(
            "WEEK_ID_MARKER",
            Path(safe),
            f"active weekly file must contain exactly one course:week-id marker; found {len(week_matches)}",
        )
        return
    marker_week = week_matches[0].group(1)
    if relative.stem != marker_week:
        reporter.error(
            "WEEK_ID_MISMATCH",
            Path(safe),
            f"weekly filename stem {relative.stem!r} does not match marker {marker_week!r}",
        )
    spec_week = spec.get("week_id")
    if isinstance(spec_week, str) and marker_week != spec_week:
        reporter.error(
            "WEEK_ID_MISMATCH",
            Path(safe),
            f"weekly marker {marker_week!r} does not match COURSE_SPEC week_id {spec_week!r}",
        )


def normalized_table_label(value: str) -> str:
    value = re.sub(r"[`*_]", "", value).strip().lower()
    return re.sub(r"\s+", " ", value)


def validate_dashboard_zero_state(target: Path, reporter: Reporter) -> None:
    relative = Path("tracking/DASHBOARD.md")
    path = target / relative
    if not path.is_file() or path.is_symlink():
        return
    text = read_text(path, reporter)
    if text is None:
        return
    required = {
        "recorded study time",
        "completed course tasks",
        "skills beyond not started",
        "evidence items recorded",
        "open reruns or review items",
    }
    observed: dict[str, tuple[int, str]] = {}
    for line_number, line in unfenced_lines(text):
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        label = normalized_table_label(cells[0])
        if label not in required:
            continue
        if label in observed:
            reporter.error(
                "DASHBOARD_ACTUAL_DUPLICATE",
                f"{relative}:{line_number}",
                f"duplicate zero-state actual row for {cells[0]!r}",
            )
            continue
        observed[label] = (line_number, cells[1])

    for label in sorted(required):
        if label not in observed:
            reporter.error(
                "DASHBOARD_ACTUAL_MISSING",
                relative,
                f"missing zero-state actual row {label!r}",
            )
            continue
        line_number, value = observed[label]
        numbers = re.findall(r"(?<![\w.])[-+]?\d+(?:\.\d+)?", value.replace(",", ""))
        if not numbers:
            reporter.error(
                "DASHBOARD_ACTUAL",
                f"{relative}:{line_number}",
                f"actual value for {label!r} must contain an explicit numeric zero",
            )
            continue
        numeric_values: list[float] = []
        for number in numbers:
            try:
                numeric_values.append(float(number))
            except (OverflowError, ValueError):
                numeric_values.append(math.inf)
        if any(
            not math.isfinite(number) or not math.isclose(number, 0.0, abs_tol=1e-12)
            for number in numeric_values
        ):
            reporter.error(
                "DASHBOARD_ACTUAL",
                f"{relative}:{line_number}",
                f"new courses require zero actuals; found {value!r} for {label!r}",
            )


SUCCESS_SUBJECT_RE = (
    r"(?:baselines?|diagnostics?|courses?|phases?|skills?|capabilit(?:y|ies)|"
    r"assessments?|exams?|mocks?|labs?|projects?|capstones?|builds?|tests?|tasks?|"
    r"modules?|exercises?|sessions?|artifacts?|attempts?|portfolios?)"
)
SUCCESS_RESULT_RE = (
    r"(?:passed|completed|finished|succeeded|successful(?:ly)?|verified|accepted|achieved|mastered)"
)
SUBJECT_FIRST_SUCCESS_RE = re.compile(
    rf"\b{SUCCESS_SUBJECT_RE}\b[^.;\n]{{0,80}}\b{SUCCESS_RESULT_RE}\b",
    re.IGNORECASE,
)
RESULT_FIRST_SUCCESS_RE = re.compile(
    rf"^\s*(?:>\s*)*(?:(?:[-*+]|\d+[.)])\s*)?"
    rf"(?:(?:all|the|these|those)\s+)?\b{SUCCESS_RESULT_RE}\b"
    rf"[^.;\n]{{0,50}}\b{SUCCESS_SUBJECT_RE}\b",
    re.IGNORECASE,
)
SUCCESS_FIELD_LABEL_RE = r"(?:Status|Result|Outcome|Decision|(?:Observed|Actual)\s+result)"
SUCCESS_FIELD_RE = re.compile(
    rf"^\s*(?:>\s*)*(?:(?:[-*+]|\d+[.)])\s*)?"
    rf"(?:(?:\*\*)?{SUCCESS_FIELD_LABEL_RE}\s*:\s*\*\*|"
    rf"(?:\*\*)?{SUCCESS_FIELD_LABEL_RE}(?:\*\*)?\s*:)\s*(.*?)\s*$",
    re.IGNORECASE,
)
ACTUAL_MEASUREMENT_LABEL_RE = (
    r"Actual\s+(?:(?:study|elapsed|practice)\s+)?(?:minutes?|hours?|seconds?|time|"
    r"duration|score|points?|marks?|percent(?:age)?|items?|questions?|tasks?|attempts?|count)"
    r"(?:\s*\([^)]*\))?"
)
ACTUAL_MEASUREMENT_FIELD_RE = re.compile(
    rf"^\s*(?:>\s*)*(?:(?:[-*+]|\d+[.)])\s*)?"
    rf"(?:(?:\*\*)?{ACTUAL_MEASUREMENT_LABEL_RE}\s*:\s*\*\*|"
    rf"(?:\*\*)?{ACTUAL_MEASUREMENT_LABEL_RE}(?:\*\*)?\s*:)\s*(.*?)\s*$",
    re.IGNORECASE,
)
SUCCESS_VALUE_RE = re.compile(
    r"^(?:(?:is|are|was|were|has|have|had)\s+(?:been\s+)?)?"
    r"(?:(?:successfully\s+)?(?:passed|completed|finished|verified|accepted|achieved|"
    r"mastered|approved)(?:\s+successfully)?|succeeded|successful|done|ready|capstone ready)"
    r"[.!]?$",
    re.IGNORECASE,
)


def plain_markdown_value(value: str) -> str:
    return re.sub(r"[`*_]", "", value).strip()


def is_success_value(value: str) -> bool:
    return bool(SUCCESS_VALUE_RE.fullmatch(plain_markdown_value(value)))


def is_nonzero_actual_value(value: str) -> bool:
    cleaned = plain_markdown_value(value).replace("\u00a0", " ").strip()
    if not cleaned or cleaned.casefold() in {
        "-",
        "—",
        "n/a",
        "na",
        "none",
        "unknown",
        "not recorded",
        "not attempted",
    }:
        return False
    clock = re.match(r"^\s*(\d+):(\d+)(?::(\d+))?\b", cleaned)
    if clock:
        return any(int(part) != 0 for part in clock.groups() if part is not None)
    number = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", cleaned)
    if number is None:
        return False
    try:
        numeric = float(number.group(0).replace(",", ""))
    except (OverflowError, ValueError):
        return True
    return not math.isfinite(numeric) or not math.isclose(numeric, 0.0, abs_tol=1e-12)


def markdown_table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def is_markdown_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(
        bool(re.fullmatch(r":?-{3,}:?", cell.replace(" ", ""))) for cell in cells
    )


def normalized_field_label(value: str) -> str:
    return re.sub(r"\s+", " ", plain_markdown_value(value)).strip().rstrip(":").casefold()


def is_actual_measurement_label(value: str) -> bool:
    return bool(
        re.fullmatch(
            ACTUAL_MEASUREMENT_LABEL_RE,
            normalized_field_label(value),
            re.IGNORECASE,
        )
    )


def validate_table_data_row(
    cells: list[str],
    success_indices: set[int],
    actual_indices: set[int],
    relative: Path,
    line_number: int,
    reporter: Reporter,
) -> None:
    success_cell_indices = {
        index for index, cell in enumerate(cells) if is_success_value(cell)
    }
    explicit_success = bool(success_cell_indices & success_indices)
    if not explicit_success and success_cell_indices:
        explicit_success = any(
            re.search(
                rf"\b{SUCCESS_SUBJECT_RE}\b",
                plain_markdown_value(other_cell),
                re.IGNORECASE,
            )
            for index in success_cell_indices
            for other_index, other_cell in enumerate(cells)
            if other_index != index
        )
    if explicit_success:
        reporter.error(
            "ZERO_STATE_SUCCESS_FIELD",
            f"{relative}:{line_number}",
            "table data row contains an explicit completed-success value",
        )

    for index in actual_indices:
        if index < len(cells) and is_nonzero_actual_value(cells[index]):
            reporter.error(
                "ZERO_STATE_ACTUAL_FIELD",
                f"{relative}:{line_number}",
                f"table actual-measurement field must be blank or zero, not {cells[index]!r}",
            )

    # Also recognize a compact key/value row without a formal header.
    for index, cell in enumerate(cells[:-1]):
        if is_actual_measurement_label(cell) and is_nonzero_actual_value(cells[index + 1]):
            reporter.error(
                "ZERO_STATE_ACTUAL_FIELD",
                f"{relative}:{line_number}",
                f"table actual-measurement field must be blank or zero, not {cells[index + 1]!r}",
            )


def validate_zero_state_tables(text: str, relative: Path, reporter: Reporter) -> None:
    lines = list(unfenced_lines(text))
    index = 0
    while index < len(lines):
        line_number, line = lines[index]
        cells = markdown_table_cells(line)
        if cells is None:
            index += 1
            continue
        next_cells = (
            markdown_table_cells(lines[index + 1][1]) if index + 1 < len(lines) else None
        )
        if next_cells is not None and is_markdown_table_separator(next_cells):
            success_indices = {
                position
                for position, cell in enumerate(cells)
                if normalized_field_label(cell)
                in {"status", "result", "outcome", "decision", "observed result", "actual result"}
            }
            actual_indices = {
                position
                for position, cell in enumerate(cells)
                if is_actual_measurement_label(cell)
            }
            index += 2
            while index < len(lines):
                data_line_number, data_line = lines[index]
                data_cells = markdown_table_cells(data_line)
                if data_cells is None or is_markdown_table_separator(data_cells):
                    break
                validate_table_data_row(
                    data_cells,
                    success_indices,
                    actual_indices,
                    relative,
                    data_line_number,
                    reporter,
                )
                index += 1
            continue
        if not is_markdown_table_separator(cells):
            validate_table_data_row(cells, set(), set(), relative, line_number, reporter)
        index += 1


def validate_zero_state_success_claims(target: Path, reporter: Reporter) -> None:
    contextual = re.compile(
        r"\b(?:must|should|would|will|when|once|until|before|after|if|unless|"
        r"only when|requires?|criteria|planned|target|goal|outcome)\b",
        re.IGNORECASE,
    )
    negated = re.compile(r"\b(?:no|not|never|without|unknown|unverified)\b", re.IGNORECASE)
    for path in walk_files(target):
        if (
            path.is_symlink()
            or path.suffix.lower() != ".md"
            or path.name.startswith("_")
            or path.name in {"AGENTS.md", "CLAUDE.md"}
        ):
            continue
        text = read_text(path, reporter)
        if text is None:
            continue
        relative = path.relative_to(target)
        validate_zero_state_tables(text, relative, reporter)
        for line_number, line in unfenced_lines(text):
            stripped = line.strip()
            success_field = SUCCESS_FIELD_RE.match(stripped)
            if success_field is not None and is_success_value(success_field.group(1)):
                reporter.error(
                    "ZERO_STATE_SUCCESS_FIELD",
                    f"{relative}:{line_number}",
                    f"explicit success field must remain unset, not {success_field.group(1)!r}",
                )
            actual_field = ACTUAL_MEASUREMENT_FIELD_RE.match(stripped)
            if actual_field is not None and is_nonzero_actual_value(actual_field.group(1)):
                reporter.error(
                    "ZERO_STATE_ACTUAL_FIELD",
                    f"{relative}:{line_number}",
                    f"actual-measurement field must be blank or zero, not {actual_field.group(1)!r}",
                )
            if (
                not stripped
                or stripped.startswith("<!--")
                or stripped.startswith("|")
                or "[ ]" in stripped
                or BOLD_GATE_RE.match(stripped)
                or contextual.search(stripped)
                or negated.search(stripped)
            ):
                continue
            match = SUBJECT_FIRST_SUCCESS_RE.search(stripped)
            if match is None:
                match = RESULT_FIRST_SUCCESS_RE.match(stripped)
            if match:
                reporter.error(
                    "ZERO_STATE_SUCCESS_CLAIM",
                    f"{relative}:{line_number}",
                    f"new courses cannot assert completed success: {match.group(0)!r}",
                )


def marker_ids(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def one_marker(
    pattern: re.Pattern[str],
    text: str,
    relative: Path,
    marker_name: str,
    reporter: Reporter,
) -> re.Match[str] | None:
    matches = list(pattern.finditer(text))
    if not matches:
        reporter.error(
            "MODULE_MARKER_MISSING",
            relative,
            f"module requires exactly one course:{marker_name} marker",
        )
        return None
    if len(matches) > 1:
        reporter.error(
            "MODULE_MARKER_DUPLICATE",
            relative,
            f"module contains {len(matches)} course:{marker_name} markers",
        )
    return matches[0]


def validate_topic_graph(
    target: Path,
    tracker: SkillTrackerData,
    reporter: Reporter,
) -> None:
    modules_root = target / "curriculum/modules"
    try:
        modules = sorted(
            path
            for path in modules_root.glob("*.md")
            if not path.name.startswith("_") and path.is_file() and not path.is_symlink()
        )
    except OSError as exc:
        reporter.error("MODULES_READ", "curriculum/modules", f"cannot inspect modules: {exc}")
        return
    if not modules:
        reporter.error(
            "MODULES_MISSING",
            "curriculum/modules",
            "course must contain at least one non-template module document",
        )
        return

    module_orders: dict[Path, int] = {}
    order_owners: dict[int, Path] = {}
    module_skills: dict[Path, list[str]] = {}
    module_prerequisites: dict[Path, list[str]] = {}
    skill_owners: dict[str, Path] = {}

    for path in modules:
        relative = path.relative_to(target)
        text = read_text(path, reporter)
        if text is None:
            continue
        order_match = one_marker(MODULE_ORDER_RE, text, relative, "module-order", reporter)
        skills_match = one_marker(MODULE_SKILLS_RE, text, relative, "module-skills", reporter)
        prerequisite_match = one_marker(
            MODULE_PREREQUISITES_RE,
            text,
            relative,
            "module-prerequisites",
            reporter,
        )
        if order_match is not None:
            try:
                order = int(order_match.group(1))
            except (OverflowError, ValueError):
                reporter.error("MODULE_ORDER", relative, "module order is not a valid integer")
                order = None
            if order is not None and order in order_owners:
                reporter.error(
                    "MODULE_ORDER_DUPLICATE",
                    relative,
                    f"module order {order} is already owned by {order_owners[order].relative_to(target)}",
                )
            elif order is not None:
                module_orders[path] = order
                order_owners[order] = path

        skills = marker_ids(skills_match.group(1)) if skills_match is not None else []
        prerequisites = (
            marker_ids(prerequisite_match.group(1)) if prerequisite_match is not None else []
        )
        module_skills[path] = skills
        module_prerequisites[path] = prerequisites
        if not skills:
            reporter.error(
                "MODULE_SKILLS_EMPTY",
                relative,
                "course:module-skills must own at least one tracker skill",
            )
        if len(set(skills)) != len(skills):
            reporter.error("MODULE_SKILLS_DUPLICATE", relative, "module-skills contains duplicate IDs")
        if len(set(prerequisites)) != len(prerequisites):
            reporter.error(
                "MODULE_PREREQUISITES_DUPLICATE",
                relative,
                "module-prerequisites contains duplicate IDs",
            )

        for skill_id in [*skills, *prerequisites]:
            if skill_id not in tracker.ids:
                reporter.error(
                    "MODULE_SKILL_UNKNOWN",
                    relative,
                    f"module marker references skill ID {skill_id!r}, absent from the tracker",
                )
        overlap = sorted(set(skills) & set(prerequisites))
        for skill_id in overlap:
            reporter.error(
                "MODULE_ENTRY_PREREQUISITE",
                relative,
                f"entry prerequisite {skill_id!r} cannot be taught by the same module",
            )
        for skill_id in skills:
            if skill_id in skill_owners:
                reporter.error(
                    "MODULE_SKILL_OWNER",
                    relative,
                    f"skill {skill_id!r} is already owned by {skill_owners[skill_id].relative_to(target)}",
                )
            else:
                skill_owners[skill_id] = path

    for skill_id in sorted(tracker.ids - set(skill_owners)):
        reporter.error(
            "MODULE_SKILL_UNOWNED",
            "curriculum/modules",
            f"tracker skill {skill_id!r} is not owned by any module",
        )

    for module_path, skills in module_skills.items():
        declared = set(module_prerequisites.get(module_path, []))
        required_cross_module: set[str] = set()
        for skill_id in skills:
            for dependency in tracker.dependencies.get(skill_id, []):
                dependency_owner = skill_owners.get(dependency)
                if dependency_owner is not None and dependency_owner != module_path:
                    required_cross_module.add(dependency)
        for dependency in sorted(required_cross_module - declared):
            reporter.error(
                "MODULE_PREREQUISITE_MISSING",
                module_path.relative_to(target),
                f"module-prerequisites must include cross-module tracker dependency {dependency!r}",
            )

    for module_path, prerequisites in module_prerequisites.items():
        module_order = module_orders.get(module_path)
        if module_order is None:
            continue
        for skill_id in prerequisites:
            owner = skill_owners.get(skill_id)
            owner_order = module_orders.get(owner) if owner is not None else None
            if skill_id in tracker.ids and owner is None:
                reporter.error(
                    "MODULE_PREREQUISITE_OWNER",
                    module_path.relative_to(target),
                    f"entry prerequisite {skill_id!r} is not owned by a module",
                )
            elif owner_order is not None and owner_order >= module_order:
                reporter.error(
                    "MODULE_PREREQUISITE_ORDER",
                    module_path.relative_to(target),
                    f"entry prerequisite {skill_id!r} is owned by module order {owner_order}, not an earlier module",
                )

    for skill_id, required in sorted(tracker.dependencies.items()):
        owner = skill_owners.get(skill_id)
        owner_order = module_orders.get(owner) if owner is not None else None
        if owner_order is None:
            continue
        for dependency in required:
            dependency_owner = skill_owners.get(dependency)
            dependency_order = (
                module_orders.get(dependency_owner) if dependency_owner is not None else None
            )
            if dependency_order is not None and dependency_order > owner_order:
                reporter.error(
                    "MODULE_DEPENDENCY_ORDER",
                    f"curriculum/skill-tracker.csv:{tracker.id_lines.get(skill_id, 0)}",
                    f"{skill_id!r} depends on {dependency!r}, which is owned by later module order {dependency_order}",
                )


LEGACY_LABEL_RE = r"(?:Skills?|Skill\s+IDs?|Prerequisites)"
LEGACY_FIELD_RE = re.compile(
    rf"^\s*(?:>\s*)*(?:(?:[-*+]|\d+[.)])\s*)?(?:(?:\*\*)?{LEGACY_LABEL_RE}\s*:\s*\*\*|"
    rf"(?:\*\*)?{LEGACY_LABEL_RE}(?:\*\*)?\s*:)\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
BOLD_GATE_RE = re.compile(
    r"^\s*(?:>\s*)*(?:(?:[-*+]|\d+[.)])\s*)?\*\*Gate(?:\s+[^*:]+)?(?::\*\*|\*\*\s*:)\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
LEGACY_ID_RE = re.compile(r"(?<![A-Za-z0-9_.-])([A-Z][A-Z0-9_.-]*\d[A-Z0-9_.-]*)(?![A-Za-z0-9_.-])")
NON_SKILL_ID_RE = re.compile(
    r"^(?:LAB|L|MODULE|MOD|M|SOURCE|SRC|REF|GATE|G|PROJECT|PROJ|P)[-_]?\d",
    re.IGNORECASE,
)


def validate_skill_references(
    target: Path,
    tracker: SkillTrackerData,
    reporter: Reporter,
) -> None:
    roadmap = Path("tracking/ROADMAP.md")
    roadmap_has_marker = False
    for path in walk_files(target):
        if path.is_symlink() or path.suffix.lower() != ".md":
            continue
        text = read_text(path, reporter)
        if text is None:
            continue
        relative = path.relative_to(target)
        matches = list(SKILL_REFS_RE.finditer(text))
        if relative == roadmap:
            roadmap_has_marker = bool(matches)
        for match in matches:
            ids = marker_ids(match.group(1))
            line_number = text.count("\n", 0, match.start()) + 1
            if not ids:
                reporter.error(
                    "SKILL_REFS_EMPTY",
                    f"{relative}:{line_number}",
                    "course:skill-refs must contain at least one tracker ID",
                )
            if len(set(ids)) != len(ids):
                reporter.error(
                    "SKILL_REFS_DUPLICATE",
                    f"{relative}:{line_number}",
                    "course:skill-refs contains duplicate IDs",
                )
            for skill_id in ids:
                if skill_id not in tracker.ids:
                    reporter.error(
                        "SKILL_REF_UNKNOWN",
                        f"{relative}:{line_number}",
                        f"skill reference {skill_id!r} is absent from the tracker",
                    )

        is_practice_artifact = (
            bool(relative.parts)
            and relative.parts[0] == "practice"
            and not path.name.startswith("_")
            and path.name.lower() != "readme.md"
        )
        mentions_project_or_capstone = bool(
            re.search(r"\b(?:project|capstone)\b", relative.as_posix(), re.IGNORECASE)
            or re.search(r"^#{1,6}\s+.*\b(?:project|capstone)\b", text, re.IGNORECASE | re.MULTILINE)
        )
        references_gate = bool(
            re.search(r"\bskill\s+(?:gate|ids?|requirements?)\b", text, re.IGNORECASE)
            or BOLD_GATE_RE.search(text)
            or LEGACY_FIELD_RE.search(text)
        )
        if is_practice_artifact and mentions_project_or_capstone and references_gate and not matches:
            reporter.error(
                "SKILL_REFS_MISSING",
                relative,
                "project/capstone artifacts that reference skill gates require course:skill-refs",
            )

        for line_number, line in unfenced_lines(text):
            legacy = LEGACY_FIELD_RE.match(line) or BOLD_GATE_RE.match(line)
            if legacy is None:
                continue
            for candidate in LEGACY_ID_RE.findall(legacy.group(1)):
                if candidate in tracker.ids or NON_SKILL_ID_RE.match(candidate):
                    continue
                reporter.error(
                    "LEGACY_SKILL_REF_UNKNOWN",
                    f"{relative}:{line_number}",
                    f"legacy skill reference {candidate!r} is absent from the tracker; use course:skill-refs",
                )

    if not roadmap_has_marker:
        reporter.error(
            "SKILL_REFS_MISSING",
            roadmap,
            "roadmap requires a course:skill-refs marker tied to the tracker",
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        raw_target = Path(args.target)
    except (TypeError, ValueError) as exc:
        print(f"validation error: invalid target path: {exc}", file=sys.stderr)
        return 2
    if not raw_target.is_absolute():
        print("validation error: target must be an absolute path", file=sys.stderr)
        return 2
    try:
        if os.path.lexists(raw_target) and raw_target.is_symlink():
            print(f"validation error: target must not be a symlink: {raw_target}", file=sys.stderr)
            return 2
        target = raw_target.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"validation error: cannot resolve target: {exc}", file=sys.stderr)
        return 2
    if not target.is_dir() or target.is_symlink():
        print(f"validation error: target is not a real directory: {target}", file=sys.stderr)
        return 2

    reporter = Reporter(initial_state=not args.in_progress)
    validate_layout_and_symlinks(target, reporter)
    spec = load_spec(target, reporter)
    if spec is not None:
        validate_spec(spec, target, reporter)
        validate_required_files(
            target,
            spec,
            reporter,
            compare_current_templates=args.scaffold,
        )
        if not args.scaffold:
            validate_final_manifest_sync(target, spec, reporter)
        parsed_csvs = validate_csvs(target, spec, reporter)
        validate_source_locks(parsed_csvs, reporter)
        tracker = validate_skill_tracker(target, spec, parsed_csvs, reporter)
        if not args.scaffold:
            validate_final_customization(target, spec, parsed_csvs, reporter)
        validate_topic_graph(target, tracker, reporter)
        validate_skill_references(target, tracker, reporter)
        validate_active_week(target, spec, reporter)
        validate_capacity(target, spec, reporter)
        if reporter.initial_state:
            validate_dashboard_zero_state(target, reporter)
        if spec.get("schema_version") == "1.1" or "modules" in spec or "skill_references" in spec:
            from sync_course import plan_updates
            try:
                pending = plan_updates(target)
                for path in pending:
                    reporter.error("DERIVED_METADATA_STALE", path.relative_to(target), "canonical mapping and derived metadata disagree; preview sync_course.py")
            except (ValueError, OSError, KeyError, TypeError, StopIteration) as exc:
                reporter.error("CANONICAL_METADATA", SPEC_RELATIVE, str(exc))
    validate_placeholders_and_checkboxes(target, reporter)
    if reporter.initial_state:
        validate_zero_state_success_claims(target, reporter)
    validate_markdown_links(target, reporter)
    reporter.emit()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
