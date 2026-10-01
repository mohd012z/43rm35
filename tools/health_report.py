"""Stream health reporting: per-stream records + JSON report assembly.

Keeps the invariant that network failure is operational information, never
catalogue corruption: every stream record carries ``catalogue_severity:
INFO`` regardless of probe outcome.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence
from urllib.parse import urlparse

from .stream_health import HealthResult, summarize_health

NOT_CHECKED = "NOT_CHECKED"
UNSUPPORTED_PROTOCOL = "UNSUPPORTED_PROTOCOL"
PROBEABLE_PROTOCOLS = frozenset({"hls", "http", "https"})


def build_stream_record(
    entry: Mapping,
    result: Optional[HealthResult],
    checked_at: str,
) -> dict:
    """Build one machine-consumable stream health record.

    ``result`` is None when no probe ran for this entry (offline mode or an
    unsupported protocol).
    """
    url = str(entry.get("url", ""))
    protocol = str(entry.get("protocol", "unknown")).lower()

    if result is None:
        status = UNSUPPORTED_PROTOCOL if protocol not in PROBEABLE_PROTOCOLS else NOT_CHECKED
        return {
            "url": url,
            "name": str(entry.get("name", "")),
            "protocol": protocol,
            "status": status,
            "http_status": None,
            "manifest_valid": False,
            "latency_ms": None,
            "redirected": False,
            "final_host": urlparse(url).netloc,
            "checked_at": checked_at,
            "failure_class": None,
            "detail": "",
            "catalogue_severity": "INFO",
        }

    final_url = result.final_url or url
    base = urlparse(final_url)
    redirected = bool(result.final_url) and result.final_url.strip() != url.strip()

    if result.status in {"HEALTHY", "DEGRADED"}:
        failure_class: Optional[str] = None
    else:
        failure_class = result.detail or result.status

    return {
        "url": url,
        "name": str(entry.get("name", "")),
        "protocol": protocol,
        "status": result.status,
        "http_status": result.status_code,
        "manifest_valid": result.manifest_valid,
        "latency_ms": result.elapsed_ms,
        "redirected": redirected,
        "final_host": base.netloc,
        "checked_at": checked_at,
        "failure_class": failure_class,
        "detail": result.detail,
        "catalogue_severity": result.catalogue_severity,
    }


def build_health_report(
    entries: Sequence[Mapping],
    results: Mapping[str, HealthResult],
    checked_at: str,
) -> dict:
    """Assemble the full health report for a catalogue snapshot."""
    streams = [build_stream_record(entry, results.get(str(entry.get("url", ""))), checked_at) for entry in entries]

    probed = list(results.values())
    summary = summarize_health(probed)
    status_counts: dict[str, int] = {}
    for stream in streams:
        status_counts[stream["status"]] = status_counts.get(stream["status"], 0) + 1

    summary["unsupported_protocol"] = status_counts.get(UNSUPPORTED_PROTOCOL, 0)
    summary["not_checked"] = status_counts.get(NOT_CHECKED, 0)

    return {
        "checked_at": checked_at,
        "total_streams": len(streams),
        "network_checks_performed": summary["network_checks_performed"],
        "summary": summary,
        "streams": streams,
    }
