"""Project VoltRL: finite-MDP battery arbitrage engine.

The module trains a price-bin Markov model, constructs the joint
(state-of-charge, price-bin) MDP, solves it with value iteration and policy
iteration, and evaluates the learned policy out of sample against a
perfect-foresight dynamic-programming upper bound.

The command-line entry point accepts a CSV price series.  When no CSV is
provided, it generates a deterministic synthetic benchmark so the complete
pipeline remains reproducible without external data.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import time
from dataclasses import asdict, dataclass
from enum import IntEnum
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


LOGGER = logging.getLogger("voltrl")


class Action(IntEnum):
    """Discrete control actions.

    The enumeration value is the action-array index, not an energy quantity.
    SOC increments are defined by :meth:`BatterySpec.soc_delta`.
    """

    CHARGE = 0
    IDLE = 1
    DISCHARGE = 2


ACTION_NAMES = np.array(["Charge", "Idle", "Discharge"], dtype=object)


@dataclass(frozen=True)
class BatterySpec:
    """Physical and economic parameters of the BESS."""

    capacity_mwh: float = 500.0
    max_power_mw: float = 100.0
    interval_hours: float = 1.0
    charge_efficiency: float = 1.0
    discharge_efficiency: float = 1.0
    degradation_cost_per_mwh: float = 0.0

    def __post_init__(self) -> None:
        if self.capacity_mwh <= 0 or self.max_power_mw <= 0:
            raise ValueError("Capacity and maximum power must be positive.")
        if self.interval_hours <= 0:
            raise ValueError("The market interval must be positive.")
        if not 0 < self.charge_efficiency <= 1:
            raise ValueError("Charge efficiency must lie in (0, 1].")
        if not 0 < self.discharge_efficiency <= 1:
            raise ValueError("Discharge efficiency must lie in (0, 1].")
        if self.degradation_cost_per_mwh < 0:
            raise ValueError("Degradation cost cannot be negative.")
        ratio = self.capacity_mwh / self.energy_step_mwh
        if not math.isclose(ratio, round(ratio), rel_tol=0.0, abs_tol=1e-10):
            raise ValueError(
                "Capacity must be an integer multiple of power times interval."
            )

    @property
    def energy_step_mwh(self) -> float:
        return self.max_power_mw * self.interval_hours

    @property
    def soc_levels(self) -> np.ndarray:
        n = int(round(self.capacity_mwh / self.energy_step_mwh))
        return np.linspace(0.0, self.capacity_mwh, n + 1)

    def soc_delta(self, action: int | Action) -> float:
        action = Action(int(action))
        if action == Action.CHARGE:
            return self.energy_step_mwh
        if action == Action.DISCHARGE:
            return -self.energy_step_mwh
        return 0.0

    def realized_reward(self, price: float, action: int | Action) -> float:
        """One-hour cash flow in currency units.

        Positive SOC movement requires grid purchases of ``delta / eta_c``;
        negative movement sells ``-delta * eta_d`` to the grid.
        """

        delta = self.soc_delta(action)
        grid_purchase = max(delta, 0.0) / self.charge_efficiency
        grid_sale = max(-delta, 0.0) * self.discharge_efficiency
        throughput_cost = self.degradation_cost_per_mwh * abs(delta)
        return float(price * (grid_sale - grid_purchase) - throughput_cost)


@dataclass(frozen=True)
class SolverConfig:
    gamma: float = 0.99
    tolerance: float = 1e-8
    max_iterations: int = 100_000

    def __post_init__(self) -> None:
        if not 0 <= self.gamma < 1:
            raise ValueError("Discount factor gamma must lie in [0, 1).")
        if self.tolerance <= 0 or self.max_iterations <= 0:
            raise ValueError("Tolerance and max_iterations must be positive.")


@dataclass
class PriceDiscretizer:
    """Quantile price discretizer with fitted representative prices."""

    edges: np.ndarray
    representatives: np.ndarray
    counts: np.ndarray

    @property
    def n_bins(self) -> int:
        return int(len(self.representatives))

    @classmethod
    def fit(cls, prices: Sequence[float], n_bins: int) -> "PriceDiscretizer":
        x = _clean_prices(prices)
        if n_bins < 2:
            raise ValueError("At least two price bins are required.")
        if len(x) < 10 * n_bins:
            raise ValueError("Use at least ten observations per requested bin.")

        interior = np.quantile(x, np.linspace(0.0, 1.0, n_bins + 1)[1:-1])
        interior = np.unique(interior)
        if len(interior) != n_bins - 1:
            raise ValueError(
                "Repeated quantiles produced empty bins; request fewer price bins."
            )
        edges = np.concatenate(([-np.inf], interior, [np.inf])).astype(float)
        labels = np.digitize(x, edges[1:-1], right=False)
        representatives = np.array(
            [float(np.mean(x[labels == k])) for k in range(n_bins)], dtype=float
        )
        counts = np.bincount(labels, minlength=n_bins).astype(int)
        return cls(edges=edges, representatives=representatives, counts=counts)

    def transform(self, prices: Sequence[float]) -> np.ndarray:
        x = np.asarray(prices, dtype=float)
        if np.any(~np.isfinite(x)):
            raise ValueError("Prices passed to transform must be finite.")
        labels = np.digitize(x, self.edges[1:-1], right=False)
        return np.clip(labels, 0, self.n_bins - 1).astype(int)

    def interval_labels(self, observed_prices: Sequence[float]) -> list[str]:
        x = _clean_prices(observed_prices)
        finite_edges = self.edges.copy()
        finite_edges[0] = float(np.min(x))
        finite_edges[-1] = float(np.max(x))
        return [
            f"[{finite_edges[k]:.1f}, {finite_edges[k + 1]:.1f}"
            + ("]" if k == self.n_bins - 1 else ")")
            for k in range(self.n_bins)
        ]


def _clean_prices(prices: Sequence[float]) -> np.ndarray:
    x = np.asarray(prices, dtype=float).reshape(-1)
    if len(x) < 20:
        raise ValueError("The price series must contain at least 20 observations.")
    if np.any(~np.isfinite(x)):
        raise ValueError("The price series contains NaN or infinite values.")
    return x


def estimate_price_transition(
    price_bins: Sequence[int],
    n_bins: int,
    prior_strength: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate a row-stochastic first-order price transition matrix.

    A Dirichlet empirical-marginal prior prevents zero-probability rows while
    preserving observed transition frequencies as the sample grows.
    """

    z = np.asarray(price_bins, dtype=int).reshape(-1)
    if len(z) < 2:
        raise ValueError("At least two binned prices are required.")
    if n_bins < 2 or np.any((z < 0) | (z >= n_bins)):
        raise ValueError("Price-bin indices are outside the declared range.")
    if prior_strength < 0:
        raise ValueError("Prior strength cannot be negative.")

    counts = np.zeros((n_bins, n_bins), dtype=float)
    np.add.at(counts, (z[:-1], z[1:]), 1.0)
    marginal = np.bincount(z[1:], minlength=n_bins).astype(float) + 1.0
    marginal /= marginal.sum()
    denominator = counts.sum(axis=1, keepdims=True) + prior_strength
    if prior_strength == 0 and np.any(denominator == 0):
        raise ValueError("Unseen source bins require a positive prior strength.")
    transition = (counts + prior_strength * marginal[None, :]) / denominator
    if not np.allclose(transition.sum(axis=1), 1.0, atol=1e-12):
        raise AssertionError("Estimated transition matrix is not row-stochastic.")
    return transition, counts


