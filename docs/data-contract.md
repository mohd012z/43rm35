# Generated data contract

Each channel record contains:

- `id`: source `tvg-id` when present.
- `name`: display name.
- `tvg_name`: source `tvg-name` when present.
- `logo`: source logo reference; not automatically fetched.
- `group`: source category/group.
- `url`: source URL/string, treated as untrusted data.
- `protocol`: parser classification.

Generated output is UTF-8 JSON. Consumers should tolerate additive report fields but should not assume a stream is reachable merely because a record exists.
