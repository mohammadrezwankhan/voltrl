"""Recompute publication statistics from VoltRL synthetic seed metrics."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

METRICS_FILE = "synthetic_seed_metrics.csv"
SUMMARY_FILE = "synthetic_summary.csv"
COMPARISONS_FILE = "paired_seed_comparisons.csv"
REQUIRED_OUTPUTS = (METRICS_FILE, SUMMARY_FILE, COMPARISONS_FILE)
ANNUAL_HOURS = 8760.0
REL_TOLERANCE = 1e-12
ABS_TOLERANCE = 1e-9


@dataclass(frozen=True)
class SeedMetric:
    line: int
    seed: int
    policy: str
    test_hours: int
    inventory_adjusted_profit: float
    annualized_adjusted_profit: float
    oracle_efficiency_percent: float


@dataclass(frozen=True)
class SummaryStatistic:
    line: int
    seeds: int
    mean_annualized_profit: float
    standard_deviation: float
    bootstrap_ci95_lower: float
    bootstrap_ci95_upper: float
    mean_oracle_efficiency_percent: float


@dataclass(frozen=True)
class PairedComparison:
    line: int
    seeds: int
    mean_paired_difference: float
    bootstrap_ci95_lower: float
    bootstrap_ci95_upper: float
    positive_seed_fraction: float


@dataclass(frozen=True)
class AuditCounts:
    metric_rows: int
    seeds: int
    policies: int
    comparisons: int


def _load_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be a JSON object")
    return manifest


def _read_table(
    path: Path,
    required_columns: Sequence[str],
    errors: list[str],
) -> list[dict[str, str]]:
    if not path.is_file():
        errors.append(f"missing synthetic statistics table: {path.name}")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as table_file:
        reader = csv.DictReader(table_file)
        columns = reader.fieldnames or []
        missing = [column for column in required_columns if column not in columns]
        if missing:
            errors.append(f"{path.name} is missing columns: {', '.join(missing)}")
            return []
        rows = list(reader)
    if not rows:
        errors.append(f"{path.name} must contain at least one data row")
    return rows


def _nonempty(value: str | None, label: str, errors: list[str]) -> str | None:
    if value is None or not value.strip():
        errors.append(f"{label} must be nonempty")
        return None
    return value


def _number(value: str | None, label: str, errors: list[str]) -> float | None:
    try:
        number = float(value) if value is not None else math.nan
    except ValueError:
        number = math.nan
    if not math.isfinite(number):
        errors.append(f"{label} must be finite, found {value!r}")
        return None
    return number


def _integer(value: str | None, label: str, errors: list[str]) -> int | None:
    number = _number(value, label, errors)
    if number is None:
        return None
    if not number.is_integer():
        errors.append(f"{label} must be an integer, found {value!r}")
        return None
    return int(number)


def _close(stated: float, recomputed: float) -> bool:
    return math.isclose(
        stated,
        recomputed,
        rel_tol=REL_TOLERANCE,
        abs_tol=ABS_TOLERANCE,
    )


def _validate_manifest(
    manifest: dict[str, object],
    errors: list[str],
) -> set[int] | None:
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list) or not all(
        isinstance(output, str) for output in outputs
    ):
        errors.append("manifest outputs must be a path list")
    else:
        missing = sorted(set(REQUIRED_OUTPUTS) - set(outputs))
        if missing:
            errors.append(
                "manifest outputs omit synthetic statistics tables: "
                + ", ".join(missing)
            )

    seed_values = manifest.get("synthetic_seeds")
    if not isinstance(seed_values, list) or not seed_values:
        errors.append("manifest synthetic_seeds must be a nonempty list")
        return None
    seeds: list[int] = []
    for position, value in enumerate(seed_values):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(
                f"manifest synthetic_seeds[{position}] must be a nonnegative integer"
            )
            continue
        seeds.append(value)
    if len(seeds) != len(set(seeds)):
        errors.append("manifest synthetic_seeds must not contain duplicates")
    return set(seeds)


def _parse_metrics(
    rows: Sequence[dict[str, str]],
    errors: list[str],
) -> dict[tuple[int, str], SeedMetric]:
    metrics: dict[tuple[int, str], SeedMetric] = {}
    for line, row in enumerate(rows, start=2):
        label = f"{METRICS_FILE} line {line}"
        seed = _integer(row.get("seed"), f"{label} seed", errors)
        policy = _nonempty(row.get("policy"), f"{label} policy", errors)
        test_hours = _integer(
            row.get("test_hours"), f"{label} test_hours", errors
        )
        inventory_profit = _number(
            row.get("inventory_adjusted_profit"),
            f"{label} inventory_adjusted_profit",
            errors,
        )
        annualized_profit = _number(
            row.get("annualized_adjusted_profit"),
            f"{label} annualized_adjusted_profit",
            errors,
        )
        oracle_efficiency = _number(
            row.get("oracle_efficiency_percent"),
            f"{label} oracle_efficiency_percent",
            errors,
        )
        if seed is not None and seed < 0:
            errors.append(f"{label} seed must be nonnegative")
        if test_hours is not None and test_hours <= 0:
            errors.append(f"{label} test_hours must be positive")
        if oracle_efficiency is not None and oracle_efficiency > 100.0:
            errors.append(f"{label} oracle_efficiency_percent must not exceed 100")

        if (
            seed is None
            or policy is None
            or test_hours is None
            or inventory_profit is None
            or annualized_profit is None
            or oracle_efficiency is None
            or test_hours <= 0
        ):
            continue
        recomputed_annualized = inventory_profit * ANNUAL_HOURS / test_hours
        if not _close(annualized_profit, recomputed_annualized):
            errors.append(
                f"{label} annualized_adjusted_profit is {annualized_profit:g}; "
                f"recomputed {recomputed_annualized:g}"
            )

        key = (seed, policy)
        if key in metrics:
            errors.append(f"{label} duplicates seed/policy pair {seed}/{policy}")
            continue
        metrics[key] = SeedMetric(
            line=line,
            seed=seed,
            policy=policy,
            test_hours=test_hours,
            inventory_adjusted_profit=inventory_profit,
            annualized_adjusted_profit=annualized_profit,
            oracle_efficiency_percent=oracle_efficiency,
        )
    return metrics


def _validate_metric_coverage(
    metrics: dict[tuple[int, str], SeedMetric],
    manifest_seeds: set[int] | None,
    errors: list[str],
) -> dict[str, dict[int, SeedMetric]]:
    by_policy: dict[str, dict[int, SeedMetric]] = defaultdict(dict)
    by_seed_hours: dict[int, set[int]] = defaultdict(set)
    for metric in metrics.values():
        by_policy[metric.policy][metric.seed] = metric
        by_seed_hours[metric.seed].add(metric.test_hours)

    policies = sorted(by_policy)
    if not policies:
        return by_policy
    baseline_seeds = set(by_policy[policies[0]])
    if len(baseline_seeds) < 2:
        errors.append("synthetic statistics require at least two seeds per policy")
    for policy in policies[1:]:
        seeds = set(by_policy[policy])
        if seeds != baseline_seeds:
            errors.append(
                f"seed coverage mismatch for {policy}: missing "
                f"{sorted(baseline_seeds - seeds)}, extra "
                f"{sorted(seeds - baseline_seeds)} versus {policies[0]}"
            )
    if manifest_seeds is not None and baseline_seeds != manifest_seeds:
        errors.append(
            "seed metrics disagree with manifest synthetic_seeds: missing "
            f"{sorted(manifest_seeds - baseline_seeds)}, extra "
            f"{sorted(baseline_seeds - manifest_seeds)}"
        )
    for seed, hours in sorted(by_seed_hours.items()):
        if len(hours) != 1:
            errors.append(
                f"seed {seed} uses inconsistent test_hours across policies: "
                f"{sorted(hours)}"
            )
    return by_policy


def _parse_summaries(
    rows: Sequence[dict[str, str]],
    errors: list[str],
) -> dict[str, SummaryStatistic]:
    summaries: dict[str, SummaryStatistic] = {}
    for line, row in enumerate(rows, start=2):
        label = f"{SUMMARY_FILE} line {line}"
        policy = _nonempty(row.get("policy"), f"{label} policy", errors)
        seeds = _integer(row.get("seeds"), f"{label} seeds", errors)
        mean_profit = _number(
            row.get("mean_annualized_profit"),
            f"{label} mean_annualized_profit",
            errors,
        )
        standard_deviation = _number(
            row.get("standard_deviation"),
            f"{label} standard_deviation",
            errors,
        )
        lower = _number(
            row.get("bootstrap_ci95_lower"),
            f"{label} bootstrap_ci95_lower",
            errors,
        )
        upper = _number(
            row.get("bootstrap_ci95_upper"),
            f"{label} bootstrap_ci95_upper",
            errors,
        )
        mean_oracle = _number(
            row.get("mean_oracle_efficiency_percent"),
            f"{label} mean_oracle_efficiency_percent",
            errors,
        )
        if seeds is not None and seeds < 1:
            errors.append(f"{label} seeds must be positive")
        if standard_deviation is not None and standard_deviation < 0.0:
            errors.append(f"{label} standard_deviation must be nonnegative")
        if mean_oracle is not None and mean_oracle > 100.0:
            errors.append(
                f"{label} mean_oracle_efficiency_percent must not exceed 100"
            )
        if lower is not None and upper is not None and lower > upper:
            errors.append(f"{label} bootstrap interval is reversed")
        if (
            mean_profit is not None
            and lower is not None
            and upper is not None
            and not lower <= mean_profit <= upper
        ):
            errors.append(f"{label} bootstrap interval does not contain its mean")
        if None in (
            policy,
            seeds,
            mean_profit,
            standard_deviation,
            lower,
            upper,
            mean_oracle,
        ):
            continue
        assert policy is not None
        if policy in summaries:
            errors.append(f"{label} duplicates policy summary {policy}")
            continue
        summaries[policy] = SummaryStatistic(
            line=line,
            seeds=seeds,
            mean_annualized_profit=mean_profit,
            standard_deviation=standard_deviation,
            bootstrap_ci95_lower=lower,
            bootstrap_ci95_upper=upper,
            mean_oracle_efficiency_percent=mean_oracle,
        )
    return summaries


def _validate_summaries(
    by_policy: dict[str, dict[int, SeedMetric]],
    summaries: dict[str, SummaryStatistic],
    errors: list[str],
) -> None:
    policy_names = set(by_policy)
    summary_names = set(summaries)
    for policy in sorted(policy_names - summary_names):
        errors.append(f"missing synthetic summary for policy {policy}")
    for policy in sorted(summary_names - policy_names):
        errors.append(f"synthetic summary has no seed metrics for policy {policy}")

    for policy in sorted(policy_names & summary_names):
        metrics = list(by_policy[policy].values())
        summary = summaries[policy]
        profits = [metric.annualized_adjusted_profit for metric in metrics]
        efficiencies = [metric.oracle_efficiency_percent for metric in metrics]
        mean_profit = math.fsum(profits) / len(profits)
        standard_deviation = statistics.stdev(profits) if len(profits) > 1 else 0.0
        mean_oracle = math.fsum(efficiencies) / len(efficiencies)
        comparisons = (
            ("seeds", float(summary.seeds), float(len(metrics))),
            (
                "mean_annualized_profit",
                summary.mean_annualized_profit,
                mean_profit,
            ),
            (
                "standard_deviation",
                summary.standard_deviation,
                standard_deviation,
            ),
            (
                "mean_oracle_efficiency_percent",
                summary.mean_oracle_efficiency_percent,
                mean_oracle,
            ),
        )
        for field, stated, recomputed in comparisons:
            if not _close(stated, recomputed):
                errors.append(
                    f"summary {field} for {policy} is {stated:g}; "
                    f"recomputed {recomputed:g}"
                )


def _comparison_policies(
    comparison: str,
    policies: Sequence[str],
) -> tuple[str, str] | None:
    matches = [
        (left, right)
        for left in policies
        for right in policies
        if left != right and comparison == f"{left} minus {right}"
    ]
    return matches[0] if len(matches) == 1 else None


def _validate_comparisons(
    rows: Sequence[dict[str, str]],
    by_policy: dict[str, dict[int, SeedMetric]],
    errors: list[str],
) -> int:
    seen: set[str] = set()
    valid_count = 0
    policies = sorted(by_policy)
    for line, row in enumerate(rows, start=2):
        label = f"{COMPARISONS_FILE} line {line}"
        comparison = _nonempty(
            row.get("comparison"), f"{label} comparison", errors
        )
        seeds = _integer(row.get("seeds"), f"{label} seeds", errors)
        mean_difference = _number(
            row.get("mean_paired_difference"),
            f"{label} mean_paired_difference",
            errors,
        )
        lower = _number(
            row.get("bootstrap_ci95_lower"),
            f"{label} bootstrap_ci95_lower",
            errors,
        )
        upper = _number(
            row.get("bootstrap_ci95_upper"),
            f"{label} bootstrap_ci95_upper",
            errors,
        )
        positive_fraction = _number(
            row.get("positive_seed_fraction"),
            f"{label} positive_seed_fraction",
            errors,
        )
        if seeds is not None and seeds < 1:
            errors.append(f"{label} seeds must be positive")
        if positive_fraction is not None and not 0.0 <= positive_fraction <= 1.0:
            errors.append(f"{label} positive_seed_fraction must be in [0, 1]")
        if lower is not None and upper is not None and lower > upper:
            errors.append(f"{label} bootstrap interval is reversed")
        if (
            mean_difference is not None
            and lower is not None
            and upper is not None
            and not lower <= mean_difference <= upper
        ):
            errors.append(f"{label} bootstrap interval does not contain its mean")
        if comparison is None:
            continue
        if comparison in seen:
            errors.append(f"{label} duplicates comparison {comparison}")
            continue
        seen.add(comparison)
        pair = _comparison_policies(comparison, policies)
        if pair is None:
            errors.append(
                f"{label} does not identify two declared policies with 'minus'"
            )
            continue
        if None in (seeds, mean_difference, lower, upper, positive_fraction):
            continue

        left, right = pair
        left_metrics = by_policy[left]
        right_metrics = by_policy[right]
        shared_seeds = sorted(set(left_metrics) & set(right_metrics))
        if set(left_metrics) != set(right_metrics):
            errors.append(f"{label} policies do not share identical seed coverage")
            continue
        differences = [
            left_metrics[seed].annualized_adjusted_profit
            - right_metrics[seed].annualized_adjusted_profit
            for seed in shared_seeds
        ]
        recomputed_mean = math.fsum(differences) / len(differences)
        recomputed_positive = (
            sum(difference > 0.0 for difference in differences) / len(differences)
        )
        comparisons = (
            ("seeds", float(seeds), float(len(differences))),
            ("mean_paired_difference", mean_difference, recomputed_mean),
            (
                "positive_seed_fraction",
                positive_fraction,
                recomputed_positive,
            ),
        )
        for field, stated, recomputed in comparisons:
            if not _close(stated, recomputed):
                errors.append(
                    f"comparison {field} for {comparison} is {stated:g}; "
                    f"recomputed {recomputed:g}"
                )
        valid_count += 1
    return valid_count


def _audit_synthetic_statistics(
    manifest_path: Path,
) -> tuple[list[str], AuditCounts]:
    manifest = _load_manifest(manifest_path)
    errors: list[str] = []
    manifest_seeds = _validate_manifest(manifest, errors)
    result_dir = manifest_path.parent
    metric_rows = _read_table(
        result_dir / METRICS_FILE,
        (
            "seed",
            "policy",
            "test_hours",
            "inventory_adjusted_profit",
            "annualized_adjusted_profit",
            "oracle_efficiency_percent",
        ),
        errors,
    )
    summary_rows = _read_table(
        result_dir / SUMMARY_FILE,
        (
            "policy",
            "seeds",
            "mean_annualized_profit",
            "standard_deviation",
            "bootstrap_ci95_lower",
            "bootstrap_ci95_upper",
            "mean_oracle_efficiency_percent",
        ),
        errors,
    )
    comparison_rows = _read_table(
        result_dir / COMPARISONS_FILE,
        (
            "comparison",
            "seeds",
            "mean_paired_difference",
            "bootstrap_ci95_lower",
            "bootstrap_ci95_upper",
            "positive_seed_fraction",
        ),
        errors,
    )

    metrics = _parse_metrics(metric_rows, errors)
    by_policy = _validate_metric_coverage(metrics, manifest_seeds, errors)
    summaries = _parse_summaries(summary_rows, errors)
    _validate_summaries(by_policy, summaries, errors)
    comparison_count = _validate_comparisons(comparison_rows, by_policy, errors)
    counts = AuditCounts(
        metric_rows=len(metrics),
        seeds=len({metric.seed for metric in metrics.values()}),
        policies=len(by_policy),
        comparisons=comparison_count,
    )
    return errors, counts


def verify_synthetic_statistics_contract(manifest_path: Path) -> list[str]:
    """Return synthetic statistics errors; empty means a valid bundle."""

    errors, _ = _audit_synthetic_statistics(manifest_path)
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        errors, counts = _audit_synthetic_statistics(args.manifest)
    except (OSError, ValueError, csv.Error, json.JSONDecodeError) as error:
        print(f"Synthetic statistics verification failed: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"Synthetic statistics verification failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Verified {counts.metric_rows} seed-policy rows across "
        f"{counts.seeds} seeds and {counts.policies} policies, plus "
        f"{counts.comparisons} paired comparisons."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
