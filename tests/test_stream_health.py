import unittest

from tools.stream_health import ProbeObservation, classify_observation, summarize_health


class StreamHealthTests(unittest.TestCase):
    def test_hls_manifest_success_is_healthy(self):
        result = classify_observation(
            ProbeObservation(
                url="https://example.test/live.m3u8",
                status_code=200,
                content_type="application/vnd.apple.mpegurl",
                elapsed_ms=120,
                final_url="https://cdn.example.test/live.m3u8",
                body_prefix="#EXTM3U\n#EXT-X-VERSION:3\n",
            )
        )
        self.assertEqual(result.status, "HEALTHY")
        self.assertTrue(result.manifest_valid)

    def test_http_error_is_unavailable_not_catalogue_error(self):
        result = classify_observation(
            ProbeObservation(url="https://example.test/live.m3u8", status_code=503)
        )
        self.assertEqual(result.status, "UNAVAILABLE")
        self.assertEqual(result.catalogue_severity, "INFO")

    def test_timeout_is_transient(self):
        result = classify_observation(
            ProbeObservation(url="https://example.test/live.m3u8", error="timeout")
        )
        self.assertEqual(result.status, "TRANSIENT_FAILURE")
        self.assertEqual(result.catalogue_severity, "INFO")

    def test_non_manifest_hls_response_is_degraded(self):
        result = classify_observation(
            ProbeObservation(
                url="https://example.test/live.m3u8",
                status_code=200,
                content_type="text/html",
                body_prefix="<html>blocked</html>",
            )
        )
        self.assertEqual(result.status, "DEGRADED")
        self.assertFalse(result.manifest_valid)

    def test_summary_keeps_network_results_separate(self):
        results = [
            classify_observation(ProbeObservation(url="https://a.test/a.m3u8", status_code=503)),
            classify_observation(ProbeObservation(url="https://b.test/b.m3u8", error="timeout")),
        ]
        summary = summarize_health(results)
        self.assertTrue(summary["network_checks_performed"])
        self.assertEqual(summary["checked"], 2)
        self.assertEqual(summary["unavailable"], 1)
        self.assertEqual(summary["transient_failure"], 1)


if __name__ == "__main__":
    unittest.main()
