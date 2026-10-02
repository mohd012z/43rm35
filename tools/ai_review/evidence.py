"""Independent, fail-closed evidence verification for AI advisory decisions."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class EvidenceBundle:
    """Evidence captured for one exact repository snapshot."""

    reviewed_sha: str
    current_sha: str
    file_hashes_verified: bool
    tests_executed: bool
    tests_passed: bool
    contradictions: Tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationResult:
    """Derived verification state; agents do not set this value directly."""

    status: str
    reviewed_sha: str
    current_sha: str
    contradictions: Tuple[str, ...] = ()


def verify_evidence(bundle: EvidenceBundle) -> VerificationResult:
    """Derive a fail-closed verification state from concrete evidence.

    Precedence matters: evidence from a different snapshot is stale; explicit
    counter-evidence contradicts the claim; missing integrity/test execution is
    insufficient; an executed failing test verifies false; only complete,
    matching, passing evidence verifies true.
    """
    if not bundle.reviewed_sha or not bundle.current_sha:
        status = "INSUFFICIENT_EVIDENCE"
    elif bundle.reviewed_sha != bundle.current_sha:
        status = "STALE"
    elif bundle.contradictions:
        status = "CONTRADICTED"
    elif not bundle.file_hashes_verified or not bundle.tests_executed:
        status = "INSUFFICIENT_EVIDENCE"
    elif not bundle.tests_passed:
        status = "VERIFIED_FALSE"
    else:
        status = "VERIFIED_TRUE"

    return VerificationResult(
        status=status,
        reviewed_sha=bundle.reviewed_sha,
        current_sha=bundle.current_sha,
        contradictions=tuple(bundle.contradictions),
    )
