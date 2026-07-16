"""Audit-ready VoltRL benchmark experiments.

This module revises the original illustrative VoltRL experiment into a
chronologically evaluated benchmark.  It provides leakage-free expanding-
window model selection, continuous predictive scoring with full-support
Gaussian-mixture emissions, price-only and hour-aware finite-horizon MDPs,
implementable baselines, multi-seed uncertainty, two historical-market pilots,
and prespecified sensitivity analyses.

The day-ahead market series are treated as sequentially revealed benchmark
signals.  The experiment is not a market-bidding or deployment study.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from voltrl import (
    ACTION_NAMES,
    Action,
    BatteryArbitrageMDP,
    BatterySpec,
    PriceDiscretizer,
    SolverConfig,
    estimate_price_transition,
    generate_synthetic_prices,
    perfect_foresight_dispatch,
    policy_bellman_residual,
    policy_iteration,
    value_iteration,
)


POLICY_HOUR = "Hour-aware finite-horizon MDP"
POLICY_PRICE = "Price-only finite-horizon MDP"
POLICY_MPC = "Seasonal 24-hour MPC"
POLICY_THRESHOLD = "Training-quantile threshold"
POLICY_IDLE = "Idle"
POLICY_ORACLE = "Perfect-foresight upper bound"
REPOSITORY_URL = "https://github.com/mohammadrezwankhan/voltrl"
ACTION_TIE_ORDER = np.array(
    [int(Action.IDLE), int(Action.CHARGE), int(Action.DISCHARGE)], dtype=int
)


@dataclass
class StateModel:
    """Discretized exogenous-state model with full-support emissions."""

    discretizer: PriceDiscretizer
    transition: np.ndarray
    emission_mean: np.ndarray
    emission_std: np.ndarray
    calendar_aware: bool
    transition_counts: np.ndarray

    @property
    def n_bins(self) -> int:
        return self.discretizer.n_bins


def _validated_frame(
    frame: pd.DataFrame, min_observations: int = 500
) -> pd.DataFrame:
    required = {"timestamp", "price"}
    if not required.issubset(frame.columns):
        raise ValueError("Frame must contain timestamp and price columns.")
    clean = frame.loc[:, ["timestamp", "price"]].copy()
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], utc=True, errors="coerce")
    clean["price"] = pd.to_numeric(clean["price"], errors="coerce")
    clean = clean.dropna().sort_values("timestamp").drop_duplicates("timestamp")
    if len(clean) < min_observations:
        raise ValueError(
            f"At least {min_observations} consecutive hourly observations are required."
        )
    deltas = clean["timestamp"].diff().dropna()
    if not bool((deltas == pd.Timedelta(hours=1)).all()):
        raise ValueError("The benchmark frame must be a consecutive hourly series.")
    if not np.isfinite(clean["price"].to_numpy(dtype=float)).all():
        raise ValueError("Prices must be finite.")
    return clean.reset_index(drop=True)


def chronological_split(
    frame: pd.DataFrame, train_fraction: float = 0.70
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split once in chronological order; no test value enters model fitting."""

    clean = _validated_frame(frame)
    if not 0.5 <= train_fraction <= 0.9:
        raise ValueError("train_fraction must lie in [0.5, 0.9].")
    split = int(math.floor(len(clean) * train_fraction))
    return clean.iloc[:split].copy(), clean.iloc[split:].copy()


def _emission_parameters(
    prices: np.ndarray, labels: np.ndarray, n_bins: int
) -> tuple[np.ndarray, np.ndarray]:
    pooled = float(np.std(prices, ddof=1))
    floor = max(0.50, 0.05 * pooled)
    means = np.empty(n_bins, dtype=float)
    stds = np.empty(n_bins, dtype=float)
    for j in range(n_bins):
        values = prices[labels == j]
        means[j] = float(np.mean(values))
        within = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        stds[j] = max(floor, within)
    return means, stds


def fit_state_model(
    frame: pd.DataFrame,
    n_bins: int,
    calendar_aware: bool,
    prior_strength: float = 1.0,
) -> StateModel:
    """Fit a price-only or hour-conditioned transition kernel.

    A unit-strength empirical-marginal Dirichlet prior prevents zero rows.  In
    the calendar-aware model, T[h, i, j] predicts the next price bin from the
    current UTC hour and current price bin; the next hour is deterministic.
    """

    clean = _validated_frame(frame)
    prices = clean["price"].to_numpy(dtype=float)
    discretizer = PriceDiscretizer.fit(prices, n_bins)
    labels = discretizer.transform(prices)
    means, stds = _emission_parameters(prices, labels, n_bins)
    marginal = np.bincount(labels[1:], minlength=n_bins).astype(float) + 1.0
    marginal /= marginal.sum()

    if calendar_aware:
        counts = np.zeros((24, n_bins, n_bins), dtype=float)
        hours = clean["timestamp"].dt.hour.to_numpy(dtype=int)
        np.add.at(counts, (hours[:-1], labels[:-1], labels[1:]), 1.0)
        denominator = counts.sum(axis=2, keepdims=True) + prior_strength
        transition = (
            counts + prior_strength * marginal[None, None, :]
        ) / denominator
    else:
        counts = np.zeros((n_bins, n_bins), dtype=float)
        np.add.at(counts, (labels[:-1], labels[1:]), 1.0)
        denominator = counts.sum(axis=1, keepdims=True) + prior_strength
        transition = (counts + prior_strength * marginal[None, :]) / denominator

    if not np.allclose(transition.sum(axis=-1), 1.0, atol=1e-12):
        raise AssertionError("Fitted transitions must be row-stochastic.")
    return StateModel(
        discretizer=discretizer,
        transition=transition,
        emission_mean=means,
        emission_std=stds,
        calendar_aware=calendar_aware,
        transition_counts=counts,
    )


