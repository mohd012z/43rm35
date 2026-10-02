import unittest
from unittest.mock import patch

from tools.http_fetcher import fetch_http_probe
from tools.stream_probe import ProbeConfig, build_probe_request


PUBLIC_DNS_RESULT = [
    (2, 1, 6, "", ("93.184.216.34", 443)),
]


class _Response:
    def __init__(self, body=b"#EXTM3U\n", status=200, content_type="application/vnd.apple.mpegurl", url="https://cdn.test/live.m3u8"):
        self._body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.url = url

    def read(self, amount=-1):
        return self._body[:amount]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class HTTPFetcherTests(unittest.TestCase):
    @patch("tools.http_fetcher.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    @patch("tools.http_fetcher.urlopen")
    def test_fetch_returns_executor_response_shape(self, mock_open, _mock_dns):
        mock_open.return_value = _Response()
        request = build_probe_request("https://example.test/live.m3u8", ProbeConfig(max_body_bytes=32))
        result = fetch_http_probe(request)
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["content_type"], "application/vnd.apple.mpegurl")
        self.assertEqual(result["final_url"], "https://cdn.test/live.m3u8")
        self.assertTrue(result["body"].startswith(b"#EXTM3U"))
        self.assertGreaterEqual(result["elapsed_ms"], 0)

    @patch("tools.http_fetcher.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    @patch("tools.http_fetcher.urlopen")
    def test_fetch_honors_body_limit(self, mock_open, _mock_dns):
        mock_open.return_value = _Response(body=b"x" * 1000)
        request = build_probe_request("https://example.test/live.m3u8", ProbeConfig(max_body_bytes=64))
        result = fetch_http_probe(request)
        self.assertLessEqual(len(result["body"]), 64)

    @patch("tools.http_fetcher.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    @patch("tools.http_fetcher.urlopen")
    def test_timeout_is_passed_to_transport(self, mock_open, _mock_dns):
        mock_open.return_value = _Response()
        request = build_probe_request("https://example.test/live.m3u8", ProbeConfig(timeout_seconds=3.5))
        fetch_http_probe(request)
        self.assertEqual(mock_open.call_args.kwargs["timeout"], 3.5)

    def test_non_http_scheme_is_rejected(self):
        request = build_probe_request("rtmp://example.test/live")
        with self.assertRaises(ValueError):
            fetch_http_probe(request)

    def test_loopback_destination_is_rejected_before_transport(self):
        request = build_probe_request("http://127.0.0.1/live.m3u8")
        with patch("tools.http_fetcher.urlopen") as mock_open:
            with self.assertRaises(ValueError):
                fetch_http_probe(request)
            mock_open.assert_not_called()

    def test_private_destination_is_rejected_before_transport(self):
        request = build_probe_request("http://192.168.1.10/live.m3u8")
        with patch("tools.http_fetcher.urlopen") as mock_open:
            with self.assertRaises(ValueError):
                fetch_http_probe(request)
            mock_open.assert_not_called()

    def test_link_local_destination_is_rejected_before_transport(self):
        request = build_probe_request("http://169.254.169.254/latest/meta-data")
        with patch("tools.http_fetcher.urlopen") as mock_open:
            with self.assertRaises(ValueError):
                fetch_http_probe(request)
            mock_open.assert_not_called()

    @patch("tools.http_fetcher.socket.getaddrinfo", return_value=PUBLIC_DNS_RESULT)
    @patch("tools.http_fetcher.urlopen")
    def test_redirect_to_private_destination_is_rejected(self, mock_open, _mock_dns):
        mock_open.return_value = _Response(url="http://127.0.0.1/private.m3u8")
        request = build_probe_request("https://example.test/live.m3u8")
        with self.assertRaises(ValueError):
            fetch_http_probe(request)


if __name__ == "__main__":
    unittest.main()
