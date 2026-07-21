from __future__ import annotations

import contextlib
import csv
import io
import json
import statistics
import tempfile
import unittest
from pathlib import Path

from synthetic_statistics_contract import (
    main,
    verify_synthetic_statistics_contract,
)


class SyntheticStatisticsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.result_dir = Path(self.temporary_directory.name)
        self.manifest_path = self.result_dir / "experiment_manifest.json"
        self.outputs = [
            "synthetic_seed_metrics.csv",
            "synthetic_summary.csv",
            "paired_seed_comparisons.csv",
        ]
        self.manifest = {
            "synthetic_seeds": [0, 1, 2],
            "outputs": self.outputs,
        }
        policy_values = {
            "Policy A": ([100.0, 120.0, 140.0], [50.0, 60.0, 70.0]),
            "Policy B": ([80.0, 110.0, 120.0], [40.0, 55.0, 65.0]),
        }
        self.metrics = [
            {
                "seed": seed,
                "policy": policy,
                "test_hours": 8760,
                "inventory_adjusted_profit": profits[seed],
                "annualized_adjusted_profit": profits[seed],
                "oracle_efficiency_percent": efficiencies[seed],
            }
            for policy, (profits, efficiencies) in policy_values.items()
            for seed in range(3)
        ]
        self.summaries = []
        for policy, (profits, efficiencies) in policy_values.items():
            mean_profit = statistics.mean(profits)
            self.summaries.append(
                {
                    "policy": policy,
                    "seeds": 3,
                    "mean_annualized_profit": mean_profit,
                    "standard_deviation": statistics.stdev(profits),
                    "bootstrap_ci95_lower": mean_profit - 20.0,
                    "bootstrap_ci95_upper": mean_profit + 20.0,
                    "mean_oracle_efficiency_percent": statistics.mean(
                        efficiencies
                    ),
                }
            )
        differences = [20.0, 10.0, 20.0]
        self.comparisons = [
            {
                "comparison": "Policy A minus Policy B",
                "seeds": 3,
                "mean_paired_difference": statistics.mean(differences),
                "bootstrap_ci95_lower": 10.0,
                "bootstrap_ci95_upper": 20.0,
                "positive_seed_fraction": 1.0,
            }
        ]
        self._write_fixture()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_csv(self, filename: str, rows: list[dict[str, object]]) -> None:
        with (self.result_dir / filename).open(
            "w", encoding="utf-8", newline=""
        ) as output_file:
            writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _write_fixture(self) -> None:
        self.manifest_path.write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        self._write_csv("synthetic_seed_metrics.csv", self.metrics)
        self._write_csv("synthetic_summary.csv", self.summaries)
        self._write_csv("paired_seed_comparisons.csv", self.comparisons)

    def test_valid_contract_verifies(self) -> None:
        self.assertEqual(
            verify_synthetic_statistics_contract(self.manifest_path), []
        )

    def test_published_result_contracts_verify(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        for result_dir in ("results_revision", "results_revision2"):
            with self.subTest(result_dir=result_dir):
                errors = verify_synthetic_statistics_contract(
                    repository / result_dir / "experiment_manifest.json"
                )
                self.assertEqual(errors, [])

    def test_summary_statistics_are_recomputed(self) -> None:
        self.summaries[0]["mean_annualized_profit"] = 999.0
        self.summaries[0]["standard_deviation"] = 999.0
        self.summaries[0]["mean_oracle_efficiency_percent"] = 99.0
        self.summaries[0]["bootstrap_ci95_upper"] = 1000.0
        self._write_fixture()

        errors = verify_synthetic_statistics_contract(self.manifest_path)

        self.assertTrue(any("mean_annualized_profit" in error for error in errors))
        self.assertTrue(any("standard_deviation" in error for error in errors))
        self.assertTrue(
            any("mean_oracle_efficiency_percent" in error for error in errors)
        )

    def test_paired_statistics_are_recomputed(self) -> None:
        self.comparisons[0]["seeds"] = 2
        self.comparisons[0]["mean_paired_difference"] = 12.0
        self.comparisons[0]["positive_seed_fraction"] = 0.5
        self._write_fixture()

        errors = verify_synthetic_statistics_contract(self.manifest_path)

        self.assertTrue(any("comparison seeds" in error for error in errors))
        self.assertTrue(
            any("comparison mean_paired_difference" in error for error in errors)
        )
        self.assertTrue(
            any("comparison positive_seed_fraction" in error for error in errors)
        )

    def test_metric_annualization_and_bounds_are_checked(self) -> None:
        self.metrics[0]["annualized_adjusted_profit"] = 101.0
        self.metrics[1]["oracle_efficiency_percent"] = 101.0
        self.metrics[2]["test_hours"] = 0
        self._write_fixture()

        errors = verify_synthetic_statistics_contract(self.manifest_path)

        self.assertTrue(
            any("annualized_adjusted_profit" in error for error in errors)
        )
        self.assertTrue(any("must not exceed 100" in error for error in errors))
        self.assertTrue(any("test_hours must be positive" in error for error in errors))

    def test_seed_coverage_and_duplicate_rows_are_checked(self) -> None:
        self.metrics = [
            row
            for row in self.metrics
            if not (row["seed"] == 2 and row["policy"] == "Policy B")
        ]
        self.metrics.append(dict(self.metrics[0]))
        self._write_fixture()

        errors = verify_synthetic_statistics_contract(self.manifest_path)

        self.assertTrue(any("duplicates seed/policy pair" in error for error in errors))
        self.assertTrue(any("seed coverage mismatch" in error for error in errors))

    def test_intervals_and_comparison_labels_are_checked(self) -> None:
        self.summaries[0]["bootstrap_ci95_lower"] = 200.0
        self.summaries[0]["bootstrap_ci95_upper"] = 100.0
        self.comparisons[0]["comparison"] = "Unknown contrast"
        self._write_fixture()

        errors = verify_synthetic_statistics_contract(self.manifest_path)

        self.assertTrue(any("interval is reversed" in error for error in errors))
        self.assertTrue(
            any("does not identify two declared policies" in error for error in errors)
        )

    def test_manifest_and_required_columns_are_checked(self) -> None:
        self.manifest["outputs"].remove("paired_seed_comparisons.csv")
        self._write_fixture()
        with (self.result_dir / "synthetic_summary.csv").open(
            "w", encoding="utf-8", newline=""
        ) as output_file:
            writer = csv.DictWriter(output_file, fieldnames=("policy", "seeds"))
            writer.writeheader()
            writer.writerow({"policy": "Policy A", "seeds": 3})

        errors = verify_synthetic_statistics_contract(self.manifest_path)

        self.assertTrue(any("manifest outputs omit" in error for error in errors))
        self.assertTrue(any("is missing columns" in error for error in errors))

    def test_cli_reports_success_and_failure(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main([str(self.manifest_path)])
        self.assertEqual(exit_code, 0)
        self.assertIn("6 seed-policy rows", stdout.getvalue())
        self.assertIn("1 paired comparisons", stdout.getvalue())

        self.comparisons[0]["mean_paired_difference"] = 0.0
        self._write_fixture()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = main([str(self.manifest_path)])
        self.assertEqual(exit_code, 1)
        self.assertIn("recomputed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
