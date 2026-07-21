import contextlib
import csv
import io
import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from historical_forecast_contract import (
    main,
    verify_historical_forecast_contract,
)


class HistoricalForecastContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.result_dir = Path(self.temporary_directory.name) / "results"
        self.result_dir.mkdir()
        self.manifest_path = self.result_dir / "experiment_manifest.json"
        self.manifest = {
            "historical_information_protocol": (
                "one 24-hour schedule fixed before each UTC delivery day"
            ),
            "outputs": [
                "historical_forecast_detail.csv",
                "historical_forecast_summary.csv",
                "real_market_metrics.csv",
            ],
        }
        self.detail = self._build_detail()
        self.summary = self._build_summary()
        self.market = [
            {
                "case": "DK1 day-ahead block",
                "policy": "Test policy",
                "test_hours": 48,
                "information_protocol": "24-hour schedule fixed before delivery day",
            }
        ]
        self._write_fixture()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _build_detail(self):
        rows = []
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for day in range(2):
            available = start + timedelta(days=day) - timedelta(hours=1)
            for method, bias in (("sarx", 1.0), ("persistence", -2.0)):
                for lead in range(1, 25):
                    delivery = available + timedelta(hours=lead)
                    realized = float(day * 24 + lead)
                    forecast = realized + bias
                    rows.append(
                        {
                            "case": "DK1 day-ahead block",
                            "forecast_method": method,
                            "information_available_through_delivery_timestamp": (
                                available.isoformat()
                            ),
                            "commitment_protocol": (
                                "schedule fixed before delivery-day auction clearing"
                            ),
                            "delivery_timestamp": delivery.isoformat(),
                            "lead_hour": lead,
                            "forecast_price": forecast,
                            "realized_price": realized,
                            "error": forecast - realized,
                        }
                    )
        return rows

    def _build_summary(self):
        rows = []
        for method in ("sarx", "persistence"):
            values = [
                float(row["error"])
                for row in self.detail
                if row["forecast_method"] == method
            ]
            rows.append(
                {
                    "case": "DK1 day-ahead block",
                    "forecast_method": method,
                    "observations": len(values),
                    "mean_error": math.fsum(values) / len(values),
                    "mean_absolute_error": (
                        math.fsum(abs(value) for value in values) / len(values)
                    ),
                    "root_mean_squared_error": math.sqrt(
                        math.fsum(value * value for value in values) / len(values)
                    ),
                }
            )
        return rows

    def _write_csv(self, filename, rows):
        with (self.result_dir / filename).open(
            "w", encoding="utf-8", newline=""
        ) as output_file:
            writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _write_fixture(self):
        self.manifest_path.write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        self._write_csv("historical_forecast_detail.csv", self.detail)
        self._write_csv("historical_forecast_summary.csv", self.summary)
        self._write_csv("real_market_metrics.csv", self.market)

    def test_valid_contract_verifies(self):
        self.assertEqual(
            verify_historical_forecast_contract(self.manifest_path), []
        )

    def test_published_revision2_contract_verifies(self):
        repository_root = Path(__file__).resolve().parents[1]
        errors = verify_historical_forecast_contract(
            repository_root / "results_revision2" / "experiment_manifest.json"
        )
        self.assertEqual(errors, [])

    def test_noncausal_timing_and_incomplete_block_are_reported(self):
        self.detail[0]["information_available_through_delivery_timestamp"] = (
            self.detail[0]["delivery_timestamp"]
        )
        self.detail.pop(1)
        self._write_fixture()
        errors = verify_historical_forecast_contract(self.manifest_path)
        self.assertTrue(any("at or after delivery" in error for error in errors))
        self.assertTrue(
            any("incomplete 24-hour forecast block" in error for error in errors)
        )

    def test_detail_error_and_summary_drift_are_reported(self):
        self.detail[0]["error"] = 7.0
        self.summary[0]["root_mean_squared_error"] = 99.0
        self._write_fixture()
        errors = verify_historical_forecast_contract(self.manifest_path)
        self.assertTrue(any("forecast minus realized" in error for error in errors))
        self.assertTrue(
            any("summary root_mean_squared_error" in error for error in errors)
        )

    def test_cross_method_alignment_and_coverage_are_reported(self):
        persistence = next(
            row for row in self.detail if row["forecast_method"] == "persistence"
        )
        persistence["realized_price"] = float(persistence["realized_price"]) + 1.0
        self.detail.pop()
        self._write_fixture()
        errors = verify_historical_forecast_contract(self.manifest_path)
        self.assertTrue(any("realized price disagrees" in error for error in errors))
        self.assertTrue(any("delivery coverage mismatch" in error for error in errors))

    def test_duplicate_and_invalid_numeric_rows_are_reported(self):
        self.detail.append(dict(self.detail[0]))
        self.detail[1]["forecast_price"] = "not-a-number"
        self._write_fixture()
        errors = verify_historical_forecast_contract(self.manifest_path)
        self.assertTrue(
            any("duplicates case/method/delivery" in error for error in errors)
        )
        self.assertTrue(any("must be a finite number" in error for error in errors))

    def test_manifest_and_market_linkage_are_reported(self):
        self.manifest.pop("historical_information_protocol")
        self.manifest["outputs"].remove("historical_forecast_detail.csv")
        self.market[0]["test_hours"] = 24
        self._write_fixture()
        errors = verify_historical_forecast_contract(self.manifest_path)
        self.assertTrue(any("manifest outputs omit" in error for error in errors))
        self.assertIn(
            "historical_information_protocol must be a nonempty string", errors
        )
        self.assertTrue(
            any("real-market metrics report 24" in error for error in errors)
        )

    def test_cli_reports_success_and_failure(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main([str(self.manifest_path)]), 0)
        self.assertIn("Verified 96 forecast rows", stdout.getvalue())

        self.summary[0]["observations"] = 1
        self._write_fixture()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(main([str(self.manifest_path)]), 1)
        self.assertIn("recomputed 48", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
