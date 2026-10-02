"""Fail-closed decision gate for Lola + Kernel AI + in_ai advisory results.

Agent assessments are advisory signals only. Independent evidence status is
always authoritative for the gate.
"""

EVIDENCE_STATES = {
    "VERIFIED_TRUE",
    "VERIFIED_FALSE",
    "CONTRADICTED",
    "INSUFFICIENT_EVIDENCE",
    "STALE",
    "UNKNOWN",
    "ERROR",
}

AGENT_STATES = {"TRUE", "FALSE", "UNKNOWN", "DISPUTE"}


def decide(*, lola: str, kernel_ai: str, in_ai: str, evidence_status: str) -> str:
    """Return the fail-closed verification state for a proposed action.

    A VERIFIED_TRUE result is allowed only when independent evidence is
    VERIFIED_TRUE *and* all three advisory agents agree on TRUE. Evidence
    failures or uncertainty are returned unchanged so callers can map them to
    block/review/reanalyze actions.
    """
    agents = (lola, kernel_ai, in_ai)
    if any(state not in AGENT_STATES for state in agents):
        return "ERROR"
    if evidence_status not in EVIDENCE_STATES:
        return "ERROR"

    if evidence_status != "VERIFIED_TRUE":
        return evidence_status

    if agents != ("TRUE", "TRUE", "TRUE"):
        return "UNKNOWN"

    return "VERIFIED_TRUE"
