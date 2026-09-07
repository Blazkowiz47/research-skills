"""Regression checks using disposable projects and no package installs or training."""

import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


create = load("create_project", "create-dl-project/scripts/create_dl_project.py")
reuse = load("reuse_component", "reuse-dl-component/scripts/reuse_dl_component.py")
doctor = load("install_check", "scripts/check_installation.py")


class TemporaryCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="research-skills-test-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()

    def invoke(self, module, args):
        with patch.object(sys, "argv", ["helper", *map(str, args)]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return module.main()


class InstallationTests(TemporaryCase):
    def install(self, *extra):
        script = REPO / ("install.bat" if os.name == "nt" else "install.sh")
        command = (["cmd", "/c", str(script)] if os.name == "nt" else ["bash", str(script)])
        return subprocess.run([*command, "--target", "codex", "--agent-home", str(self.root), "--skill", "unslop", *extra], text=True, capture_output=True)

    def test_backups_are_not_discoverable(self):
        destination = self.root / "skills/unslop"
        destination.mkdir(parents=True)
        (destination / "SKILL.md").write_text("---\nname: unslop\n---\nOld customized content\n")
        run = self.install("--method", "copy", "--force")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual([p.name for p in (self.root / "skills").iterdir()], ["unslop"])
        saved = list((self.root / "skill-backups").rglob("SKILL.md"))
        self.assertEqual(len(saved), 1)
        self.assertIn("Old customized", saved[0].read_text())

    @unittest.skipIf(os.name == "nt", "local symlinks may require Windows Developer Mode")
    def test_copy_can_replace_existing_symlink(self):
        self.assertEqual(self.install().returncode, 0)
        self.assertTrue((self.root / "skills/unslop").is_symlink())
        run = self.install("--method", "copy", "--force")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertFalse((self.root / "skills/unslop").is_symlink())

    def test_legacy_backup_migration_preserves_content(self):
        backup = self.root / "skills/unslop.backup-20260901"
        backup.mkdir(parents=True)
        content = "---\nname: unslop\n---\nOld content\n"
        (backup / "SKILL.md").write_text(content)
        self.assertTrue(any("legacy backup" in issue for issue in doctor.check(self.root)))
        with contextlib.redirect_stdout(io.StringIO()):
            doctor.check(self.root, move_backups=True)
        self.assertFalse(backup.exists())
        self.assertEqual(next((self.root / "skill-backups").rglob("SKILL.md")).read_text(), content)


class ReuseTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.source = self.root / "source"
        self.destination = self.root / "destination"
        for project in (self.source, self.destination):
            (project / "src/datasets").mkdir(parents=True)
            (project / "pyproject.toml").write_text('[project]\nname="fixture"\ndependencies=["deep-learning-core"]\n')
            (project / "src/__init__.py").write_text("# root export\n")
            (project / "src/datasets/__init__.py").write_text("# package export\n")
        self.source_file = self.source / "src/datasets/demo.py"
        self.dest_file = self.destination / "src/datasets/demo.py"
        self.source_file.write_text("value = 42\n")
        self.dest_file.write_text("value = 1\n")
        self.arguments = ["--source-project", self.source, "--dest-project", self.destination, "--component-type", "dataset", "--name", "Demo", "--force"]

    def test_invalid_source_is_rejected_before_mutation(self):
        self.source_file.write_text("def invalid(:\n")
        with patch.object(reuse, "run") as run:
            with self.assertRaises(SyntaxError):
                self.invoke(reuse, self.arguments)
            run.assert_not_called()
        self.assertEqual(self.dest_file.read_text(), "value = 1\n")

    def test_missing_local_import_is_rejected(self):
        (self.source / "src/shared.py").write_text("value = 1\n")
        self.source_file.write_text("from src.shared import value\n")
        with self.assertRaises(SystemExit):
            self.invoke(reuse, self.arguments)
        self.assertEqual(self.dest_file.read_text(), "value = 1\n")

    def test_failure_restores_component_and_exports(self):
        before = {p: p.read_bytes() for p in (self.destination / "src").rglob("*.py")}
        def fail(command, cwd, dry_run):
            self.dest_file.write_text("generated = True\n")
            (cwd / "src/__init__.py").write_text("changed = True\n")
            (cwd / "src/datasets/__init__.py").write_text("changed = True\n")
            raise subprocess.CalledProcessError(1, command)
        with patch.object(reuse, "run", side_effect=fail):
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke(reuse, self.arguments)
        self.assertEqual(before, {p: p.read_bytes() for p in (self.destination / "src").rglob("*.py")})

    def test_success_preserves_generated_exports(self):
        def scaffold(command, cwd, dry_run):
            self.dest_file.write_text("generated = True\n")
            (cwd / "src/datasets/__init__.py").write_text("from .demo import value\n")
        with patch.object(reuse, "run", side_effect=scaffold):
            self.assertEqual(self.invoke(reuse, self.arguments), 0)
        self.assertEqual(self.dest_file.read_bytes(), self.source_file.read_bytes())
        self.assertEqual((self.destination / "src/datasets/__init__.py").read_text(), "from .demo import value\n")

    def test_export_mismatch_restores_originals(self):
        def scaffold(command, cwd, dry_run):
            self.dest_file.write_text("class DemoDataset: pass\n")
            (cwd / "src/datasets/__init__.py").write_text("from .demo import DemoDataset\n")
        with patch.object(reuse, "run", side_effect=scaffold):
            with self.assertRaises(RuntimeError):
                self.invoke(reuse, self.arguments)
        self.assertEqual(self.dest_file.read_text(), "value = 1\n")
        self.assertEqual((self.destination / "src/datasets/__init__.py").read_text(), "# package export\n")


class ProjectTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.target = self.root / "project"
        self.arguments = ["--path", self.target, "--backend", "core", "--torch-version", "2.8.0"]

    def test_folder_name_cannot_escape_parent(self):
        for name in ("../outside", "..", "a/b", "a\\b", "/absolute"):
            with self.subTest(name=name), self.assertRaises(SystemExit):
                self.invoke(create, ["--parent", self.root, "--name", name, "--backend", "core", "--torch-version", "2.8.0", "--dry-run"])

    def test_preview_rejects_nonempty_target(self):
        self.target.mkdir()
        (self.target / "keep.txt").write_text("user work")
        with self.assertRaises(SystemExit):
            self.invoke(create, [*self.arguments, "--dry-run"])
        self.assertEqual((self.target / "keep.txt").read_text(), "user work")

    def test_preview_does_not_create_target(self):
        with patch.object(create, "ensure_uv", return_value="uv"):
            self.assertEqual(self.invoke(create, [*self.arguments, "--dry-run"]), 0)
        self.assertFalse(self.target.exists())

    def test_resume_skips_completed_steps_and_rejects_user_edits(self):
        commands = []
        def fail_add(command, cwd, dry_run):
            commands.append(command)
            if command[1] == "init":
                (cwd / "pyproject.toml").write_text('[project]\nname="fixture"\n')
            if command[1] == "add":
                raise subprocess.CalledProcessError(1, command)
        with patch.object(create, "ensure_uv", return_value="uv"), patch.object(create, "run", side_effect=fail_add):
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke(create, self.arguments)
        (self.target / "user.txt").write_text("preserve")
        with self.assertRaises(SystemExit):
            self.invoke(create, [*self.arguments, "--resume"])
        (self.target / "user.txt").unlink()
        with patch.object(create, "ensure_uv", return_value="uv"), patch.object(create, "run", side_effect=lambda cmd, cwd, dry: commands.append(cmd)):
            self.assertEqual(self.invoke(create, [*self.arguments, "--resume"]), 0)
        self.assertEqual(sum(command[1] == "init" for command in commands), 1)
        state = json.loads((self.target / create.STATE_FILE).read_text())
        self.assertIn("scaffold", state["completed"])


class LauncherTests(TemporaryCase):
    def launch(self, *args):
        return subprocess.run([sys.executable, str(REPO / "reproduce-dl-core-results/scripts/launch_run.py"), *map(str, args)], capture_output=True, text=True)

    def test_records_exit_output_and_working_directory(self):
        record = self.root / "run.json"
        run = self.launch("--project", self.root, "--record", record, "--", sys.executable, "-c", "import os,sys; print(os.getcwd()); print('error',file=sys.stderr); sys.exit(7)")
        self.assertEqual(run.returncode, 7, run.stdout + run.stderr)
        data = json.loads(record.read_text())
        self.assertEqual(data["exit_code"], 7)
        self.assertTrue(data["started_at"] and data["finished_at"])
        self.assertIn(str(self.root), record.with_suffix(".log").read_text())
        self.assertIn("error", record.with_suffix(".log").read_text())

    def test_missing_directory_does_not_launch(self):
        sentinel = self.root / "should-not-exist"
        code = f"from pathlib import Path; Path({str(sentinel)!r}).touch()"
        run = self.launch("--project", self.root / "missing", "--record", self.root / "run.json", "--", sys.executable, "-c", code)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse(sentinel.exists())
        self.assertFalse((self.root / "run.json").exists())

    def test_inherited_gpu_allocation_survives_preview(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "3"}):
            run = self.launch("--project", self.root, "--record", "run.json", "--dry-run", "--", sys.executable, "-c", "pass")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["preview"]["cuda_visible_devices"], "3")
        self.assertFalse((self.root / "run.json").exists())


if __name__ == "__main__":
    unittest.main()
