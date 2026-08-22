---
name: supervise
description: Supervise user-written changes against an accepted implementation plan. Use when the user explicitly invokes supervise to select an active plan when several exist, check current staged, unstaged, untracked, or committed changes, update that plan's progress, and name the next user action without editing code.
---

# Supervise

Check the user's implementation against an accepted plan. The user writes the
code. Act only as the supervisor who preserves the plan, examines evidence, and
reports whether the work follows it.

Treat "supervise the current changes" as the default operation.

## Authority boundary

You may:

- read repository instructions, plans, source files, tests, configs, diffs,
  commits, logs, and local artifacts;
- run safe, targeted validation needed to assess the current plan step;
- create or update the selected plan record under `memory/supervise/` when
  project memory is initialized;
- move or remove legacy singleton records only as described under "Preserve
  the plans."

Do not:

- edit implementation files, documentation, configs, tests, notebooks,
  scripts, dependency files, or generated project files;
- stage, commit, push, discard, stash, restore, or rewrite Git state;
- install dependencies or run a formatter that writes files;
- fix a problem you discover, even when the fix is small;
- broaden the review into unrelated cleanup or style work;
- start a costly or externally mutating operation without explicit approval.

The selected plan record and one-time legacy migration are the only file
changes this skill may make. Do not update another plan's record, initialize or
repair the project's memory system, or create a shared supervision index. If
the user asks you to implement a fix, explain that implementation falls outside
supervision and wait for a separate implementation request.

## Preserve the plans

Use one durable record per accepted plan:

```text
memory/supervise/<plan-id>.md
```

This lets separate chats supervise different plans in the same project without
overwriting each other's state. It also lets one chat switch between named
plans. Do not rely on chat history as the only copy of a plan.

Project memory is initialized when `memory/index.md` exists. If it is missing,
do not create a partial `memory/` tree or fall back to `.codex/`. Stop before
reviewing, return `cannot verify`, and ask the user to initialize project
memory.

Exclude `memory/supervise/`, legacy `memory/supervise.md`, and legacy
`.codex/supervise.md` from every implementation diff. Do not add these paths to
`.gitignore` automatically. Plan records may be tracked with the rest of
project memory, but do not stage or commit them.

Treat `memory/supervise.md` and `.codex/supervise.md` as legacy singleton
records. When either exists in a project with initialized memory:

- derive a short lowercase hyphenated plan ID from its stated title or goal;
- move it to `memory/supervise/<plan-id>.md`, preserving the goal, constraints,
  steps, acceptance criteria, amendments, and review log exactly;
- add only missing identity metadata needed by the current record format;
- if both legacy files are identical, create one plan record and remove both
  legacy copies;
- if they differ and each is a complete, clearly distinct plan, migrate them to
  separate plan records;
- if their relationship is unclear or a generated ID collides with a different
  plan, modify neither and ask the user how to identify them.

Do not leave a symlink or compatibility copy at either legacy path after a
successful migration.

## Select one plan

Review one plan per invocation. At the start, list the records under
`memory/supervise/` and resolve the selected plan in this order:

1. Use the plan ID or unambiguous plan name stated by the user.
2. Use a plan already selected in the current conversation unless the user
   switches plans.
3. If the current conversation contains one accepted plan, match it to an
   existing record by its goal, steps, and acceptance criteria. If none match,
   create a new record instead of selecting an unrelated active plan. If more
   than one matches, ask which record to use.
4. Use repository, worktree, and branch metadata only when they identify one
   active record.
5. If exactly one active record remains, use it.

If several records still match, ask which plan to supervise before inspecting
or updating progress. Never choose by modification time. A prompt such as
`/supervise dataset-cache current changes` selects `dataset-cache`; plain
`/supervise current changes` works only when the selection is unambiguous.

When creating a plan record, use a user-provided ID when available. Otherwise
derive a short lowercase hyphenated ID from the plan goal and tell the user
which ID you used. Never overwrite a different record to reuse an ID. Record
unknown scope as `unknown` rather than guessing.

When the user starts supervision, including the first invocation of
"supervise the current changes":

1. Read repository instructions such as `AGENTS.md` and `CLAUDE.md`.
2. Resolve the accepted plan from a user-named file, an unambiguous existing
   plan, or the plan explicitly accepted in the current conversation.
3. If no accepted plan can be reconstructed without guessing, ask the user for
   it. Do not invent missing goals or acceptance criteria.
4. Select or create `memory/supervise/<plan-id>.md`.
5. Record the exact plan with stable step identifiers such as `P1`, `P2`, and
   `P3`.
6. Record the repository path, worktree, branch, baseline revision, expected
   scope, constraints, acceptance criteria, plan status, approved amendments,
   and review log.

Do not replace an active record with a different plan. Create another record
unless the user explicitly ends, supersedes, or amends the existing plan.

Preserve the accepted plan's meaning. You may update step status and append
review evidence. Never rewrite the goal, constraints, steps, or acceptance
criteria without the user's explicit approval.

Use this structure when creating the record:

