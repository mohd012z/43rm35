# Local operation

```bash
python -m unittest discover -s tests -v
python tools/catalogue.py test --output data/channels.json --report reports/validation.json
python -m http.server 8000
```

The generated `data/channels.json` and `reports/validation.json` can then be viewed from `/web/`.

Do not treat successful parsing as a live-stream health check.
