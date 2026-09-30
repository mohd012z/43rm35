import unittest

from tools.ai_review.protocol import PreActionReview, validate_pre_action_review


class AIReviewProtocolTests(unittest.TestCase):
    def valid_review(self, **overrides):
        data = dict(
            intent="Enable automatic Lola analysis after catalogue validation.",
            actual_operation="Modify the advisory workflow trigger and orchestration.",
            reviewed_sha="abc123",
            affected_files=(".github/workflows/lola-advisory.yml",),
            affected_functions=("workflow_run",),
            downstream_impacts=("CI advisory execution",),
            assumptions=("Validate catalogue is the upstream trusted workflow.",),
            missing_evidence=(),
            proposed_action="Install dispatcher after independent verification.",
            reversible=True,
            risk="HIGH",
        )
        data.update(overrides)
        return PreActionReview(**data)

    def test_complete_review_is_ready_for_reanalysis(self):
        result = validate_pre_action_review(self.valid_review())
        self.assertEqual(result.status, "READY_FOR_REANALYSIS")

    def test_missing_actual_operation_is_incomplete(self):
        result = validate_pre_action_review(self.valid_review(actual_operation=""))
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertIn("actual_operation", result.missing_fields)

    def test_missing_sha_is_stale_unbound(self):
        result = validate_pre_action_review(self.valid_review(reviewed_sha=""))
        self.assertEqual(result.status, "UNBOUND")

    def test_missing_impact_map_is_incomplete(self):
        result = validate_pre_action_review(
            self.valid_review(affected_files=(), affected_functions=(), downstream_impacts=())
        )
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertIn("impact_map", result.missing_fields)

    def test_missing_evidence_is_preserved_not_hidden(self):
        result = validate_pre_action_review(
            self.valid_review(missing_evidence=("workflow_run execution proof",))
        )
        self.assertEqual(result.status, "NEEDS_EVIDENCE")
        self.assertEqual(result.missing_evidence, ("workflow_run execution proof",))

    def test_invalid_risk_fails_closed(self):
        result = validate_pre_action_review(self.valid_review(risk="MAYBE"))
        self.assertEqual(result.status, "INVALID")


if __name__ == "__main__":
    unittest.main()
