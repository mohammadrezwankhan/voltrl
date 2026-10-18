import unittest

import numpy as np
import pandas as pd

from voltrl import Action, BatterySpec, SolverConfig, estimate_price_transition
from voltrl_benchmark import (
    SeasonalARModel,
    fit_seasonal_ar,
    fit_state_model,
    seasonal_ar_forecast,
    trajectory_from_actions,
)


class NumericAndCausalInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=504, freq="h", tz="UTC"),
                "price": 50.0 + np.tile(np.arange(24, dtype=float), 21),
            }
        )

    def test_transition_prior_must_be_finite_and_nonnegative(self):
        for prior in (-1.0, np.nan, np.inf, -np.inf):
            with self.subTest(prior=prior, estimator="price"):
                with self.assertRaises(ValueError):
                    estimate_price_transition([0, 1, 0, 1], 2, prior_strength=prior)
            for calendar_aware in (False, True):
                with self.subTest(prior=prior, calendar_aware=calendar_aware):
                    with self.assertRaises(ValueError):
                        fit_state_model(self.frame, 4, calendar_aware, prior_strength=prior)

    def test_zero_prior_requires_an_observed_outgoing_transition_per_state(self):
        with self.assertRaisesRegex(ValueError, "(?i)unobserved|unseen|zero"):
            fit_state_model(self.frame, 4, True, prior_strength=0.0)
        model = fit_state_model(self.frame, 4, False, prior_strength=0.0)
        self.assertTrue(np.all(model.transition >= 0.0))
        np.testing.assert_allclose(model.transition.sum(axis=-1), 1.0)

    def test_ar_fit_rejects_noncausal_or_unusable_lags(self):
        for lags in ((), (0,), (-1,), (1.5,), (True,), (len(self.frame),)):
            with self.subTest(lags=lags), self.assertRaisesRegex(ValueError, "lag|history"):
                fit_seasonal_ar(self.frame, lags=lags)

    def test_ar_ridge_must_be_finite_and_nonnegative(self):
        for ridge in (-1.0, np.nan, np.inf):
            with self.subTest(ridge=ridge), self.assertRaises(ValueError):
                fit_seasonal_ar(self.frame, ridge=ridge)

    @staticmethod
    def lag_two_model():
        return SeasonalARModel(
            lags=(2,),
            coefficients=np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            price_mean=0.0,
            price_scale=1.0,
            clip_low=-1e6,
            clip_high=1e6,
        )

    def test_forecast_rejects_insufficient_history_instead_of_reading_array_tail(self):
        timestamps = self.frame["timestamp"].iloc[:3]
        with self.assertRaisesRegex(ValueError, "history|lag"):
            seasonal_ar_forecast(self.lag_two_model(), np.array([10.0, 20.0, 99.0]), timestamps, 0, steps=1)

    def test_forecast_uses_available_history_and_ignores_unknown_future_prices(self):
        timestamps = self.frame["timestamp"].iloc[:3]
        result = seasonal_ar_forecast(
            self.lag_two_model(), np.array([10.0, 20.0, np.nan]), timestamps, 1, steps=1
        )
        np.testing.assert_array_equal(result, [10.0])

    def test_forecast_rejects_invalid_index_horizon_and_missing_timestamps(self):
        prices = np.array([10.0, 20.0, 30.0])
        timestamps = self.frame["timestamp"].iloc[:3]
        for index, steps in ((-1, 1), (3, 1), (1.5, 1), (1, -1), (1, 1.5), (1, 2)):
            with self.subTest(index=index, steps=steps), self.assertRaises(ValueError):
                seasonal_ar_forecast(self.lag_two_model(), prices, timestamps, index, steps)

    def test_actions_cannot_be_silently_reassigned_when_frame_is_sorted(self):
        frame = self.frame.copy()
        frame.loc[0, "price"] = 10.0
        frame.loc[1, "price"] = 100.0
        frame = frame.iloc[[1, 0, *range(2, len(frame))]].reset_index(drop=True)
        actions = [Action.DISCHARGE, Action.CHARGE] + [Action.IDLE] * (len(frame) - 2)
        with self.assertRaisesRegex(ValueError, "chronological|order|align"):
            trajectory_from_actions(frame, actions, BatterySpec(), 200.0)

    def test_action_values_are_validated_before_integer_conversion(self):
        for action in (0.5, 1.5, np.nan, np.inf, -1, 3):
            actions = np.full(len(self.frame), float(Action.IDLE))
            actions[0] = action
            with self.subTest(action=action), self.assertRaises(ValueError):
                trajectory_from_actions(self.frame, actions, BatterySpec(), 200.0)
        with self.assertRaises(ValueError):
            BatterySpec().soc_delta(1.5)

    def test_chronological_actions_preserve_price_alignment_and_cash_flow(self):
        frame = self.frame.copy()
        frame.loc[0, "price"] = 10.0
        frame.loc[1, "price"] = 100.0
        actions = [Action.CHARGE, Action.DISCHARGE] + [Action.IDLE] * (len(frame) - 2)
        trajectory = trajectory_from_actions(frame, actions, BatterySpec(), 200.0)
        self.assertEqual(trajectory["profit"].sum(), 9000.0)
        self.assertEqual(trajectory["soc_after_mwh"].iloc[-1], 200.0)

    def test_battery_parameters_must_be_finite(self):
        for field in (
            "capacity_mwh", "max_power_mw", "interval_hours", "charge_efficiency",
            "discharge_efficiency", "degradation_cost_per_mwh", "dod_stress_exponent",
            "linear_degradation_fraction", "soc_stress_cost_per_hour",
        ):
            for value in (np.nan, np.inf, -np.inf):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    BatterySpec(**{field: value})

    def test_solver_rejects_nonfinite_tolerance_and_noninteger_iteration_limit(self):
        for tolerance in (np.nan, np.inf, -np.inf):
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                SolverConfig(tolerance=tolerance)
        for limit in (np.nan, np.inf, 1.5, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                SolverConfig(max_iterations=limit)


if __name__ == "__main__":
    unittest.main()
