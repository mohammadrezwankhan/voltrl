import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from artifact_integrity import (
    build_artifact_inventory,
    record_artifact_inventory,
    verify_artifact_manifest,
)


class ArtifactIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.result_dir = Path(self.temporary_directory.name)
        (self.result_dir / "figures").mkdir()
        (self.result_dir / "metrics.csv").write_bytes(b"value\n1\n")
        (self.result_dir / "figures" / "result.pdf").write_bytes(b"pdf-data")
        self.outputs = ["metrics.csv", "figures/result.pdf"]
        self.manifest_path = self.result_dir / "experiment_manifest.json"
        self.manifest_path.write_text(
            json.dumps({"outputs": self.outputs}), encoding="utf-8"
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_inventory_records_size_and_sha256_in_output_order(self):
        inventory = build_artifact_inventory(self.result_dir, self.outputs)
        self.assertEqual([entry["path"] for entry in inventory], self.outputs)
        self.assertEqual(inventory[0]["bytes"], 8)
        self.assertEqual(
            inventory[0]["sha256"], hashlib.sha256(b"value\n1\n").hexdigest()
        )

    def test_recorded_manifest_verifies(self):
        self.assertEqual(record_artifact_inventory(self.manifest_path), 2)
        self.assertEqual(verify_artifact_manifest(self.manifest_path), [])

    def test_csv_line_endings_are_canonicalized_to_lf(self):
        metrics = self.result_dir / "metrics.csv"
        metrics.write_bytes(b"value\r\n1\r\n")
        crlf_inventory = build_artifact_inventory(self.result_dir, ["metrics.csv"])
        metrics.write_bytes(b"value\n1\n")
        lf_inventory = build_artifact_inventory(self.result_dir, ["metrics.csv"])
        self.assertEqual(crlf_inventory, lf_inventory)
        self.assertEqual(crlf_inventory[0]["bytes"], 8)

    def test_tampering_is_reported(self):
        record_artifact_inventory(self.manifest_path)
        (self.result_dir / "metrics.csv").write_bytes(b"value\n2\n")
        errors = verify_artifact_manifest(self.manifest_path)
        self.assertIn("SHA-256 mismatch for metrics.csv", errors)

    def test_incomplete_inventory_is_reported(self):
        inventory = build_artifact_inventory(self.result_dir, self.outputs[:1])
        self.manifest_path.write_text(
            json.dumps({"outputs": self.outputs, "artifact_inventory": inventory}),
            encoding="utf-8",
        )
        errors = verify_artifact_manifest(self.manifest_path)
        self.assertIn("missing inventory records: figures/result.pdf", errors)

    def test_parent_traversal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "stay below"):
            build_artifact_inventory(self.result_dir, ["../outside.csv"])


if __name__ == "__main__":
    unittest.main()
