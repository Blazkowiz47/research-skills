---
name: reuse-dl-component
description: Copy same-named local dl-core dataset or metric_manager components from one experiment repository into another while preserving destination scaffold conventions. Use when a user wants to reuse a shared dataset wrapper or metric manager across dl-core experiment projects by running dl-core add in the destination, copying the source module, and validating the copied file.
---

# Reuse DL Component

## Overview

Reuse a same-named local component from one `dl-core` experiment repository in another. This skill is intentionally narrow: support `dataset` and `metric_manager` components with the same name in both projects.

## Required Inputs

Before acting, determine:

- Source experiment repository path
- Destination experiment repository path
- Component type: `dataset` or `metric_manager`
- Component name, such as `ArcfaceDataset` or `StandardBiometricManager`
- Whether overwriting an existing destination component is allowed

Ask for any missing required input. Do not guess source or destination paths.

## Workflow

Use `scripts/reuse_dl_component.py` whenever possible.

Example:

```sh
python3 scripts/reuse_dl_component.py \
  --source-project /home/ubuntu/1Projects/old_project \
  --dest-project /home/ubuntu/1Projects/new_project \
  --component-type dataset \
  --name ArcfaceDataset
```

For a metric manager:

```sh
python3 scripts/reuse_dl_component.py \
  --source-project /home/ubuntu/1Projects/old_project \
  --dest-project /home/ubuntu/1Projects/new_project \
  --component-type metric_manager \
  --name BiometricMetrics
```

The helper:

1. Validates both paths look like `dl-core` experiment repositories.
2. Resolves the normalized module path, such as `src/datasets/arcface_dataset.py`.
3. Runs `uv run dl-core add <type> <name>` in the destination so package exports stay aligned.
4. Copies the source module over the generated destination module.
5. Checks the copied Python file for syntax errors without importing it.

## Safety Rules

- Same-name reuse only. If the user wants to rename the component, explain that this requires manually reviewing decorators, class names, imports, and config references.
- If the destination component already exists, stop unless the user explicitly permits overwrite and the helper is run with `--force`.
- Do not stage, commit, or push either experiment repository unless the user separately asks from inside that repository.
- After copying, tell the user to inspect imports and run the generated project checks, usually `uv run dl-inspect-dataset --config configs/base.yaml` or `uv run dl-smoke --config configs/base.yaml`.

## Manual Fallback

If the helper cannot be used:

```sh
cd /path/to/new_project
uv run dl-core add dataset ArcfaceDataset
cp /path/to/old_project/src/datasets/arcface_dataset.py src/datasets/arcface_dataset.py
python3 -m py_compile src/datasets/arcface_dataset.py
```

Use `metric_manager` and `src/metric_managers/` for metric managers. Prefer the helper's syntax-only validation when available because it avoids writing `__pycache__` files.