def continuous_predictive_nll(model: StateModel, frame: pd.DataFrame) -> float:
    """Mean next-price negative log density under a Gaussian mixture.

    Unlike the previous truncated-bin likelihood, every component has support
    over the real line, so tail observations remain valid and comparable across
    candidate bin counts.
    """

    clean = _validated_frame(frame, min_observations=20)
    prices = clean["price"].to_numpy(dtype=float)
    source = model.discretizer.transform(prices[:-1])
    destination_prices = prices[1:]
    if model.calendar_aware:
        hours = clean["timestamp"].dt.hour.to_numpy(dtype=int)[:-1]
        weights = model.transition[hours, source, :]
    else:
        weights = model.transition[source, :]

    residual = (
        destination_prices[:, None] - model.emission_mean[None, :]
    ) / model.emission_std[None, :]
    log_components = (
        np.log(np.maximum(weights, 1e-300))
        - np.log(model.emission_std[None, :])
        - 0.5 * math.log(2.0 * math.pi)
        - 0.5 * residual**2
    )
    maxima = np.max(log_components, axis=1)
    log_density = maxima + np.log(
        np.exp(log_components - maxima[:, None]).sum(axis=1)
    )
    return float(-np.mean(log_density))


def expanding_window_selection(
    frame: pd.DataFrame, candidates: Iterable[int]
) -> tuple[int, pd.DataFrame]:
    """Select K using three leakage-free expanding-window validation folds."""

    clean = _validated_frame(frame)
    candidate_list = sorted(set(int(k) for k in candidates))
    if not candidate_list or min(candidate_list) < 2:
        raise ValueError("Candidate bin counts must contain integers >= 2.")
    boundaries = np.floor(np.array([0.50, 2 / 3, 5 / 6, 1.0]) * len(clean)).astype(int)
    rows: list[dict[str, float | int | str]] = []
    for k in candidate_list:
        for fold in range(3):
            fit = clean.iloc[: boundaries[fold]].copy()
            valid = clean.iloc[boundaries[fold] : boundaries[fold + 1]].copy()
            for calendar_aware, label in ((False, "price_only"), (True, "hour_aware")):
                model = fit_state_model(fit, k, calendar_aware)
                rows.append(
                    {
                        "n_bins": k,
                        "fold": fold + 1,
                        "model": label,
                        "fit_hours": len(fit),
                        "validation_hours": len(valid),
                        "mean_nll": continuous_predictive_nll(model, valid),
                    }
                )
    table = pd.DataFrame(rows)
    hour_means = (
        table[table["model"] == "hour_aware"]
        .groupby("n_bins", as_index=False)["mean_nll"]
        .mean()
    )
    best = int(hour_means.loc[hour_means["mean_nll"].idxmin(), "n_bins"])
    return best, table


def _feasible_next_indices(battery: BatterySpec) -> np.ndarray:
    levels = battery.soc_levels
    result = np.full((len(levels), len(Action)), -1, dtype=int)
    for soc_i, soc in enumerate(levels):
        for action in Action:
            next_soc = soc + battery.soc_delta(action)
            if -1e-10 <= next_soc <= battery.capacity_mwh + 1e-10:
                result[soc_i, int(action)] = int(
                    round(next_soc / battery.energy_step_mwh)
                )
    return result


def finite_horizon_policy(
    model: StateModel,
    battery: BatterySpec,
    timestamps: Sequence[object],
    terminal_salvage_price: float,
    planner_discount: float = 1.0,
) -> np.ndarray:
    """Solve the test-length finite-horizon MDP by backward induction.

    The primary experiment uses planner_discount=1, exactly matching the
    undiscounted evaluation objective and terminal inventory valuation.
    Decisions have shape (time, SOC level, price bin) and depend only on the
    fitted model, current state, known calendar hour, and remaining horizon.
    """

    if not 0 < planner_discount <= 1:
        raise ValueError("planner_discount must lie in (0, 1].")
    time_index = pd.to_datetime(pd.Series(timestamps), utc=True, errors="raise")
    hours = time_index.dt.hour.to_numpy(dtype=int)
    horizon = len(hours)
    if horizon < 1:
        raise ValueError("A nonempty horizon is required.")
    n_soc = len(battery.soc_levels)
    k = model.n_bins
    next_soc = _feasible_next_indices(battery)
    rewards = np.array(
        [
            [battery.realized_reward(price, action) for price in model.emission_mean]
            for action in Action
        ],
        dtype=float,
    )
    decisions = np.empty((horizon, n_soc, k), dtype=np.int8)

    if model.calendar_aware:
        values_next = np.broadcast_to(
            (
                terminal_salvage_price
                * battery.discharge_efficiency
                * battery.soc_levels[:, None, None]
            ),
            (n_soc, 24, k),
        ).copy()
        next_hours = (np.arange(24) + 1) % 24
        for t in range(horizon - 1, -1, -1):
            following = values_next[:, next_hours, :]
            continuation = np.einsum(
                "hij,shj->shi", model.transition, following, optimize=True
            )
            q_order = np.full((n_soc, 24, k, len(Action)), -np.inf, dtype=float)
            for pos, action in enumerate(ACTION_TIE_ORDER):
                for soc_i in range(n_soc):
                    dest_soc = next_soc[soc_i, action]
                    if dest_soc >= 0:
                        q_order[soc_i, :, :, pos] = (
                            rewards[action][None, :]
                            + planner_discount * continuation[dest_soc]
                        )
            best_position = np.argmax(q_order, axis=3)
            actions = ACTION_TIE_ORDER[best_position]
            decisions[t] = actions[:, hours[t], :]
            values_next = np.take_along_axis(
                q_order, best_position[:, :, :, None], axis=3
            )[:, :, :, 0]
    else:
        values_next = np.broadcast_to(
            (
                terminal_salvage_price
                * battery.discharge_efficiency
                * battery.soc_levels[:, None]
            ),
            (n_soc, k),
        ).copy()
        for t in range(horizon - 1, -1, -1):
            continuation = values_next @ model.transition.T
            q_order = np.full((n_soc, k, len(Action)), -np.inf, dtype=float)
            for pos, action in enumerate(ACTION_TIE_ORDER):
                for soc_i in range(n_soc):
                    dest_soc = next_soc[soc_i, action]
                    if dest_soc >= 0:
                        q_order[soc_i, :, pos] = (
                            rewards[action]
                            + planner_discount * continuation[dest_soc]
                        )
            best_position = np.argmax(q_order, axis=2)
            decisions[t] = ACTION_TIE_ORDER[best_position]
            values_next = np.take_along_axis(
                q_order, best_position[:, :, None], axis=2
            )[:, :, 0]
    return decisions


