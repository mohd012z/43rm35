"""Opt-in bounded executor for HTTP/HLS stream health probes.

The executor is disabled by default. It only schedules HTTP/HLS targets and
converts fetch failures into operational health observations rather than
catalogue validation errors.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Optional

from .stream_health import classify_observation, summarize_health
from .stream_probe import ProbeConfig, build_probe_request, observation_from_response


MAX_WORKERS = 8
DEFAULT_WORKERS = 4
SUPPORTED_PROTOCOLS = frozenset({"hls", "http", "https"})


@dataclass(frozen=True)
class ExecutorConfig:
    enabled: bool = False
    max_workers: int = DEFAULT_WORKERS
    timeout_seconds: float = 5.0
    max_body_bytes: int = 8192

    def bounded_workers(self) -> int:
        try:
            workers = int(self.max_workers)
        except (TypeError, ValueError):
            workers = DEFAULT_WORKERS
        return max(1, min(workers, MAX_WORKERS))


def select_probe_targets(entries: Iterable[Mapping]) -> list[dict]:
    """Return only HTTP/HLS catalogue entries suitable for this executor."""
    selected = []
    for entry in entries:
        protocol = str(entry.get("protocol", "")).strip().lower()
        url = str(entry.get("url", "")).strip()
        if protocol in SUPPORTED_PROTOCOLS and url:
            selected.append(dict(entry))
    return selected


def _probe_one(entry: Mapping, config: ExecutorConfig, fetcher: Callable) -> object:
    url = str(entry.get("url", "")).strip()
    request = build_probe_request(
        url,
        ProbeConfig(
            timeout_seconds=config.timeout_seconds,
            max_body_bytes=config.max_body_bytes,
            follow_redirects=True,
        ),
    )
    try:
        response = fetcher(request)
        if response is None:
            response = {}
        observation = observation_from_response(
            url=url,
            status_code=response.get("status_code"),
            content_type=response.get("content_type", ""),
            elapsed_ms=response.get("elapsed_ms"),
            final_url=response.get("final_url", ""),
            body=response.get("body", b""),
            error=response.get("error", ""),
        )
    except Exception as exc:  # boundary: third-party network adapter
        observation = observation_from_response(url=url, error=str(exc) or exc.__class__.__name__)
    return classify_observation(observation)


def run_probe_targets(
    entries: Iterable[Mapping],
    *,
    config: Optional[ExecutorConfig] = None,
    fetcher: Optional[Callable] = None,
) -> dict:
    """Run bounded probes when explicitly enabled and return a health summary."""
    cfg = config or ExecutorConfig()
    targets = select_probe_targets(entries)

    if not cfg.enabled:
        return {
            "network_checks_performed": False,
            "checked": 0,
            "healthy": 0,
            "degraded": 0,
            "unavailable": 0,
            "transient_failure": 0,
        }

    if not targets:
        return {
            "network_checks_performed": True,
            "checked": 0,
            "healthy": 0,
            "degraded": 0,
            "unavailable": 0,
            "transient_failure": 0,
        }

    if fetcher is None:
        raise ValueError("enabled stream probing requires an explicit fetcher")

    results = []
    with ThreadPoolExecutor(max_workers=cfg.bounded_workers()) as pool:
        futures = [pool.submit(_probe_one, entry, cfg, fetcher) for entry in targets]
        for future in as_completed(futures):
            results.append(future.result())

    return summarize_health(results)


def probe_entries(
    entries: Iterable[Mapping],
    *,
    config: Optional[ExecutorConfig] = None,
    fetcher: Callable,
) -> dict[str, object]:
    """Probe all supported entries and return per-URL health results.

    Unlike :func:`run_probe_targets`, this returns the individual
    :class:`~tools.stream_health.HealthResult` objects (keyed by URL) so
    callers can build per-stream reports. It always runs (callers decide
    opt-in) and never probes rtmp/rtsp/other entries.
    """
    cfg = config or ExecutorConfig()
    targets = select_probe_targets(entries)
    if not targets:
        return {}

    results: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=cfg.bounded_workers()) as pool:
        submitted = [(entry, pool.submit(_probe_one, entry, cfg, fetcher)) for entry in targets]
        for entry, future in submitted:
            results[str(entry.get("url", ""))] = future.result()
    return results
