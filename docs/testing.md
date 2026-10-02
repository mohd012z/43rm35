# Testing strategy

- Parser tests use `.invalid` URLs and never depend on external services.
- Validation contract tests cover deterministic normalization, fingerprints and severity.
- CI parses the legacy input to detect regressions against real repository formatting.
- Network availability is outside the structural test suite.

For behavior changes, add a failing regression/contract test before modifying production parser code.
