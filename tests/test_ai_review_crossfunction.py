import unittest

from tools.ai_review.crossfunction import ImpactMap, evaluate_crossfunction


class AIReviewCrossFunctionTests(unittest.TestCase):
    def impact(self, **overrides):
        data = dict(
            reviewed_sha="abc123",
            changed_nodes=("catalogue.fingerprint",),
            downstream_nodes=("catalogue.deduplicate", "catalogue.export"),
            required_tests=("test_fingerprint", "test_deduplicate", "test_export"),
            executed_tests=("test_fingerprint", "test_deduplicate", "test_export"),
            unresolved_impacts=(),
        )
        data.update(overrides)
        return ImpactMap(**data)

    def test_complete_impact_map_is_ready(self):
        result = evaluate_crossfunction(self.impact())
        self.assertEqual(result.status, "CROSSFUNCTION_VERIFIED")

    def test_missing_sha_is_unbound(self):
        result = evaluate_crossfunction(self.impact(reviewed_sha=""))
        self.assertEqual(result.status, "UNBOUND")

    def test_no_downstream_map_fails_closed(self):
        result = evaluate_crossfunction(
            self.impact(downstream_nodes=(), required_tests=(), executed_tests=())
        )
        self.assertEqual(result.status, "IMPACT_MAP_INCOMPLETE")

    def test_missing_downstream_test_needs_evidence(self):
        result = evaluate_crossfunction(
            self.impact(executed_tests=("test_fingerprint", "test_deduplicate"))
        )
        self.assertEqual(result.status, "NEEDS_EVIDENCE")
        self.assertIn("test_export", result.missing_tests)

    def test_unresolved_impact_blocks_verification(self):
        result = evaluate_crossfunction(
            self.impact(unresolved_impacts=("NovaStreamerTV consumer compatibility",))
        )
        self.assertEqual(result.status, "UNRESOLVED_IMPACT")
        self.assertEqual(
            result.unresolved_impacts,
            ("NovaStreamerTV consumer compatibility",),
        )


if __name__ == "__main__":
    unittest.main()
