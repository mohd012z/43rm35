# Phase 2 validation design

The catalogue remains offline-first. Validation findings are assigned a severity:

- `INFO`: informational quality signal that does not block catalogue generation.
- `WARN`: incomplete or duplicate metadata requiring review.
- `ERROR`: malformed entries that cannot be safely represented by the catalogue contract.

Channel fingerprints normalize identity fields before hashing so case and surrounding whitespace do not create false distinctions. The fingerprint is for catalogue deduplication only; it is not an authentication or security primitive.

The web dashboard is read-only and must escape catalogue strings before inserting them into HTML. It does not contact channel stream URLs.