def trajectory_from_actions(
    frame: pd.DataFrame,
    actions: Sequence[int],
    battery: BatterySpec,
    initial_soc_mwh: float,
) -> pd.DataFrame:
    clean = _validated_frame(frame)
    action_array = np.asarray(actions, dtype=int)
    if action_array.shape != (len(clean),):
        raise ValueError("One action is required per test observation.")
    levels = battery.soc_levels
    matches = np.where(np.isclose(levels, initial_soc_mwh))[0]
    if len(matches) != 1:
        raise ValueError("initial_soc_mwh must lie on the SOC grid.")
    soc_i = int(matches[0])
    rows: list[dict[str, object]] = []
    cumulative = 0.0
    for t, row in clean.iterrows():
        action = int(action_array[t])
        soc_before = float(levels[soc_i])
        next_soc = soc_before + battery.soc_delta(action)
        if not -1e-10 <= next_soc <= battery.capacity_mwh + 1e-10:
            raise AssertionError("A simulated policy selected an infeasible action.")
        reward = battery.realized_reward(float(row["price"]), action)
        soc_i = int(round(next_soc / battery.energy_step_mwh))
        cumulative += reward
        rows.append(
            {
                "step": t,
                "timestamp": row["timestamp"],
                "price": float(row["price"]),
                "soc_before_mwh": soc_before,
                "action": str(ACTION_NAMES[action]),
                "soc_after_mwh": float(next_soc),
                "profit": float(reward),
                "cumulative_profit": float(cumulative),
            }
        )
    return pd.DataFrame(rows)


def simulate_finite_policy(
    frame: pd.DataFrame,
    model: StateModel,
    decisions: np.ndarray,
    battery: BatterySpec,
    initial_soc_mwh: float,
) -> pd.DataFrame:
    clean = _validated_frame(frame)
    bins = model.discretizer.transform(clean["price"].to_numpy(dtype=float))
    levels = battery.soc_levels
    soc_i = int(np.where(np.isclose(levels, initial_soc_mwh))[0][0])
    actions = np.empty(len(clean), dtype=int)
    for t, price_bin in enumerate(bins):
        action = int(decisions[t, soc_i, price_bin])
        actions[t] = action
        soc_i += int(np.sign(battery.soc_delta(action)))
    return trajectory_from_actions(clean, actions, battery, initial_soc_mwh)


def idle_trajectory(
    frame: pd.DataFrame, battery: BatterySpec, initial_soc_mwh: float
) -> pd.DataFrame:
    return trajectory_from_actions(
        frame, np.full(len(frame), int(Action.IDLE)), battery, initial_soc_mwh
    )


def threshold_trajectory(
    train: pd.DataFrame,
    test: pd.DataFrame,
    battery: BatterySpec,
    initial_soc_mwh: float,
) -> pd.DataFrame:
    lower, upper = np.quantile(train["price"].to_numpy(dtype=float), [0.25, 0.75])
    soc = initial_soc_mwh
    actions = np.full(len(test), int(Action.IDLE), dtype=int)
    for t, price in enumerate(test["price"].to_numpy(dtype=float)):
        if price <= lower and soc < battery.capacity_mwh - 1e-10:
            actions[t] = int(Action.CHARGE)
        elif price >= upper and soc > 1e-10:
            actions[t] = int(Action.DISCHARGE)
        soc += battery.soc_delta(actions[t])
    return trajectory_from_actions(test, actions, battery, initial_soc_mwh)


def _deterministic_value_update(
    values_next: np.ndarray, price: float, battery: BatterySpec
) -> np.ndarray:
    next_soc = _feasible_next_indices(battery)
    result = np.full(len(battery.soc_levels), -np.inf, dtype=float)
    for soc_i in range(len(result)):
        for action in ACTION_TIE_ORDER:
            destination = next_soc[soc_i, action]
            if destination >= 0:
                result[soc_i] = max(
                    result[soc_i],
                    battery.realized_reward(price, action) + values_next[destination],
                )
    return result


