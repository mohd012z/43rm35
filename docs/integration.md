# Client integration

Consumers such as a web UI or an authorized player should consume `data/channels.json` rather than parse the legacy M3U themselves.

Recommended client contract:

1. Fetch a versioned catalogue artifact.
2. Validate required fields locally.
3. Filter by group/protocol as needed.
4. Treat availability as unknown unless an authorized health source explicitly supplies it.
5. Never infer authorization from the presence of a URL in the legacy source.

This keeps parsing, normalization and data-quality policy centralized in 43rm35 while playback remains a separate responsibility.
