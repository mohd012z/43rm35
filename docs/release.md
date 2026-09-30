# Release criteria

A catalogue release requires:

- unit/contract tests passing;
- legacy input parses without fatal errors;
- generated JSON is valid and reproducible;
- validation report clearly states that network checks were not performed;
- dashboard treats catalogue fields as untrusted text;
- no destructive legacy-source migration without a verified replacement.
