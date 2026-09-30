"""Cross-function and downstream impact verification for AI advisory changes."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ImpactMap:
    reviewed_sha: str
    changed_nodes: Tuple[str, ...] = ()
    downstream_nodes: Tuple[str, ...] = ()
    required_tests: Tuple[str, ...] = ()
    executed_tests: Tuple[str, ...] = ()
    unresolved_impacts: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CrossFunctionResult:
    status: str
    reviewed_sha: str = ""
    missing_tests: Tuple[str, ...] = ()
    unresolved_impacts: Tuple[str, ...] = ()


def evaluate_crossfunction(impact: ImpactMap) -> CrossFunctionResult:
    """Fail closed until downstream impact and required regression tests are known."""
    reviewed_sha = impact.reviewed_sha.strip()
    if not reviewed_sha:
        return CrossFunctionResult("UNBOUND")

    changed = tuple(node.strip() for node in impact.changed_nodes if node.strip())
    downstream = tuple(node.strip() for node in impact.downstream_nodes if node.strip())
    required = tuple(dict.fromkeys(test.strip() for test in impact.required_tests if test.strip()))
    executed = {test.strip() for test in impact.executed_tests if test.strip()}

    if not changed or not downstream:
        return CrossFunctionResult(
            "IMPACT_MAP_INCOMPLETE",
            reviewed_sha=reviewed_sha,
        )

    if impact.unresolved_impacts:
        return CrossFunctionResult(
            "UNRESOLVED_IMPACT",
            reviewed_sha=reviewed_sha,
            unresolved_impacts=tuple(impact.unresolved_impacts),
        )

    missing = tuple(test for test in required if test not in executed)
    if missing:
        return CrossFunctionResult(
            "NEEDS_EVIDENCE",
            reviewed_sha=reviewed_sha,
            missing_tests=missing,
        )

    if not required:
        return CrossFunctionResult(
            "IMPACT_MAP_INCOMPLETE",
            reviewed_sha=reviewed_sha,
        )

    return CrossFunctionResult(
        "CROSSFUNCTION_VERIFIED",
        reviewed_sha=reviewed_sha,
    )
