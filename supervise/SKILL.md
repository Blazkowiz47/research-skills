---
name: supervise
description: Review user-written changes against an accepted implementation plan when explicitly asked to supervise. Report alignment, correctness, evidence, and next actions without implementing fixes.
---

# Supervise

The user writes the implementation. Review the requested changes against the
accepted plan, run proportionate checks, and explain what the evidence establishes.
Treat "supervise the current changes" as the default operation.

## Scope and mode changes

Read plans, repository instructions, source, diffs, commits, tests, and relevant
artifacts. Run inexpensive local checks using the existing environment. During
supervision, do not edit implementation, dependencies, tests, documentation, or Git
state. Do not install tools or start training merely to make a review complete.

If the user explicitly asks to implement a fix, switch to implementation for that
scope and proceed. That request need not be repeated in another message or task.
A finding or suggested fix alone does not authorize implementation. Existing user
authorization still applies to checks; ask only for additional costly or external
actions that are actually needed and have not already been authorized.

## Resolve the plan

Read local `AGENTS.md` and `CLAUDE.md` when present. Use the user's named plan,
then the plan already selected in this conversation, then an unambiguous accepted
plan. Never invent requirements or select among several plans by modification time.
Ask for the plan or its identity only when that ambiguity prevents review.

When `memory/index.md` exists, read [plan-records.md](references/plan-records.md)
and use its per-plan selection, migration, and update rules. Otherwise use the
accepted plan in chat or the user-named file. Give an in-chat checkpoint after the
review; do not create a partial memory system. Missing memory does not by itself
justify `cannot verify`. Do not change a user-named plan file without authorization.

Record the accepted goal, stable step IDs, constraints, acceptance criteria, and
known comparison baseline. Preserve unknown boundaries explicitly. Other plans'
changes are context, not part of the selected plan's progress.

## Inspect and assess

In Git, inspect branch/HEAD, staged and unstaged diffs, relevant untracked files,
and commits since the accepted baseline or last reviewed checkpoint. Read enough
surrounding implementation and tests to understand behavior. Exclude supervision
records and legacy singleton records from implementation diffs.

Distinguish selected-plan work from pre-existing or unrelated changes using the
actual diff and checkpoint evidence. State attribution limits. Without Git, use
identified files and any reliable baseline; explain what comparison was possible.

For each attempted step, check scope, constraints, wiring, acceptance evidence,
and correctness or regression risks. A plan may itself be flawed. Report both:

- Alignment: `aligned`, `aligned but incomplete`, `off-plan`,
  `plan amendment needed`, or `cannot verify`.
- Correctness: `no issues found in reviewed scope`, `issues found`, or
  `not established`, with concrete evidence and limitations.

An implementation can align with a flawed plan. Show a proposed amendment and its
consequences when justified; require approval before changing accepted criteria.
Mark steps complete only when their acceptance criteria are satisfied.

## Validation and report

Use the smallest existing check that establishes the relevant behavior. Inspect
commands for writes or external effects. In dl-core projects, prefer the existing
interpreter or `uv run --no-sync` for discovery; inspect realized configs and
artifacts without launching experiments. Report missing dependencies rather than
installing them during supervision.

For a small review, report the plan/step, alignment, correctness, evidence, any gap,
and one concrete next action. Cite files and lines when useful. Include checks run,
results, and material checks not run. For larger reviews, group findings by step.
Update only the selected durable record when available; otherwise include a compact
in-chat checkpoint with the reviewed revision/scope and remaining acceptance gaps.
