import unittest

import numpy as np
import pandas as pd

from voltrl import BatterySpec, generate_synthetic_prices, perfect_foresight_dispatch
from voltrl_benchmark import (
    chronological_day_split,
    chronological_split,
    continuous_predictive_nll,
    day_ahead_block_trajectory,
    expanding_window_selection,
    finite_horizon_policy,
    fit_seasonal_ar,
    fit_state_model,
    seasonal_ar_forecast,
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

    def test_seasonal_ar_forecast_does_not_read_future_prices(self):
        model = fit_seasonal_ar(self.train)
        combined = pd.concat([self.train, self.test], ignore_index=True)
        prices_a = combined["price"].to_numpy(dtype=float)
        prices_b = prices_a.copy()
        current = len(self.train) + 12
        prices_b[current + 1 :] += 10_000.0
        prediction_a = seasonal_ar_forecast(
            model, prices_a, combined["timestamp"], current, steps=24
        )
        prediction_b = seasonal_ar_forecast(
            model, prices_b, combined["timestamp"], current, steps=24
        )
        np.testing.assert_allclose(prediction_a, prediction_b, atol=0.0, rtol=0.0)

    def test_day_ahead_actions_are_fixed_before_delivery_prices(self):
        train, test, _ = chronological_day_split(self.frame)
        battery = BatterySpec(
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            degradation_cost_per_mwh=5.0,
            nonlinear_degradation=True,
            dod_stress_exponent=1.6,
            linear_degradation_fraction=0.25,
            soc_stress_cost_per_hour=1.0,
        )
        salvage = float(np.median(train["price"]))
        baseline, forecast = day_ahead_block_trajectory(
            train, test, battery, 200.0, salvage, "sarx"
        )
        altered = test.copy()
        altered.loc[altered.index[:24], "price"] += 10_000.0
        changed, _ = day_ahead_block_trajectory(
            train, altered, battery, 200.0, salvage, "sarx"
        )
        self.assertEqual(
            baseline["action"].iloc[:24].tolist(),
            changed["action"].iloc[:24].tolist(),
        )
        decision = pd.to_datetime(
            forecast["information_available_through_delivery_timestamp"], utc=True
        )
        delivery = pd.to_datetime(forecast["delivery_timestamp"], utc=True)
        self.assertTrue(bool((decision < delivery).all()))


if __name__ == "__main__":
    unittest.main()
