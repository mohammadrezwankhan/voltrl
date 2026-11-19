# Verification evidence ledger

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

This ledger separates observed local execution, recorded historical evidence and work still needed for delivery. Its review target is source `8058e89e4d3516825a400fe86ac45d2e36b6bef0`; it does not claim a documentation commit, merge or deployment identity. Exact candidate fingerprints, command logs and independent QA receipts belong to the external delivery record.

## Executed during the 2026-11-19 review

| Check | Observation | What it supports / limit |
| --- | --- | --- |
| Canonical source identity | 178 Git-tree entries; 146 blob payloads hash-verified | Complete path accounting; semantic dispositions differ by artifact |
| Existing unit tests | `python -m unittest discover -s tests -v`: **80 tests passed** | Existing solver, causality, validation, tampering and audit fixtures; no coverage-percentage claim |
| Revision-1 aggregate audit | Four passed, historical forecast check explicitly skipped | Applicable stored contracts, not the later historical protocol |
| Revision-2 aggregate audit | All five checks passed | Stored table/inventory/source/timing checks, not a fresh experiment |
| Native help | All nine module `--help` commands succeeded | CLI parsing/declared options, not every argument combination |
| Legacy smoke | 1000 synthetic hours, seed 7, four fixed bins; successful outputs and VI/PI convergence | Small legacy calculation, not primary benchmark replication |
| Native finite-horizon example | 2400 synthetic hours, seed 7, fixed four bins; feasible SOC and oracle-bound assertion passed | Concrete default-primary battery example on one synthetic path |
| Portfolio validator | Six source-linked paths validated | Config/embed/source-path/SVG checks, not browser execution |
| Active browser pure model | Eight market-mode lesson checkpoints passed; embedded JSON equals config | Actual inline arithmetic only; no UI/clipboard/storage test |

Relevant test definitions: [tests/test_voltrl.py:22–118](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_voltrl.py#L22-L118) [tests/test_voltrl_benchmark.py:22–122](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_voltrl_benchmark.py#L22-L122) [tests/test_numeric_and_causal_inputs.py:16–126](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_numeric_and_causal_inputs.py#L16-L126). The full test directory includes adversarial contract, path, digest and result-summary fixtures; their scope is accounted in [source evidence](../SOURCE_EVIDENCE.md).

## Stored bundle identity

| Bundle | Recorded generating source | Declared outputs | Applicable audit |
| --- | --- | ---: | --- |
| `results_revision` | `2e01d9fcec78adbf30357a4cda05b19f6d572b04` | 20: 10 CSV + 5 PNG + 5 PDF | Configuration, synthetic statistics, artifact integrity, software provenance; historical forecast skip |
| `results_revision2` | `70fa9609a1a122055f50f7897720eefc97cbb3e0` | 25: 13 CSV + 6 PNG + 6 PDF | All five, including historical forecast contract |

These manifests record Windows/Python 3.12.13 with NumPy 2.5.1, pandas 3.0.1 and Matplotlib 3.11.0. Current pinned requirements and the local review environment differ. Clean source verification reads the recorded historical Git blobs, which is why older result source remains auditable after code changes. [results_revision/experiment_manifest.json:1–125](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/results_revision/experiment_manifest.json#L1-L125) [results_revision2/experiment_manifest.json:1–140](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/results_revision2/experiment_manifest.json#L1-L140) [software_provenance.py:163–252](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L163-L252)

The revision-2 historical contract checked 90,720 detail rows and 3,780 fixed forecast blocks. No manual review of every CSV row is claimed. The 11 PNG and 11 PDF result artifacts were integrity-checked and indexed; no new full figure-by-figure visual certification or manuscript render is claimed.

## Claim-specific evidence

| Claim | Strongest available evidence | Remaining boundary |
| --- | --- | --- |
| SOC feasibility and stochastic transitions | Existing unit fixtures and native example | Only discrete modeled constraints |
| VI/PI numerical agreement | Tests plus legacy smoke | Discounted model, not physical calibration |
| SARX avoids future-price reads | Perturb-future tests | Does not establish exchange publication time |
| First historical day stays precommitted | Perturb-first-day test | Does not model accepted bids or latency |
| Reported synthetic means/paired values match rows | Statistics contract | Bootstrap endpoints are sanity-checked, not regenerated by this audit |
| Forecast errors/blocks align | Historical contract | Does not rebuild fitted forecasts from raw data |
| Files match declared bundle | Artifact and historical-source audit | Declared outputs and three default software paths only |
| OPSD bytes match source record | Verification routine exists and fixture tests pass | Actual external CSV absent in this review; **not executed against the real file** |

## Remote and publication state

At the read-only metadata snapshot, source-head checks `deploy`, `validate` and `human-authorship-policy` were successful. These are [checks for the reviewed source](https://github.com/mohammadrezwankhan/voltrl/commit/8058e89e4d3516825a400fe86ac45d2e36b6bef0/checks), not checks for the authored documentation. The source-head check set does not include a fresh Python-validation result; path-filtered workflows need separate interpretation.

The repository has a Pages route and an active signature ruleset. Classic protection details were inaccessible through the integration API. Candidate CI, complete required-review/check policy, expected-head merge, deployment commit linkage and live updated handbook content must be observed after a real candidate exists. No “published” or “merged” state follows from local PASS. [Delivery procedure](CI_CD_AND_RELEASE_PLAYBOOK.md).

## Re-run evidence rather than copying conclusions

Run the exact setup/audit commands, retain command, environment, start/end time, tested revision or full candidate tree fingerprint, exit code and output. Link any synthetic-merge/queue run back to both PR head and base. If an input changes, invalidate the relevant result instead of borrowing an older successful check. Archive measured results and disclose unexecuted historical reproduction or inaccessible policy independently.
