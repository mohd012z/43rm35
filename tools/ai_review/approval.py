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
    checks_green: bool = False
    evidence_verified: bool = False


@dataclass(frozen=True)
class ApprovalDecision:
    approval_required: bool
    disposition: str
    reason: str


def evaluate_approval(context: ActionContext) -> ApprovalDecision:
    """Auto-approve verified reversible branch work; hold hard boundaries.

    Lola may finish ordinary reversible work automatically once required checks
    and evidence are green. Explicit approval remains required for secrets or
    permission changes, destructive/irreversible actions, ambiguous critical
    actions, and control-plane mutations directly on the trusted default branch.
    """
    if context.no_action or context.action == "none":
        return ApprovalDecision(False, "NO_ACTION", "No repository action is required.")

    if context.touches_secrets_or_permissions:
        return ApprovalDecision(True, "REQUEST_APPROVAL", "Secrets or permissions boundary change.")
    if context.destructive or not context.reversible:
        return ApprovalDecision(True, "REQUEST_APPROVAL", "Destructive or irreversible operation.")
    if context.ambiguous and context.impact.upper() == "CRITICAL":
        return ApprovalDecision(True, "REQUEST_APPROVAL", "Ambiguous critical-impact operation.")
    if context.changes_control_plane and context.target_branch in {"master", "main"}:
        return ApprovalDecision(True, "REQUEST_APPROVAL", "Trusted default-branch control-plane change.")

    if context.read_only or context.action in {"analyze", "run_tests", "static_check", "generate_report"}:
        return ApprovalDecision(False, "PROCEED_AUTOMATICALLY", "Read-only or verification operation.")

    if context.reversible and context.checks_green and context.evidence_verified:
        return ApprovalDecision(False, "PROCEED_AUTOMATICALLY", "Verified reversible branch operation.")

    return ApprovalDecision(True, "REQUEST_APPROVAL", "Required verification is not yet green.")
