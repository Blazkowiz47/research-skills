---
name: create-course
description: Create a new personalized, evidence-driven self-study project in a user-specified directory. Use when Codex is asked to turn a topic or capability goal into a filesystem-based course with a roadmap, prerequisite skills, modules, diagnostics, tasks, an initial daily and weekly plan, progress trackers, practice or lab workflows, review loops, source records, and measurable completion gates. Also use when a new learning system should borrow structural ideas from an existing study workspace without copying its personal data or completion state. Do not use for merely explaining a topic, drafting one lesson, maintaining an existing course, or building a public course website or LMS.
---

# Create Course

Create a new personal learning operating system, not a collection of generic lessons. Convert the desired outcome into demonstrable capabilities, prerequisite-aware phases, executable practice, evidence, and a feedback loop.

## Required inputs

Obtain only these blocking inputs:

- `topic`: the subject or capability to learn;
- `target_dir`: the absolute directory for the new project.

Infer other fields from the request and local context when safe. Otherwise record an explicit provisional assumption instead of running a questionnaire:

- desired outcome or capstone;
- learner background and baseline;
- normal and minimum weekly capacity;
- deadline or deadline-free progression;
- available tools, equipment, accessibility, safety, and logistical constraints;
- reference project directories;
- output depth: `starter`, `standard`, or `deep`.

If baseline or capacity is unknown, create a diagnostic and a calibration week. Ask only when the topic/path is missing or the exact destination already contains files. V1 creates new courses only: never merge into or replace a non-empty directory.

## Resource routing

Before creating files:

1. Read [course-architecture.md](references/course-architecture.md) for the `CourseSpec`, invariant artifacts, depth choices, and execution loop.
2. Read [domain-profiles.md](references/domain-profiles.md) and select `knowledge-exam`, `technical-experimental`, `creative-portfolio`, or `mixed`. For `mixed`, choose one concrete primary profile and only the secondary evidence lanes required by the outcome.
3. Read [research-and-evidence-rules.md](references/research-and-evidence-rules.md) whenever claims may be current, regulated, toolchain-sensitive, safety-sensitive, or derived from a reference workspace. Also read it before final semantic validation.

Use the templates in `assets/templates/` through the scaffold helper. Treat them as structural starting points; customize their substance to the actual topic.

## Workflow

### 1. Inspect before designing

- Resolve and display the exact target directory.
- Read applicable `AGENTS.md` or other local instructions in the target's ancestors.
- Inspect the target and reference workspaces read-only.
- Preserve all existing files. If the target is non-empty, stop and request a new empty directory; do not offer force overwrite.
- Extract only reusable mechanics from references. Never copy personal details, checked tasks, scores, captured evidence, deadlines, or subject-specific claims.

### 2. Define the course specification

Define:

- the observable end capability and explicit non-goals;
- the learner context, known strengths, unverified gaps, and constraints;
- profile and depth; for `mixed`, primary profile, selected secondary profiles, and rationale;
- assessment modes: explanation, retrieval, exercises, tests, labs, projects, critique, or a justified mix;
- source authority/freshness policy;
- safety and authorization boundaries;
- normal and minimum-viable capacity lanes;
- assumptions and unresolved decisions.

Do not claim a baseline that was not measured. Prefer evidence-gated progression; label calendar estimates as ranges.

### 3. Research the boundary

Use authoritative primary sources for the current scope, versions, standards, assessment rules, or tooling. Browse when facts may have changed. Distinguish discovery references from exact versions later used in evidence. Keep the source set deliberately small and attach dates or versions to volatile claims.

### 4. Design backward from proof

1. Define one capstone or external readiness condition.
2. Decompose it into stable skill IDs and demonstrable capabilities.
3. Add prerequisites and detect parallel branches and join points.
4. Assign required evidence to every skill.
5. Group skills into phases with observable entry/exit gates.
6. Select the smallest practice machinery appropriate to the profile.
7. Estimate effort ranges and capacity lanes without letting elapsed time override gates.

Reading alone must not establish mastery. Allow a well-supported decision not to use a technique or layer when that decision is itself the intended judgment.

### 5. Scaffold safely

Locate this skill's directory, then preview the scaffold:

```sh
python3 <skill-dir>/scripts/scaffold_course.py \
  --target /absolute/path/to/course \
  --topic "Topic or capability" \
  --profile technical-experimental \
  --depth standard \
  --weekly-hours 6 \
  --dry-run
```

