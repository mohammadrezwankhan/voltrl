from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import result_bundle_audit


class ResultBundleAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[1]

    def test_revision_one_passes_and_skips_historical_check(self) -> None:
        report = result_bundle_audit.audit_result_bundle(
            self.repository / "results_revision" / "experiment_manifest.json"
        )

        self.assertTrue(report.passed)
        statuses = {check.name: check.status for check in report.checks}
        self.assertEqual(statuses["experiment_contract"], "passed")
        self.assertEqual(statuses["artifact_integrity"], "passed")
        self.assertEqual(statuses["software_provenance"], "passed")
        self.assertEqual(statuses["historical_forecast_contract"], "skipped")

    def test_revision_two_runs_and_passes_all_checks(self) -> None:
        report = result_bundle_audit.audit_result_bundle(
            self.repository / "results_revision2" / "experiment_manifest.json"
        )

        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 4)
        self.assertTrue(all(check.status == "passed" for check in report.checks))

    def test_historical_audit_requires_forecast_specific_declaration(self) -> None:
        self.assertFalse(
            result_bundle_audit._requires_historical_audit(
                {"outputs": ["real_market_metrics.csv"]}
            )
        )
        self.assertTrue(
            result_bundle_audit._requires_historical_audit(
                {"outputs": ["historical_forecast_detail.csv"]}
            )
        )

    def test_failed_verifier_is_preserved_in_aggregate_report(self) -> None:
        manifest = (
            self.repository / "results_revision" / "experiment_manifest.json"
        )
        with patch(
            "result_bundle_audit.verify_artifact_manifest",
            return_value=["SHA-256 mismatch for figure.png"],
        ):
            report = result_bundle_audit.audit_result_bundle(manifest)

        self.assertFalse(report.passed)
        artifact_check = next(
            check for check in report.checks if check.name == "artifact_integrity"
        )
        self.assertEqual(artifact_check.status, "failed")
        self.assertEqual(
            artifact_check.errors,
            ("SHA-256 mismatch for figure.png",),
        )

    def test_expected_verifier_exception_becomes_failed_check(self) -> None:
        manifest = (
            self.repository / "results_revision" / "experiment_manifest.json"
        )
        with patch(
            "result_bundle_audit.verify_experiment_contract",
            side_effect=ValueError("invalid contract"),
        ):
            report = result_bundle_audit.audit_result_bundle(manifest)

        self.assertFalse(report.passed)
        self.assertEqual(report.checks[0].status, "failed")
        self.assertEqual(report.checks[0].errors, ("invalid contract",))

    def test_json_cli_report_is_machine_readable(self) -> None:
        manifest = (
            self.repository / "results_revision2" / "experiment_manifest.json"
        )
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = result_bundle_audit.main([str(manifest), "--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["passed"])
        self.assertEqual(len(payload["checks"]), 4)

    def test_invalid_manifest_returns_nonzero_json_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "experiment_manifest.json"
            manifest.write_text("[]\n", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = result_bundle_audit.main([str(manifest), "--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["passed"])
        self.assertIn("JSON object", payload["error"])


if __name__ == "__main__":
    unittest.main()
