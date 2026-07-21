import contextlib
import csv
import io
import json
import tempfile
import unittest
from itertools import product
from pathlib import Path

from experiment_contract import main, verify_experiment_contract


class ExperimentContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.result_dir = Path(self.temporary_directory.name)
        self.manifest_path = self.result_dir / "experiment_manifest.json"
        self.outputs = [
            "synthetic_seed_metrics.csv",
            "synthetic_summary.csv",
            "paired_seed_comparisons.csv",
            "model_selection_folds.csv",
            "case_diagnostics.csv",
        ]
        self.manifest = {
            "repository_url": "https://github.com/example/voltrl",
            "study_type": "test benchmark",
            "synthetic_generator": "voltrl.generate_synthetic_prices",
            "synthetic_seeds": [0, 1],
            "synthetic_hours_per_seed": 100,
            "chronological_train_fraction": 0.7,
            "candidate_bins": [4, 6],
            "main_battery": {
                "capacity_mwh": 500.0,
                "max_power_mw": 100.0,
                "interval_hours": 1.0,
                "charge_efficiency": 0.95,
                "discharge_efficiency": 0.95,
                "degradation_cost_per_mwh": 5.0,
                "nonlinear_degradation": True,
                "dod_stress_exponent": 1.6,
                "linear_degradation_fraction": 0.25,
                "soc_stress_cost_per_hour": 1.0,
            },
            "initial_soc_mwh": 200.0,
            "primary_planner_discount": 1.0,
            "opsd_source": {
                "package": "Test package",
                "doi": "10.0000/example",
                "url": "https://example.com/data/",
                "file": "source.csv",
                "sha256": "a" * 64,
                "markets": ["DK1", "DK2"],
            },
            "runtime": {
                "python": "3.12",
                "platform": "test",
                "numpy": "2.5.1",
                "pandas": "3.0.1",
                "matplotlib": "3.11.0",
            },
            "outputs": self.outputs,
        }
        self.metrics = [
            {
                "seed": seed,
                "policy": policy,
                "selected_bins": 4 if seed == 0 else 6,
                "test_hours": 30,
            }
            for seed, policy in product((0, 1), ("Policy A", "Policy B"))
        ]
        self.folds = [
            {"seed": seed, "n_bins": bins, "fold": fold, "model": model}
            for seed, bins, fold, model in product(
                (0, 1),
                (4, 6),
                (1, 2, 3),
                ("hour_aware", "price_only"),
            )
        ]
        self.diagnostics = [
            {
                "seed": seed,
                "observations": 100,
                "train_hours": 70,
                "test_hours": 30,
                "selected_bins": 4 if seed == 0 else 6,
            }
            for seed in (0, 1)
        ]
        self._write_fixture()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _write_csv(self, filename, rows):
        with (self.result_dir / filename).open(
            "w", encoding="utf-8", newline=""
        ) as output_file:
            writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _write_fixture(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self._write_csv("synthetic_seed_metrics.csv", self.metrics)
        self._write_csv("model_selection_folds.csv", self.folds)
        self._write_csv("case_diagnostics.csv", self.diagnostics)
        self._write_csv(
            "synthetic_summary.csv",
            [{"policy": "Policy A", "seeds": 2}],
        )
        self._write_csv(
            "paired_seed_comparisons.csv",
            [{"comparison": "A minus B", "seeds": 2}],
        )

    def test_valid_contract_verifies(self):
        self.assertEqual(verify_experiment_contract(self.manifest_path), [])

    def test_published_result_contracts_verify(self):
        repository_root = Path(__file__).resolve().parents[1]
        for result_dir in ("results_revision", "results_revision2"):
            with self.subTest(result_dir=result_dir):
                errors = verify_experiment_contract(
                    repository_root / result_dir / "experiment_manifest.json"
                )
                self.assertEqual(errors, [])

    def test_missing_seed_and_duplicate_policy_are_reported(self):
        self.metrics = [row for row in self.metrics if row["seed"] == 0]
        self.metrics.append(dict(self.metrics[0]))
        self._write_fixture()
        errors = verify_experiment_contract(self.manifest_path)
        self.assertTrue(any("seed coverage mismatch" in error for error in errors))
        self.assertTrue(any("duplicates seed/policy pair" in error for error in errors))

    def test_incomplete_selection_grid_is_reported(self):
        self.folds.pop()
        self._write_fixture()
        errors = verify_experiment_contract(self.manifest_path)
        self.assertTrue(
            any("missing 1 selection combinations" in error for error in errors)
        )

    def test_invalid_configuration_cross_fields_are_reported(self):
        self.manifest["candidate_bins"] = [4, 4]
        self.manifest["initial_soc_mwh"] = 250.0
        self._write_fixture()
        errors = verify_experiment_contract(self.manifest_path)
        self.assertIn(
            "candidate_bins must be strictly increasing and unique",
            errors,
        )
        self.assertIn("initial_soc_mwh must lie on the battery SOC grid", errors)

    def test_output_paths_must_stay_below_result_directory(self):
        self.manifest["outputs"].append("../escaped.csv")
        self._write_fixture()
        errors = verify_experiment_contract(self.manifest_path)
        self.assertTrue(
            any("must stay below the result directory" in error for error in errors)
        )

    def test_diagnostic_drift_is_reported(self):
        self.diagnostics[0]["observations"] = 101
        self._write_fixture()
        errors = verify_experiment_contract(self.manifest_path)
        self.assertTrue(any("disagree with manifest" in error for error in errors))
        self.assertTrue(any("train/test hours do not sum" in error for error in errors))

    def test_reported_seed_count_is_checked(self):
        self._write_csv(
            "synthetic_summary.csv",
            [{"policy": "Policy A", "seeds": 1}],
        )
        errors = verify_experiment_contract(self.manifest_path)
        self.assertTrue(any("reports 1 seeds; expected 2" in error for error in errors))

    def test_cli_reports_success_and_failure(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main([str(self.manifest_path)]), 0)
        self.assertIn("2 seeds, 2 candidates, and 5 tables", stdout.getvalue())

        self.folds.pop()
        self._write_fixture()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(main([str(self.manifest_path)]), 1)
        self.assertIn("missing 1 selection combinations", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
