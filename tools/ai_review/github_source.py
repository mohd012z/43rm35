"""GitHub PR source completeness manifest for Lola advisory ingestion."""

from dataclasses import dataclass
from typing import Optional, Tuple

from .pr_ingest import PRFile, PRSnapshot


@dataclass(frozen=True)
class SourceFile:
    path: str
    patch: Optional[str] = None


@dataclass(frozen=True)
class GitHubPRSource:
    pr_number: int
    base_sha: str
    head_sha: str
    declared_changed_files: int
    files: Tuple[SourceFile, ...] = ()


@dataclass(frozen=True)
class SourceManifest:
    expected_files: int
    observed_files: int
    missing_patches: Tuple[str, ...] = ()
    duplicate_paths: Tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceManifestResult:
    status: str
    snapshot: PRSnapshot
    manifest: SourceManifest


def build_source_manifest(source: GitHubPRSource) -> SourceManifestResult:
    """Build a PR snapshot while proving the changed-file inventory is complete."""
    head = source.head_sha.strip()
    base = source.base_sha.strip()
    paths = tuple(item.path.replace("\\", "/").strip() for item in source.files if item.path.strip())

    counts = {}
    for path in paths:
        counts[path] = counts.get(path, 0) + 1
    duplicates = tuple(path for path, count in counts.items() if count > 1)
    missing_patches = tuple(
        item.path.replace("\\", "/").strip()
        for item in source.files
        if item.path.strip() and item.patch is None
    )

    snapshot = PRSnapshot(
        number=source.pr_number,
        base_sha=base,
        head_sha=head,
        files=tuple(PRFile(item.path.replace("\\", "/").strip(), item.patch) for item in source.files if item.path.strip()),
    )
    manifest = SourceManifest(
        expected_files=source.declared_changed_files,
        observed_files=len(paths),
        missing_patches=missing_patches,
        duplicate_paths=duplicates,
    )

    if not head:
        return SourceManifestResult("UNBOUND", snapshot, manifest)
    if duplicates:
        return SourceManifestResult("SOURCE_INVALID", snapshot, manifest)
    if source.declared_changed_files != len(paths) or missing_patches:
        return SourceManifestResult("SOURCE_INCOMPLETE", snapshot, manifest)
    return SourceManifestResult("SOURCE_COMPLETE", snapshot, manifest)
