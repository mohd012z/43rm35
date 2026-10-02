import json
import subprocess
import sys
import tempfile
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class DashboardSmokeTests(unittest.TestCase):
    def test_generated_dashboard_assets_are_served_and_parseable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "web").mkdir()
            (root / "data").mkdir()
            (root / "reports").mkdir()
            (root / "web" / "index.html").write_text(
                (ROOT / "web" / "index.html").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "catalogue.py"),
                    str(ROOT / "test"),
                    "--output",
                    str(root / "data" / "channels.json"),
                    "--report",
                    str(root / "reports" / "validation.json"),
                ],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(root), **kwargs)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                html = urlopen(f"{base}/web/index.html", timeout=2).read().decode("utf-8")
                channels = json.loads(urlopen(f"{base}/data/channels.json", timeout=2).read())
                report = json.loads(urlopen(f"{base}/reports/validation.json", timeout=2).read())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

            self.assertIn("43rm35 Catalogue", html)
            self.assertIn("../data/channels.json", html)
            self.assertIn("../reports/validation.json", html)
            self.assertIsInstance(channels, list)
            self.assertGreater(len(channels), 0)
            self.assertEqual(report["total"], len(channels))
            self.assertIn("unique_urls", report)
            self.assertIn("issue_entries", report)


if __name__ == "__main__":
    unittest.main()
