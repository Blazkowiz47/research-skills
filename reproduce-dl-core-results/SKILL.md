---
name: reproduce-dl-core-results
description: Reproduce and audit deep-learning paper baselines specifically in Sushrut deep-learning-core/dl-core experiment repositories. Use when a user asks to validate whether deep-learning-core has a correct training pipeline, reproduce a paper result with dl-run or dl-sweep, comb through an official GitHub repo for reproducibility code, match paper datasets/hyperparameters/evaluation protocols through simple local dl-core components, reuse dataset or metric_manager wrappers, or diagnose a metric gap between dl-core artifacts and a published table.
---

# Reproduce DL-Core Results

## Overview

Use this workflow to reproduce paper results through the `deep-learning-core` package, not through a one-off training script. Every reported number should trace to a source, a realized dl-core config, local component wiring, dataset manifests, checkpoints, and evaluation commands.

The goal is to validate both the paper implementation and the package pipeline: config realization, registries, datasets, augmentations, model/loss/optimizer/scheduler setup, metric managers, checkpoint selection, sweeps, artifacts, and analysis.

## Required Inputs

Determine these before launching expensive work:

- Target paper or official implementation, preferably a PDF, arXiv page, OpenReview page, or official repository.
- Exact target result: table row, dataset, model, loss, metric, and expected value.
- `deep-learning-core` experiment repository path.
- Package/backend variant, such as `deep-learning-core`, `deep-learning-wandb`, `deep-learning-mlflow`, or `deep-learning-azure`.
- Available datasets and their root directories.
- Hardware budget, especially GPU count and memory.
- Whether a run is already active and whether to reuse an existing `tmux` session.

If any required input is missing, inspect local files first. Ask only when it cannot be discovered safely.

## Parallel Roles

Use subagents when the reproduction is large enough to benefit from independent passes:

- `knowledge-collector`: inspect the paper and official GitHub repository for reproducibility details. Return concrete files, functions, configs, defaults, scripts, and commands; avoid implementation advice unless it follows directly from source code.
- `implementation-reviewer`: review local dl-core changes for readability, unnecessary methods/classes, component wiring risks, and mismatches against the paper or official implementation.
- `results-auditor`: inspect artifacts, logs, checkpoints, metric direction, best-epoch selection, and post-hoc evaluation commands after a run completes.

Keep subagent prompts narrow and artifact-based. Do not pass conclusions as facts; ask for independent extraction or review.

## Workflow

### 1. Source the Target

Use primary sources before spending GPU time:

- Read the paper table, method section, training details, evaluation protocol, and appendix.
- Read the official implementation when it exists; treat it as the tie-breaker for omitted details.
- Record the exact target row, including train data, backbone, loss, margin/scale, batch size, optimizer, LR schedule, training duration, preprocessing, augmentation, and checkpoint selection.
- Convert reported iterations to epochs only after computing the local dataset size and batch size.

Do not infer unstable or version-sensitive facts from memory. Verify current repositories, docs, or dataset pages when they affect reproduction.

### 2. Audit the Official Repo

If a paper GitHub repository exists, inspect it before finalizing local dl-core code:

- Search for dataset construction, preprocessing, augmentation, alignment/cropping, normalization, and split/protocol files.
- Search for model/backbone definitions, heads/classifiers, initialization, frozen parameters, feature normalization, and train/eval mode details.
- Search for loss implementation, margin/scale constants, optimizer groups, weight decay exclusions, LR schedule units, warmup, gradient accumulation, AMP, and distributed assumptions.
- Search for training scripts, config defaults, checkpoint naming, best-checkpoint selection, evaluation scripts, and published command lines.
- Prefer `rg` over broad manual browsing. Start with terms from the paper table and method names, then inspect imported files and configs.

Record exact source paths and confirmed differences. Treat official implementation behavior as the tie-breaker when the paper omits implementation details.

### 3. Inspect the DL-Core Repository

Before editing:

