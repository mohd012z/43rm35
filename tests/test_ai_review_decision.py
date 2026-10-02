import unittest

from tools.ai_review.decision import decide


class AIReviewDecisionTests(unittest.TestCase):
    def test_consensus_without_evidence_cannot_pass(self):
        result = decide(
            lola="TRUE",
            kernel_ai="TRUE",
            in_ai="TRUE",
            evidence_status="INSUFFICIENT_EVIDENCE",
        )
        self.assertEqual("INSUFFICIENT_EVIDENCE", result)

    def test_agent_disagreement_requires_review(self):
        result = decide(
            lola="TRUE",
            kernel_ai="FALSE",
            in_ai="UNKNOWN",
            evidence_status="UNKNOWN",
        )
        self.assertEqual("UNKNOWN", result)

    def test_sha_mismatch_is_stale(self):
        result = decide(
            lola="TRUE",
            kernel_ai="TRUE",
            in_ai="TRUE",
            evidence_status="STALE",
        )
        self.assertEqual("STALE", result)

    def test_counter_evidence_blocks_as_contradicted(self):
        result = decide(
            lola="TRUE",
            kernel_ai="TRUE",
            in_ai="TRUE",
            evidence_status="CONTRADICTED",
        )
        self.assertEqual("CONTRADICTED", result)

    def test_only_independently_verified_evidence_can_pass(self):
        result = decide(
            lola="TRUE",
            kernel_ai="TRUE",
            in_ai="TRUE",
            evidence_status="VERIFIED_TRUE",
        )
        self.assertEqual("VERIFIED_TRUE", result)


if __name__ == "__main__":
    unittest.main()
