"""Run every applicable verifier for one published VoltRL result bundle."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Sequence

from artifact_integrity import verify_artifact_manifest
from experiment_contract import verify_experiment_contract
from historical_forecast_contract import (
    DETAIL_FILE as HISTORICAL_DETAIL_FILE,
    SUMMARY_FILE as HISTORICAL_SUMMARY_FILE,
    verify_historical_forecast_contract,
)
from software_provenance import verify_software_provenance

CheckStatus = Literal["passed", "failed", "skipped"]
Verifier = Callable[[], list[str]]
HISTORICAL_TRIGGER_OUTPUTS = {
    HISTORICAL_DETAIL_FILE,
    HISTORICAL_SUMMARY_FILE,
}


@dataclass(frozen=True)
class AuditCheck:
    """Outcome from one independently runnable bundle verifier."""

    name: str
    status: CheckStatus
    errors: tuple[str, ...] = ()
    detail: str | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "name": self.name,
            "status": self.status,
            "errors": list(self.errors),
        }
        if self.detail is not None:
            result["detail"] = self.detail
        return result


@dataclass(frozen=True)
class BundleAudit:
    """Aggregate result from all checks that apply to a result bundle."""

    manifest: str
    source_root: str
    checks: tuple[AuditCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.status != "failed" for check in self.checks)

    def as_dict(self) -> dict[str, object]:
        return {
            "manifest": self.manifest,
            "source_root": self.source_root,
            "passed": self.passed,
            "checks": [check.as_dict() for check in self.checks],
        }


def _load_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be a JSON object")
    return manifest


def _requires_historical_audit(manifest: dict[str, object]) -> bool:
    outputs = manifest.get("outputs")
    declared = (
        {output for output in outputs if isinstance(output, str)}
        if isinstance(outputs, list)
        else set()
    )
    return (
        "historical_information_protocol" in manifest
        or bool(declared.intersection(HISTORICAL_TRIGGER_OUTPUTS))
    )


def _run_check(name: str, verifier: Verifier) -> AuditCheck:
    try:
        errors = verifier()
    except (OSError, ValueError, csv.Error, subprocess.SubprocessError) as error:
        errors = [str(error)]
    return AuditCheck(
        name=name,
        status="failed" if errors else "passed",
        errors=tuple(errors),
    )


def audit_result_bundle(
    manifest_path: Path,
    source_root: Path | None = None,
) -> BundleAudit:
    """Run semantic, artifact, source, and optional historical checks."""

    manifest_path = manifest_path.resolve()
    manifest = _load_manifest(manifest_path)
    resolved_source_root = (
        source_root.resolve()
        if source_root is not None
        else manifest_path.parent.parent.resolve()
    )

    checks = [
        _run_check(
            "experiment_contract",
            lambda: verify_experiment_contract(manifest_path),
        ),
        _run_check(
            "artifact_integrity",
            lambda: verify_artifact_manifest(manifest_path),
        ),
        _run_check(
            "software_provenance",
            lambda: verify_software_provenance(
                manifest_path,
                resolved_source_root,
            ),
        ),
    ]
    if _requires_historical_audit(manifest):
        checks.append(
            _run_check(
                "historical_forecast_contract",
                lambda: verify_historical_forecast_contract(manifest_path),
            )
        )
    else:
        checks.append(
            AuditCheck(
                name="historical_forecast_contract",
                status="skipped",
                detail="bundle declares no historical forecast protocol or tables",
            )
        )

    return BundleAudit(
        manifest=str(manifest_path),
        source_root=str(resolved_source_root),
        checks=tuple(checks),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--source-root",
        type=Path,
        help="source repository (default: directory above the result bundle)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit a machine-readable audit report",
    )
    return parser


def _print_text_report(report: BundleAudit) -> None:
    for check in report.checks:
        label = check.status.upper()
        suffix = f": {check.detail}" if check.detail else ""
        print(f"{label} {check.name}{suffix}")
        for error in check.errors:
            print(f"  - {error}")
    passed = sum(check.status == "passed" for check in report.checks)
    skipped = sum(check.status == "skipped" for check in report.checks)
    outcome = "passed" if report.passed else "failed"
    print(
        f"Bundle audit {outcome}: {passed} passed, "
        f"{skipped} skipped, {len(report.checks) - passed - skipped} failed."
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = audit_result_bundle(args.manifest, args.source_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        if args.as_json:
            print(
                json.dumps(
                    {
                        "manifest": str(args.manifest),
                        "passed": False,
                        "error": str(error),
                    },
                    indent=2,
                )
            )
        else:
            print(f"Bundle audit failed: {error}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        _print_text_report(report)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
