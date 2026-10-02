"""Bounded, read-only HTTP transport for stream health probes.

This is the only module in the probe pipeline that touches the network. It
executes a previously bounded ``ProbeRequest`` (GET-only, capped timeout and
body) and converts the response — or the failure — into a plain dict that
``stream_executor`` turns into a health observation.
"""

from __future__ import annotations

import ipaddress
import socket
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


def _is_public_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return ip.is_global


def _validate_destination(url: str) -> None:
    """Reject destinations that can reach local/private network resources."""
    parsed = urlparse(url)
    _validate_scheme(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("bounded probe URL requires a hostname")

    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None

    if literal is not None:
        if not literal.is_global:
            raise ValueError("bounded probe destination must use a public IP address")
        return

    try:
        resolved = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme.lower() == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"unable to resolve bounded probe destination: {hostname}") from exc

    addresses = {entry[4][0] for entry in resolved if entry and len(entry) >= 5 and entry[4]}
    if not addresses:
        raise ValueError(f"unable to resolve bounded probe destination: {hostname}")
    if any(not _is_public_ip(address) for address in addresses):
        raise ValueError("bounded probe destination resolves to a non-public IP address")


def _read_bounded(body: Any, limit: int) -> bytes:
    if limit <= 0:
        return b""
    data = body.read(limit)
    if data is None:
        return b""
    if isinstance(data, str):
        data = data.encode("utf-8", errors="replace")
    return bytes(data)[:limit]


def _request_field(request: Any, name: str, default: Any = None) -> Any:
    if isinstance(request, Mapping):
        return request.get(name, default)
    return getattr(request, name, default)


def fetch_http_probe(request: Any) -> dict:
    """Execute one bounded GET and return a plain observation dict."""
    url = str(_request_field(request, "url", "")).strip()
    timeout = float(_request_field(request, "timeout_seconds", 5.0))
    max_body = int(_request_field(request, "max_body_bytes", 8192))
    method = str(_request_field(request, "method", "GET")).upper()
    if method != "GET":
        raise ValueError("bounded probes are GET-only")

    _validate_destination(url)

    started = time.perf_counter()
    http_request = urlrequest.Request(url, method="GET")
    http_request.add_header("User-Agent", USER_AGENT)

    try:
        response = urlopen(http_request, timeout=timeout)
    except ValueError as exc:
        elapsed = int((time.perf_counter() - started) * 1000)
        return {
            "status_code": None,
            "content_type": "",
            "elapsed_ms": elapsed,
            "final_url": "",
            "body": b"",
            "error": str(exc),
        }
    except Exception as exc:
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
        _validate_destination(str(final_url))

    elapsed = int((time.perf_counter() - started) * 1000)
    return {
        "status_code": status,
        "content_type": content_type or "",
        "elapsed_ms": elapsed,
        "final_url": final_url,
        "body": body,
        "error": "",
    }
