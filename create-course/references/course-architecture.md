# Course Architecture

Use this reference when normalizing inputs, selecting output depth, or reasoning about how generated artifacts fit together.

## Contents

- [CourseSpec](#coursespec)
- [Invariant artifact roles](#invariant-artifact-roles)
- [Relationships and sources of truth](#relationships-and-sources-of-truth)
- [Artifact depth](#artifact-depth)
- [Zero state](#zero-state)
- [Execution loops](#execution-loops)

## CourseSpec

Treat `.course/COURSE_SPEC.json` as the machine-readable contract for one generated course. Require only:

- `topic`: subject or capability to learn.
- `target_dir`: absolute destination directory.

Record these fields when supplied; otherwise use `null`, an empty list, or an explicitly labeled provisional value:

- `objective`: observable end capability.
- `learner_background` and `existing_knowledge`.
- `target_outcome`: capstone, assessment, portfolio, or other demonstration.
- `capacity_hours_per_week`, `deadline`, and `start_date`.
- `available_resources`: hardware, software, books, courses, mentors, or datasets.
- `constraints`: cost, access, schedule, platform, accessibility, or language.
- `safety_constraints` and authorization boundaries.
- `learning_preferences`.
- `profile`: `knowledge-exam`, `technical-experimental`, `creative-portfolio`, or `mixed`.
- `primary_profile`: the dominant concrete profile; required for `mixed`.
- `secondary_profiles`: only the additional concrete evidence lanes required for a `mixed` outcome.
- `profile_rationale`: why the chosen primary and secondary lanes match the end demonstration.
- `depth`: `starter`, `standard`, or `deep`.
- `reference_projects`: optional paths used only for structural inspiration.
- `assumptions`: provisional decisions with reasons and a review trigger.

Do not infer learner competence, completed work, available equipment, deadlines, or study capacity from silence. When capacity is unknown, make Week 1 a calibration week. When baseline is unknown, schedule a diagnostic rather than placing the learner by guesswork.

## Invariant artifact roles

Keep the visible root limited to `README.md`, `TODAY.md`, `AGENTS.md`, and `CLAUDE.md`. Keep machine metadata in hidden `.course/`. Generate each artifact with one clear ownership boundary:

- `AGENTS.md`: operating rules for learner-first reasoning, evidence, safety, and maintenance.
- `README.md`: entry point, start order, course map, and navigation.
- `CLAUDE.md`: a short assistant entry point that delegates to `AGENTS.md`.
- `.course/COURSE_SPEC.json`: normalized inputs, assumptions, profile, and generation metadata.
- `tracking/ROADMAP.md`: phases, dependencies, estimates, outcomes, and evidence gates.
- `tracking/DASHBOARD.md`: current state derived only from recorded evidence.
- `tracking/BACKLOG.md`: course setup and maintenance work; do not duplicate learning sessions.
- `TODAY.md`: ordered, capacity-sized executable checklist.
- `resources/SOURCES.md`: source policy and human-readable source index.
- `curriculum/BASELINE_DIAGNOSTIC.md`: placement exercise with no fabricated result.
- `curriculum/SKILL_MAP.md`: capabilities and prerequisite graph.
- `curriculum/skill-tracker.csv`: canonical skill state and evidence links.
- `curriculum/modules/`: learning outcomes, prerequisites, practice, and exit evidence.
- `notes/`: learner-authored explanations, maps, examples, and corrections.
- `practice/`: exercises, labs, projects, attempts, debugging records, and small evidence artifacts.
- `tracking/`: weekly plans, actual-time logs, dashboards, reviews, and history.
- `tracking/daily/`: exact archived daily plans.
- `resources/`: sources, setup, safety, reference maps, and version locks.

The only top-level content directories are `curriculum/`, `notes/`, `practice/`, `tracking/`, and `resources/`. Put profile-specific artifacts inside those homes. Do not create empty architecture for its own sake, and do not add a separate revision directory: schedule retrieval, reruns, and rework through tracking reviews and the backlog.

## Relationships and sources of truth

Maintain this chain:

`objective -> skills -> prerequisites -> phases -> weekly plan -> TODAY -> evidence -> tracker status -> review -> next plan`

Apply these ownership rules:

- Put a skill's status only in `skill-tracker.csv`; summarize it elsewhere.
- Put planned phase scope in `tracking/ROADMAP.md`; put actual progress in evidence and reviews.
- Derive `tracking/DASHBOARD.md` from trackers and logs; never use it as evidence.
- Keep `tracking/ACTIVE_PHASE.md`, if generated, at active-phase outcome level only.
- Give every lab, exercise, project, review, and skill a stable unique ID.
- Link evidence rather than copying raw outputs into multiple artifacts.
- Keep the validator markers in sync with the human-readable design: module order, owned skills, entry prerequisites, roadmap/capstone skill references, and the active week must all point to canonical tracker IDs and files.
- Keep `.course/COURSE_SPEC.json` synchronized after customization: `generated_files` exactly matches course artifacts, scaffold-provenance lists remain accurate for their own files, and CSV schemas match their files.

## Artifact depth

- `starter`: Produce the contract, operating rules, start page, phase outline, calibration module, skill map/tracker, diagnostic, first week, first day, source index/lock, notes, and minimal evidence/review templates. Use for exploratory goals or sparse inputs.
- `standard` (default): Add reusable module, practice-session, and milestone-review machinery to the invariant core plus the selected profile's evidence lane.
- `deep`: Expand standard output with rubrics, dependency rationale, deeper source evaluation, environment/version controls, milestone audits, and capstone decomposition. Use when the domain is complex, regulated, high-risk, or long-running.

Depth controls planning detail, not assumed duration or difficulty. Keep estimates as ranges and label uncertainty.

Use validator `--scaffold` mode only to check the untouched intermediate scaffold. The default final mode must reject an uncustomized generic outcome, tracker, or module before handoff.

## Zero state

Initialize the system before learning has occurred:

- Set all skill states to `Not started` unless imported evidence is explicitly verified.
- Leave actual time, scores, build results, observations, and review conclusions blank or zero.
- Use unchecked boxes for learner actions.
- Distinguish `planned`, `observed`, and `inferred` values.
- Create starter attempts as empty evidence records, never as successful examples.
- Record generation assumptions in `.course/COURSE_SPEC.json` and surface consequential ones in `README.md`.

## Execution loops

Daily loop:

1. Archive the previous `TODAY.md` exactly, including checkbox state.
2. Select due retrieval or reruns, the active gate, the next unmet prerequisite, then at most two carry-forwards.
3. Size the checklist to the active capacity lane and include an evidence destination.
4. Preserve the learner's first attempt before adding corrections or assistance.
5. Update actuals and tracker states only from recorded evidence.

Weekly loop:

1. Review actual time, evidence produced, misconceptions, blockers, and due retrieval or reruns.
2. Compare planned versus actual capacity without inventing missing data.
3. Reorder work by prerequisite and gate impact.
4. Generate the next weekly plan only after the review.
5. Generate the next `TODAY.md` from that reviewed plan.

Keep later weeks at phase level until evidence makes detailed scheduling useful. A course is an adaptive execution system, not a fully scripted calendar.
