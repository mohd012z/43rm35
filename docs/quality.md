# Data quality dimensions

The catalogue reports separate dimensions instead of one opaque score:

- completeness: required/optional metadata presence;
- uniqueness: duplicate URLs and normalized identities;
- syntax: parsable records and recognized protocols;
- provenance: legacy vs curated input (future field);
- availability: intentionally unknown in offline validation.

This avoids presenting syntactically valid entries as verified live streams.
