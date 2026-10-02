import unittest

from tools.stream_probe import ProbeConfig, build_probe_request, observation_from_response


class StreamProbeTests(unittest.TestCase):
    def test_request_is_bounded_and_read_only(self):
        request = build_probe_request(
            "https://example.test/live.m3u8",
            ProbeConfig(timeout_seconds=4.0, max_body_bytes=4096),
        )
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.timeout_seconds, 4.0)
        self.assertEqual(request.max_body_bytes, 4096)
        self.assertTrue(request.follow_redirects)

    def test_timeout_limit_is_clamped(self):
        request = build_probe_request(
            "https://example.test/live.m3u8",
            ProbeConfig(timeout_seconds=60.0),
        )
        self.assertLessEqual(request.timeout_seconds, 10.0)

    def test_body_limit_is_clamped(self):
        request = build_probe_request(
            "https://example.test/live.m3u8",
            ProbeConfig(max_body_bytes=10_000_000),
        )
        self.assertLessEqual(request.max_body_bytes, 65536)

    def test_response_maps_to_health_observation(self):
        observation = observation_from_response(
            url="https://example.test/live.m3u8",
            status_code=200,
            content_type="application/vnd.apple.mpegurl",
            elapsed_ms=150,
            final_url="https://cdn.example.test/live.m3u8",
            body=b"#EXTM3U\n#EXT-X-VERSION:3\n",
        )
        self.assertEqual(observation.status_code, 200)
        self.assertEqual(observation.elapsed_ms, 150)
        self.assertEqual(observation.final_url, "https://cdn.example.test/live.m3u8")
        self.assertTrue(observation.body_prefix.startswith("#EXTM3U"))

    def test_binary_or_invalid_text_does_not_crash(self):
        observation = observation_from_response(
            url="https://example.test/live.m3u8",
            status_code=200,
            body=b"\xff\xfe#EXTM3U",
        )
        self.assertIsInstance(observation.body_prefix, str)


if __name__ == "__main__":
    unittest.main()
