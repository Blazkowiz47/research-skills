# Domain Profiles

Use this reference to select the smallest profile that matches the learner's final evidence. Profile choice changes practice and evidence artifacts; it does not change the core planning loop.

## Contents

- [Selection rule](#selection-rule)
- [Knowledge-exam](#knowledge-exam)
- [Technical-experimental](#technical-experimental)
- [Creative-portfolio](#creative-portfolio)
- [Mixed](#mixed)
- [Profile-fit audit](#profile-fit-audit)

## Selection rule

Choose the profile whose dominant end demonstration answers the question below:

| Profile | Dominant end demonstration |
|---|---|
| `knowledge-exam` | Recall, reason, or write correctly under an assessment rubric and time limit |
| `technical-experimental` | Build, observe, modify, verify, and debug a working system or experiment |
| `creative-portfolio` | Produce, critique, revise, and present a coherent body of original work |
| `mixed` | Two or more of those demonstrations are independently required for success |

Do not choose `mixed` merely because every subject contains theory and practice. Select one primary profile and add only the secondary artifacts required by the target outcome. Record the selection and rationale in `.course/COURSE_SPEC.json`.

## Knowledge-exam

Use modules such as:

- Scope, syllabus, assessment format, and scoring constraints.
- Foundational concepts and vocabulary.
- Retrieval and spaced revision.
- Worked examples and untimed practice.
- Timed topic practice and mixed practice.
- Error classification and targeted remediation.
- Full simulations and exam strategy.

Add profile artifacts only when useful:

- `curriculum/` for scope-to-skill mapping.
- `practice/` for question sets, answer attempts, and rubrics.
- `tracking/reviews/` for timed-test and simulation reviews.
- `tracking/` for misconception and execution-error records.

Accept evidence such as an unaided answer, rubric-scored practice, retrieval result, error correction, timed performance, or a full simulation. Keep the original response separate from corrections. Record denominator, conditions, rubric version, time, and scorer where relevant. Never infer mastery from reading or copy a benchmark score from a reference project.

Useful gates progress from scope recognition to untimed accuracy, timed transfer, mixed-topic performance, and stable full-assessment performance. Define thresholds from the actual assessment or label them provisional.

## Technical-experimental

Use modules such as:

- Environment, tooling, reproducibility, and safe rollback.
- Conceptual and mathematical foundations.
- System architecture and interface tracing.
- Controlled reproductions and baseline measurements.
- Deliberate modifications with predictions.
- Fault injection, debugging, and recovery.
- Integrated projects and capstone demonstration.

Add profile artifacts only when useful:

- `practice/` for lab specifications, attempts, projects, small scripts, patches, and acceptance tests.
- `tracking/` for lab logs, hypotheses, failures, diagnoses, and reusable error patterns.
- `resources/` for environment, version, authorization, and recovery records.

Require evidence to include the environment and versions, baseline, learner hypothesis, change, raw output, interpretation, verification, result, rollback, and evidence link. A successful command demonstrates execution, not understanding. Raise status only after the learner explains the mechanism, makes a deliberate change, or independently diagnoses a failure at the relevant gate.

Use simulation, mocks, emulators, synthetic data, or disposable hardware before persistent or physical changes. Require an explicit recovery gate before destructive experiments.

## Creative-portfolio

Use modules such as:

- Medium, tools, vocabulary, and reference analysis.
- Fundamental studies and constrained exercises.
- Composition, craft, and intentional variation.
- Original briefs and iterative production.
- Self-critique, external critique, and revision.
- Selection, sequencing, presentation, and portfolio narrative.

Add profile artifacts only when useful:

- `practice/` for studies and constrained exercises.
- `practice/` for briefs, self-review, external feedback, versions, and selected work.
- `tracking/` for critique and portfolio logs.

Accept evidence such as dated artifacts, version history, process notes, constraint compliance, critique, revision rationale, and a curated portfolio. Preserve early versions; do not replace them with polished output. Use explicit rubrics for subjective dimensions and distinguish learner judgment, external feedback, and AI suggestions.

Useful gates progress from controlled studies to intentional variation, independent brief execution, revision from critique, and coherent portfolio selection.

## Mixed

Design mixed courses as a primary profile plus named secondary evidence lanes. Examples include:

- Certification plus implementation: `knowledge-exam` primary, technical labs as a secondary lane.
- Engineering design portfolio: `technical-experimental` primary, creative presentation as a secondary lane.
- Practice-based entrance assessment: `creative-portfolio` primary, timed knowledge assessment as a secondary lane.

Share skills, sources, planning, and reviews. Keep separate rubrics and gates where evidence is not interchangeable. A capstone may satisfy multiple gates only when its acceptance criteria explicitly test each one.

For the scaffold helper, use `--profile mixed --primary-profile <profile>` and repeat `--secondary-profile <profile>` only for required secondary lanes. Do not generate all profiles by default.

## Profile-fit audit

Before generation, verify:

- Every generated directory supports a required evidence type.
- Every phase ends in an observable demonstration.
- The profile includes the target assessment, work product, or operating environment.
- Secondary lanes do not overwhelm the primary outcome or weekly capacity.
- Domain-specific vocabulary from a reference project has not leaked into an unrelated course.
