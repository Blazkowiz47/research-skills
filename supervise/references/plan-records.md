# Durable plan records

Use one durable record per accepted plan:

```text
memory/supervise/<plan-id>.md
```

This lets separate chats supervise different plans in the same project without
overwriting each other's state. It also lets one chat switch between named
plans. Do not rely on chat history as the only copy of a plan.

Use this reference only when `memory/index.md` exists. Otherwise review the
accepted plan in chat or a user-named file without creating a memory tree.
Missing durable storage alone does not prevent review.

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


## Record updates

Immediately before writing, reload the selected record and preserve any newer
entries. If concurrent changes conflict, report the conflict without choosing a
winner. Update only that plan's status and review evidence. Record revision,
worktree scope, checks, alignment, correctness, limitations, and next action.
Amend accepted requirements only after the user approves the amendment.
When all acceptance criteria are satisfied, retain the record and mark it complete.
