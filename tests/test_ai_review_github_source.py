import unittest

from tools.ai_review.github_source import GitHubPRSource, SourceFile, build_source_manifest


class GitHubSourceTests(unittest.TestCase):
    def source(self, **overrides):
        data = dict(
            pr_number=1,
            base_sha="base123",
            head_sha="head456",
            declared_changed_files=2,
            files=(
                SourceFile(path="tools/catalogue.py", patch="@@ -1 +1 @@\n def fingerprint(value):\n+    return value.strip()\n"),
                SourceFile(path="README.md", patch="+docs\n"),
            ),
        )
        data.update(overrides)
        return GitHubPRSource(**data)

    def test_complete_source_builds_snapshot_and_manifest(self):
        result = build_source_manifest(self.source())
        self.assertEqual(result.status, "SOURCE_COMPLETE")
        self.assertEqual(result.snapshot.number, 1)
        self.assertEqual(result.snapshot.head_sha, "head456")
        self.assertEqual(result.manifest.expected_files, 2)
        self.assertEqual(result.manifest.observed_files, 2)
        self.assertEqual(result.manifest.missing_patches, ())

    def test_missing_patch_is_explicit_uncertainty(self):
        result = build_source_manifest(
            self.source(files=(SourceFile(path="src/player.py", patch=None), SourceFile(path="README.md", patch="+docs\n")))
        )
        self.assertEqual(result.status, "SOURCE_INCOMPLETE")
        self.assertIn("src/player.py", result.manifest.missing_patches)

    def test_declared_file_count_mismatch_fails_closed(self):
        result = build_source_manifest(self.source(declared_changed_files=3))
        self.assertEqual(result.status, "SOURCE_INCOMPLETE")
        self.assertEqual(result.manifest.expected_files, 3)
        self.assertEqual(result.manifest.observed_files, 2)

    def test_duplicate_path_is_invalid(self):
        result = build_source_manifest(
            self.source(files=(SourceFile(path="README.md", patch="+a"), SourceFile(path="README.md", patch="+b")))
        )
        self.assertEqual(result.status, "SOURCE_INVALID")
        self.assertIn("README.md", result.manifest.duplicate_paths)

    def test_missing_head_sha_is_unbound(self):
        result = build_source_manifest(self.source(head_sha=""))
        self.assertEqual(result.status, "UNBOUND")


if __name__ == "__main__":
    unittest.main()
