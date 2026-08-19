# Research and Evidence Rules

Use this reference when researching the topic, defining progression, importing a reference project's structure, or validating a generated course.

## Contents

- [Research policy](#research-policy)
- [Source locks](#source-locks)
- [Evidence progression](#evidence-progression)
- [Safety and authorization](#safety-and-authorization)
- [Reference-project privacy](#reference-project-privacy)
- [Validation](#validation)

## Research policy

Browse before locking the course when any of these apply:

- The topic, toolchain, assessment, regulation, price, schedule, standard, or product may have changed.
- A named source, syllabus, specification, paper, dataset, device, or software version must be represented accurately.
- The domain is niche, emerging, safety-sensitive, medical, legal, financial, or otherwise high stakes.
- Recommendations could cause substantial expense, time commitment, account changes, downloads, or device modification.
- The course needs direct links, quotations, compatibility claims, or precise attribution.

Prefer sources in this order:

1. Official syllabus, specification, documentation, repository, standards body, regulator, or original research.
2. Maintainer-authored or institutionally authoritative guidance.
3. High-quality secondary explanation for pedagogy or gaps, clearly labeled as secondary.

Use multiple sources when a claim is interpretive, contested, or consequential. Distinguish facts supported by sources from the course designer's inference. If browsing is unavailable, mark unstable claims provisional and create a verification task; do not fabricate links or versions.

Research only enough to establish scope, dependencies, current constraints, evidence standards, and safe execution. Do not turn the generated project into a copied textbook.

## Source locks

For reproducibility-sensitive claims, record a source lock with:

- Stable source ID and topic or claim.
- Direct URL or repository path.
- Publisher or maintainer.
- Version, edition, branch, tag, commit, syllabus year, or retrieval date as applicable.
- Scope: which module, lab, assessment, or decision depends on it.
- Status: `current`, `provisional`, `superseded`, or `unavailable`.
- Notes describing compatibility constraints or inferences.

Keep human-readable navigation in `resources/SOURCES.md`; use a CSV or JSON lock file when the profile needs machine validation. Never silently update a locked version. Record the replacement and affected artifacts.

## Evidence progression

Use the default state vocabulary where it fits:

1. `Not started`: no learner evidence.
2. `Learning`: activity exists, but no demonstrated baseline.
3. `Reproduced`: learner can recreate a reference result under recorded conditions.
4. `Explained`: learner can give an unaided mechanism, rationale, or solution explanation.
5. `Modified`: learner can make a deliberate variation and predict its effects.
6. `Debugged independently`: learner can diagnose and repair a nontrivial failure without the answer being supplied.
7. `Capstone ready`: prerequisite gates have evidence and the learner can attempt integration safely.

Use a documented profile-specific subset if some states do not fit, but define the allowed values once and validate them consistently. Never advance a state because content was read, a command happened to succeed, a polished AI answer exists, or time elapsed.

For every gate, specify:

- Required capability and prerequisites.
- Observable task and conditions.
- Evidence artifact and destination.
- Rubric or acceptance criteria.
- Pass threshold and whether it is authoritative or provisional.
- Retry, remediation, and review behavior.

Preserve the learner's unaided attempt verbatim before correction. Keep raw observations separate from interpretation and AI assistance. Preserve failures because they establish the reasoning and debugging trail.

## Safety and authorization

Constrain course generation and execution to legal, authorized, consensual work. Prefer synthetic or public data, simulation, mock systems, and recoverable environments. For physical devices, accounts, human participants, hazardous materials, sensitive data, or regulated decisions, add explicit authorization, privacy, backup, rollback, and stop conditions.

Do not generate covert surveillance, credential interception, bypass, persistence, destructive exploitation, or instructions targeting assets without authorization. Do not initialize repositories, install software, download large datasets, purchase equipment, flash devices, contact people, or mutate external systems merely because a course recommends them. Represent those actions as gated tasks unless the user separately authorizes execution.

## Reference-project privacy

When the user supplies an existing course or project as inspiration:

- Extract relationships, loops, artifact roles, schemas, and useful conventions.
- Do not copy names, personal schedules, progress, scores, logs, device identifiers, account data, secrets, private recordings, or absolute paths into the new project.
- Do not carry completed checkboxes or status values into the new zero state.
- Replace domain-specific language unless it genuinely applies.
- Treat distinctive visual annotation or learner-assistance conventions as opt-in unless requested.
- Cite or record the reference path in `.course/COURSE_SPEC.json` only when the user wants provenance retained.

## Validation

Run deterministic checks after scaffolding:

- Resolve all local links and referenced files.
- Parse JSON and CSV files; verify schemas and allowed status values.
- Detect duplicate IDs, missing prerequisites, and dependency cycles.
- Detect unresolved placeholders and stale template examples.
- Detect checked learner actions, nonzero actuals, invented scores, or success claims in zero state.
- Compare weekly planned minutes with declared capacity and retained slack.
- Confirm `TODAY.md` tasks belong to the active week and point to evidence destinations.
- Confirm source locks contain required version or retrieval fields.
- Confirm the target directory policy was respected and no unrelated files changed.

Follow with a semantic audit:

- Does the objective describe an observable capability?
- Does every phase gate have evidence and prerequisites?
- Is the start order learner-first and executable without reading the whole roadmap?
- Does the selected profile match the final demonstration?
- Are estimates labeled and plausible for the declared capacity?
- Are current claims supported by authoritative sources?
- Are safety, authorization, privacy, and recovery proportional to risk?
- Does the first week calibrate unknowns instead of pretending to know them?
- Is the system adaptive, or has it overspecified distant daily work without evidence?

Use an independent audit when practical, passing the generated artifacts rather than the intended answer. Fix material findings and rerun both deterministic and semantic checks.
