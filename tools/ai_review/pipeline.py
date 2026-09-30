"""Safety bridge from repository change extraction to Lola dispatch planning."""

from dataclasses import dataclass
from typing import Tuple

from .change_extractor import ChangeExtractionResult
from .dispatch import FULL_GATES, build_dispatch_plan


@dataclass(frozen=True)
class PipelinePlan:
    status: str
    gates: Tuple[str, ...] = ()
    risk: str = "LOW"
    lightweight_allowed: bool = False
    control_plane_change: bool = False
    reviewed_sha: str = ""
    base_sha: str = ""
    uncertainties: Tuple[str, ...] = ()


def plan_extracted_change(extraction: ChangeExtractionResult) -> PipelinePlan:
    """Translate extraction state into a dispatch plan without losing uncertainty.

    Any extraction uncertainty escalates to HIGH/full review. Uncertainty can
    never be interpreted as evidence that a change is documentation-only.
    """
    change_set = extraction.change_set
    reviewed_sha = change_set.reviewed_sha.strip()
    base_sha = change_set.base_sha.strip()

    if extraction.status == "UNBOUND" or not reviewed_sha:
        return PipelinePlan("UNBOUND", reviewed_sha=reviewed_sha, base_sha=base_sha)

    if extraction.status == "NO_ACTION":
        return PipelinePlan("NO_ACTION", reviewed_sha=reviewed_sha, base_sha=base_sha)

    if extraction.status == "EXTRACTED_WITH_UNCERTAINTY":
        return PipelinePlan(
            "DISPATCH_REVIEW",
            gates=FULL_GATES,
            risk="HIGH",
            lightweight_allowed=False,
            reviewed_sha=reviewed_sha,
            base_sha=base_sha,
            uncertainties=tuple(extraction.uncertainties),
        )

    if extraction.status != "EXTRACTED":
        return PipelinePlan("INVALID", reviewed_sha=reviewed_sha, base_sha=base_sha)

    dispatch = build_dispatch_plan(change_set)
    return PipelinePlan(
        dispatch.status,
        gates=dispatch.gates,
        risk=dispatch.risk,
        lightweight_allowed=dispatch.status == "DISPATCH_LIGHTWEIGHT",
        control_plane_change=dispatch.control_plane_change,
        reviewed_sha=dispatch.reviewed_sha,
        base_sha=dispatch.base_sha,
    )
