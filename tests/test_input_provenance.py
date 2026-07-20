import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from input_provenance import load_source_record, main, verify_source_file


class InputProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source_path = self.root / "source.csv"
        self.source_path.write_bytes(b"timestamp,value\n2020-01-01,1\n")
        self.record_path = self.root / "source.json"
        self.record = {
            "dataset": "Test dataset",
            "version": "2020-01-01",
            "doi": "10.0000/example",
            "url": "https://example.com/dataset/",
            "filename": self.source_path.name,
            "sha256": hashlib.sha256(self.source_path.read_bytes()).hexdigest(),
        }
        self._write_record()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _write_record(self):
        self.record_path.write_text(json.dumps(self.record), encoding="utf-8")

    def test_matching_source_is_verified(self):
        verification = verify_source_file(self.source_path, self.record_path)
        self.assertEqual(verification.bytes, self.source_path.stat().st_size)
        self.assertEqual(verification.sha256, self.record["sha256"])
        self.assertEqual(verification.version, "2020-01-01")

    def test_tampered_source_is_rejected(self):
        self.source_path.write_bytes(b"timestamp,value\n2020-01-01,2\n")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify_source_file(self.source_path, self.record_path)

    def test_wrong_source_filename_is_rejected(self):
        self.record["filename"] = "different.csv"
        self._write_record()
        with self.assertRaisesRegex(ValueError, "filename mismatch"):
            verify_source_file(self.source_path, self.record_path)

    def test_invalid_checksum_record_is_rejected(self):
        self.record["sha256"] = "not-a-digest"
        self._write_record()
        with self.assertRaisesRegex(ValueError, "64 hexadecimal"):
            load_source_record(self.record_path)

    def test_cli_reports_success_and_failure(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(
                main([str(self.source_path), "--record", str(self.record_path)]), 0
            )
        self.assertIn("Verified source.csv", stdout.getvalue())

        self.source_path.write_bytes(b"changed")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(
                main([str(self.source_path), "--record", str(self.record_path)]), 1
            )
        self.assertIn("SHA-256 mismatch", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
