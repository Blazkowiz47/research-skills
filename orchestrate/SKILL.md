---
name: orchestrate
description: Execute an approved development plan through native Codex or Claude subagents. Use when the user requests orchestrated implementation with a chosen worker model and effort, narrow assignments, dependency-aware scheduling, critique, verification, and project-memory handoffs.
---

# Orchestrate

Keep the current conversation as orchestrator. Use the host's native subagents;
this skill supplies working instructions, not an orchestration runtime. Delegate
substantive implementation to workers. Own planning, coordination, critique, and
verification. Make only small integration fixes yourself: wiring completed work
or correcting minor mismatches without new design decisions. Substantial missing
integration work becomes another worker assignment.

## Establish the execution contract

- Recover the approved plan from the user's reference or this conversation. Read
  relevant repository instructions, source, and existing changes. Preserve
  unrelated work and distinguish it from this run's changes.
- Invocation authorizes execution within that approved scope. Split, reorder,
  and refine tasks without another approval. Ask when a significant design
  decision or intended outcome must change; show the evidence and proposed
  change. Continue independent, unaffected work while awaiting the answer.
- An incomplete breakdown is yours to complete. An absent or ambiguous approved
  outcome is not: resolve that before implementation. Do not weaken acceptance
  criteria to make failing work appear complete.
- Use the user's invocation-specified model and reasoning effort for every worker
  and critic, including replacements and follow-ups, unless the user explicitly
  overrides a particular assignment. Keep the orchestrator on the current chat's
  settings. Reuse unambiguous settings already supplied in this conversation;
  request missing settings before dispatch, while doing independent inspection.
- Read the matching host section in [native-hosts.md](references/native-hosts.md).
  Confirm the available tools can express the requested configuration. Never
  silently substitute a model, drop the effort setting, or claim a configuration
  was applied when it cannot be established. Report the limitation and obtain the
  missing choice if needed; do not replace delegation with substantive solo work.
- Existing execution permissions and project boundaries still apply. Invocation
  does not itself authorize publishing, deployments, paid runs, or unrelated
  changes. Honor authorization already given without asking for it again.

## Refine and schedule

First produce a concise execution breakdown, even when the approved plan looks
detailed. Inspect enough implementation to identify real dependencies. Critique
the plan's assumptions and each assignment's acceptance criteria before dispatch.

Maintain one compact task ledger using the host's task facilities or a checkpoint
in this conversation. Include task ID, expected outcome, dependencies, edit
ownership, acceptance evidence, worker/model/effort, critique owner, and state.
Distinguish `pending`, `running`, `awaiting review`, `needs correction`, `accepted`,
and `blocked`. Scale detail to the work; do not build a second project-management
system. If initialized memory provides an appropriate plan record, use that
convention for durable checkpoints.

Run ready tasks concurrently only when their edits and assumptions are independent.
Different files can still share an unstable interface, schema, generated output,
test fixture, or process. Settle shared contracts first. Assign one active writer
per overlapping edit surface; sequence dependent changes and orchestrator fixes.
Use worktree isolation when useful and supported, with an explicit baseline and
integration owner. Isolation does not remove semantic dependencies.

Respect host concurrency limits; use fewer workers when coordination dominates.
After each result, update the ledger and dispatch newly ready work. Use native
completion events or bounded waits rather than busy polling. Do not end the run
merely because a worker is still running. Before reassigning stalled work, stop
the prior writer and confirm its state so two agents cannot own the same edits.

## Give narrow assignments

Supply each worker enough context to work without the whole conversation:

- Task ID, approved outcome, relevant decisions, and dependency results.
- Exact repository/worktree, baseline, relevant instructions and source paths.
- Owned files or edit surfaces, forbidden overlaps, and known concurrent work.
- Required behavior, acceptance criteria, and proportionate validation.
- Exact model and effort, plus the report and memory instructions below.

Tell the worker to implement only this assignment, preserve unrelated changes,
and report necessary work outside its scope to the orchestrator. Workers do not
expand scope, delegate further, or perform Git integration/publication unless
specifically assigned and authorized. Do not pass the orchestrator role to a
worker merely by loading this entire skill; send the worker contract explicitly.

Require a concise handback containing:

