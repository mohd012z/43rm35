#!/usr/bin/env python3
"""Parse and structurally validate an Extended M3U catalogue.

Offline by design: this module does not contact stream endpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ATTR_RE = re.compile(r'([\w-]+)=(?:"([^"]*)"|([^\s,]+))')
SMART_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})
SUPPORTED_PROTOCOLS = {"hls", "http", "https", "rtmp", "rtmpe", "rtsp"}


def normalize(text: str) -> str:
    return text.translate(SMART_QUOTES).strip()


def _identity_part(value: object) -> str:
    """Return a stable, case-insensitive identity component."""
    return " ".join(normalize(str(value or "")).casefold().split())


def fingerprint(channel: dict) -> str:
    """Build a stable fingerprint from normalized channel identity fields.

    The URL is included so two distinct stream variants are not silently
    collapsed into one record. Cosmetic whitespace/case changes do not alter
    the fingerprint.
    """
    payload = "\x1f".join(
        (
            _identity_part(channel.get("id")),
            _identity_part(channel.get("name")),
            normalize(str(channel.get("url") or "")).strip(),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def protocol_of(url: str) -> str:
    scheme = urlparse(url.split()[0]).scheme.lower()
    if scheme in {"http", "https"} and ".m3u8" in url.lower():
        return "hls"
    return scheme or "unknown"


def parse_extinf(line: str) -> tuple[dict[str, str], str]:
    line = normalize(line)
    head, sep, name = line.partition(",")
    attrs = {}
    for match in ATTR_RE.finditer(head):
        attrs[match.group(1)] = normalize(match.group(2) or match.group(3) or "")
    return attrs, normalize(name) if sep else ""


def parse_m3u(path: Path) -> list[dict]:
    lines = [normalize(x) for x in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    channels: list[dict] = []
    pending: tuple[dict[str, str], str] | None = None

    for line in lines:
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            pending = parse_extinf(line)
            continue
        if line.startswith("#"):
            continue
        if pending:
            attrs, display_name = pending
            url = line
            channel = {
                "id": attrs.get("tvg-id", ""),
                "name": display_name or attrs.get("tvg-name", ""),
                "tvg_name": attrs.get("tvg-name", ""),
                "logo": attrs.get("tvg-logo", ""),
                "group": attrs.get("group-title", ""),
                "url": url,
                "protocol": protocol_of(url),
            }
            channel["fingerprint"] = fingerprint(channel)
            channels.append(channel)
            pending = None
    return channels


def _issue_severity(flags: list[str]) -> str:
    """Classify a channel issue bundle by its most important finding."""
    if "MISSING_NAME" in flags or "UNKNOWN_PROTOCOL" in flags:
        return "ERROR"
    if any(flag in flags for flag in ("MISSING_TVG_ID", "MISSING_GROUP", "DUPLICATE_URL", "DUPLICATE_IDENTITY")):
        return "WARN"
    return "INFO"


def validate(channels: list[dict]) -> dict:
    urls = Counter(c.get("url", "") for c in channels if c.get("url"))
    identities = Counter(
        (_identity_part(c.get("id")), _identity_part(c.get("name")))
        for c in channels
    )
    issues = []
    severity_counts = Counter({"INFO": 0, "WARN": 0, "ERROR": 0})

    for i, c in enumerate(channels, start=1):
        flags = []
        name = c.get("name", "")
        channel_id = c.get("id", "")
        group = c.get("group", "")
        url = c.get("url", "")
        protocol = c.get("protocol", "unknown")

        if not name:
            flags.append("MISSING_NAME")
        if not channel_id:
            flags.append("MISSING_TVG_ID")
        if not group:
            flags.append("MISSING_GROUP")
        if url and urls[url] > 1:
            flags.append("DUPLICATE_URL")
        if identities[(_identity_part(channel_id), _identity_part(name))] > 1:
            flags.append("DUPLICATE_IDENTITY")
        if protocol not in SUPPORTED_PROTOCOLS:
            flags.append("UNKNOWN_PROTOCOL")

        if flags:
            severity = _issue_severity(flags)
            severity_counts[severity] += 1
            issues.append({
                "index": i,
                "name": name,
                "fingerprint": c.get("fingerprint") or fingerprint(c),
                "severity": severity,
                "flags": flags,
            })

    return {
        "total": len(channels),
        "unique_urls": len(urls),
        "duplicate_url_count": sum(1 for n in urls.values() if n > 1),
        "issue_entries": len(issues),
        "severity_counts": dict(severity_counts),
        "protocols": dict(Counter(c.get("protocol", "unknown") for c in channels)),
        "groups": dict(Counter(c.get("group") or "UNSET" for c in channels)),
        "issues": issues,
        "network_checks_performed": False,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/channels.json"))
    parser.add_argument("--report", type=Path, default=Path("reports/validation.json"))
    args = parser.parse_args()

    channels = parse_m3u(args.input)
    report = validate(channels)
    write_json(args.output, channels)
    write_json(args.report, report)
    print(json.dumps({k: v for k, v in report.items() if k != "issues"}, indent=2))
    return 0 if channels else 1


if __name__ == "__main__":
    raise SystemExit(main())
