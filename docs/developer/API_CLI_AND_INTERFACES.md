# API, CLI and data interfaces

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

Import the repository modules directly from the checkout. The source has no installed package or console-script manifest. The [declaration catalog](API_REFERENCE.md) enumerates source-defined public names and signatures, including helper dataclasses and methods; it is a source snapshot, not a promise of backward compatibility. Python parameters without `/` or `*` are positional-or-keyword; a default makes a value optional, not keyword-only.

## Native object contracts

| Object / entry | Contract |
| --- | --- |
| `Action` | `CHARGE=0`, `IDLE=1`, `DISCHARGE=2`; use names rather than signed integers |
| `BatterySpec(...)` | Frozen configuration; validates finite physical fields and grid divisibility; properties expose q and SOC levels |
| `reward_components(price, action, soc_before_mwh=None)` | Returns `(energy_cash_flow, degradation_cost, net_reward)`; nonlinear cost needs SOC; this method is not a complete frame/action validator |
| `SolverConfig(...)` | Frozen discounted-solver settings; γ<1, positive tolerance and positive integer cap |
| `PriceDiscretizer.fit(prices,K)` / `.transform(prices)` | Training quantile fit / integer labels; preserves training edges/representatives |
| `BatteryArbitrageMDP.build(...)` | Dense joint SOC-price transition/reward/action mask; `state_index` and `decode_state` expose ordering |
| `value_iteration` / `policy_iteration` | Return `SolverResult`: values, integer policy, iterations, convergence flag, run time and log DataFrame |
| `fit_state_model(frame,K,calendar_aware)` | Returns `StateModel` with transition probabilities, count arrays and Gaussian emissions |
| `finite_horizon_policy(...)` | Returns `(H,N_soc,K)` action array, with default discount 1 and terminal inventory value |
| `trajectory_from_actions(...)` | Settles an already aligned chronological frame and one valid feasible action per row; rejects silent action reassignment |
| `fit_seasonal_ar(...)` / `seasonal_ar_forecast(...)` | Training-fitted regression / recursive forecast from history through `current_index`; no future actual-price access |
| `day_ahead_block_trajectory(...)` | Returns trajectory plus timestamped forecast-detail DataFrame for `sarx`, `seasonal_mean` or `persistence` |
| `artifact_integrity.verify_artifact_manifest(...)` | Returns `list[str]` of artifact inventory, size and hash errors |
| `software_provenance.verify_software_provenance(...)` | Returns `list[str]` of recorded source-provenance errors |
| `experiment_contract.verify_experiment_contract(...)` | Returns `list[str]` of configuration, coverage and semantic contract errors |
| `synthetic_statistics_contract.verify_synthetic_statistics_contract(...)` | Returns `list[str]` of synthetic-statistics contract errors |
| `historical_forecast_contract.verify_historical_forecast_contract(...)` | Returns `list[str]` of historical-forecast contract errors |
| `input_provenance.verify_source_file(...)` | Returns a frozen `SourceVerification` record containing path, byte count, SHA-256, dataset, version, DOI and URL; raises `FileNotFoundError` for a missing input file, `ValueError` for invalid metadata or filename/hash mismatch, and can propagate file-reading `OSError` |
| `audit_result_bundle(...)` | Returns `BundleAudit`, containing `AuditCheck` records and `passed` property; skipped checks remain explicit |

