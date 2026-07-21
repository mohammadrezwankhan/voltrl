import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from software_provenance import (
    DEFAULT_SOFTWARE_PATHS,
    capture_software_provenance,
    main,
    verify_software_provenance,
)


class SoftwareProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.manifest_path = self.root / "results" / "experiment_manifest.json"
        self.manifest_path.parent.mkdir()
        for relative_path in DEFAULT_SOFTWARE_PATHS:
            (self.root / relative_path).write_text(
                f"content for {relative_path}\n", encoding="utf-8"
            )
        self._git("init", "--quiet")
        self._git("config", "user.name", "Test User")
        self._git("config", "user.email", "test@example.com")
        self._git("add", *DEFAULT_SOFTWARE_PATHS)
        self._git("commit", "--quiet", "-m", "Initial source")
        self.provenance = capture_software_provenance(self.root)
        self._write_manifest()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _git(self, *arguments):
        subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _write_manifest(self):
        self.manifest_path.write_text(
            json.dumps({"software_provenance": self.provenance}),
            encoding="utf-8",
        )

    def test_clean_commit_snapshot_verifies(self):
        self.assertFalse(self.provenance["git_dirty"])
        self.assertEqual(
            [record["path"] for record in self.provenance["files"]],
            list(DEFAULT_SOFTWARE_PATHS),
        )
        self.assertEqual(verify_software_provenance(self.manifest_path, self.root), [])

    def test_historical_snapshot_survives_later_source_commit(self):
        (self.root / "voltrl.py").write_text("new version\n", encoding="utf-8")
        self._git("add", "voltrl.py")
        self._git("commit", "--quiet", "-m", "Update source")
        self.assertEqual(verify_software_provenance(self.manifest_path, self.root), [])

    def test_dirty_snapshot_uses_exact_working_tree_bytes(self):
        source = self.root / "voltrl.py"
        source.write_text("uncommitted experiment\n", encoding="utf-8")
        self.provenance = capture_software_provenance(self.root)
        self.assertTrue(self.provenance["git_dirty"])
        self._write_manifest()
        self.assertEqual(verify_software_provenance(self.manifest_path, self.root), [])
        source.write_text("changed again\n", encoding="utf-8")
        errors = verify_software_provenance(self.manifest_path, self.root)
        self.assertIn("SHA-256 mismatch for software source voltrl.py", errors)

    def test_tampered_historical_digest_is_reported(self):
        self.provenance["files"][0]["sha256"] = "0" * 64
        self._write_manifest()
        errors = verify_software_provenance(self.manifest_path, self.root)
        self.assertIn("SHA-256 mismatch for software source voltrl.py", errors)

    def test_missing_required_source_record_is_reported(self):
        self.provenance["files"] = self.provenance["files"][1:]
        self._write_manifest()
        errors = verify_software_provenance(self.manifest_path, self.root)
        self.assertIn("missing software source records: voltrl.py", errors)

    def test_parent_traversal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "stay below"):
            capture_software_provenance(self.root, ["../outside.py"])

    def test_cli_reports_success_and_failure(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(
                main([str(self.manifest_path), "--source-root", str(self.root)]), 0
            )
        self.assertIn("Verified 3 software files", stdout.getvalue())

        self.provenance["files"][1]["bytes"] = 1
        self._write_manifest()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(
                main([str(self.manifest_path), "--source-root", str(self.root)]), 1
            )
        self.assertIn("size mismatch", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
