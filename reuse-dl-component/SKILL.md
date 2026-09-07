---
name: reuse-dl-component
description: Copy a same-named dataset or metric_manager between local dl-core experiment projects, preserving exports and recovering from copy failures. Excludes renaming and general project scaffolding.
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

Inspect the request and current repository first. Ask only for inputs that remain ambiguous. Default to no overwrite unless the user already authorized replacement.

## Workflow

Use `scripts/reuse_dl_component.py` whenever possible.

Example:

```sh
python3 <skill-dir>/scripts/reuse_dl_component.py \
  --source-project /home/ubuntu/1Projects/old_project \
  --dest-project /home/ubuntu/1Projects/new_project \
  --component-type dataset \
  --name ArcfaceDataset
```

For a metric manager:

```sh
python3 <skill-dir>/scripts/reuse_dl_component.py \
  --source-project /home/ubuntu/1Projects/old_project \
  --dest-project /home/ubuntu/1Projects/new_project \
  --component-type metric_manager \
  --name BiometricMetrics
```

The helper validates the source syntax and checks project-local import paths
before writing. It runs `uv run --no-sync dl-core add` using the destination's
existing environment, copies the component, and validates component/export syntax.
It restores the prior component and package exports if any operation fails.
`--dry-run` performs the read-only checks and prints the intended actions.

Review source/destination package versions and external imports as needed. Static
checks do not prove runtime compatibility or resolve dynamic imports. Run the
smallest existing project check that verifies the copied component, using an
isolated synthetic input when practical. Inspect the check first for dataset,
tracker, or expensive execution effects. Report precisely what was verified.

## Safety Rules

- Same-name reuse only. If the user wants to rename the component, explain that this requires manually reviewing decorators, class names, imports, and config references.
- If the destination component already exists, stop unless the user explicitly permits overwrite and the helper is run with `--force`.
- Do not stage, commit, or push either experiment repository unless the user separately asks from inside that repository.
- Complete inexpensive validation within the authorized scope. Ask only for missing data or additional costly/external execution that is actually required.

## Manual Fallback

If the helper cannot be used, first compile the source and preserve the destination component and package exports. Restore them on any failure. Then run the equivalent operations:

```sh
cd /path/to/new_project
uv run dl-core add dataset ArcfaceDataset
cp /path/to/old_project/src/datasets/arcface_dataset.py src/datasets/arcface_dataset.py
python3 -m py_compile src/datasets/arcface_dataset.py
```

Use `metric_manager` and `src/metric_managers/` for metric managers. Prefer the helper's syntax-only validation when available because it avoids writing `__pycache__` files.
