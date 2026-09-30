"""Automatic review-plan selection for Lola advisory repository changes."""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Tuple


FULL_GATES = (
    "protocol",
    "reanalysis",
    "falsification",
    "crossfunction",
    "evidence",
    "approval",
)
LIGHTWEIGHT_GATES = ("protocol", "evidence", "approval")
DOC_SUFFIXES = {".md", ".rst", ".txt"}


@dataclass(frozen=True)
class ChangeSet:
    reviewed_sha: str
    base_sha: str
    changed_files: Tuple[str, ...] = ()
    changed_functions: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DispatchPlan:
    status: str
    gates: Tuple[str, ...] = ()
    risk: str = "LOW"
    control_plane_change: bool = False
    reviewed_sha: str = ""
    base_sha: str = ""


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def _is_control_plane(path: str) -> bool:
    normalized = _normalize_repo_path(path)
    return normalized.startswith(".github/workflows/") or normalized in {
        "CODEOWNERS",
        ".github/CODEOWNERS",
    }


def _is_documentation(path: str) -> bool:
    normalized = _normalize_repo_path(path)
    pure = PurePosixPath(normalized)
    return pure.suffix.lower() in DOC_SUFFIXES or "docs" in {part.lower() for part in pure.parts}


def build_dispatch_plan(changes: ChangeSet) -> DispatchPlan:
    """Choose the minimum safe review pipeline without silently skipping risk gates."""
    reviewed_sha = changes.reviewed_sha.strip()
    base_sha = changes.base_sha.strip()
    files = tuple(path.strip() for path in changes.changed_files if path.strip())
    functions = tuple(name.strip() for name in changes.changed_functions if name.strip())

    if not reviewed_sha:
        return DispatchPlan("UNBOUND")

    if not files and not functions:
        return DispatchPlan(
            "NO_ACTION",
            reviewed_sha=reviewed_sha,
            base_sha=base_sha,
        )

    control_plane = any(_is_control_plane(path) for path in files)
    if control_plane:
        return DispatchPlan(
            "DISPATCH_REVIEW",
            FULL_GATES,
            risk="HIGH",
            control_plane_change=True,
            reviewed_sha=reviewed_sha,
            base_sha=base_sha,
        )

    docs_only = bool(files) and not functions and all(_is_documentation(path) for path in files)
    if docs_only:
        return DispatchPlan(
            "DISPATCH_LIGHTWEIGHT",
            LIGHTWEIGHT_GATES,
            risk="LOW",
            reviewed_sha=reviewed_sha,
            base_sha=base_sha,
        )

    return DispatchPlan(
        "DISPATCH_REVIEW",
        FULL_GATES,
        risk="MEDIUM",
        reviewed_sha=reviewed_sha,
        base_sha=base_sha,
    )
