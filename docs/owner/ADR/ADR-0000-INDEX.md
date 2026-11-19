# Architecture and scientific decision register

[Handbook](../../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

This register is reconstructed from reviewed source and documentation. The pinned tree contains no original approved ADR series. “Observed” below records implemented practice, not an invented historical approval. Future changes need an owner-reviewed decision record with alternatives, evidence and consequences.

| ID | Status | Decision / consequence | Evidence and follow-up |
| --- | --- | --- | --- |
| ADR-0001 | Observed | Use a discrete internal-energy SOC grid and full charge/idle/discharge actions | [voltrl.py:52–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L52-L194); VR-02 evaluates separate grid-side power limits |
| ADR-0002 | Observed | Separate synthetic sequential policy inputs from historical fixed 24-hour forecasts/schedules | [voltrl_benchmark.py:655–811](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L655-L811); VR-01 formalizes real information availability before operational claims |
| ADR-0003 | Observed | Select K by training-only hour-aware NLL and share it in the price-only ablation | [voltrl_benchmark.py:261–295](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L261-L295); VR-04 proposes stronger selected-K audit |
| ADR-0004 | Observed | Compare finite-horizon reward with training-median terminal inventory; retain oracle as an upper bound | [voltrl_benchmark.py:311–397](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L311-L397) [voltrl_benchmark.py:814–851](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L814-L851) |
| ADR-0005 | Observed | Audit declared result files and three default software paths separately from fresh execution | [artifact_integrity.py:48–77](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L48-L77) [artifact_integrity.py:87–193](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L87-L193) [software_provenance.py:14–18](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L14-L18) [result_bundle_audit.py:75–162](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L75-L162) |
| ADR-0006 | Documentation package decision | Maintain Markdown as canonical and regenerate the static handbook | [Renderer and maintenance contract](../../maintainer/DOCS_MAINTENANCE_RUNBOOK.md); no native algorithm change |
| ADR-0007 | Proposed | Define an explicit publication-asset and backup-maintainer recovery record | [Recovery runbook](../BUS_FACTOR_RECOVERY_RUNBOOK.md); VR-07, owner assignment pending |

For a new ADR, state the problem, alternatives, evidence/source SHA, chosen scope, expected benefits, risks, measurable validation and whether owner approval exists. Include units, information timing and objective changes for scientific proposals. Keep proposed dates/staffing separate from implemented behavior.
