# Validation policy

Structural validation is deterministic and offline.

Planned severity mapping:

| Finding | Severity |
| --- | --- |
| Duplicate URL | WARN |
| Duplicate normalized identity | WARN |
| Missing `tvg-id` | WARN |
| Missing group | INFO |
| Missing display name | ERROR |
| Missing URL / unknown protocol | ERROR |

Severity describes catalogue data quality, not whether a stream is online, legal, safe, or authorized.