def select_bin_count_bic(
    prices: Sequence[float],
    candidates: Iterable[int] = range(4, 11),
    validation_fraction: float = 0.2,
    prior_strength: float = 1.0,
) -> tuple[int, pd.DataFrame]:
    """Select a quantile-bin count using chronological validation and BIC.

    For each candidate, the first-order Markov kernel is fitted on the early
    training segment and scored on the held-out tail.  To make likelihoods
    comparable across different bin counts, the categorical transition
    probability is converted to a piecewise-uniform conditional *density* by
    dividing by the destination-bin width.  The criterion is
    ``BIC = -2 log L_density + (k(k-1) + k-1) log(n_validation_transitions)``;
    the final term counts transition and interior-edge parameters.
    """

    x = _clean_prices(prices)
    if not 0.05 <= validation_fraction <= 0.5:
        raise ValueError("validation_fraction must lie in [0.05, 0.5].")
    split = int(round(len(x) * (1.0 - validation_fraction)))
    fit_x, valid_x = x[:split], x[split:]
    rows: list[dict[str, float | int]] = []
    for candidate in sorted(set(int(k) for k in candidates)):
        try:
            discretizer = PriceDiscretizer.fit(fit_x, candidate)
            fit_bins = discretizer.transform(fit_x)
            valid_bins = discretizer.transform(valid_x)
            transition, _ = estimate_price_transition(
                fit_bins, candidate, prior_strength=prior_strength
            )
            probabilities = transition[valid_bins[:-1], valid_bins[1:]]
            finite_edges = discretizer.edges.copy()
            finite_edges[0] = float(np.min(fit_x))
            finite_edges[-1] = float(np.max(fit_x))
            widths = np.maximum(np.diff(finite_edges), 1e-12)
            destination_widths = widths[valid_bins[1:]]
            log_likelihood = float(
                (
                    np.log(np.maximum(probabilities, 1e-300))
                    - np.log(destination_widths)
                ).sum()
            )
            n_obs = max(1, len(probabilities))
            parameters = candidate * (candidate - 1) + candidate - 1
            bic = -2.0 * log_likelihood + parameters * math.log(n_obs)
            rows.append(
                {
                    "n_bins": candidate,
                    "log_likelihood": log_likelihood,
                    "parameters": parameters,
                    "bic": bic,
                }
            )
        except ValueError:
            continue
    if not rows:
        raise ValueError("No candidate bin count could be fitted.")
    table = pd.DataFrame(rows).sort_values("n_bins").reset_index(drop=True)
    best = int(table.loc[table["bic"].idxmin(), "n_bins"])
    return best, table