- Read local instructions such as `AGENTS.md`, `CLAUDE.md`, and project memory/log files.
- Inspect `configs/`, `experiments/`, `src/datasets/`, `src/models/`, `src/losses/`, `src/optimizers/`, `src/schedulers/`, `src/augmentations/`, `src/metric_managers/`, `scripts/`, previous artifacts, and analysis files.
- Prefer `uv run dl-core list ...`, `uv run dl-core describe ...`, and `uv run dl-core add ...` over guessing registry names, extension points, or base-class contracts.
- If the user asks to reuse a local component, use `$reuse-dl-component` when available.
- Preserve dl-core scaffold conventions and exports. Let `uv run dl-core add ...` create local components before editing them.

Keep project code in local extension points under `src/`. Do not patch installed package code unless the user explicitly requests it and the package behavior itself is the target of the audit.

### 4. Match Data and Protocols

Validate the realized dataset, not just the config text:

- Confirm train record count, identity/class count, label density, split membership, and whether the paper trains on one dataset or a merged dataset.
- Confirm image preprocessing: crop/alignment, size, color order, normalization, random flips, and any domain-specific augmentation.
- Confirm test protocols: pair-list source, pair counts, benchmark variants, folds, threshold selection, and whether horizontal flip or template aggregation is used.
- Check for train/test identity leakage when using verification datasets.
- Make the paper's default validation benchmark part of the dl-core run config, and provide a post-hoc script for remaining paper benchmarks when they are not cheap enough to run every epoch.
- Use `uv run dl-inspect-dataset --config <config>` and targeted temporary tests to verify realized split sizes and batch shapes.

For face-recognition protocols, common checks include LFW `6000` pairs, AgeDB-30 `6000` pairs, CFP-FP `7000` pairs, image size `112x112`, RGB/BGR handling, normalization to `[-1, 1]`, and train-time horizontal flip.

### 5. Implement Paper-Aligned DL-Core Components

Prefer small, explicit local wrappers and configs:

- Create one dl-core config per paper protocol, such as one for each training dataset.
- Keep dataset wrappers simple. Inline one-off helper logic unless it is reused meaningfully.
- Put score-distribution plots for genuine/impostor scores inside the metric manager when the task is biometric or verification-based.
- Add post-hoc evaluation scripts that accept a run path, checkpoint selector, benchmark list, batch size, workers, and device.
- Use paper terminology in config names and run names so artifacts are easy to compare later.
- Keep reusable values in `configs/`; keep sweep/run matrices in `experiments/`.
- Prefer local dataset, augmentation, model, scheduler, optimizer, loss, and metric manager wrappers over ad hoc logic inside scripts.

Validate each new local component with syntax checks and the project's temporary tests when available.

### 6. Keep Code Simple

Optimize for auditability over abstraction:

- Keep new local components direct and readable; another researcher should be able to compare them against the paper or official repo quickly.
- Inline helper logic when it is used fewer than three times and remains readable in place.
- Do not add a new function, method, class, registry, or script just to name a two-line operation.
- Avoid custom orchestration when `dl-run`, `dl-sweep`, local components, metric managers, or existing scripts already express the workflow.
- Keep dataset wrappers especially lean: path discovery, manifest/protocol parsing, split construction, item loading, label mapping, and transforms.
- Avoid broad "utility" files unless several local components genuinely share the same nontrivial behavior.
- Prefer explicit config values over hidden defaults when a paper comparison depends on them.

After implementation, run a readability review before expensive jobs. Remove unused helpers, collapse thin wrappers, simplify config indirection, and verify that metric/evaluation code remains easy to audit.

### 7. Validate Before Real Runs

Run cheap checks before launching training:

```sh
uv run dl-run --config configs/<paper_config>.yaml --validate-only
uv run dl-inspect-dataset --config configs/<paper_config>.yaml
uv run dl-smoke --config configs/<paper_config>.yaml
uv run python scripts/temporary/test_dataset.py
uv run python scripts/temporary/test_model.py
```

