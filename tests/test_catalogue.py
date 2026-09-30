import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from catalogue import parse_m3u, validate


SAMPLE = '''#EXTM3U
#EXTINF:-1 tvg-id="one" tvg-name="One" group-title="Demo",One
https://example.invalid/live/one.m3u8
#EXTINF:-1 tvg-id="two" tvg-name="Two" group-title="Demo",Two
https://example.invalid/live/one.m3u8
'''


class CatalogueTests(unittest.TestCase):
    def test_parse_and_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.m3u"
            path.write_text(SAMPLE, encoding="utf-8")
            channels = parse_m3u(path)
        self.assertEqual(2, len(channels))
        self.assertEqual("One", channels[0]["name"])
        self.assertEqual("hls", channels[0]["protocol"])

    def test_duplicate_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.m3u"
            path.write_text(SAMPLE, encoding="utf-8")
            channels = parse_m3u(path)
        report = validate(channels)
        self.assertEqual(1, report["duplicate_url_count"])
        self.assertFalse(report["network_checks_performed"])


if __name__ == "__main__":
    unittest.main()
