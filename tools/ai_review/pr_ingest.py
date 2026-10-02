"""PR-native adapter from GitHub metadata/patch snapshots to Lola review planning."""

from dataclasses import dataclass
from typing import Optional, Tuple

from .change_extractor import DiffFile, extract_change_set
from .pipeline import PipelinePlan, plan_extracted_change


@dataclass(frozen=True)
class PRFile:
    path: str
    patch: Optional[str] = None


@dataclass(frozen=True)
class PRSnapshot:
    number: int
    base_sha: str
    head_sha: str
    files: Tuple[PRFile, ...] = ()


def ingest_pr_snapshot(snapshot: PRSnapshot) -> PipelinePlan:
    """Convert a PR snapshot into a fail-closed Lola dispatch plan.

    A missing source patch is intentionally preserved as extraction uncertainty,
    which the pipeline escalates to HIGH/full review rather than lightweight.
    """
    extraction = extract_change_set(
        base_sha=snapshot.base_sha,
        reviewed_sha=snapshot.head_sha,
        files=tuple(DiffFile(item.path, item.patch) for item in snapshot.files),
    )
    return plan_extracted_change(extraction)