@dataclass
class BatteryArbitrageMDP:
    """Finite joint SOC-price MDP."""

    battery: BatterySpec
    price_representatives: np.ndarray
    price_transition: np.ndarray
    transition: np.ndarray
    reward: np.ndarray
    valid_actions: np.ndarray
    soc_levels: np.ndarray

    @property
    def n_price_bins(self) -> int:
        return int(len(self.price_representatives))

    @property
    def n_soc_levels(self) -> int:
        return int(len(self.soc_levels))

    @property
    def n_states(self) -> int:
        return self.n_soc_levels * self.n_price_bins

    @property
    def n_actions(self) -> int:
        return len(Action)

    def state_index(self, soc_index: int, price_bin: int) -> int:
        return int(soc_index * self.n_price_bins + price_bin)

    def decode_state(self, state: int) -> tuple[int, int]:
        return divmod(int(state), self.n_price_bins)

    @classmethod
    def build(
        cls,
        battery: BatterySpec,
        price_representatives: Sequence[float],
        price_transition: np.ndarray,
    ) -> "BatteryArbitrageMDP":
        representatives = np.asarray(price_representatives, dtype=float)
        price_transition = np.asarray(price_transition, dtype=float)
        k = len(representatives)
        if price_transition.shape != (k, k):
            raise ValueError("Price transition shape must be (n_bins, n_bins).")
        if np.any(price_transition < 0) or not np.allclose(
            price_transition.sum(axis=1), 1.0, atol=1e-12
        ):
            raise ValueError("Price transition matrix must be row-stochastic.")

        soc_levels = battery.soc_levels
        n_states = len(soc_levels) * k
        n_actions = len(Action)
        transition = np.zeros((n_states, n_actions, n_states), dtype=float)
        reward = np.full((n_states, n_actions), -np.inf, dtype=float)
        valid = np.zeros((n_states, n_actions), dtype=bool)

        for soc_i, soc in enumerate(soc_levels):
            for price_i, representative in enumerate(representatives):
                state = soc_i * k + price_i
                for action in Action:
                    delta = battery.soc_delta(action)
                    next_soc = soc + delta
                    feasible = -1e-10 <= next_soc <= battery.capacity_mwh + 1e-10
                    if not feasible:
                        transition[state, int(action), state] = 1.0
                        continue
                    next_soc_i = int(round(next_soc / battery.energy_step_mwh))
                    next_states = next_soc_i * k + np.arange(k)
                    transition[state, int(action), next_states] = price_transition[
                        price_i
                    ]
                    reward[state, int(action)] = battery.realized_reward(
                        representative, action
                    )
                    valid[state, int(action)] = True

        mdp = cls(
            battery=battery,
            price_representatives=representatives,
            price_transition=price_transition,
            transition=transition,
            reward=reward,
            valid_actions=valid,
            soc_levels=soc_levels,
        )
        mdp.validate()
        return mdp

    def validate(self) -> None:
        if self.transition.shape != (self.n_states, self.n_actions, self.n_states):
            raise AssertionError("Joint transition tensor has an invalid shape.")
        if self.reward.shape != (self.n_states, self.n_actions):
            raise AssertionError("Reward matrix has an invalid shape.")
        if not np.all(self.valid_actions[:, int(Action.IDLE)]):
            raise AssertionError("Idle must be feasible in every state.")
        rows = self.transition[self.valid_actions]
        if np.any(rows < -1e-14) or not np.allclose(rows.sum(axis=1), 1.0, atol=1e-12):
            raise AssertionError("Valid joint transition rows must sum to one.")
        if not np.all(np.isfinite(self.reward[self.valid_actions])):
            raise AssertionError("Valid rewards must be finite.")
        for price_i in range(self.n_price_bins):
            empty = self.state_index(0, price_i)
            full = self.state_index(self.n_soc_levels - 1, price_i)
            if self.valid_actions[empty, int(Action.DISCHARGE)]:
                raise AssertionError("Discharge cannot be feasible at empty SOC.")
            if self.valid_actions[full, int(Action.CHARGE)]:
                raise AssertionError("Charge cannot be feasible at full SOC.")


@dataclass
class SolverResult:
    values: np.ndarray
    policy: np.ndarray
    iterations: int
    converged: bool
    runtime_seconds: float
    log: pd.DataFrame


def bellman_q(mdp: BatteryArbitrageMDP, values: np.ndarray, gamma: float) -> np.ndarray:
    continuation = np.einsum("sak,k->sa", mdp.transition, values, optimize=True)
    q_values = mdp.reward + gamma * continuation
    q_values[~mdp.valid_actions] = -np.inf
    return q_values


def value_iteration(
    mdp: BatteryArbitrageMDP, config: SolverConfig = SolverConfig()
) -> SolverResult:
    start = time.perf_counter()
    values = np.zeros(mdp.n_states, dtype=float)
    records: list[dict[str, float | int]] = []
    converged = False

    for iteration in range(1, config.max_iterations + 1):
        q_values = bellman_q(mdp, values, config.gamma)
        updated = np.max(q_values, axis=1)
        residual = float(np.max(np.abs(updated - values)))
        records.append({"iteration": iteration, "bellman_residual": residual})
        values = updated
        if residual <= config.tolerance:
            converged = True
            break

    policy = np.argmax(bellman_q(mdp, values, config.gamma), axis=1).astype(int)
    runtime = time.perf_counter() - start
    return SolverResult(
        values=values,
        policy=policy,
        iterations=iteration,
        converged=converged,
        runtime_seconds=runtime,
        log=pd.DataFrame(records),
    )


