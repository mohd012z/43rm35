import unittest

from tools.ai_review.approval import ActionContext, evaluate_approval


class AIReviewApprovalTests(unittest.TestCase):
    def test_read_only_analysis_auto_proceeds(self):
        result = evaluate_approval(ActionContext(action="analyze", read_only=True))
        self.assertFalse(result.approval_required)
        self.assertEqual(result.disposition, "PROCEED_AUTOMATICALLY")

    def test_test_execution_auto_proceeds(self):
        result = evaluate_approval(ActionContext(action="run_tests", read_only=True))
        self.assertFalse(result.approval_required)
        self.assertEqual(result.disposition, "PROCEED_AUTOMATICALLY")

    def test_default_branch_control_plane_change_requires_approval(self):
        result = evaluate_approval(ActionContext(
            action="modify_workflow",
            target_branch="master",
            changes_control_plane=True,
            reversible=True,
        ))
        self.assertTrue(result.approval_required)
        self.assertEqual(result.disposition, "REQUEST_APPROVAL")

    def test_secret_or_permission_change_requires_approval(self):
        result = evaluate_approval(ActionContext(
            action="change_permissions",
            touches_secrets_or_permissions=True,
        ))
        self.assertTrue(result.approval_required)
        self.assertEqual(result.disposition, "REQUEST_APPROVAL")

    def test_destructive_action_requires_approval(self):
        result = evaluate_approval(ActionContext(
            action="delete_data",
            destructive=True,
            reversible=False,
        ))
        self.assertTrue(result.approval_required)
        self.assertEqual(result.disposition, "REQUEST_APPROVAL")

    def test_ambiguous_high_impact_action_holds_for_approval(self):
        result = evaluate_approval(ActionContext(
            action="unknown_external_change",
            impact="HIGH",
            ambiguous=True,
        ))
        self.assertTrue(result.approval_required)
        self.assertEqual(result.disposition, "REQUEST_APPROVAL")

    def test_no_action_is_distinct_from_approval(self):
        result = evaluate_approval(ActionContext(action="none", no_action=True))
        self.assertFalse(result.approval_required)
        self.assertEqual(result.disposition, "NO_ACTION")


if __name__ == "__main__":
    unittest.main()
