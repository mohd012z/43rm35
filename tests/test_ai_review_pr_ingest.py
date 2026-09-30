import unittest

from tools.ai_review.pr_ingest import PRFile, PRSnapshot, ingest_pr_snapshot


class AIReviewPRIngestTests(unittest.TestCase):
    def snapshot(self, **overrides):
        data = dict(
            number=1,
            base_sha="base123",
            head_sha="head456",
            files=(
                PRFile(
                    path="tools/catalogue.py",
                    patch="@@ -10,2 +10,3 @@\n def fingerprint(value):\n+    return value.strip()\n",
                ),
            ),
        )
        data.update(overrides)
        return PRSnapshot(**data)

    def test_clean_pr_flows_to_normal_dispatch(self):
        result = ingest_pr_snapshot(self.snapshot())
        self.assertEqual(result.status, "DISPATCH_REVIEW")
        self.assertEqual(result.reviewed_sha, "head456")
        self.assertEqual(result.base_sha, "base123")
        self.assertEqual(result.risk, "MEDIUM")

    def test_missing_patch_escalates_to_high_full_review(self):
        result = ingest_pr_snapshot(
            self.snapshot(files=(PRFile(path="src/player.py", patch=None),))
        )
        self.assertEqual(result.status, "DISPATCH_REVIEW")
        self.assertEqual(result.risk, "HIGH")
        self.assertFalse(result.lightweight_allowed)
        self.assertIn("src/player.py:functions_unknown", result.uncertainties)

    def test_docs_only_pr_can_use_lightweight_when_patch_is_known(self):
        result = ingest_pr_snapshot(
            self.snapshot(files=(PRFile(path="README.md", patch="+documentation\n"),))
        )
        self.assertEqual(result.status, "DISPATCH_LIGHTWEIGHT")
        self.assertTrue(result.lightweight_allowed)

    def test_missing_head_sha_is_unbound(self):
        result = ingest_pr_snapshot(self.snapshot(head_sha=""))
        self.assertEqual(result.status, "UNBOUND")
        self.assertEqual(result.gates, ())

    def test_empty_pr_is_no_action(self):
        result = ingest_pr_snapshot(self.snapshot(files=()))
        self.assertEqual(result.status, "NO_ACTION")
        self.assertEqual(result.gates, ())


if __name__ == "__main__":
    unittest.main()
