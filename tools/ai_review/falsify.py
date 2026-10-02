"""Active falsification gate for AI advisory claims."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class FalsificationCase:
    reviewed_sha: str
    claim: str
    proposed_tests: Tuple[str, ...] = ()
    executed_tests: Tuple[str, ...] = ()
    counterexamples: Tuple[str, ...] = ()


@dataclass(frozen=True)
class FalsificationResult:
    status: str
    reviewed_sha: str = ""
    missing_tests: Tuple[str, ...] = ()
    counterexamples: Tuple[str, ...] = ()


def evaluate_falsification(case: FalsificationCase) -> FalsificationResult:
    """Attempt to disprove a claim before it can proceed to evidence verification.

    Surviving falsification is not proof. It only means every proposed
    counter-test was executed and none produced a counterexample.
    """
    reviewed_sha = case.reviewed_sha.strip()
    if not reviewed_sha:
        return FalsificationResult("UNBOUND")

    proposed = tuple(dict.fromkeys(test.strip() for test in case.proposed_tests if test.strip()))
    executed = set(test.strip() for test in case.executed_tests if test.strip())

    if not proposed:
        return FalsificationResult(
            "INSUFFICIENT_FALSIFICATION",
            reviewed_sha=reviewed_sha,
        )

    if case.counterexamples:
        return FalsificationResult(
            "CONTRADICTED",
            reviewed_sha=reviewed_sha,
            counterexamples=tuple(case.counterexamples),
        )

    missing = tuple(test for test in proposed if test not in executed)
    if missing:
        return FalsificationResult(
            "NEEDS_EVIDENCE",
            reviewed_sha=reviewed_sha,
            missing_tests=missing,
        )

    return FalsificationResult(
        "SURVIVED_FALSIFICATION",
        reviewed_sha=reviewed_sha,
    )
