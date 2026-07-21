"""Verify semantic consistency between a VoltRL manifest and result tables."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path, PurePosixPath
from typing import Sequence

REQUIRED_RESULT_TABLES = (
    "synthetic_seed_metrics.csv",
    "synthetic_summary.csv",
    "paired_seed_comparisons.csv",
    "model_selection_folds.csv",
    "case_diagnostics.csv",
)
EXPECTED_SELECTION_MODELS = ("hour_aware", "price_only")
EXPECTED_SELECTION_FOLDS = (1, 2, 3)
SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}")


def _load_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be a JSON object")
    return manifest


def _is_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _json_number(
    value: object,
    label: str,
    errors: list[str],
) -> float | None:
    if not _is_number(value):
        errors.append(f"{label} must be a finite number")
        return None
    return float(value)


def _json_integer(
    value: object,
    label: str,
    errors: list[str],
) -> int | None:
    number = _json_number(value, label, errors)
    if number is None:
        return None
    if not number.is_integer():
        errors.append(f"{label} must be an integer")
        return None
    return int(number)


def _csv_integer(value: str | None, label: str, errors: list[str]) -> int | None:
    try:
        number = float(value) if value is not None else math.nan
    except ValueError:
        number = math.nan
    if not math.isfinite(number) or not number.is_integer():
        errors.append(f"{label} must be an integer, found {value!r}")
        return None
    return int(number)


def _nonempty_string(value: object, label: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a nonempty string")
        return None
    return value


def _canonical_result_path(result_dir: Path, relative_path: str) -> Path:
    if not relative_path or "\\" in relative_path:
        raise ValueError(
            f"result path must use canonical POSIX form: {relative_path!r}"
        )
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError(
            f"result path must stay below the result directory: {relative_path}"
        )
    resolved_root = result_dir.resolve()
    resolved_path = resolved_root.joinpath(*pure_path.parts).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            f"result path must stay below the result directory: {relative_path}"
        ) from error
    return resolved_path


def _read_table(
    result_dir: Path,
    relative_path: str,
    required_columns: Sequence[str],
    errors: list[str],
) -> list[dict[str, str]]:
    try:
        path = _canonical_result_path(result_dir, relative_path)
    except ValueError as error:
        errors.append(str(error))
        return []
    if not path.is_file():
        errors.append(f"missing contract table: {relative_path}")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as table_file:
        reader = csv.DictReader(table_file)
        columns = reader.fieldnames or []
        missing_columns = [
            column for column in required_columns if column not in columns
        ]
        if missing_columns:
            errors.append(
                f"{relative_path} is missing columns: {', '.join(missing_columns)}"
            )
            return []
        rows = list(reader)
    if not rows:
        errors.append(f"{relative_path} must contain at least one data row")
    return rows


def _validate_configuration(
    manifest: dict[str, object], errors: list[str]
) -> tuple[list[int], list[int], int | None, float | None, list[str]]:
    seeds_value = manifest.get("synthetic_seeds")
    seeds: list[int] = []
    if not isinstance(seeds_value, list) or not seeds_value:
        errors.append("synthetic_seeds must be a nonempty list")
    else:
        for position, value in enumerate(seeds_value):
            seed = _json_integer(value, f"synthetic_seeds[{position}]", errors)
            if seed is not None:
                seeds.append(seed)
        if len(seeds) != len(set(seeds)):
            errors.append("synthetic_seeds must not contain duplicates")
        if any(seed < 0 for seed in seeds):
            errors.append("synthetic_seeds must be nonnegative")

    candidates_value = manifest.get("candidate_bins")
    candidates: list[int] = []
    if not isinstance(candidates_value, list) or not candidates_value:
        errors.append("candidate_bins must be a nonempty list")
    else:
        for position, value in enumerate(candidates_value):
            candidate = _json_integer(value, f"candidate_bins[{position}]", errors)
            if candidate is not None:
                candidates.append(candidate)
        if candidates != sorted(set(candidates)):
            errors.append("candidate_bins must be strictly increasing and unique")
        if any(candidate < 2 for candidate in candidates):
            errors.append("candidate_bins must contain integers >= 2")

    synthetic_hours = _json_integer(
        manifest.get("synthetic_hours_per_seed"),
        "synthetic_hours_per_seed",
        errors,
    )
    if synthetic_hours is not None and synthetic_hours < 1:
        errors.append("synthetic_hours_per_seed must be positive")

    train_fraction = _json_number(
        manifest.get("chronological_train_fraction"),
        "chronological_train_fraction",
        errors,
    )
    if train_fraction is not None and not 0.0 < train_fraction < 1.0:
        errors.append("chronological_train_fraction must lie in (0, 1)")

    planner_discount = _json_number(
        manifest.get("primary_planner_discount"),
        "primary_planner_discount",
        errors,
    )
    if planner_discount is not None and not 0.0 < planner_discount <= 1.0:
        errors.append("primary_planner_discount must lie in (0, 1]")

    battery = manifest.get("main_battery")
    battery_values: dict[str, float] = {}
    required_battery_fields = (
        "capacity_mwh",
        "max_power_mw",
        "interval_hours",
        "charge_efficiency",
        "discharge_efficiency",
        "degradation_cost_per_mwh",
    )
    if not isinstance(battery, dict):
        errors.append("main_battery must be an object")
    else:
        for field in required_battery_fields:
            number = _json_number(battery.get(field), f"main_battery.{field}", errors)
            if number is not None:
                battery_values[field] = number
        for field in ("capacity_mwh", "max_power_mw", "interval_hours"):
            if field in battery_values and battery_values[field] <= 0.0:
                errors.append(f"main_battery.{field} must be positive")
        for field in ("charge_efficiency", "discharge_efficiency"):
            if field in battery_values and not 0.0 < battery_values[field] <= 1.0:
                errors.append(f"main_battery.{field} must lie in (0, 1]")
        if battery_values.get("degradation_cost_per_mwh", 0.0) < 0.0:
            errors.append("main_battery.degradation_cost_per_mwh must be nonnegative")

        optional_nonnegative = (
            "dod_stress_exponent",
            "soc_stress_cost_per_hour",
        )
        for field in optional_nonnegative:
            if field in battery:
                number = _json_number(battery[field], f"main_battery.{field}", errors)
                if number is not None and number < 0.0:
                    errors.append(f"main_battery.{field} must be nonnegative")
        if "linear_degradation_fraction" in battery:
            fraction = _json_number(
                battery["linear_degradation_fraction"],
                "main_battery.linear_degradation_fraction",
                errors,
            )
            if fraction is not None and not 0.0 <= fraction <= 1.0:
                errors.append(
                    "main_battery.linear_degradation_fraction must lie in [0, 1]"
                )
        if "nonlinear_degradation" in battery and not isinstance(
            battery["nonlinear_degradation"], bool
        ):
            errors.append("main_battery.nonlinear_degradation must be a boolean")

    initial_soc = _json_number(
        manifest.get("initial_soc_mwh"), "initial_soc_mwh", errors
    )
    capacity = battery_values.get("capacity_mwh")
    power = battery_values.get("max_power_mw")
    interval = battery_values.get("interval_hours")
    if initial_soc is not None and capacity is not None:
        if not 0.0 <= initial_soc <= capacity:
            errors.append("initial_soc_mwh must lie within battery capacity")
    if capacity and power and interval:
        energy_step = power * interval
        if not math.isclose(capacity / energy_step, round(capacity / energy_step)):
            errors.append(
                "main_battery capacity must contain an integer number of steps"
            )
        if initial_soc is not None and not math.isclose(
            initial_soc / energy_step, round(initial_soc / energy_step)
        ):
            errors.append("initial_soc_mwh must lie on the battery SOC grid")

    source = manifest.get("opsd_source")
    if not isinstance(source, dict):
        errors.append("opsd_source must be an object")
    else:
        for field in ("package", "doi", "url", "file"):
            _nonempty_string(source.get(field), f"opsd_source.{field}", errors)
        filename = source.get("file")
        if isinstance(filename, str) and (
            filename in {".", ".."} or "/" in filename or "\\" in filename
        ):
            errors.append("opsd_source.file must be a canonical base name")
        sha256 = source.get("sha256")
        if not isinstance(sha256, str) or SHA256_PATTERN.fullmatch(sha256) is None:
            errors.append("opsd_source.sha256 must contain 64 hexadecimal digits")
        markets = source.get("markets")
        if (
            not isinstance(markets, list)
            or not markets
            or not all(isinstance(market, str) and market.strip() for market in markets)
        ):
            errors.append("opsd_source.markets must be a nonempty string list")
        elif len(markets) != len(set(markets)):
            errors.append("opsd_source.markets must not contain duplicates")

    outputs_value = manifest.get("outputs")
    outputs: list[str] = []
    if (
        not isinstance(outputs_value, list)
        or not outputs_value
        or not all(isinstance(output, str) for output in outputs_value)
    ):
        errors.append("outputs must be a nonempty path list")
    else:
        outputs = list(outputs_value)
        if len(outputs) != len(set(outputs)):
            errors.append("outputs must not contain duplicate paths")
        for output in outputs:
            try:
                _canonical_result_path(Path("."), output)
            except ValueError as error:
                errors.append(str(error))
        missing_tables = sorted(set(REQUIRED_RESULT_TABLES) - set(outputs))
        if missing_tables:
            errors.append("outputs omit contract tables: " + ", ".join(missing_tables))

    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime must be an object")
    else:
        for field in ("python", "platform", "numpy", "pandas", "matplotlib"):
            _nonempty_string(runtime.get(field), f"runtime.{field}", errors)

    for field in ("repository_url", "study_type", "synthetic_generator"):
        _nonempty_string(manifest.get(field), field, errors)

    return seeds, candidates, synthetic_hours, train_fraction, outputs


def _validate_metrics(
    result_dir: Path,
    seeds: list[int],
    candidates: list[int],
    errors: list[str],
) -> tuple[dict[int, int], dict[int, int]]:
    filename = "synthetic_seed_metrics.csv"
    rows = _read_table(
        result_dir,
        filename,
        ("seed", "policy", "selected_bins", "test_hours"),
        errors,
    )
    pairs: set[tuple[int, str]] = set()
    policies_by_seed: dict[int, set[str]] = defaultdict(set)
    selected_by_seed: dict[int, set[int]] = defaultdict(set)
    test_hours_by_seed: dict[int, set[int]] = defaultdict(set)
    for row_number, row in enumerate(rows, start=2):
        seed = _csv_integer(
            row.get("seed"), f"{filename} line {row_number} seed", errors
        )
        selected = _csv_integer(
            row.get("selected_bins"),
            f"{filename} line {row_number} selected_bins",
            errors,
        )
        test_hours = _csv_integer(
            row.get("test_hours"),
            f"{filename} line {row_number} test_hours",
            errors,
        )
        policy = (row.get("policy") or "").strip()
        if not policy:
            errors.append(f"{filename} line {row_number} policy must be nonempty")
        if seed is None:
            continue
        pair = (seed, policy)
        if pair in pairs:
            errors.append(f"{filename} duplicates seed/policy pair: {seed}, {policy}")
        pairs.add(pair)
        policies_by_seed[seed].add(policy)
        if selected is not None:
            selected_by_seed[seed].add(selected)
            if selected not in candidates:
                errors.append(
                    f"{filename} seed {seed} selected bin {selected} is not a candidate"
                )
        if test_hours is not None:
            test_hours_by_seed[seed].add(test_hours)

    if set(policies_by_seed) != set(seeds):
        errors.append(
            f"{filename} seed coverage mismatch: expected {seeds}, "
            f"found {sorted(policies_by_seed)}"
        )
    if policies_by_seed:
        reference_seed = min(policies_by_seed)
        reference_policies = policies_by_seed[reference_seed]
        for seed in seeds:
            if policies_by_seed.get(seed, set()) != reference_policies:
                errors.append(f"{filename} policy coverage differs for seed {seed}")
    selected_result: dict[int, int] = {}
    test_hours_result: dict[int, int] = {}
    for seed in seeds:
        selected_values = selected_by_seed.get(seed, set())
        if len(selected_values) != 1:
            errors.append(f"{filename} seed {seed} must use one selected bin")
        else:
            selected_result[seed] = next(iter(selected_values))
        test_values = test_hours_by_seed.get(seed, set())
        if len(test_values) != 1:
            errors.append(f"{filename} seed {seed} must use one test_hours value")
        else:
            test_hours_result[seed] = next(iter(test_values))
    return selected_result, test_hours_result


def _validate_selection_folds(
    result_dir: Path,
    seeds: list[int],
    candidates: list[int],
    errors: list[str],
) -> None:
    filename = "model_selection_folds.csv"
    rows = _read_table(
        result_dir,
        filename,
        ("seed", "n_bins", "fold", "model"),
        errors,
    )
    actual: set[tuple[int, int, int, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        if not (row.get("seed") or "").strip():
            continue
        seed = _csv_integer(
            row.get("seed"), f"{filename} line {row_number} seed", errors
        )
        candidate = _csv_integer(
            row.get("n_bins"), f"{filename} line {row_number} n_bins", errors
        )
        fold = _csv_integer(
            row.get("fold"), f"{filename} line {row_number} fold", errors
        )
        model = (row.get("model") or "").strip()
        if seed is None or candidate is None or fold is None:
            continue
        key = (seed, candidate, fold, model)
        if key in actual:
            errors.append(f"{filename} duplicates selection row: {key}")
        actual.add(key)

    expected = set(
        product(seeds, candidates, EXPECTED_SELECTION_FOLDS, EXPECTED_SELECTION_MODELS)
    )
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(
            f"{filename} is missing {len(missing)} selection combinations; "
            f"first: {missing[:3]}"
        )
    if extra:
        errors.append(
            f"{filename} has {len(extra)} unexpected selection combinations; "
            f"first: {extra[:3]}"
        )


def _validate_diagnostics(
    result_dir: Path,
    seeds: list[int],
    candidates: list[int],
    synthetic_hours: int | None,
    train_fraction: float | None,
    metrics_selected: dict[int, int],
    metrics_test_hours: dict[int, int],
    errors: list[str],
) -> None:
    filename = "case_diagnostics.csv"
    rows = _read_table(
        result_dir,
        filename,
        ("seed", "observations", "train_hours", "test_hours", "selected_bins"),
        errors,
    )
    diagnostics: dict[int, tuple[int, int, int, int]] = {}
    for row_number, row in enumerate(rows, start=2):
        if not (row.get("seed") or "").strip():
            continue
        seed = _csv_integer(
            row.get("seed"), f"{filename} line {row_number} seed", errors
        )
        observations = _csv_integer(
            row.get("observations"),
            f"{filename} line {row_number} observations",
            errors,
        )
        train_hours = _csv_integer(
            row.get("train_hours"),
            f"{filename} line {row_number} train_hours",
            errors,
        )
        test_hours = _csv_integer(
            row.get("test_hours"),
            f"{filename} line {row_number} test_hours",
            errors,
        )
        selected = _csv_integer(
            row.get("selected_bins"),
            f"{filename} line {row_number} selected_bins",
            errors,
        )
        if None in (seed, observations, train_hours, test_hours, selected):
            continue
        assert seed is not None
        if seed in diagnostics:
            errors.append(f"{filename} duplicates synthetic seed {seed}")
        diagnostics[seed] = (observations, train_hours, test_hours, selected)

    if set(diagnostics) != set(seeds):
        errors.append(
            f"{filename} seed coverage mismatch: expected {seeds}, "
            f"found {sorted(diagnostics)}"
        )
    for seed, (observations, train_hours, test_hours, selected) in diagnostics.items():
        if synthetic_hours is not None and observations != synthetic_hours:
            errors.append(
                f"{filename} seed {seed} observations {observations} disagree with "
                f"manifest {synthetic_hours}"
            )
        if train_hours + test_hours != observations:
            errors.append(f"{filename} seed {seed} train/test hours do not sum")
        if train_fraction is not None:
            expected_train = int(observations * train_fraction)
            if train_hours != expected_train:
                errors.append(
                    f"{filename} seed {seed} train_hours {train_hours} disagree with "
                    f"fraction-derived {expected_train}"
                )
        if selected not in candidates:
            errors.append(f"{filename} seed {seed} selected bin is not a candidate")
        if metrics_selected.get(seed) != selected:
            errors.append(f"{filename} seed {seed} selected bin disagrees with metrics")
        if metrics_test_hours.get(seed) != test_hours:
            errors.append(f"{filename} seed {seed} test_hours disagrees with metrics")


def _validate_reported_seed_counts(
    result_dir: Path, expected_count: int, errors: list[str]
) -> None:
    for filename in ("synthetic_summary.csv", "paired_seed_comparisons.csv"):
        rows = _read_table(result_dir, filename, ("seeds",), errors)
        for row_number, row in enumerate(rows, start=2):
            count = _csv_integer(
                row.get("seeds"), f"{filename} line {row_number} seeds", errors
            )
            if count is not None and count != expected_count:
                errors.append(
                    f"{filename} line {row_number} reports {count} seeds; "
                    f"expected {expected_count}"
                )


def verify_experiment_contract(manifest_path: Path) -> list[str]:
    """Return semantic contract errors for one published result bundle."""

    manifest = _load_manifest(manifest_path)
    errors: list[str] = []
    seeds, candidates, synthetic_hours, train_fraction, _ = _validate_configuration(
        manifest, errors
    )
    result_dir = manifest_path.parent
    metrics_selected, metrics_test_hours = _validate_metrics(
        result_dir, seeds, candidates, errors
    )
    _validate_selection_folds(result_dir, seeds, candidates, errors)
    _validate_diagnostics(
        result_dir,
        seeds,
        candidates,
        synthetic_hours,
        train_fraction,
        metrics_selected,
        metrics_test_hours,
        errors,
    )
    _validate_reported_seed_counts(result_dir, len(seeds), errors)
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        errors = verify_experiment_contract(args.manifest)
        manifest = _load_manifest(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Experiment contract verification failed: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"Experiment contract verification failed: {error}", file=sys.stderr)
        return 1
    seeds = manifest["synthetic_seeds"]
    candidates = manifest["candidate_bins"]
    print(
        f"Verified experiment contract for {len(seeds)} seeds, "
        f"{len(candidates)} candidates, and {len(REQUIRED_RESULT_TABLES)} tables."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
