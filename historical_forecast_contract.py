"""Verify causal timing and aggregates for VoltRL historical forecasts."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

DETAIL_FILE = "historical_forecast_detail.csv"
SUMMARY_FILE = "historical_forecast_summary.csv"
MARKET_FILE = "real_market_metrics.csv"
REQUIRED_OUTPUTS = (DETAIL_FILE, SUMMARY_FILE, MARKET_FILE)
EXPECTED_LEADS = frozenset(range(1, 25))


@dataclass(frozen=True)
class ForecastRow:
    line: int
    case: str
    method: str
    available: datetime
    protocol: str
    delivery: datetime
    lead: int
    forecast: float
    realized: float
    error: float


@dataclass(frozen=True)
class ForecastSummary:
    line: int
    observations: int
    mean_error: float
    mean_absolute_error: float
    root_mean_squared_error: float


@dataclass(frozen=True)
class AuditCounts:
    rows: int = 0
    cases: int = 0
    methods: int = 0
    blocks: int = 0


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
        errors.append(f"missing historical forecast table: {path.name}")
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
    return value.strip()


def _finite_float(
    value: str | None,
    label: str,
    errors: list[str],
) -> float | None:
    try:
        number = float(value) if value is not None else math.nan
    except ValueError:
        number = math.nan
    if not math.isfinite(number):
        errors.append(f"{label} must be a finite number, found {value!r}")
        return None
    return number


def _integer(value: str | None, label: str, errors: list[str]) -> int | None:
    number = _finite_float(value, label, errors)
    if number is None:
        return None
    if not number.is_integer():
        errors.append(f"{label} must be an integer, found {value!r}")
        return None
    return int(number)


def _timestamp(
    value: str | None,
    label: str,
    errors: list[str],
) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value) if value is not None else None
    except ValueError:
        parsed = None
    if parsed is None:
        errors.append(f"{label} must be an ISO 8601 timestamp, found {value!r}")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{label} must include a UTC offset")
        return None
    return parsed


def _close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def _parse_detail(
    rows: list[dict[str, str]],
    errors: list[str],
) -> list[ForecastRow]:
    parsed: list[ForecastRow] = []
    seen: dict[tuple[str, str, datetime], int] = {}
    for position, row in enumerate(rows, start=2):
        label = f"{DETAIL_FILE} row {position}"
        case = _nonempty(row.get("case"), f"{label} case", errors)
        method = _nonempty(
            row.get("forecast_method"), f"{label} forecast_method", errors
        )
        protocol = _nonempty(
            row.get("commitment_protocol"),
            f"{label} commitment_protocol",
            errors,
        )
        available = _timestamp(
            row.get("information_available_through_delivery_timestamp"),
            f"{label} information timestamp",
            errors,
        )
        delivery = _timestamp(
            row.get("delivery_timestamp"),
            f"{label} delivery_timestamp",
            errors,
        )
        lead = _integer(row.get("lead_hour"), f"{label} lead_hour", errors)
        forecast = _finite_float(
            row.get("forecast_price"), f"{label} forecast_price", errors
        )
        realized = _finite_float(
            row.get("realized_price"), f"{label} realized_price", errors
        )
        stated_error = _finite_float(row.get("error"), f"{label} error", errors)
        if None in (
            case,
            method,
            protocol,
            available,
            delivery,
            lead,
            forecast,
            realized,
            stated_error,
        ):
            continue

        assert isinstance(case, str)
        assert isinstance(method, str)
        assert isinstance(protocol, str)
        assert isinstance(available, datetime)
        assert isinstance(delivery, datetime)
        assert isinstance(lead, int)
        assert isinstance(forecast, float)
        assert isinstance(realized, float)
        assert isinstance(stated_error, float)

        if lead not in EXPECTED_LEADS:
            errors.append(f"{label} lead_hour must lie in [1, 24], found {lead}")
        elapsed_hours = (delivery - available).total_seconds() / 3600.0
        if elapsed_hours <= 0.0:
            errors.append(f"{label} uses information at or after delivery")
        if not _close(elapsed_hours, float(lead)):
            errors.append(
                f"{label} lead_hour {lead} disagrees with its "
                f"{elapsed_hours:g}-hour timestamp interval"
            )
        if not _close(stated_error, forecast - realized):
            errors.append(
                f"{label} error {stated_error:g} does not equal forecast minus "
                f"realized price ({forecast - realized:g})"
            )

        key = (case, method, delivery)
        if key in seen:
            errors.append(
                f"{label} duplicates case/method/delivery row from line {seen[key]}"
            )
        else:
            seen[key] = position
        parsed.append(
            ForecastRow(
                line=position,
                case=case,
                method=method,
                available=available,
                protocol=protocol,
                delivery=delivery,
                lead=lead,
                forecast=forecast,
                realized=realized,
                error=stated_error,
            )
        )
    return parsed


def _parse_summaries(
    rows: list[dict[str, str]],
    errors: list[str],
) -> dict[tuple[str, str], ForecastSummary]:
    summaries: dict[tuple[str, str], ForecastSummary] = {}
    for position, row in enumerate(rows, start=2):
        label = f"{SUMMARY_FILE} row {position}"
        case = _nonempty(row.get("case"), f"{label} case", errors)
        method = _nonempty(
            row.get("forecast_method"), f"{label} forecast_method", errors
        )
        observations = _integer(
            row.get("observations"), f"{label} observations", errors
        )
        mean_error = _finite_float(
            row.get("mean_error"), f"{label} mean_error", errors
        )
        mean_absolute_error = _finite_float(
            row.get("mean_absolute_error"),
            f"{label} mean_absolute_error",
            errors,
        )
        root_mean_squared_error = _finite_float(
            row.get("root_mean_squared_error"),
            f"{label} root_mean_squared_error",
            errors,
        )
        if None in (
            case,
            method,
            observations,
            mean_error,
            mean_absolute_error,
            root_mean_squared_error,
        ):
            continue

        assert isinstance(case, str)
        assert isinstance(method, str)
        assert isinstance(observations, int)
        assert isinstance(mean_error, float)
        assert isinstance(mean_absolute_error, float)
        assert isinstance(root_mean_squared_error, float)
        if observations < 1:
            errors.append(f"{label} observations must be positive")
        if mean_absolute_error < 0.0:
            errors.append(f"{label} mean_absolute_error must be nonnegative")
        if root_mean_squared_error < 0.0:
            errors.append(f"{label} root_mean_squared_error must be nonnegative")

        key = (case, method)
        if key in summaries:
            errors.append(f"{label} duplicates summary for {case}/{method}")
            continue
        summaries[key] = ForecastSummary(
            line=position,
            observations=observations,
            mean_error=mean_error,
            mean_absolute_error=mean_absolute_error,
            root_mean_squared_error=root_mean_squared_error,
        )
    return summaries


def _validate_blocks_and_alignment(
    details: list[ForecastRow],
    errors: list[str],
) -> tuple[dict[tuple[str, str], list[ForecastRow]], int]:
    groups: dict[tuple[str, str], list[ForecastRow]] = defaultdict(list)
    blocks: dict[tuple[str, str, datetime], list[ForecastRow]] = defaultdict(list)
    delivery_sets: dict[tuple[str, str], set[datetime]] = defaultdict(set)
    aligned: dict[tuple[str, datetime], ForecastRow] = {}
    protocols: dict[str, set[str]] = defaultdict(set)

    for row in details:
        key = (row.case, row.method)
        groups[key].append(row)
        blocks[(row.case, row.method, row.available)].append(row)
        delivery_sets[key].add(row.delivery)
        protocols[row.case].add(row.protocol)

        alignment_key = (row.case, row.delivery)
        baseline = aligned.get(alignment_key)
        if baseline is None:
            aligned[alignment_key] = row
        else:
            if not _close(row.realized, baseline.realized):
                errors.append(
                    f"{DETAIL_FILE} line {row.line} realized price disagrees across "
                    f"methods for {row.case} at {row.delivery.isoformat()}"
                )
            if row.available != baseline.available or row.lead != baseline.lead:
                errors.append(
                    f"{DETAIL_FILE} line {row.line} forecast timing disagrees across "
                    f"methods for {row.case} at {row.delivery.isoformat()}"
                )

    for case, values in sorted(protocols.items()):
        if len(values) != 1:
            errors.append(
                f"{DETAIL_FILE} uses {len(values)} commitment protocols for {case}"
            )

    for (case, method, available), block_rows in sorted(blocks.items()):
        leads = {row.lead for row in block_rows}
        if len(block_rows) != 24 or leads != EXPECTED_LEADS:
            missing = sorted(EXPECTED_LEADS - leads)
            extra = sorted(leads - EXPECTED_LEADS)
            errors.append(
                f"incomplete 24-hour forecast block for {case}/{method} after "
                f"{available.isoformat()}: {len(block_rows)} rows, "
                f"missing leads {missing}, extra leads {extra}"
            )

    methods_by_case: dict[str, list[str]] = defaultdict(list)
    for case, method in groups:
        methods_by_case[case].append(method)
    for case, methods in sorted(methods_by_case.items()):
        baseline_method = sorted(methods)[0]
        baseline = delivery_sets[(case, baseline_method)]
        for method in sorted(methods)[1:]:
            deliveries = delivery_sets[(case, method)]
            if deliveries != baseline:
                errors.append(
                    f"delivery coverage mismatch for {case}/{method}: "
                    f"missing {len(baseline - deliveries)}, extra "
                    f"{len(deliveries - baseline)} versus {baseline_method}"
                )
    return groups, len(blocks)


def _validate_summaries(
    groups: dict[tuple[str, str], list[ForecastRow]],
    summaries: dict[tuple[str, str], ForecastSummary],
    errors: list[str],
) -> None:
    group_keys = set(groups)
    summary_keys = set(summaries)
    for case, method in sorted(group_keys - summary_keys):
        errors.append(f"missing forecast summary for {case}/{method}")
    for case, method in sorted(summary_keys - group_keys):
        errors.append(f"forecast summary has no detail rows for {case}/{method}")

    for key in sorted(group_keys & summary_keys):
        rows = groups[key]
        summary = summaries[key]
        count = len(rows)
        mean_error = math.fsum(row.error for row in rows) / count
        mean_absolute_error = math.fsum(abs(row.error) for row in rows) / count
        root_mean_squared_error = math.sqrt(
            math.fsum(row.error * row.error for row in rows) / count
        )
        case, method = key
        if summary.observations != count:
            errors.append(
                f"summary observations for {case}/{method} are "
                f"{summary.observations}; recomputed {count}"
            )
        comparisons = (
            ("mean_error", summary.mean_error, mean_error),
            (
                "mean_absolute_error",
                summary.mean_absolute_error,
                mean_absolute_error,
            ),
            (
                "root_mean_squared_error",
                summary.root_mean_squared_error,
                root_mean_squared_error,
            ),
        )
        for field, stated, recomputed in comparisons:
            if not _close(stated, recomputed):
                errors.append(
                    f"summary {field} for {case}/{method} is {stated:g}; "
                    f"recomputed {recomputed:g}"
                )


def _validate_market_linkage(
    rows: list[dict[str, str]],
    groups: dict[tuple[str, str], list[ForecastRow]],
    errors: list[str],
) -> None:
    market_hours: dict[str, set[int]] = defaultdict(set)
    market_protocols: dict[str, set[str]] = defaultdict(set)
    for position, row in enumerate(rows, start=2):
        label = f"{MARKET_FILE} row {position}"
        case = _nonempty(row.get("case"), f"{label} case", errors)
        hours = _integer(row.get("test_hours"), f"{label} test_hours", errors)
        protocol = _nonempty(
            row.get("information_protocol"),
            f"{label} information_protocol",
            errors,
        )
        if case is None or hours is None or protocol is None:
            continue
        if hours < 1:
            errors.append(f"{label} test_hours must be positive")
        market_hours[case].add(hours)
        market_protocols[case].add(protocol)

    detail_cases = {case for case, _ in groups}
    market_cases = set(market_hours)
    for case in sorted(detail_cases - market_cases):
        errors.append(f"real-market metrics are missing forecast case {case}")
    for case in sorted(market_cases - detail_cases):
        errors.append(f"real-market metrics case has no forecasts: {case}")
    for case in sorted(market_cases):
        if len(market_hours[case]) != 1:
            errors.append(f"real-market metrics disagree on test_hours for {case}")
        if len(market_protocols[case]) != 1:
            errors.append(
                f"real-market metrics use multiple information protocols for {case}"
            )
    for (case, method), detail_rows in sorted(groups.items()):
        hours = market_hours.get(case)
        if hours is not None and len(hours) == 1:
            expected = next(iter(hours))
            if len(detail_rows) != expected:
                errors.append(
                    f"forecast detail for {case}/{method} has {len(detail_rows)} "
                    f"rows; real-market metrics report {expected} test_hours"
                )


def _audit_historical_forecasts(
    manifest_path: Path,
) -> tuple[list[str], AuditCounts]:
    manifest = _load_manifest(manifest_path)
    errors: list[str] = []
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list) or not all(
        isinstance(output, str) for output in outputs
    ):
        errors.append("manifest outputs must be a path list")
    else:
        missing = sorted(set(REQUIRED_OUTPUTS) - set(outputs))
        if missing:
            errors.append(
                "manifest outputs omit historical forecast tables: "
                + ", ".join(missing)
            )
    protocol = manifest.get("historical_information_protocol")
    if not isinstance(protocol, str) or not protocol.strip():
        errors.append("historical_information_protocol must be a nonempty string")

    result_dir = manifest_path.parent
    detail_rows = _read_table(
        result_dir / DETAIL_FILE,
        (
            "case",
            "forecast_method",
            "information_available_through_delivery_timestamp",
            "commitment_protocol",
            "delivery_timestamp",
            "lead_hour",
            "forecast_price",
            "realized_price",
            "error",
        ),
        errors,
    )
    summary_rows = _read_table(
        result_dir / SUMMARY_FILE,
        (
            "case",
            "forecast_method",
            "observations",
            "mean_error",
            "mean_absolute_error",
            "root_mean_squared_error",
        ),
        errors,
    )
    market_rows = _read_table(
        result_dir / MARKET_FILE,
        ("case", "test_hours", "information_protocol"),
        errors,
    )

    details = _parse_detail(detail_rows, errors)
    summaries = _parse_summaries(summary_rows, errors)
    groups, block_count = _validate_blocks_and_alignment(details, errors)
    _validate_summaries(groups, summaries, errors)
    _validate_market_linkage(market_rows, groups, errors)
    counts = AuditCounts(
        rows=len(details),
        cases=len({case for case, _ in groups}),
        methods=len({method for _, method in groups}),
        blocks=block_count,
    )
    return errors, counts


def verify_historical_forecast_contract(manifest_path: Path) -> list[str]:
    """Return historical forecast contract errors; empty means a valid bundle."""

    errors, _ = _audit_historical_forecasts(manifest_path)
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        errors, counts = _audit_historical_forecasts(args.manifest)
    except (OSError, ValueError, csv.Error, json.JSONDecodeError) as error:
        print(f"Historical forecast verification failed: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"Historical forecast verification failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Verified {counts.rows} forecast rows across {counts.cases} cases, "
        f"{counts.methods} methods, and {counts.blocks} fixed forecast blocks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
