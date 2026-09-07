---
name: maintain-course
description: Review evidence and replan an existing personal course, including today's session, weekly reviews, and prerequisite-based progress. Excludes creating a new course and doing assessed learner work on the learner's behalf.
---

# Maintain course

Keep an existing course usable as evidence, capacity, and goals change. Follow its
local instructions and preserve learner-authored work, past plans, and raw results.

## Establish the current state

Resolve the course path from the request or current workspace. Read `AGENTS.md`,
`TODAY.md`, the active weekly plan, skill tracker, and relevant evidence/reviews.
Read `.course/COURSE_SPEC.json` when present. Do not reconstruct progress from a
dashboard or assume that checked plans establish mastery. Inspect only the material
needed for the requested update.

If a required result is missing, keep its status unknown and proceed with planning
that does not depend on it. Ask for observations only the learner can provide.
Do not ask again for an already supplied schedule, goal, or approved scope change.

## Review and replan

- For a daily update, archive the exact prior `TODAY.md`, preserving checkbox state,
  under `tracking/daily/` with a unique dated filename before replacing it.
- For a weekly update, record a review of actual time, evidence, misconceptions,
  unmet gates, and capacity before writing the next week. Preserve earlier weeks.
- Promote a skill only when its stated gate has linked evidence. Preserve the
  unaided first attempt and distinguish observations, corrections, and AI help.
- Choose work from due retrieval/reruns, the active phase gate, and the next unmet
  prerequisite. Carry forward only work that still serves that gate.
- Fit the plan to available capacity with slack. Calibrate unknown capacity instead
  of inventing hours. Adjust scope when the goal and capacity conflict.
- Create the next needed module, exercise, note, or review artifact when it becomes
  useful. Starter courses intentionally omit later templates and profile machinery.
- Derive dashboard summaries from the tracker and logs. Never change actuals to
  make the dashboard agree with a plan.

An explicit request for an explanation or worked example can be answered. Label
assistance and do not count it as an unaided assessment. Do not execute expensive
labs, buy resources, or mutate external systems merely to fill an evidence gap.

## Keep relationships consistent

For create-course projects with schema 1.1, skill IDs and dependencies live in
`curriculum/skill-tracker.csv`. Module ownership/order and reference scopes live in
the spec's `modules` and `skill_references` fields; `week_id` selects the active week.
Update those canonical fields when replanning changes relationships.

If the companion create-course skill is installed, locate its directory and read
`references/metadata-sync.md`. Preview `scripts/sync_course.py` and apply its derived
marker/manifest changes. Run `scripts/validate_course.py --in-progress` after the
update. Do not use the creation validator's zero-state mode on a used course.
The companion is optional: if unavailable, check IDs, dependencies, links, evidence,
capacity, and active-week consistency directly. Do not install a dependency merely
to complete maintenance.

For legacy schema 1.0, adopt existing markers only when they are unambiguous and the
user's maintenance request requires synchronization. Preserve profile/depth and
existing artifacts. For other course formats, follow their conventions rather than
forcing a migration to this layout.

## Handoff

Report what the evidence supports, what changed in the plan, unresolved gaps, and
validation limits. Point to the exact first action in `TODAY.md`. Never report the
learner's work complete because a plan or teaching artifact was generated.
