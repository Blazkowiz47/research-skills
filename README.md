# Research Skills

Shared Codex and Claude skills for Sushrut/Mobai research workflows.

## Install

Clone this repository, then install the skills into both agents:

```sh
git clone git@github.com:Blazkowiz47/research-skills.git ~/1Projects/research-skills
cd ~/1Projects/research-skills
./install.sh
```

The installer uses symlinks by default. After that, updates are just:

```sh
cd ~/1Projects/research-skills
git pull
```

Useful install variants:

```sh
./install.sh --target codex
./install.sh --target claude
./install.sh --method copy --force
./install.sh --skill create-dl-project
./install.sh --skill reuse-dl-component
./install.sh --skill create-course --target codex
./install.sh --skill rubberduck --target both
./install.sh --skill supervise --target both
./install.sh --skill unslop --target both
```

## Skills

### `create-course`

Create a new personalized, evidence-driven learning project in a specified directory. It turns a topic or capability goal into a prerequisite-aware roadmap, curriculum, diagnostic, trackers, practice or lab system, reviews, and an executable first week and first day. Generated courses use a compact, Obsidian-friendly five-folder structure.

Example prompt:

```text
Use $create-course to build a personalized course on embedded Rust in /absolute/path/to/embedded-rust, with 6 hours per week.
```

### `create-dl-project`

Scaffold a new `dl-core` experiment project with `uv`, a chosen Torch version, and one backend:

- `core`: no external tracker
- `azure`: Azure extension wiring
- `mlflow`: local MLflow wiring
- `wandb`: Weights & Biases wiring

Example prompt:

```text
Use $create-dl-project to create a new dl-core experiment project.
```

### `reuse-dl-component`

Copy a same-named local `dataset` or `metric_manager` component from one `dl-core` experiment repo to another. The helper runs `dl-core add` in the destination first, so the generated package exports stay aligned, then copies the source module over the generated file.

Example prompt:

```text
Use $reuse-dl-component to copy the ArcfaceDataset dataset from /home/ubuntu/1Projects/old_project to /home/ubuntu/1Projects/new_project.
```

For now, this skill intentionally supports same-name reuse only. Renaming requires manually checking decorators, class names, imports, and config references.

### `rubberduck`

Think through a half-formed research idea with a conversational partner that can clarify assumptions, challenge claims, search the literature, and use relevant project evidence. In `dl-core` projects, it understands the generated config, component, experiment, artifact, and temporary-script conventions without editing project code.

Example prompt:

```text
Use $rubberduck to help me explore whether this metric gap points to a dataset issue or a training issue.
```

### `supervise`

Check user-written changes against an accepted implementation plan without taking over the coding. In projects with initialized memory, the skill keeps one durable record per plan under `memory/supervise/`. Separate chats can supervise different plans, and one chat can select between several named plans. The skill reviews staged, unstaged, untracked, or committed changes, runs proportionate validation, and reports whether the work is aligned, incomplete, off-plan, or needs an approved plan amendment.

Example prompt:

```text
/supervise the current changes
```

When more than one plan is active, name the plan:

```text
/supervise dataset-cache current changes
```

The explicit form also works:

```text
Use $supervise to check my current changes against the accepted plan.
```

### `unslop`

Remove common AI-writing patterns while preserving meaning and authorial voice. The research-aware rules protect citations, numerical results, calibrated uncertainty, technical terminology, scope boundaries, and reproducibility details.

Example prompt:

```text
Use $unslop to revise this discussion section without strengthening its claims or changing its citations and statistical results.
```