def evaluate_policy_exact(
    mdp: BatteryArbitrageMDP, policy: np.ndarray, gamma: float
) -> np.ndarray:
    states = np.arange(mdp.n_states)
    policy = np.asarray(policy, dtype=int)
    if policy.shape != (mdp.n_states,):
        raise ValueError("Policy must contain one action per state.")
    if np.any(~mdp.valid_actions[states, policy]):
        raise ValueError("Policy contains an infeasible action.")
    p_policy = mdp.transition[states, policy, :]
    r_policy = mdp.reward[states, policy]
    return np.linalg.solve(np.eye(mdp.n_states) - gamma * p_policy, r_policy)


def policy_iteration(
    mdp: BatteryArbitrageMDP, config: SolverConfig = SolverConfig()
) -> SolverResult:
    start = time.perf_counter()
    policy = np.full(mdp.n_states, int(Action.IDLE), dtype=int)
    records: list[dict[str, float | int]] = []
    converged = False

    for iteration in range(1, config.max_iterations + 1):
        values = evaluate_policy_exact(mdp, policy, config.gamma)
        q_values = bellman_q(mdp, values, config.gamma)
        improved = np.argmax(q_values, axis=1).astype(int)
        changes = int(np.count_nonzero(improved != policy))
        residual = float(np.max(np.abs(np.max(q_values, axis=1) - values)))
        records.append(
            {
                "iteration": iteration,
                "policy_changes": changes,
                "bellman_residual": residual,
            }
        )
        policy = improved
        if changes == 0:
            converged = True
            break

    values = evaluate_policy_exact(mdp, policy, config.gamma)
    runtime = time.perf_counter() - start
    return SolverResult(
        values=values,
        policy=policy,
        iterations=iteration,
        converged=converged,
        runtime_seconds=runtime,
        log=pd.DataFrame(records),
    )


def policy_bellman_residual(
    mdp: BatteryArbitrageMDP,
    values: np.ndarray,
    gamma: float,
) -> float:
    return float(np.max(np.abs(np.max(bellman_q(mdp, values, gamma), axis=1) - values)))


def nearest_soc_index(mdp: BatteryArbitrageMDP, initial_soc_mwh: float) -> int:
    distances = np.abs(mdp.soc_levels - initial_soc_mwh)
    index = int(np.argmin(distances))
    if not math.isclose(mdp.soc_levels[index], initial_soc_mwh, abs_tol=1e-9):
        raise ValueError(
            f"Initial SOC must be on the grid {mdp.soc_levels.tolist()}; "
            f"received {initial_soc_mwh}."
        )
    return index


def simulate_policy(
    prices: Sequence[float],
    timestamps: Sequence[object],
    discretizer: PriceDiscretizer,
    mdp: BatteryArbitrageMDP,
    policy: np.ndarray,
    initial_soc_mwh: float,
) -> pd.DataFrame:
    x = _clean_prices(prices)
    if len(timestamps) != len(x):
        raise ValueError("Timestamp and price arrays must have equal length.")
    bins = discretizer.transform(x)
    soc_i = nearest_soc_index(mdp, initial_soc_mwh)
    rows: list[dict[str, object]] = []
    cumulative = 0.0

    for t, (timestamp, price, price_bin) in enumerate(zip(timestamps, x, bins)):
        state = mdp.state_index(soc_i, int(price_bin))
        action = int(policy[state])
        if not mdp.valid_actions[state, action]:
            raise AssertionError("The learned policy selected an infeasible action.")
        soc_before = float(mdp.soc_levels[soc_i])
        reward = mdp.battery.realized_reward(float(price), action)
        next_soc = soc_before + mdp.battery.soc_delta(action)
        soc_i = int(round(next_soc / mdp.battery.energy_step_mwh))
        cumulative += reward
        rows.append(
            {
                "step": t,
                "timestamp": timestamp,
                "price": float(price),
                "price_bin": int(price_bin),
                "soc_before_mwh": soc_before,
                "action": ACTION_NAMES[action],
                "soc_after_mwh": float(next_soc),
                "profit": float(reward),
                "cumulative_profit": float(cumulative),
            }
        )
    return pd.DataFrame(rows)


def perfect_foresight_dispatch(
    prices: Sequence[float],
    timestamps: Sequence[object],
    battery: BatterySpec,
    initial_soc_mwh: float,
    terminal_salvage_price: float,
) -> pd.DataFrame:
    """Finite-horizon clairvoyant benchmark solved by backward induction."""

    x = _clean_prices(prices)
    if len(timestamps) != len(x):
        raise ValueError("Timestamp and price arrays must have equal length.")
    soc_levels = battery.soc_levels
    n_soc = len(soc_levels)
    horizon = len(x)
    terminal_values = terminal_salvage_price * battery.discharge_efficiency * soc_levels
    values_next = terminal_values.copy()
    decisions = np.full((horizon, n_soc), int(Action.IDLE), dtype=int)

    for t in range(horizon - 1, -1, -1):
        values = np.full(n_soc, -np.inf, dtype=float)
        for soc_i, soc in enumerate(soc_levels):
            best_value = -np.inf
            best_action = int(Action.IDLE)
            for action in Action:
                next_soc = soc + battery.soc_delta(action)
                if not (-1e-10 <= next_soc <= battery.capacity_mwh + 1e-10):
                    continue
                next_i = int(round(next_soc / battery.energy_step_mwh))
                candidate = battery.realized_reward(float(x[t]), action) + values_next[next_i]
                if candidate > best_value + 1e-12:
                    best_value = candidate
                    best_action = int(action)
            values[soc_i] = best_value
            decisions[t, soc_i] = best_action
        values_next = values

    initial_i = int(np.where(np.isclose(soc_levels, initial_soc_mwh))[0][0])
    soc_i = initial_i
    cumulative = 0.0
    rows: list[dict[str, object]] = []
    for t, (timestamp, price) in enumerate(zip(timestamps, x)):
        action = int(decisions[t, soc_i])
        soc_before = float(soc_levels[soc_i])
        reward = battery.realized_reward(float(price), action)
        next_soc = soc_before + battery.soc_delta(action)
        soc_i = int(round(next_soc / battery.energy_step_mwh))
        cumulative += reward
        rows.append(
            {
                "step": t,
                "timestamp": timestamp,
                "price": float(price),
                "soc_before_mwh": soc_before,
                "action": ACTION_NAMES[action],
                "soc_after_mwh": float(next_soc),
                "profit": float(reward),
                "cumulative_profit": float(cumulative),
            }
        )
    return pd.DataFrame(rows)


