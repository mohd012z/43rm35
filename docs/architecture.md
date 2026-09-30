# Architecture

```text
playlist input
    |
    v
parser + normalization
    |
    +--> structured channels.json
    |
    +--> structural validation --> validation.json
                                  |
                                  v
                           read-only dashboard
                                  |
                                  v
                    optional authorized clients
```

## Boundaries

- Playlist input is untrusted data.
- Parser/validator performs no network access.
- Generated JSON is the stable boundary for UI/client integrations.
- Dashboard escapes displayed strings and does not execute playlist metadata.
- Stream availability is deliberately not inferred from syntax validation.
