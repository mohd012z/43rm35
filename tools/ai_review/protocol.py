"""Structured pre-action review contract for Lola advisory."""

from dataclasses import dataclass
from typing import Tuple


VALID_RISKS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


@dataclass(frozen=True)
class PreActionReview:
    """Lola's structured answer to: what am I actually about to do?"""

    intent: str
    actual_operation: str
    reviewed_sha: str
    affected_files: Tuple[str, ...] = ()
    affected_functions: Tuple[str, ...] = ()
    downstream_impacts: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()
    missing_evidence: Tuple[str, ...] = ()
    proposed_action: str = ""
    reversible: bool = True
    risk: str = "LOW"


@dataclass(frozen=True)
class ProtocolValidation:
    status: str
    missing_fields: Tuple[str, ...] = ()
    missing_evidence: Tuple[str, ...] = ()


def validate_pre_action_review(review: PreActionReview) -> ProtocolValidation:
    """Validate that a pre-action review is sufficiently specified to reanalyze.

    The packet is fail-closed: it must be bound to a repository SHA, identify
    the actual operation and impact map, and preserve any declared evidence
    gaps rather than allowing them to disappear into an agent conclusion.
    """
    if review.risk.upper() not in VALID_RISKS:
        return ProtocolValidation("INVALID")

    if not review.reviewed_sha.strip():
        return ProtocolValidation("UNBOUND")

    missing = []
    if not review.intent.strip():
        missing.append("intent")
    if not review.actual_operation.strip():
        missing.append("actual_operation")
    if not review.proposed_action.strip():
        missing.append("proposed_action")
    if not (review.affected_files or review.affected_functions or review.downstream_impacts):
        missing.append("impact_map")

    if missing:
        return ProtocolValidation("INCOMPLETE", tuple(missing), tuple(review.missing_evidence))

    if review.missing_evidence:
        return ProtocolValidation(
            "NEEDS_EVIDENCE",
            (),
            tuple(review.missing_evidence),
        )

    return ProtocolValidation("READY_FOR_REANALYSIS")
