# Architecture and information flow

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

The scientific engine is a collection of directly importable Python modules. There is no packaged service, training daemon, exchange connection, hardware interface, installed console entry point or database in this source tree. The Pages site is a separate static teaching and reading surface. [voltrl.py:1–49](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1-L49) [voltrl_benchmark.py:1–74](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1-L74) [.github/workflows/deploy-dashboard.yml:1–82](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/deploy-dashboard.yml#L1-L82)

## Components and responsibilities

| Component | Inputs and responsibility | Outputs / boundary |
| --- | --- | --- |
| `voltrl.py` | Battery grid/reward, price bins and transitions, stationary VI/PI, trajectory settlement, full-future oracle, synthetic generator, legacy CLI | Arrays, trajectories, diagnostics, CSV/NPZ/PNG/JSON; no market execution |
| `voltrl_benchmark.py` | Validate hourly frames; select bin count; fit price-only/hour-aware transitions and SARX; evaluate causal policies; build revision-2 tables and figures | A reproducible benchmark directory with manifest; historical input must first match the provenance record |
| `input_provenance.py` | Required local basename and raw SHA-256 | Verified source identity before CSV parsing |
| `experiment_contract.py` | Manifest settings and five core tables | Configuration, seed/policy/fold/split coverage errors |
| `synthetic_statistics_contract.py` | Seed rows and summaries | Recomputed means, sample deviations, paired differences, annualization and interval sanity |
| `historical_forecast_contract.py` | Forecast detail/summary and market table | Timing, complete blocks, cross-method alignment and recomputed forecast errors |
| `artifact_integrity.py` / `software_provenance.py` | Declared output files / recorded source files | Canonical CSV and byte-exact figure integrity / historical Git-blob or working-file verification |
| `result_bundle_audit.py` | One experiment manifest | Readable or JSON aggregate with explicit passed, failed and skipped checks |
| `docs/index.html` | Embedded lesson JSON and inline deterministic JavaScript | Synthetic local teaching telemetry; no Python or OPSD execution |

Module locators: [voltrl.py:374–797](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L374-L797) [voltrl_benchmark.py:105–295](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L105-L295) [voltrl_benchmark.py:1666–1835](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1666-L1835) [input_provenance.py:65–118](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L65-L118) [result_bundle_audit.py:75–162](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L75-L162).

## Decision-time data access

| Stage | Synthetic sequential benchmark | Historical block pilot |
| --- | --- | --- |
| Development | First 70% of observations; three expanding folds select K using hour-aware continuous NLL | First 70% of complete UTC days; fit SARX and training-hour seasonal means |
| Policy input | Current realized price/bin, current SOC and known UTC hour; MPC has current and earlier prices | Before each UTC day, use observations through the preceding delivery hour; construct 24 forecast prices |
| Decision | Finite-horizon MDP action or the first action of a rolling forecast DP | Solve a forecast-price DP once; freeze all 24 actions |
| Settlement | Apply the action to the actual current price | Apply the frozen schedule to the actual day's prices |
| Diagnostic | Full future actual-price oracle with matching physical constraints and inventory valuation | Same full-future oracle, explicitly unavailable to causal policies |

[voltrl_benchmark.py:127–155](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L127-L155) [voltrl_benchmark.py:453–469](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L453-L469) [voltrl_benchmark.py:591–811](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L591-L811) [voltrl.py:648–714](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L648-L714)

OPSD processing trims missing edges and interpolates internal gaps before the train/test split. This is disclosed offline data preparation. The recorded “information available through” time is a delivery timestamp; code does not map it to an exchange auction gate or publication latency. Forecast-causality tests establish code-level data dependence, not an operational market schedule. [voltrl_benchmark.py:1083–1118](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1083-L1118) [tests/test_voltrl_benchmark.py:79–122](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_voltrl_benchmark.py#L79-L122)

## State, memory and execution

The legacy dense MDP has `S = (C/q + 1)K` states, three actions and a transition tensor `(S, 3, S)`. Price transitions are exogenous; feasible actions deterministically move SOC and distribute probability over the next price bin. Infeasible actions carry `-inf` reward and are masked. At default C=500, q=100 and K=4, S=24. [voltrl.py:374–481](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L374-L481)

The benchmark stores `(24,K,K)` hour-aware transitions or `(K,K)` price-only transitions, and finite-horizon action decisions `(H,N_soc,K)` as `int8`. Backward recursion retains two-dimensional value slices. No continuous-state approximation, neural network or rainflow cycle counter is implemented. [voltrl_benchmark.py:78–102](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L78-L102) [voltrl_benchmark.py:173–224](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L173-L224) [voltrl_benchmark.py:311–397](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L311-L397)

## Artifact and publication flow

A new benchmark run verifies input bytes, captures provenance for `voltrl.py`, `voltrl_benchmark.py` and `requirements.txt`, writes tables/figures, then hashes declared outputs into the manifest. Audit the bundle independently before quoting it. Those three software hashes are narrower than a complete repository or environment attestation. [voltrl_benchmark.py:1666–1835](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1666-L1835) [software_provenance.py:14–20](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L14-L20) [software_provenance.py:89–130](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L89-L130)

The Pages workflow validates the static config and deploys the entire `docs/` directory from main. The new reference page is derived from canonical Markdown. Existing lesson JSON, model JavaScript, historical visual assets and original result bundles remain unchanged. [.github/workflows/deploy-dashboard.yml:26–82](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/deploy-dashboard.yml#L26-L82)
