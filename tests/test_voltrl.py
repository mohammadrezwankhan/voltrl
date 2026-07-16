import unittest

import numpy as np
import pandas as pd

from voltrl import (
    Action,
    BatteryArbitrageMDP,
    BatterySpec,
    PriceDiscretizer,
    SolverConfig,
    estimate_price_transition,
    perfect_foresight_dispatch,
    policy_bellman_residual,
    policy_iteration,
    simulate_policy,
    trajectory_metrics,
    value_iteration,
)


class VoltRLTests(unittest.TestCase):
    def setUp(self):
        self.battery = BatterySpec()
        self.price_transition = np.array([[0.85, 0.15], [0.25, 0.75]])
        self.mdp = BatteryArbitrageMDP.build(
            self.battery, np.array([20.0, 100.0]), self.price_transition
        )

    def test_boundary_actions_and_transition_rows(self):
        for price_bin in range(2):
            empty = self.mdp.state_index(0, price_bin)
            full = self.mdp.state_index(self.mdp.n_soc_levels - 1, price_bin)
            self.assertFalse(self.mdp.valid_actions[empty, Action.DISCHARGE])
            self.assertFalse(self.mdp.valid_actions[full, Action.CHARGE])
        valid_rows = self.mdp.transition[self.mdp.valid_actions]
        np.testing.assert_allclose(valid_rows.sum(axis=1), 1.0, atol=1e-12)

    def test_transition_estimator_is_smoothed_and_stochastic(self):
        sequence = np.array([0, 0, 1, 1, 1, 0, 1, 0])
        transition, counts = estimate_price_transition(sequence, 3, prior_strength=1.0)
        self.assertEqual(counts.shape, (3, 3))
        self.assertTrue(np.all(transition > 0.0))
        np.testing.assert_allclose(transition.sum(axis=1), 1.0, atol=1e-12)

    def test_value_and_policy_iteration_agree(self):
        config = SolverConfig(gamma=0.95, tolerance=1e-10)
        vi = value_iteration(self.mdp, config)
        pi = policy_iteration(self.mdp, config)
        self.assertTrue(vi.converged)
        self.assertTrue(pi.converged)
        np.testing.assert_allclose(vi.values, pi.values, atol=2e-7, rtol=0.0)
        self.assertLess(policy_bellman_residual(self.mdp, pi.values, config.gamma), 1e-7)
        self.assertTrue(np.array_equal(vi.policy, pi.policy))

    def test_simulation_respects_soc_bounds(self):
        prices = np.tile([15.0, 110.0, 20.0, 90.0], 30)
        timestamps = pd.date_range("2025-01-01", periods=len(prices), freq="h")
        discretizer = PriceDiscretizer.fit(prices, 2)
        transition, _ = estimate_price_transition(discretizer.transform(prices), 2)
        mdp = BatteryArbitrageMDP.build(
            self.battery, discretizer.representatives, transition
        )
        policy = value_iteration(mdp, SolverConfig(gamma=0.95, tolerance=1e-9)).policy
        trajectory = simulate_policy(
            prices, timestamps.astype(str), discretizer, mdp, policy, 200.0
        )
        self.assertGreaterEqual(trajectory["soc_after_mwh"].min(), 0.0)
        self.assertLessEqual(trajectory["soc_after_mwh"].max(), 500.0)

    def test_perfect_foresight_is_an_upper_bound_after_inventory_adjustment(self):
        prices = np.tile([10.0, 15.0, 100.0, 80.0], 40)
        timestamps = pd.date_range("2025-01-01", periods=len(prices), freq="h")
        discretizer = PriceDiscretizer.fit(prices, 2)
        transition, _ = estimate_price_transition(discretizer.transform(prices), 2)
        mdp = BatteryArbitrageMDP.build(
            self.battery, discretizer.representatives, transition
        )
        policy = value_iteration(mdp, SolverConfig(gamma=0.95, tolerance=1e-9)).policy
        learned = simulate_policy(
            prices, timestamps.astype(str), discretizer, mdp, policy, 200.0
        )
        perfect = perfect_foresight_dispatch(
            prices, timestamps.astype(str), self.battery, 200.0, 50.0
        )
        metrics = trajectory_metrics(learned, perfect, self.battery, 200.0, 50.0)
        self.assertLessEqual(
            metrics["inventory_adjusted_profit"],
            metrics["perfect_foresight_inventory_adjusted_profit"] + 1e-8,
        )

    def test_nonlinear_degradation_penalizes_deep_discharge(self):
        battery = BatterySpec(
            degradation_cost_per_mwh=5.0,
            nonlinear_degradation=True,
            dod_stress_exponent=1.6,
            linear_degradation_fraction=0.25,
        )
        shallow = battery.degradation_cost(Action.DISCHARGE, 500.0)
        deep = battery.degradation_cost(Action.DISCHARGE, 100.0)
        self.assertGreater(deep, shallow)

    def test_nonlinear_full_cycle_matches_nominal_linear_cost(self):
        battery = BatterySpec(
            degradation_cost_per_mwh=5.0,
            nonlinear_degradation=True,
            dod_stress_exponent=1.6,
            linear_degradation_fraction=0.25,
        )
        total = 0.0
        soc = 0.0
        for _ in range(5):
            total += battery.degradation_cost(Action.CHARGE, soc)
            soc += 100.0
        for _ in range(5):
            total += battery.degradation_cost(Action.DISCHARGE, soc)
            soc -= 100.0
        self.assertAlmostEqual(total, 2.0 * 500.0 * 5.0, places=8)


if __name__ == "__main__":
    unittest.main()
