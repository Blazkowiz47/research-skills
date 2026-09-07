#!/usr/bin/env python3
"""Reuse same-named dl-core local components across experiment repositories."""

from __future__ import annotations

import argparse
import ast
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
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
        help="Replace an existing destination component, restoring prior files on failure.",
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
    if not start.exists():
        raise SystemExit(f"Project path does not exist: {path}")
    candidates = [start, *start.parents]
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
    return shlex.join(command)


def run(command: list[str], cwd: Path, dry_run: bool) -> None:
    print(f"+ {render_command(command)}")
    if dry_run:
        return
    subprocess.run(command, cwd=str(cwd), check=True)


def validate_python_syntax(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")


def inspect_imports(source_file: Path, source_root: Path, dest_root: Path) -> list[str]:
    """Find missing project-local imports without executing user code."""
    missing: set[str] = set()
    package = source_file.relative_to(source_root).with_suffix("").parts[:-1]
    for node in ast.walk(ast.parse(source_file.read_text(encoding="utf-8"))):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            prefix = list(package[:len(package) - node.level + 1]) if node.level else []
            base = [*prefix, *(node.module.split(".") if node.module else [])]
            modules = [".".join(base), *[".".join([*base, alias.name]) for alias in node.names if alias.name != "*"]]
        for module in modules:
            if not module:
                continue
            relative = Path(*module.split("."))
            for base in (Path(), Path("src")):
                candidates = (base / relative.with_suffix(".py"), base / relative / "__init__.py")
                for candidate in candidates:
                    if (source_root / candidate).is_file() and not (dest_root / candidate).is_file():
                        if source_root / candidate != source_file:
                            missing.add(candidate.as_posix())
    return sorted(missing)


def validate_component_exports(component: Path) -> None:
    """Catch definitely missing exports without importing the component."""
    body = ast.parse(component.read_text(encoding="utf-8")).body
    names: set[str] = set()
    uncertain = False
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            uncertain |= node.name == "__getattr__"
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    uncertain = True
                else:
                    names.add(alias.asname or (alias.name.split(".")[0] if isinstance(node, ast.Import) else alias.name))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                names.update(child.id for child in ast.walk(target) if isinstance(child, ast.Name))
        elif isinstance(node, (ast.If, ast.Try)):
            uncertain = True
    init = component.parent / "__init__.py"
    if uncertain or not init.is_file():
        return
    for node in ast.walk(ast.parse(init.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module == component.stem:
            missing = {alias.name for alias in node.names if alias.name != "*"} - names
            if missing:
                raise RuntimeError(f"Generated exports are absent from {component.name}: {', '.join(sorted(missing))}")


def copy_component(source_file: Path, dest_file: Path, dest_root: Path, command: list[str]) -> None:
    """Restore the component and package exports if scaffolding or copying fails."""
    src_root = dest_root / "src"
    if not dest_file.parent.is_dir():
        raise SystemExit(f"Expected legacy component directory {dest_file.parent}. Inspect the destination layout before copying.")
    exports = set(src_root.rglob("__init__.py")) | {src_root / "__init__.py", dest_file.parent / "__init__.py"}
    tracked = exports | {dest_file}
    for path in tracked:
        parents = (parent for parent in path.parents if dest_root in parent.parents)
        if path.is_symlink() or any(parent.is_symlink() for parent in parents):
            raise SystemExit(f"Refusing to replace a symlinked component/export: {path}")
    existing = {p: p.read_bytes() for p in tracked if p.exists()}
    modes = {p: p.stat().st_mode for p in existing}
    backup = Path(tempfile.mkdtemp(prefix="reuse-dl-component-"))
    retain_backup = False
    staged: Path | None = None
    try:
        for path, content in existing.items():
            saved = backup / path.relative_to(dest_root)
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(content)
        try:
            run(command, dest_root, False)
            if not dest_file.is_file():
                raise RuntimeError(f"dl-core generated no component at the expected path: {dest_file}")
            with tempfile.NamedTemporaryFile(dir=dest_file.parent, prefix=".reuse-", suffix=".py", delete=False) as handle:
                staged = Path(handle.name)
            shutil.copy2(source_file, staged)
            validate_python_syntax(staged)
            os.replace(staged, dest_file)
            for path in set(src_root.rglob("__init__.py")) | {dest_file}:
                if path not in existing or path.read_bytes() != existing[path]:
                    validate_python_syntax(path)
            validate_component_exports(dest_file)
        except BaseException:
            # Try every restoration even if one path has become unwritable.
            errors = []
            for path in tracked | set(src_root.rglob("__init__.py")):
                try:
                    if path in existing:
                        if not path.exists() or path.read_bytes() != existing[path]:
                            path.write_bytes(existing[path])
                        path.chmod(modes[path])
                    elif path.exists():
                        path.unlink()
                except OSError as exc:
                    errors.append(str(exc))
            if errors:
                retain_backup = True
                print(f"Some files could not be restored. Original contents retained at {backup}: " + "; ".join(errors), file=sys.stderr)
            raise
    finally:
        if staged is not None and staged.exists():
            staged.unlink()
        if not retain_backup:
            shutil.rmtree(backup)


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
    validate_python_syntax(source_file)
    missing = inspect_imports(source_file, source_root, dest_root)
    if missing:
        raise SystemExit("Missing destination project-local dependencies; review/copy these first: " + ", ".join(missing))

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

    command = ["uv", "run", "--no-sync", "dl-core", "add", component["dl_core_type"], args.name]
    if args.force:
        command.append("--force")
    if args.dry_run:
        run(command, dest_root, True)
        print(f"Would copy {source_file} to {dest_file} and validate component/exports.")
        return 0
    copy_component(source_file, dest_file, dest_root, command)

    print("\nReused component successfully.")
    print("Checked source syntax, local import paths, and generated component/export syntax.")
    print("Runtime imports and dataset/model behavior still need a targeted project check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
