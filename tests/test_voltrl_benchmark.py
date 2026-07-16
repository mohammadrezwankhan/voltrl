import unittest

import numpy as np
import pandas as pd

from voltrl import BatterySpec, generate_synthetic_prices, perfect_foresight_dispatch
from voltrl_benchmark import (
    chronological_split,
    continuous_predictive_nll,
    expanding_window_selection,
    finite_horizon_policy,
    fit_state_model,
    simulate_finite_policy,
    trajectory_metrics,
)


class VoltRLBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = generate_synthetic_prices(hours=2400, seed=7)
        cls.train, cls.test = chronological_split(cls.frame)

    def test_hour_conditioned_transitions_are_stochastic(self):
        model = fit_state_model(self.train, n_bins=4, calendar_aware=True)
        self.assertEqual(model.transition.shape, (24, 4, 4))
        self.assertTrue(np.all(model.transition > 0.0))
        np.testing.assert_allclose(model.transition.sum(axis=2), 1.0, atol=1e-12)

    def test_continuous_score_has_full_support_for_extreme_tail(self):
        model = fit_state_model(self.train, n_bins=4, calendar_aware=False)
        tail = self.test.copy()
        tail.loc[tail.index[-1], "price"] = 10_000.0
        score = continuous_predictive_nll(model, tail)
        self.assertTrue(np.isfinite(score))

    def test_expanding_window_selection_is_complete_and_deterministic(self):
        best_a, table_a = expanding_window_selection(self.train, (3, 4))
        best_b, table_b = expanding_window_selection(self.train, (3, 4))
        self.assertIn(best_a, (3, 4))
        self.assertEqual(best_a, best_b)
        self.assertEqual(len(table_a), 3 * 2 * 2)
        pd.testing.assert_frame_equal(table_a, table_b)

    def test_finite_horizon_policy_respects_bounds_and_oracle_upper_bound(self):
        battery = BatterySpec(
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            degradation_cost_per_mwh=5.0,
        )
        model = fit_state_model(self.train, n_bins=4, calendar_aware=True)
        salvage = float(np.median(self.train["price"]))
        decisions = finite_horizon_policy(
            model, battery, self.test["timestamp"], salvage
        )
        learned = simulate_finite_policy(
            self.test, model, decisions, battery, initial_soc_mwh=200.0
        )
        self.assertGreaterEqual(learned["soc_after_mwh"].min(), 0.0)
        self.assertLessEqual(learned["soc_after_mwh"].max(), 500.0)
        oracle = perfect_foresight_dispatch(
            self.test["price"].to_numpy(),
            self.test["timestamp"].astype(str).tolist(),
            battery,
            200.0,
            salvage,
        )
        learned_result = trajectory_metrics(learned, battery, 200.0, salvage)
        oracle_result = trajectory_metrics(oracle, battery, 200.0, salvage)
        self.assertLessEqual(
            learned_result["inventory_adjusted_profit"],
            oracle_result["inventory_adjusted_profit"] + 1e-8,
        )


if __name__ == "__main__":
    unittest.main()
