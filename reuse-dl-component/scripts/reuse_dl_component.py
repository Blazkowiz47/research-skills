#!/usr/bin/env python3
"""Reuse same-named dl-core local components across experiment repositories."""

from __future__ import annotations

import argparse
from datetime import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path


COMPONENTS = {
    "dataset": {"dl_core_type": "dataset", "directory": "datasets"},
    "datasets": {"dl_core_type": "dataset", "directory": "datasets"},
    "metric_manager": {
        "dl_core_type": "metric_manager",
        "directory": "metric_managers",
    },
    "metric-manager": {
        "dl_core_type": "metric_manager",
        "directory": "metric_managers",
    },
    "metric_managers": {
        "dl_core_type": "metric_manager",
        "directory": "metric_managers",
    },
    "metric-managers": {
        "dl_core_type": "metric_manager",
        "directory": "metric_managers",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a same-named dl-core dataset or metric_manager component."
    )
    parser.add_argument("--source-project", help="Source dl-core experiment repository.")
    parser.add_argument(
        "--dest-project",
        "--destination-project",
        dest="dest_project",
        help="Destination dl-core experiment repository.",
    )
    parser.add_argument(
        "--component-type",
        "--type",
        choices=sorted(COMPONENTS),
        help="Component type to reuse: dataset or metric_manager.",
    )
    parser.add_argument("--name", help="Same component name in source and destination.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing destination component after backing it up.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without running dl-core add or copying files.",
    )
    return parser.parse_args()


def is_interactive() -> bool:
    return sys.stdin.isatty()


def prompt_value(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        raise SystemExit(f"Missing required value: {label}")
    return value


def resolve_required_args(args: argparse.Namespace) -> argparse.Namespace:
    if is_interactive():
        if not args.source_project:
            args.source_project = prompt_value("Source project path")
        if not args.dest_project:
            args.dest_project = prompt_value("Destination project path")
        if not args.component_type:
            args.component_type = prompt_value("Component type (dataset or metric_manager)")
        if not args.name:
            args.name = prompt_value("Component name")

    missing = [
        flag
        for flag, value in [
            ("--source-project", args.source_project),
            ("--dest-project", args.dest_project),
            ("--component-type", args.component_type),
            ("--name", args.name),
        ]
        if not value
    ]
    if missing:
        raise SystemExit(f"Missing required arguments: {', '.join(missing)}")
    return args


def normalize_component_type(value: str) -> dict[str, str]:
    key = value.strip().lower().replace(" ", "_")
    if key not in COMPONENTS:
        supported = ", ".join(sorted(COMPONENTS))
        raise SystemExit(f"Unsupported component type '{value}'. Use one of: {supported}")
    return COMPONENTS[key]


def to_module_name(value: str) -> str:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value.strip())
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    if not slug:
        raise SystemExit("Component name must contain at least one alphanumeric character.")
    module_name = slug.replace("-", "_")
    if module_name[0].isdigit():
        module_name = f"exp_{module_name}"
    return module_name


def find_project_root(path: Path) -> Path:
    start = path.expanduser().resolve()
    candidates = [start, *start.parents] if start.exists() else [start, *start.parents]
    for candidate in candidates:
        if (candidate / "pyproject.toml").exists() and (candidate / "src").is_dir():
            return candidate
    raise SystemExit(
        f"Could not find a dl-core experiment root from {path}. "
        "Expected pyproject.toml and src/."
    )


def component_path(project_root: Path, directory: str, module_name: str) -> Path:
    return project_root / "src" / directory / f"{module_name}.py"


def render_command(command: list[str]) -> str:
    return " ".join(command)


def run(command: list[str], cwd: Path, dry_run: bool) -> None:
    print(f"+ {render_command(command)}")
    if dry_run:
        return
    subprocess.run(command, cwd=str(cwd), check=True)


def backup_existing(path: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    backup = path.with_name(
        f"{path.name}.backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    print(f"+ mv {path} {backup}")
    if not dry_run:
        shutil.move(str(path), str(backup))


def validate_python_syntax(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")


def main() -> int:
    args = resolve_required_args(parse_args())
    component = normalize_component_type(args.component_type)
    module_name = to_module_name(args.name)

    source_root = find_project_root(Path(args.source_project))
    dest_root = find_project_root(Path(args.dest_project))
    if source_root == dest_root:
        raise SystemExit("Source and destination projects resolve to the same repo.")

    source_file = component_path(source_root, component["directory"], module_name)
    dest_file = component_path(dest_root, component["directory"], module_name)
    if not source_file.exists():
        raise SystemExit(f"Source component file not found: {source_file}")

    print(f"Source project: {source_root}")
    print(f"Destination project: {dest_root}")
    print(f"Component type: {component['dl_core_type']}")
    print(f"Component name: {args.name}")
    print(f"Source file: {source_file}")
    print(f"Destination file: {dest_file}")

    if dest_file.exists() and not args.force:
        raise SystemExit(
            f"Destination component already exists: {dest_file}\n"
            "Re-run with --force only if overwriting is intended."
        )

    if dest_file.exists():
        backup_existing(dest_file, args.dry_run)

    command = ["uv", "run", "dl-core", "add", component["dl_core_type"], args.name]
    if args.force:
        command.append("--force")
    run(command, dest_root, args.dry_run)

    print(f"+ cp {source_file} {dest_file}")
    if not args.dry_run:
        shutil.copy2(source_file, dest_file)
        validate_python_syntax(dest_file)

    print("\nReused component successfully.")
    print("Next: inspect imports and run the destination repo's dl-core smoke checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
