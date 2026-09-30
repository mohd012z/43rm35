import unittest

from tools.ai_review.reanalysis import AgentAnalysis, reanalyze


class AIReviewReanalysisTests(unittest.TestCase):
    def analysis(self, agent, verdict="TRUE", sha="abc123", **overrides):
        data = dict(
            agent=agent,
            reviewed_sha=sha,
            verdict=verdict,
            reason=f"{agent} independent assessment",
            evidence_refs=("test:unit",),
            assumptions=(),
            missing_evidence=(),
            counterarguments=(),
            proposed_tests=(),
        )
        data.update(overrides)
        return AgentAnalysis(**data)

    def test_independent_agreement_is_ready_for_evidence(self):
        result = reanalyze(
            self.analysis("LOLA"),
            self.analysis("KERNEL_AI"),
            self.analysis("IN_AI"),
        )
        self.assertEqual(result.status, "READY_FOR_EVIDENCE")
        self.assertEqual(result.consensus, "TRUE")

    def test_agent_disagreement_is_explicit_contradiction(self):
        result = reanalyze(
            self.analysis("LOLA", "TRUE"),
            self.analysis("KERNEL_AI", "FALSE"),
            self.analysis("IN_AI", "FALSE"),
        )
        self.assertEqual(result.status, "AGENT_CONTRADICTION")
        self.assertIn("LOLA:TRUE", result.contradictions)
        self.assertIn("KERNEL_AI:FALSE", result.contradictions)

    def test_sha_mismatch_is_stale(self):
        result = reanalyze(
            self.analysis("LOLA", sha="abc123"),
            self.analysis("KERNEL_AI", sha="def456"),
            self.analysis("IN_AI", sha="abc123"),
        )
        self.assertEqual(result.status, "STALE")

    def test_missing_evidence_is_preserved(self):
        result = reanalyze(
            self.analysis("LOLA"),
            self.analysis("KERNEL_AI", missing_evidence=("integration proof",)),
            self.analysis("IN_AI"),
        )
        self.assertEqual(result.status, "NEEDS_EVIDENCE")
        self.assertIn("KERNEL_AI:integration proof", result.missing_evidence)

    def test_unknown_verdict_fails_closed(self):
        result = reanalyze(
            self.analysis("LOLA"),
            self.analysis("KERNEL_AI", verdict="MAYBE"),
            self.analysis("IN_AI"),
        )
        self.assertEqual(result.status, "INVALID")

    def test_duplicate_agent_identity_is_invalid(self):
        result = reanalyze(
            self.analysis("LOLA"),
            self.analysis("LOLA"),
            self.analysis("IN_AI"),
        )
        self.assertEqual(result.status, "INVALID")


if __name__ == "__main__":
    unittest.main()
