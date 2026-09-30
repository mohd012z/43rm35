# 43rm35 Stream Catalogue

43rm35 is being modernized from a legacy Extended M3U file into a maintainable stream catalogue and validation toolkit.

## Goals

- Parse Extended M3U metadata into structured JSON.
- Normalize inconsistent quotes and metadata.
- Detect duplicate stream URLs and channel identities.
- Classify protocols without automatically contacting endpoints.
- Produce machine-readable reports suitable for a web UI or authorized player client.
- Keep the original playlist as legacy input until migration is verified.

## Usage

```bash
python tools/catalogue.py test --output data/channels.json --report reports/validation.json
python -m unittest discover -s tests -v
```

The validator is intentionally offline by default. It checks structure and metadata but does not probe third-party stream endpoints. Only add network health checks for sources you are authorized to access and validate.

## Roadmap

1. Legacy parser and normalization
2. Duplicate and metadata validation
3. CI tests
4. Split verified/authorized playlists from legacy data
5. Web catalogue/dashboard
6. Optional feed integration with NovaStreamerTV
