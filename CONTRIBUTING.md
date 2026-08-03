# Contributing

Contributions should preserve VoltRL's auditability: a reader must be able to
identify the data snapshot, information protocol, objective, code version, and
validation evidence behind a reported result.

## Good Contributions

- Improve provenance, contract, or artifact-integrity checks.
- Add tests for a bounded behavior or an explicitly documented protocol.
- Clarify assumptions without presenting the benchmark as a live bidding system.
- Add public data or references with their license, checksum, and retrieval context.

## Pull Request Checklist

- [ ] The README and result-manifest conventions remain accurate.
- [ ] Synthetic and historical information boundaries are explicit.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] Any generated result bundle passes `result_bundle_audit.py`.
- [ ] No credentials, private market data, or unverifiable claims are included.
