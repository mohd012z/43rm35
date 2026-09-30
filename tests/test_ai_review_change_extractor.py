import unittest

from tools.ai_review.change_extractor import DiffFile, extract_change_set


class AIReviewChangeExtractorTests(unittest.TestCase):
    def test_extracts_python_functions_from_patch(self):
        result = extract_change_set(
            base_sha="base123",
            reviewed_sha="head456",
            files=(
                DiffFile(
                    path="tools/catalogue.py",
                    patch="@@ -10,2 +10,4 @@\n def fingerprint(value):\n+    normalized = value.strip()\n+    return normalized\n",
                ),
            ),
        )
        self.assertEqual(result.status, "EXTRACTED")
        self.assertEqual(result.change_set.changed_files, ("tools/catalogue.py",))
        self.assertIn("fingerprint", result.change_set.changed_functions)

    def test_workflow_file_is_preserved_exactly(self):
        result = extract_change_set(
            base_sha="base123",
            reviewed_sha="head456",
            files=(DiffFile(path=".github/workflows/lola-advisory.yml", patch="+name: Lola\n"),),
        )
        self.assertEqual(
            result.change_set.changed_files,
            (".github/workflows/lola-advisory.yml",),
        )

    def test_missing_head_sha_is_unbound(self):
        result = extract_change_set(
            base_sha="base123",
            reviewed_sha="",
            files=(DiffFile(path="README.md", patch="+docs\n"),),
        )
        self.assertEqual(result.status, "UNBOUND")

    def test_empty_diff_is_no_action(self):
        result = extract_change_set(
            base_sha="base123",
            reviewed_sha="head456",
            files=(),
        )
        self.assertEqual(result.status, "NO_ACTION")
        self.assertEqual(result.change_set.changed_files, ())

    def test_unparseable_source_patch_preserves_file_and_marks_uncertainty(self):
        result = extract_change_set(
            base_sha="base123",
            reviewed_sha="head456",
            files=(DiffFile(path="src/player.py", patch=None),),
        )
        self.assertEqual(result.status, "EXTRACTED_WITH_UNCERTAINTY")
        self.assertEqual(result.change_set.changed_files, ("src/player.py",))
        self.assertIn("src/player.py:functions_unknown", result.uncertainties)


if __name__ == "__main__":
    unittest.main()
