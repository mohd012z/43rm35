import unittest

from tools.ai_review.evidence import EvidenceBundle, verify_evidence


class AIReviewEvidenceTests(unittest.TestCase):
    def test_matching_sha_and_complete_proof_is_verified_true(self):
        bundle = EvidenceBundle(
            reviewed_sha="abc123",
            current_sha="abc123",
            file_hashes_verified=True,
            tests_executed=True,
            tests_passed=True,
            contradictions=(),
        )
        result = verify_evidence(bundle)
        self.assertEqual(result.status, "VERIFIED_TRUE")
        self.assertEqual(result.reviewed_sha, "abc123")

    def test_sha_mismatch_is_stale(self):
        bundle = EvidenceBundle(
            reviewed_sha="abc123",
            current_sha="def456",
            file_hashes_verified=True,
            tests_executed=True,
            tests_passed=True,
            contradictions=(),
        )
        self.assertEqual(verify_evidence(bundle).status, "STALE")

    def test_missing_file_hash_proof_is_insufficient(self):
        bundle = EvidenceBundle(
            reviewed_sha="abc123",
            current_sha="abc123",
            file_hashes_verified=False,
            tests_executed=True,
            tests_passed=True,
            contradictions=(),
        )
        self.assertEqual(verify_evidence(bundle).status, "INSUFFICIENT_EVIDENCE")

    def test_unexecuted_tests_are_insufficient(self):
        bundle = EvidenceBundle(
            reviewed_sha="abc123",
            current_sha="abc123",
            file_hashes_verified=True,
            tests_executed=False,
            tests_passed=False,
            contradictions=(),
        )
        self.assertEqual(verify_evidence(bundle).status, "INSUFFICIENT_EVIDENCE")

    def test_failed_tests_verify_false(self):
        bundle = EvidenceBundle(
            reviewed_sha="abc123",
            current_sha="abc123",
            file_hashes_verified=True,
            tests_executed=True,
            tests_passed=False,
            contradictions=(),
        )
        self.assertEqual(verify_evidence(bundle).status, "VERIFIED_FALSE")

    def test_counter_evidence_is_contradicted(self):
        bundle = EvidenceBundle(
            reviewed_sha="abc123",
            current_sha="abc123",
            file_hashes_verified=True,
            tests_executed=True,
            tests_passed=True,
            contradictions=("counterexample-1",),
        )
        result = verify_evidence(bundle)
        self.assertEqual(result.status, "CONTRADICTED")
        self.assertEqual(result.contradictions, ("counterexample-1",))


if __name__ == "__main__":
    unittest.main()