def trajectory_metrics(
    learned: pd.DataFrame,
    perfect: pd.DataFrame,
    battery: BatterySpec,
    initial_soc_mwh: float,
    terminal_salvage_price: float,
) -> dict[str, float | int]:
    learned_profit = float(learned["profit"].sum())
    perfect_profit = float(perfect["profit"].sum())
    learned_end = float(learned["soc_after_mwh"].iloc[-1])
    perfect_end = float(perfect["soc_after_mwh"].iloc[-1])
    eta_d = battery.discharge_efficiency
    learned_adjusted = learned_profit + terminal_salvage_price * eta_d * (
        learned_end - initial_soc_mwh
    )
    perfect_adjusted = perfect_profit + terminal_salvage_price * eta_d * (
        perfect_end - initial_soc_mwh
    )
    efficiency = (
        100.0 * learned_adjusted / perfect_adjusted
        if perfect_adjusted > 1e-12
        else float("nan")
    )

    cumulative = np.concatenate(([0.0], learned["cumulative_profit"].to_numpy()))
    running_peak = np.maximum.accumulate(cumulative)
    max_drawdown = float(np.max(running_peak - cumulative))
    throughput = float(
        np.abs(
            learned["soc_after_mwh"].to_numpy()
            - learned["soc_before_mwh"].to_numpy()
        ).sum()
    )
    action_counts = learned["action"].value_counts()
    dates = pd.to_datetime(learned["timestamp"], utc=True).dt.floor("D")
    daily_profit = learned.groupby(dates, sort=True)["profit"].sum().to_numpy()
    # Circular seven-day moving-block bootstrap preserves short weekly
    # dependence better than independently resampling individual days.
    rng = np.random.default_rng(0)
    block_length = min(7, len(daily_profit))
    n_blocks = int(math.ceil(len(daily_profit) / block_length))
    bootstrap_means = np.empty(2_000, dtype=float)
    offsets = np.arange(block_length)
    for b in range(len(bootstrap_means)):
        starts = rng.integers(0, len(daily_profit), size=n_blocks)
        indices = (starts[:, None] + offsets[None, :]) % len(daily_profit)
        bootstrap_means[b] = daily_profit[indices.reshape(-1)[: len(daily_profit)]].mean()
    return {
        "test_hours": int(len(learned)),
        "cumulative_profit": learned_profit,
        "terminal_soc_mwh": learned_end,
        "inventory_adjusted_profit": float(learned_adjusted),
        "perfect_foresight_profit": perfect_profit,
        "perfect_foresight_terminal_soc_mwh": perfect_end,
        "perfect_foresight_inventory_adjusted_profit": float(perfect_adjusted),
        "arbitrage_efficiency_percent": float(efficiency),
        "max_drawdown": max_drawdown,
        "equivalent_full_cycles": throughput / (2.0 * battery.capacity_mwh),
        "mean_hourly_profit": float(learned["profit"].mean()),
        "hourly_profit_standard_deviation": float(learned["profit"].std(ddof=1)),
        "mean_daily_profit": float(np.mean(daily_profit)),
        "median_daily_profit": float(np.median(daily_profit)),
        "daily_profit_standard_deviation": float(np.std(daily_profit, ddof=1)),
        "daily_profit_p05": float(np.quantile(daily_profit, 0.05)),
        "daily_profit_p95": float(np.quantile(daily_profit, 0.95)),
        "profitable_days_fraction": float(np.mean(daily_profit > 0.0)),
        "bootstrap_replications": int(len(bootstrap_means)),
        "bootstrap_block_days": int(block_length),
        "mean_daily_profit_weekly_block_bootstrap_ci95_lower": float(
            np.quantile(bootstrap_means, 0.025)
        ),
        "mean_daily_profit_weekly_block_bootstrap_ci95_upper": float(
            np.quantile(bootstrap_means, 0.975)
        ),
        "annualized_inventory_adjusted_profit": float(
            learned_adjusted * 8_760.0 / len(learned)
        ),
        "charge_hours": int(action_counts.get("Charge", 0)),
        "discharge_hours": int(action_counts.get("Discharge", 0)),
        "idle_hours": int(action_counts.get("Idle", 0)),
    }


