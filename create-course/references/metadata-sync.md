# Course metadata and synchronization

New courses use schema 1.1. Existing schema 1.0 courses remain supported.

Use these sources of truth:

- `curriculum/skill-tracker.csv`: skill IDs, descriptions, prerequisites, required
  evidence, and observed learner state.
- `.course/COURSE_SPEC.json` `modules`: ordered objects with `path` and `skills`.
  Optional `prerequisites` lists extra entry requirements. Cross-module tracker
  prerequisites are derived automatically. Each skill belongs to one module.
- `skill_references`: a map from document path to the skill IDs used by that
  document, including the roadmap and any generated capstone/dependency map.
- `week_id`: the selected `tracking/YYYY-Www.md` file. Create its substantive plan
  first; synchronization does not invent a week of work.

Example module mapping:

```json
{
  "modules": [
    {"path": "curriculum/modules/M01-foundations.md", "skills": ["S01"]},
    {"path": "curriculum/modules/M02-practice.md", "skills": ["S02"]}
  ],
  "skill_references": {"tracking/ROADMAP.md": ["S01", "S02"]}
}
```

Preview after adding or renaming artifacts, changing module ownership, or selecting
another week:

```sh
python3 <skill-dir>/scripts/sync_course.py /absolute/path/to/course
python3 <skill-dir>/scripts/sync_course.py /absolute/path/to/course --write
```

Preview exits 1 when changes are pending, 0 when already synchronized, and 2 on
invalid inputs. It prints the exact diff. `--write` applies only derived markers,
the `Week:` navigation line in TODAY, file lists, and CSV schemas. It preserves
prose, checkboxes, tracker values, study logs, and evidence. Review added artifact
paths before applying; a manifest entry does not make its contents accurate.

The helper rejects ambiguous ownership, cycles, missing files, and symlinks. It
never creates module content or claims learner progress. Keep human-readable skill
maps and prerequisite explanations aligned with the canonical data during editing.
Synchronization validates structure, not pedagogical meaning.

For legacy courses lacking canonical mappings, `--adopt-existing` reads their
unambiguous module/reference markers into the spec. Combine with `--write` only
after reviewing the preview. It does not delete old artifacts or change depth.

At creation handoff, run `validate_course.py` in its default final mode. For a used
course, run `validate_course.py --in-progress`. The latter allows checked tasks,
logged actuals, and evidenced skill progress while retaining structural checks.
It verifies local evidence link targets, not the truth or quality of their contents;
review the underlying evidence before approving any promotion.
