"""Validate the version and checksum of a benchmark input dataset."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from artifact_integrity import sha256_file

DEFAULT_SOURCE_RECORD = Path(__file__).resolve().parent / "data" / "opsd_source.json"
REQUIRED_FIELDS = ("dataset", "version", "doi", "url", "filename", "sha256")
SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}")


@dataclass(frozen=True)
class SourceVerification:
    """Verified identity and provenance metadata for an input file."""

    path: Path
    bytes: int
    sha256: str
    dataset: str
    version: str
    doi: str
    url: str


def load_source_record(record_path: Path) -> dict[str, str]:
    """Load and validate a machine-readable source provenance record."""

    record = json.loads(record_path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("source record root must be a JSON object")

    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"source record field {field!r} must be a nonempty string")

    filename = record["filename"]
    if filename in {".", ".."} or "/" in filename or "\\" in filename:
        raise ValueError("source record filename must be a canonical base name")
    if SHA256_PATTERN.fullmatch(record["sha256"]) is None:
        raise ValueError(
            "source record sha256 must contain exactly 64 hexadecimal digits"
        )

    return {field: record[field] for field in REQUIRED_FIELDS}


def verify_source_file(
    source_path: Path, record_path: Path = DEFAULT_SOURCE_RECORD
) -> SourceVerification:
    """Verify an input file against its versioned provenance record."""

    record = load_source_record(record_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"source file is missing: {source_path}")
    if source_path.name != record["filename"]:
        raise ValueError(
            "source filename mismatch: "
            f"expected {record['filename']!r}, found {source_path.name!r}"
        )

    actual_sha256 = sha256_file(source_path)
    expected_sha256 = record["sha256"].lower()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "source SHA-256 mismatch: "
            f"expected {expected_sha256}, found {actual_sha256}"
        )

    return SourceVerification(
        path=source_path,
        bytes=source_path.stat().st_size,
        sha256=actual_sha256,
        dataset=record["dataset"],
        version=record["version"],
        doi=record["doi"],
        url=record["url"],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Downloaded source file to verify")
    parser.add_argument(
        "--record",
        type=Path,
        default=DEFAULT_SOURCE_RECORD,
        help="Machine-readable provenance record",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        verification = verify_source_file(args.source, args.record)
    except (OSError, ValueError) as error:
        print(f"Input verification failed: {error}", file=sys.stderr)
        return 1

    print(
        f"Verified {verification.path.name}: {verification.bytes} bytes, "
        f"SHA-256 {verification.sha256}, {verification.dataset} "
        f"version {verification.version}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