def seasonal_mpc_trajectory(
    train: pd.DataFrame,
    test: pd.DataFrame,
    battery: BatterySpec,
    initial_soc_mwh: float,
    terminal_salvage_price: float,
) -> pd.DataFrame:
    """Causal 24-hour receding-horizon baseline using training hourly means."""

    seasonal = train.assign(hour=train["timestamp"].dt.hour).groupby("hour")[
        "price"
    ].mean()
    if len(seasonal) != 24:
        raise ValueError("Every UTC hour must occur in the training segment.")
    continuation = np.empty((24, len(battery.soc_levels)), dtype=float)
    terminal = (
        terminal_salvage_price
        * battery.discharge_efficiency
        * battery.soc_levels
    )
    for current_hour in range(24):
        values = terminal.copy()
        for lead in range(23, 0, -1):
            forecast = float(seasonal.loc[(current_hour + lead) % 24])
            values = _deterministic_value_update(values, forecast, battery)
        continuation[current_hour] = values

    next_soc = _feasible_next_indices(battery)
    soc_i = int(np.where(np.isclose(battery.soc_levels, initial_soc_mwh))[0][0])
    actions = np.full(len(test), int(Action.IDLE), dtype=int)
    for t, row in test.reset_index(drop=True).iterrows():
        hour = int(row["timestamp"].hour)
        candidates: list[tuple[float, int]] = []
        for tie_rank, action in enumerate(ACTION_TIE_ORDER):
            destination = next_soc[soc_i, action]
            if destination >= 0:
                value = battery.realized_reward(float(row["price"]), action)
                value += continuation[hour, destination]
                candidates.append((value - tie_rank * 1e-12, int(action)))
        actions[t] = max(candidates)[1]
        soc_i = next_soc[soc_i, actions[t]]
    return trajectory_from_actions(test, actions, battery, initial_soc_mwh)


def trajectory_metrics(
    trajectory: pd.DataFrame,
    battery: BatterySpec,
    initial_soc_mwh: float,
    terminal_salvage_price: float,
) -> dict[str, float | int]:
    cash = float(trajectory["profit"].sum())
    terminal_soc = float(trajectory["soc_after_mwh"].iloc[-1])
    adjusted = cash + terminal_salvage_price * battery.discharge_efficiency * (
        terminal_soc - initial_soc_mwh
    )
    cumulative = np.concatenate(([0.0], trajectory["profit"].cumsum().to_numpy()))
    drawdown = np.maximum.accumulate(cumulative) - cumulative
    throughput = float(
        np.abs(
            trajectory["soc_after_mwh"].to_numpy()
            - trajectory["soc_before_mwh"].to_numpy()
        ).sum()
    )
    return {
        "test_hours": len(trajectory),
        "cash_profit": cash,
        "terminal_soc_mwh": terminal_soc,
        "inventory_adjusted_profit": adjusted,
        "annualized_adjusted_profit": adjusted * 8760.0 / len(trajectory),
        "equivalent_full_cycles": throughput / (2.0 * battery.capacity_mwh),
        "max_cash_drawdown": float(drawdown.max()),
    }


