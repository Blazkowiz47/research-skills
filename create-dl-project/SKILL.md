---
name: create-dl-project
description: Create or resume a uv-based dl-core experiment project with a chosen backend, Torch version, and Python/device requirements. Use for project scaffolding, not training or paper reproduction.
---

# Create DL Project

## Overview

Create a new deep-learning experiment repository with `uv`, a selected Sushrut `deep-learning-*` package, a chosen Torch version, and the matching `dl-init` scaffold command.

## Required Inputs

Before creating a project, determine:

- Project location, usually the parent directory such as `/home/ubuntu/1Projects`
- Project folder name such as `arcface_reproduce`
- Torch version, such as `2.8.0`
- Backend package:
  - `core`: install `deep-learning-core`; run `uv run dl-init` with no tracker flag
  - `azure`: install `deep-learning-azure`; run `uv run dl-init --with-azure`
  - `mlflow`: install `deep-learning-mlflow`; run `uv run dl-init --with-mlflow`
  - `wandb`: install `deep-learning-wandb`; run `uv run dl-init --with-wandb`

Use the request and local context to resolve inputs already supplied. Ask only
when location, name, backend, or version remains ambiguous. Offer `2.8.0` as an
example default when appropriate, not a universal compatibility claim. Preserve
explicit versions and the user's backend choice.

Check Python, Torch, operating system, and requested device compatibility using
current official package metadata or documentation before installation. Pass
`--python` and `--device cpu|cuda|mps` when specified. The dependency resolver checks
package compatibility; the helper then imports Torch and checks device availability.
A hardware check does not certify training correctness.

## Workflow

Use `scripts/create_dl_project.py` for the actual project creation whenever possible. It verifies or installs `uv`, checks for unsafe existing directories, installs the selected package plus `torch==<version>`, and runs the correct `dl-init` command.

Example:

```sh
python3 <skill-dir>/scripts/create_dl_project.py \
  --parent /home/ubuntu/1Projects \
  --name arcface_reproduce \
  --backend wandb \
  --torch-version 2.8.0
```

For a no-tracker project:

```sh
python3 <skill-dir>/scripts/create_dl_project.py \
  --parent /home/ubuntu/1Projects \
  --name arcface_reproduce \
  --backend core \
  --torch-version 2.8.0
```

## Preview and recovery

Start with `--dry-run` to check the path and print commands. Preview does not install
packages or claim device compatibility. `--name` accepts a single folder name;
use `--path` for a full path. Use `--create-parent` if the requested parent needs creation.

The helper records completed steps in `.dl-project-setup.json`. If setup fails,
retry with the same arguments plus `--resume`. It refuses to resume over changed
project files. Inspect a partially generated `dl-init` scaffold before completing
it manually; the helper never blindly repeats a partial scaffold over user work.
The state records setup progress only, not experiment results.

## Safety Rules

- If the target directory exists and is non-empty, stop unless the user explicitly asks to reuse it and the script is run with `--allow-existing`.
- If `uv` is not installed, let the helper install it using the official Astral installer. The helper should continue in the same run by discovering the installed binary.
- If neither `curl` nor `wget` is available for installing `uv`, report that one of them must be installed first.
- Do not stage, commit, or push the generated project unless the user separately asks from inside that project repository.

## Manual Fallback

If the helper cannot be used, run the equivalent commands:

```sh
mkdir -p /home/ubuntu/1Projects/arcface_reproduce
cd /home/ubuntu/1Projects/arcface_reproduce
uv init
uv add deep-learning-wandb torch==2.8.0
uv run dl-init --with-wandb
```

Change the package and `dl-init` flag according to the selected backend. For `core`, use `deep-learning-core` and omit the `--with-*` flag.