Use the checks that exist in the target repo. Verify the printed or realized values for batch size, total steps, train samples, classes, LR milestones, optimizer params, loss params, device count, metric manager, augmentation, and output directory. A config that says the right thing is not enough; the dl-core realized objects must match.

For sweeps, validate without execution first:

```sh
uv run dl-sweep experiments/<sweep>.yaml --preview
uv run dl-sweep experiments/<sweep>.yaml --dry-run
```

Only move to a sweep after one concrete `dl-run` works.

### 8. Run DL-Core Safely

Launch only after a single config validates:

- Respect the user's GPU constraint. For one GPU, set `CUDA_VISIBLE_DEVICES=0` and avoid distributed assumptions.
- Reuse an existing `tmux` session/window when the user asks. Do not create a new session in that case.
- Print start time, command, exit status, and finish time inside the `tmux` pane.
- For sweeps, run preview or dry-run first and preserve sweep state files.
- Do not delete sweep tracking directories, analysis folders, or existing artifacts to refresh generated YAMLs.

Example:

```sh
tmux send-keys -t <session>:<window> \
  'cd /path/to/repo && export CUDA_VISIBLE_DEVICES=0; echo "started $(date -Is)"; uv run dl-run --config configs/<paper_config>.yaml; status=$?; echo "finished ${status} $(date -Is)"' C-m
```

Poll `tmux`, process state, logs, artifact files, and GPU usage while the job is running. Do not interrupt unless the user asks or the run is clearly invalid.

### 9. Analyze DL-Core Artifacts

When a run completes:

- Identify the best checkpoint using the paper-aligned validation metric, not automatically the final checkpoint.
- Run post-hoc paper benchmarks on that checkpoint.
- Compare against the exact table row with absolute metric gaps.
- Report training duration in both paper units and realized local units, such as steps and epochs.
- Save commands, artifact paths, checkpoint names, and metric values.
- Use `uv run dl-analyze --sweep <sweep>` for finished sweeps when available.
- Inspect `experiments/<sweep>/analysis/` and update `experiments/experiments.log` when the repository convention asks for it.

If the paper reports a 20-epoch result but the implementation uses fixed iterations, compute whether local epochs match the reported iteration budget before concluding there is a mismatch.

### 10. Audit DL-Core Reproduction Gaps

When local results miss the paper:

- First rule out bookkeeping: wrong checkpoint, wrong metric direction, missing best-checkpoint evaluation, incomplete run, or wrong artifact.
- Audit data: counts, classes, label mapping, duplicate filtering, train/test overlap, alignment, crop, color mode, normalization, and protocol files.
- Audit model/loss: backbone variant, embedding dimension, classifier type, margin/scale, frozen parameters, initialization, dropout, partial FC, mixed precision, and train/eval mode.
- Audit optimization: global batch size, gradient accumulation, LR scaling, milestone units, warmup, weight decay scope, momentum, scheduler stepping frequency, and seed.
- Audit evaluation: feature normalization, flip evaluation, threshold selection, fold aggregation, distance metric, and pair parsing.
- Audit dl-core wiring: registry key, local class import/export, config nesting, default values, trainer callback behavior, checkpoint monitor mode, metric manager state reset, device placement, and scheduler step unit.
- Compare local code against official code line by line for high-impact differences before starting another full run.

Record confirmed mismatches separately from hypotheses. Fix the smallest confirmed mismatch first, then rerun the minimal protocol that can validate the change.

## Logging

Keep a durable audit trail:

- Update project memory or `worklogs.md` when present.
- Log run command, config, artifact path, dataset, checkpoint, result, and next action.
- In `dl-core` sweep repos, update `experiments/experiments.log` when an analysis markdown file exists.
- Include source links or local source paths for paper claims and official implementation details.

The final report should state what matches the paper, what does not, what was verified, what remains uncertain, and the exact command or artifact needed for the next step.
