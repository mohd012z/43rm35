# Security and trust boundaries

The project treats playlist metadata and URLs as untrusted input.

- Do not interpolate channel metadata into executable HTML or JavaScript.
- Do not automatically follow, probe, proxy, restream, or redistribute third-party URLs.
- Network health checking, if added later, must use an explicit allowlist of authorized sources, strict timeouts, redirect limits, and private-network/loopback blocking.
- Keep generated catalogue data separate from application secrets.
- CI currently performs parsing and unit tests only.
