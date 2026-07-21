# VoltRL: Audit-Ready Battery-Arbitrage Benchmark

[![Python validation](https://github.com/mohammadrezwankhan/voltrl/actions/workflows/python-validation.yml/badge.svg)](https://github.com/mohammadrezwankhan/voltrl/actions/workflows/python-validation.yml)

VoltRL is a research benchmark for finite-state battery-arbitrage control under
two explicit information protocols. Synthetic prices are revealed sequentially
and support a price-only versus price-plus-hour state ablation. Historical DK1
and DK2 day-ahead prices are evaluated using one 24-hour schedule fixed before
each delivery day; realized prices are used only for settlement. VoltRL is a
**benchmark, not a deployment or live bidding system**.

Public repository: <https://github.com/mohammadrezwankhan/voltrl>

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
The pipeline reads `DK_1_price_day_ahead` and `DK_2_price_day_ahead`. Twelve
internal missing hours per zone (0.024%, spring clock changes) are linearly
interpolated and reported in `data_quality.csv`. The exact local filename and
SHA-256 checksum are recorded in [`data/README.md`](data/README.md) and the
machine-readable [`data/opsd_source.json`](data/opsd_source.json). The benchmark
verifies the source filename and checksum before parsing any market data.

## Reproduce the revised benchmark

```powershell
python input_provenance.py `
  data\opsd_time_series_60min_singleindex_2020-10-06.csv

python voltrl_benchmark.py `
  --opsd-csv data\opsd_time_series_60min_singleindex_2020-10-06.csv `
  --output-dir results_revision2 `
  --synthetic-seeds 30 `
  --synthetic-hours 17520 `
  --candidates 4,6,8,10,12,16,20,24,32,40,48

python -m unittest discover -s tests -v
python artifact_integrity.py results_revision2\experiment_manifest.json
```

The upper resolution is 48 rather than 12. Transition rows use hierarchical
smoothing, and the selection audit verifies that the optimum is not the upper
candidate.

## Main conventions

- Battery: 500 MWh capacity and 100 MW one-hour charge/discharge step.
- Main one-way charge/discharge efficiency: 0.95 (90.25% round trip).
- Main aging cost: 5 currency units/MWh nominal full-cycle normalization, 25%
  linear throughput component, DOD exponent 1.6, and quadratic SOC stress.
- SOC grid: 0, 100, 200, 300, 400, and 500 MWh.
- Chronological split: first 70% training/development, final 30% untouched
  holdout.
- Primary planner discount: 1.0; terminal SOC is valued at the training-median
  price with discharge efficiency applied.
- Historical actions are fixed as a complete 24-hour vector before the
  delivery day. The price-taking abstraction assumes accepted fixed quantities
  and still omits bid curves, fees, imbalance, and market impact.
- Perfect foresight is a diagnostic upper bound and is never available to any
  causal policy.

## Outputs

`results_revision2/` contains seed-level metrics, paired bootstrap summaries,
block-schedule historical results, forecast errors, model-selection folds,
aging and physical sensitivities, solver checks, a machine-readable manifest,
and PNG/PDF figures. Publication claims are based on `voltrl_benchmark.py` and
`results_revision2/`.

The manifest records the verified dataset digest and byte count, binds the
results to the exact Git commit and source-file digests used to generate them,
then declares every CSV and PNG/PDF figure with its byte size and SHA-256
digest. Run both verifiers after cloning, downloading, copying, or archiving
the results:

```powershell
python artifact_integrity.py results_revision2\experiment_manifest.json
python software_provenance.py results_revision2\experiment_manifest.json
```

The commands exit nonzero when a declared artifact is missing, unrecorded,
resized, or changed, or when the recorded historical source snapshot is absent
or does not match its byte sizes and SHA-256 digests. Clean runs are verified
against immutable Git objects; runs made from uncommitted code record and check
the exact working-tree bytes instead. CSV files are canonicalized to LF before
hashing so the same table verifies on Windows and Linux; PNG and PDF artifacts
remain byte-exact.

## License

The software is released under the MIT License. Historical prices retain the
terms stated by Open Power System Data and its upstream providers.