1. Task ID and outcome: ready for review, incomplete, or blocked.
2. Changes and rationale, with affected paths and any integration handoff.
3. Checks actually run, their results, and material validation gaps.
4. Assumptions, risks, deviations, and decisions needed from the orchestrator.
5. Project-memory entry location, or why logging is absent or pending.

Treat a handback as evidence to evaluate, never as automatic acceptance.

## Critique and verify

Every substantive task must be critiqued by you or a separate critic. Choose a
separate critic when complexity, uncertainty, consequential behavior, or changes
across components warrant an independent perspective. The same user-selected
model and effort apply. You remain responsible for accepting the result.
When you critique directly, retain the current chat's settings; the worker/critic
configuration applies to spawned agents, not to orchestrator self-review.

A critic is read-only: inspect the expected behavior, actual implementation,
surrounding code, and validation evidence. Allow non-destructive checks in an
appropriate environment, but no implementation edits or project-memory writes.
Provide concrete findings with location, impact, evidence, and the criterion at
risk. Separate required corrections from optional improvements and unsupported
suspicions. Include the reviewed revision or checkpoint and verification limits.

Critique assignments before implementation, meaningful intermediate checkpoints
when early feedback helps, and completed work before acceptance. Review a stable
snapshot or agree a checkpoint with the worker; do not treat findings from moving
files as a final review. Re-review affected behavior after subsequent edits.

Inspect actual changes and check the acceptance evidence yourself, including when
a critic reports no issues. Resolve valid findings into narrow worker corrections
and re-review the fixes. You adjudicate disagreements against requirements and
evidence. Continue until criteria are met; do not loop over stylistic preferences
or expand scope to satisfy optional suggestions. If a review/correction cycle
repeats without new evidence or progress, investigate the cause, change the
assignment or reviewer, or report the specific blocker. Do not retry indefinitely
or declare success to escape the loop.

Once tasks are accepted, verify the combined implementation against the approved
outcome. Check shared interfaces, wiring, and relevant regression behavior;
individual passing checks do not establish integration. Critique your own small
integration fixes too, and use an independent critic when warranted. Run checks
appropriate to the change rather than inventing tests that mirror implementation.

## Project memory

Detect initialized project memory from repository instructions and its layout
marker/index. Follow the project's own remember/logging workflow, entry format,
write locks, ownership, and rollover rules. Do not initialize or migrate memory
as a side effect of this skill. Without initialized memory, use worker handbacks
and the conversation checkpoint.

Workers record meaningful changes, reasons, evidence, and validation limits before
their final handback when the project workflow permits it. Mark worker completion
as pending orchestrator review; do not pre-claim acceptance. Memory is a shared
edit surface even when source ownership does not overlap. Use existing cooperative
locking and serialize writes to a shared journal or plan record. Never archive
under live writers. If a safe write cannot be made, return the intended entry as
pending; arrange a serialized worker write or record it on the worker's behalf
under the project's rules. Do not invent per-agent journals to bypass the layout.

The orchestrator owns overall plan/review state and records accepted outcomes,
integration evidence, decisions, and unresolved blockers without duplicating each
worker's narrative. Record critic findings through this workflow; critics remain
read-only. Logging failure does not erase completed code work: track and report
the outstanding memory handoff explicitly.

## Continue and finish

Maintain a compact checkpoint after meaningful transitions: approved scope,
settings, task states, active writers, reviewed evidence, pending corrections,
memory status, and next ready work. After compaction or resumption, reconcile it
with actual files and live agents; a historical task ID is not proof an agent is
still running. Resume outstanding work without asking the user to repeat decisions.
If ownership of existing edits is uncertain, reconstruct it from the baseline,
diffs, and handbacks before modifying those edits. Preserve ambiguous changes and
resolve the specific uncertainty if evidence is insufficient; do not reset or
overwrite them to restart a task.

Keep going through implementation, critique, corrections, and integration within
scope. Ask only for material scope/design changes, genuinely missing choices or
access, or permissions not already granted. At a blocker, preserve recoverable
state and report what is needed; never imply that partial completion is success.

Before finishing, account for every dispatched worker and critic and leave no
untracked active writer. Report the delivered outcome, verification performed,
material limitations, and any outstanding tasks or memory writes. Commit, push,
or publish only when the user's authorization or applicable project workflow
calls for it.