def generate_synthetic_prices(
    hours: int = 17_520, seed: int = 42
) -> pd.DataFrame:
    """Create a reproducible hourly series with seasonality and price regimes."""

    if hours < 500:
        raise ValueError("Synthetic benchmark requires at least 500 hours.")
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2023-01-01", periods=hours, freq="h", tz="UTC")
    hour = np.arange(hours)
    hour_of_day = timestamps.hour.to_numpy()
    day_of_week = timestamps.dayofweek.to_numpy()

    daily = 17.0 * np.sin(2.0 * np.pi * (hour_of_day - 8.0) / 24.0)
    second_harmonic = 5.0 * np.sin(4.0 * np.pi * (hour_of_day - 15.0) / 24.0)
    annual = 9.0 * np.cos(2.0 * np.pi * hour / (24.0 * 365.25))
    weekend = np.where(day_of_week >= 5, -7.0, 0.0)

    regime_transition = np.array(
        [[0.986, 0.008, 0.006], [0.15, 0.84, 0.01], [0.13, 0.01, 0.86]]
    )
    regimes = np.zeros(hours, dtype=int)
    for t in range(1, hours):
        regimes[t] = int(rng.choice(3, p=regime_transition[regimes[t - 1]]))
    regime_shift = np.array([0.0, 85.0, -55.0])[regimes]
    regime_noise = np.array([4.5, 18.0, 10.0])[regimes] * rng.normal(size=hours)

    ar_noise = np.zeros(hours, dtype=float)
    innovations = rng.normal(0.0, 5.5, size=hours)
    for t in range(1, hours):
        ar_noise[t] = 0.82 * ar_noise[t - 1] + innovations[t]
    prices = 52.0 + daily + second_harmonic + annual + weekend + regime_shift
    prices += ar_noise + regime_noise
    prices = np.clip(prices, -120.0, 450.0)
    return pd.DataFrame({"timestamp": timestamps, "price": prices})


def load_price_data(
    csv_path: str | None,
    price_column: str,
    timestamp_column: str | None,
    synthetic_hours: int,
    seed: int,
) -> tuple[pd.DataFrame, str]:
    if csv_path is None:
        return generate_synthetic_prices(synthetic_hours, seed), "synthetic"
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    if price_column not in frame.columns:
        raise ValueError(
            f"Price column '{price_column}' was not found. Available: {frame.columns.tolist()}"
        )
    prices = pd.to_numeric(frame[price_column], errors="coerce")
    if timestamp_column:
        if timestamp_column not in frame.columns:
            raise ValueError(f"Timestamp column '{timestamp_column}' was not found.")
        timestamps = pd.to_datetime(frame[timestamp_column], errors="coerce", utc=True)
    else:
        timestamps = pd.date_range("2000-01-01", periods=len(frame), freq="h", tz="UTC")
    clean = pd.DataFrame({"timestamp": timestamps, "price": prices}).dropna()
    clean = clean.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    if len(clean) < 200:
        raise ValueError("At least 200 valid hourly observations are required.")
    return clean.reset_index(drop=True), str(path.resolve())


def make_policy_table(
    mdp: BatteryArbitrageMDP,
    policy: np.ndarray,
    discretizer: PriceDiscretizer,
    train_prices: Sequence[float],
) -> pd.DataFrame:
    labels = discretizer.interval_labels(train_prices)
    rows = []
    for soc_i, soc in enumerate(mdp.soc_levels):
        for price_i, label in enumerate(labels):
            state = mdp.state_index(soc_i, price_i)
            action = int(policy[state])
            rows.append(
                {
                    "soc_mwh": float(soc),
                    "price_bin": price_i,
                    "price_interval": label,
                    "representative_price": float(mdp.price_representatives[price_i]),
                    "action": ACTION_NAMES[action],
                }
            )
    return pd.DataFrame(rows)


