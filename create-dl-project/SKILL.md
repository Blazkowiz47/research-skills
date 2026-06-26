---
name: create-dl-project
description: Create new uv-based deep-learning experiment repositories using Sushrut's dl-init workflow. Use when a user wants to scaffold a new project with uv, install one of deep-learning-core, deep-learning-azure, deep-learning-mlflow, or deep-learning-wandb, choose a Torch version, bootstrap uv if needed, and run dl-init with the matching tracking backend flag.
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

Ask the user for any missing required input. Do not guess the project location, project name, or backend. If the user has not specified a Torch version, offer `2.8.0` as the default and let them choose.

## Workflow

Use `scripts/create_dl_project.py` for the actual project creation whenever possible. It verifies or installs `uv`, checks for unsafe existing directories, installs the selected package plus `torch==<version>`, and runs the correct `dl-init` command.

Example:

```sh
python3 scripts/create_dl_project.py \
  --parent /home/ubuntu/1Projects \
  --name arcface_reproduce \
  --backend wandb \
  --torch-version 2.8.0
```

For a no-tracker project:

```sh
python3 scripts/create_dl_project.py \
  --parent /home/ubuntu/1Projects \
  --name arcface_reproduce \
  --backend core \
  --torch-version 2.8.0
```

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
