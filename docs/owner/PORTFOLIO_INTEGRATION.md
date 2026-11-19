# Portfolio integration and reuse boundaries

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

Voltrl can contribute a **public source-backed research reference** to a portfolio: discrete battery accounting, causal information protocols, model-selection records and claim-specific result audits. It has no implemented runtime integration with another repository in this snapshot. Reuse is a proposal until an interface and corresponding evidence exist.

## Reusable pieces and their limits

| Piece | Useful reuse | Conditions before reuse |
| --- | --- | --- |
| Battery energy/reward conventions | Explain internal vs grid energy, cost and terminal inventory | Preserve units and distinguish the internal step from an AC limit |
| Hour-aware/price-only ablation | Teach training-only model selection and state assumptions | Preserve the selected-K procedure, split and exogenous-price model |
| Audit layers | Separate file integrity, software provenance, table statistics and timing | Carry each audit's actual scope; do not advertise full experiment reproduction |
| Derived handbook pattern | Publish canonical Markdown through existing static Pages | Review renderer/CSP/navigation for the target repository; no application dependency implied |
| Teaching proxy | Demonstrate gross spread minus costs | Keep it labeled USD/bps, synthetic, noncumulative and separate from native MWh profit |

[voltrl.py:105–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L105-L194) [voltrl_benchmark.py:261–295](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L261-L295) [result_bundle_audit.py:75–162](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L75-L162) [docs/index.html:296–299](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L296-L299)

## Public hub entry

A public summary may identify this public repository, its source snapshot, the current documentation route, applicable local checks and dated result-bundle limits. It should link the [evidence ledger](../maintainer/VERIFICATION_EVIDENCE_LEDGER.md), [assumptions](../math-and-physics/ASSUMPTIONS_AND_LIMITS.md) and [roadmap](../../ROADMAP.md). Describe merge/deployment only after exact receipts exist. Do not publish private portfolio counts, source paths, names or derived findings here.

## Shared work without fictional dependencies

Documentation-format validation, CFF validation and exact-revision delivery procedures may be coordinated across repositories. Voltrl's current Python imports remain local modules plus declared third-party packages; no cross-repository orchestration or model API was found. Roadmap items VR-04/05 can share validation design review, but no upstream project is a blocking runtime dependency. Scientific extensions must be assessed on Voltrl's own source/data, not copied claims from another battery repository. [voltrl_benchmark.py:1–47](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1-L47)

## Useful owner indicators

Track audited result-bundle identities, remaining protocol ambiguities, native test outcomes, publication-asset availability, documentation freshness and the latest verified live handbook revision. Avoid a single undifferentiated “healthy” score: local content, CI, merge and publication are separate outcomes. The proposed [recovery drill](BUS_FACTOR_RECOVERY_RUNBOOK.md) gives a measurable continuity check.
