import unittest

from tools.ai_review.orchestrator import GateSnapshot, orchestrate


class AIReviewOrchestratorTests(unittest.TestCase):
    def snapshot(self, **overrides):
        data = dict(
            reviewed_sha="abc123",
            protocol_status="READY_FOR_REANALYSIS",
            reanalysis_status="READY_FOR_EVIDENCE",
            falsification_status="SURVIVED_FALSIFICATION",
            crossfunction_status="CROSSFUNCTION_VERIFIED",
            evidence_status="VERIFIED_TRUE",
            approval_disposition="PROCEED_AUTOMATICALLY",
        )
        data.update(overrides)
        return GateSnapshot(**data)

    def test_all_verified_auto_action_is_ready(self):
        result = orchestrate(self.snapshot())
        self.assertEqual(result.status, "READY_TO_ACT")

    def test_human_approval_is_preserved(self):
        result = orchestrate(self.snapshot(approval_disposition="REQUEST_APPROVAL"))
        self.assertEqual(result.status, "AWAITING_APPROVAL")

    def test_protocol_evidence_gap_stops_pipeline(self):
        result = orchestrate(self.snapshot(protocol_status="NEEDS_EVIDENCE"))
        self.assertEqual(result.status, "NEEDS_EVIDENCE")
        self.assertEqual(result.blocked_at, "protocol")

    def test_agent_contradiction_stops_pipeline(self):
        result = orchestrate(self.snapshot(reanalysis_status="AGENT_CONTRADICTION"))
        self.assertEqual(result.status, "CONTRADICTED")
        self.assertEqual(result.blocked_at, "reanalysis")

    def test_falsification_counterexample_blocks(self):
        result = orchestrate(self.snapshot(falsification_status="CONTRADICTED"))
        self.assertEqual(result.status, "CONTRADICTED")
        self.assertEqual(result.blocked_at, "falsification")

    def test_unresolved_crossfunction_impact_blocks(self):
        result = orchestrate(self.snapshot(crossfunction_status="UNRESOLVED_IMPACT"))
        self.assertEqual(result.status, "UNRESOLVED_IMPACT")
        self.assertEqual(result.blocked_at, "crossfunction")

    def test_stale_evidence_requires_reanalysis(self):
        result = orchestrate(self.snapshot(evidence_status="STALE"))
        self.assertEqual(result.status, "REANALYZE")
        self.assertEqual(result.blocked_at, "evidence")

    def test_verified_false_blocks_action(self):
        result = orchestrate(self.snapshot(evidence_status="VERIFIED_FALSE"))
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocked_at, "evidence")

    def test_unknown_gate_state_fails_closed(self):
        result = orchestrate(self.snapshot(crossfunction_status="MYSTERY"))
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.blocked_at, "crossfunction")


if __name__ == "__main__":
    unittest.main()
