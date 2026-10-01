import unittest

from tools.stream_executor import ExecutorConfig, select_probe_targets, run_probe_targets


class StreamExecutorTests(unittest.TestCase):
    def test_only_http_and_hls_targets_are_selected(self):
        entries = [
            {"url": "https://a.test/live.m3u8", "protocol": "hls"},
            {"url": "http://b.test/live", "protocol": "http"},
            {"url": "rtmp://c.test/live", "protocol": "rtmp"},
            {"url": "rtsp://d.test/live", "protocol": "rtsp"},
        ]
        targets = select_probe_targets(entries)
        self.assertEqual([item["protocol"] for item in targets], ["hls", "http"])

    def test_executor_is_disabled_by_default(self):
        calls = []
        report = run_probe_targets(
            [{"url": "https://a.test/live.m3u8", "protocol": "hls"}],
            fetcher=lambda request: calls.append(request),
        )
        self.assertFalse(report["network_checks_performed"])
        self.assertEqual(calls, [])

    def test_enabled_executor_uses_bounded_concurrency(self):
        active = 0
        peak = 0

        def fetcher(request):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            active -= 1
            return {
                "status_code": 200,
                "content_type": "application/vnd.apple.mpegurl",
                "elapsed_ms": 10,
                "final_url": request.url,
                "body": b"#EXTM3U\n",
            }

        entries = [
            {"url": f"https://{i}.test/live.m3u8", "protocol": "hls"}
            for i in range(10)
        ]
        report = run_probe_targets(
            entries,
            config=ExecutorConfig(enabled=True, max_workers=3),
            fetcher=fetcher,
        )
        self.assertTrue(report["network_checks_performed"])
        self.assertLessEqual(peak, 3)
        self.assertEqual(report["checked"], 10)

    def test_fetch_exception_becomes_transient_result(self):
        report = run_probe_targets(
            [{"url": "https://a.test/live.m3u8", "protocol": "hls"}],
            config=ExecutorConfig(enabled=True),
            fetcher=lambda request: (_ for _ in ()).throw(TimeoutError("timeout")),
        )
        self.assertEqual(report["transient_failure"], 1)
        self.assertEqual(report["checked"], 1)

    def test_worker_limit_is_clamped(self):
        config = ExecutorConfig(enabled=True, max_workers=999)
        self.assertLessEqual(config.bounded_workers(), 8)


if __name__ == "__main__":
    unittest.main()