After reviewing the exact path and manifest, rerun without `--dry-run`. Omit `--weekly-hours` or `--deadline` when unknown rather than inventing values.

An untouched scaffold can be checked structurally before customization with:

```sh
python3 <skill-dir>/scripts/validate_course.py --scaffold /absolute/path/to/course
```

`--scaffold` is an intermediate check only. It intentionally does not certify that the generic outcome, skills, and module have been customized.

For a genuinely mixed outcome, preview only the required lanes:

```sh
python3 <skill-dir>/scripts/scaffold_course.py \
  --target /absolute/path/to/course \
  --topic "Topic or capability" \
  --profile mixed \
  --primary-profile knowledge-exam \
  --secondary-profile technical-experimental \
  --depth standard \
  --dry-run
```

Do not pass primary or secondary profile flags for a concrete profile.

### 6. Customize every generated artifact

- Replace all template placeholders using file edits appropriate to the environment.
- Write topic-specific outcomes, skill dependencies, evidence, phases, module briefs, source strategy, safety boundaries, first diagnostic, first week, and first day.
- Keep machine-readable relationship markers synchronized with prose: every concrete `curriculum/modules/*.md` needs `course:module-order`, `course:module-skills`, and `course:module-prerequisites`; the roadmap, dependency map, and capstone use `course:skill-refs`. Every referenced ID must exist in the tracker, and module entry prerequisites must include tracker dependencies owned by earlier modules.
- Keep `TODAY.md`'s `course:active-week` marker and wiki link aligned with the selected `tracking/<week-id>.md`, whose `course:week-id` marker must match.
- When customization adds, removes, or renames artifacts, keep `.course/COURSE_SPEC.json` synchronized: `generated_files` must exactly match course artifacts, scaffold-provenance lists must reflect changes to their own files, and CSV schemas must match. Do not leave stale paths or silently omit new course artifacts.
- Pair every reusable template with one correctly instantiated starter artifact when the selected depth calls for it.
- Keep the visible root to `README.md`, `TODAY.md`, `AGENTS.md`, and `CLAUDE.md`. Use only `curriculum/`, `notes/`, `practice/`, `tracking/`, and `resources/` as top-level content folders; keep machine metadata under hidden `.course/`.
- Use Obsidian-friendly wiki links for navigation hubs while retaining valid relative Markdown links where appropriate.
- Make `TODAY.md` a small, ordered session that fits capacity and captures an unaided baseline before polished reference material.
- Leave every learner status at `Not started`, all actual logs empty, and all learner checkboxes unchecked.
- Keep planned targets separate from actual values.
- Create months of roadmap outcomes, not months of brittle daily plans.
- Do not initialize Git, download large resources, purchase equipment, enroll in services, or mutate external systems unless separately requested.

### 7. Validate mechanically and semantically

Run:

```sh
python3 <skill-dir>/scripts/validate_course.py /absolute/path/to/course
```

The default validator is the final/customized check; do not pass `--scaffold` at handoff. Fix all reported errors. Then review semantics that scripts cannot prove:

- Does the capstone demonstrate the requested outcome?
- Do prerequisites and phase order agree across the roadmap, tracker, modules, practice, and active phase?
- Is the first week feasible?
- Does `README` point to the same first action as `TODAY`?
- Are sources authoritative and appropriately current?
- Are safety controls proportional and concrete?
- Are uncertainty and learner progress represented truthfully?

For a substantial or safety-sensitive course, use independent technical/source and usability/coherence review passes. Give reviewers the generated artifacts, not the intended answer.

### 8. Hand off

Report:

- the absolute target path, selected profile/depth, and any mixed primary/secondary lanes;
- the end capability and estimated effort range;
- important assumptions and unresolved decisions;
- validation results;
- the exact file to open first.

The final instruction should normally be to open `TODAY.md`. Do not report learner work as complete merely because the course scaffold was created.

## Non-negotiable integrity rules

- Never overwrite a non-empty target.
- Never infer completion, study time, scores, experiment results, or mastery.
- Preserve learner-authored first attempts when the course asks for explanation, prediction, recall, or reflection. Make visual AI-annotation styling optional unless the user requests an existing convention.
- Keep raw failures and corrections distinguishable.
- Require evidence links for status promotion.
- Use owned/authorized environments and data; add recovery gates before destructive or privileged practice.
- Keep secrets, personal captures, credentials, proprietary material, and large generated artifacts out of the learning repository.
