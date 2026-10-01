"""Bounded, read-only stream probe request and response adapters.

Network execution is intentionally kept separate from this module's pure
configuration/response conversion helpers so tests remain deterministic.
"""

from dataclasses import dataclass
from typing import Optional

from .stream_health import ProbeObservation


MAX_TIMEOUT_SECONDS = 10.0
MAX_BODY_BYTES = 65536
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_BODY_BYTES = 8192


@dataclass(frozen=True)
class ProbeConfig:
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_body_bytes: int = DEFAULT_BODY_BYTES
    follow_redirects: bool = True


@dataclass(frozen=True)
class ProbeRequest:
    url: str
    method: str
    timeout_seconds: float
    max_body_bytes: int
    follow_redirects: bool


def _bounded_timeout(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = DEFAULT_TIMEOUT_SECONDS
    return max(0.1, min(numeric, MAX_TIMEOUT_SECONDS))


def _bounded_body_bytes(value: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = DEFAULT_BODY_BYTES
    return max(1, min(numeric, MAX_BODY_BYTES))


def build_probe_request(url: str, config: Optional[ProbeConfig] = None) -> ProbeRequest:
    """Build a bounded GET-only probe description."""
    cfg = config or ProbeConfig()
    return ProbeRequest(
        url=url.strip(),
        method="GET",
        timeout_seconds=_bounded_timeout(cfg.timeout_seconds),
        max_body_bytes=_bounded_body_bytes(cfg.max_body_bytes),
        follow_redirects=bool(cfg.follow_redirects),
    )


def observation_from_response(
    *,
    url: str,
    status_code: Optional[int] = None,
    content_type: str = "",
    elapsed_ms: Optional[int] = None,
    final_url: str = "",
    body: bytes = b"",
    error: str = "",
) -> ProbeObservation:
    """Safely convert a bounded response sample into a health observation."""
    if body is None:
        body = b""
    if isinstance(body, str):
        text = body
    else:
        text = bytes(body[:MAX_BODY_BYTES]).decode("utf-8", errors="replace")

    return ProbeObservation(
        url=url,
        status_code=status_code,
        content_type=content_type or "",
        elapsed_ms=elapsed_ms,
        final_url=final_url or "",
        body_prefix=text,
        error=error or "",
    )