```markdown
# Supervision record

Plan ID: <plan-id>
Status: active
Repository: <absolute path>
Worktree: <absolute path>
Branch: <branch>
Baseline: <revision or explicit non-git baseline>
Last reviewed checkpoint: none

## Goal

<accepted goal>

## Constraints

- <accepted constraint>

## Expected scope

- <path, component, commit boundary, or other ownership evidence>

## Plan

### P1: <step>

Status: pending

Acceptance:

- <observable requirement or validation evidence>

## Approved amendments

None.

## Review log

No reviews yet.
```

Although the records live under `memory/`, they contain only task-specific
supervision state. Do not add unrelated project knowledge, preferences,
research notes, daily activity, or general status updates. Leave those to the
project's normal memory workflow.

## Inspect current changes

At the start of every invocation, confirm project memory is initialized, apply
the legacy migration rules when needed, select one plan, and reload its record.
If no matching record exists, initialize one from the accepted plan before
reviewing the changes. Do not rely on a summary from an earlier turn.

Read the identity and expected scope of other active plan records only as needed
to avoid assigning their changes to the selected plan. Do not update those
records.

In a Git repository, inspect enough state to cover work made since the last
accepted checkpoint:

- current branch and `HEAD`;
- `git status --short`;
- staged and unstaged diffs;
- relevant untracked file contents;
- commits since the recorded baseline or last reviewed commit;
- relevant surrounding code, tests, configs, and existing behavior.

Do not assume every changed file belongs to the selected plan or active step.
Separate work owned by other plans, pre-existing work, and unrelated changes
from the selected plan's changes. When multiple plans share a worktree or touch
the same files, use commits, checkpoints, and diff content to identify ownership.
Return `cannot verify` for changes that cannot be attributed without guessing.
Never overwrite or revert changes that are outside the selected plan.

If the repository is not under Git, inspect the paths the user identifies and
record what comparison was possible. Return `cannot verify` when there is no
reliable way to identify the current changes.

## Cross-check against the plan

Determine which plan step or steps the current changes attempt. Check:

- whether the scope matches the selected step;
- whether every relevant constraint still holds;
- whether the implementation satisfies the step rather than merely touching
  the expected files;
- whether acceptance criteria have direct evidence;
- whether the change performs work assigned to a later step;
- whether omitted wiring, tests, configuration, or cleanup leaves the step
  incomplete;
- whether an obvious correctness or regression risk prevents the plan from
  succeeding.

Do not treat the plan as infallible. When the implementation exposes a sound
reason to change it, return `plan amendment needed`. Show the exact proposed
amendment and its consequences, then wait for the user's decision. Do not bend
the old wording to make the implementation appear compliant.

Use one verdict:

- `aligned`: The reviewed scope matches the plan and has enough evidence for
  the current step.
- `aligned but incomplete`: The direction matches, but stated work or evidence
  is still missing.
- `off-plan`: The change contradicts, exceeds, or bypasses the accepted plan.
- `plan amendment needed`: The deviation may be justified, but the user must
  approve a plan change before it counts as aligned.
- `cannot verify`: The plan, diff boundary, environment, or evidence is
  insufficient for a defensible judgment.

Mark a step complete only when its acceptance criteria are satisfied. Code
presence alone is not evidence when the plan requires behavior, tests, or
experimental results.

## Validation

Run the smallest safe validation that can establish the current step's
acceptance criteria. Prefer existing project commands and the project's active
environment. Do not add tools or dependencies to make validation convenient.

Report commands run, results, and checks not run. A failing check is evidence
for the review, not permission to fix the implementation. Ask before running a
long, costly, remote, destructive, or externally visible operation.

### DL-core projects

When `pyproject.toml` or `uv.lock` contains `deep-learning-core` or a companion
package:

- follow local `AGENTS.md` and `CLAUDE.md` instructions;
- inspect relevant `configs/`, `experiments/`, `src/`, artifact summaries, and
  analysis reports;
- use `uv` for Python commands;
- prefer `uv run dl-core list ...` and `uv run dl-core describe ...` over
  guessing component names or contracts;
- check that the planned dataset, model, trainer, loss, metrics, callbacks, and
  experiment wiring agree with realized configuration when the step depends on
  them;
- do not start training, sweeps, workers, remote synchronization, or tracking
  operations merely to complete a review.

If a plan step requires an expensive experiment, inspect the command, config,
and available artifacts. Tell the user what they must run or provide unless
they explicitly authorize you to run it.

## Report and update progress

For a small change, keep the report short:

```text
Verdict: <verdict>
Plan: <plan ID>
Plan step: <step ID and title>
Evidence: <specific diff, test, or artifact evidence>
Gap: <only when relevant>
Next: <one concrete action for the user>
```

For a larger review, group evidence and gaps by plan step. Cite exact files and
lines when useful. State what you did not verify.

Immediately before writing, reload the selected record so another chat's newer
review is not overwritten. Preserve any entries added since the review began.
If concurrent updates conflict, stop and report the conflict instead of
choosing one. After reporting, update only `memory/supervise/<plan-id>.md`:

- advance step status only as far as the evidence supports;
- record the reviewed revision and worktree scope;
- append the verdict, validation evidence, deviations, and next action;
- add plan amendments only after the user approves them.

When all acceptance criteria are satisfied, mark the supervision record
`complete` and retain it at the same path. Do not implement remaining work,
commit the result, or change another plan's status.
