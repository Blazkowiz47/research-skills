"""Course generation, synchronization, and progress-integrity checks."""

import contextlib
import csv
import io
import itertools
import json
import os
from pathlib import Path
import sys
import unittest

from test_helpers import REPO, TemporaryCase

sys.path.insert(0, str(REPO / "create-course/scripts"))
import scaffold_course as scaffold
import sync_course as sync
import validate_course as validator


@unittest.skipIf(os.name == "nt", "course creation requires POSIX descriptor-relative filesystem support; use WSL")
class CourseTests(TemporaryCase):
    def generate(self, target, profile="knowledge-exam", depth="standard", lanes=()):
        args = ["--target", str(target), "--topic", "Probability", "--profile", profile, "--depth", depth, "--weekly-hours", "6"]
        if profile == "mixed":
            args += ["--primary-profile", lanes[0]]
            for lane in lanes[1:]:
                args += ["--secondary-profile", lane]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(scaffold.main(args), 0)

    def validate(self, target, *flags):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = validator.main([*flags, str(target)])
        return code, out.getvalue()

    def customize(self, target):
        spec_path = target / ".course/COURSE_SPEC.json"
        spec = json.loads(spec_path.read_text())
        spec["objective"] = "Solve conditional probability problems and justify the assumptions."
        spec["target_outcome"] = "Solve an unseen assessment with explained sample spaces and event relationships."
        spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
        path = target / "curriculum/skill-tracker.csv"
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        capabilities = ["Define sample spaces", "Explain conditional probability", "Compute a conditional probability", "Select a probability model", "Diagnose a base-rate error", "Vary a conditioning event", "Solve an unfamiliar word problem", "Defend a probability analysis"]
        for row, description in zip(rows, capabilities):
            row["skill"] = description
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        readme = target / "README.md"
        readme.write_text(readme.read_text().replace("The exact capstone and acceptance criteria are defined during Phase 0 rather than assumed here.", "The capstone is an unseen probability assessment with a justified event model."))
        module = target / "curriculum/modules/M00-calibration.md"
        module.write_text(module.read_text().replace("Turn the generic starter capabilities", "Develop probability capabilities").replace("Rewrite S01–S08", "Practice the probability skills"))
        sync.apply_updates(sync.plan_updates(target))

    def test_all_profile_and_depth_combinations(self):
        profiles = list(scaffold.CONCRETE_PROFILES)
        cases = [(p, ()) for p in profiles]
        for primary in profiles:
            rest = [p for p in profiles if p != primary]
            for count in (1, 2):
                cases += [("mixed", (primary, *secondary)) for secondary in itertools.combinations(rest, count)]
        for index, ((profile, lanes), depth) in enumerate(itertools.product(cases, scaffold.DEPTHS)):
            with self.subTest(profile=profile, lanes=lanes, depth=depth):
                target = self.root / f"course-{index}"
                self.generate(target, profile, depth, lanes)
                code, output = self.validate(target, "--scaffold")
                self.assertEqual(code, 0, output)
                self.assertNotEqual(self.validate(target)[0], 0)
                self.assertEqual(sync.plan_updates(target), {})
                if depth == "starter":
                    count = len(json.loads((target / ".course/COURSE_SPEC.json").read_text())["generated_files"])
                    self.assertLessEqual(count, 20)

    def test_customized_course_passes_final_validation(self):
        target = self.root / "course"
        self.generate(target)
        self.customize(target)
        code, output = self.validate(target)
        self.assertEqual(code, 0, output)

    def test_sync_derives_prerequisites_and_preserves_learner_content(self):
        target = self.root / "course"
        self.generate(target)
        self.customize(target)
        first = target / "curriculum/modules/M00-calibration.md"
        first.write_text(first.read_text() + "\nLearner's original explanation stays verbatim.\n")
        second = target / "curriculum/modules/M01-practice.md"
        second.write_text("# Conditional probability practice\n\nUnaided prediction: uncertain.\n")
        spec_path = target / ".course/COURSE_SPEC.json"
        spec = json.loads(spec_path.read_text())
        spec["modules"] = [{"path": first.relative_to(target).as_posix(), "skills": ["S01"]}, {"path": second.relative_to(target).as_posix(), "skills": [f"S{i:02d}" for i in range(2, 9)]}]
        spec_path.write_text(json.dumps(spec))
        tracker = target / "curriculum/skill-tracker.csv"
        before = tracker.read_bytes()
        changes = sync.plan_updates(target)
        self.assertNotIn("course:module-prerequisites", second.read_text())
        sync.apply_updates(changes)
        self.assertEqual(before, tracker.read_bytes())
        self.assertIn("Unaided prediction: uncertain.", second.read_text())
        self.assertIn("Learner's original explanation stays verbatim.", first.read_text())
        self.assertEqual(sync.plan_updates(target), {})
        code, output = self.validate(target)
        self.assertEqual(code, 0, output)

    def test_progress_requires_real_evidence_and_preserves_actuals(self):
        target = self.root / "course"
        self.generate(target)
        self.customize(target)
        tracker = target / "curriculum/skill-tracker.csv"
        with tracker.open(newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        rows[0]["status"] = "Learning"
        rows[0]["evidence_link"] = "../practice/attempt.md"
        with tracker.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        today = target / "TODAY.md"
        today.write_text(today.read_text().replace("- [ ]", "- [x]", 1))
        code, output = self.validate(target, "--in-progress")
        self.assertNotEqual(code, 0)
        self.assertIn("BROKEN_LINK", output)
        (target / "practice/attempt.md").write_text("# First attempt\nI counted the conditioning cases incorrectly.\n")
        sync.apply_updates(sync.plan_updates(target))
        snapshot = tracker.read_bytes(), today.read_bytes()
        code, output = self.validate(target, "--in-progress")
        self.assertEqual(code, 0, output)
        self.assertEqual(snapshot, (tracker.read_bytes(), today.read_bytes()))
        self.assertNotEqual(self.validate(target)[0], 0)

    def test_nonempty_target_is_preserved(self):
        target = self.root / "course"
        target.mkdir()
        existing = target / "work.md"
        existing.write_text("Existing learner work")
        with contextlib.redirect_stderr(io.StringIO()):
            result = scaffold.main(["--target", str(target), "--topic", "Probability", "--profile", "knowledge-exam", "--depth", "starter"])
        self.assertNotEqual(result, 0)
        self.assertEqual(existing.read_text(), "Existing learner work")

    def test_sync_rejects_cycle_without_writing(self):
        target = self.root / "course"
        self.generate(target)
        path = target / "curriculum/skill-tracker.csv"
        text = path.read_text().replace("S01,Use the essential vocabulary precisely,,", "S01,Use the essential vocabulary precisely,S02,")
        path.write_text(text)
        before = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
        with self.assertRaises(ValueError):
            sync.plan_updates(target)
        self.assertEqual(before, {p: p.read_bytes() for p in target.rglob("*") if p.is_file()})

    def test_legacy_spec_can_adopt_existing_markers(self):
        target = self.root / "course"
        self.generate(target)
        self.customize(target)
        path = target / ".course/COURSE_SPEC.json"
        spec = json.loads(path.read_text())
        spec["schema_version"] = "1.0"
        del spec["modules"]
        del spec["skill_references"]
        path.write_text(json.dumps(spec))
        with self.assertRaises(ValueError):
            sync.plan_updates(target)
        sync.apply_updates(sync.plan_updates(target, adopt_existing=True))
        self.assertEqual(json.loads(path.read_text())["schema_version"], "1.0")
        code, output = self.validate(target)
        self.assertEqual(code, 0, output)


if __name__ == "__main__":
    unittest.main()
