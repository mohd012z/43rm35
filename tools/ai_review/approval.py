"""Risk-based pre-action approval policy for AI advisory operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionContext:
    action: str
    read_only: bool = False
    target_branch: str = ""
    changes_control_plane: bool = False
    touches_secrets_or_permissions: bool = False
    destructive: bool = False
    reversible: bool = True
    impact: str = "LOW"
    ambiguous: bool = False
    no_action: bool = False


@dataclass(frozen=True)
class ApprovalDecision:
    approval_required: bool
    disposition: str
    reason: str


def evaluate_approval(context: ActionContext) -> ApprovalDecision:
    """Classify whether a proposed operation needs explicit human approval.

    Read-only inspection and tests may proceed. Consequential control-plane,
    permission/secret, destructive, or ambiguous high-impact operations are
    held for approval. The policy is deliberately fail-closed for those cases.
    """
    if context.no_action or context.action == "none":
        return ApprovalDecision(False, "NO_ACTION", "No repository action is required.")

    reasons = []
    if context.changes_control_plane and context.target_branch in {"master", "main"}:
        reasons.append("trusted default-branch control-plane change")
    if context.touches_secrets_or_permissions:
        reasons.append("secrets or permissions boundary change")
    if context.destructive:
        reasons.append("destructive operation")
    if context.ambiguous and context.impact.upper() in {"HIGH", "CRITICAL"}:
        reasons.append("ambiguous high-impact operation")

    if reasons:
        return ApprovalDecision(True, "REQUEST_APPROVAL", "; ".join(reasons))

    if context.read_only or context.action in {"analyze", "run_tests", "static_check", "generate_report"}:
        return ApprovalDecision(False, "PROCEED_AUTOMATICALLY", "Read-only or verification operation.")

    # Unknown mutating operations are not silently authorized.
    return ApprovalDecision(True, "REQUEST_APPROVAL", "Unclassified mutating operation requires review.")
