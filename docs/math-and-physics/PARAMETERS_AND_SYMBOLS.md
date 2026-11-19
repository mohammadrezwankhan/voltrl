# Parameters, symbols and units

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

The implementation uses scalar floats and NumPy/pandas arrays; units are conventions encoded in names and equations, not a runtime units library. Historical price plots use EUR/MWh; synthetic results use the generator's illustrative currency scale. A value in browser USD/bps must not be converted into battery profit without an independently defined model. [voltrl.py:52–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L52-L194) [voltrl_benchmark.py:1481–1516](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1481-L1516) [docs/index.html:214–219](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L214-L219)

## Native battery and objective

| Symbol / code field | Units | Legacy default | Primary benchmark | Validity and meaning |
| --- | --- | ---: | ---: | --- |
| C / `capacity_mwh` | MWh internal energy | 500 | 500 | Finite >0; C/q integer |
| P / `max_power_mw` | MW internal step rate | 100 | 100 | Finite >0; no separate AC import/export cap |
| Δt / `interval_hours` | h | 1 | 1 | Positive; benchmark is hourly throughout |
| q / `energy_step_mwh` | MWh | 100 | 100 | PΔt; one full action step |
| E / `soc_*_mwh` | MWh | grid 0…500 | same | Energy, not percentage |
| E0 / `initial_soc_mwh` | MWh | 200 | 200 | Must match the grid |
| ηc,ηd / efficiency fields | ratio | 1,1 | .95,.95 | Each in (0,1]; round trip .9025 |
| d / `degradation_cost_per_mwh` | currency/internal MWh | 0 | 5 | Nonnegative nominal coefficient |
| `nonlinear_degradation` | boolean | false | true | Enables DOD potential and SOC stress |
| ν / `dod_stress_exponent` | dimensionless | 1.6 | 1.6 | ≥1 in `BatterySpec` |
| α / `linear_degradation_fraction` | ratio | .25 | .25 | [0,1] |
| s / `soc_stress_cost_per_hour` | currency/h | 0 | 1 | Nonnegative; after-action SOC stress |
| p / `price` | currency/MWh | generated / CSV | generated / OPSD | May be negative; finite where validated |
| v / terminal salvage | currency/MWh | training median unless CLI override | training median | Values remaining energy with ηd; initial inventory removed in adjusted metric |
| γ / planner discount | dimensionless per step | .99 | 1 | Legacy [0,1); finite horizon (0,1] |
| tolerance | currency-valued value change | 1e−8 | no iterative primary solve | Positive finite; legacy stopping condition |
| `max_iterations` | iterations | 100000 | not a finite-horizon setting | Positive integer, not boolean |

[voltrl.py:52–213](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L52-L213) [voltrl.py:1171–1203](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1171-L1203) [voltrl_benchmark.py:1671–1682](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1671-L1682)

## Statistical and protocol configuration

| Quantity | Implemented choice | Consequence |
| --- | --- | --- |
| K / price bins | Legacy CLI auto or integer; benchmark candidates 4,6,8,10,12,16,20,24,32,40,48 | Each training fit needs ≥10K observations and distinct quantile edges |
| Transition prior λ | Legacy 1; benchmark 12 | Positive prior covers unseen outgoing states; empirical marginal is fitted separately |
| σ floor | max(.5,.05×training pooled SD) | Full real-line Gaussian-mixture scoring; .5 has price units |
| Development fraction | .7 | Synthetic floor(.7N); historical split on complete UTC days |
| SARX lags | 1,2,24,48,168 hours | Require enough available history; regression uses six harmonic features |
| SARX ridge | .001 | Standardized-price fit; intercept unpenalized |
| Synthetic seeds / hours | 0…29 / 17520 each | These are generator experiments, not 30 measured markets |
| Forecast block / MPC horizon | 24 h | Historical fixed day; synthetic rolling first action |
| Bootstrap | 5000 resamples; seven-day circular blocks within a case | Distinguish cross-seed annualized estimates from conditional daily cash estimates |
| H | number of hourly observations | Annualization uses 8760/H; not a forecast horizon confidence guarantee |

[voltrl_benchmark.py:158–295](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L158-L295) [voltrl_benchmark.py:544–709](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L544-L709) [voltrl_benchmark.py:854–883](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L854-L883) [voltrl_benchmark.py:1121–1171](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1121-L1171) [voltrl_benchmark.py:1838–1859](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1838-L1859)

## Array and table conventions

`Action` values are categorical indices 0/1/2, not signed control magnitudes. `BatteryArbitrageMDP.state_index(i,j)=iK+j`; flattening is SOC-major. A `StateModel` has bin means/SD of shape `(K,)`, price-only transitions `(K,K)` or hour-aware transitions `(24,K,K)`. Finite decisions have shape `(H,N_soc,K)`; trajectories have one row per settled hour. UTC timestamps and matching row order are part of the causal contract. [voltrl.py:36–45](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L36-L45) [voltrl.py:374–405](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L374-L405) [voltrl_benchmark.py:78–102](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L78-L102) [voltrl_benchmark.py:400–450](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L400-L450)

A forecast error is forecast minus realized price. ME retains sign, MAE removes it, RMSE squares before averaging and taking a square root. These are price-unit errors, not revenue metrics. CSV booleans, empty optional cells and mixed synthetic/historical diagnostics must be interpreted by column meaning rather than assuming every field is present in every row. [historical_forecast_contract.py:194–207](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L194-L207) [historical_forecast_contract.py:365–410](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L365-L410)
