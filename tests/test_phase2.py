import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from catalogue import fingerprint, validate


class Phase2ContractTests(unittest.TestCase):
    def test_fingerprint_normalizes_identity(self):
        a = {"id": " TV-1 ", "name": "TV One", "url": "https://example.invalid/live.m3u8"}
        b = {"id": "tv-1", "name": " tv one ", "url": "https://example.invalid/live.m3u8"}
        self.assertEqual(fingerprint(a), fingerprint(b))

    def test_validation_issues_have_severity(self):
        channels = [{
            "id": "",
            "name": "Example",
            "tvg_name": "Example",
            "logo": "",
            "group": "",
            "url": "https://example.invalid/live.m3u8",
            "protocol": "hls",
        }]
        report = validate(channels)
        self.assertTrue(report["issues"])
        self.assertIn("severity", report["issues"][0])
        self.assertIn(report["issues"][0]["severity"], {"INFO", "WARN", "ERROR"})

    def test_validation_exposes_severity_totals(self):
        channels = [{
            "id": "",
            "name": "Example",
            "tvg_name": "Example",
            "logo": "",
            "group": "",
            "url": "https://example.invalid/live.m3u8",
            "protocol": "hls",
        }]
        report = validate(channels)
        self.assertIn("severity_counts", report)
        self.assertGreaterEqual(report["severity_counts"]["WARN"], 1)


if __name__ == "__main__":
    unittest.main()
