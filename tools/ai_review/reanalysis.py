"""Independent Lola, Kernel AI, and in_ai reanalysis and contradiction gate."""

from dataclasses import dataclass
from typing import Tuple


EXPECTED_AGENTS = {"LOLA", "KERNEL_AI", "IN_AI"}
VALID_VERDICTS = {"TRUE", "FALSE", "UNKNOWN"}


@dataclass(frozen=True)
class AgentAnalysis:
    agent: str
    reviewed_sha: str
    verdict: str
    reason: str
    evidence_refs: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()
    missing_evidence: Tuple[str, ...] = ()
    counterarguments: Tuple[str, ...] = ()
    proposed_tests: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ReanalysisResult:
    status: str
    consensus: str = ""
    contradictions: Tuple[str, ...] = ()
    missing_evidence: Tuple[str, ...] = ()
    reviewed_sha: str = ""


def reanalyze(*analyses: AgentAnalysis) -> ReanalysisResult:
    """Compare three independent analyses without treating consensus as proof."""
    if len(analyses) != 3:
        return ReanalysisResult("INVALID")

    agents = tuple(item.agent.upper() for item in analyses)
    if len(set(agents)) != 3 or set(agents) != EXPECTED_AGENTS:
        return ReanalysisResult("INVALID")

    verdicts = tuple(item.verdict.upper() for item in analyses)
    if any(verdict not in VALID_VERDICTS for verdict in verdicts):
        return ReanalysisResult("INVALID")

    shas = tuple(item.reviewed_sha.strip() for item in analyses)
    if any(not sha for sha in shas):
        return ReanalysisResult("STALE")
    if len(set(shas)) != 1:
        return ReanalysisResult("STALE")

    missing = tuple(
        f"{item.agent.upper()}:{gap}"
        for item in analyses
        for gap in item.missing_evidence
    )
    if missing:
        return ReanalysisResult(
            "NEEDS_EVIDENCE",
            missing_evidence=missing,
            reviewed_sha=shas[0],
        )

    if len(set(verdicts)) != 1:
        contradictions = tuple(
            f"{item.agent.upper()}:{item.verdict.upper()}" for item in analyses
        )
        return ReanalysisResult(
            "AGENT_CONTRADICTION",
            contradictions=contradictions,
            reviewed_sha=shas[0],
        )

    return ReanalysisResult(
        "READY_FOR_EVIDENCE",
        consensus=verdicts[0],
        reviewed_sha=shas[0],
    )
