"""Bounded, read-only HTTP transport for stream health probes.

This is the only module in the probe pipeline that touches the network. It
executes a previously bounded ``ProbeRequest`` (GET-only, capped timeout and
body) and converts the response — or the failure — into a plain dict that
``stream_executor`` turns into a health observation.

Design rules (see docs/limits.md):
- Scheme-restricted: http/https only. Anything else is a programming error
  (``ValueError``) and never reaches the transport.
- Timeouts and body limits come from the request; they are already clamped by
  ``stream_probe.build_probe_request``.
- Redirects are followed by the transport (urllib default); the final URL is
  reported so the classifier can record the redirect.
- Failures are returned, not raised: a network error is operational data
  (``error`` field), never a catalogue structural error.
"""

from __future__ import annotations

import time
from typing import Any, Mapping
from urllib import request as urlrequest
from urllib.parse import urlparse
from urllib.request import urlopen

ALLOWED_SCHEMES = {"http", "https"}
USER_AGENT = "43rm35-catalogue-probe/1.0 (+read-only; bounded health check)"


def _validate_scheme(url: str) -> None:
    scheme = urlparse(url).scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"unsupported scheme for bounded probe: {scheme or 'missing'} (allowed: http, https)"
        )


def _read_bounded(body: Any, limit: int) -> bytes:
    """Read at most ``limit`` bytes from a urllib response body."""
    if limit <= 0:
        return b""
    data = body.read(limit)
    if data is None:
        return b""
    if isinstance(data, str):
        data = data.encode("utf-8", errors="replace")
    return bytes(data)[:limit]


def _request_field(request: Any, name: str, default: Any = None) -> Any:
    """Read a field from a ``ProbeRequest`` dataclass or a plain mapping."""
    if isinstance(request, Mapping):
        return request.get(name, default)
    return getattr(request, name, default)


def fetch_http_probe(request: Any) -> dict:
    """Execute one bounded GET and return a plain observation dict.

    Accepts a ``stream_probe.ProbeRequest`` or an equivalent mapping.
    Returns keys: ``status_code``, ``content_type``, ``elapsed_ms``,
    ``final_url``, ``body`` (capped), and ``error`` (empty on success).
    Raises ``ValueError`` for non-http(s) URLs before any network I/O.
    """
    url = str(_request_field(request, "url", "")).strip()
    timeout = float(_request_field(request, "timeout_seconds", 5.0))
    max_body = int(_request_field(request, "max_body_bytes", 8192))
    method = str(_request_field(request, "method", "GET")).upper()
    if method != "GET":
        raise ValueError("bounded probes are GET-only")

    _validate_scheme(url)

    started = time.perf_counter()
    http_request = urlrequest.Request(url, method="GET")
    http_request.add_header("User-Agent", USER_AGENT)

    try:
        response = urlopen(http_request, timeout=timeout)
    except ValueError as exc:
        # urlopen raises ValueError for malformed URLs — surface as error data.
        elapsed = int((time.perf_counter() - started) * 1000)
        return {
            "status_code": None,
            "content_type": "",
            "elapsed_ms": elapsed,
            "final_url": "",
            "body": b"",
            "error": str(exc),
        }
    except Exception as exc:  # boundary: third-party transport (URLError, socket.timeout, ...)
        elapsed = int((time.perf_counter() - started) * 1000)
        message = str(exc) or exc.__class__.__name__
        return {
            "status_code": getattr(exc, "code", None),
            "content_type": "",
            "elapsed_ms": elapsed,
            "final_url": "",
            "body": b"",
            "error": message,
        }

    with response:
        status = int(getattr(response, "status", None) or getattr(response, "getcode", lambda: None)() or 200)
        headers = getattr(response, "headers", None)
        content_type = headers.get("Content-Type", "") if headers is not None else ""
        body = _read_bounded(response, max_body)
        geturl = getattr(response, "geturl", None)
        final_url = (geturl() if callable(geturl) else None) or getattr(response, "url", None) or url

    elapsed = int((time.perf_counter() - started) * 1000)
    return {
        "status_code": status,
        "content_type": content_type or "",
        "elapsed_ms": elapsed,
        "final_url": final_url,
        "body": body,
        "error": "",
    }
