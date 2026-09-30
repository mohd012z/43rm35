# Dashboard

Generate the catalogue and report first:

```bash
python tools/catalogue.py test --output data/channels.json --report reports/validation.json
```

Serve the repository root with a local static HTTP server, for example:

```bash
python -m http.server 8000
```

Then open `/web/` through that local server. The dashboard reads only the generated JSON files; it does not open or probe stream URLs.
