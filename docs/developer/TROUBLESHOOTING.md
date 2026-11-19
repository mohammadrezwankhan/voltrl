# Troubleshooting by failed contract

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

Keep the exact command, source SHA, input identity and full error output. Diagnose a failed verifier before changing any recorded digest or benchmark setting.

| Symptom | Likely cause and evidence | Next action |
| --- | --- | --- |
| Historical Git object cannot be read | Archive/shallow clone omits manifest's generating commit | Use a full clone or fetch missing history; preserve the manifest's recorded SHA |
| Input filename mismatch | OPSD file was not saved with the source record's required basename | Rename the unchanged official bytes to the required basename, then verify |
| Input SHA mismatch | Wrong package/file, modified bytes or incomplete download | Obtain the exact versioned file; do not rewrite the expected digest |
| Quantile edges are not distinct | Too few distinct prices for requested K | Inspect training data and lower K explicitly for an exploratory run; do not claim it is the original protocol |
| Too few prices / timestamps not hourly | Small or irregular frame | Supply sufficient consecutive hourly UTC data; disclose preprocessing |
| Zero-prior unobserved transition error | Some state/hour has no outgoing count | Use the declared positive smoothing or establish full row coverage |
| Initial SOC off-grid | E0 is not one of 0,q,…,C | Choose a valid grid value; 250 MWh is invalid for default q=100 |
| Action alignment error | Actions supplied before a frame was reordered or cleaned | Align actions to the already validated chronological frame |
| AR history/lag failure | Index precedes needed lags or time horizon exceeds timestamp array | Provide causal history and future timestamps; future actual prices are not forecast inputs |
| VI/PI fails convergence | Invalid solver parameters or iteration cap reached | Inspect residual/logs; do not report incomplete solve as optimal |
| Artifact audit fails | Missing/changed declared file, malformed inventory or canonicalization mismatch | Compare to immutable bundle; restore intended bytes or create an explicitly new experiment |
| One audit says passed but historical says skipped | Revision 1 lacks forecast protocol/tables | Report the skip; use revision 2 for that specific stored contract |
| Handbook `--check` fails | Canonical chapter, manifest, CSS or renderer changed | Regenerate and review generated HTML; do not edit HTML as a separate source |
| Browser checkpoints fail after a slider edit | Current parameters no longer match the lesson preset | Reload the preset and use its declared model time; review actual values/tolerances |

[software_provenance.py:49–78](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L49-L78) [input_provenance.py:56–86](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L56-L86) [voltrl.py:217–266](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L217-L266) [voltrl.py:591–599](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L591-L599) [voltrl_benchmark.py:105–124](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L105-L124) [voltrl_benchmark.py:400–450](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L400-L450) [voltrl_benchmark.py:591–652](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L591-L652)

## Environment and numerical messages

The local Python 3.12.14/pandas 3.1.1 review passed all tests but emitted deprecation warnings for `Timestamp.dayofweek` and `dayofyear` in `_seasonal_features`. Treat that as future maintenance debt, not a present numerical failure; changing source is outside this documentation change. [voltrl_benchmark.py:517–531](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L517-L531)

`voltrl.py` catches run-time exceptions, logs a traceback and returns 1; argparse usage errors return 2. The benchmark CLI lets run exceptions surface. Individual audit CLIs report failures and return nonzero. Direct low-level calls do not all share one uniform validation/error contract: for example, the oracle's off-grid initial SOC lookup can fail differently from `nearest_soc_index`. Use the documented validated paths and preserve traceback context. [voltrl.py:648–666](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L648-L666) [voltrl.py:1206–1225](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1206-L1225) [voltrl_benchmark.py:1853–1863](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1853-L1863)

## CI and publication

The metadata policy logs forbidden/missing commit metadata and its checked-commit count; it does not echo its chosen revision range. Reconstruct that range from the event inputs and the workflow's event branches if needed. A historical successful check is not evidence for a new docs head. [.github/workflows/no-codex-attribution.yml:24–99](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/no-codex-attribution.yml#L24-L99)

The active all-branch ruleset requires signatures and exposes no bypass. If a supported commit route yields unsigned commits, use an ordinary verified route permitted by the repository or preserve the candidate for the owner; do not weaken the rule. Classic-protection API access was denied to the current integration, so its unknown requirements must be inspected before delivery. [Release playbook](../maintainer/CI_CD_AND_RELEASE_PLAYBOOK.md).
