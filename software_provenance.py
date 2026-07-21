"""Capture and verify the exact source snapshot behind benchmark results."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Sequence

DEFAULT_SOFTWARE_PATHS = (
    "voltrl.py",
    "voltrl_benchmark.py",
    "requirements.txt",
)
GIT_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40,64}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _source_path(source_root: Path, relative_path: str) -> Path:
    if not relative_path or "\\" in relative_path or ":" in relative_path:
        raise ValueError(
            f"source path must use canonical POSIX form: {relative_path!r}"
        )
    pure_path = PurePosixPath(relative_path)
    if (
        pure_path.is_absolute()
        or ".." in pure_path.parts
        or pure_path.as_posix() != relative_path
    ):
        raise ValueError(
            f"source path must stay below the repository root: {relative_path}"
        )

    resolved_root = source_root.resolve()
    resolved_path = resolved_root.joinpath(*pure_path.parts).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            f"source path must stay below the repository root: {relative_path}"
        ) from error
    return resolved_path


def _run_git(source_root: Path, *arguments: str) -> bytes:
    try:
        process = subprocess.run(
            ["git", "-C", str(source_root), *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise ValueError("git executable is unavailable") from error
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(detail or f"git {' '.join(arguments)} failed")
    return process.stdout


def _current_commit(source_root: Path) -> str | None:
    try:
        commit = _run_git(source_root, "rev-parse", "--verify", "HEAD^{commit}")
    except ValueError:
        return None
    decoded = commit.decode("ascii", errors="strict").strip().lower()
    if GIT_COMMIT_PATTERN.fullmatch(decoded) is None:
        raise ValueError(f"git returned an invalid commit identifier: {decoded!r}")
    return decoded


def _git_blob(source_root: Path, commit: str, relative_path: str) -> bytes:
    _source_path(source_root, relative_path)
    return _run_git(source_root, "cat-file", "blob", f"{commit}:{relative_path}")


def _software_record(relative_path: str, content: bytes) -> dict[str, object]:
    return {
        "path": relative_path,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def capture_software_provenance(
    source_root: Path,
    relative_paths: Sequence[str] = DEFAULT_SOFTWARE_PATHS,
) -> dict[str, object]:
    """Capture a portable source inventory and its Git state when available."""

    if len(relative_paths) != len(set(relative_paths)):
        raise ValueError("software source paths contain duplicates")
    source_paths = [
        (relative_path, _source_path(source_root, relative_path))
        for relative_path in relative_paths
    ]
    for relative_path, source_path in source_paths:
        if not source_path.is_file():
            raise FileNotFoundError(f"software source is missing: {relative_path}")

    commit = _current_commit(source_root)
    dirty: bool | None = None
    if commit is not None:
        status = _run_git(
            source_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *relative_paths,
        )
        dirty = bool(status.strip())

    records: list[dict[str, object]] = []
    for relative_path, source_path in source_paths:
        if commit is not None and dirty is False:
            content = _git_blob(source_root, commit, relative_path)
        else:
            content = source_path.read_bytes()
        records.append(_software_record(relative_path, content))

    return {
        "git_commit": commit,
        "git_dirty": dirty,
        "files": records,
    }


def _load_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be a JSON object")
    return manifest


def record_software_provenance(
    manifest_path: Path,
    source_root: Path,
    relative_paths: Sequence[str] = DEFAULT_SOFTWARE_PATHS,
) -> int:
    """Add or replace software provenance in an experiment manifest."""

    manifest = _load_manifest(manifest_path)
    manifest["software_provenance"] = capture_software_provenance(
        source_root, relative_paths
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(relative_paths)


def _validated_provenance(
    manifest: dict[str, object],
) -> tuple[str | None, bool | None, list[dict[str, object]], list[str]]:
    provenance = manifest.get("software_provenance")
    if not isinstance(provenance, dict):
        return None, None, [], ["manifest has no software_provenance object"]

    errors: list[str] = []
    commit = provenance.get("git_commit")
    dirty = provenance.get("git_dirty")
    if commit is not None and (
        not isinstance(commit, str)
        or GIT_COMMIT_PATTERN.fullmatch(commit.lower()) is None
    ):
        errors.append("software_provenance git_commit is invalid")
        commit = None
    elif isinstance(commit, str):
        commit = commit.lower()
    if commit is None:
        if dirty is not None:
            errors.append("git_dirty must be null when git_commit is null")
            dirty = None
    elif not isinstance(dirty, bool):
        errors.append("git_dirty must be a boolean when git_commit is present")
        dirty = None

    files = provenance.get("files")
    if not isinstance(files, list):
        errors.append("software_provenance files must be a list")
        return commit, dirty, [], errors
    return commit, dirty, files, errors


def verify_software_provenance(manifest_path: Path, source_root: Path) -> list[str]:
    """Return source-provenance errors; an empty list means a complete match."""

    manifest = _load_manifest(manifest_path)
    commit, dirty, files, errors = _validated_provenance(manifest)
    records: dict[str, dict[str, object]] = {}
    for position, entry in enumerate(files):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            errors.append(f"software_provenance files[{position}] is not valid")
            continue
        relative_path = entry["path"]
        try:
            _source_path(source_root, relative_path)
        except ValueError as error:
            errors.append(str(error))
            continue
        if relative_path in records:
            errors.append(f"duplicate software source path: {relative_path}")
            continue
        records[relative_path] = entry

    missing_paths = sorted(set(DEFAULT_SOFTWARE_PATHS) - set(records))
    if missing_paths:
        errors.append("missing software source records: " + ", ".join(missing_paths))

    use_git_snapshot = commit is not None and dirty is False
    for relative_path, entry in records.items():
        try:
            if use_git_snapshot:
                content = _git_blob(source_root, commit, relative_path)
            else:
                source_path = _source_path(source_root, relative_path)
                if not source_path.is_file():
                    errors.append(f"missing software source: {relative_path}")
                    continue
                content = source_path.read_bytes()
        except (OSError, ValueError) as error:
            errors.append(f"cannot read software source {relative_path}: {error}")
            continue

        expected_size = entry.get("bytes")
        if (
            isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_size != len(content)
        ):
            errors.append(
                f"size mismatch for software source {relative_path}: "
                f"expected {expected_size}, found {len(content)}"
            )

        expected_hash = entry.get("sha256")
        actual_hash = hashlib.sha256(content).hexdigest()
        if (
            not isinstance(expected_hash, str)
            or SHA256_PATTERN.fullmatch(expected_hash.lower()) is None
            or expected_hash.lower() != actual_hash
        ):
            errors.append(f"SHA-256 mismatch for software source {relative_path}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("."),
        help="Repository containing the recorded Git commit and source files",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="record the current source snapshot before verification",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.write:
            record_software_provenance(args.manifest, args.source_root)
        errors = verify_software_provenance(args.manifest, args.source_root)
        manifest = _load_manifest(args.manifest)
        commit, dirty, files, schema_errors = _validated_provenance(manifest)
        if schema_errors and not errors:
            errors.extend(schema_errors)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Software provenance verification failed: {error}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"Software provenance verification failed: {error}", file=sys.stderr)
        return 1
    source_label = (
        f"commit {commit}"
        if commit is not None and dirty is False
        else "source snapshot"
    )
    print(f"Verified {len(files)} software files from {source_label}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