def save_figures(
    output_dir: Path,
    train: pd.DataFrame,
    test: pd.DataFrame,
    mdp: BatteryArbitrageMDP,
    discretizer: PriceDiscretizer,
    vi: SolverResult,
    pi: SolverResult,
    learned: pd.DataFrame,
    perfect: pd.DataFrame,
) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.2))
    axes[0].semilogy(
        vi.log["iteration"],
        np.maximum(vi.log["bellman_residual"], 1e-16),
        color="#176B87",
        linewidth=1.7,
    )
    axes[0].set(title="Value iteration", xlabel="Iteration", ylabel="Bellman residual")
    axes[0].grid(alpha=0.2)
    axes[1].plot(
        pi.log["iteration"],
        pi.log["policy_changes"],
        marker="o",
        color="#B35C1E",
        linewidth=1.7,
    )
    axes[1].set(title="Policy iteration", xlabel="Improvement step", ylabel="States changed")
    axes[1].set_xticks(pi.log["iteration"].astype(int))
    axes[1].grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_dir / "convergence.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    policy_matrix = vi.policy.reshape(mdp.n_soc_levels, mdp.n_price_bins)
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    cmap = matplotlib.colors.ListedColormap(["#3B82C4", "#D9D9D9", "#E67E22"])
    image = ax.imshow(policy_matrix, aspect="auto", origin="lower", cmap=cmap, vmin=0, vmax=2)
    ax.set_xticks(np.arange(mdp.n_price_bins))
    ax.set_xticklabels([f"B{k + 1}\n{p:.1f}" for k, p in enumerate(mdp.price_representatives)])
    ax.set_yticks(np.arange(mdp.n_soc_levels))
    ax.set_yticklabels([f"{soc:.0f}" for soc in mdp.soc_levels])
    ax.set(xlabel="Price bin and representative price", ylabel="SOC (MWh)", title="Optimal stationary policy")
    for soc_i in range(mdp.n_soc_levels):
        for price_i in range(mdp.n_price_bins):
            action = policy_matrix[soc_i, price_i]
            ax.text(price_i, soc_i, ACTION_NAMES[action][0], ha="center", va="center", fontsize=8)
    colorbar = fig.colorbar(image, ax=ax, ticks=[0, 1, 2], fraction=0.045, pad=0.04)
    colorbar.ax.set_yticklabels(["Charge", "Idle", "Discharge"])
    fig.tight_layout()
    fig.savefig(output_dir / "optimal_policy.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(9.2, 5.0), sharex=True)
    axes[0].plot(
        learned["step"], learned["cumulative_profit"], label="VoltRL", color="#176B87"
    )
    axes[0].plot(
        perfect["step"],
        perfect["cumulative_profit"],
        label="Perfect foresight",
        color="#B35C1E",
        alpha=0.85,
    )
    axes[0].set(ylabel="Cumulative profit", title="Unseen-test performance")
    axes[0].legend(frameon=False, ncol=2)
    axes[0].grid(alpha=0.2)
    axes[1].plot(learned["step"], learned["soc_after_mwh"], color="#176B87", linewidth=0.8)
    axes[1].set(xlabel="Test hour", ylabel="SOC (MWh)")
    axes[1].set_ylim(-10, mdp.battery.capacity_mwh + 10)
    axes[1].grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_dir / "test_performance.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    sample = pd.concat(
        [train.tail(min(24 * 21, len(train))), test.head(min(24 * 21, len(test)))]
    )
    fig, ax = plt.subplots(figsize=(9.2, 2.8))
    ax.plot(np.arange(len(sample)), sample["price"], color="#176B87", linewidth=0.7)
    ax.axvline(min(24 * 21, len(train)), color="#B35C1E", linestyle="--", linewidth=1.0)
    ax.set(title="Chronological train/test boundary (six-week window)", xlabel="Hour", ylabel="Price")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_dir / "price_series_split.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _json_value(value: object) -> object:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    return value


