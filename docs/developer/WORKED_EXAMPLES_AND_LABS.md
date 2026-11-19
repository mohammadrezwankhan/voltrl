# Worked examples and labs

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

These examples were executed against pinned source `8058e89e4d3516825a400fe86ac45d2e36b6bef0` during the 2026-11-19 documentation review. Small synthetic runs illustrate contracts; they do not reproduce the archived 30-seed/historical study. Use the [setup guide](SETUP_AND_REPRODUCIBILITY.md) first.

## 1. Reconcile one charge/discharge pair

```python
from voltrl import Action, BatterySpec

battery = BatterySpec(
    charge_efficiency=0.95, discharge_efficiency=0.95,
    degradation_cost_per_mwh=5.0, nonlinear_degradation=True,
    dod_stress_exponent=1.6, linear_degradation_fraction=0.25,
    soc_stress_cost_per_hour=1.0,
)
charge = battery.reward_components(50.0, Action.CHARGE, 200.0)
discharge = battery.reward_components(100.0, Action.DISCHARGE, 300.0)
print(charge)       # energy cash, modeled degradation/stress, net reward
print(discharge)
print(charge[2] + discharge[2])
```

Observed values, rounded:

| Step | Internal SOC | Grid energy | Energy cash | Aging/stress | Net reward |
| --- | --- | --- | ---: | ---: | ---: |
| Charge at 50 currency/MWh | 200→300 MWh | Buy 105.263158 MWh | −5263.157895 | 125.040000 | −5388.197895 |
| Discharge at 100 currency/MWh | 300→200 MWh | Sell 95 MWh | 9500.000000 | 915.469383 | 8584.530617 |
| Pair | Initial inventory restored | 10.263158 MWh conversion loss | 4236.842105 | 1040.509383 | **3196.332722** |

Terminal adjustment is zero because final and initial SOC agree. Idle at 200 MWh still costs .04 per hour under this primary aging specification. The low-level reward method returns a three-item tuple; it is not a feasibility dispatcher. [voltrl.py:113–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L113-L194)

## 2. Inspect the legacy stationary solver

```bash
python voltrl.py --synthetic-hours 1000 --seed 7 --bins 4 --output-dir ../voltrl-smoke
```

The observed run used 700 training and 300 test hours, selected the explicitly requested four bins, converged in 2469 VI iterations and five PI iterations, and had identical VI/PI policies. VI residual was about 9.98e−9 and PI residual about 2.91e−11. Learned adjusted profit was 203482.674 versus oracle adjusted profit 358332.772 in synthetic currency units. Do not compare these default ideal-battery results directly with revision-2 nonlinear-aging results. [voltrl.py:1001–1168](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1001-L1168)

Inspect `results.json`, `test_trajectory_voltrl.csv`, `test_trajectory_perfect_foresight.csv`, `optimal_policy.csv`, convergence logs and figures. Timing depends on the machine and is not a performance benchmark. Auto-bin selection invokes the legacy BIC-like path; this example avoids that path by setting `--bins 4`.

## 3. Build a finite-horizon native policy

```python
import numpy as np
from voltrl import BatterySpec, generate_synthetic_prices
from voltrl_benchmark import (
    chronological_split, fit_state_model, finite_horizon_policy,
    simulate_finite_policy, trajectory_metrics,
)

frame = generate_synthetic_prices(hours=2400, seed=7)
train, test = chronological_split(frame)
battery = BatterySpec(
    charge_efficiency=.95, discharge_efficiency=.95,
    degradation_cost_per_mwh=5, nonlinear_degradation=True,
    dod_stress_exponent=1.6, linear_degradation_fraction=.25,
    soc_stress_cost_per_hour=1,
)
model = fit_state_model(train, n_bins=4, calendar_aware=True)
salvage = float(np.median(train['price']))
decisions = finite_horizon_policy(model, battery, test['timestamp'], salvage)
trajectory = simulate_finite_policy(test, model, decisions, battery, 200.0)
metrics = trajectory_metrics(trajectory, battery, 200.0, salvage)
print(model.transition.shape, decisions.shape)
print(metrics['inventory_adjusted_profit'])
```

Observed split: 1680/720 hours. Transition shape: `(24,4,4)`. Decisions: `(720,6,4)`. Salvage: 57.8598954975. Adjusted profit: 399607.182976; terminal SOC: 500 MWh. A separate full-future oracle calculation gave 677540.768074 under the same physical model and valuation; the feasibility and upper-bound assertions passed. The fixed K=4 is an explicit teaching choice, not the benchmark's automatic expanding-window selection. [voltrl_benchmark.py:127–136](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L127-L136) [voltrl_benchmark.py:311–469](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L311-L469)

Extend the exercise by calling `expanding_window_selection(train, (3,4))`, reading all 12 candidate/fold/model rows, then refitting the chosen K on all training rows. Never select K using test profit. The existing test verifies this small selection grid is deterministic. [tests/test_voltrl_benchmark.py:41–47](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_voltrl_benchmark.py#L41-L47)

## 4. Audit the archived evidence

```bash
python result_bundle_audit.py results_revision/experiment_manifest.json --json
python result_bundle_audit.py results_revision2/experiment_manifest.json --json
```

The first gives four passed checks and an explicit skip; the second gives five passed checks. The revision-2 historical validator covers 90,720 forecast rows: two cases × three forecast methods × 15,120 test hours, organized into 3,780 complete method/day blocks. These are audits of committed rows, not new forecasts. [historical_forecast_contract.py:298–410](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L298-L410) [result_bundle_audit.py:75–162](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L75-L162)

## 5. Check the browser teaching proxy

Open the [interactive lab](../index.html), load each module preset, set the declared time and check outcomes. Module 1 at t=0 gives 25 bps and 25 USD. Module 2 gives zero USD at t=0 and −4.755283 USD at t=24. Module 3 gives −20 bps initially and −24.755283 USD at t=24. Module 4 gives 60 USD costs and 40.489435 USD scenario P&L at t=24. All eight configured checks passed when the actual inline pure-model export was evaluated locally. [docs/lesson-config.json:1–317](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/lesson-config.json#L1-L317) [docs/index.html:296–345](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L296-L345)

The P&L is one hypothetical opportunity at the selected time, not accumulated earnings. CSV export has 241 deterministic sample points and current parameters. Browser display, keyboard flow and download behavior remain separate from the pure-function check. [Browser contracts](BROWSER_MODEL_CATALOG.md).
