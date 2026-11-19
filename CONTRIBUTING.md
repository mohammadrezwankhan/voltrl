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


## Source-pinned documentation changes

Read the [handbook](docs/INDEX.md), [maintenance runbook](docs/maintainer/DOCS_MAINTENANCE_RUNBOOK.md) and [release playbook](docs/maintainer/CI_CD_AND_RELEASE_PLAYBOOK.md). Keep Markdown canonical, regenerate `docs/reference/index.html`, and run `python docs/reference/build_reference.py --check`. Preserve historical result identities and distinguish source review, measured execution and proposed work.

Use a fresh directory for new benchmark outputs. Record all native commands and their environment/revision; a successful stored-bundle audit does not replace a fresh external-data reproduction. For documentation-only work, keep application, scientific, workflow, dependency and license changes in separately reviewed proposals. The [roadmap](ROADMAP.md) carries identified follow-up work.

The active signature ruleset and all applicable branch/check/review requirements still apply. Refresh exact-head evidence before integration; do not bypass checks or rewrite attribution to pass a policy. Current classic-protection details must be read through an authorized surface when the API is inaccessible.
