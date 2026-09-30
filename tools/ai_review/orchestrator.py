"""Fail-closed orchestration of the Lola advisory trust gates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GateSnapshot:
    reviewed_sha: str
    protocol_status: str
    reanalysis_status: str
    falsification_status: str
    crossfunction_status: str
    evidence_status: str
    approval_disposition: str


@dataclass(frozen=True)
class OrchestrationResult:
    status: str
    blocked_at: str = ""
    reviewed_sha: str = ""


def _result(status: str, snapshot: GateSnapshot, blocked_at: str = "") -> OrchestrationResult:
    return OrchestrationResult(status, blocked_at, snapshot.reviewed_sha.strip())


def orchestrate(snapshot: GateSnapshot) -> OrchestrationResult:
    """Evaluate gates in dependency order and never convert uncertainty to approval."""
    if not snapshot.reviewed_sha.strip():
        return _result("INVALID", snapshot, "sha")

    protocol = {
        "READY_FOR_REANALYSIS": None,
        "NEEDS_EVIDENCE": "NEEDS_EVIDENCE",
        "INCOMPLETE": "INVALID",
        "UNBOUND": "INVALID",
        "INVALID": "INVALID",
    }
    if snapshot.protocol_status not in protocol:
        return _result("INVALID", snapshot, "protocol")
    if protocol[snapshot.protocol_status]:
        return _result(protocol[snapshot.protocol_status], snapshot, "protocol")

    reanalysis = {
        "READY_FOR_EVIDENCE": None,
        "AGENT_CONTRADICTION": "CONTRADICTED",
        "NEEDS_EVIDENCE": "NEEDS_EVIDENCE",
        "STALE": "REANALYZE",
        "INVALID": "INVALID",
    }
    if snapshot.reanalysis_status not in reanalysis:
        return _result("INVALID", snapshot, "reanalysis")
    if reanalysis[snapshot.reanalysis_status]:
        return _result(reanalysis[snapshot.reanalysis_status], snapshot, "reanalysis")

    falsification = {
        "SURVIVED_FALSIFICATION": None,
        "CONTRADICTED": "CONTRADICTED",
        "NEEDS_EVIDENCE": "NEEDS_EVIDENCE",
        "INSUFFICIENT_FALSIFICATION": "NEEDS_EVIDENCE",
        "UNBOUND": "INVALID",
    }
    if snapshot.falsification_status not in falsification:
        return _result("INVALID", snapshot, "falsification")
    if falsification[snapshot.falsification_status]:
        return _result(falsification[snapshot.falsification_status], snapshot, "falsification")

    crossfunction = {
        "CROSSFUNCTION_VERIFIED": None,
        "UNRESOLVED_IMPACT": "UNRESOLVED_IMPACT",
        "NEEDS_EVIDENCE": "NEEDS_EVIDENCE",
        "IMPACT_MAP_INCOMPLETE": "NEEDS_EVIDENCE",
        "UNBOUND": "INVALID",
    }
    if snapshot.crossfunction_status not in crossfunction:
        return _result("INVALID", snapshot, "crossfunction")
    if crossfunction[snapshot.crossfunction_status]:
        return _result(crossfunction[snapshot.crossfunction_status], snapshot, "crossfunction")

    evidence = {
        "VERIFIED_TRUE": None,
        "VERIFIED_FALSE": "BLOCKED",
        "CONTRADICTED": "CONTRADICTED",
        "INSUFFICIENT_EVIDENCE": "NEEDS_EVIDENCE",
        "STALE": "REANALYZE",
        "UNKNOWN": "NEEDS_EVIDENCE",
        "ERROR": "BLOCKED",
    }
    if snapshot.evidence_status not in evidence:
        return _result("INVALID", snapshot, "evidence")
    if evidence[snapshot.evidence_status]:
        return _result(evidence[snapshot.evidence_status], snapshot, "evidence")

    approval = {
        "PROCEED_AUTOMATICALLY": "READY_TO_ACT",
        "REQUEST_APPROVAL": "AWAITING_APPROVAL",
        "NO_ACTION": "NO_ACTION",
    }
    status = approval.get(snapshot.approval_disposition)
    if status is None:
        return _result("INVALID", snapshot, "approval")
    return _result(status, snapshot)
