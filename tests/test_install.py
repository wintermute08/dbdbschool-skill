import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install_skill.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_installs_complete_skill_with_unicode_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = installer.install(Path(tmp) / "한글 경로")
            files = [p for p in installer.SOURCE.rglob("*") if p.is_file()]
            self.assertGreater(len(files), 2)
            for source in files:
                self.assertEqual(source.read_bytes(), (target / source.relative_to(installer.SOURCE)).read_bytes())
            self.assertFalse((target / "README.md").exists())

    def test_existing_install_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "dbdbschool"
            target.mkdir()
            marker = target / "user-notes.md"
            marker.write_text("사용자 수정")
            with self.assertRaises(FileExistsError):
                installer.install(tmp)
            self.assertEqual(marker.read_text(), "사용자 수정")
            self.assertEqual(list(target.iterdir()), [marker])

    def test_dangling_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "dbdbschool"
            target.symlink_to(Path(tmp) / "missing")
            with self.assertRaises(FileExistsError):
                installer.install(tmp)
            self.assertTrue(target.is_symlink())

    def test_missing_source_does_not_create_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "destination"
            with self.assertRaises(ValueError):
                installer.install(dest, Path(tmp) / "absent")
            self.assertFalse(dest.exists())

    def test_failed_copy_removes_only_new_partial_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            sibling = Path(tmp) / "another-skill"
            sibling.mkdir()
            with patch.object(installer.shutil, "copytree", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    installer.install(tmp)
            self.assertTrue(sibling.is_dir())
            self.assertFalse((Path(tmp) / "dbdbschool").exists())

    def test_codex_home_override(self):
        with patch.dict(os.environ, {"CODEX_HOME": "/tmp/example-codex"}):
            self.assertEqual(installer.default_skills_dir(), Path("/tmp/example-codex/skills"))

    def test_self_copy_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("test")
            with self.assertRaises(ValueError):
                installer.install(source / "nested", source)
            self.assertFalse((source / "nested").exists())


if __name__ == "__main__":
    unittest.main()
