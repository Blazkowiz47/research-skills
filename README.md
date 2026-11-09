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
./install.sh --skill orchestrate --target both
./install.sh --skill unslop --target both
./install.sh --skill maintain-course --target both
./install.sh --skill technical-diagrams --target both
```

Replaced skills are preserved under the agent's `skill-backups/`, outside skill
discovery. Check for duplicate names, broken links, and outdated/customized copies:

```sh
python3 scripts/check_installation.py --target both
python3 scripts/check_installation.py --target both --move-legacy-backups
```

The second command moves recognizable legacy backups of this repository's skills
and preserves their contents. `--agent-home /absolute/path` checks one explicit
agent home; installers accept it with a single target too.

## Skills

### `create-course`

Create a new personalized, evidence-driven learning project in a specified directory. It turns a topic or capability goal into a prerequisite-aware roadmap, curriculum, diagnostic, trackers, practice or lab system, reviews, and an executable first week and first day. Generated courses use a compact, Obsidian-friendly five-folder structure.

Example prompt:

```text
Use $create-course to build a personalized course on embedded Rust in /absolute/path/to/embedded-rust, with 6 hours per week.
```

Starter course depth generates 17 files for the first learning cycle. Standard and
deep include the selected profile's broader templates. Course creation uses POSIX
filesystem primitives; on Windows, run its helper under WSL. The metadata sync
helper previews updates to module markers, active-week navigation, and manifests
while preserving learner content. See [metadata synchronization](create-course/references/metadata-sync.md).

### `maintain-course`

Review recorded evidence, update an existing course's next session or weekly plan,
and create additional practice material when needed. Preserve first attempts and
past plans; advance skills only from linked evidence. Used courses are validated
with `validate_course.py --in-progress`, which allows real progress and checks
structural consistency and evidence links.

```text
Use $maintain-course to review this week's evidence and prepare my next study session.
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

Copy a same-named local `dataset` or `metric_manager` component from one `dl-core` experiment repo to another. The helper checks source syntax and project-local imports before running `dl-core add`, then copies the component and validates package exports. It restores previous files if an operation fails.

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

### `technical-diagrams`

Draw neural-network architectures, combined system/data-flow views, method-call
sequences, and control flow using translucent pastel shapes and light outlines.
Use Explain mode for understanding and Present mode for papers or slides. The
short entry point loads the shared style and only the relevant diagram reference;
accepted examples include editable SVGs and PNG previews.

The skill supports implicit selection for architecture, data-flow, and call-order
requests, and system explanations where a diagram helps. Explicit invocation:

```text
Use $technical-diagrams to explain how these classes call each other.
```

### `supervise`

Check user-written changes against an accepted implementation plan without taking over the coding. The skill reviews an accepted plan in chat or a named file even without project memory. With initialized memory, it keeps one durable record per plan under `memory/supervise/`. Separate chats can supervise different plans, and one chat can select between several named plans. The skill reviews staged, unstaged, untracked, or committed changes, runs proportionate validation, and reports whether the work is aligned, incomplete, off-plan, or needs an approved plan amendment.

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

### `orchestrate`

Execute an approved development plan with the current chat as orchestrator and
native Codex or Claude subagents as narrow implementation workers. The orchestrator
refines the breakdown, schedules independent work concurrently, critiques every
substantive task itself or through a read-only critic, and verifies corrections
and integration. Workers follow initialized project-memory conventions, with
coordinated writes. No separate orchestration runtime is installed.

Specify the worker model and effort when invoking; they apply to all workers and
critics unless you explicitly override an assignment. Use a model and effort
supported by the active host. For example, in Codex:

```text
Use $orchestrate to execute the approved plan. Use gpt-6.1-sol with high effort for all workers and critics.
```

In Claude Code, invoke `/orchestrate` with the approved plan and your selected
Claude model and effort. The orchestrator can split, reorder, and refine tasks
within scope; significant design or outcome changes return to you. It delegates
substantive implementation and may make small integration fixes itself.

### `unslop`

Remove common AI-writing patterns while preserving meaning and authorial voice. The research-aware rules protect citations, numerical results, calibrated uncertainty, technical terminology, scope boundaries, and reproducibility details.

Example prompt:

```text
Use $unslop to revise this discussion section without strengthening its claims or changing its citations and statistical results.
```

## Validation

Run the helper regression suite without package installs or training:

```sh
python3 -B -m unittest discover -s tests -v
```

CI runs these checks on Linux, macOS, and Windows; POSIX-only course creation tests
are skipped on native Windows. The suite covers recovery, preview behavior,
installation backups, launcher records, course profile/depth combinations,
metadata synchronization, and evidence requirements for existing courses.

[Behavioral cases](tests/behavioral_cases.json) provide realistic prompts for skill
selection and workflow evaluation. Run those in fresh disposable sessions and
judge actions and artifacts against the expected outcomes. The unit suite does not
claim to evaluate a model's response to those prompts.