def moving_block_daily_difference(
    reference: pd.DataFrame,
    comparator: pd.DataFrame,
    seed: int,
    block_days: int = 7,
    replications: int = 5000,
) -> tuple[float, float, float]:
    """Conditional moving-block interval for paired daily cash-profit differences."""

    ref_dates = pd.to_datetime(reference["timestamp"], utc=True).dt.floor("D")
    cmp_dates = pd.to_datetime(comparator["timestamp"], utc=True).dt.floor("D")
    ref_daily = reference.groupby(ref_dates, sort=True)["profit"].sum()
    cmp_daily = comparator.groupby(cmp_dates, sort=True)["profit"].sum()
    common = ref_daily.index.intersection(cmp_daily.index)
    differences = (ref_daily.loc[common] - cmp_daily.loc[common]).to_numpy(dtype=float)
    if len(differences) < block_days:
        raise ValueError("Insufficient daily observations for block resampling.")
    rng = np.random.default_rng(seed)
    n_blocks = int(math.ceil(len(differences) / block_days))
    offsets = np.arange(block_days)
    means = np.empty(replications, dtype=float)
    for b in range(replications):
        starts = rng.integers(0, len(differences), size=n_blocks)
        indices = (starts[:, None] + offsets[None, :]) % len(differences)
        means[b] = differences[indices.reshape(-1)[: len(differences)]].mean()
    return (
        float(differences.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
    )


def evaluate_case(
    frame: pd.DataFrame,
    case: str,
    battery: BatterySpec,
    candidates: Iterable[int],
    initial_soc_mwh: float = 200.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Fit, select, and evaluate every policy on one chronological case."""

    train, test = chronological_split(frame)
    selected_k, selection = expanding_window_selection(train, candidates)
    price_model = fit_state_model(train, selected_k, calendar_aware=False)
    hour_model = fit_state_model(train, selected_k, calendar_aware=True)
    salvage = float(np.median(train["price"]))

    price_decisions = finite_horizon_policy(
        price_model, battery, test["timestamp"], salvage
    )
    hour_decisions = finite_horizon_policy(
        hour_model, battery, test["timestamp"], salvage
    )
    trajectories = {
        POLICY_HOUR: simulate_finite_policy(
            test, hour_model, hour_decisions, battery, initial_soc_mwh
        ),
        POLICY_PRICE: simulate_finite_policy(
            test, price_model, price_decisions, battery, initial_soc_mwh
        ),
        POLICY_MPC: seasonal_mpc_trajectory(
            train, test, battery, initial_soc_mwh, salvage
        ),
        POLICY_THRESHOLD: threshold_trajectory(
            train, test, battery, initial_soc_mwh
        ),
        POLICY_IDLE: idle_trajectory(test, battery, initial_soc_mwh),
    }
    oracle = perfect_foresight_dispatch(
        test["price"].to_numpy(dtype=float),
        test["timestamp"].astype(str).tolist(),
        battery,
        initial_soc_mwh,
        salvage,
    )
    trajectories[POLICY_ORACLE] = oracle

    rows: list[dict[str, object]] = []
    oracle_metrics = trajectory_metrics(oracle, battery, initial_soc_mwh, salvage)
    oracle_adjusted = float(oracle_metrics["inventory_adjusted_profit"])
    for policy_index, (policy, trajectory) in enumerate(trajectories.items()):
        metrics = trajectory_metrics(
            trajectory, battery, initial_soc_mwh, salvage
        )
        daily_mean, daily_low, daily_high = moving_block_daily_difference(
            trajectories[POLICY_HOUR], trajectory, seed=3000 + policy_index
        )
        metrics.update(
            {
                "case": case,
                "policy": policy,
                "selected_bins": selected_k,
                "oracle_efficiency_percent": (
                    100.0 * float(metrics["inventory_adjusted_profit"]) / oracle_adjusted
                    if oracle_adjusted > 0
                    else float("nan")
                ),
                "mean_daily_cash_advantage_hour_minus_policy": daily_mean,
                "daily_advantage_block_ci95_lower": daily_low,
                "daily_advantage_block_ci95_upper": daily_high,
                "daily_advantage_block_days": 7,
                "daily_advantage_bootstrap_replications": 5000,
            }
        )
        rows.append(metrics)

    selection = selection.copy()
    selection.insert(0, "case", case)
    diagnostics = {
        "case": case,
        "observations": len(frame),
        "train_hours": len(train),
        "test_hours": len(test),
        "train_start": str(train["timestamp"].iloc[0]),
        "train_end": str(train["timestamp"].iloc[-1]),
        "test_start": str(test["timestamp"].iloc[0]),
        "test_end": str(test["timestamp"].iloc[-1]),
        "selected_bins": selected_k,
        "test_nll_price_only": continuous_predictive_nll(price_model, test),
        "test_nll_hour_aware": continuous_predictive_nll(hour_model, test),
        "terminal_salvage_price": salvage,
        "price_min": float(frame["price"].min()),
        "price_max": float(frame["price"].max()),
        "price_mean": float(frame["price"].mean()),
    }
    return pd.DataFrame(rows), selection, diagnostics


def load_opsd_markets(csv_path: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Load and minimally repair DK1/DK2 from OPSD version 2020-10-06."""

    columns = ["utc_timestamp", "DK_1_price_day_ahead", "DK_2_price_day_ahead"]
    raw = pd.read_csv(csv_path, usecols=columns, parse_dates=["utc_timestamp"])
    raw["utc_timestamp"] = pd.to_datetime(raw["utc_timestamp"], utc=True)
    markets: dict[str, pd.DataFrame] = {}
    quality_rows: list[dict[str, object]] = []
    for case, column in (("DK1 historical", columns[1]), ("DK2 historical", columns[2])):
        nonmissing = raw.loc[raw[column].notna(), "utc_timestamp"]
        start, end = nonmissing.iloc[0], nonmissing.iloc[-1]
        subset = raw.loc[
            raw["utc_timestamp"].between(start, end), ["utc_timestamp", column]
        ].copy()
        missing_before = int(subset[column].isna().sum())
        subset[column] = subset[column].interpolate(
            method="linear", limit_direction="both"
        )
        frame = subset.rename(columns={"utc_timestamp": "timestamp", column: "price"})
        frame = _validated_frame(frame)
        markets[case] = frame
        quality_rows.append(
            {
                "case": case,
                "source_column": column,
                "start": str(frame["timestamp"].iloc[0]),
                "end": str(frame["timestamp"].iloc[-1]),
                "hours": len(frame),
                "interpolated_hours": missing_before,
                "interpolated_percent": 100.0 * missing_before / len(frame),
            }
        )
    return markets, pd.DataFrame(quality_rows)


def bootstrap_mean_ci(
    values: Sequence[float], seed: int, replications: int = 5000
) -> tuple[float, float]:
    x = np.asarray(values, dtype=float)
    if len(x) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(x), size=(replications, len(x)))
    means = x[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def summarize_seed_results(metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for index, (policy, group) in enumerate(metrics.groupby("policy", sort=False)):
        values = group["annualized_adjusted_profit"].to_numpy(dtype=float)
        low, high = bootstrap_mean_ci(values, 1000 + index)
        rows.append(
            {
                "policy": policy,
                "seeds": len(values),
                "mean_annualized_profit": float(np.mean(values)),
                "standard_deviation": float(np.std(values, ddof=1)),
                "bootstrap_ci95_lower": low,
                "bootstrap_ci95_upper": high,
                "mean_oracle_efficiency_percent": float(
                    group["oracle_efficiency_percent"].mean()
                ),
            }
        )
    summary = pd.DataFrame(rows)

    wide = metrics.pivot(
        index="seed", columns="policy", values="annualized_adjusted_profit"
    )
    comparisons: list[dict[str, object]] = []
    competitors = [POLICY_PRICE, POLICY_MPC, POLICY_THRESHOLD, POLICY_IDLE]
    for index, competitor in enumerate(competitors):
        differences = (wide[POLICY_HOUR] - wide[competitor]).to_numpy(dtype=float)
        low, high = bootstrap_mean_ci(differences, 2000 + index)
        comparisons.append(
            {
                "comparison": f"{POLICY_HOUR} minus {competitor}",
                "seeds": len(differences),
                "mean_paired_difference": float(np.mean(differences)),
                "bootstrap_ci95_lower": low,
                "bootstrap_ci95_upper": high,
                "positive_seed_fraction": float(np.mean(differences > 0)),
            }
        )
    return summary, pd.DataFrame(comparisons)


def evaluate_single_policy(
    frame: pd.DataFrame,
    model: StateModel,
    battery: BatterySpec,
    initial_soc_mwh: float,
    planner_discount: float = 1.0,
) -> dict[str, float | int]:
    train, test = chronological_split(frame)
    salvage = float(np.median(train["price"]))
    decisions = finite_horizon_policy(
        model,
        battery,
        test["timestamp"],
        salvage,
        planner_discount=planner_discount,
    )
    learned = simulate_finite_policy(test, model, decisions, battery, initial_soc_mwh)
    oracle = perfect_foresight_dispatch(
        test["price"].to_numpy(dtype=float),
        test["timestamp"].astype(str).tolist(),
        battery,
        initial_soc_mwh,
        salvage,
    )
    result = trajectory_metrics(learned, battery, initial_soc_mwh, salvage)
    oracle_result = trajectory_metrics(oracle, battery, initial_soc_mwh, salvage)
    result["oracle_efficiency_percent"] = (
        100.0
        * float(result["inventory_adjusted_profit"])
        / float(oracle_result["inventory_adjusted_profit"])
    )
    return result


def sensitivity_analysis(
    frames: dict[str, pd.DataFrame],
    selected_bins: dict[str, int],
    initial_soc_mwh: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    parameter_rows: list[dict[str, object]] = []
    gamma_rows: list[dict[str, object]] = []
    for case, frame in frames.items():
        train, _ = chronological_split(frame)
        model = fit_state_model(
            train, selected_bins[case], calendar_aware=True
        )
        for eta in (1.00, 0.95, 0.90):
            for degradation in (0.0, 5.0, 15.0):
                battery = BatterySpec(
                    charge_efficiency=eta,
                    discharge_efficiency=eta,
                    degradation_cost_per_mwh=degradation,
                )
                row = evaluate_single_policy(
                    frame, model, battery, initial_soc_mwh
                )
                row.update(
                    {
                        "case": case,
                        "symmetric_efficiency": eta,
                        "round_trip_efficiency": eta**2,
                        "degradation_cost_per_internal_mwh": degradation,
                    }
                )
                parameter_rows.append(row)
        battery = BatterySpec(
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            degradation_cost_per_mwh=5.0,
        )
        for gamma in (0.95, 0.99, 1.00):
            row = evaluate_single_policy(
                frame,
                model,
                battery,
                initial_soc_mwh,
                planner_discount=gamma,
            )
            row.update({"case": case, "planner_discount": gamma})
            gamma_rows.append(row)
    return pd.DataFrame(parameter_rows), pd.DataFrame(gamma_rows)


def solver_diagnostics(frame: pd.DataFrame, n_bins: int) -> pd.DataFrame:
    """Retain VI/PI agreement only as a software-verification diagnostic."""

    train, _ = chronological_split(frame)
    discretizer = PriceDiscretizer.fit(train["price"].to_numpy(dtype=float), n_bins)
    labels = discretizer.transform(train["price"].to_numpy(dtype=float))
    transition, _ = estimate_price_transition(labels, n_bins)
    battery = BatterySpec(
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        degradation_cost_per_mwh=5.0,
    )
    mdp = BatteryArbitrageMDP.build(
        battery, discretizer.representatives, transition
    )
    rows: list[dict[str, object]] = []
    for gamma in (0.95, 0.99):
        config = SolverConfig(gamma=gamma, tolerance=1e-9)
        vi = value_iteration(mdp, config)
        pi = policy_iteration(mdp, config)
        rows.append(
            {
                "gamma": gamma,
                "value_iteration_converged": vi.converged,
                "value_iteration_iterations": vi.iterations,
                "policy_iteration_converged": pi.converged,
                "policy_iteration_iterations": pi.iterations,
                "policy_agreement_fraction": float(np.mean(vi.policy == pi.policy)),
                "maximum_value_difference": float(np.max(np.abs(vi.values - pi.values))),
                "vi_bellman_residual": policy_bellman_residual(
                    mdp, vi.values, gamma
                ),
                "pi_bellman_residual": policy_bellman_residual(
                    mdp, pi.values, gamma
                ),
            }
        )
    return pd.DataFrame(rows)


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "figure.dpi": 160,
            "savefig.dpi": 400,
            "savefig.bbox": "tight",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def make_figures(
    output_dir: Path,
    market_frames: dict[str, pd.DataFrame],
    selections: pd.DataFrame,
    synthetic_summary: pd.DataFrame,
    paired: pd.DataFrame,
    real_metrics: pd.DataFrame,
    sensitivity: pd.DataFrame,
    gamma_sensitivity: pd.DataFrame,
) -> None:
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    _style()

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.2), constrained_layout=True)
    for case, frame in market_frames.items():
        sample = frame.iloc[-24 * 60 :]
        axes[0].plot(sample["timestamp"], sample["price"], lw=0.75, label=case)
    axes[0].axhline(0, color="0.35", lw=0.6)
    axes[0].set_ylabel("Day-ahead price (EUR/MWh)")
    axes[0].set_title("A. Last 60 days of the historical benchmark")
    axes[0].legend(ncol=2, frameon=False)
    axes[0].tick_params(axis="x", rotation=20)
    historical_selection = selections[selections["case"] == "DK1 historical"]
    means = (
        historical_selection.groupby(["n_bins", "model"], as_index=False)["mean_nll"]
        .mean()
    )
    for model, group in means.groupby("model"):
        axes[1].plot(
            group["n_bins"],
            group["mean_nll"],
            marker="o",
            label=model.replace("_", " "),
        )
    axes[1].set_xlabel("Candidate number of price bins")
    axes[1].set_ylabel("Mean validation NLL")
    axes[1].set_title("B. Leakage-free expanding-window model selection (DK1)")
    axes[1].legend(frameon=False)
    fig.savefig(figures / "Figure_1_data_and_model_selection.png")
    fig.savefig(figures / "Figure_1_data_and_model_selection.pdf")
    plt.close(fig)

    order = [POLICY_HOUR, POLICY_PRICE, POLICY_MPC, POLICY_THRESHOLD, POLICY_IDLE]
    plot = synthetic_summary.set_index("policy").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(7.2, 3.8), constrained_layout=True)
    x = np.arange(len(plot))
    means = plot["mean_annualized_profit"].to_numpy() / 1e6
    errors = np.vstack(
        [
            means - plot["bootstrap_ci95_lower"].to_numpy() / 1e6,
            plot["bootstrap_ci95_upper"].to_numpy() / 1e6 - means,
        ]
    )
    ax.bar(x, means, color=["#214F7A", "#6E9ECF", "#6A9A57", "#D28B3C", "#888888"])
    ax.errorbar(x, means, yerr=errors, fmt="none", ecolor="black", capsize=3, lw=0.9)
    ax.set_xticks(x, ["Hour-aware\nMDP", "Price-only\nMDP", "Seasonal\nMPC", "Threshold", "Idle"])
    ax.set_ylabel("Annualized adjusted profit (million currency units)")
    ax.set_title("Synthetic performance over independently regenerated datasets")
    ax.axhline(0, color="black", lw=0.6)
    fig.savefig(figures / "Figure_2_synthetic_baselines.png")
    fig.savefig(figures / "Figure_2_synthetic_baselines.pdf")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), constrained_layout=True)
    labels = [
        value.replace(f"{POLICY_HOUR} minus ", "")
        for value in paired["comparison"]
    ]
    y = np.arange(len(labels))
    mean = paired["mean_paired_difference"].to_numpy() / 1e6
    low = paired["bootstrap_ci95_lower"].to_numpy() / 1e6
    high = paired["bootstrap_ci95_upper"].to_numpy() / 1e6
    axes[0].errorbar(
        mean,
        y,
        xerr=np.vstack((mean - low, high - mean)),
        fmt="o",
        color="#214F7A",
        capsize=3,
    )
    axes[0].axvline(0, color="black", lw=0.7)
    axes[0].set_yticks(y, [s.replace(" finite-horizon ", "\n") for s in labels])
    axes[0].set_xlabel("Paired annualized difference (million)")
    axes[0].set_title("A. Hour-aware advantage across seeds")
    historical = real_metrics[
        real_metrics["policy"].isin(order)
    ].copy()
    pivot = historical.pivot(
        index="policy", columns="case", values="annualized_adjusted_profit"
    ).reindex(order)
    width = 0.35
    x = np.arange(len(order))
    for j, case in enumerate(pivot.columns):
        axes[1].bar(
            x + (j - 0.5) * width,
            pivot[case].to_numpy() / 1e6,
            width=width,
            label=case,
        )
    axes[1].set_xticks(
        x,
        ["Hour\nMDP", "Price\nMDP", "Seasonal\nMPC", "Quantile\nrule", "Idle"],
    )
    axes[1].tick_params(axis="x", labelsize=7)
    axes[1].set_ylabel("Annualized adjusted profit (million EUR)")
    axes[1].set_title("B. Historical holdout results")
    axes[1].legend(frameon=False)
    fig.savefig(figures / "Figure_3_comparative_results.png")
    fig.savefig(figures / "Figure_3_comparative_results.pdf")
    plt.close(fig)

    cases = list(sensitivity["case"].drop_duplicates())
    fig, axes = plt.subplots(1, len(cases), figsize=(7.2, 3.2), constrained_layout=True)
    if len(cases) == 1:
        axes = [axes]
    global_min = sensitivity["annualized_adjusted_profit"].min() / 1e6
    global_max = sensitivity["annualized_adjusted_profit"].max() / 1e6
    image = None
    for ax, case in zip(axes, cases):
        table = sensitivity[sensitivity["case"] == case].pivot(
            index="symmetric_efficiency",
            columns="degradation_cost_per_internal_mwh",
            values="annualized_adjusted_profit",
        ).sort_index(ascending=False)
        image = ax.imshow(
            table.to_numpy() / 1e6,
            cmap="viridis",
            vmin=global_min,
            vmax=global_max,
            aspect="auto",
        )
        ax.set_xticks(range(len(table.columns)), [f"{x:g}" for x in table.columns])
        ax.set_yticks(range(len(table.index)), [f"{x:.2f}" for x in table.index])
        ax.set_xlabel("Degradation cost (currency/MWh)")
        ax.set_ylabel("One-way efficiency")
        ax.set_title(case)
    fig.colorbar(image, ax=axes, label="Annualized adjusted profit (million)", shrink=0.85)
    fig.savefig(figures / "Figure_4_physical_sensitivity.png")
    fig.savefig(figures / "Figure_4_physical_sensitivity.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 3.4), constrained_layout=True)
    for case, group in gamma_sensitivity.groupby("case"):
        ax.plot(
            group["planner_discount"],
            group["annualized_adjusted_profit"] / 1e6,
            marker="o",
            label=case,
        )
    ax.set_xlabel("Finite-horizon planner discount")
    ax.set_ylabel("Annualized adjusted profit (million)")
    ax.set_title("Planner-discount sensitivity; primary specification is gamma = 1")
    ax.legend(frameon=False)
    fig.savefig(figures / "Figure_5_discount_sensitivity.png")
    fig.savefig(figures / "Figure_5_discount_sensitivity.pdf")
    plt.close(fig)


def run_benchmark(args: argparse.Namespace) -> dict[str, object]:
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidates = tuple(int(value) for value in args.candidates.split(","))
    main_battery = BatterySpec(
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        degradation_cost_per_mwh=5.0,
    )
    initial_soc = 200.0

    market_frames, data_quality = load_opsd_markets(Path(args.opsd_csv))
    synthetic_metrics_parts: list[pd.DataFrame] = []
    selection_parts: list[pd.DataFrame] = []
    diagnostics: list[dict[str, object]] = []
    selected_bins: dict[str, int] = {}

    for seed in range(args.synthetic_seeds):
        case = f"Synthetic seed {seed}"
        frame = generate_synthetic_prices(args.synthetic_hours, seed)
        metrics, selection, diagnostic = evaluate_case(
            frame, case, main_battery, candidates, initial_soc
        )
        metrics.insert(1, "seed", seed)
        synthetic_metrics_parts.append(metrics)
        selection.insert(1, "seed", seed)
        selection_parts.append(selection)
        diagnostic["seed"] = seed
        diagnostics.append(diagnostic)
        if seed == args.sensitivity_seed:
            selected_bins["Synthetic seed 42"] = int(diagnostic["selected_bins"])

    synthetic_metrics = pd.concat(synthetic_metrics_parts, ignore_index=True)
    synthetic_summary, paired = summarize_seed_results(synthetic_metrics)

    real_parts: list[pd.DataFrame] = []
    for case, frame in market_frames.items():
        metrics, selection, diagnostic = evaluate_case(
            frame, case, main_battery, candidates, initial_soc
        )
        real_parts.append(metrics)
        selection_parts.append(selection)
        diagnostics.append(diagnostic)
        selected_bins[case] = int(diagnostic["selected_bins"])
    real_metrics = pd.concat(real_parts, ignore_index=True)
    all_selections = pd.concat(selection_parts, ignore_index=True)
    diagnostic_frame = pd.DataFrame(diagnostics)

    sensitivity_frames = {
        "Synthetic seed 42": generate_synthetic_prices(
            args.synthetic_hours, args.sensitivity_seed
        ),
        "DK1 historical": market_frames["DK1 historical"],
    }
    if "Synthetic seed 42" not in selected_bins:
        train, _ = chronological_split(sensitivity_frames["Synthetic seed 42"])
        selected_bins["Synthetic seed 42"], _ = expanding_window_selection(
            train, candidates
        )
    physical_sensitivity, gamma_sensitivity = sensitivity_analysis(
        sensitivity_frames, selected_bins, initial_soc
    )
    solver = solver_diagnostics(
        sensitivity_frames["Synthetic seed 42"],
        selected_bins["Synthetic seed 42"],
    )

    outputs = {
        "synthetic_seed_metrics.csv": synthetic_metrics,
        "synthetic_summary.csv": synthetic_summary,
        "paired_seed_comparisons.csv": paired,
        "real_market_metrics.csv": real_metrics,
        "model_selection_folds.csv": all_selections,
        "case_diagnostics.csv": diagnostic_frame,
        "data_quality.csv": data_quality,
        "physical_sensitivity.csv": physical_sensitivity,
        "gamma_sensitivity.csv": gamma_sensitivity,
        "solver_diagnostics.csv": solver,
    }
    for filename, table in outputs.items():
        table.to_csv(output / filename, index=False)

    make_figures(
        output,
        market_frames,
        all_selections,
        synthetic_summary,
        paired,
        real_metrics,
        physical_sensitivity,
        gamma_sensitivity,
    )

    manifest = {
        "repository_url": REPOSITORY_URL,
        "study_type": "synthetic and historical benchmark; not a deployment study",
        "synthetic_generator": "voltrl.generate_synthetic_prices",
        "synthetic_seeds": list(range(args.synthetic_seeds)),
        "synthetic_hours_per_seed": args.synthetic_hours,
        "chronological_train_fraction": 0.70,
        "model_selection": "three-fold expanding-window continuous predictive NLL",
        "candidate_bins": list(candidates),
        "main_battery": asdict(main_battery),
        "initial_soc_mwh": initial_soc,
        "primary_planner_discount": 1.0,
        "opsd_source": {
            "package": "Open Power System Data, Time series, version 2020-10-06",
            "doi": "10.25832/time_series/2020-10-06",
            "url": "https://data.open-power-system-data.org/time_series/2020-10-06/",
            "file": Path(args.opsd_csv).name,
            "markets": ["DK_1_price_day_ahead", "DK_2_price_day_ahead"],
        },
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "outputs": list(outputs) + [
            "figures/Figure_1_data_and_model_selection.png",
            "figures/Figure_2_synthetic_baselines.png",
            "figures/Figure_3_comparative_results.png",
            "figures/Figure_4_physical_sensitivity.png",
            "figures/Figure_5_discount_sensitivity.png",
        ],
    }
    (output / "experiment_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opsd-csv", required=True)
    parser.add_argument("--output-dir", default="results_revision")
    parser.add_argument("--synthetic-seeds", type=int, default=30)
    parser.add_argument("--synthetic-hours", type=int, default=17_520)
    parser.add_argument("--sensitivity-seed", type=int, default=42)
    parser.add_argument("--candidates", default="4,6,8,10,12")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = run_benchmark(args)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
