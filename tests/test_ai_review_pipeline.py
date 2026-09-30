import unittest

from tools.ai_review.change_extractor import ChangeExtractionResult
from tools.ai_review.dispatch import ChangeSet
from tools.ai_review.pipeline import plan_extracted_change


class AIReviewPipelineTests(unittest.TestCase):
    def extracted(self, status="EXTRACTED", **overrides):
        data = dict(
            reviewed_sha="head456",
            base_sha="base123",
            changed_files=("tools/catalogue.py",),
            changed_functions=("fingerprint",),
        )
        data.update(overrides)
        return ChangeExtractionResult(
            status=status,
            change_set=ChangeSet(**data),
            uncertainties=("tools/catalogue.py:functions_unknown",) if status == "EXTRACTED_WITH_UNCERTAINTY" else (),
        )

    def test_clean_extraction_uses_normal_dispatch(self):
        result = plan_extracted_change(self.extracted())
        self.assertEqual(result.status, "DISPATCH_REVIEW")
        self.assertEqual(result.risk, "MEDIUM")

    def test_uncertain_extraction_escalates_and_never_lightweights(self):
        result = plan_extracted_change(
            self.extracted(
                status="EXTRACTED_WITH_UNCERTAINTY",
                changed_files=("README.md",),
                changed_functions=(),
            )
        )
        self.assertEqual(result.status, "DISPATCH_REVIEW")
        self.assertEqual(result.risk, "HIGH")
        self.assertFalse(result.lightweight_allowed)
        self.assertIn("reanalysis", result.gates)
        self.assertIn("falsification", result.gates)
        self.assertIn("crossfunction", result.gates)

    def test_unbound_extraction_does_not_dispatch(self):
        result = plan_extracted_change(
            self.extracted(status="UNBOUND", reviewed_sha="")
        )
        self.assertEqual(result.status, "UNBOUND")
        self.assertEqual(result.gates, ())

    def test_no_action_extraction_does_not_dispatch(self):
        result = plan_extracted_change(
            self.extracted(status="NO_ACTION", changed_files=(), changed_functions=())
        )
        self.assertEqual(result.status, "NO_ACTION")
        self.assertEqual(result.gates, ())

    def test_unknown_extraction_state_fails_closed(self):
        result = plan_extracted_change(self.extracted(status="MYSTERY"))
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.gates, ())


if __name__ == "__main__":
    unittest.main()
