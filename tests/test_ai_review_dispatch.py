import unittest

from tools.ai_review.dispatch import ChangeSet, build_dispatch_plan


class AIReviewDispatchTests(unittest.TestCase):
    def changes(self, **overrides):
        data = dict(
            reviewed_sha="abc123",
            base_sha="base123",
            changed_files=("tools/catalogue.py",),
            changed_functions=("fingerprint",),
        )
        data.update(overrides)
        return ChangeSet(**data)

    def test_code_change_builds_full_review_plan(self):
        plan = build_dispatch_plan(self.changes())
        self.assertEqual(plan.status, "DISPATCH_REVIEW")
        self.assertEqual(
            plan.gates,
            ("protocol", "reanalysis", "falsification", "crossfunction", "evidence", "approval"),
        )

    def test_workflow_change_is_high_risk_and_requires_approval_gate(self):
        plan = build_dispatch_plan(
            self.changes(changed_files=(".github/workflows/lola-advisory.yml",))
        )
        self.assertEqual(plan.risk, "HIGH")
        self.assertTrue(plan.control_plane_change)
        self.assertIn("approval", plan.gates)

    def test_docs_only_change_uses_lightweight_review(self):
        plan = build_dispatch_plan(
            self.changes(changed_files=("README.md",), changed_functions=())
        )
        self.assertEqual(plan.status, "DISPATCH_LIGHTWEIGHT")
        self.assertEqual(plan.gates, ("protocol", "evidence", "approval"))

    def test_missing_review_sha_is_unbound(self):
        plan = build_dispatch_plan(self.changes(reviewed_sha=""))
        self.assertEqual(plan.status, "UNBOUND")
        self.assertEqual(plan.gates, ())

    def test_no_changes_results_in_no_action(self):
        plan = build_dispatch_plan(
            self.changes(changed_files=(), changed_functions=())
        )
        self.assertEqual(plan.status, "NO_ACTION")
        self.assertEqual(plan.gates, ())


if __name__ == "__main__":
    unittest.main()
