"""Non-destructive stream-health classification.

This module deliberately separates network observations from catalogue
correctness. Temporary reachability failures are operational information,
not structural catalogue errors.
"""

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class ProbeObservation:
    url: str
    status_code: Optional[int] = None
    content_type: str = ""
    elapsed_ms: Optional[int] = None
    final_url: str = ""
    body_prefix: str = ""
    error: str = ""


@dataclass(frozen=True)
class HealthResult:
    url: str
    status: str
    catalogue_severity: str = "INFO"
    manifest_valid: bool = False
    status_code: Optional[int] = None
    elapsed_ms: Optional[int] = None
    final_url: str = ""
    detail: str = ""


def _looks_like_hls(observation: ProbeObservation) -> bool:
    content_type = observation.content_type.lower()
    body = observation.body_prefix.lstrip("\ufeff\r\n\t ")
    return (
        "mpegurl" in content_type
        or observation.url.lower().split("?", 1)[0].endswith(".m3u8")
        or body.startswith("#EXTM3U")
    )


def _valid_hls_manifest(observation: ProbeObservation) -> bool:
    return observation.body_prefix.lstrip("\ufeff\r\n\t ").startswith("#EXTM3U")


def classify_observation(observation: ProbeObservation) -> HealthResult:
    """Classify one already-collected network observation without doing I/O."""
    error = observation.error.strip().lower()
    if error:
        transient_tokens = ("timeout", "timed out", "temporary", "reset", "dns", "connection")
        transient = any(token in error for token in transient_tokens)
        return HealthResult(
            url=observation.url,
            status="TRANSIENT_FAILURE" if transient else "UNAVAILABLE",
            status_code=observation.status_code,
            elapsed_ms=observation.elapsed_ms,
            final_url=observation.final_url,
            detail=observation.error,
        )

    code = observation.status_code
    if code is None:
        return HealthResult(
            url=observation.url,
            status="TRANSIENT_FAILURE",
            elapsed_ms=observation.elapsed_ms,
            final_url=observation.final_url,
            detail="no HTTP status observed",
        )

    if code < 200 or code >= 400:
        return HealthResult(
            url=observation.url,
            status="UNAVAILABLE",
            status_code=code,
            elapsed_ms=observation.elapsed_ms,
            final_url=observation.final_url,
            detail=f"HTTP {code}",
        )

    if _looks_like_hls(observation):
        manifest_valid = _valid_hls_manifest(observation)
        return HealthResult(
            url=observation.url,
            status="HEALTHY" if manifest_valid else "DEGRADED",
            manifest_valid=manifest_valid,
            status_code=code,
            elapsed_ms=observation.elapsed_ms,
            final_url=observation.final_url,
            detail="valid HLS manifest" if manifest_valid else "response is not a valid HLS manifest",
        )

    return HealthResult(
        url=observation.url,
        status="HEALTHY",
        status_code=code,
        elapsed_ms=observation.elapsed_ms,
        final_url=observation.final_url,
        detail="reachable HTTP resource",
    )


def summarize_health(results: Sequence[HealthResult]) -> dict:
    """Summarize operational health independently of catalogue validation."""
    counts = {
        "healthy": 0,
        "degraded": 0,
        "unavailable": 0,
        "transient_failure": 0,
    }
    for result in results:
        key = result.status.lower()
        if key in counts:
            counts[key] += 1

    return {
        "network_checks_performed": bool(results),
        "checked": len(results),
        **counts,
    }