The five bundle verifiers listed above return an empty error list when their checks find no errors; malformed inputs and file-reading failures can raise before a list is returned. `verify_source_file` has a separate record-or-exception contract. [artifact_integrity.py:126–193](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L126-L193) [software_provenance.py:191–250](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L191-L250) [experiment_contract.py:544–568](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/experiment_contract.py#L544-L568) [synthetic_statistics_contract.py:563–567](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L563-L567) [historical_forecast_contract.py:529–533](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L529-L533) [input_provenance.py:20–86](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L20-L86)

[voltrl.py:36–266](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L36-L266) [voltrl.py:374–645](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L374-L645) [voltrl_benchmark.py:78–102](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L78-L102) [voltrl_benchmark.py:311–811](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L311-L811) [result_bundle_audit.py:24–162](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L24-L162)

Two modules define **different** `trajectory_metrics` functions: the core version takes both learned and oracle trajectories; the benchmark version takes one trajectory. Import them with explicit module names or aliases. Likewise `main` and `build_parser` belong to each module, not one unified global CLI. [voltrl.py:717–797](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L717-L797) [voltrl_benchmark.py:814–851](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L814-L851)

## Commands and write boundaries

| Command | Inputs / options | Read or write behavior |
| --- | --- | --- |
| `python voltrl.py` | Optional CSV or generated prices; flags listed below | Creates/reuses output directory; writes legacy results |
| `python voltrl_benchmark.py` | Required `--opsd-csv`; record, seeds, hours, K candidates | Verifies exact external input, then writes full benchmark bundle |
| `python input_provenance.py FILE [--record RECORD]` | Default record `data/opsd_source.json` | Read-only filename/raw-digest verification |
| `python result_bundle_audit.py MANIFEST [--source-root ROOT] [--json]` | Default source root inferred from manifest location | Read-only aggregate; stdout report; exit 1 for failure |
| `python artifact_integrity.py MANIFEST [--write]` | Declared output paths | Read-only normally; `--write` replaces inventory metadata |
| `python software_provenance.py MANIFEST [--source-root ROOT] [--write]` | Source root defaults to current directory | Read-only normally; `--write` records new software provenance |
| `python experiment_contract.py MANIFEST` | Five core tables | Read-only configuration/coverage checks |
| `python synthetic_statistics_contract.py MANIFEST` | Three statistical tables | Read-only statistics checks |
| `python historical_forecast_contract.py MANIFEST` | Historical detail, summary and market table | Read-only timing/alignment/error checks |
| `python scripts/portfolio/validate_guide.py` | Repository-local static guide/config/assets | Assertions and summary; no model execution |
| `python docs/reference/build_reference.py [--check]` | Canonical handbook files and Pandoc | Writes only derived handbook HTML; `--check` compares without writing |

Each native CLI supports `--help`; all nine native help commands were executed successfully in review. Source parsers: [voltrl.py:1171–1225](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1171-L1225) [voltrl_benchmark.py:1838–1863](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1838-L1863) [result_bundle_audit.py:165–224](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L165-L224).

### Legacy options and exact defaults

| Options | Defaults / meaning |
| --- | --- |
| `--csv`, `--price-column`, `--timestamp-column` | No CSV → synthetic; `price`; no timestamp column → generated hourly index |
| `--output-dir`, `--synthetic-hours`, `--seed` | `results`, 17520, 42 |
| `--train-fraction` | .7; CLI requires (.05,.95); both partitions at least 100 rows |
| `--bins`, `--candidate-bins`, `--bin-validation-fraction` | `auto`; `4,5,6,7,8,9,10,11,12,13,14,15,16`; .2 |
| `--prior-strength` | 1 |
| `--capacity-mwh`, `--max-power-mw` | 500,100; interval stays 1 h in this CLI |
| `--charge-efficiency`, `--discharge-efficiency`, `--degradation-cost` | 1,1,0; nonlinear parameters have no legacy CLI flags |
| `--gamma`, `--tolerance`, `--max-iterations` | .99,1e−8,100000 |
| `--initial-soc-mwh`, `--salvage-price` | 200; unspecified salvage → training median |
| `--log-level` | `INFO` |

### Benchmark options and exact defaults

| Option | Default |
| --- | --- |
| `--opsd-csv` | Required path |
| `--opsd-provenance` | `data/opsd_source.json` |
| `--output-dir` | `results_revision2` |
| `--synthetic-seeds` | 30, interpreted as `range(30)` |
| `--synthetic-hours` | 17520 per seed |
| `--sensitivity-seed` | 42 |
| `--candidates` | `4,6,8,10,12,16,20,24,32,40,48` |

The benchmark's primary physical settings and .7 split are code-defined, not CLI flags. Its sensitivity labels/figure title contain defaults (`Synthetic seed 42`, `30 seeds`) that do not adapt to all custom CLI values; label a custom run accurately and see debt VR-03. [voltrl_benchmark.py:1289–1400](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1289-L1400) [voltrl_benchmark.py:1495–1495](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1495-L1495) [voltrl_benchmark.py:1666–1835](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1666-L1835)

## Input and file formats

Native frames have `timestamp` and `price`. The strict benchmark validator converts to UTC/numeric, drops invalid rows, sorts, deduplicates and then requires consecutive hourly finite prices; trajectory settlement additionally rejects a frame whose ordering/length would change. The legacy CSV loader is more permissive and does not enforce an uninterrupted hourly cadence. [voltrl.py:837–865](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L837-L865) [voltrl_benchmark.py:105–124](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L105-L124) [voltrl_benchmark.py:400–450](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L400-L450)

| Data product | Important fields / interpretation |
| --- | --- |
| Core trajectory | `step,timestamp,price,price_bin,soc_before_mwh,action,soc_after_mwh,energy_cash_flow,degradation_cost,profit,cumulative_profit` |
| Benchmark trajectory | Same settlement meanings, without `price_bin`; action labels are charge/idle/discharge |
| `synthetic_seed_metrics.csv` | One seed-policy row; selected K, test hours, cash/adjusted/annualized metrics, oracle ratio and conditional daily contrasts |
| `model_selection_folds.csv` | Seed/case, K, fold, model type, training/validation hours and mean NLL |
| `case_diagnostics.csv` | Split ranges/counts, selected K and synthetic scores; historical rows have complete-day fields |
| `historical_forecast_detail.csv` | Case, method, prior-delivery timestamp, protocol, delivery timestamp, lead 1…24, forecast, realized price, signed error |
| `historical_forecast_summary.csv` | Count, ME, MAE, RMSE per case/method |
| `experiment_manifest.json` | Configuration, declared outputs, artifact inventory, recorded generating source, runtime and OPSD record |

[voltrl.py:602–645](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L602-L645) [voltrl_benchmark.py:400–450](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L400-L450) [voltrl_benchmark.py:886–1080](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L886-L1080)

The legacy run writes `training_prices.csv`, `test_prices.csv`, optional `bin_selection_bic.csv`, `price_transition_matrix.csv`, `price_transition_counts.csv`, `price_bins.csv`, `optimal_policy.csv`, both solver logs, both `test_trajectory_*.csv`, `mdp_arrays.npz`, four PNG figures and `results.json`. The benchmark's revision-2 manifest declares 13 CSV tables and six figures in both PNG and PDF (25 artifacts). Consult the exact manifest instead of inferring freshness from filenames. [voltrl.py:1118–1168](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1118-L1168) [voltrl_benchmark.py:1752–1835](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1752-L1835)

## Browser and documentation interfaces

[Browser contracts](BROWSER_MODEL_CATALOG.md) distinguish `LabSimulation`, `LabDashboard`, synthetic CSV/config export, personal learning-path storage and archived animation controls. There is no native REST API, authentication/session endpoint, message queue or device I/O to configure in this snapshot. These are inventory findings, not promises about future releases.
