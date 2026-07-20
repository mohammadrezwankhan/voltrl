"""Record and verify cryptographic integrity metadata for benchmark artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Sequence

HASH_CHUNK_BYTES = 1024 * 1024


def _artifact_path(root: Path, relative_path: str) -> Path:
    if not relative_path or "\\" in relative_path:
        raise ValueError(
            f"artifact path must use canonical POSIX form: {relative_path!r}"
        )
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError(
            f"artifact path must stay below the result directory: {relative_path}"
        )

    resolved_root = root.resolve()
    resolved_path = resolved_root.joinpath(*pure_path.parts).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            f"artifact path must stay below the result directory: {relative_path}"
        ) from error
    return resolved_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_artifact_inventory(
    result_dir: Path, relative_paths: Sequence[str]
) -> list[dict[str, object]]:
    """Return deterministic size and SHA-256 records for declared artifacts."""

    inventory: list[dict[str, object]] = []
    seen: set[str] = set()
    for relative_path in relative_paths:
        if relative_path in seen:
            raise ValueError(f"duplicate artifact path: {relative_path}")
        seen.add(relative_path)
        artifact_path = _artifact_path(result_dir, relative_path)
        if not artifact_path.is_file():
            raise FileNotFoundError(f"declared artifact is missing: {relative_path}")
        inventory.append(
            {
                "path": relative_path,
                "bytes": artifact_path.stat().st_size,
                "sha256": sha256_file(artifact_path),
            }
        )
    return inventory


def _load_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be a JSON object")
    return manifest


def _declared_outputs(manifest: dict[str, object]) -> list[str]:
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list) or not all(
        isinstance(item, str) for item in outputs
    ):
        raise ValueError("manifest outputs must be a list of paths")
    if len(outputs) != len(set(outputs)):
        raise ValueError("manifest outputs contain duplicate paths")
    return outputs


def record_artifact_inventory(manifest_path: Path) -> int:
    """Add or replace integrity records for every manifest output."""

    manifest = _load_manifest(manifest_path)
    outputs = _declared_outputs(manifest)
    manifest["artifact_inventory"] = build_artifact_inventory(
        manifest_path.parent, outputs
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(outputs)


def verify_artifact_manifest(manifest_path: Path) -> list[str]:
    """Return integrity errors; an empty list means every artifact matched."""

    manifest = _load_manifest(manifest_path)
    outputs = _declared_outputs(manifest)
    inventory = manifest.get("artifact_inventory")
    if not isinstance(inventory, list):
        return ["manifest has no artifact_inventory list"]

    errors: list[str] = []
    records: dict[str, dict[str, object]] = {}
    for position, entry in enumerate(inventory):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            errors.append(f"artifact_inventory[{position}] is not a valid record")
            continue
        relative_path = entry["path"]
        if relative_path in records:
            errors.append(f"duplicate inventory path: {relative_path}")
            continue
        records[relative_path] = entry

    missing_records = sorted(set(outputs) - set(records))
    extra_records = sorted(set(records) - set(outputs))
    if missing_records:
        errors.append("missing inventory records: " + ", ".join(missing_records))
    if extra_records:
        errors.append("undeclared inventory records: " + ", ".join(extra_records))

    for relative_path in outputs:
        entry = records.get(relative_path)
        if entry is None:
            continue
        try:
            artifact_path = _artifact_path(manifest_path.parent, relative_path)
        except ValueError as error:
            errors.append(str(error))
            continue
        if not artifact_path.is_file():
            errors.append(f"missing artifact: {relative_path}")
            continue

        actual_size = artifact_path.stat().st_size
        expected_size = entry.get("bytes")
        if not isinstance(expected_size, int) or expected_size != actual_size:
            errors.append(
                f"size mismatch for {relative_path}: expected {expected_size}, "
                f"found {actual_size}"
            )

        expected_hash = entry.get("sha256")
        actual_hash = sha256_file(artifact_path)
        if not isinstance(expected_hash, str) or expected_hash != actual_hash:
            errors.append(f"SHA-256 mismatch for {relative_path}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--write",
        action="store_true",
        help="record current sizes and SHA-256 digests before verification",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.write:
            record_artifact_inventory(args.manifest)
        errors = verify_artifact_manifest(args.manifest)
        manifest = _load_manifest(args.manifest)
        artifact_count = len(_declared_outputs(manifest))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Artifact verification failed: {error}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"Artifact verification failed: {error}", file=sys.stderr)
        return 1
    print(f"Verified {artifact_count} artifacts declared by {args.manifest}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
