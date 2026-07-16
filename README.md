# VoltRL: Audit-Ready Battery-Arbitrage Benchmark

VoltRL is a research benchmark for testing finite-state battery-arbitrage
policies under chronologically revealed hourly prices. The revised study is
explicitly a **benchmark, not a deployment or market-bidding study**. It
compares a price-only finite-horizon MDP with an hour-aware state model, a
causal seasonal model-predictive controller, a training-quantile threshold
rule, an idle controller, and a perfect-foresight diagnostic upper bound.

Public repository: <https://github.com/mohammadrezwankhan/voltrl>

## What changed in the revision

- Three-fold expanding-window model selection replaces the invalid BIC-like
  criterion in the original illustrative script.
- Candidate models are scored by a continuous Gaussian-mixture next-price
  density with full real-line support, so holdout tail values are valid.
- The primary planner and evaluation now use the same undiscounted finite-
  horizon objective and terminal-inventory valuation.
- The exogenous state can include current UTC hour, addressing the known
  seasonal misspecification of a price-only Markov state.
- Thirty independently regenerated synthetic datasets propagate generator,
  fitting, model-selection, and evaluation variability.
- DK1 and DK2 historical day-ahead prices from Open Power System Data version
  2020-10-06 provide external pilot evidence (DOI:
  `10.25832/time_series/2020-10-06`).
- Physical and planner sensitivities cover one-way efficiency
  `{0.90, 0.95, 1.00}`, degradation cost `{0, 5, 15}`, and planner discount
  `{0.95, 0.99, 1.00}`.

## Environment

Python 3.12 is recommended. Install the exact tested dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Historical data

Download `time_series_60min_singleindex.csv` from the official
[OPSD 2020-10-06 package](https://data.open-power-system-data.org/time_series/2020-10-06/).
The pipeline reads `DK_1_price_day_ahead` and `DK_2_price_day_ahead`. Twelve
internal missing hours per zone (0.024%, spring clock changes) are linearly
interpolated and reported in `data_quality.csv`. The exact local filename and
SHA-256 checksum are recorded in [`data/README.md`](data/README.md).

## Reproduce the revised benchmark

```powershell
python voltrl_benchmark.py `
  --opsd-csv data\opsd_time_series_60min_singleindex_2020-10-06.csv `
  --output-dir results_revision `
  --synthetic-seeds 30 `
  --synthetic-hours 17520 `
  --candidates 4,6,8,10,12

python -m unittest discover -s tests -v
```

The common candidate range is deliberately capped at 12 bins: for the
two-year synthetic training segments this retains at least 42 observations on
average per hour-price source state. The cap controls transition sparsity and
is therefore part of the prespecified benchmark, not a claim that 12 is a
globally optimal discretization.

## Main conventions

- Battery: 500 MWh capacity and 100 MW one-hour charge/discharge step.
- Main one-way charge/discharge efficiency: 0.95 (90.25% round trip).
- Main degradation proxy: 5 currency units per internal MWh moved.
- SOC grid: 0, 100, 200, 300, 400, and 500 MWh.
- Chronological split: first 70% training/development, final 30% untouched
  holdout.
- Primary planner discount: 1.0; terminal SOC is valued at the training-median
  price with discharge efficiency applied.
- The historical day-ahead series are evaluated as sequentially revealed
  benchmark signals. Results do not represent executable bidding revenue.
- Perfect foresight is a diagnostic upper bound and is never available to any
  causal policy.

## Outputs

`results_revision/` contains seed-level metrics, paired bootstrap summaries,
historical results, model-selection folds, state-prediction diagnostics,
sensitivity tables, solver checks, a machine-readable manifest, and figures
in PNG/PDF. The original `voltrl.py` remains as the reusable finite-MDP engine;
publication claims are based on `voltrl_benchmark.py` and `results_revision/`.

## License

The software is released under the MIT License. Historical prices retain the
terms stated by Open Power System Data and its upstream providers.
