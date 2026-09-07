#!/usr/bin/env python3
"""Create a uv deep-learning project using Sushrut's dl-init workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


BACKENDS = {
    "core": {"package": "deep-learning-core", "flag": None},
    "azure": {"package": "deep-learning-azure", "flag": "--with-azure"},
    "mlflow": {"package": "deep-learning-mlflow", "flag": "--with-mlflow"},
    "wandb": {"package": "deep-learning-wandb", "flag": "--with-wandb"},
}

DEFAULT_TORCH_VERSION = "2.8.0"
STATE_FILE = ".dl-project-setup.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a uv deep-learning experiment project."
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--path", help="Full target project directory.")
    target.add_argument("--parent", help="Parent directory for the new project.")
    parser.add_argument("--name", help="Project directory name. Required with --parent.")
    parser.add_argument("--python", help="Requested Python interpreter or version, passed unchanged to uv.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="auto")
    parser.add_argument("--resume", action="store_true", help="Resume a failed setup whose files have not changed.")
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
        if args.name:
            raise SystemExit("Use --name only with --parent.")
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
    if name in {".", ".."} or "/" in name or "\\" in name or not name.strip():
        raise SystemExit("--name must be one folder name, without path separators or traversal.")
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
    if parent.exists() and not parent.is_dir():
        raise SystemExit(f"Parent is not a directory: {parent}")
    if not parent.exists():
        if args.create_parent or confirm(f"Create parent directory {parent}?"):
            if not args.dry_run:
                parent.mkdir(parents=True, exist_ok=True)
        else:
            raise SystemExit(f"Parent directory does not exist: {parent}")

    if project_dir.exists():
        if not project_dir.is_dir():
            raise SystemExit(f"Target is not a directory: {project_dir}")
        entries = list(project_dir.iterdir())
        if entries and not (args.allow_existing or args.resume):
            raise SystemExit(
                f"Target directory already exists and is non-empty: {project_dir}\n"
                "Re-run with --allow-existing only if you explicitly want to reuse it."
            )
    elif not args.dry_run:
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
        command = [curl, "-LsSf", installer]
    elif wget:
        command = [wget, "-qO-", installer]
    else:
        raise SystemExit("Cannot install uv: neither curl nor wget is available.")

    print("uv was not found; installing uv with the official Astral installer.")
    script = subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout
    subprocess.run(["sh"], input=script, check=True)
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
    rendered = shlex.join(command)
    print(f"+ {rendered}")
    if dry_run:
        return
    subprocess.run(command, cwd=str(cwd), check=True)


def project_fingerprints(project_dir: Path) -> dict[str, str]:
    result = {}
    for directory, folders, filenames in os.walk(project_dir):
        folders[:] = [name for name in folders if name not in {".git", ".venv", "__pycache__"}]
        for name in filenames:
            path = Path(directory) / name
            if name != STATE_FILE and not path.is_symlink():
                result[path.relative_to(project_dir).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def save_state(project_dir: Path, state: dict) -> None:
    state["files"] = project_fingerprints(project_dir)
    path = project_dir / STATE_FILE
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=project_dir, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write((json.dumps(state, indent=2) + "\n").encode("utf-8"))
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def compatibility_command(uv: str, device: str) -> list[str]:
    code = (
        "import json,sys,torch; "
        "available={'cpu':True,'cuda':torch.cuda.is_available(),"
        "'mps':bool(getattr(torch.backends,'mps',None) and torch.backends.mps.is_available())}; "
        "print(json.dumps({'python':sys.version,'torch':torch.__version__,'devices':available})); "
        f"sys.exit(0 if {device!r} == 'auto' or available.get({device!r},False) else 1)"
    )
    return [uv, "run", "--no-sync", "python", "-c", code]


def main() -> int:
    args = parse_args()
    project_dir = resolve_target(args)
    backend = resolve_backend(args)
    torch_version = resolve_torch_version(args)
    if not re.fullmatch(r"[0-9][A-Za-z0-9.+-]*", torch_version):
        raise SystemExit("--torch-version must be an exact version such as 2.8.0.")
    backend_spec = BACKENDS[backend]

    print(f"Project: {project_dir}")
    print(f"Backend: {backend} ({backend_spec['package']})")
    print(f"Torch: torch=={torch_version}")

    state_path = project_dir / STATE_FILE
    settings = {"backend": backend, "torch_version": torch_version, "python": args.python, "device": args.device}
    state = {"settings": settings, "completed": [], "files": {}}
    if args.resume:
        if not state_path.is_file():
            raise SystemExit(f"No setup state to resume: {state_path}")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("settings") != settings:
            raise SystemExit("Resume with the same backend, Torch, Python, and device options.")
        if state.get("files") != project_fingerprints(project_dir):
            raise SystemExit("Project files changed since setup stopped; inspect them before retrying. Nothing overwritten.")
        if state.get("partial_scaffold"):
            raise SystemExit("dl-init left partial files. Review those files and complete dl-init manually; setup will not overwrite them.")
    elif state_path.exists():
        raise SystemExit(f"Setup state already exists; use --resume: {state_path}")
    prepare_target(project_dir, args)
    uv = ensure_uv(args.dry_run)
    init = [uv, "init", "--no-workspace"]
    if args.python:
        init.extend(["--python", args.python])
    add = [uv, "add", backend_spec["package"], f"torch=={torch_version}"]
    if args.python:
        add.extend(["--python", args.python])
    init_command = [uv, "run", "dl-init"]
    if backend_spec["flag"]:
        init_command.append(backend_spec["flag"])
    steps = [("init", init), ("dependencies", add), ("compatibility", compatibility_command(uv, args.device)), ("scaffold", init_command)]
    for step, command in steps:
        if step in state["completed"]:
            continue
        if step == "init" and (project_dir / "pyproject.toml").is_file():
            state["completed"].append(step)
            continue
        before = project_fingerprints(project_dir) if step == "scaffold" else {}
        try:
            run(command, project_dir, args.dry_run)
        except (OSError, subprocess.CalledProcessError, KeyboardInterrupt):
            state["failed_step"] = step
            state["partial_scaffold"] = step == "scaffold" and before != project_fingerprints(project_dir)
            save_state(project_dir, state)
            action = "Inspect the partial dl-init files before completing the scaffold manually." if state["partial_scaffold"] else "Retry with the same options and --resume."
            print(f"Setup stopped at {step}. Files preserved. {action}", file=sys.stderr)
            raise
        state["completed"].append(step)
        if not args.dry_run:
            state.pop("failed_step", None)
            save_state(project_dir, state)

    if args.dry_run:
        print("\nPreview complete. No project was created or compatibility check executed.")
        return 0

    print("\nCreated experiment scaffold.")
    print(f"Location: {project_dir}")
    print("Next: read AGENTS.md, implement the dataset, then run the generated smoke checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
