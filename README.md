<!-- repository-presentation:start -->

![VoltRL — project overview](https://raw.githubusercontent.com/mohammadrezwankhan/mohammadrezwankhan/main/assets/makeover/social/voltrl.png)

Compare finite-state battery-arbitrage policies under explicit synthetic and historical day-ahead information protocols.

[Environment](#environment) · [Reproduce the benchmark](#reproduce-the-revised-benchmark) · [Benchmark source](voltrl_benchmark.py) · [Result evidence](#outputs) · [Limits](#scope-and-limitations)

---

<!-- repository-presentation:end -->

![VoltRL Arbitrage Evidence Lab: original vector system illustration](assets/brand-uniformity/hero-25d.svg)

VoltRL compares finite-state battery policies under synthetic prices and a documented historical day-ahead protocol. The browser isolates a generic friction calculation before the native inventory, aging, and information constraints.

**[Native-source lesson guide](docs/portfolio/) · [Offline interactive lab](docs/index.html) · [Lesson configuration](docs/lesson-config.json) · [Configuration schema](docs/lesson-config.schema.json)**

## Previous animations

[Open the previous-animation gallery](https://mohammadrezwankhan.github.io/voltrl/animations/) · [Local gallery](docs/animations/index.html)

Earlier animated artwork, waveform demos, and original interactive experiences are linked alongside the current animations.

## Your first interactive result

1. Download or clone this repository and open `docs/index.html` in a modern browser.
2. Select **Module 1**, apply its preset, and compare the declared checkpoint with the plotted result.
3. Change one slider, inspect the model assumptions, then export the configuration or telemetry for your notes.

The browser lab runs offline with no packages, accounts, or live data feeds. Its numbers are deterministic teaching simulations. Each checkpoint states its model time and tolerance; passing it demonstrates agreement with that model, not field calibration or production readiness.

<!-- source-mapped-visuals:start -->

<details>
<summary>System topology and model boundaries</summary>

![Battery arbitrage state machine](assets/brand-uniformity/svg-2.5d/diagrams/battery-arbitrage-state-machine.svg)

Conceptual bounded charge/idle/discharge abstraction; not the full DP, MILP, or RL method.

Motion is optional; the vector topology remains readable with reduced motion enabled.

</details>

<!-- source-mapped-visuals:end -->

## Four-module learning path

| Module | Investigation | Approximate time |
|---|---|---:|
| 1. Separate a gross spread from a net result | Reconcile a normalized hypothetical opportunity before comparing policies. | 12 min |
| 2. Find the break-even boundary | Show how costs can remove an apparent gross opportunity. | 15 min |
| 3. Protect the information boundary | Explain why a policy may not use future realized prices just because a plot displays them. | 18 min |
| 4. Assemble a reproducible benchmark claim | Tie a comparison to its data source, source revision, protocol, and metric definitions. | 18 min |

**Who this is for:** Energy-market researchers and developers learning to compare battery policies without information leakage.

### Continue into the implementation

- [README.md](README.md)
- [requirements.txt](requirements.txt)
- [voltrl.py](voltrl.py)
- [voltrl_benchmark.py](voltrl_benchmark.py)
- [input_provenance.py](input_provenance.py)
- [data/README.md](data/README.md)
- [data/opsd_source.json](data/opsd_source.json)

### Explore or run the source

Python 3.12 recommended with pinned requirements. The historical OPSD CSV is not bundled and must be obtained and hash-verified separately for historical reproduction.

```bash
python -m pip install -r requirements.txt
python voltrl.py --help
python -m unittest discover -s tests -v
```

These commands come from the audited source revision. Runtime requirements and the project's own validation limits are documented below; the standalone browser lab does not execute these commands.

The detailed project guide below remains the source for installation, supported features, licences, and scientific limits. The browser equations and laboratory settings do not change the original application or numerical engine.

<details>
<summary>Project documentation, installation, attribution, and existing validation</summary>

# VoltRL: Audit-Ready Battery-Arbitrage Benchmark

[![Python validation](https://github.com/mohammadrezwankhan/voltrl/actions/workflows/python-validation.yml/badge.svg)](https://github.com/mohammadrezwankhan/voltrl/actions/workflows/python-validation.yml)

VoltRL is a research benchmark for finite-state battery-arbitrage control under
two explicit information protocols. Synthetic prices are revealed sequentially
and support a price-only versus price-plus-hour state ablation. Historical DK1
and DK2 day-ahead prices are evaluated using one 24-hour schedule fixed before
each UTC delivery day. The schedules use history through the previous UTC day,
and delivery-day prices settle the committed quantities. VoltRL is a
**benchmark, not a deployment or live bidding system**.

Public repository: <https://github.com/mohammadrezwankhan/voltrl>

## Documentation Map

- [Environment](#environment) for the pinned runtime.
- [Historical data](#historical-data) for source provenance and checksum requirements.
- [Reproduce the revised benchmark](#reproduce-the-revised-benchmark) for the canonical commands.
- [Main conventions](#main-conventions) for the physical and information assumptions.
- [Outputs](#outputs) for the manifest and audit trail.
- [Contributing](CONTRIBUTING.md) and [citation metadata](CITATION.cff) for shared results.

## What this benchmark demonstrates

VoltRL is an auditable research benchmark under two explicit information
protocols, not a live-trading or deployment system. Across 30 regenerated
synthetic datasets, seasonal autoregressive (SARX) 24-hour MPC has the highest
mean annualized adjusted profit (5.13M currency units, 95% bootstrap CI 5.05–5.23M),
versus 4.62M for the hour-aware finite-horizon MDP (4.51–4.73M).
Historical DK1/DK2 schedules are fixed before delivery and use realized prices
only for settlement; SARX reports EUR 0.129M and EUR 0.187M annualized adjusted
profit, respectively, after modeled degradation. These protocol-bound results
show reproducible policy comparisons, not forecasts of live revenue or evidence
of deployment readiness.

![Primary revision-2 result: synthetic paired differences and historical day-ahead block profit](results_revision2/figures/Figure_3_comparative_results.png)

*Primary result snapshot from the committed revision-2 bundle, generated by
the [`voltrl_benchmark.py`](voltrl_benchmark.py) command below. Panel A shows
paired annualized differences across 30 synthetic seeds; panel B shows
annualized adjusted profit for DK1 and DK2 24-hour schedules fixed before each
delivery day. The [experiment manifest](results_revision2/experiment_manifest.json)
and [audit commands](#outputs) define the information protocol and integrity
checks.*

## What changed in revision 2

- Three-fold expanding-window model selection replaces the invalid BIC-like
  criterion in the original illustrative script.
- Candidate resolutions `4,6,8,10,12,16,20,24,32,40,48` are scored by a
  continuous Gaussian-mixture next-price density with full real-line support,
  so holdout tail values are valid.
- Hierarchical empirical-marginal Dirichlet smoothing (strength 12) supports
  the expanded state-resolution search; the selected values are interior.
- The primary planner and evaluation now use the same undiscounted finite-
  horizon objective and terminal-inventory valuation.
- The exogenous state can include current UTC hour, addressing the known
  seasonal misspecification of a price-only Markov state.
- Thirty independently regenerated synthetic datasets propagate generator,
  fitting, model-selection, and evaluation variability.
- A ridge seasonal autoregression using price lags and daily, weekly, and annual
  harmonics replaces the training-hourly-mean MPC forecast.
- DK1 and DK2 use a day-ahead block protocol that prevents same-day realized
  prices from changing an already committed schedule.
- The primary reward replaces a purely linear throughput proxy with a
  normalized nonlinear DOD potential plus quadratic SOC stress. No-cost,
  linear, and nonlinear models are compared explicitly.
- Physical and planner sensitivities cover one-way efficiency
  `{0.90, 0.95, 1.00}`, degradation cost `{0, 5, 15}`, and planner discount
  `{0.95, 0.99, 1.00}`.

## Environment

Python 3.12 is recommended. Install the exact tested dependencies:

```powershell
python -m pip install -r requirements.txt
```

Continuous integration installs the same pinned environment and runs all unit
tests whenever Python sources or dependencies change.

## Historical data

Download `time_series_60min_singleindex.csv` from the official
[OPSD 2020-10-06 package](https://data.open-power-system-data.org/time_series/2020-10-06/).
The pipeline reads `DK_1_price_day_ahead` and `DK_2_price_day_ahead`. The archived
protocol linearly interpolates 12 missing hours per zone (0.024%) before the
split and reports them in `data_quality.csv`. Linear interpolation uses both
neighboring prices, so an imputed value can depend on a later delivery timestamp.
The exact local filename and
SHA-256 checksum are recorded in [`data/README.md`](data/README.md) and the
machine-readable [`data/opsd_source.json`](data/opsd_source.json). The benchmark
verifies the source filename and checksum before parsing any market data.

### Full Git history for committed-result provenance

For strict verification of the committed revision-2 result bundles, use a complete Git clone:

```powershell
git clone https://github.com/mohammadrezwankhan/voltrl.git
cd voltrl
```

Use the default full-history clone; do not add `--depth`. A source archive or shallow clone may run parts of the project, but it may omit historical Git objects that `software_provenance.py` reads to verify the commits recorded in clean result manifests. The input file checksum check in `input_provenance.py` is separate and remains unchanged. The standalone browser lesson can still be opened from an archive.

## Reproduce the revised benchmark

```powershell
python input_provenance.py `
  data\opsd_time_series_60min_singleindex_2020-10-06.csv

python voltrl_benchmark.py `
  --opsd-csv data\opsd_time_series_60min_singleindex_2020-10-06.csv `
  --output-dir results_revision2_replay `
  --synthetic-seeds 30 `
  --synthetic-hours 17520 `
  --candidates 4,6,8,10,12,16,20,24,32,40,48

python -m unittest discover -s tests -v
python result_bundle_audit.py results_revision2_replay\experiment_manifest.json
```

The upper resolution is 48 rather than 12. Transition rows use hierarchical
smoothing, and the selection audit verifies that the optimum is not the upper
candidate.

## Main conventions

- The 500 MWh battery uses a 100 MWh internal SOC step per hour. With 0.95
  charge efficiency, a full step draws about 105.263 MWh at the grid connection.
- Main one-way charge/discharge efficiency: 0.95 (90.25% round trip).
- Main aging cost: 5 currency units/MWh nominal full-cycle normalization, 25%
  linear throughput component, DOD exponent 1.6, and quadratic SOC stress.
- SOC grid: 0, 100, 200, 300, 400, and 500 MWh.
- Chronological split: first 70% training/development, final 30% untouched
  holdout.
- Primary planner discount: 1.0; terminal SOC is valued at the training-median
  price with discharge efficiency applied.
- Historical actions are fixed as a 24-hour vector using prices through the
  previous UTC day. This is a pre-delivery scheduling experiment. The model does
  not align its information set or delivery blocks to the [Nord Pool Nordic auction gate](https://support.nordpoolgroup.com/support/solutions/articles/8000077444-about-the-day-ahead-auction-in-nordics-baltics)
  at noon CET on the preceding day. It assumes accepted fixed quantities and
  omits bid curves, fees, imbalance, and market impact.
- The perfect-foresight row is an ex-post upper bound computed with the entire
  holdout price path. Archived historical CSVs share one protocol label across
  rows, including the oracle. New runs label the oracle separately.

## Outputs

`results_revision2/` contains seed-level metrics, paired bootstrap summaries,
block-schedule historical results, forecast errors, model-selection folds,
aging and physical sensitivities, solver checks, a machine-readable manifest,
and PNG/PDF figures. Publication claims are based on `voltrl_benchmark.py` and
`results_revision2/`.

The manifest records the verified dataset digest and byte count, binds the
results to the exact Git commit and source-file digests used to generate them,
then declares every CSV and PNG/PDF figure with its byte size and SHA-256
digest. The experiment contract independently checks that manifest physics and
study settings agree with synthetic seed coverage, policy rows, the complete
candidate/fold grid, selected-bin diagnostics, chronological split sizes, and
reported sample counts. The synthetic statistics contract recomputes every
policy mean, sample standard deviation, mean oracle efficiency, paired mean,
positive-seed fraction, and annualized seed result from the underlying rows;
it also recomputes both endpoints of the deterministic percentile bootstrap intervals.
The historical forecast contract then reconstructs
forecast errors and summary metrics from all timestamped rows, checks that each
24-hour block uses only information available before delivery, and confirms
that methods share the same realized prices and test horizon. Run the complete
applicable audit after cloning, downloading, copying, or archiving the results:

```powershell
python result_bundle_audit.py results_revision\experiment_manifest.json
python result_bundle_audit.py results_revision2\experiment_manifest.json --json
```

Revision 1 automatically skips the historical-forecast check because it does
not declare that protocol; revision 2 runs all five checks. The command exits
nonzero when configuration, forecast timing, recomputed
metrics, or result-table coverage drift; when a declared artifact is missing,
unrecorded, has malformed integrity metadata, is resized, or is changed; or when the recorded historical source
snapshot is absent or does not match its byte sizes and SHA-256 digests. Clean
runs are verified against immutable Git objects; runs made from uncommitted
code record and check the exact working-tree bytes instead. CSV files are
canonicalized to LF before hashing so the same table verifies on Windows and
Linux; PNG and PDF artifacts remain byte-exact.

The individual verifier commands remain available for focused diagnosis.

## Scope and Limitations

VoltRL is a reproducible benchmark for comparing explicitly defined policies;
it is not a live market interface, bidding strategy, revenue guarantee, or
grid-operations approval. The price-taking abstraction omits bid curves, fees,
imbalance settlement, market impact, outages, telemetry limits, and plant-level
degradation certification. Treat historical and synthetic results as
protocol-bound evidence, and document any change to the data, assumptions, or
objective before comparing runs.

## Contributing

Focused improvements to the benchmark contract, provenance checks, tests, and
documentation are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md), install the
pinned dependencies, and run the full test and artifact-audit commands before
opening a pull request.

## Citation

For papers, reports, or teaching material, cite the versioned metadata in
[CITATION.cff](CITATION.cff) and identify the exact result bundle and source
snapshot used.

## License

The software is released under the MIT License. Historical prices retain the
terms stated by Open Power System Data and its upstream providers.

</details>


## Source and evidence handbook — 2026-11-19

**[Native handbook](docs/INDEX.md) · [Static reading view](docs/reference/index.html) · [Equations and units](docs/math-and-physics/EQUATIONS_AND_DERIVATIONS.md) · [API/CLI](docs/developer/API_CLI_AND_INTERFACES.md) · [Verification limits](docs/maintainer/VERIFICATION_EVIDENCE_LEDGER.md) · [Roadmap](ROADMAP.md)**

This documentation snapshot reviews source `8058e89e4d3516825a400fe86ac45d2e36b6bef0`. The project guide above is preserved. The handbook adds several precision notes for interpreting it:

- The legacy CLI and the current benchmark use different defaults and selection methods; the revised study is driven by `voltrl_benchmark.py`.
- The nominal 100 MW defines an internal SOC step; inefficient charging requires more grid energy. Nonlinear aging is an absolute-SOC DOD potential plus stress, without rainflow cycles or physical capacity fade.
- Historical preparation interpolates gaps before splitting. Recorded forecast availability is a prior delivery timestamp; no actual exchange auction/publication calendar is modeled.
- Stored synthetic figures use illustrative currency units. Historical DK1/DK2 prices have separate OPSD provenance; the browser proxy uses USD/bps. These are distinct quantities.
- The experiment contract checks selected-bin/fold consistency, not a recomputed NLL optimum or interior optimum. The statistics contract recomputes summaries but only sanity-checks bootstrap intervals. Software provenance defaults to three files at the recorded historical commit.
- Both stored bundles passed their applicable local audits, and 80 existing unit tests passed on the reviewed implementation. The full external-data benchmark, candidate CI, guarded merge and updated live publication are separate outcomes.

See the [assumptions](docs/math-and-physics/ASSUMPTIONS_AND_LIMITS.md), [source coverage](docs/SOURCE_EVIDENCE.md), [security reporting](SECURITY.md) and [recovery runbook](docs/owner/BUS_FACTOR_RECOVERY_RUNBOOK.md). This package preserves native code, workflows, dependencies, original result files, citation and license.
