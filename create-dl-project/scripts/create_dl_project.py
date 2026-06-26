#!/usr/bin/env python3
"""Create a uv deep-learning project using Sushrut's dl-init workflow."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


BACKENDS = {
    "core": {"package": "deep-learning-core", "flag": None},
    "azure": {"package": "deep-learning-azure", "flag": "--with-azure"},
    "mlflow": {"package": "deep-learning-mlflow", "flag": "--with-mlflow"},
    "wandb": {"package": "deep-learning-wandb", "flag": "--with-wandb"},
}

DEFAULT_TORCH_VERSION = "2.8.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a uv deep-learning experiment project."
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--path", help="Full target project directory.")
    target.add_argument("--parent", help="Parent directory for the new project.")
    parser.add_argument("--name", help="Project directory name. Required with --parent.")
    parser.add_argument(
        "--backend",
        choices=sorted(BACKENDS),
        help="Backend package/tracker choice.",
    )
    parser.add_argument(
        "--torch-version",
        default=None,
        help=f"Torch version to install. Default when prompted: {DEFAULT_TORCH_VERSION}.",
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Allow an existing non-empty target directory.",
    )
    parser.add_argument(
        "--create-parent",
        action="store_true",
        help="Create the parent directory if it does not exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the actions without installing uv or creating the project.",
    )
    return parser.parse_args()


def is_interactive() -> bool:
    return sys.stdin.isatty()


def prompt_value(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    if default is not None:
        return default
    raise SystemExit(f"Missing required value: {label}")


def prompt_backend() -> str:
    print("Backend choices:")
    print("  core   - deep-learning-core, no external tracker")
    print("  azure  - deep-learning-azure, dl-init --with-azure")
    print("  mlflow - deep-learning-mlflow, dl-init --with-mlflow")
    print("  wandb  - deep-learning-wandb, dl-init --with-wandb")
    while True:
        value = prompt_value("Backend").lower()
        if value in BACKENDS:
            return value
        print("Choose one of: core, azure, mlflow, wandb")


def resolve_target(args: argparse.Namespace) -> Path:
    if args.path:
        return Path(args.path).expanduser().resolve()

    parent = args.parent
    name = args.name
    if is_interactive():
        if not parent:
            parent = prompt_value("Project parent directory")
        if not name:
            name = prompt_value("Project folder name")

    if not parent or not name:
        raise SystemExit("Provide --path, or provide both --parent and --name.")
    return (Path(parent).expanduser() / name).resolve()


def resolve_backend(args: argparse.Namespace) -> str:
    if args.backend:
        return args.backend
    if is_interactive():
        return prompt_backend()
    raise SystemExit("Provide --backend with one of: core, azure, mlflow, wandb.")


def resolve_torch_version(args: argparse.Namespace) -> str:
    if args.torch_version:
        return args.torch_version
    if is_interactive():
        return prompt_value("Torch version", DEFAULT_TORCH_VERSION)
    raise SystemExit(
        f"Provide --torch-version, for example --torch-version {DEFAULT_TORCH_VERSION}."
    )


def confirm(message: str) -> bool:
    if not is_interactive():
        return False
    answer = input(f"{message} [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def prepare_target(project_dir: Path, args: argparse.Namespace) -> None:
    parent = project_dir.parent
    if not parent.exists():
        if args.create_parent or confirm(f"Create parent directory {parent}?"):
            parent.mkdir(parents=True, exist_ok=True)
        else:
            raise SystemExit(f"Parent directory does not exist: {parent}")

    if project_dir.exists():
        entries = list(project_dir.iterdir())
        if entries and not args.allow_existing:
            raise SystemExit(
                f"Target directory already exists and is non-empty: {project_dir}\n"
                "Re-run with --allow-existing only if you explicitly want to reuse it."
            )
    else:
        project_dir.mkdir(parents=True)


def candidate_paths() -> list[str]:
    home = Path.home()
    return [
        str(home / ".local" / "bin"),
        str(home / ".cargo" / "bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ]


def find_uv(extra_paths: list[str] | None = None) -> str | None:
    path = os.environ.get("PATH", "")
    if extra_paths:
        path = os.pathsep.join(extra_paths + [path])
    uv = shutil.which("uv", path=path)
    if uv:
        return uv
    for directory in candidate_paths():
        candidate = Path(directory) / "uv"
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def install_uv() -> str:
    installer = "https://astral.sh/uv/install.sh"
    curl = shutil.which("curl")
    wget = shutil.which("wget")
    if curl:
        command = f"{curl} -LsSf {installer} | sh"
    elif wget:
        command = f"{wget} -qO- {installer} | sh"
    else:
        raise SystemExit("Cannot install uv: neither curl nor wget is available.")

    print("uv was not found; installing uv with the official Astral installer.")
    subprocess.run(command, shell=True, check=True)
    uv = find_uv(candidate_paths())
    if not uv:
        raise SystemExit(
            "uv installation finished, but uv was not found. Add ~/.local/bin or "
            "~/.cargo/bin to PATH and retry."
        )
    return uv


def ensure_uv(dry_run: bool) -> str:
    uv = find_uv()
    if uv:
        return uv
    if dry_run:
        return "uv"
    return install_uv()


def run(command: list[str], cwd: Path, dry_run: bool) -> None:
    rendered = " ".join(command)
    print(f"+ {rendered}")
    if dry_run:
        return
    subprocess.run(command, cwd=str(cwd), check=True)


def main() -> int:
    args = parse_args()
    project_dir = resolve_target(args)
    backend = resolve_backend(args)
    torch_version = resolve_torch_version(args)
    backend_spec = BACKENDS[backend]

    print(f"Project: {project_dir}")
    print(f"Backend: {backend} ({backend_spec['package']})")
    print(f"Torch: torch=={torch_version}")

    if not args.dry_run:
        prepare_target(project_dir, args)

    uv = ensure_uv(args.dry_run)
    run([uv, "init"], project_dir, args.dry_run)
    run(
        [uv, "add", backend_spec["package"], f"torch=={torch_version}"],
        project_dir,
        args.dry_run,
    )

    init_command = [uv, "run", "dl-init"]
    if backend_spec["flag"]:
        init_command.append(backend_spec["flag"])
    run(init_command, project_dir, args.dry_run)

    print("\nCreated experiment scaffold.")
    print(f"Location: {project_dir}")
    print("Next: read AGENTS.md, implement the dataset, then run the generated smoke checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
