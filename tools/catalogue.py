#!/usr/bin/env python3
"""Parse and structurally validate an Extended M3U catalogue.

Offline by design: this module does not contact stream endpoints.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ATTR_RE = re.compile(r'([\w-]+)=(?:"([^"]*)"|([^\s,]+))')
SMART_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def normalize(text: str) -> str:
    return text.translate(SMART_QUOTES).strip()


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
            channels.append({
                "id": attrs.get("tvg-id", ""),
                "name": display_name or attrs.get("tvg-name", ""),
                "tvg_name": attrs.get("tvg-name", ""),
                "logo": attrs.get("tvg-logo", ""),
                "group": attrs.get("group-title", ""),
                "url": url,
                "protocol": protocol_of(url),
            })
            pending = None
    return channels


def validate(channels: list[dict]) -> dict:
    urls = Counter(c["url"] for c in channels if c["url"])
    identities = Counter((c["id"].casefold(), c["name"].casefold()) for c in channels)
    issues = []
    for i, c in enumerate(channels, start=1):
        flags = []
        if not c["name"]:
            flags.append("MISSING_NAME")
        if not c["id"]:
            flags.append("MISSING_TVG_ID")
        if not c["group"]:
            flags.append("MISSING_GROUP")
        if urls[c["url"]] > 1:
            flags.append("DUPLICATE_URL")
        if identities[(c["id"].casefold(), c["name"].casefold())] > 1:
            flags.append("DUPLICATE_IDENTITY")
        if c["protocol"] not in {"hls", "http", "https", "rtmp", "rtmpe", "rtsp"}:
            flags.append("UNKNOWN_PROTOCOL")
        if flags:
            issues.append({"index": i, "name": c["name"], "flags": flags})

    return {
        "total": len(channels),
        "unique_urls": len(urls),
        "duplicate_url_count": sum(1 for n in urls.values() if n > 1),
        "issue_entries": len(issues),
        "protocols": dict(Counter(c["protocol"] for c in channels)),
        "groups": dict(Counter(c["group"] or "UNSET" for c in channels)),
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