def run_experiment(args: argparse.Namespace) -> dict[str, object]:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frame, data_source = load_price_data(
        args.csv,
        args.price_column,
        args.timestamp_column,
        args.synthetic_hours,
        args.seed,
    )
    split = int(len(frame) * args.train_fraction)
    if split < 100 or len(frame) - split < 100:
        raise ValueError("Chronological split must leave at least 100 hours in each set.")
    train = frame.iloc[:split].reset_index(drop=True)
    test = frame.iloc[split:].reset_index(drop=True)

    if args.bins == "auto":
        candidates = [int(x) for x in args.candidate_bins.split(",") if x.strip()]
        n_bins, bic_table = select_bin_count_bic(
            train["price"].to_numpy(),
            candidates=candidates,
            validation_fraction=args.bin_validation_fraction,
            prior_strength=args.prior_strength,
        )
    else:
        n_bins = int(args.bins)
        bic_table = pd.DataFrame()
    discretizer = PriceDiscretizer.fit(train["price"].to_numpy(), n_bins)
    train_bins = discretizer.transform(train["price"].to_numpy())
    price_transition, transition_counts = estimate_price_transition(
        train_bins, n_bins, prior_strength=args.prior_strength
    )

    battery = BatterySpec(
        capacity_mwh=args.capacity_mwh,
        max_power_mw=args.max_power_mw,
        interval_hours=1.0,
        charge_efficiency=args.charge_efficiency,
        discharge_efficiency=args.discharge_efficiency,
        degradation_cost_per_mwh=args.degradation_cost,
    )
    mdp = BatteryArbitrageMDP.build(
        battery, discretizer.representatives, price_transition
    )
    config = SolverConfig(
        gamma=args.gamma,
        tolerance=args.tolerance,
        max_iterations=args.max_iterations,
    )
    vi = value_iteration(mdp, config)
    pi = policy_iteration(mdp, config)
    if not vi.converged or not pi.converged:
        raise RuntimeError("One or both dynamic-programming solvers did not converge.")

    salvage_price = (
        float(np.median(train["price"]))
        if args.salvage_price is None
        else float(args.salvage_price)
    )
    learned = simulate_policy(
        test["price"].to_numpy(),
        test["timestamp"].astype(str).to_numpy(),
        discretizer,
        mdp,
        vi.policy,
        args.initial_soc_mwh,
    )
    perfect = perfect_foresight_dispatch(
        test["price"].to_numpy(),
        test["timestamp"].astype(str).to_numpy(),
        battery,
        args.initial_soc_mwh,
        salvage_price,
    )
    metrics = trajectory_metrics(
        learned,
        perfect,
        battery,
        args.initial_soc_mwh,
        salvage_price,
    )

    exact_pi_residual = policy_bellman_residual(mdp, pi.values, args.gamma)
    max_value_difference = float(np.max(np.abs(vi.values - pi.values)))
    policy_agreement = float(np.mean(vi.policy == pi.policy))
    results: dict[str, object] = {
        "project": "Project VoltRL: Battery Arbitrage Engine",
        "data_source": data_source,
        "observations": int(len(frame)),
        "train_hours": int(len(train)),
        "test_hours": int(len(test)),
        "train_fraction": float(args.train_fraction),
        "selected_price_bins": int(n_bins),
        "price_representatives": discretizer.representatives.tolist(),
        "price_edges_observed": [
            float(train["price"].min()),
            *[float(x) for x in discretizer.edges[1:-1]],
            float(train["price"].max()),
        ],
        "terminal_salvage_price": salvage_price,
        "battery": asdict(battery),
        "solver": asdict(config),
        "value_iteration": {
            "iterations": vi.iterations,
            "runtime_seconds": vi.runtime_seconds,
            "final_bellman_residual": float(vi.log["bellman_residual"].iloc[-1]),
        },
        "policy_iteration": {
            "iterations": pi.iterations,
            "runtime_seconds": pi.runtime_seconds,
            "final_bellman_residual": exact_pi_residual,
        },
        "solver_max_value_difference": max_value_difference,
        "solver_policy_agreement_fraction": policy_agreement,
        "evaluation": metrics,
    }

    train.assign(price_bin=train_bins).to_csv(output_dir / "training_prices.csv", index=False)
    test.to_csv(output_dir / "test_prices.csv", index=False)
    if not bic_table.empty:
        bic_table.to_csv(output_dir / "bin_selection_bic.csv", index=False)
    pd.DataFrame(price_transition).to_csv(
        output_dir / "price_transition_matrix.csv", index_label="from_bin"
    )
    pd.DataFrame(transition_counts).to_csv(
        output_dir / "price_transition_counts.csv", index_label="from_bin"
    )
    bin_labels = discretizer.interval_labels(train["price"].to_numpy())
    bin_rows = []
    finite_edges = discretizer.edges.copy()
    finite_edges[0] = float(train["price"].min())
    finite_edges[-1] = float(train["price"].max())
    for k in range(n_bins):
        bin_rows.append(
            {
                "price_bin": k,
                "interval": bin_labels[k],
                "lower_observed_bound": finite_edges[k],
                "upper_observed_bound": finite_edges[k + 1],
                "representative_price": discretizer.representatives[k],
                "training_count": discretizer.counts[k],
            }
        )
    pd.DataFrame(bin_rows).to_csv(output_dir / "price_bins.csv", index=False)
    make_policy_table(mdp, vi.policy, discretizer, train["price"]).to_csv(
        output_dir / "optimal_policy.csv", index=False
    )
    vi.log.to_csv(output_dir / "value_iteration_log.csv", index=False)
    pi.log.to_csv(output_dir / "policy_iteration_log.csv", index=False)
    learned.to_csv(output_dir / "test_trajectory_voltrl.csv", index=False)
    perfect.to_csv(output_dir / "test_trajectory_perfect_foresight.csv", index=False)
    np.savez_compressed(
        output_dir / "mdp_arrays.npz",
        transition=mdp.transition,
        reward=mdp.reward,
        valid_actions=mdp.valid_actions,
        price_transition=price_transition,
        value_iteration_values=vi.values,
        value_iteration_policy=vi.policy,
        policy_iteration_values=pi.values,
        policy_iteration_policy=pi.policy,
    )
    save_figures(output_dir, train, test, mdp, discretizer, vi, pi, learned, perfect)

    with (output_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_value, allow_nan=False)
    LOGGER.info("Results written to %s", output_dir)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train and evaluate the Project VoltRL battery arbitrage MDP."
    )
    parser.add_argument("--csv", help="Optional CSV containing chronological hourly prices.")
    parser.add_argument("--price-column", default="price")
    parser.add_argument("--timestamp-column")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--synthetic-hours", type=int, default=17_520)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument(
        "--bins", default="auto", help="Integer bin count or 'auto' for BIC selection."
    )
    parser.add_argument("--candidate-bins", default="4,5,6,7,8,9,10,11,12,13,14,15,16")
    parser.add_argument("--bin-validation-fraction", type=float, default=0.20)
    parser.add_argument("--prior-strength", type=float, default=1.0)
    parser.add_argument("--capacity-mwh", type=float, default=500.0)
    parser.add_argument("--max-power-mw", type=float, default=100.0)
    parser.add_argument("--charge-efficiency", type=float, default=1.0)
    parser.add_argument("--discharge-efficiency", type=float, default=1.0)
    parser.add_argument("--degradation-cost", type=float, default=0.0)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--tolerance", type=float, default=1e-8)
    parser.add_argument("--max-iterations", type=int, default=100_000)
    parser.add_argument("--initial-soc-mwh", type=float, default=200.0)
    parser.add_argument(
        "--salvage-price",
        type=float,
        help="Terminal inventory valuation; defaults to the training median price.",
    )
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )
    if not 0.05 < args.train_fraction < 0.95:
        parser.error("--train-fraction must lie in (0.05, 0.95).")
    try:
        results = run_experiment(args)
    except Exception as exc:  # pragma: no cover - CLI error reporting
        LOGGER.exception("VoltRL failed: %s", exc)
        return 1
    print(json.dumps(results, indent=2, default=_json_value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
