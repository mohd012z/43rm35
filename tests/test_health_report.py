import unittest
from pathlib import Path

from tools.stream_health import HealthResult
from tools.health_report import (
    NOT_CHECKED,
    UNSUPPORTED_PROTOCOL,
    build_health_report,
    build_stream_record,
)
from tools import catalogue


CHECKED_AT = "2026-10-01T00:00:00+00:00"


class StreamRecordTests(unittest.TestCase):
    def test_healthy_hls_with_redirect(self):
        entry = {"url": "https://origin.test/live.m3u8", "protocol": "hls"}
        result = HealthResult(
            url=entry["url"],
            status="HEALTHY",
            status_code=200,
            elapsed_ms=183,
            final_url="https://cdn.test/live.m3u8",
            manifest_valid=True,
            detail="valid HLS manifest",
        )
        record = build_stream_record(entry, result, CHECKED_AT)
        self.assertEqual(record["status"], "HEALTHY")
        self.assertEqual(record["http_status"], 200)
        self.assertTrue(record["manifest_valid"])
        self.assertEqual(record["latency_ms"], 183)
        self.assertTrue(record["redirected"])
        self.assertEqual(record["final_host"], "cdn.test")
        self.assertIsNone(record["failure_class"])

    def test_unavailable_keeps_http_status(self):
        entry = {"url": "http://origin.test/live", "protocol": "http"}
        result = HealthResult(
            url=entry["url"],
            status="UNAVAILABLE",
            status_code=404,
            elapsed_ms=55,
            detail="HTTP 404",
        )
        record = build_stream_record(entry, result, CHECKED_AT)
        self.assertEqual(record["status"], "UNAVAILABLE")
        self.assertEqual(record["http_status"], 404)
        self.assertEqual(record["failure_class"], "HTTP 404")

    def test_transient_failure_is_operational_not_structural(self):
        entry = {"url": "https://origin.test/live.m3u8", "protocol": "hls"}
        result = HealthResult(
            url=entry["url"],
            status="TRANSIENT_FAILURE",
            elapsed_ms=None,
            detail="timeout",
        )
        record = build_stream_record(entry, result, CHECKED_AT)
        self.assertEqual(record["status"], "TRANSIENT_FAILURE")
        self.assertEqual(record["failure_class"], "timeout")
        # catalogue_severity stays INFO: a dead stream is not a broken catalogue
        self.assertEqual(record["catalogue_severity"], "INFO")

    def test_unprobed_supported_entry_is_not_checked(self):
        entry = {"url": "https://origin.test/live.m3u8", "protocol": "hls"}
        record = build_stream_record(entry, None, CHECKED_AT)
        self.assertEqual(record["status"], NOT_CHECKED)

    def test_unsupported_protocol_entry_is_flagged(self):
        entry = {"url": "rtmp://origin.test/live", "protocol": "rtmp"}
        record = build_stream_record(entry, None, CHECKED_AT)
        self.assertEqual(record["status"], UNSUPPORTED_PROTOCOL)


class HealthReportTests(unittest.TestCase):
    def test_report_combines_summary_and_streams(self):
        entries = [
            {"url": "https://a.test/live.m3u8", "protocol": "hls"},
            {"url": "http://b.test/live", "protocol": "http"},
            {"url": "rtmp://c.test/live", "protocol": "rtmp"},
        ]
        results = {
            "https://a.test/live.m3u8": HealthResult(
                url="https://a.test/live.m3u8", status="HEALTHY", status_code=200,
                elapsed_ms=10, manifest_valid=True,
            ),
            "http://b.test/live": HealthResult(
                url="http://b.test/live", status="UNAVAILABLE", status_code=503,
                detail="HTTP 503",
            ),
        }
        report = build_health_report(entries, results, CHECKED_AT)
        self.assertEqual(report["checked_at"], CHECKED_AT)
        self.assertTrue(report["network_checks_performed"])
        self.assertEqual(len(report["streams"]), 3)
        self.assertEqual(report["summary"]["healthy"], 1)
        self.assertEqual(report["summary"]["unavailable"], 1)
        self.assertEqual(report["streams"][2]["status"], UNSUPPORTED_PROTOCOL)

    def test_report_without_any_results(self):
        entries = [{"url": "rtmp://c.test/live", "protocol": "rtmp"}]
        report = build_health_report(entries, {}, CHECKED_AT)
        self.assertFalse(report["network_checks_performed"])
        self.assertEqual(report["streams"][0]["status"], UNSUPPORTED_PROTOCOL)


class HealthCommandTests(unittest.TestCase):
    def _write(self, tmp: Path, name: str, text: str) -> Path:
        path = tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_health_command_offline_with_fake_fetcher(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            channels = self._write(
                tmp,
                "channels.json",
                "[\n"
                '  {"name": "A", "url": "https://a.test/live.m3u8", "protocol": "hls"},\n'
                '  {"name": "B", "url": "rtmp://b.test/live", "protocol": "rtmp"}\n'
                "]\n",
            )
            output = tmp / "health-report.json"

            def fake_fetcher(request):
                return {
                    "status_code": 200,
                    "content_type": "application/vnd.apple.mpegurl",
                    "elapsed_ms": 12,
                    "final_url": request.url,
                    "body": b"#EXTM3U\n",
                    "error": "",
                }

            args = catalogue.build_arg_parser().parse_args(
                ["health", "--input", str(channels), "--output", str(output)]
            )
            exit_code = catalogue.run_health_command(args, fetcher=fake_fetcher)
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["summary"]["healthy"], 1)
        self.assertEqual(report["streams"][1]["status"], UNSUPPORTED_PROTOCOL)


if __name__ == "__main__":
    unittest.main()
