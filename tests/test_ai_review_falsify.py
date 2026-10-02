import unittest

from tools.ai_review.falsify import FalsificationCase, evaluate_falsification


class AIReviewFalsificationTests(unittest.TestCase):
    def case(self, **overrides):
        data = dict(
            reviewed_sha="abc123",
            claim="catalogue identity normalization is deterministic",
            proposed_tests=("unicode-normalization", "empty-identity"),
            executed_tests=("unicode-normalization", "empty-identity"),
            counterexamples=(),
        )
        data.update(overrides)
        return FalsificationCase(**data)

    def test_completed_countertests_without_counterexample_survive(self):
        result = evaluate_falsification(self.case())
        self.assertEqual(result.status, "SURVIVED_FALSIFICATION")

    def test_counterexample_contradicts_claim(self):
        result = evaluate_falsification(
            self.case(counterexamples=("unicode collision",))
        )
        self.assertEqual(result.status, "CONTRADICTED")
        self.assertEqual(result.counterexamples, ("unicode collision",))

    def test_unexecuted_proposed_test_needs_evidence(self):
        result = evaluate_falsification(
            self.case(executed_tests=("unicode-normalization",))
        )
        self.assertEqual(result.status, "NEEDS_EVIDENCE")
        self.assertIn("empty-identity", result.missing_tests)

    def test_missing_sha_is_unbound(self):
        result = evaluate_falsification(self.case(reviewed_sha=""))
        self.assertEqual(result.status, "UNBOUND")

    def test_no_countertests_fails_closed(self):
        result = evaluate_falsification(
            self.case(proposed_tests=(), executed_tests=())
        )
        self.assertEqual(result.status, "INSUFFICIENT_FALSIFICATION")


if __name__ == "__main__":
    unittest.main()
